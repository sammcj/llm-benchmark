# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openai>=3.1.0",
#     "httpx>=0.28.1",
# ]
# ///
import argparse
import asyncio
import json
import logging
import math
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("llm_benchmark")

SHORT_PROMPTS = [
    "Explain the concept of artificial intelligence in simple terms.",
    "What are the main causes of climate change?",
    "Describe the process of photosynthesis in plants.",
    "How does the human immune system work?",
    "What were the main causes of World War II?",
    "Explain the theory of relativity in layman's terms.",
    "What are the key principles of effective leadership?",
    "How does blockchain technology work?",
    "What are the main theories about the origin of the universe?",
    "Describe the water cycle and its importance for life on Earth.",
    "What are the major differences between capitalism and socialism?",
    "How does the human brain process and store memories?",
    "What are the main challenges in space exploration?",
    "Explain the concept of supply and demand in economics.",
]

LONG_PROMPT_PAIRS = [
    {
        "prompt": "Explain the concept of artificial intelligence in simple terms.",
        "context": "Artificial intelligence (AI) is a rapidly evolving field of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence. These tasks include visual perception, speech recognition, decision-making, and language translation. AI systems are designed to learn from experience, adjust to new inputs, and perform human-like tasks. The field of AI encompasses various subfields, including machine learning, neural networks, and deep learning, which have led to significant advancements in areas such as autonomous vehicles, virtual assistants, and recommendation systems."
    },
    {
        "prompt": "What are the main causes of climate change?",
        "context": "Climate change is a complex global phenomenon primarily driven by human activities that release greenhouse gases into the atmosphere. The burning of fossil fuels for energy, deforestation, industrial processes, and agriculture are major contributors to the increased concentration of carbon dioxide and other heat-trapping gases. These gases form a 'blanket' around the Earth, causing the planet to warm at an unprecedented rate. The resulting changes in temperature patterns lead to more frequent and severe weather events, rising sea levels, and disruptions to ecosystems worldwide."
    },
        {
        "prompt": "Describe the process of photosynthesis in plants.",
        "context": "Photosynthesis is a fundamental biological process that allows plants to convert light energy into chemical energy. This process occurs in the chloroplasts of plant cells, specifically in structures called thylakoids. Chlorophyll, the pigment that gives plants their green color, is crucial in capturing light energy. During photosynthesis, plants take in carbon dioxide from the air through tiny pores called stomata and water from the soil through their roots. Using light energy, they combine these ingredients to produce glucose and oxygen. This process not only provides energy for the plant but also releases oxygen as a byproduct, which is essential for most life on Earth."
    },
    {
        "prompt": "How does the human immune system work?",
        "context": "The human immune system is a complex network of cells, tissues, and organs that work together to defend the body against harmful pathogens. It consists of two main parts: the innate immune system, which provides a quick, non-specific response to invaders, and the adaptive immune system, which develops targeted defenses against specific pathogens. Key components include white blood cells (such as neutrophils, macrophages, and lymphocytes), antibodies, and the complement system. The immune system has the remarkable ability to distinguish between the body's own cells and foreign invaders, allowing it to target threats while minimizing damage to healthy tissue."
    },
    {
        "prompt": "What were the main causes of World War II?",
        "context": "World War II, which lasted from 1939 to 1945, was one of the deadliest conflicts in human history. Its origins can be traced to several complex factors. The harsh terms of the Treaty of Versailles, which ended World War I, left Germany economically devastated and resentful. This paved the way for the rise of fascism and the Nazi Party under Adolf Hitler. Aggressive expansionist policies by Nazi Germany, Fascist Italy, and Imperial Japan, combined with the policy of appeasement by Western powers, allowed these regimes to gain territory unchecked. The immediate trigger for the war in Europe was Germany's invasion of Poland in September 1939, while the attack on Pearl Harbor in 1941 brought the United States into the conflict."
    },
    {
        "prompt": "Explain the theory of relativity in layman's terms.",
        "context": "Albert Einstein's theory of relativity, developed in the early 20th century, revolutionized our understanding of space, time, and gravity. It consists of two parts: special relativity and general relativity. Special relativity, introduced in 1905, deals with objects moving at very high speeds. It proposes that the speed of light is constant for all observers and that time and space are not absolute but relative to the observer's motion. This leads to phenomena like time dilation and length contraction. General relativity, published in 1915, extends these ideas to include gravity. Einstein proposed that massive objects curve the fabric of spacetime, and this curvature is what we experience as gravity. These theories have been consistently supported by experimental evidence and have practical applications in technologies like GPS satellites."
    },
    {
        "prompt": "What are the key principles of effective leadership?",
        "context": "Effective leadership is crucial in guiding organizations, teams, and individuals towards achieving their goals. While leadership styles may vary, several key principles are widely recognized as essential for success. These include clear communication, which ensures that vision and expectations are understood by all; integrity, which builds trust and respect; adaptability, allowing leaders to navigate changing environments; empathy, fostering strong relationships and understanding team dynamics; decision-making skills, enabling timely and informed choices; vision, providing direction and inspiration; and the ability to empower others, encouraging growth and innovation within the team. Effective leaders also demonstrate accountability, both for their own actions and those of their team, and continuously seek personal growth and learning opportunities."
    },
    {
        "prompt": "How does blockchain technology work?",
        "context": "Blockchain is a decentralized, distributed ledger technology that underlies cryptocurrencies like Bitcoin, but has potential applications far beyond digital currencies. At its core, a blockchain is a chain of blocks, each containing a list of transactions. Every block is linked to the previous one through cryptographic hashes, creating an immutable record. The key innovation of blockchain is its ability to achieve consensus in a decentralized network without requiring trust in any single entity. This is typically achieved through consensus mechanisms like Proof of Work or Proof of Stake. When a new transaction occurs, it is broadcast to a network of computers (nodes) for validation. Once validated, the transaction is combined with others to create a new block, which is then added to the chain. This process ensures transparency, security, and resistance to tampering, making blockchain suitable for various applications beyond finance, including supply chain management, voting systems, and digital identity verification."
    },
    {
        "prompt": "What are the main theories about the origin of the universe?",
        "context": "The origin of the universe has been a subject of intense scientific inquiry and philosophical debate for centuries. Currently, the most widely accepted scientific theory is the Big Bang model, which proposes that the universe began as an infinitely dense and hot singularity about 13.8 billion years ago, and has been expanding and cooling ever since. This theory is supported by observational evidence such as the cosmic microwave background radiation and the abundance of light elements in the universe. However, questions remain about what happened before the Big Bang and what caused it. Other theories include the Steady State theory, which suggests that the universe has always existed and is constantly creating new matter as it expands, though this theory has fallen out of favor due to lack of supporting evidence. More speculative ideas include the concept of a cyclic universe, where big bangs and big crunches occur in an endless cycle, and the idea of a multiverse, where our universe is just one of many existing universes."
    },
    {
        "prompt": "Describe the water cycle and its importance for life on Earth.",
        "context": "The water cycle, also known as the hydrologic cycle, is the continuous movement of water within the Earth and atmosphere. It is a complex system involving the processes of evaporation, transpiration, condensation, precipitation, and runoff. Water evaporates from the Earth's surface, primarily from oceans, lakes, and rivers, due to solar energy. Plants also release water vapor through transpiration. As this water vapor rises in the atmosphere, it cools and condenses to form clouds. Eventually, it falls back to Earth as precipitation in the form of rain, snow, or hail. Some of this water flows over the land as surface runoff, returning to bodies of water, while some seeps into the ground, replenishing groundwater reserves. This cycle is crucial for life on Earth as it redistributes water around the globe, shapes landscapes through erosion and deposition, regulates global temperatures, and provides fresh water essential for all living organisms. Understanding and protecting the water cycle is vital for managing water resources and addressing environmental challenges like climate change and water scarcity."
    },
    {
        "prompt": "What are the major differences between capitalism and socialism?",
        "context": "Capitalism and socialism are two contrasting economic and political systems that have shaped much of modern history. Capitalism is characterized by private ownership of the means of production, where individuals or corporations own businesses and property. It operates on the principles of free market competition, with prices determined by supply and demand. Profit is a key motivator in capitalist systems, and government intervention is generally limited. In contrast, socialism advocates for collective or governmental ownership and administration of the means of production and distribution of goods. It aims to create a more equitable society by reducing class distinctions and distributing resources according to need rather than ability to pay. In socialist systems, the government plays a much larger role in economic planning and the provision of social services. While pure forms of either system are rare, many countries adopt mixed economies incorporating elements of both capitalism and socialism to varying degrees."
    },
    {
        "prompt": "How does the human brain process and store memories?",
        "context": "The human brain's ability to process and store memories is a complex and fascinating process involving various regions and neural networks. When we experience something, sensory information is first processed in the relevant cortical areas (e.g., visual cortex for sight, auditory cortex for sound). This information is then integrated in the hippocampus, a seahorse-shaped structure crucial for forming new memories. The hippocampus helps bind different aspects of an experience into a cohesive memory and plays a key role in converting short-term memories into long-term ones. Long-term memories are thought to be stored through changes in synaptic connections between neurons across widespread areas of the cortex. This process, known as consolidation, can take days or even years. Different types of memories (e.g., episodic, semantic, procedural) involve different brain regions and processes. The retrieval of memories involves reactivating these neural patterns, which explains why memories can be influenced by our current state and environment. Understanding these processes is crucial for addressing memory-related disorders and developing potential therapies."
    },
    {
        "prompt": "What are the main challenges in space exploration?",
        "context": "Space exploration, while offering immense potential for scientific discovery and technological advancement, faces numerous challenges. One of the primary obstacles is the hostile environment of space itself. The vacuum of space, extreme temperatures, and harmful radiation pose significant risks to both human astronauts and sensitive equipment. Prolonged exposure to microgravity can lead to health issues for astronauts, including muscle atrophy and bone density loss. Logistical challenges are also substantial: the enormous distances involved in space travel require advanced propulsion systems and careful resource management. Launching payloads into orbit remains extremely expensive, limiting the scope and frequency of missions. Communication delays become increasingly problematic for deep space missions, necessitating a high degree of autonomy in spacecraft and rovers. Additionally, space debris orbiting Earth poses a growing threat to satellites and spacecraft. As we look towards long-term goals like establishing bases on the Moon or Mars, we face new challenges in creating sustainable habitats and managing psychological effects on crew members during extended missions. Despite these obstacles, ongoing research and technological innovations continue to push the boundaries of what's possible in space exploration."
    },
    {
        "prompt": "Explain the concept of supply and demand in economics.",
        "context": "Supply and demand is a fundamental concept in economics that describes how the price and quantity of a good or service in a market are determined through the interaction between buyers and sellers. The law of demand states that, all else being equal, as the price of a product increases, the quantity demanded by consumers decreases. This is typically represented by a downward-sloping demand curve. Conversely, the law of supply states that as the price of a product increases, the quantity that producers are willing to supply increases, represented by an upward-sloping supply curve. The point where these two curves intersect is called the equilibrium point, determining the market price and quantity. This model helps explain how prices fluctuate in response to changes in supply or demand. For instance, if demand increases while supply remains constant, prices will rise. If supply increases while demand remains constant, prices will fall. Understanding supply and demand is crucial for analyzing market behavior, predicting price changes, and formulating economic policies."
    },
    {
        "prompt": "What are the key features of a democratic government?",
        "context": "Democratic government is a system of governance based on the principle of rule by the people. While democracies can take various forms, they typically share several key features. First and foremost is the concept of free and fair elections, where citizens have the right to vote for their representatives at regular intervals. This is closely tied to the principle of political pluralism, allowing for multiple political parties and viewpoints to compete for power. The protection of individual rights and civil liberties, such as freedom of speech, press, and assembly, is another crucial aspect of democracy. Separation of powers is often implemented to prevent the concentration of power, typically dividing government into executive, legislative, and judicial branches that provide checks and balances on each other. The rule of law, ensuring that all citizens, including those in power, are equally subject to the law, is fundamental to democratic governance. Transparency and accountability in government operations, often facilitated by a free press and active civil society, help maintain democratic principles. Additionally, many democracies emphasize the protection of minority rights and the concept of majority rule with minority rights, aiming to balance the will of the majority with the fundamental rights of all citizens."
    },
    {
        "prompt": "How do vaccines work to prevent diseases?",
        "context": "Vaccines are one of the most effective tools in preventing infectious diseases, working by harnessing the body's own immune system. When a pathogen such as a virus or bacteria enters the body, the immune system responds by producing antibodies specific to that pathogen. These antibodies help neutralize or destroy the invader. Vaccines mimic this natural process by introducing a harmless form of the pathogen – either weakened, inactivated, or just a part of it – into the body. This stimulates the immune system to produce antibodies and memory cells specific to that pathogen, without causing the actual disease. If the vaccinated person later encounters the real pathogen, their immune system can quickly recognize it and mount a rapid and effective response, often preventing the disease entirely or reducing its severity. Some vaccines require multiple doses or periodic boosters to maintain immunity. The concept of herd immunity is also important in vaccination strategies: when a large portion of a population is vaccinated, it becomes difficult for the pathogen to spread, indirectly protecting those who cannot be vaccinated. Advances in vaccine technology, such as mRNA vaccines, are expanding our ability to rapidly develop vaccines for new threats."
    },
    {
        "prompt": "What are the main theories of human evolution?",
        "context": "Human evolution is the study of the biological and cultural development of our species, Homo sapiens, and our ancestors. The main scientific theory explaining human evolution is based on Darwin's theory of evolution by natural selection, adapted to incorporate modern genetic understanding. This theory proposes that humans evolved from earlier primate species over millions of years. Key ideas include the concept of common ancestry, suggesting that humans share a common ancestor with other primates, particularly the great apes. The 'Out of Africa' theory posits that modern humans originated in Africa and then migrated to other parts of the world. Fossil evidence has revealed a series of intermediate species, such as Australopithecus, Homo habilis, and Homo erectus, showing gradual changes in features like brain size, bipedalism, and tool use. Recent discoveries and genetic studies have complicated this picture, suggesting interbreeding between different human species (like Homo sapiens and Neanderthals) and the possibility of multiple migrations out of Africa. Ongoing research in paleontology, genetics, and archaeology continues to refine our understanding of human evolution, often challenging previous assumptions and revealing the complex history of our species."
    },
    {
        "prompt": "Describe the process of plate tectonics and its effects on Earth.",
        "context": "Plate tectonics is a fundamental theory in geology that explains the large-scale motions of Earth's lithosphere. The theory proposes that Earth's outer layer is divided into several large, rigid plates that move relative to one another. These plates float on the semi-fluid asthenosphere beneath them and are driven by convection currents in the mantle. Plate boundaries are classified into three types: divergent boundaries, where plates move apart and new crust is created; convergent boundaries, where plates collide, leading to subduction or mountain building; and transform boundaries, where plates slide past each other horizontally. The process of plate tectonics has profound effects on Earth's surface and internal structure. It is responsible for the formation of mountain ranges, ocean basins, and island arcs. It also plays a crucial role in the rock cycle, volcanic activity, and earthquake occurrence. Over geological time, plate tectonics has influenced climate patterns, ocean currents, and the distribution of flora and fauna across the globe. Understanding plate tectonics is essential for predicting geological hazards, explaining the distribution of natural resources, and comprehending Earth's long-term geological history."
    },
    {
        "prompt": "What are the primary causes of biodiversity loss?",
        "context": "Biodiversity loss, the decline in the variety of life forms on Earth, is a critical environmental issue with far-reaching consequences for ecosystems and human well-being. Several interconnected factors contribute to this loss. Habitat destruction and fragmentation, often due to human activities like deforestation, urbanization, and agricultural expansion, is a primary driver. Climate change is increasingly recognized as a major threat, altering ecosystems faster than many species can adapt. Overexploitation of natural resources, including overfishing and poaching, directly reduces populations of many species. Pollution, including chemical runoff, plastic waste, and air pollution, degrades habitats and harms wildlife. The introduction of invasive species, often facilitated by human activities, can disrupt local ecosystems and outcompete native species. Additionally, the spread of diseases, sometimes exacerbated by climate change and habitat stress, can devastate populations of certain species. These factors often interact and compound each other's effects, accelerating the rate of biodiversity loss. Addressing this crisis requires comprehensive conservation strategies, sustainable resource management, and global cooperation to mitigate human impacts on natural ecosystems."
    },
]

@dataclass
class RequestResult:
    output_tokens: int
    latency: float
    ttft: float
    decode_tps: float


_METRIC_LINE = re.compile(r"^((?:vllm|llamacpp):[A-Za-z0-9_]+)(?:\{(.*?)\})?\s+([0-9.eE+-]+)\s*$")
_POSITION_LABEL = re.compile(r'position="(\d+)"')
_CACHE_CONFIG_LINE = re.compile(r"^vllm:cache_config_info\{(.*)\}\s")
_LABEL_PAIR = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)="((?:[^"\\]|\\.)*)"')


def server_base_url(api_url: str) -> str:
    return api_url.rstrip("/").removesuffix("/v1")


def parse_vllm_metrics(text: str) -> dict[str, float]:
    """Sum samples by metric name across engines; per-position samples keyed as name[pos]."""
    metrics: dict[str, float] = {}
    for line in text.splitlines():
        m = _METRIC_LINE.match(line)
        if not m:
            continue
        name, labels, value = m.group(1), m.group(2) or "", float(m.group(3))
        pos = _POSITION_LABEL.search(labels)
        key = f"{name}[{pos.group(1)}]" if pos else name
        metrics[key] = metrics.get(key, 0.0) + value
    return metrics


def parse_cache_config(metrics_text: str) -> dict[str, str] | None:
    """Extract the CacheConfig labels vLLM publishes on the cache_config_info gauge."""
    for line in metrics_text.splitlines():
        m = _CACHE_CONFIG_LINE.match(line)
        if m:
            return {k: v for k, v in _LABEL_PAIR.findall(m.group(1)) if k != "engine"}
    return None


async def fetch_text(url: str, api_key: str | None) -> str | None:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPError as e:
        log.warning(f"Could not fetch {url}: {e}")
        return None


async def discover_metrics(base_url: str, model: str, api_key: str | None) -> tuple[str | None, str | None, str | None]:
    """Find a vLLM or llama.cpp metrics endpoint, directly or behind llama-swap.

    Returns (backend, metrics_url, first_snapshot_text)."""
    for url in (f"{base_url}/metrics", f"{base_url}/upstream/{model}/metrics"):
        text = await fetch_text(url, api_key)
        if not text:
            continue
        if "vllm:" in text:
            return "vllm", url, text
        if "llamacpp:" in text:
            return "llamacpp", url, text
    log.warning("No vLLM or llama.cpp metrics endpoint found; server_metrics will be null")
    return None, None, None


async def fetch_json(url: str, api_key: str | None) -> dict | None:
    body = await fetch_text(url, api_key)
    if body:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            log.warning(f"Non-JSON response from {url}")
    return None


async def fetch_server_info(backend: str | None, base_url: str, metrics_url: str | None, api_key: str | None, metrics_text: str | None) -> dict:
    """Engine settings observable over HTTP; full CLI args are only in the server's startup log."""
    info: dict = {"backend": backend}
    if backend == "vllm":
        version = await fetch_json(f"{base_url}/version", api_key)
        info["vllm_version"] = version.get("version") if version else None
        info["cache_config"] = parse_cache_config(metrics_text) if metrics_text else None
    elif backend == "llamacpp" and metrics_url:
        props = await fetch_json(metrics_url.removesuffix("/metrics") + "/props", api_key)
        if props:
            info["llamacpp_build"] = props.get("build_info")
            info["model_path"] = props.get("model_path")
            info["n_ctx"] = props.get("default_generation_settings", {}).get("n_ctx")
            info["total_slots"] = props.get("total_slots")
    return info


def server_metrics_delta(backend: str | None, before: dict[str, float] | None, after: dict[str, float] | None) -> dict | None:
    """Server-side counters attributable to this run (delta of two /metrics snapshots)."""
    if backend is None or before is None or after is None:
        return None
    prefix = backend

    def delta(name: str) -> float:
        return after.get(f"{prefix}:{name}", 0.0) - before.get(f"{prefix}:{name}", 0.0)

    if backend == "vllm":
        prompt_tokens = delta("prompt_tokens_total")
        generation_tokens = delta("generation_tokens_total")
        cache_queries = delta("prefix_cache_queries_total")
        cache_hits = delta("prefix_cache_hits_total")
    else:
        # llama.cpp: prompt_tokens_total excludes cached tokens; no explicit query counter
        cache_hits = delta("prompt_tokens_cached_total")
        prompt_tokens = delta("prompt_tokens_total") + cache_hits
        generation_tokens = delta("tokens_predicted_total")
        cache_queries = prompt_tokens

    result = {
        "prompt_tokens": int(prompt_tokens),
        "generation_tokens": int(generation_tokens),
        "prefix_cache": {
            "queried_tokens": int(cache_queries),
            "hit_tokens": int(cache_hits),
            "hit_rate": cache_hits / cache_queries if cache_queries else None,
        },
        "speculative_decoding": None,
    }

    drafts = delta("spec_decode_num_drafts_total")
    draft_tokens = delta("spec_decode_num_draft_tokens_total")
    accepted = delta("spec_decode_num_accepted_tokens_total")
    if drafts:
        per_pos_prefix = f"{prefix}:spec_decode_num_accepted_tokens_per_pos_total["
        per_pos_keys = sorted(
            (k for k in after if k.startswith(per_pos_prefix)),
            key=lambda k: int(k[k.index("[") + 1:-1]),
        )
        result["speculative_decoding"] = {
            "drafts": int(drafts),
            "draft_tokens": int(draft_tokens),
            "accepted_tokens": int(accepted),
            "draft_acceptance_rate": accepted / draft_tokens if draft_tokens else None,
            # +1 for the bonus token the target model emits each draft step
            "mean_acceptance_length": 1 + accepted / drafts,
            "per_position_acceptance_rate": [
                round((after.get(k, 0.0) - before.get(k, 0.0)) / drafts, 4) for k in per_pos_keys
            ] or None,
        }
    return result


async def make_request(client: AsyncOpenAI, model: str, output_tokens: int, request_timeout: float, use_long_context: bool) -> RequestResult | None:
    if use_long_context:
        prompt_pair = random.choice(LONG_PROMPT_PAIRS)
        content = prompt_pair["context"] + "\n\n" + prompt_pair["prompt"]
    else:
        content = random.choice(SHORT_PROMPTS)

    start = time.perf_counter()
    try:
        async with asyncio.timeout(request_timeout):
            stream = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=output_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            first_token_at = None
            chunk_count = 0
            usage = None
            async with stream:
                async for chunk in stream:
                    if chunk.usage:
                        usage = chunk.usage
                    delta = chunk.choices[0].delta if chunk.choices else None
                    # Reasoning models stream reasoning/reasoning_content before content
                    if delta and (delta.content or getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)):
                        chunk_count += 1
                        if first_token_at is None:
                            first_token_at = time.perf_counter()

        end = time.perf_counter()
        # Chunk count undercounts with speculative decoding (multiple tokens per chunk)
        completion_tokens = usage.completion_tokens if usage else chunk_count
        latency = end - start
        ttft = (first_token_at - start) if first_token_at else latency
        decode_time = (end - first_token_at) if first_token_at else latency
        decode_tps = completion_tokens / decode_time if decode_time > 0 else 0.0
        return RequestResult(completion_tokens, latency, ttft, decode_tps)

    except TimeoutError:
        log.warning(f"Request timed out after {request_timeout} seconds")
    except Exception as e:  # noqa: BLE001 - one failed request must not abort the run
        log.error(f"Error during request: {e}")
    return None


async def worker(client: AsyncOpenAI, queue: asyncio.Queue, results: list[RequestResult], model: str, output_tokens: int, request_timeout: float, use_long_context: bool) -> None:
    while True:
        task_id = await queue.get()
        if task_id is None:
            break
        log.info(f"Starting request {task_id}")
        result = await make_request(client, model, output_tokens, request_timeout, use_long_context)
        if result:
            results.append(result)
        else:
            log.warning(f"Request {task_id} failed")
        log.info(f"Finished request {task_id}")


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summarise(values: list[float], reverse: bool = False) -> dict[str, float | None]:
    return {
        "average": sum(values) / len(values) if values else 0,
        "p50": percentile(values, 50),
        "p95": percentile(values, 5 if reverse else 95),
        "p99": percentile(values, 1 if reverse else 99),
    }


async def run_benchmark(num_requests, concurrency, request_timeout, output_tokens, base_url, api_key=None, use_long_context=False, model: str | None = None, warmup: bool = True):
    # The SDK requires a non-empty key even for unauthenticated servers
    client = AsyncOpenAI(base_url=base_url, api_key=api_key or "EMPTY")
    try:
        models = await client.models.list()
        model_entry = next((m for m in models.data if m.id == model), models.data[0] if models.data else None)
        if model is None and model_entry:
            model = model_entry.id
            log.info(f"Benchmarking model: {model}")
        if model is None:
            raise RuntimeError("No --model given and the server reported no models")

        if warmup:
            # Absorbs model load (llama-swap loads lazily) so it doesn't pollute results;
            # runs before the metrics snapshot so its tokens stay out of the server deltas
            warmup_start = time.perf_counter()
            result = await make_request(client, model, 16, max(request_timeout, 600), use_long_context)
            status = "done" if result else "FAILED"
            log.info(f"Warmup request {status} in {time.perf_counter() - warmup_start:.1f} s")

        server_url = server_base_url(base_url)
        backend, metrics_url, metrics_text_before = await discover_metrics(server_url, model, api_key)
        metrics_before = parse_vllm_metrics(metrics_text_before) if metrics_text_before else None
        server_info = await fetch_server_info(backend, server_url, metrics_url, api_key, metrics_text_before)
        if model_entry:
            server_info.setdefault("model_path", getattr(model_entry, "root", None))
            max_len = getattr(model_entry, "max_model_len", None) or getattr(model_entry, "context_length", None)
            server_info.setdefault("max_model_len", max_len)

        queue: asyncio.Queue[int | None] = asyncio.Queue()
        results: list[RequestResult] = []
        for i in range(num_requests):
            queue.put_nowait(i)
        for _ in range(concurrency):
            queue.put_nowait(None)

        start = time.perf_counter()
        async with asyncio.TaskGroup() as tg:
            for _ in range(concurrency):
                tg.create_task(worker(client, queue, results, model, output_tokens, request_timeout, use_long_context))
        total_elapsed = time.perf_counter() - start

        metrics_text_after = await fetch_text(metrics_url, api_key) if metrics_url else None
        metrics_after = parse_vllm_metrics(metrics_text_after) if metrics_text_after else None
    finally:
        await client.close()

    total_output_tokens = sum(r.output_tokens for r in results)
    latency = summarise([r.latency for r in results])
    decode_tps = summarise([r.decode_tps for r in results], reverse=True)
    ttft = summarise([r.ttft for r in results])
    aggregate_tps = total_output_tokens / total_elapsed if total_elapsed > 0 else 0
    return {
        "model": model,
        # The client-experienced numbers: per-stream decode rate and TTFT
        "summary": {
            "client_tokens_per_second_p50": decode_tps["p50"],
            "aggregate_tokens_per_second": aggregate_tps,
            "time_to_first_token_p50": ttft["p50"],
            "latency_p50": latency["p50"],
        },
        "server": server_info,
        "total_requests": num_requests,
        "successful_requests": len(results),
        "concurrency": concurrency,
        "request_timeout": request_timeout,
        "max_output_tokens": output_tokens,
        "use_long_context": use_long_context,
        "total_time": total_elapsed,
        "requests_per_second": len(results) / total_elapsed if total_elapsed > 0 else 0,
        "total_output_tokens": total_output_tokens,
        "aggregate_output_tokens_per_second": aggregate_tps,
        "latency": latency,
        "decode_tokens_per_second": decode_tps,
        "time_to_first_token": ttft,
        "server_metrics": server_metrics_delta(backend, metrics_before, metrics_after),
    }


def print_results(results):
    print(json.dumps(results, indent=2))


def save_results(results: dict, out_dir: Path = Path("benchmark_results")) -> Path:
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    model_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", results["model"])
    path = out_dir / f"{stamp}_{model_slug}.json"
    path.write_text(json.dumps(results, indent=2))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark an OpenAI-compatible LLM server (vLLM, llama.cpp, llama-swap)")
    parser.add_argument("--num_requests", type=int, required=True, help="Number of requests to make")
    parser.add_argument("--concurrency", type=int, required=True, help="Number of concurrent requests")
    parser.add_argument("--request_timeout", type=int, default=120, help="Timeout for each request in seconds (default: 120)")
    parser.add_argument("--output_tokens", type=int, default=50, help="Max output tokens per request (default: 50)")
    parser.add_argument("--base_url", type=str, required=True, help="Base URL of any OpenAI-compatible server (vLLM, llama.cpp, llama-swap), e.g. https://host/v1")
    parser.add_argument("--api_key", type=str, default=None, help="API key, if the server requires one")
    parser.add_argument("--model", type=str, default=None, help="Model name (default: first model served)")
    parser.add_argument("--use_long_context", action="store_true", help="Use long context prompt pairs instead of short prompts")
    parser.add_argument("--no_warmup", action="store_true", help="Skip the untimed warmup request that absorbs model load")
    parser.add_argument("--no_save", action="store_true", help="Do not write results to benchmark_results/")
    args = parser.parse_args()

    results = asyncio.run(run_benchmark(args.num_requests, args.concurrency, args.request_timeout, args.output_tokens, args.base_url, args.api_key, args.use_long_context, model=args.model, warmup=not args.no_warmup))
    print_results(results)
    s = results["summary"]
    if results["successful_requests"] == 0:
        log.error("All requests failed; no summary to report")
        return
    log.info(
        f"Client tokens/s (p50): {s['client_tokens_per_second_p50']:.1f} | "
        f"aggregate: {s['aggregate_tokens_per_second']:.1f} | "
        f"TTFT p50: {s['time_to_first_token_p50'] * 1000:.0f} ms"
    )
    if not args.no_save:
        saved = save_results(results)
        log.info(f"Results saved to {saved}")
        try:
            from generate_report import build_report

            built = build_report(saved.parent)
            if built:
                log.info(f"Report updated: {built[0]} ({built[1]} runs)")
        except ImportError:
            log.warning("generate_report.py not found alongside this script; report not updated")


if __name__ == "__main__":
    main()

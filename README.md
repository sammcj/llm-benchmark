# LLM Benchmark

Benchmarks LLMs served over an OpenAI-compatible API (vLLM, llama.cpp, llama-swap). Measures the throughput and latency a client actually experiences, and captures server-side metrics and engine config so tuning changes can be correlated with results.

## Requirements

Python 3.12+ and [uv](https://docs.astral.sh/uv/) (dependencies are declared inline via PEP 723), or `pip install openai httpx`.

## Usage

```
uv run llm_benchmark.py --num_requests 100 --concurrency 10 --output_tokens 100 --base_url "http://localhost:8000/v1"
```

Example: Run a comparison of single-stream decode benchmarks, against vLLM and llama.cpp/llama-swap:

```shell
uv run llm_benchmark.py --num_requests 5 --concurrency 1 --output_tokens 4096 --base_url "https://vllm.your.domain/v1" --model "Qwen3.8-27B-int4-AutoRound" --use_long_context

uv run llm_benchmark.py --num_requests 5 --concurrency 1 --output_tokens 4096 --base_url "https://llamaswap.your.domain/v1" --model "qwen3-8-27b-ud-q5kxl-192k" --use_long_context
```

Flags:

- `--num_requests` / `--concurrency`: total requests and how many run in parallel
- `--output_tokens`: max tokens per request
- `--base_url`: OpenAI-compatible endpoint, e.g. `http://localhost:8000/v1`
- `--model`: defaults to the first model the server reports
- `--api_key`: only needed if the server requires one
- `--request_timeout`: seconds per request (default 120)
- `--use_long_context`: ~200-token prompts instead of short questions
- `--no_warmup`: skip the untimed warmup request that absorbs model load
- `--no_save`: print results without writing them or refreshing the report

`uv run run_benchmarks.py --base_url ...` sweeps concurrency 1, 10, 50 and 100 in one go.

## Results

Each run prints JSON with a `summary` block up top (client tokens/s p50, aggregate tokens/s, TTFT) and saves to `benchmark_results/<timestamp>_<model>.json` (gitignored). Measurement details worth knowing:

- Token counts come from API `usage`, not stream chunk counts, so they stay correct under speculative decoding
- TTFT counts the first `reasoning` or `content` delta (reasoning-model aware); decode tokens/s excludes TTFT
- `server`: detected backend and its observable settings - vLLM version and cache config, or llama.cpp build, n_ctx and slots
- `server_metrics`: delta of the server's Prometheus counters over the run - prompt/generation tokens, prefix cache hit rate, speculative decoding acceptance. The endpoint is auto-detected: `/metrics`, or llama-swap's `/upstream/<model>/metrics`

## Report

Every saved run rebuilds `benchmark_results/report.html`: a self-contained static page (no external dependencies, no Node) with per-metric bar charts, model/backend/concurrency filters, an A/B run comparison with per-metric deltas and configuration diff, and a table with expandable per-run JSON. Light and dark mode supported.

Build it manually with `uv run generate_report.py --open` (`--results_dir` and `--output` override the defaults).

## License

Apache 2.0 - see [LICENSE](LICENSE).

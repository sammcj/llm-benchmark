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
from pathlib import Path

from generate_report import build_report
from llm_benchmark import run_benchmark, save_results

CONFIGURATIONS = [
    {"num_requests": 10, "concurrency": 1, "output_tokens": 100},
    {"num_requests": 100, "concurrency": 10, "output_tokens": 100},
    {"num_requests": 500, "concurrency": 50, "output_tokens": 100},
    {"num_requests": 1000, "concurrency": 100, "output_tokens": 100},
]


async def run_all_benchmarks(base_url, api_key, use_long_context):
    all_results = []
    for config in CONFIGURATIONS:
        print(f"Running benchmark with concurrency {config['concurrency']}...")
        results = await run_benchmark(config["num_requests"], config["concurrency"], 120, config["output_tokens"], base_url, api_key, use_long_context)
        print(f"Saved {save_results(results)}")
        all_results.append(results)
        await asyncio.sleep(5)  # Let the system cool down between runs
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Run LLM benchmarks with various configurations")
    parser.add_argument("--base_url", type=str, required=True, help="Base URL of the OpenAI-compatible server")
    parser.add_argument("--api_key", type=str, default=None, help="API key, if the server requires one")
    parser.add_argument("--use_long_context", action="store_true", help="Use long context prompt pairs instead of short prompts")
    args = parser.parse_args()

    all_results = asyncio.run(run_all_benchmarks(args.base_url, args.api_key, args.use_long_context))

    out_path = Path("benchmark_results/benchmark_results.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"Combined results saved to {out_path}")
    built = build_report(out_path.parent)
    if built:
        print(f"Report updated: {built[0]} ({built[1]} runs)")


if __name__ == "__main__":
    main()

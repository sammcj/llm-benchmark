# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate a static HTML report comparing saved benchmark runs."""
import argparse
import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path

STAMP_RE = re.compile(r"^(\d{8}-\d{6})_")


def load_runs(results_dir: Path) -> list[dict]:
    runs = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"Skipping unreadable {path}")
            continue
        items = data if isinstance(data, list) else [data]
        m = STAMP_RE.match(path.stem)
        local_tz = datetime.now().astimezone().tzinfo
        stamp = (
            datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").replace(tzinfo=local_tz)
            if m
            else datetime.fromtimestamp(path.stat().st_mtime, tz=local_tz)
        )
        for item in items:
            if isinstance(item, dict) and "total_requests" in item:
                item["_file"] = path.name
                item["_timestamp"] = stamp.strftime("%Y-%m-%d %H:%M:%S")
                runs.append(item)
    runs.sort(key=lambda r: r["_timestamp"])
    return runs


def build_report(results_dir: Path, output: Path | None = None) -> tuple[Path, int] | None:
    """Render all saved runs into a static HTML report; returns (path, run count) or None if no runs."""
    runs = load_runs(results_dir)
    if not runs:
        return None
    output = output or results_dir / "report.html"
    template = (Path(__file__).parent / "report_template.html").read_text()
    output.parent.mkdir(exist_ok=True)
    output.write_text(template.replace("__DATA__", json.dumps(runs)))
    return output, len(runs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an HTML comparison report from saved benchmark runs")
    parser.add_argument("--results_dir", type=Path, default=Path("benchmark_results"), help="Directory of benchmark JSON files")
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/report.html"), help="Output HTML path")
    parser.add_argument("--open", action="store_true", help="Open the report in a browser")
    args = parser.parse_args()

    built = build_report(args.results_dir, args.output)
    if not built:
        print(f"No benchmark JSON files found in {args.results_dir}")
        return
    path, count = built
    print(f"Report with {count} runs written to {path}")
    if args.open:
        webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    main()

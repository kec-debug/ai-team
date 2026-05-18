"""CLI: python -m app.reports [--run-dir PATH | --latest] [--reports-dir DIR]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.reports.dry_run_analyzer import analyze_run, find_latest_run_dir, write_analysis_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze dry-run reports")
    parser.add_argument("--run-dir", type=Path, help="Specific run directory")
    parser.add_argument("--latest", action="store_true", help="Analyze the latest run")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports") / "dry_run",
        help="Base reports directory (default: reports/dry_run)",
    )
    args = parser.parse_args(argv)

    if args.run_dir and args.latest:
        parser.error("specify either --run-dir or --latest, not both")
    if not args.run_dir and not args.latest:
        args.latest = True

    if args.latest:
        run_dir = find_latest_run_dir(args.reports_dir)
        if run_dir is None:
            print(f"no run directories found under {args.reports_dir}", file=sys.stderr)
            return 1
    else:
        run_dir = args.run_dir
        if not run_dir.is_dir():
            print(f"run_dir not found: {run_dir}", file=sys.stderr)
            return 1

    try:
        result = analyze_run(run_dir)
        paths = write_analysis_files(result)
    except Exception as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

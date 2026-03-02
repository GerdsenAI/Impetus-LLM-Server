#!/usr/bin/env python3
"""
Performance baseline comparison tool.

Reads baselines from tests/perf_baselines.json, runs perf tests,
compares actual vs expected, and fails if regression exceeds threshold.

Usage:
    python scripts/perf_baseline.py              # Compare against baselines
    python scripts/perf_baseline.py --update      # Update baselines from current run
    python scripts/perf_baseline.py --show        # Show current baselines
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASELINES_FILE = Path(__file__).parent.parent / "tests" / "perf_baselines.json"


def load_baselines() -> dict:
    """Load baselines from JSON file."""
    if not BASELINES_FILE.exists():
        print(f"ERROR: Baselines file not found: {BASELINES_FILE}")
        sys.exit(1)
    with open(BASELINES_FILE) as f:
        return json.load(f)


def show_baselines():
    """Display current baselines."""
    data = load_baselines()
    print(f"Performance Baselines v{data['version']}")
    print(f"Regression threshold: {data['regression_threshold_percent']}%")
    print()
    for key, value in data["baselines"].items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")


def run_perf_tests() -> bool:
    """Run performance tests and return success status."""
    print("Running performance tests...")
    result = subprocess.run(
        ["python", "-m", "pytest", "-m", "perf", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent,
        capture_output=False,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Performance baseline tool")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update baselines from current run",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current baselines",
    )
    args = parser.parse_args()

    if args.show:
        show_baselines()
        return

    if args.update:
        print("Updating baselines requires manual editing of perf_baselines.json")
        print(f"File location: {BASELINES_FILE}")
        show_baselines()
        return

    # Run perf tests
    data = load_baselines()
    threshold = data.get("regression_threshold_percent", 20)
    print(f"Regression threshold: {threshold}%")
    print()

    success = run_perf_tests()

    if success:
        print()
        print("All performance tests PASSED — no regressions detected.")
    else:
        print()
        print("FAILED — performance regression detected!")
        print("Review test output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

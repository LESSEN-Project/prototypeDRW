#!/usr/bin/env python
"""Judging pipeline for the study, one command, resumable:

    1. collect.py   -> results_study/answers.csv
    2. judge.py     llama3.3:70b over every unique (ground truth, answer) pair   (primary)
    3. judge.py     gpt-oss:20b over the same pairs                             (agreement check)
    4. aggregate.py -> results_study/summary.md

Each judge appends to its own judged_<judge>.jsonl and skips pairs already
judged, so Ctrl+C and rerun is safe. Needs the tunnel to limmy and free GPUs
(the 70b spans both cards).

    venv\\Scripts\\python experiments\\contrastive\\run_judging.py
    venv\\Scripts\\python experiments\\contrastive\\run_judging.py --skip-second   # 70b only
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable
STUDY = HERE / "results_study"


def step(title: str, cmd: list) -> None:
    print(f"\n=== {time.strftime('%H:%M:%S')} {title}\n    {' '.join(str(c) for c in cmd)}", flush=True)
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    if rc != 0:
        sys.exit(f"step failed (exit {rc}): {title}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(STUDY))
    ap.add_argument("--primary", default="llama3.3:70b")
    ap.add_argument("--second", default="gpt-oss:20b")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--skip-second", action="store_true")
    args = ap.parse_args()
    results = Path(args.results)
    answers = results / "answers.csv"

    t0 = time.time()
    step("collect answers", [PY, HERE / "collect.py", "--results", results])
    step(f"judge with {args.primary}", [PY, HERE / "judge.py", "--answers", answers,
                                        "--judge", args.primary, "--parallel", str(args.parallel)])
    if not args.skip_second:
        step(f"judge with {args.second}", [PY, HERE / "judge.py", "--answers", answers,
                                           "--judge", args.second, "--parallel", str(args.parallel)])
    tag = args.primary.split("/")[-1].replace(":", "-")
    step("aggregate", [PY, HERE / "aggregate.py", "--results", results, "--judge", tag])
    print(f"\nall done in {(time.time() - t0)/3600:.2f} h -> {results / 'summary.md'}")


if __name__ == "__main__":
    main()

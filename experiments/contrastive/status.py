#!/usr/bin/env python
"""One-screen status of the contrastive study: what finished, what failed, what to run next.

    venv\\Scripts\\python experiments\\contrastive\\status.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_grid  # noqa: E402
import run_study  # noqa: E402

STUDY_ROOT = run_study.STUDY_ROOT
EXPECTED_CASES = 124
INFRA = "utter_internal_error_rasa"


def driver_running() -> bool:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_study.py*' -and $_.Name -like 'python*' }).Count"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return int(out or 0) > 0
    except Exception:
        return False


def rasa_processes() -> int:
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "@(Get-Process rasa -ErrorAction SilentlyContinue).Count"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return int(out or 0)
    except Exception:
        return -1


def run_health(run_dir: Path) -> dict:
    """cases seen, infra errors, and whether both result files exist."""
    passed, failed = run_dir / "e2e_results_passed.yml", run_dir / "e2e_results_failed.yml"
    complete = passed.exists() and failed.exists() and (run_dir / "meta.json").exists()
    cases = infra = 0
    for f in (passed, failed):
        if f.exists():
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for r in data.get("test_results", []) or []:
                cases += 1
                a = ((r.get("assertion_failure") or {}).get("assertion") or {})
                if a.get("utter_name") == INFRA and a.get("type") == "bot_did_not_utter":
                    infra += 1
    return {"complete": complete, "cases": cases, "infra": infra}


def main() -> None:
    print(f"study status at {time.strftime('%Y-%m-%d %H:%M')}   root: {STUDY_ROOT}\n")
    running = driver_running()
    nproc = rasa_processes()
    print(f"driver running: {'YES' if running else 'no'}   rasa processes: {nproc}\n")

    problems = []
    total_expected = total_done = 0
    print(f"{'phase':9s} {'model':44s} {'done':>9s} {'in-flight':>9s} {'min/run':>8s} {'infra':>6s}  note")
    for name, model, cset, reps, conc, cmd in run_study.PHASES:
        expected = len(run_grid.CONDITION_SETS[cset]) * reps
        total_expected += expected
        phase_dir = STUDY_ROOT / run_grid.model_tag(model)
        if not phase_dir.exists():
            print(f"{name:9s} {model[:44]:44s} {0:>5d}/{expected:<3d} {'-':>9s} {'-':>8s} {'-':>6s}  not started")
            continue
        done, inflight, secs, infra, short = 0, 0, [], 0, []
        for d in sorted(p for p in phase_dir.iterdir() if p.is_dir() and "_r" in p.name):
            h = run_health(d)
            if h["complete"]:
                done += 1
                secs.append(json.loads((d / "meta.json").read_text())["seconds"])
                infra += h["infra"]
                if h["cases"] != EXPECTED_CASES:
                    short.append(f"{d.name}({h['cases']} cases)")
            else:
                inflight += 1
        total_done += done
        note = []
        if short:
            note.append("incomplete: " + ", ".join(short[:3]))
            problems.append(f"{name}: runs with missing cases -> delete those dirs and relaunch run_study.py")
        if infra:
            note.append(f"{infra} internal errors")
            problems.append(f"{name}: {infra} internal-error cases (tunnel or VRAM trouble during the run?)")
        if done < expected and not running:
            problems.append(f"{name}: {expected - done} runs missing and the driver is not running -> relaunch run_study.py")
        mean = f"{sum(secs)/len(secs)/60:.1f}" if secs else "-"
        print(f"{name:9s} {model[:44]:44s} {done:>5d}/{expected:<3d} {inflight:>9d} {mean:>8s} {infra:>6d}  {'; '.join(note)}")

    print(f"\ntotal: {total_done}/{total_expected} runs complete")
    if running and total_done < total_expected:
        remaining = total_expected - total_done
        print(f"still running; about {remaining} runs to go.")

    judged = list(STUDY_ROOT.glob("judged_*.jsonl"))
    answers = STUDY_ROOT / "answers.csv"
    print()
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        print()
    if running:
        print("NEXT: wait for the driver to finish (or Ctrl+C it and relaunch later; finished runs are kept).")
    elif total_done < total_expected:
        print("NEXT: relaunch the study to finish the missing runs:")
        print("      venv\\Scripts\\python experiments\\contrastive\\run_study.py")
    else:
        print("Generation is COMPLETE.")
        if not answers.exists() or not judged:
            print("NEXT: run the judging pipeline (collect -> llama3.3:70b -> gpt-oss:20b -> aggregate):")
            print("      venv\\Scripts\\python experiments\\contrastive\\run_judging.py")
        else:
            for j in judged:
                n = sum(1 for line in j.read_text(encoding="utf-8").splitlines() if line.strip())
                print(f"judged by {j.stem[len('judged_'):]}: {n} pairs")
            print("NEXT: venv\\Scripts\\python experiments\\contrastive\\run_judging.py   (resumes/refreshes)")
            print("      results: experiments\\contrastive\\results_study\\summary.md")


if __name__ == "__main__":
    main()

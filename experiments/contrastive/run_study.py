#!/usr/bin/env python
"""Run the full contrastive study: several answer models, each through a condition set.

Models run one after another (so only one answer model is loaded on limmy at a
time), each into results_study/<model tag>/. Everything is resumable; rerun the
same command after an interruption and finished runs are skipped.

Phases (edit PHASES below to change the study):
    name        answer model                          conditions   repeats  concurrency
    12b         gemma3:12b                            full         5        6
    4b          gemma3:4b                             core         5        6
    27b         gemma3:27b                            core         5        6
    qwen9b      qwen3.5:9b (thinking off)             core         5        6
    qwen27b     qwen3.5:27b (thinking off)            core         5        6
    mistral     mistral-small3.2                      core         5        6
    geitje      GEITje-7B-ultra (Dutch, Mistral-7B)   core         5        6
    fietje      fietje-2-chat (Dutch, 2.7B)           core         5        6
    eurollm     EuroLLM-9B-Instruct (EU multilingual) core         5        6
    ref70b      llama3.3:70b (reference ceiling,      reference    5        2
                also its own command generator)

Concurrency 6 assumes OLLAMA_NUM_PARALLEL=8 on limmy (set 2026-09-14).

Usage:
    venv/Scripts/python experiments/contrastive/run_study.py                 # everything
    venv/Scripts/python experiments/contrastive/run_study.py --phases 12b 4b # a subset
    venv/Scripts/python experiments/contrastive/run_study.py --list
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_grid  # noqa: E402

HERE = Path(__file__).resolve().parent
STUDY_ROOT = HERE / "results_study"
SUITE = run_grid.ROOT / "tests" / "test_contrastive_suite.yml"

# (phase, answer model, condition set, repeats, concurrency, command model override)
# The 70b reference reuses itself as command generator: 42 GB of weights plus
# gemma3:4b and bge-m3 would not fit two 24 GB cards, and the command prompt is tiny.
PHASES = [
    ("12b", "gemma3:12b", "full", 5, 6, None),
    ("4b", "gemma3:4b", "core", 5, 6, None),
    ("27b", "gemma3:27b", "core", 5, 6, None),
    ("qwen9b", "qwen3.5:9b", "core", 5, 6, None),
    ("qwen27b", "qwen3.5:27b", "core", 5, 6, None),
    ("mistral", "mistral-small3.2", "core", 5, 6, None),
    ("geitje", "hf.co/BramVanroy/GEITje-7B-ultra-GGUF:Q4_K_M", "core", 5, 6, None),
    ("fietje", "hf.co/BramVanroy/fietje-2-chat-GGUF:Q4_K_M", "core", 5, 6, None),
    ("eurollm", "hf.co/bartowski/EuroLLM-9B-Instruct-GGUF:Q4_K_M", "core", 5, 6, None),
    ("ref70b", "llama3.3:70b", "reference", 5, 2, "llama3.3:70b"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", nargs="*", default=[p[0] for p in PHASES])
    ap.add_argument("--repeats", type=int, default=None, help="override repeats for all phases")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    selected = [p for p in PHASES if p[0] in args.phases]
    unknown = set(args.phases) - {p[0] for p in PHASES}
    if unknown:
        sys.exit(f"unknown phases {sorted(unknown)}; available: {[p[0] for p in PHASES]}")
    if args.list:
        for name, model, cset, reps, conc, cmd in PHASES:
            n = len(run_grid.CONDITION_SETS[cset]) * (args.repeats or reps)
            print(f"{name:8s} {model:48s} {cset:10s} {n:3d} runs  concurrency {conc}"
                  + (f"  command model {cmd}" if cmd else ""))
        return

    t0 = time.time()
    for name, model, cset, reps, conc, cmd in selected:
        reps = args.repeats or reps
        results = STUDY_ROOT / run_grid.model_tag(model)
        run_grid.log(f"=== phase {name}: {model}, {cset} conditions x {reps} repeats -> {results}")
        run_grid.run_grid(run_grid.CONDITION_SETS[cset], reps, conc, SUITE, results,
                          answer_model=model, dry_run=args.dry_run, command_model=cmd)
    run_grid.log(f"study finished in {(time.time() - t0)/3600:.2f} h")
    run_grid.log(f"next: venv/Scripts/python experiments/contrastive/collect.py --results {STUDY_ROOT}")


if __name__ == "__main__":
    main()

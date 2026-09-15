#!/usr/bin/env python
"""Run an ablation grid of Rasa e2e runs with concurrent processes.

Each run is `rasa test e2e <suite> --endpoints <variant> -o <results dir>`, where
the variant is derived from endpoints.yml with the condition's retriever settings
and, optionally, a different answer model. Runs are resumable: a run whose results
files already exist is skipped. Run metadata records the knowledge-base fingerprint
and the answer model.

Usage (from the project root, tunnel to limmy open):
    venv/Scripts/python experiments/contrastive/run_grid.py --repeats 5 --concurrency 4
    venv/Scripts/python experiments/contrastive/run_grid.py --conditions k0 --repeats 1   # calibration
    venv/Scripts/python experiments/contrastive/run_grid.py --answer-model gemma3:27b \\
        --results experiments/contrastive/results_study/gemma3-27b --conditions core
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RASA = ROOT / "venv" / "Scripts" / ("rasa.exe" if os.name == "nt" else "rasa")

# name -> (contrast_k, contrast_mode, top_k)
CONDITIONS = {
    "k0": (0, "bottom", 4),
    "topk2": (0, "bottom", 2),          # baseline: fewer documents, no contrast
    "bottom_k1": (1, "bottom", 4),
    "bottom_k2": (2, "bottom", 4),
    "bottom_k3": (3, "bottom", 4),
    "bottom_k4": (4, "bottom", 4),
    "random_k1": (1, "random", 4),
    "random_k2": (2, "random", 4),
    "random_k3": (3, "random", 4),
    "random_k4": (4, "random", 4),
    "next_k1": (1, "next", 4),
    "next_k2": (2, "next", 4),
    "next_k3": (3, "next", 4),
    "next_k4": (4, "next", 4),
}
CONDITION_SETS = {
    "full": list(CONDITIONS),
    "core": ["k0", "topk2", "bottom_k2", "bottom_k4", "random_k2", "random_k4", "next_k2", "next_k4"],
    "pilot": ["k0", "bottom_k2", "bottom_k4", "random_k2", "random_k4", "next_k2", "next_k4"],
    "reference": ["k0"],
}

# Extra LiteLLM parameters per answer model. `reasoning_effort` outside
# low/medium/high makes LiteLLM send `think: false` to Ollama, which switches
# thinking off for Qwen-style models (verified 2026-09-14 on both Ollama routes).
# fietje-2 (Phi-2, n_ctx_train 2048) rambles after its answer; without an output cap
# prompt + generation run past 2048 positions and Ollama's CUDA runner dies with
# "misaligned address" (2026-09-15). max_tokens -> num_predict via LiteLLM.
MODEL_EXTRAS = {
    "qwen3.5:9b": {"reasoning_effort": "none"},
    "qwen3.5:27b": {"reasoning_effort": "none"},
    "qwen3:14b": {"reasoning_effort": "none"},
    "hf.co/BramVanroy/fietje-2-chat-GGUF:Q4_K_M": {"num_ctx": 2048, "max_tokens": 160},
}
EXTRA_KEYS = sorted({k for v in MODEL_EXTRAS.values() for k in v})

_print_lock = threading.Lock()
ANSWER_MODEL: str | None = None
RASA_MODEL: str | None = None


def log(msg: str) -> None:
    with _print_lock:
        print(time.strftime("%H:%M:%S"), msg, flush=True)


def docs_fingerprint(docs_dir: Path) -> dict:
    """Short hash over the knowledge base so results record which docs they used."""
    h = hashlib.sha256()
    files = sorted(p for p in docs_dir.rglob("*.txt"))
    for f in files:
        h.update(str(f.relative_to(docs_dir)).encode("utf-8"))
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return {"docs_files": len(files), "docs_sha256": h.hexdigest()[:12]}


def model_tag(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "-", model.split("/")[-1])


ANSWER_BLOCK_RE = re.compile(
    r"(id: ollama_answer_llm\s*\n\s*models:\s*\n\s*- provider: ollama\s*\n(\s*)model:)\s*\S+([^\n]*\n(?:\2\S[^\n]*\n)*)"
)
COMMAND_MODEL_RE = re.compile(
    r"(id: ollama_command_llm\s*\n\s*models:\s*\n\s*- provider: ollama\s*\n\s*model:)\s*\S+"
)
COMMAND_MODEL: str | None = None


def _set_key(text: str, key: str, value) -> str:
    text, n = re.subn(rf"^(\s*{key}:).*$", lambda m: f"{m.group(1)} {value}", text, flags=re.M)
    if n != 1:
        sys.exit(f"expected exactly one '{key}:' line in endpoints.yml, found {n}")
    return text


def write_endpoint_variants(base: Path, out_dir: Path, answer_model: str | None = None,
                            command_model: str | None = None) -> dict:
    """Derive one endpoints file per condition from the base endpoints.yml."""
    text = base.read_text(encoding="utf-8")
    if command_model:
        text, n = COMMAND_MODEL_RE.subn(lambda m: f"{m.group(1)} {command_model}", text)
        if n != 1:
            sys.exit("could not locate the ollama_command_llm block in endpoints.yml")
    if answer_model:
        m = ANSWER_BLOCK_RE.search(text)
        if not m:
            sys.exit("could not locate the ollama_answer_llm block in endpoints.yml")
        indent = m.group(2)
        rest = m.group(3)
        for key in EXTRA_KEYS:
            rest = re.sub(rf"^{indent}{key}:.*\n", "", rest, flags=re.M)
        extras = "".join(f"{indent}{k}: {v}\n" for k, v in MODEL_EXTRAS.get(answer_model, {}).items())
        text = text[: m.start()] + f"{m.group(1)} {answer_model}{rest}{extras}" + text[m.end():]
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    tag = f"_{model_tag(answer_model)}" if answer_model else ""
    if command_model:
        tag += f"_cmd-{model_tag(command_model)}"
    for name, (k, mode, top_k) in CONDITIONS.items():
        variant = _set_key(text, "contrast_k", k)
        variant = _set_key(variant, "contrast_mode", mode)
        variant = _set_key(variant, "top_k", top_k)
        p = out_dir / f"endpoints_{name}{tag}.yml"
        p.write_text(variant, encoding="utf-8")
        paths[name] = p
    return paths


def run_one(name: str, rep: int, endpoints: Path, suite: Path, results_root: Path) -> dict:
    run_dir = results_root / f"{name}_r{rep}"
    passed = run_dir / "e2e_results_passed.yml"
    failed = run_dir / "e2e_results_failed.yml"
    meta_path = run_dir / "meta.json"
    if passed.exists() and failed.exists() and meta_path.exists():
        log(f"skip  {run_dir.name} (already done)")
        return json.loads(meta_path.read_text())
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(RASA), "test", "e2e", str(suite), "--endpoints", str(endpoints), "-o", str(run_dir)]
    if RASA_MODEL:
        cmd += ["-m", RASA_MODEL]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    log(f"start {run_dir.name}")
    t0 = time.time()
    with open(run_dir / "run.log", "w", encoding="utf-8") as logf:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=logf, stderr=subprocess.STDOUT)
    k, mode, top_k = CONDITIONS[name]
    meta = {
        "condition": name,
        "repeat": rep,
        "contrast_k": k,
        "contrast_mode": mode,
        "top_k": top_k,
        "answer_model": ANSWER_MODEL or "endpoints.yml default",
        "command_model": COMMAND_MODEL or "endpoints.yml default",
        "rasa_model": RASA_MODEL or "latest in models/",
        "suite": str(suite.relative_to(ROOT)).replace("\\", "/"),
        **docs_fingerprint(ROOT / "docs"),
        "returncode": proc.returncode,
        "seconds": round(time.time() - t0, 1),
        "started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    ok = passed.exists() or failed.exists()
    log(f"done  {run_dir.name} rc={proc.returncode} {meta['seconds']/60:.1f} min"
        + ("" if ok else "  ** no results written, see run.log **"))
    return meta


def run_grid(conditions, repeats, concurrency, suite: Path, results_root: Path,
             answer_model=None, rasa_model=None, stagger=20.0, dry_run=False,
             command_model=None) -> list:
    global ANSWER_MODEL, RASA_MODEL, COMMAND_MODEL
    ANSWER_MODEL, RASA_MODEL, COMMAND_MODEL = answer_model, rasa_model, command_model
    unknown = [c for c in conditions if c not in CONDITIONS]
    if unknown:
        sys.exit(f"unknown conditions {unknown}; choose from {list(CONDITIONS)}")
    variants = write_endpoint_variants(ROOT / "endpoints.yml", HERE / "endpoints", answer_model, command_model)
    plan = [(c, r) for r in range(1, repeats + 1) for c in conditions]
    log(f"{len(plan)} runs, concurrency {concurrency}, results in {results_root}")
    log(f"knowledge base: {docs_fingerprint(ROOT / 'docs')}; answer model: {answer_model or 'default'}")
    if dry_run:
        for c, r in plan:
            print(f"  {c}_r{r}  ->  {variants[c].name}")
        return []
    started = 0
    metas = []

    def launch(c: str, r: int) -> dict:
        nonlocal started
        with _print_lock:
            index = started
            started += 1
        # Only the first wave is staggered (so index builds do not collide);
        # later runs start as soon as a worker is free.
        if index < concurrency:
            time.sleep(index * stagger)
        return run_one(c, r, variants[c], suite, results_root)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for meta in pool.map(lambda cr: launch(*cr), plan):
            metas.append(meta)
    bad = [m for m in metas if m["returncode"] not in (0, 1)]
    log(f"all done in {(time.time() - t0)/3600:.2f} h; {len(bad)} runs with unexpected exit codes")
    return metas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--conditions", nargs="*", default=CONDITION_SETS["pilot"],
                    help="condition names, or one of the sets: " + ", ".join(CONDITION_SETS))
    ap.add_argument("--suite", default="tests/test_contrastive_suite.yml")
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--stagger", type=float, default=20.0,
                    help="seconds between process starts, so index builds do not collide")
    ap.add_argument("--answer-model", default=None,
                    help="override the ollama_answer_llm model, e.g. gemma3:27b")
    ap.add_argument("--model", default=None, help="trained Rasa model path (prompt ablations)")
    ap.add_argument("--command-model", default=None,
                    help="override the ollama_command_llm model (e.g. reuse a 70b answer model to save VRAM)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conditions = args.conditions
    if len(conditions) == 1 and conditions[0] in CONDITION_SETS:
        conditions = CONDITION_SETS[conditions[0]]
    run_grid(conditions, args.repeats, args.concurrency, (ROOT / args.suite).resolve(),
             Path(args.results).resolve(), args.answer_model, args.model, args.stagger, args.dry_run,
             command_model=args.command_model)
    log("next: venv/Scripts/python experiments/contrastive/collect.py --results <dir>")


if __name__ == "__main__":
    main()

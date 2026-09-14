#!/usr/bin/env python
"""Offline groundedness judge over answers.csv, using Rasa's own judge prompt.

For every unique (ground_truth, answer) pair with a non-empty answer, the judge
model is asked, with Rasa's groundedness template, to split the answer into
statements and mark each as supported (1) or not (0). The score is the mean, the
same formula Rasa's `generative_response_is_grounded` uses. Results are cached
per judge in judged_<judge>.jsonl, so the script is resumable and re-running
only judges new pairs.

Usage:
    venv/Scripts/python experiments/contrastive/judge.py --answers <dir>/answers.csv \\
        --judge llama3.3:70b --parallel 4
    venv/Scripts/python experiments/contrastive/judge.py --answers ... --judge gpt-oss:20b --sample 2000
"""

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from jinja2 import Template

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "venv" / "Lib" / "site-packages" / "rasa" / "e2e_test" / "llm_judge_prompts" / "groundedness_prompt_template.jinja2"
OLLAMA = "http://localhost:11434"

_lock = threading.Lock()


def pair_id(ground_truth: str, answer: str) -> str:
    return hashlib.sha256(f"{ground_truth}\n---\n{answer}".encode("utf-8")).hexdigest()[:16]


def parse_statements(text: str):
    """Rasa's parser, plus tolerance for text around the JSON object."""
    cleaned = text.replace("```json\n", "").replace("```json", "").replace("```", "").replace("\n", "")
    try:
        return json.loads(cleaned)["statements"]
    except Exception:
        m = re.search(r"\{.*\}", cleaned, re.S)
        if not m:
            raise
        return json.loads(m.group(0))["statements"]


def judge_one(judge: str, prompt: str, num_ctx: int, timeout: int) -> dict:
    t0 = time.time()
    body = {"model": judge, "stream": False, "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": num_ctx}}
    if judge.startswith("gpt-oss"):
        body["think"] = "low"
    r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=timeout).json()
    if "error" in r:
        raise RuntimeError(r["error"])
    content = (r.get("message") or {}).get("content", "") or ""
    statements = parse_statements(content)
    scores = [int(s.get("score", 0)) for s in statements]
    return {
        "score": (sum(scores) / len(scores)) if scores else None,
        "n_statements": len(scores),
        "n_supported": sum(scores),
        "statements": statements,
        "seconds": round(time.time() - t0, 1),
        "eval_count": r.get("eval_count"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--judge", required=True, help="Ollama model name")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--sample", type=int, default=None, help="judge a random sample of N unique pairs (seed 0)")
    ap.add_argument("--limit", type=int, default=None, help="judge at most N new pairs this invocation")
    ap.add_argument("--num-ctx", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    answers = Path(args.answers)
    tag = re.sub(r"[^A-Za-z0-9.]+", "-", args.judge.split("/")[-1])
    out_path = answers.parent / f"judged_{tag}.jsonl"
    template = Template(TEMPLATE.read_text(encoding="utf-8"))

    rows = list(csv.DictReader(open(answers, encoding="utf-8")))
    pairs = {}
    for r in rows:
        if r["answer"] and r["ground_truth"]:
            pairs.setdefault(pair_id(r["ground_truth"], r["answer"]), (r["ground_truth"], r["answer"]))
    done = {}
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                done[d["pair_id"]] = d
    todo = [pid for pid in pairs if pid not in done]
    if args.sample is not None:
        rng = random.Random(0)
        keep = set(rng.sample(sorted(pairs), min(args.sample, len(pairs))))
        todo = [pid for pid in todo if pid in keep]
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"{len(pairs)} unique pairs, {len(done)} already judged by {args.judge}, {len(todo)} to do -> {out_path}")
    if not todo:
        return

    counter = {"n": 0, "err": 0, "t0": time.time()}

    def work(pid: str):
        gt, ans = pairs[pid]
        prompt = template.render(bot_message=ans, ground_truth=gt)
        try:
            res = judge_one(args.judge, prompt, args.num_ctx, args.timeout)
            rec = {"pair_id": pid, "judge": args.judge, "ground_truth": gt, "answer": ans, **res}
        except Exception as exc:
            rec = {"pair_id": pid, "judge": args.judge, "ground_truth": gt, "answer": ans,
                   "score": None, "error": str(exc)[:300]}
            counter["err"] += 1
        with _lock:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            counter["n"] += 1
            if counter["n"] % 25 == 0 or counter["n"] == len(todo):
                el = time.time() - counter["t0"]
                rate = counter["n"] / el
                eta = (len(todo) - counter["n"]) / rate / 60 if rate else 0
                print(f"{counter['n']}/{len(todo)} judged, {counter['err']} errors, "
                      f"{el/60:.1f} min elapsed, ~{eta:.0f} min left", flush=True)

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(work, todo))
    print("done; errors:", counter["err"])


if __name__ == "__main__":
    main()

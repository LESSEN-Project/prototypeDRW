#!/usr/bin/env python
"""Collect e2e run results into one answers table (answers.csv).

Reads every <results>/<condition>_r<n>/ directory (recursively, so a study root
with one sub-directory per answer model works too). For each test case it
records the deterministic outcome, the bot's answer text (from the transcript
that the capture assertion forces Rasa to write), a hedged-answer flag, the
retrieval scores from run.log, and the ground truth for answerable cases.

Outcomes:
    A (answerable):  answered | abstained | infra
    N/O:             abstained | answered | infra
    plus hedged=1 when an answered case says the information is missing.

Usage:
    venv/Scripts/python experiments/contrastive/collect.py --results experiments/contrastive/results_study
"""

import argparse
import csv
import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ABSTAIN = "utter_no_relevant_answer_found"
INFRA = "utter_internal_error_rasa"
CAPTURE_REGEX = "(?!)"

# Rasa formats the transcript as BotUttered('<text>', {<data>}, {<metadata>}, <ts>)
# with the raw text in single quotes and no escaping, so apostrophes occur inside.
# The text ends at the first "', {" that starts the data dict.
BOT_RE = re.compile(r"^BotUttered\('(.*?)', (\{.*)$", re.S)
UTTER_ACTION_RE = re.compile(r'"utter_action": "([^"]+)"')
UTTER_SOURCE_RE = re.compile(r'"utter_source": "([^"]+)"')
SCORE_RE = re.compile(r"but was '([0-9.]+)'")
SEARCH_RE = re.compile(
    r'"query": "((?:[^"\\]|\\.)*)", "mode": "[a-z]+", "top": \[([^\]]*)\](?:, "top_scores": \[([^\]]*)\])?'
)

HEDGE_PATTERNS = [
    r"geen (specifieke |verdere |concrete |aanvullende )?informatie",
    r"(staat|wordt|is) (er |echter )?(niet|nergens) (vermeld|genoemd|beschreven|aangegeven|gespecificeerd|expliciet)",
    r"niet (expliciet |specifiek )?(vermeld|genoemd|beschreven|aangegeven)",
    r"kan ik (je |u )?(deze |die |jouw |uw )?vraag niet",
    r"niet (kunnen )?beantwoorden",
    r"niet direct beantwoorden",
    r"geen (gegevens|details|informatie) over",
    r"niets? (over|vermeld)",
    r"(is|zijn) (mij )?niet bekend",
    r"ik weet (het )?niet",
    r"helaas .{0,40}geen",
    r"de documenten (geven|bevatten|zeggen|vermelden) (geen|niets)",
    r"beschikbare informatie",
    r"geen informatie beschikbaar",
]
HEDGE_RE = re.compile("|".join(f"(?:{p})" for p in HEDGE_PATTERNS), re.I)


def stratum(name: str) -> str:
    return name.split("|", 1)[0].strip()


def parse_bot_utterance(event: str):
    m = BOT_RE.match(event)
    if not m:
        return None, None, None
    text = m.group(1).strip()
    rest = m.group(2)
    action = (UTTER_ACTION_RE.search(rest) or [None, None])[1]
    source = (UTTER_SOURCE_RE.search(rest) or [None, None])[1]
    return text, action, source


def answer_from_transcript(transcript) -> str:
    """The enterprise-search answer, or '' when the bot abstained/errored."""
    for ev in transcript or []:
        if not ev.startswith("BotUttered"):
            continue
        text, action, source = parse_bot_utterance(ev)
        if source == "EnterpriseSearchPolicy" and action is None:
            return text or ""
    return ""


def classify(result: dict, passed: bool):
    s = stratum(result["name"])
    if passed:
        return ("answered" if s == "A" else "abstained"), None
    af = result.get("assertion_failure") or {}
    a = af.get("assertion") or {}
    msg = af.get("error_message", "") or ""
    atype = a.get("type") or ("generative_response_is_grounded" if "ground_truth" in a else "")
    utter = a.get("utter_name") or ""
    if atype == "bot_did_not_utter" and utter == INFRA:
        return "infra", None
    if atype == "bot_did_not_utter" and utter == ABSTAIN:
        return "abstained", None
    if atype == "bot_uttered" and utter == ABSTAIN:
        return "answered", None
    if atype == "bot_uttered" and a.get("text_matches") == CAPTURE_REGEX:
        return ("answered" if s == "A" else "abstained"), None
    if atype == "generative_response_is_grounded":
        m = SCORE_RE.search(msg)
        return "answered", (float(m.group(1)) if m else None)
    return f"other:{atype}", None


def retrieval_from_log(run_dir: Path) -> dict:
    """query text -> (top docs, top scores) from the retriever's log lines."""
    out = {}
    log = run_dir / "run.log"
    if not log.exists():
        return out
    for m in SEARCH_RE.finditer(log.read_text(encoding="utf-8", errors="ignore")):
        query = m.group(1).encode("utf-8").decode("unicode_escape", errors="ignore")
        docs = [d.strip().strip('"').replace("docs\\\\", "").replace("\\\\", "/") for d in m.group(2).split(",") if d.strip()]
        scores = [float(x) for x in m.group(3).split(",")] if m.group(3) else []
        out[query] = (docs, scores)
    return out


def load_suite_questions(suite_path: Path) -> dict:
    data = yaml.safe_load(suite_path.read_text(encoding="utf-8")) or {}
    return {tc["test_case"]: tc["steps"][0]["user"] for tc in data.get("test_cases", [])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, help="results directory (searched recursively)")
    ap.add_argument("--out", default=None, help="output CSV (default: <results>/answers.csv)")
    ap.add_argument("--ground-truth", default=str(HERE / "ground_truth.yml"))
    args = ap.parse_args()

    root = Path(args.results).resolve()
    out_path = Path(args.out) if args.out else root / "answers.csv"
    gt = yaml.safe_load(Path(args.ground_truth).read_text(encoding="utf-8")) or {}
    suite_cache = {}
    rows = []
    for meta_path in sorted(root.rglob("meta.json")):
        run_dir = meta_path.parent
        meta = json.loads(meta_path.read_text())
        suite_rel = meta.get("suite", "tests/test_contrastive_suite.yml")
        if suite_rel not in suite_cache:
            p = ROOT / suite_rel
            suite_cache[suite_rel] = load_suite_questions(p) if p.exists() else {}
        questions = suite_cache[suite_rel]
        retrieval = retrieval_from_log(run_dir)
        for status, passed in (("passed", True), ("failed", False)):
            f = run_dir / f"e2e_results_{status}.yml"
            if not f.exists():
                continue
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for r in data.get("test_results", []) or []:
                outcome, judge = classify(r, passed)
                transcript = (r.get("assertion_failure") or {}).get("actual_events_transcript") or []
                answer = answer_from_transcript(transcript) if outcome == "answered" else ""
                question = questions.get(r["name"], "")
                docs, scores = retrieval.get(question, ([], []))
                rows.append({
                    "results_root": str(run_dir.parent.relative_to(root.parent)) if root.parent in run_dir.parents else str(run_dir.parent),
                    "answer_model": meta.get("answer_model", ""),
                    "docs_sha256": meta.get("docs_sha256", ""),
                    "condition": meta["condition"],
                    "contrast_k": meta.get("contrast_k", ""),
                    "contrast_mode": meta.get("contrast_mode", ""),
                    "top_k": meta.get("top_k", 4),
                    "repeat": meta["repeat"],
                    "run": run_dir.name,
                    "case": r["name"],
                    "stratum": stratum(r["name"]),
                    "question": question,
                    "outcome": outcome,
                    "hedged": int(bool(answer) and bool(HEDGE_RE.search(answer))),
                    "answer": answer,
                    "top1_score": scores[0] if scores else "",
                    "top_scores": " ".join(f"{s:.4f}" for s in scores),
                    "top_docs": " ".join(docs),
                    "ground_truth": gt.get(r["name"], ""),
                    "inline_judge_score": "" if judge is None else judge,
                })
    if not rows:
        raise SystemExit(f"no results under {root}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n_runs = len({r["run"] + r["results_root"] for r in rows})
    n_ans = sum(1 for r in rows if r["outcome"] == "answered")
    n_txt = sum(1 for r in rows if r["answer"])
    n_uniq = len({(r["ground_truth"], r["answer"]) for r in rows if r["answer"] and r["ground_truth"]})
    print(f"{len(rows)} case results from {n_runs} runs -> {out_path}")
    print(f"answered: {n_ans}, with answer text: {n_txt}, unique (ground_truth, answer) pairs to judge: {n_uniq}")
    missing = [r for r in rows if r["outcome"] == "answered" and not r["answer"]]
    if missing:
        print(f"WARNING: {len(missing)} answered cases without answer text (old suite without capture assertion?)")


if __name__ == "__main__":
    main()

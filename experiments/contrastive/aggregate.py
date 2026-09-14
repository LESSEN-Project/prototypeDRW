#!/usr/bin/env python
"""Aggregate answers.csv (+ offline judge files) into study tables.

Inputs
    <results>/answers.csv              from collect.py
    <results>/judged_<judge>.jsonl     from judge.py (optional, any number of judges)

Per answer model and condition the report gives, over cases (per-case majority
across repeats, ties count as the worse outcome):
    A false-abstain      answerable cases the bot declined
    A hedged             answerable cases answered with an "information missing" hedge
    A grounded           answerable cases answered with judge score >= threshold
    N false-answer       near-miss cases answered outright (hedged excluded)
    N hedged             near-miss cases answered with a hedge
    O false-answer       out-of-scope cases answered
with 95% bootstrap confidence intervals over cases, McNemar's exact test against
the same model's k0 condition on the primary N false-answer outcome, a similarity-
floor baseline computed from the logged retrieval distances, per-case flap tables,
and judge agreement when more than one judge file is present.

Usage:
    venv/Scripts/python experiments/contrastive/aggregate.py --results experiments/contrastive/results_study
"""

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
THRESHOLD = 0.8
CONDITION_ORDER = ["k0", "topk2",
                   "bottom_k1", "bottom_k2", "bottom_k3", "bottom_k4",
                   "random_k1", "random_k2", "random_k3", "random_k4",
                   "next_k1", "next_k2", "next_k3", "next_k4"]
CODES = {"grounded": "G", "ungrounded": "U", "unjudged": "u", "hedged": "H", "abstained": "A",
         "answered": "X", "infra": "!"}
# per stratum: the outcome we want, and the ranking used for majority ties (worst first)
WANT = {"A": "grounded", "N": "abstained", "O": "abstained"}
RANK = {"A": ["infra", "abstained", "hedged", "ungrounded", "unjudged", "grounded"],
        "N": ["infra", "answered", "hedged", "abstained"],
        "O": ["infra", "answered", "hedged", "abstained"]}


def load_judgements(root: Path) -> dict:
    """judge name -> {(ground_truth, answer): score}"""
    out = {}
    for f in sorted(root.glob("judged_*.jsonl")):
        name = f.stem[len("judged_"):]
        scores = {}
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if d.get("score") is not None:
                scores[(d["ground_truth"], d["answer"])] = float(d["score"])
        out[name] = scores
    return out


def fine_outcome(row: dict, judge_scores: dict | None) -> str:
    o = row["outcome"]
    if o != "answered":
        return o
    if row["hedged"] == "1":
        return "hedged"
    if row["stratum"] != "A":
        return "answered"
    score = None
    if judge_scores is not None:
        score = judge_scores.get((row["ground_truth"], row["answer"]))
    if score is None and row.get("inline_judge_score"):
        score = float(row["inline_judge_score"])
    if score is None:
        return "unjudged"
    return "grounded" if score >= THRESHOLD else "ungrounded"


def majority(outcomes: list, stratum: str) -> str:
    c = Counter(outcomes)
    top = max(c.values())
    tied = [o for o, n in c.items() if n == top]
    return min(tied, key=lambda o: RANK[stratum].index(o) if o in RANK[stratum] else 99)


def bootstrap_ci(values: list, n=2000, seed=0):
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = []
    k = len(values)
    for _ in range(n):
        s = [values[rng.randrange(k)] for _ in range(k)]
        means.append(sum(s) / k)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value for discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def pct(x: float) -> str:
    return "n/a" if x != x else f"{100 * x:5.1f}%"


def similarity_floor(rows: list) -> list:
    """Sweep an abstain-if-top1-distance-above-threshold rule on k0 rows (any repeat)."""
    k0 = [r for r in rows if r["condition"] == "k0" and r["top1_score"]]
    if not k0:
        return []
    per_case = defaultdict(list)
    for r in k0:
        per_case[(r["stratum"], r["case"])].append(float(r["top1_score"]))
    dist = {k: sum(v) / len(v) for k, v in per_case.items()}
    lines = ["| distance threshold | A false-abstain | N false-answer | O false-answer |", "|---|---|---|---|"]
    ds = sorted(set(round(d, 2) for d in dist.values()))
    for t in [ds[i] for i in range(0, len(ds), max(1, len(ds) // 12))]:
        res = {}
        for s in "ANO":
            items = [d for (st, _), d in dist.items() if st == s]
            if not items:
                res[s] = float("nan")
                continue
            abst = sum(1 for d in items if d > t)
            res[s] = abst / len(items) if s == "A" else 1 - abst / len(items)
        lines.append(f"| > {t:.2f} | {pct(res['A'])} | {pct(res['N'])} | {pct(res['O'])} |")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--judge", default=None, help="judge file to use for groundedness (default: first found)")
    args = ap.parse_args()
    root = Path(args.results).resolve()
    rows = list(csv.DictReader(open(root / "answers.csv", encoding="utf-8")))
    judges = load_judgements(root)
    judge_name = args.judge or (next(iter(judges)) if judges else None)
    judge_scores = judges.get(judge_name) if judge_name else None

    out = [f"# Contrastive study summary\n", f"Judge for groundedness: {judge_name or 'none (inline scores only)'}; "
           f"threshold {THRESHOLD}. Rates are over cases, using the per-case majority across repeats.\n"]
    models = sorted({r["answer_model"] for r in rows})
    for model in models:
        mrows = [r for r in rows if r["answer_model"] == model]
        conds = [c for c in CONDITION_ORDER if any(r["condition"] == c for r in mrows)]
        kb = sorted({r["docs_sha256"] for r in mrows})
        reps = {c: len({r["repeat"] for r in mrows if r["condition"] == c}) for c in conds}
        out.append(f"\n## {model}\n")
        out.append(f"Knowledge base {', '.join(kb)}; repeats per condition: " +
                   ", ".join(f"{c}={reps[c]}" for c in conds) + "\n")
        # per-case majority outcome per condition
        maj = defaultdict(dict)   # case -> condition -> outcome
        flaps = defaultdict(dict)  # case -> condition -> code string
        for c in conds:
            by_case = defaultdict(list)
            for r in mrows:
                if r["condition"] == c:
                    by_case[r["case"]].append((int(r["repeat"]), fine_outcome(r, judge_scores)))
            for case, lst in by_case.items():
                lst.sort()
                outs = [o for _, o in lst]
                maj[case][c] = majority(outs, case.split("|")[0].strip())
                flaps[case][c] = "".join(CODES.get(o, "?") for o in outs)
        cases = sorted(maj, key=lambda n: ({"A": 0, "N": 1, "O": 2}.get(n.split("|")[0].strip(), 3), n))
        A = [x for x in cases if x.startswith("A")]
        N = [x for x in cases if x.startswith("N")]
        O = [x for x in cases if x.startswith("O")]

        out.append("| condition | A false-abstain | A hedged | A grounded | N false-answer | N hedged | O false-answer | McNemar vs k0 (N) | infra |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        k0_nfa = {x: maj[x].get("k0") == "answered" for x in N}
        for c in conds:
            def rate(cases_, pred):
                vals = [1 if pred(maj[x].get(c)) else 0 for x in cases_ if c in maj[x]]
                if not vals:
                    return "n/a"
                m = sum(vals) / len(vals)
                lo, hi = bootstrap_ci(vals)
                return f"{100*m:4.1f}% [{100*lo:.0f}-{100*hi:.0f}]"
            infra = sum(1 for r in mrows if r["condition"] == c and r["outcome"] == "infra")
            if c == "k0" or "k0" not in conds:
                p = "-"
            else:
                b = sum(1 for x in N if k0_nfa[x] and maj[x].get(c) != "answered")
                cc = sum(1 for x in N if not k0_nfa[x] and maj[x].get(c) == "answered")
                p = f"p={mcnemar_exact(b, cc):.2f} (-{b}/+{cc})"
            out.append(
                f"| {c} | {rate(A, lambda o: o == 'abstained')} | {rate(A, lambda o: o == 'hedged')} | "
                f"{rate(A, lambda o: o == 'grounded')} | {rate(N, lambda o: o == 'answered')} | "
                f"{rate(N, lambda o: o == 'hedged')} | {rate(O, lambda o: o == 'answered')} | {p} | {infra} |")
        out.append("\nMcNemar: discordant near-miss cases, -n moved from false-answer to correct, +n the reverse.\n")

        floor = similarity_floor(mrows)
        if floor:
            out.append("### Similarity-floor baseline (abstain when top-1 L2 distance exceeds threshold; k0 retrieval, no LLM)\n")
            out.extend(floor)
            out.append("")

        out.append("### Per-case outcomes across repeats\n")
        out.append("Codes: G grounded, U ungrounded, u unjudged, H hedged, A abstained, X answered (N/O), ! infra.\n")
        out.append("| case | " + " | ".join(conds) + " |")
        out.append("|---|" + "---|" * len(conds))
        for case in cases:
            cells = [flaps[case].get(c, "-") for c in conds]
            good = WANT[case.split("|")[0].strip()]
            if all(set(cell) == {CODES[good]} for cell in cells if cell != "-"):
                continue  # stable and correct everywhere: omit to keep the table readable
            out.append(f"| {case} | " + " | ".join(cells) + " |")
        out.append("")

    if len(judges) > 1:
        out.append("\n## Judge agreement\n")
        names = list(judges)
        out.append("| judge A | judge B | pairs | agree on pass/fail | mean abs diff |")
        out.append("|---|---|---|---|---|")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = judges[names[i]], judges[names[j]]
                common = [k for k in a if k in b]
                if not common:
                    continue
                agree = sum(1 for k in common if (a[k] >= THRESHOLD) == (b[k] >= THRESHOLD)) / len(common)
                mad = sum(abs(a[k] - b[k]) for k in common) / len(common)
                out.append(f"| {names[i]} | {names[j]} | {len(common)} | {100*agree:.1f}% | {mad:.3f} |")
        out.append("")

    summary = "\n".join(out)
    (root / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"\nwritten: {root / 'summary.md'}")


if __name__ == "__main__":
    main()

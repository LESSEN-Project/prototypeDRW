#!/usr/bin/env python
"""Run the suite mapping (suite_map.yml) against the built graph and report, per
stratum, how many suite questions come out entailed / contradicted / unknown,
how many needed inference, and how that compares with the text bot's k0 result.

    venv/Scripts/python experiments/kg/coverage.py
    venv/Scripts/python experiments/kg/coverage.py --answers experiments/contrastive/results_study/answers.csv --model gemma3:12b

Writes coverage.md next to this file.
"""
import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from build import build
from query import KG, verbalise, _short

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUITE = ROOT / "tests" / "test_contrastive_suite.yml"


def base_name(case: str) -> str:
    return re.sub(r"\s*\|\s*v\d+$", "", case.strip())


def load_suite():
    doc = yaml.safe_load(SUITE.read_text(encoding="utf-8"))
    out = []
    for tc in doc["test_cases"]:
        q = next(s["user"] for s in tc["steps"] if "user" in s)
        out.append((tc["test_case"], q))
    return out


def text_bot_majority(answers_csv: Path, model: str) -> dict:
    """case -> majority outcome of the text bot at k0 (answered / hedged / abstained), plus grounded flag."""
    per = defaultdict(list)
    with open(answers_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["answer_model"] != model or r["condition"] != "k0":
                continue
            o = r["outcome"]
            if o == "answered":
                o = "hedged" if r["hedged"] == "1" else "answered"
            per[r["case"]].append(o)
    return {c: Counter(v).most_common(1)[0][0] for c, v in per.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=str(ROOT / "experiments" / "contrastive" / "results_study" / "answers.csv"))
    ap.add_argument("--model", default="gemma3:12b")
    ap.add_argument("--extra", action="store_true", help="also run extra_questions.yml (v2-suite seeds) and print them")
    a = ap.parse_args()

    ds, _ = build(write=False)
    kg = KG(ds)
    smap = yaml.safe_load((HERE / "suite_map.yml").read_text(encoding="utf-8"))
    text = text_bot_majority(Path(a.answers), a.model) if Path(a.answers).exists() else {}

    rows = []
    for case, question in load_suite():
        stratum = case.split("|", 1)[0].strip()
        m = smap.get(base_name(case))
        if m is None:
            rows.append((case, stratum, question, "-", "UNMAPPED", "", "", text.get(case, "")))
            continue
        if m.get("template") is None:
            rows.append((case, stratum, question, "-", "unknown", "", "no entity links", text.get(case, "")))
            continue
        v = kg.run(m["template"], m.get("args", {}))
        rows.append((case, stratum, question, m["template"], v.verdict, "yes" if v.inferred else "",
                     v.note or (", ".join(_short(x)[:40] for x in v.values[:2])), text.get(case, ""), m.get("expect"), v))

    # -- report --------------------------------------------------------------
    out = ["# KG coverage of the 124-case suite", "",
           f"Graph: {sum(1 for g in ds.graphs() if str(g.identifier).startswith("urn:drw:doc:"))} converted documents; text-bot column = {a.model} at k0, per-case majority over 5 repeats.", ""]
    for stratum, want in (("A", "answered"), ("N", "declined"), ("O", "declined")):
        sub = [r for r in rows if r[1] == stratum]
        c = Counter(r[4] for r in sub)
        inf = sum(1 for r in sub if r[5] == "yes")
        mism = sum(1 for r in sub if len(r) > 8 and r[8] and r[4] != r[8])
        out.append(f"## Stratum {stratum} ({len(sub)} cases)")
        out.append("")
        out.append(f"entailed {c['entailed']}, contradicted {c['contradicted']}, unknown {c['unknown']}, unmapped {c['UNMAPPED']}; "
                   f"via inference {inf}; verdict differs from the hand expectation on {mism}.")
        if text:
            tc = Counter(r[7] for r in sub)
            out.append(f"Text bot ({a.model}, k0): answered {tc['answered']}, hedged {tc['hedged']}, abstained {tc['abstained']}.")
        out.append("")
        out.append("| case | template | verdict | inferred | note / value | text bot k0 |")
        out.append("|---|---|---|---|---|---|")
        for r in sub:
            out.append(f"| {r[0]} | {r[3]} | {r[4]} | {r[5]} | {str(r[6]).replace('|', '/')} | {r[7]} |")
        out.append("")

    out.append("## Evidence for the inferred verdicts")
    out.append("")
    for r in rows:
        if len(r) > 9 and r[9].inferred:
            out.append(f"**{r[0]}**")
            out.append("")
            out.append("```")
            out.append(verbalise(r[9]))
            out.append("```")
            out.append("")
    if a.extra:
        extra = yaml.safe_load((HERE / "extra_questions.yml").read_text(encoding="utf-8"))
        out.append("## Extra questions (v2-suite seeds, extra_questions.yml)")
        out.append("")
        out.append("| case | question | template | verdict | inferred | note | expected |")
        out.append("|---|---|---|---|---|---|---|")
        print()
        for e in extra:
            v = kg.run(e["template"], e.get("args", {}))
            flag = "" if v.verdict == e.get("expect") else "  <-- expected " + str(e.get("expect"))
            print(f"{e['case']:40s} {str(v):80s}{flag}")
            out.append(f"| {e['case']} | {e['question']} | {e['template']} | {v.verdict} | {'yes' if v.inferred else ''} | "
                       f"{(v.note or '').replace('|', '/')} | {e.get('expect', '')} |")
            out.append("")
            out.append("```")
            out.append(verbalise(v))
            out.append("```")
            out.append("")
    report = "\n".join(out)
    (HERE / "coverage.md").write_text(report, encoding="utf-8")
    # console summary
    for stratum in "ANO":
        sub = [r for r in rows if r[1] == stratum]
        c = Counter(r[4] for r in sub)
        print(f"{stratum}: n={len(sub)} entailed={c['entailed']} contradicted={c['contradicted']} unknown={c['unknown']} "
              f"unmapped={c['UNMAPPED']} inferred={sum(1 for r in sub if r[5] == 'yes')}")
    for r in rows:
        if len(r) > 8 and r[8] and r[4] != r[8]:
            print(f"  MISMATCH {r[0]}: got {r[4]}, expected {r[8]} ({r[6]})")
    print("written:", HERE / "coverage.md")


if __name__ == "__main__":
    main()

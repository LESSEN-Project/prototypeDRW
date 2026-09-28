#!/usr/bin/env python
"""Fixed question set for the 2026-09-29 demo: build the graph once, then ask each
question through its template and print the verdict, the evidence with the source
document, and a one-line Dutch answer.

    venv/Scripts/python experiments/kg/demo.py            # all questions
    venv/Scripts/python experiments/kg/demo.py 2 3 4      # a subset, by number
    venv/Scripts/python experiments/kg/demo.py --list     # show the question set
    venv/Scripts/python experiments/kg/demo.py --full     # do not cap the evidence list

Entity linking is not implemented yet (next step 1 in the README), so every question
is mapped to its template call by hand here, exactly as suite_map.yml does for the suite.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from build import build            # noqa: E402
from query import KG, verbalise    # noqa: E402

# (question, template, args, what to say about it)
QUESTIONS = [
    ("Verkopen jullie jeans?",
     "sells", {"category": "d:Jeans"},
     "direct: the assortment document lists jeans"),
    ("Verkopen jullie sneakers?",
     "sells", {"category": "d:Sneakers"},
     "inferred: doesNotSell Shoes propagates down the category tree; no triple mentions sneakers"),
    ("Verkopen jullie wasmachines?",
     "sells", {"category": "d:WashingMachines"},
     "completeness: no negative triple anywhere; the top-level list (kleding, accessoires) is declared complete"),
    ("Verkopen jullie hoodies?",
     "sells", {"category": "d:Hoodies"},
     "unknown: clothing is sold, the clothing list is 'onder andere', hoodies are not listed"),
    ("Kan ik met Bancontact betalen?",
     "accepts", {"payment": "d:Bancontact"},
     "per channel: webshop list complete -> contradicted online; store list open -> unknown; overall unknown"),
    ("Kan ik in termijnen betalen?",
     "accepts", {"payment": "d:Installments"},
     "per channel, same shape as Bancontact: contradicted online, unknown in store; every RAG model answered this from the Billink document"),
    ("Bezorgen jullie in Antwerpen?",
     "ships_to", {"region": "d:Antwerp"},
     "inferred: shipsTo Europe, Antwerp partOf Belgium partOf Europe (two steps)"),
    ("Repareren jullie een Nudie die ik elders heb gekocht?",
     "repairs", {"brand": "d:NudieJeans", "origin": "d:BoughtElsewhere"},
     "inferred: repair applies to clothing -> Nudie line; the origin rule on that line allows any origin"),
    ("Repareren jullie een Levi's die ik elders heb gekocht?",
     "repairs", {"brand": "d:Levis", "origin": "d:BoughtElsewhere"},
     "contradicted: same service, default purchase condition (bought here) applies, no rule for Levi's"),
    ("Zijn jullie op zondag open?",
     "open_on", {"day": "d:Sunday"},
     "direct, with the hours as values"),
    ("Zijn jullie op Koningsdag open?",
     "open_on", {"day": "d:Koningsdag"},
     "unknown: the weekly list is complete, but the document says holiday hours may differ"),
]

DUTCH = {"entailed": "Ja", "contradicted": "Nee", "unknown": "Daar hebben we geen informatie over"}
MAX_EVIDENCE = 6


def show(i, kg, q, template, args, why, full=False):
    v = kg.run(template, args)
    call = f"{template}({', '.join(f'{k}={a}' for k, a in args.items())})"
    print(f"\n[{i}] {q}")
    print(f"    template  {call}")
    print(f"    verdict   {v}")
    ev = verbalise(v).splitlines()
    if ev and not full and len(ev) > MAX_EVIDENCE:
        ev = ev[:MAX_EVIDENCE] + [f"... {len(ev) - MAX_EVIDENCE} more (run with --full)"]
    if ev:
        print("    evidence  " + "\n              ".join(ev))
    answer = DUTCH[v.verdict]
    if template == "open_on" and v.verdict == "entailed" and v.values:
        answer += " (" + ", ".join(str(x).split("#")[-1] for x in v.values) + ")"
    print(f"    answer    {answer}")
    print(f"    why       {why}")


def main(argv):
    if "--list" in argv:
        for i, (q, t, a, _) in enumerate(QUESTIONS, 1):
            print(f"[{i}] {q}   -> {t} {a}")
        return 0
    ds, n_problems = build(write=False, quiet=True)
    if n_problems:
        print(f"build reported {n_problems} problems; fix them before the demo", file=sys.stderr)
        return 1
    kg = KG(ds)
    wanted = [int(x) for x in argv if x.isdigit()] or range(1, len(QUESTIONS) + 1)
    for i in wanted:
        show(i, kg, *QUESTIONS[i - 1], full="--full" in argv)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python
"""Does the bot mirror the customer's register (u vs je)?

Offline measurement over the answers logged by the contrastive study
(experiments/contrastive/results_study/answers.csv): every row has the question,
the answer text, the answer model and the condition, so no new runs are needed.

The question's register is decided with the same marker rules as the bot's own
action (actions/actions.py: detect_register), so "question register" here is what
the bot believed the customer's register to be. The answer's register is decided
from second-person markers in the answer text: formal (u, uw, "kunt u", "heeft u",
"neemt u"), informal (je, jij, jou, jouw, jezelf). Answers without any second-person
marker are "neutral" and cannot mirror or fail to mirror.

    venv/Scripts/python experiments/register/analyze.py
    venv/Scripts/python experiments/register/analyze.py --answers <path>

Writes summary.md next to this file.
"""
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from actions.actions import detect_register  # the bot's own rule  # noqa: E402

ANSWER_FORMAL = [r"\bu\b", r"\buw\b", r"\bkunt u\b", r"\bheeft u\b", r"\bhebt u\b", r"\bneemt u\b", r"\bwilt u\b"]
ANSWER_INFORMAL = [r"\bje\b", r"\bjij\b", r"\bjou\b", r"\bjouw\b", r"\bjezelf\b"]
QUESTION_FORMAL_MARKERS = [r"\bu\b", r"\buw\b"]     # for the "does the question carry an explicit u" column


def answer_register(text: str) -> str:
    t = text.lower()
    f = sum(len(re.findall(p, t)) for p in ANSWER_FORMAL)
    i = sum(len(re.findall(p, t)) for p in ANSWER_INFORMAL)
    if f == 0 and i == 0:
        return "neutral"
    if f and i:
        return "mixed"
    return "formeel" if f else "informeel"


def question_has_u(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in QUESTION_FORMAL_MARKERS)


def pct(n, d):
    return "n/a" if not d else f"{100 * n / d:5.1f}%"


# ---- the register suite (tests/test_register.yml), read from e2e transcripts ---------------
import yaml  # noqa: E402

SLOT_RE = re.compile(r"SlotSet\(key: klant_register, value: (\w+)\)")
USER_RE = re.compile(r"^UserUttered\('(.*?)', '")
BOT_RE = re.compile(r"^BotUttered\('(.*?)', \{.*?\}, \{(.*)\}", re.S)
CAPTURE = "(?!)"


def turns_from_transcript(events):
    """Split a transcript into turns: dicts with the user text, the klant_register value
    after the turn, the enterprise-search answer text, and the fixed utterances."""
    turns = []
    cur = None
    for ev in events:
        m = USER_RE.match(ev)
        if m:
            cur = {"user": m.group(1), "slot": None, "answer": "", "fixed": []}
            turns.append(cur)
            continue
        if cur is None:
            continue
        m = SLOT_RE.search(ev)
        if m:
            cur["slot"] = m.group(1)
            continue
        m = BOT_RE.match(ev)
        if m:
            text, meta = m.group(1), m.group(2)
            if '"utter_source": "EnterpriseSearchPolicy"' in meta and '"utter_action"' not in meta:
                cur["answer"] = text
            else:
                cur["fixed"].append(text)
    return turns


def e2e_section(run_dir: Path) -> list:
    """Summarise one `rasa test e2e tests/test_register.yml -o <run_dir>` run."""
    rows = []
    for status in ("passed", "failed"):
        f = run_dir / f"e2e_results_{status}.yml"
        if not f.exists():
            continue
        for r in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("test_results", []) or []:
            af = r.get("assertion_failure") or {}
            assertion = af.get("assertion") or {}
            real_failure = status == "failed" and assertion.get("text_matches") != CAPTURE
            turns = turns_from_transcript(af.get("actual_events_transcript") or [])
            rows.append((r["name"], real_failure, assertion if real_failure else None, turns))
    out = [f"## Register suite run: `{run_dir.as_posix()}`", "",
           "Read from the e2e transcripts. `slot` is the value of `klant_register` after the turn; `answer` is the "
           "register of the enterprise-search answer text (neutral = no second-person marker); `Rasa` is whether the "
           "case's own assertions passed (the never-matching capture assertion excluded).", "",
           "| case | turn | user message | slot | answer register | Rasa |", "|---|---|---|---|---|---|"]
    tally = Counter()
    for name, failed, assertion, turns in rows:
        kind = name.split("|", 1)[0].strip()
        for i, t in enumerate(turns, 1):
            areg = answer_register(t["answer"]) if t["answer"] else "-"
            if t["answer"]:
                tally[(kind, t["slot"], areg)] += 1
            out.append(f"| {name} | {i} | {t['user'][:60]} | {t['slot'] or ''} | {areg} | "
                       f"{'FAIL' if failed and i == len(turns) else 'ok'} |")
    out.append("")

    def rate(kind, slot):
        n = sum(v for (k, s, a_), v in tally.items() if k == kind and s == slot and a_ in ("formeel", "informeel"))
        ok = sum(v for (k, s, a_), v in tally.items() if k == kind and s == slot and a_ == slot)
        neutral = sum(v for (k, s, a_), v in tally.items() if k == kind and s == slot and a_ == "neutral")
        return n, ok, neutral

    n_f, ok_f, neu_f = rate("F", "formeel")
    n_i, ok_i, neu_i = rate("I", "informeel")
    n_m, ok_m, neu_m = rate("M", "formeel")
    n_failed = sum(1 for _, failed, _, _ in rows if failed)
    out += [f"Formal single-turn: {ok_f} of {n_f} answers with a marker are formal ({pct(ok_f, n_f)}), {neu_f} neutral. "
            f"Informal single-turn: {ok_i} of {n_i} informal ({pct(ok_i, n_i)}), {neu_i} neutral. "
            f"Multi-turn formal turns: {ok_m} of {n_m} formal, {neu_m} neutral. "
            f"Rasa assertion failures: {n_failed} of {len(rows)} cases.", ""]
    fails = [(name, assertion) for name, failed, assertion, _ in rows if failed]
    if fails:
        out += ["Failed assertions:", ""] + [f"- {name}: {assertion}" for name, assertion in fails] + [""]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=str(ROOT / "experiments" / "contrastive" / "results_study" / "answers.csv"))
    ap.add_argument("--e2e", nargs="*", default=[], help="result dirs of `rasa test e2e tests/test_register.yml -o <dir>` runs")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.answers, encoding="utf-8")))
    answered = [r for r in rows if r["outcome"] == "answered" and r["answer"].strip()]
    for r in answered:
        r["q_reg"] = detect_register([r["question"]])
        r["q_has_u"] = question_has_u(r["question"])
        r["a_reg"] = answer_register(r["answer"])

    out = ["# Register mirroring in the study answers", "",
           f"Source: `{Path(a.answers).as_posix()}`, {len(rows)} case results, {len(answered)} with an answer text.", "",
           "The question register is the bot's own classification (`detect_register` in `actions/actions.py`, "
           "informal unless formal markers dominate). The answer register comes from second-person markers "
           "in the answer text; neutral answers have none and are excluded from the mirroring rate.", ""]

    # -- the suite itself -------------------------------------------------------------
    questions = {r["case"]: r["question"] for r in rows}
    q_reg = Counter(detect_register([q]) for q in questions.values())
    q_u = sum(1 for q in questions.values() if question_has_u(q))
    out += ["## The suite's questions", "",
            f"{len(questions)} distinct questions: {q_reg['formeel']} classified formal, {q_reg['informeel']} informal "
            f"(the default). {q_u} contain an explicit *u*/*uw*. The suite was written for retrieval and, despite the plan, "
            f"contains no formal paraphrases, so the study answers can only show the informal direction; the formal "
            f"direction is measured with `tests/test_register.yml` (sections below).", ""]
    formal_qs = sorted(c for c, q in questions.items() if detect_register([q]) == "formeel")
    out += ["Formal questions:", ""] + [f"- {c}: \"{questions[c]}\"" for c in formal_qs] + [""]

    # -- mirroring per model (all conditions pooled, and k0) -----------------------------
    def table(subset, title):
        out.append(f"## {title}")
        out.append("")
        out.append("| answer model | n answered | formal Q: answered formal | formal Q: answered informal | informal Q: answered informal | informal Q: answered formal | neutral answers | mixed |")
        out.append("|---|---|---|---|---|---|---|---|")
        for model in sorted({r["answer_model"] for r in subset}):
            s = [r for r in subset if r["answer_model"] == model]
            fq = [r for r in s if r["q_reg"] == "formeel" and r["a_reg"] in ("formeel", "informeel")]
            iq = [r for r in s if r["q_reg"] == "informeel" and r["a_reg"] in ("formeel", "informeel")]
            neutral = sum(1 for r in s if r["a_reg"] == "neutral")
            mixed = sum(1 for r in s if r["a_reg"] == "mixed")
            out.append(f"| {model.split('/')[-1]} | {len(s)} | "
                       f"{pct(sum(1 for r in fq if r['a_reg'] == 'formeel'), len(fq))} ({len(fq)}) | "
                       f"{pct(sum(1 for r in fq if r['a_reg'] == 'informeel'), len(fq))} | "
                       f"{pct(sum(1 for r in iq if r['a_reg'] == 'informeel'), len(iq))} ({len(iq)}) | "
                       f"{pct(sum(1 for r in iq if r['a_reg'] == 'formeel'), len(iq))} | "
                       f"{pct(neutral, len(s))} | {pct(mixed, len(s))} |")
        out.append("")

    table([r for r in answered if r["condition"] == "k0"], "Mirroring per answer model, k0 condition")
    table(answered, "Mirroring per answer model, all conditions pooled")

    # -- per condition for the model with the full sweep ----------------------------------
    m12 = [r for r in answered if r["answer_model"] == "gemma3:12b"]
    out += ["## gemma3:12b per condition", "",
            "| condition | formal Q answered formal | informal Q answered informal | neutral |", "|---|---|---|---|"]
    conds = ["k0", "topk2"] + [f"{m}_k{k}" for m in ("bottom", "random", "next") for k in (1, 2, 3, 4)]
    for c in conds:
        s = [r for r in m12 if r["condition"] == c]
        if not s:
            continue
        fq = [r for r in s if r["q_reg"] == "formeel" and r["a_reg"] in ("formeel", "informeel")]
        iq = [r for r in s if r["q_reg"] == "informeel" and r["a_reg"] in ("formeel", "informeel")]
        out.append(f"| {c} | {pct(sum(1 for r in fq if r['a_reg'] == 'formeel'), len(fq))} ({len(fq)}) | "
                   f"{pct(sum(1 for r in iq if r['a_reg'] == 'informeel'), len(iq))} ({len(iq)}) | "
                   f"{pct(sum(1 for r in s if r['a_reg'] == 'neutral'), len(s))} |")
    out.append("")

    # -- paraphrase pairs with different registers ------------------------------------------
    base = defaultdict(dict)
    for c, q in questions.items():
        m = re.match(r"(.*)\s\|\s(v\d)$", c)
        if m:
            base[m.group(1)][m.group(2)] = c
    pairs = [(b, v["v1"], v["v2"]) for b, v in base.items() if "v1" in v and "v2" in v
             and detect_register([questions[v["v1"]]]) != detect_register([questions[v["v2"]]])]
    out += ["## Paraphrase pairs whose two versions differ in register", "",
            f"{len(pairs)} of the answerable questions have one formal and one informal paraphrase. For each pair and model "
            f"(k0, all repeats), the share of answers whose register follows the question:", ""]
    out.append("| answer model | formal version answered formal | informal version answered informal |")
    out.append("|---|---|---|")
    k0 = [r for r in answered if r["condition"] == "k0"]
    for model in sorted({r["answer_model"] for r in k0}):
        f_ok = f_n = i_ok = i_n = 0
        for _, c1, c2 in pairs:
            for c in (c1, c2):
                for r in k0:
                    if r["answer_model"] == model and r["case"] == c and r["a_reg"] in ("formeel", "informeel"):
                        if r["q_reg"] == "formeel":
                            f_n += 1; f_ok += r["a_reg"] == "formeel"
                        else:
                            i_n += 1; i_ok += r["a_reg"] == "informeel"
        out.append(f"| {model.split('/')[-1]} | {pct(f_ok, f_n)} ({f_n}) | {pct(i_ok, i_n)} ({i_n}) |")
    out.append("")
    out += ["Pairs:", ""] + [f"- {b}: v1 \"{questions[c1]}\" ({detect_register([questions[c1]])}), v2 \"{questions[c2]}\" ({detect_register([questions[c2]])})"
                             for b, c1, c2 in pairs] + [""]

    # -- examples of failures ---------------------------------------------------------------
    fails = [r for r in k0 if r["q_reg"] == "formeel" and r["a_reg"] == "informeel"]
    out += ["## Examples: formal question answered informally (k0)", ""]
    seen = set()
    for r in fails:
        key = (r["answer_model"], r["case"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f"- {r['answer_model'].split('/')[-1]} / {r['case']}: \"{r['answer'][:160]}\"")
        if len(seen) >= 12:
            break
    out.append("")
    for d in a.e2e:
        out += e2e_section(Path(d))
    (HERE / "summary.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:40]))
    print("written:", HERE / "summary.md")


if __name__ == "__main__":
    main()

"""Toy example: one ambiguous message, three pieces of evidence, three candidate questions.

Run with:  venv/Scripts/python experiments/interrogative_agenda/example.py

The message is invented: "Ik heb een vraag over mijn Kuyichi jeans". The numbers
are illustrative; nothing here is estimated from data.
"""
from __future__ import annotations

from ds import (Question, bel, combine_all, condition, decide, mass, nonspecificity,
                pignistic, pignistic_entropy, pl, rank_questions)

# The frame: four routes the bot could take for this message.
MERK = "merk"              # graph: does the shop carry this brand?
REPARATIE = "reparatie"    # graph: can the shop repair or alter this garment?
BESTELLING = "bestelling"  # the customer's own order: needs a person or the order system
ZOEKEN = "zoeken"          # anything else: retrieval
FRAME = frozenset({MERK, REPARATIE, BESTELLING, ZOEKEN})

# Three sources of evidence about the message, each as a mass function.
EVIDENCE = {
    "linker found a brand (Kuyichi)":
        mass({(MERK, REPARATIE, BESTELLING): 0.7, FRAME: 0.3}),
    'possessive wording ("mijn ... jeans")':
        mass({(REPARATIE, BESTELLING): 0.6, FRAME: 0.4}),
    "no order vocabulary (bestelling, pakket, levering)":
        mass({(MERK, REPARATIE, ZOEKEN): 0.3, FRAME: 0.7}),
}

QUESTIONS = [
    Question("kapot", "Is er iets stuk aan de jeans, of wil je hem laten vermaken?",
             {"ja": frozenset({REPARATIE}),
              "nee": frozenset({MERK, BESTELLING, ZOEKEN})}),
    Question("bestelling", "Gaat het om een bestelling die nog onderweg is of klaarligt?",
             {"ja": frozenset({BESTELLING}),
              "nee": frozenset({MERK, REPARATIE, ZOEKEN})}),
    # The question the shop's employees ask in the WhatsApp logs. It matters inside
    # the repair route (the purchase condition) and separates the routes only weakly.
    Question("gekocht", "Heb je de jeans bij ons gekocht?",
             {"ja": frozenset({REPARATIE, BESTELLING, ZOEKEN}),
              "nee": frozenset({MERK, REPARATIE, ZOEKEN})}),
]


def show(m, title):
    print(f"\n{title}")
    for focal, w in sorted(m.items(), key=lambda kv: -kv[1]):
        label = "{" + ", ".join(sorted(focal)) + "}"
        print(f"  m({label}) = {w:.3f}")
    print("  route        Bel    Pl     BetP")
    betp = pignistic(m)
    for r in sorted(FRAME):
        print(f"  {r:<12} {bel(m, {r}):.3f}  {pl(m, {r}):.3f}  {betp.get(r, 0.0):.3f}")
    print(f"  nonspecificity {nonspecificity(m):.3f} bits, pignistic entropy {pignistic_entropy(m):.3f} bits")
    route = decide(m)
    print(f"  decision at threshold 0.6: {'commit to ' + route if route else 'ask'}")


def main():
    for name, m in EVIDENCE.items():
        print(f"evidence: {name}")
    combined, conflicts = combine_all(EVIDENCE.values())
    show(combined, "After combining the evidence (conflict per step: "
         + ", ".join(f"{k:.3f}" for k in conflicts) + ")")

    print("\nQuestions ranked by expected gain")
    ranking = rank_questions(combined, QUESTIONS)
    for s in ranking:
        probs = ", ".join(f"{a} {p:.2f}" for a, p in s.answer_probabilities.items())
        print(f"  {s.question.name:<11} gain {s.gain:.3f} bits  (expected entropy {s.expected_entropy:.3f}; P: {probs})")
        print(f"              {s.question.text}")

    best = ranking[0].question
    for answer, routes in best.answers.items():
        show(condition(combined, routes), f'After "{best.text}" -> {answer}')


if __name__ == "__main__":
    main()

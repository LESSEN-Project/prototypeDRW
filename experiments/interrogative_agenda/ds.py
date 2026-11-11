"""Dempster-Shafer mass functions over a finite frame, and question selection on top of them.

The frame is a set of hashable labels (here: the routes the bot can take). A mass
function is a dict from frozenset to float whose values sum to 1 and that puts no
mass on the empty set. Mass on a set with more than one element is evidence that
does not distinguish between the elements; mass on the whole frame is ignorance.

The Dempster-Shafer part (combine, bel, pl, condition) is textbook material
(Shafer 1976). The question-selection part (Question, rank_questions, decide) is a
first design of our own and has not been checked against the interrogative-agenda
papers yet; see README.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Hashable, Iterable, Mapping

Focal = frozenset
Mass = dict[Focal, float]
TOL = 1e-9


def mass(assignments: Mapping[Iterable[Hashable], float]) -> Mass:
    """Build a mass function from {iterable of labels: weight}; checks that it is valid."""
    m: Mass = {}
    for labels, weight in assignments.items():
        focal = frozenset(labels)
        if not focal:
            raise ValueError("no mass may be put on the empty set")
        if weight < -TOL:
            raise ValueError(f"negative mass on {set(focal)}")
        if weight > TOL:
            m[focal] = m.get(focal, 0.0) + weight
    total = sum(m.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"masses sum to {total}, expected 1")
    return m


def vacuous(frame: Iterable[Hashable]) -> Mass:
    """Total ignorance: all mass on the frame."""
    return {frozenset(frame): 1.0}


def combine(m1: Mass, m2: Mass) -> tuple[Mass, float]:
    """Dempster's rule. Returns the combined mass function and the conflict K.

    K is the mass that the two sources put on incompatible sets. The rule
    renormalizes by 1 - K; with K = 1 the sources contradict each other fully
    and no combination exists.
    """
    raw: Mass = {}
    conflict = 0.0
    for a, wa in m1.items():
        for b, wb in m2.items():
            inter = a & b
            if inter:
                raw[inter] = raw.get(inter, 0.0) + wa * wb
            else:
                conflict += wa * wb
    if conflict >= 1.0 - TOL:
        raise ValueError("total conflict: the two mass functions cannot be combined")
    return {focal: w / (1.0 - conflict) for focal, w in raw.items()}, conflict


def combine_all(masses: Iterable[Mass]) -> tuple[Mass, list[float]]:
    """Combine several mass functions in order; returns the result and the conflict at each step."""
    it = iter(masses)
    result = next(it)
    conflicts: list[float] = []
    for m in it:
        result, k = combine(result, m)
        conflicts.append(k)
    return result, conflicts


def condition(m: Mass, event: Iterable[Hashable]) -> Mass:
    """Dempster conditioning: combine with the certain evidence that the truth lies in `event`."""
    return combine(m, {frozenset(event): 1.0})[0]


def bel(m: Mass, event: Iterable[Hashable]) -> float:
    """Belief: the mass that is committed to `event` (focal sets inside it)."""
    e = frozenset(event)
    return sum(w for focal, w in m.items() if focal <= e)


def pl(m: Mass, event: Iterable[Hashable]) -> float:
    """Plausibility: the mass that does not contradict `event` (focal sets that meet it)."""
    e = frozenset(event)
    return sum(w for focal, w in m.items() if focal & e)


def pignistic(m: Mass) -> dict[Hashable, float]:
    """Pignistic transform: spread each focal set's mass evenly over its elements."""
    p: dict[Hashable, float] = {}
    for focal, w in m.items():
        share = w / len(focal)
        for x in focal:
            p[x] = p.get(x, 0.0) + share
    return p


def nonspecificity(m: Mass) -> float:
    """Generalized Hartley measure: sum of m(A) * log2|A|. Zero when all mass is on singletons."""
    return sum(w * log2(len(focal)) for focal, w in m.items())


def pignistic_entropy(m: Mass) -> float:
    """Shannon entropy (bits) of the pignistic distribution. Counts both imprecision and conflict."""
    return -sum(p * log2(p) for p in pignistic(m).values() if p > TOL)


# --------------------------------------------------------------------------------------
# Question selection (our own first design)
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Question:
    """A feature the bot can ask about.

    `answers` maps each possible answer to the set of routes that are compatible
    with it. The sets may overlap: a route that says nothing about the feature is
    compatible with every answer.
    """
    name: str
    text: str
    answers: Mapping[str, frozenset]


@dataclass(frozen=True)
class QuestionScore:
    question: Question
    expected_entropy: float      # expected pignistic entropy after the answer
    gain: float                  # current entropy minus expected entropy
    answer_probabilities: dict[str, float]


def answer_probabilities(m: Mass, question: Question) -> dict[str, float]:
    """Probability of each answer under the pignistic distribution.

    A route that is compatible with several answers divides its probability
    evenly over them.
    """
    probs = {a: 0.0 for a in question.answers}
    for route, p in pignistic(m).items():
        compatible = [a for a, routes in question.answers.items() if route in routes]
        for a in compatible:
            probs[a] += p / len(compatible)
    return probs


def score_question(m: Mass, question: Question) -> QuestionScore:
    probs = answer_probabilities(m, question)
    expected = 0.0
    for answer, p in probs.items():
        if p <= TOL:
            continue
        expected += p * pignistic_entropy(condition(m, question.answers[answer]))
    return QuestionScore(question, expected, pignistic_entropy(m) - expected, probs)


def rank_questions(m: Mass, questions: Iterable[Question]) -> list[QuestionScore]:
    """Questions ordered by expected information gain, best first."""
    return sorted((score_question(m, q) for q in questions), key=lambda s: -s.gain)


def decide(m: Mass, threshold: float = 0.6) -> Hashable | None:
    """Commit to a route when the belief in it alone reaches the threshold; otherwise None (ask)."""
    best = max(pignistic(m).items(), key=lambda kv: kv[1])[0]
    return best if bel(m, {best}) >= threshold else None

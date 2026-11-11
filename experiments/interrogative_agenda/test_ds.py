"""Checks on the Dempster-Shafer functions and on the toy example.

Run with:  venv/Scripts/python -m pytest experiments/interrogative_agenda/test_ds.py -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from ds import (bel, combine, combine_all, condition, decide, mass, nonspecificity,  # noqa: E402
                pignistic, pignistic_entropy, pl, rank_questions, vacuous)
from example import BESTELLING, EVIDENCE, FRAME, MERK, QUESTIONS, REPARATIE, ZOEKEN  # noqa: E402


def test_mass_must_sum_to_one_and_avoid_the_empty_set():
    with pytest.raises(ValueError):
        mass({("a",): 0.5})
    with pytest.raises(ValueError):
        mass({(): 0.2, ("a",): 0.8})


def test_vacuous_mass_is_neutral_in_combination():
    m = mass({("a",): 0.4, ("a", "b"): 0.6})
    combined, conflict = combine(m, vacuous({"a", "b", "c"}))
    assert conflict == 0
    assert combined == pytest.approx(m)


def test_dempster_rule_on_a_textbook_case():
    # Two sources over {a, b, c}: 0.6 on {a}, 0.4 ignorance; 0.5 on {b}, 0.5 ignorance.
    frame = ("a", "b", "c")
    m, conflict = combine(mass({("a",): 0.6, frame: 0.4}), mass({("b",): 0.5, frame: 0.5}))
    assert conflict == pytest.approx(0.3)
    assert m[frozenset({"a"})] == pytest.approx(0.3 / 0.7)
    assert m[frozenset({"b"})] == pytest.approx(0.2 / 0.7)
    assert m[frozenset(frame)] == pytest.approx(0.2 / 0.7)


def test_total_conflict_is_reported():
    with pytest.raises(ValueError):
        combine(mass({("a",): 1.0}), mass({("b",): 1.0}))


def test_belief_never_exceeds_plausibility_and_they_are_dual():
    m, _ = combine_all(EVIDENCE.values())
    for route in FRAME:
        assert bel(m, {route}) <= pl(m, {route}) + 1e-12
        assert pl(m, {route}) == pytest.approx(1 - bel(m, FRAME - {route}))
    assert sum(pignistic(m).values()) == pytest.approx(1)


def test_uncertainty_measures_at_the_extremes():
    assert nonspecificity(vacuous(FRAME)) == pytest.approx(2)        # log2(4)
    assert pignistic_entropy(vacuous(FRAME)) == pytest.approx(2)
    certain = mass({(REPARATIE,): 1.0})
    assert nonspecificity(certain) == 0
    assert pignistic_entropy(certain) == 0
    # Two singletons in conflict: fully specific, still one bit of uncertainty.
    split = mass({(REPARATIE,): 0.5, (MERK,): 0.5})
    assert nonspecificity(split) == 0
    assert pignistic_entropy(split) == pytest.approx(1)


def test_toy_example_asks_and_ranks_the_within_route_question_last():
    m, conflicts = combine_all(EVIDENCE.values())
    assert conflicts == [0, 0]
    assert decide(m) is None                       # the evidence does not single out a route
    assert bel(m, {REPARATIE}) < 0.6 < pl(m, {REPARATIE})
    ranking = rank_questions(m, QUESTIONS)
    assert ranking[0].question.name == "kapot"
    assert ranking[-1].question.name == "gekocht"
    assert all(s.gain >= -1e-9 for s in ranking)


def test_answer_settles_the_route():
    m, _ = combine_all(EVIDENCE.values())
    kapot = next(q for q in QUESTIONS if q.name == "kapot")
    after_ja = condition(m, kapot.answers["ja"])
    assert decide(after_ja) == REPARATIE
    after_nee = condition(m, kapot.answers["nee"])
    assert bel(after_nee, {REPARATIE}) == 0
    assert set(pignistic(after_nee)) <= {MERK, BESTELLING, ZOEKEN}

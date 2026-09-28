#!/usr/bin/env python
"""End-to-end checks for the knowledge graph: build it, ask it real SPARQL questions,
and compare the answers with the Python query templates in query.py.

    venv/Scripts/python -m pytest experiments/kg/test_kg.py -v
    venv/Scripts/python experiments/kg/test_kg.py          # same checks without pytest

The SPARQL queries run over the union of all named graphs (schema, vocabulary,
documents, inferred), which is what a runtime endpoint would expose. Each test
states the customer question it stands for, the query, and the reply we expect.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rdflib import Graph  # noqa: E402

from build import build, union  # noqa: E402
from query import KG, D, DRW, verbalise  # noqa: E402

PREFIXES = """
PREFIX drw: <https://derodewinkel.nl/kg/schema#>
PREFIX d:   <https://derodewinkel.nl/kg/data#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""

_cache = {}


def graph() -> Graph:
    """Build once per process: the union graph (asserted + inferred) for SPARQL."""
    if "g" not in _cache:
        ds, n_problems = build(write=False, quiet=True)
        assert n_problems == 0, "the graph must validate cleanly before the queries mean anything"
        _cache["ds"] = ds
        _cache["g"] = union(ds, include_inferred=True)
    return _cache["g"]


def kg() -> KG:
    graph()
    return KG(_cache["ds"])


def ask(q: str) -> bool:
    return bool(graph().query(PREFIXES + q).askAnswer)


def rows(q: str) -> list:
    return [tuple(r) for r in graph().query(PREFIXES + q)]


# ---- "Bezorgen jullie ook in Antwerpen?" -> ja (Europe covers Belgium covers Antwerp) -------

def test_ships_to_antwerp_is_derived():
    assert ask("ASK { d:Shipping drw:shipsTo d:Antwerp }")
    # and the chain is visible: Antwerp is part of Europe, which is a stated destination
    assert ask("ASK { d:Antwerp drw:partOf d:Europe . d:Shipping drw:shipsTo d:Europe }")
    v = kg().ships_to(D.Antwerp)
    assert v.verdict == "entailed" and v.inferred


def test_ships_to_usa_is_contradicted_by_completeness():
    assert not ask("ASK { d:Shipping drw:shipsTo d:USA }")
    assert ask("ASK { d:Shipping drw:completeFor drw:shipsTo }")
    assert kg().ships_to(D.USA).verdict == "contradicted"


# ---- "Tot hoe laat zijn jullie donderdag open?" -> 10:00-21:00 -------------------------------

def test_opening_hours_thursday():
    got = rows("""
        SELECT ?opens ?closes WHERE {
            d:Store drw:openingHours ?oh . ?oh drw:day d:Thursday ; drw:opens ?opens ; drw:closes ?closes .
        }""")
    assert (("10:00", "21:00") in {(str(a), str(b)) for a, b in got})
    v = kg().open_on(D.Thursday)
    assert v.verdict == "entailed" and v.values == ["10:00-21:00"]


def test_koopavond_links_to_thursday():
    got = rows('SELECT ?day WHERE { ?day skos:altLabel "koopavond"@nl }')
    assert (D.Thursday,) in got


def test_holiday_is_unknown():
    assert rows("SELECT ?oh WHERE { d:Store drw:openingHours ?oh . ?oh drw:day d:Koningsdag }") == []
    assert kg().open_on(D.Koningsdag).verdict == "unknown"


# ---- "Verkopen jullie sneakers?" -> nee (not selling shoes propagates down) -------------------

def test_sneakers_not_sold_is_derived():
    assert ask("ASK { d:DeRodeWinkel drw:doesNotSell d:Sneakers }")
    assert not ask("ASK { d:DeRodeWinkel drw:sells d:Sneakers }")
    v = kg().sells(D.Sneakers)
    assert v.verdict == "contradicted" and v.inferred


def test_jeans_sold_and_trousers_derived():
    # selling jeans is stated; selling trousers follows from it and is also stated elsewhere
    assert ask("ASK { d:DeRodeWinkel drw:sells d:Jeans }")
    assert ask("ASK { d:DeRodeWinkel drw:sells d:Trousers }")
    assert kg().sells(D.Jeans).verdict == "entailed"


def test_washing_machines_contradicted_by_top_level_completeness():
    # nothing states doesNotSell for white goods; the top-level list (kleding, accessoires) is complete
    assert not ask("ASK { d:DeRodeWinkel drw:doesNotSell d:WashingMachines }")
    assert ask("ASK { d:DeRodeWinkel drw:completeFor drw:sells }")
    assert kg().sells(D.WashingMachines).verdict == "contradicted"


# ---- "Kan ik met Klarna betalen?" / "Accepteren jullie Bancontact?" ---------------------------

def test_klarna_explicitly_refused_online():
    assert ask("ASK { d:Webshop drw:doesNotAccept d:Klarna }")
    assert kg().accepts(D.Klarna, D.Webshop).verdict == "contradicted"


def test_bancontact_unknown_overall_contradicted_online():
    assert rows("SELECT ?ch WHERE { ?ch drw:accepts d:Bancontact }") == []
    assert ask("ASK { d:Webshop drw:completeFor drw:accepts }")
    assert not ask("ASK { d:Store drw:completeFor drw:accepts }")
    v = kg().accepts(D.Bancontact)
    assert v.verdict == "unknown" and "Webshop: contradicted" in v.note and "Store: unknown" in v.note


def test_installments_contradicted_on_both_channels():
    # online: the webshop list is complete; in store: a curated explicit negative (not in the FAQ)
    assert ask("ASK { d:Store drw:doesNotAccept d:Installments }")
    assert not ask("ASK { d:Store drw:completeFor drw:accepts }")
    assert kg().accepts(D.Installments, D.Webshop).note == "accepted list is complete"
    assert kg().accepts(D.Installments, D.Store).note == "explicit doesNotAccept"
    v = kg().accepts(D.Installments)
    assert v.verdict == "contradicted" and "Webshop: contradicted" in v.note and "Store: contradicted" in v.note
    assert any("curated_store_payment" in str(g) for _, _, _, g in v.evidence)


# ---- "Kunnen jullie mijn Levi's repareren, ook als die niet van jullie is?" -------------------

def test_repair_applies_to_levis_through_the_tree():
    got = rows("SELECT ?svc WHERE { ?svc drw:appliesTo d:LevisJeans ; a drw:AtelierService }")
    assert {D.RepairService, D.AlterationService} <= {s for (s,) in got}
    # the statement itself is made once, for clothing
    assert ask("ASK { d:RepairService drw:appliesTo d:Clothing }")


def test_levis_bought_elsewhere_is_refused_but_nudie_is_not():
    # the only origin exception on file is for the Nudie brand line
    got = rows("""
        SELECT ?cat ?origin WHERE {
            ?rule a drw:OriginRule ; drw:forService d:RepairService ; drw:forCategory ?cat ; drw:allowsOrigin ?origin .
        }""")
    assert got == [(D.NudieJeansJeans, D.AnyOrigin)]
    assert kg().repairs(brand=D.Levis, origin=D.BoughtElsewhere).verdict == "contradicted"
    assert kg().repairs(brand=D.NudieJeans, origin=D.BoughtElsewhere).verdict == "entailed"
    assert kg().repairs(brand=D.Levis).verdict == "entailed"   # with the note that it must be bought here


# ---- evidence carries the source document ---------------------------------------------------

def test_evidence_cites_documents_and_inference():
    text = verbalise(kg().ships_to(D.Antwerp))
    assert "[inferred]" in text and "[doc:verzending_05]" in text


# ---- validation catches the conflict test files ---------------------------------------------

def test_conflict_files_are_reported():
    _, n = build(write=False, quiet=True, extra=[HERE / "tests" / "conflict_after_closure.ttl"])
    assert n >= 3
    _, n = build(write=False, quiet=True, extra=[HERE / "tests" / "conflict_completeness.ttl"])
    assert n == 3


if __name__ == "__main__":
    import inspect
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print(f"ok    {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL  {name}: {e}")
    print("all passed" if not failed else f"{failed} failed")
    sys.exit(1 if failed else 0)

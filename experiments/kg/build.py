#!/usr/bin/env python
"""Build the De Rode Winkel knowledge graph: load schema + vocabulary + one
named graph per converted document, validate, compute the OWL RL closure into
a separate `inferred` graph, validate again, and write everything as TriG.

    venv/Scripts/python experiments/kg/build.py                      # writes graph.trig, prints stats
    venv/Scripts/python experiments/kg/build.py --no-write
    venv/Scripts/python experiments/kg/build.py --no-write --extra-data tests/conflict_after_closure.ttl

Validation runs in two passes:
  pass 1  shapes WITHOUT `drw:phase drw:afterClosure`, on asserted data only
          (cardinality, datatypes, patterns, closed shapes)
  pass 2  shapes WITH the tag, on asserted + inferred data (conflicts that only
          appear once the property chains have fired), each violation reported
          with the documents that asserted the two sides
  plus    a completeness check across documents: a value asserted by document B
          for a (subject, property) that document A declared complete, and that
          is not in A's list. Needs named graphs, so it is Python, not SHACL.

Derived triples keep their provenance by living in <urn:drw:inferred>; every
asserted triple lives in <urn:drw:doc:<name>> (or <urn:drw:vocab> / <urn:drw:schema>).
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import owlrl
import pyshacl
from rdflib import BNode, Dataset, Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SH

HERE = Path(__file__).resolve().parent
DRW = Namespace("https://derodewinkel.nl/kg/schema#")
D = Namespace("https://derodewinkel.nl/kg/data#")
SCHEMA_G = URIRef("urn:drw:schema")
VOCAB_G = URIRef("urn:drw:vocab")
INFERRED_G = URIRef("urn:drw:inferred")
AFTER_CLOSURE = DRW.afterClosure


def doc_graph_name(stem: str) -> URIRef:
    return URIRef(f"urn:drw:doc:{stem}")


def load(here: Path = HERE, extra: list[Path] = ()) -> Dataset:
    ds = Dataset()
    ds.graph(SCHEMA_G).parse(here / "schema.ttl", format="turtle")
    ds.graph(VOCAB_G).parse(here / "vocab.ttl", format="turtle")
    for f in sorted((here / "data").glob("*.ttl")):
        ds.graph(doc_graph_name(f.stem)).parse(f, format="turtle")
    for f in extra:
        ds.graph(doc_graph_name(f.stem)).parse(f, format="turtle")
    return ds


def doc_graphs(ds: Dataset):
    return [g for g in ds.graphs() if str(g.identifier).startswith("urn:drw:doc:")]


def short(x) -> str:
    s = str(x)
    if s.startswith("urn:drw:doc:"):
        return "doc:" + s[len("urn:drw:doc:"):]
    return s.split("#")[-1] if "#" in s else s


def union(ds: Dataset, include_inferred: bool) -> Graph:
    g = Graph()
    for ctx in ds.graphs():
        if ctx.identifier == INFERRED_G and not include_inferred:
            continue
        for t in ctx:
            g.add(t)
    return g


def shapes_for_phase(ds: Dataset, after_closure: bool) -> Graph:
    """A COPY of the schema graph with the targets of the other phase's shapes removed
    (a shape without targets is inactive).

    The copy matters: this graph is handed to pyshacl, which writes into the graphs it
    is given (see run_shacl). The dataset's own schema graph must stay exactly what
    schema.ttl says, because the closure runs over it afterwards.
    """
    shapes = Graph()
    for t in ds.graph(SCHEMA_G):
        shapes.add(t)
    for shape in list(shapes.subjects(RDF.type, SH.NodeShape)):
        tagged = (shape, DRW.phase, AFTER_CLOSURE) in shapes
        if tagged != after_closure:
            shapes.remove((shape, SH.targetClass, None))
    return shapes


def run_shacl(data: Graph, shapes: Graph):
    """Validate `data` against `shapes`; return (conforms, [result dicts], report text).

    Both arguments must be throw-away copies. pyshacl mutates the graphs it receives:
    when the shapes graph doubles as `ont_graph` it adds vocabulary triples to it
    (`owl:Class rdfs:subClassOf rdfs:Class`, `owl:DatatypeProperty rdfs:subClassOf
    rdf:Property`), and with `ont_graph` set it mixes the ontology into the data graph.
    An earlier version of this file passed the dataset's live schema graph here; the
    injected triples then leaked into the OWL RL closure as 53 extra rdf:type triples.
    `union()` and `shapes_for_phase()` build fresh graphs, so the dataset is untouched.
    """
    conforms, results, text = pyshacl.validate(data, shacl_graph=shapes, ont_graph=shapes,
                                               inference="none", advanced=True)
    found = []
    for r in results.subjects(RDF.type, SH.ValidationResult):
        found.append({
            "focus": results.value(r, SH.focusNode),
            "path": results.value(r, SH.resultPath),
            "value": results.value(r, SH.value),
            "shape": results.value(r, SH.sourceShape),
            "message": str(results.value(r, SH.resultMessage) or ""),
        })
    return conforms, found, text


# ---- provenance for pass-2 conflicts -------------------------------------------------

def asserted(ds: Dataset, s, p, o):
    """(o, doc) for asserted triples (s, p, o) over the document graphs (o=None: any)."""
    out = []
    for g in doc_graphs(ds):
        for _, _, obj in g.triples((s, p, o)):
            out.append((obj, g.identifier))
    return out


def ancestors(ds: Dataset, cat) -> set:
    full = union(ds, include_inferred=True)
    return set(full.objects(cat, DRW.subcategoryOf))


def explain_conflict(ds: Dataset, focus, value, shape) -> str:
    """Name the asserted triples (with documents) behind an after-closure conflict."""
    pairs = {DRW.NoSellsConflictShape: (DRW.sells, DRW.doesNotSell, "up", "down"),
             DRW.NoAcceptConflictShape: (DRW.accepts, DRW.doesNotAccept, None, None),
             DRW.NoOfferConflictShape: (DRW.offers, DRW.doesNotOffer, None, None)}
    if shape not in pairs:
        return ""
    pos, neg, pos_dir, neg_dir = pairs[shape]
    anc = ancestors(ds, value) if pos_dir else set()
    full = union(ds, include_inferred=True)
    desc = set(full.subjects(DRW.subcategoryOf, value)) if pos_dir else set()
    pos_src = [(o, g) for o, g in asserted(ds, focus, pos, None) if o == value or o in desc]
    neg_src = [(o, g) for o, g in asserted(ds, focus, neg, None) if o == value or o in anc]
    fmt = lambda lst, p: ", ".join(f"{short(p)} {short(o)} [{short(g)}]" for o, g in lst) or "(no asserted source found)"
    return f"{fmt(pos_src, pos)}  <->  {fmt(neg_src, neg)}"


# ---- completeness check across documents ---------------------------------------------

def value_key(ds: Dataset, prop, value):
    """Comparable key for a value: blank nodes compare by their drw:day; sells at top level."""
    full = union(ds, include_inferred=True)
    if isinstance(value, BNode):
        return ("day", full.value(value, DRW.day))
    if prop == DRW.sells:
        tops = [a for a in ancestors(ds, value) | {value} if (a, DRW.subcategoryOf, D.Product) in ds.graph(VOCAB_G)]
        return ("top", tops[0] if tops else value)
    return ("v", value)


def completeness_check(ds: Dataset) -> list[str]:
    problems = []
    for g_a in doc_graphs(ds):
        for subj, _, prop in g_a.triples((None, DRW.completeFor, None)):
            listed = {value_key(ds, prop, v) for v in g_a.objects(subj, prop)}
            for g_b in doc_graphs(ds):
                if g_b.identifier == g_a.identifier:
                    continue
                for v in g_b.objects(subj, prop):
                    k = value_key(ds, prop, v)
                    if k not in listed:
                        shown = short(k[1]) if k[0] != "v" else short(v)
                        problems.append(f"{short(subj)} {short(prop)} {short(v)} [{short(g_b.identifier)}] is not in the list "
                                        f"that [{short(g_a.identifier)}] declared complete"
                                        + (f" (top level {shown})" if k[0] == "top" and k[1] != v else ""))
    return problems


# ---- closure ---------------------------------------------------------------------------

def closure(ds: Dataset) -> Graph:
    """OWL RL closure over the asserted union (schema + vocabulary + documents);
    returns only the NEW triples, minus bookkeeping (see _is_noise).

    Runs on a fresh copy of the union, so the dataset's graphs are not modified; the
    caller stores the result in the <urn:drw:inferred> graph. The count printed by
    build() is the size of this graph and should only change when schema.ttl,
    vocab.ttl or a document changes.
    """
    base = union(ds, include_inferred=False)
    work = Graph()
    for t in base:
        work.add(t)
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(work)
    new = Graph()
    for t in work:
        if t not in base and not _is_noise(t):
            new.add(t)
    return new


# rdf:type targets that are OWL/RDFS bookkeeping, never domain facts. The inferred graph
# is meant to hold derived facts about the shop (sells, appliesTo, shipsTo, ...), so a
# triple saying that drw:Brand is an rdfs:Class, or that drw:email is an rdf:Property,
# is filtered out. Without this filter the inferred-triple count depends on which
# vocabulary triples happen to be in the schema graph when the closure runs (see the
# note in run_shacl: pyshacl once injected two such triples and inflated the count
# from 491 to 544 without changing a single query result).
_BOOKKEEPING_TYPES = {
    str(OWL.Thing), str(OWL.NamedIndividual), str(OWL.Class), str(OWL.ObjectProperty),
    str(OWL.DatatypeProperty), str(OWL.AnnotationProperty),
    str(RDFS.Class), str(RDFS.Resource), str(RDF.Property),
}


def _is_noise(t) -> bool:
    """True for closure output that is not a domain fact.

    Dropped: self-loops (owl:sameAs x x), equivalence statements, rdf:type triples whose
    object is an OWL/RDFS vocabulary term (see _BOOKKEEPING_TYPES), and the class /
    property hierarchy (rdfs:subClassOf, rdfs:subPropertyOf), which OWL RL derives for
    the schema itself. Everything the query templates read passes through.
    """
    s, p, o = t
    if s == o:
        return True
    if p in (OWL.sameAs, OWL.equivalentClass, OWL.equivalentProperty):
        return True
    if p == RDF.type and str(o) in _BOOKKEEPING_TYPES:
        return True
    if p in (RDFS.subClassOf, RDFS.subPropertyOf):
        return True
    return False


# ---- build -----------------------------------------------------------------------------

def build(write: bool = True, here: Path = HERE, extra: list[Path] = (), quiet: bool = False) -> tuple[Dataset, int]:
    say = (lambda *a: None) if quiet else print
    ds = load(here, extra)
    n_problems = 0

    conforms, found, _ = run_shacl(union(ds, False), shapes_for_phase(ds, after_closure=False))
    say(f"SHACL pass 1 (asserted data): {'conforms' if conforms else f'{len(found)} violation(s)'}")
    for f in found:
        say(f"  {short(f['focus'])} {short(f['path'])} {short(f['value'])}: {f['message']}")
    n_problems += len(found)

    inferred = closure(ds)
    ig = ds.graph(INFERRED_G)
    for t in inferred:
        ig.add(t)

    conforms, found, _ = run_shacl(union(ds, True), shapes_for_phase(ds, after_closure=True))
    say(f"SHACL pass 2 (after closure): {'conforms' if conforms else f'{len(found)} violation(s)'}")
    for f in found:
        say(f"  {short(f['focus'])} / {short(f['value'])}: {f['message']}")
        say(f"      {explain_conflict(ds, f['focus'], f['value'], f['shape'])}")
    n_problems += len(found)

    problems = completeness_check(ds)
    say(f"completeness check: {'clean' if not problems else f'{len(problems)} clash(es)'}")
    for p in problems:
        say(f"  {p}")
    n_problems += len(problems)

    n_docs = len(doc_graphs(ds))
    n_asserted = sum(len(g) for g in doc_graphs(ds))
    say(f"documents converted: {n_docs}; asserted document triples: {n_asserted}; "
        f"vocabulary triples: {len(ds.graph(VOCAB_G))}; inferred triples: {len(inferred)}")
    if write:
        out = here / "graph.trig"
        ds.serialize(out, format="trig")
        say("written:", out)
    return ds, n_problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--extra-data", nargs="*", default=[], help="extra Turtle files loaded as documents (e.g. tests/conflict_*.ttl)")
    a = ap.parse_args()
    ds, n = build(write=not a.no_write, extra=[Path(p) if Path(p).is_absolute() else HERE / p for p in a.extra_data])
    sys.exit(1 if n else 0)

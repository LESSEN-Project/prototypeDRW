#!/usr/bin/env python
"""Entity linking from a customer's words to a vocabulary individual.

The hand-written mapping in suite_map.yml and demo.py stood in for this step. The
linker indexes every rdfs:label and skos:altLabel in the built dataset (vocabulary and
document graphs alike, so a label asserted by a document such as "koopavond" on
d:Thursday counts) and resolves a phrase in three passes, each restricted to the
classes the caller allows:

    1. the whole phrase equals a label (after normalisation)
    2. the longest label that occurs as a token sequence inside the phrase
    3. the same two passes on stemmed tokens, so "sneaker" finds "sneakers" and
       "wasmachine" finds "wasmachines"

Normalisation lowercases, strips accents and punctuation (so "Levi's" becomes "levi s"),
and collapses whitespace. The stemmer only removes a plural "-s", "-'s" or "-en", which
is enough for the category labels and keeps the module free of dependencies.

A phrase that matches labels of more than one individual in the allowed classes is
ambiguous and returns None with the candidates listed, so the caller can ask instead
of guessing. Class restriction resolves most of these: "cadeaukaart" is a payment
method and a service, and a payment question only allows drw:PaymentMethod.

    >>> from build import build; from link import Linker, DRW
    >>> lk = Linker(build(write=False, quiet=True)[0])
    >>> lk.link("spijkerbroek", DRW.ProductCategory).iri
    rdflib.term.URIRef('https://derodewinkel.nl/kg/data#Jeans')
"""
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Optional

from rdflib import Dataset, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import SKOS

DRW = Namespace("https://derodewinkel.nl/kg/schema#")
D = Namespace("https://derodewinkel.nl/kg/data#")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def stem(token: str) -> str:
    """Strip a Dutch plural ending; short tokens are left alone ("jeans", "pin", "cash")."""
    if len(token) > 5 and token.endswith("en"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


def stem_phrase(s: str) -> str:
    return " ".join(stem(t) for t in s.split())


@dataclass
class Link:
    iri: URIRef
    label: str            # the label that matched, as written in the graph
    matched: str          # the normalised text that matched it
    exact: bool           # True when the whole phrase matched, False for a sub-phrase
    stemmed: bool = False
    candidates: list = field(default_factory=list)   # other individuals the phrase also matched

    @property
    def name(self) -> str:
        return str(self.iri).split("#")[-1]

    def __str__(self) -> str:
        how = "exact" if self.exact else "contains"
        if self.stemmed:
            how += "+stem"
        return f"{self.name} <- '{self.matched}' ({how})"


class Linker:
    def __init__(self, ds: Dataset):
        self.classes: dict[URIRef, set] = {}        # individual -> its classes (with superclasses)
        self.labels: dict[str, dict[URIRef, str]] = {}   # normalised label -> {individual: label}
        self.stems: dict[str, dict[URIRef, str]] = {}
        superclasses = {}
        for ctx in ds.graphs():
            for c, _, parent in ctx.triples((None, RDFS.subClassOf, None)):
                superclasses.setdefault(c, set()).add(parent)
        for ctx in ds.graphs():
            for s, _, c in ctx.triples((None, RDF.type, None)):
                if isinstance(s, URIRef) and str(s).startswith(str(D)):
                    cs = self.classes.setdefault(s, set())
                    cs.add(c)
                    cs |= _ancestors(c, superclasses)
        for ctx in ds.graphs():
            for pred in (RDFS.label, SKOS.altLabel, SKOS.prefLabel):
                for s, _, lab in ctx.triples((None, pred, None)):
                    if s not in self.classes:
                        continue
                    n = norm(lab)
                    if not n:
                        continue
                    self.labels.setdefault(n, {}).setdefault(s, str(lab))
                    self.stems.setdefault(stem_phrase(n), {}).setdefault(s, str(lab))

    # -- public -------------------------------------------------------------
    def link(self, text: str, classes: Optional[Iterable[URIRef] | URIRef] = None) -> Optional[Link]:
        """The individual the phrase refers to, or None when nothing or several match."""
        if text is None:
            return None
        allowed = self._allowed(classes)
        n = norm(text)
        if not n:
            return None
        for stemmed, index, phrase in ((False, self.labels, n), (True, self.stems, stem_phrase(n))):
            hit = self._exact(phrase, index, allowed, stemmed)
            if hit is not None:
                return hit
            hit = self._contains(phrase, index, allowed, stemmed)
            if hit is not None:
                return hit
        return None

    def candidates(self, text: str, classes=None) -> list[URIRef]:
        """All individuals whose label equals the phrase (for reporting ambiguity)."""
        allowed = self._allowed(classes)
        hits = self.labels.get(norm(text), {})
        return [s for s in hits if allowed is None or self.classes[s] & allowed]

    # -- internals -----------------------------------------------------------
    def _allowed(self, classes) -> Optional[set]:
        if classes is None:
            return None
        if isinstance(classes, URIRef):
            return {classes}
        return set(classes)

    def _filter(self, hits: dict, allowed: Optional[set]) -> dict:
        if allowed is None:
            return hits
        return {s: lab for s, lab in hits.items() if self.classes[s] & allowed}

    def _exact(self, phrase, index, allowed, stemmed) -> Optional[Link]:
        hits = self._filter(index.get(phrase, {}), allowed)
        if not hits:
            return None
        return self._resolve(hits, phrase, exact=True, stemmed=stemmed)

    def _contains(self, phrase, index, allowed, stemmed) -> Optional[Link]:
        padded = f" {phrase} "
        best: list[tuple[str, dict]] = []
        for lab, hits in index.items():
            if f" {lab} " in padded:
                hits = self._filter(hits, allowed)
                if hits:
                    best.append((lab, hits))
        if not best:
            return None
        best.sort(key=lambda x: (-len(x[0].split()), -len(x[0])))
        longest = best[0][0].split().__len__()
        tied = [(lab, hits) for lab, hits in best if len(lab.split()) == longest]
        merged: dict[URIRef, str] = {}
        for lab, hits in tied:
            merged.update(hits)
        return self._resolve(merged, tied[0][0], exact=False, stemmed=stemmed)

    def _resolve(self, hits: dict, matched: str, exact: bool, stemmed: bool) -> Optional[Link]:
        if len(hits) == 1:
            (s, lab), = hits.items()
            return Link(s, lab, matched, exact, stemmed)
        # several individuals share the label: prefer the one whose canonical label it is
        canonical = [s for s, lab in hits.items() if norm(lab) == matched or stem_phrase(norm(lab)) == matched]
        if len(canonical) == 1:
            s = canonical[0]
            return Link(s, hits[s], matched, exact, stemmed, candidates=[c for c in hits if c != s])
        return None


def _ancestors(c, superclasses) -> set:
    out, todo = set(), [c]
    while todo:
        x = todo.pop()
        for p in superclasses.get(x, ()):
            if p not in out:
                out.add(p)
                todo.append(p)
    return out


if __name__ == "__main__":   # quick manual check: python link.py "spijkerbroek" [ClassName]
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from build import build
    lk = Linker(build(write=False, quiet=True)[0])
    text = sys.argv[1] if len(sys.argv) > 1 else "spijkerbroek"
    cls = DRW[sys.argv[2]] if len(sys.argv) > 2 else None
    print(lk.link(text, cls))

#!/usr/bin/env python
"""Query templates over the built graph with a three-valued verdict.

Every template returns a Verdict:
    entailed      the graph contains (or derives) the fact; `values`/`evidence` say what
    contradicted  the graph says the fact does not hold: an explicit negative, or an
                  empty result on a (subject, property) that is declared complete
    unknown       empty result and nothing declared complete: honest "geen informatie"

`evidence` lists the supporting triples with the named graph they came from, so a
verbaliser can cite documents; `inferred` is True when at least one supporting
triple came from the OWL RL closure rather than from a document.

Templates (the ~7 question shapes that cover the suite):
    sells(category)                       Verkopen jullie X?
    carries(brand)                        Hebben jullie merk X?
    accepts(payment, channel=None)        Kan ik met X betalen (online / in de winkel)?
    offers(service, category=None, brand=None, origin=None)
                                          Doen jullie X (voor Y, ook als elders gekocht)?
    open_on(day)                          Zijn jullie open op X? Tot hoe laat?
    ships_to(region)                      Bezorgen jullie in X?
    store_in(region)                      Hebben jullie een winkel in X?
    repairs(category, brand, origin, kind) Kunnen jullie X repareren/vermaken, ook als elders gekocht?
                                          (brand -> its brand lines; OriginRule on the category path overrides the default)
    fact(subject, property)               Wat is / hoeveel is ... ?
"""
from dataclasses import dataclass, field
from typing import Optional

from rdflib import Dataset, Literal, Namespace, RDF, URIRef

DRW = Namespace("https://derodewinkel.nl/kg/schema#")
D = Namespace("https://derodewinkel.nl/kg/data#")
INFERRED_G = URIRef("urn:drw:inferred")
SHOP = D.DeRodeWinkel


@dataclass
class Verdict:
    verdict: str                      # entailed | contradicted | unknown
    values: list = field(default_factory=list)
    evidence: list = field(default_factory=list)   # (s, p, o, graph)
    note: str = ""

    @property
    def inferred(self) -> bool:
        return any(g == INFERRED_G for *_, g in self.evidence)

    def __str__(self) -> str:
        v = f"{self.verdict}"
        if self.values:
            v += " " + ", ".join(_short(x) for x in self.values)
        if self.inferred:
            v += " (inferred)"
        if self.note:
            v += f" [{self.note}]"
        return v


def _short(x) -> str:
    if isinstance(x, Literal):
        return str(x)
    s = str(x)
    return s.split("#")[-1] if "#" in s else s


class KG:
    def __init__(self, ds: Dataset):
        self.ds = ds

    # -- low-level helpers -------------------------------------------------
    def triples(self, s=None, p=None, o=None):
        """Quads (s, p, o, graph) over all named graphs, asserted first."""
        out = []
        for ctx in self.ds.graphs():
            for t in ctx.triples((s, p, o)):
                out.append((*t, ctx.identifier))
        out.sort(key=lambda q: q[3] == INFERRED_G)
        return out

    def has(self, s, p, o) -> list:
        return self.triples(s, p, o)

    def objects(self, s, p) -> list:
        return [(o, g) for _, _, o, g in self.triples(s, p, None)]

    def complete(self, s, p) -> list:
        return self.has(s, DRW.completeFor, p)

    def is_a(self, s, cls) -> bool:
        return bool(self.has(s, RDF.type, cls))

    def ancestors(self, cat) -> set:
        return {o for o, _ in self.objects(cat, DRW.subcategoryOf)}

    # -- templates -----------------------------------------------------------
    def sells(self, category: URIRef) -> Verdict:
        ev = self.has(SHOP, DRW.sells, category)
        if ev:
            v = Verdict("entailed", [category], ev)
            if ev[0][3] == INFERRED_G:   # explain the chain: a sold subcategory
                for sub, g in self.objects(category, DRW.hasSubcategory):
                    direct = [q for q in self.has(SHOP, DRW.sells, sub) if q[3] != INFERRED_G]
                    if direct:
                        v.evidence += direct + [(sub, DRW.subcategoryOf, category, g)]
                        break
            return v
        neg = self.has(SHOP, DRW.doesNotSell, category)
        if neg:
            v = Verdict("contradicted", [], neg, "explicit doesNotSell")
            if neg[0][3] == INFERRED_G:
                for anc in self.ancestors(category):
                    direct = [q for q in self.has(SHOP, DRW.doesNotSell, anc) if q[3] != INFERRED_G]
                    if direct:
                        v.evidence += direct
                        break
            return v
        comp = self.complete(SHOP, DRW.sells)
        if comp:
            # completeness holds at the top level of the tree: the categories directly under d:Product
            tops = [a for a in self.ancestors(category) | {category}
                    if any(g != INFERRED_G for q in [None] for _, _, _, g in self.has(a, DRW.subcategoryOf, D.Product))]
            sold_top = [a for a in tops if any(g != INFERRED_G for *_, g in self.has(SHOP, DRW.sells, a))]
            if not sold_top:
                return Verdict("contradicted", [], comp,
                               f"top-level category {', '.join(_short(t) for t in tops)} is not sold and the top-level list is complete")
            return Verdict("unknown", [], [], "parent category is sold, this one is not listed")
        return Verdict("unknown")

    def carries(self, brand: URIRef) -> Verdict:
        ev = self.has(SHOP, DRW.carries, brand)
        if ev:
            return Verdict("entailed", [brand], ev)
        if self.complete(SHOP, DRW.carries):
            return Verdict("contradicted", [], self.complete(SHOP, DRW.carries))
        return Verdict("unknown", note="brand list is 'onder andere'")

    def list_brands(self) -> Verdict:
        objs = self.objects(SHOP, DRW.carries)
        if objs:
            return Verdict("entailed", [o for o, _ in objs], [(SHOP, DRW.carries, o, g) for o, g in objs])
        return Verdict("unknown")

    def accepts(self, payment: URIRef, channel: Optional[URIRef] = None) -> Verdict:
        channels = [channel] if channel is not None else [D.Webshop, D.Store]
        subs = {}
        for ch in channels:
            ev = self.has(ch, DRW.accepts, payment)
            if ev:
                subs[ch] = Verdict("entailed", [ch], ev)
                continue
            neg = self.has(ch, DRW.doesNotAccept, payment)
            if neg:
                subs[ch] = Verdict("contradicted", [ch], neg, "explicit doesNotAccept")
                continue
            comp = self.complete(ch, DRW.accepts)
            if comp:
                subs[ch] = Verdict("contradicted", [ch], comp, "accepted list is complete")
                continue
            subs[ch] = Verdict("unknown", [ch])
        if len(subs) == 1:
            return next(iter(subs.values()))
        # channel unspecified: entailed if any channel accepts; contradicted only if all do
        if any(v.verdict == "entailed" for v in subs.values()):
            ent = [v for v in subs.values() if v.verdict == "entailed"]
            return Verdict("entailed", [v.values[0] for v in ent], sum((v.evidence for v in ent), []),
                           "; ".join(f"{_short(c)}: {v.verdict}" for c, v in subs.items()))
        if all(v.verdict == "contradicted" for v in subs.values()):
            return Verdict("contradicted", [], sum((v.evidence for v in subs.values()), []),
                           "; ".join(f"{_short(c)}: {v.verdict}" for c, v in subs.items()))
        return Verdict("unknown", [], sum((v.evidence for v in subs.values()), []),
                       "; ".join(f"{_short(c)}: {v.verdict}" for c, v in subs.items()))

    def offers(self, service: URIRef, category: Optional[URIRef] = None, brand: Optional[URIRef] = None,
               origin: Optional[URIRef] = None) -> Verdict:
        ev = self.has(SHOP, DRW.offers, service)
        if not ev:
            if self.has(SHOP, DRW.doesNotOffer, service):
                return Verdict("contradicted", [], self.has(SHOP, DRW.doesNotOffer, service), "explicit doesNotOffer")
            if self.complete(SHOP, DRW.offers):
                return Verdict("contradicted", [], self.complete(SHOP, DRW.offers), "service list is complete")
            return Verdict("unknown")
        evidence = list(ev)
        if category is not None:
            app = self.has(service, DRW.appliesTo, category)
            if not app:
                return Verdict("unknown", [], evidence, f"service exists, no statement for {_short(category)}")
            evidence += app
            if app[0][3] == INFERRED_G:
                for anc in self.ancestors(category):
                    direct = [q for q in self.has(service, DRW.appliesTo, anc) if q[3] != INFERRED_G]
                    if direct:
                        evidence += direct + [(category, DRW.subcategoryOf, anc, INFERRED_G)]
                        break
        if brand is not None:   # a brand resolves to its brand lines (categories with ofBrand brand)
            lines = [q[0] for q in self.triples(None, DRW.ofBrand, brand)]
            appb = [q for line in lines for q in self.has(service, DRW.appliesTo, line)]
            if not appb:
                return Verdict("unknown", [], evidence, f"service exists, no statement for brand {_short(brand)}")
            evidence += appb[:1] + [(appb[0][2], DRW.ofBrand, brand, INFERRED_G)]
        if origin is not None:
            conds = self.objects(service, DRW.purchaseCondition)
            if conds:
                allowed = {c for c, _ in conds}
                if D.AnyOrigin in allowed or origin in allowed:
                    evidence += [(service, DRW.purchaseCondition, c, g) for c, g in conds]
                else:
                    return Verdict("contradicted", [], evidence + [(service, DRW.purchaseCondition, c, g) for c, g in conds],
                                   f"requires {', '.join(_short(c) for c in allowed)}")
            else:
                return Verdict("unknown", [], evidence, "no purchase condition recorded")
        values = [o for o, _ in self.objects(service, DRW.howTo)] + [o for o, _ in self.objects(service, DRW.discountPercent)]
        return Verdict("entailed", values, evidence)

    def depth(self, cat) -> int:
        return len(self.ancestors(cat))

    def origin_rule(self, service: URIRef, category: URIRef):
        """The most specific OriginRule for (service, category or an ancestor), or None."""
        best = None
        for rule, _ in [(q[0], q[3]) for q in self.triples(None, DRW.forService, service)]:
            for cat, _ in self.objects(rule, DRW.forCategory):
                if cat == category or cat in self.ancestors(category):
                    if best is None or self.depth(cat) > self.depth(best[1]):
                        best = (rule, cat)
        return best

    def repairs(self, category: Optional[URIRef] = None, brand: Optional[URIRef] = None,
                origin: Optional[URIRef] = None, kind: Optional[URIRef] = None) -> Verdict:
        """Kunnen jullie X repareren / vermaken (ook als elders gekocht)?

        One service per kind of work (RepairService, AlterationService). A service applies
        to a category when appliesTo covers it (the closure walks the tree down). The
        origin condition is the service's purchaseCondition unless an OriginRule on the
        category, or on the nearest ancestor, overrides it. A brand resolves to its brand
        lines (categories with ofBrand brand), narrowed to `category` when both are given.
        Entailed when some service applies and the origin passes; contradicted when
        services apply but the origin fails for all of them, or the category is never sold
        here; unknown when no service is stated to apply.
        """
        services = [q[0] for q in self.triples(None, RDF.type, DRW.AtelierService)
                    if self.has(SHOP, DRW.offers, q[0]) and (kind is None or q[0] == kind)]
        if not services:
            return Verdict("unknown", note="no atelier service offered")
        # resolve the product the customer means
        if brand is not None:
            lines = [q[0] for q in self.triples(None, DRW.ofBrand, brand)]
            if category is not None:
                narrowed = [l for l in lines if l == category or category in self.ancestors(l)]
                lines = narrowed or lines
            if not lines:
                return Verdict("unknown", note=f"no products of brand {_short(brand)} in the graph")
            candidates = lines
        elif category is not None:
            candidates = [category]
        else:
            candidates = [None]
        results = []
        for cat in candidates:
            if cat is not None and self.has(SHOP, DRW.doesNotSell, cat):
                results.append(Verdict("contradicted", [], self.has(SHOP, DRW.doesNotSell, cat),
                                       f"{_short(cat)} is not sold here, so it cannot have been bought here"))
                continue
            applicable, rejected = [], []
            for svc in services:
                ev = self.has(SHOP, DRW.offers, svc)[:1]
                if cat is not None:
                    app = self.has(svc, DRW.appliesTo, cat)
                    if not app:
                        continue
                    ev += app
                    if app[0][3] == INFERRED_G:
                        for anc in sorted(self.ancestors(cat), key=self.depth, reverse=True):
                            direct = [q for q in self.has(svc, DRW.appliesTo, anc) if q[3] != INFERRED_G]
                            if direct:
                                ev += direct + [(cat, DRW.subcategoryOf, anc, INFERRED_G)]
                                break
                # origin condition: rule on the path beats the service default
                rule = self.origin_rule(svc, cat) if cat is not None else None
                if rule:
                    allowed = {o for o, _ in self.objects(rule[0], DRW.allowsOrigin)}
                    ev += self.triples(rule[0], None, None)
                else:
                    allowed = {c for c, _ in self.objects(svc, DRW.purchaseCondition)}
                    ev += self.triples(svc, DRW.purchaseCondition, None)
                if origin is None or not allowed or D.AnyOrigin in allowed or origin in allowed:
                    applicable.append((svc, ev, allowed))
                else:
                    rejected.append((svc, ev, allowed))
            if applicable:
                svc, ev, allowed = applicable[0]
                note = ""
                if origin is None and allowed and D.AnyOrigin not in allowed:
                    note = "only for " + ", ".join(_short(c) for c in allowed)
                results.append(Verdict("entailed", [svc] + ([cat] if cat else []), sum((e for _, e, _ in applicable), []), note))
            elif rejected:
                results.append(Verdict("contradicted", [], sum((e for _, e, _ in rejected), []),
                                       "applicable services require " + ", ".join(sorted({_short(c) for _, _, cs in rejected for c in cs}))))
            else:
                results.append(Verdict("unknown", note="no atelier service is stated to apply"))
        ent = [r for r in results if r.verdict == "entailed"]
        if ent:
            return ent[0] if len(results) == 1 else Verdict("entailed", ent[0].values, sum((r.evidence for r in ent), []), ent[0].note)
        if results and all(r.verdict == "contradicted" for r in results):
            return results[0] if len(results) == 1 else Verdict("contradicted", [], sum((r.evidence for r in results), []), results[0].note)
        return results[0] if len(results) == 1 else Verdict("unknown", note="; ".join(r.note for r in results if r.note))

    def open_on(self, day: URIRef) -> Verdict:
        store = D.Store
        for oh, g in self.objects(store, DRW.openingHours):
            if self.has(oh, DRW.day, day):
                opens = [o for o, _ in self.objects(oh, DRW.opens)]
                closes = [o for o, _ in self.objects(oh, DRW.closes)]
                ev = [(store, DRW.openingHours, oh, g)] + self.has(oh, DRW.day, day)
                return Verdict("entailed", [f"{opens[0]}-{closes[0]}"] if opens and closes else [], ev)
        if self.is_a(day, DRW.Holiday) and self.has(store, DRW.holidayHoursMayDiffer, Literal(True)):
            return Verdict("unknown", [], self.has(store, DRW.holidayHoursMayDiffer, Literal(True)), "holiday hours may differ")
        comp = self.complete(store, DRW.openingHours)
        if comp and self.is_a(day, DRW.Weekday):
            return Verdict("contradicted", [], comp, "closed that day: weekly hours are complete")
        return Verdict("unknown")

    def ships_to(self, region: URIRef) -> Verdict:
        ship = D.Shipping
        ev = self.has(ship, DRW.shipsTo, region)
        if ev:
            v = Verdict("entailed", [region], ev)
            if ev[0][3] == INFERRED_G:
                for anc, g in self.objects(region, DRW.partOf):
                    direct = [q for q in self.has(ship, DRW.shipsTo, anc) if q[3] != INFERRED_G]
                    if direct:
                        v.evidence += direct + [(region, DRW.partOf, anc, g)]
                        break
            fees = self.objects(ship, DRW.internationalFeeMinEur) + self.objects(ship, DRW.internationalFeeMaxEur)
            v.values += [o for o, _ in fees]
            return v
        comp = self.complete(ship, DRW.shipsTo)
        if comp:
            return Verdict("contradicted", [], comp, "destination list is complete")
        return Verdict("unknown")

    def store_in(self, region: URIRef) -> Verdict:
        hits = []
        for store, g in self.objects(SHOP, DRW.hasStore):
            loc = self.has(store, DRW.locatedIn, region)
            if loc:
                hits += [(SHOP, DRW.hasStore, store, g)] + loc
        if hits:
            return Verdict("entailed", [region], hits)
        comp = self.complete(SHOP, DRW.hasStore)
        if comp:
            return Verdict("contradicted", [], comp, "store list is complete")
        return Verdict("unknown")

    def fact(self, subject: URIRef, property: URIRef) -> Verdict:
        prop = property
        objs = self.objects(subject, prop)
        if objs:
            return Verdict("entailed", [o for o, _ in objs], [(subject, prop, o, g) for o, g in objs])
        comp = self.complete(subject, prop)
        if comp:
            return Verdict("contradicted", [], comp, "value list is complete and empty")
        return Verdict("unknown")

    def run(self, template: str, args: dict) -> Verdict:
        fn = getattr(self, template)
        return fn(**{k: _to_uri(v) for k, v in args.items()})


def _to_uri(v):
    if v is None:
        return None
    if isinstance(v, str):
        if v.startswith("d:"):
            return D[v[2:]]
        if v.startswith("drw:"):
            return DRW[v[4:]]
    return v


def verbalise(v: Verdict) -> str:
    """Evidence as short Dutch-ish lines a verbaliser could pass to the answer model."""
    lines = []
    for s, p, o, g in v.evidence:
        src = str(g).replace("urn:drw:doc:", "doc:").replace("urn:drw:", "")
        lines.append(f"{_short(s)} {_short(p)} {_short(o)}  [{src}]")
    return "\n".join(lines)

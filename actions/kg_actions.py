"""Custom actions that answer a question from the knowledge graph in experiments/kg.

Each action belongs to one flow in data/flows.yml and one query template in
experiments/kg/query.py. The command generator starts the flow and fills its slots with
the customer's own words; the action links each slot value to a vocabulary individual
(experiments/kg/link.py), runs the template, and utters a Dutch sentence that follows
from the verdict, with the source documents named. The verdict is written to the
`kg_verdict` slot so the flow can fall through to retrieval when the graph does not
settle the question.

The graph is built once per process (schema + vocabulary + documents, SHACL, OWL RL
closure; about two seconds) on the first question.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

KG_DIR = Path(__file__).resolve().parents[1] / "experiments" / "kg"
if str(KG_DIR) not in sys.path:
    sys.path.insert(0, str(KG_DIR))

from build import build        # noqa: E402
from link import Linker, DRW, D  # noqa: E402
from query import KG, Verdict, INFERRED_G  # noqa: E402

_state: Dict[str, Any] = {}


def graph() -> tuple:
    if "kg" not in _state:
        ds, n_problems = build(write=False, quiet=True)
        if n_problems:
            raise RuntimeError(f"knowledge graph build reported {n_problems} problem(s); run experiments/kg/build.py")
        _state["kg"] = KG(ds)
        _state["linker"] = Linker(ds)
    return _state["kg"], _state["linker"]


def label_of(kg: KG, iri) -> str:
    """The canonical Dutch label of an individual, or its local name."""
    from rdflib import RDFS
    for _, _, lab, _ in kg.triples(iri, RDFS.label, None):
        return str(lab)
    return str(iri).split("#")[-1]


def sources(v: Verdict) -> str:
    docs = []
    for *_, g in v.evidence:
        name = str(g).replace("urn:drw:doc:", "")
        if g != INFERRED_G and not name.startswith("urn:drw:") and name not in docs:
            docs.append(name)
    parts = []
    if docs:
        parts.append("bron: " + ", ".join(docs))
    if v.inferred:
        parts.append("deels afgeleid door de reasoner")
    return f" ({'; '.join(parts)})" if parts else ""


CHANNEL = {"online": D.Webshop, "winkel": D.Store}
ORIGIN = {"hier": D.BoughtAtDRW, "elders": D.BoughtElsewhere}
CHANNEL_NL = {D.Webshop: "online", D.Store: "in de winkel"}


class KGAction(Action):
    """Shared machinery: link the slots, run the template, say the answer, set kg_verdict."""

    template: str = ""
    linked_slots: Dict[str, Any] = {}     # slot name -> (template argument, allowed class)
    fixed_slots: Dict[str, Any] = {}      # slot name -> (template argument, value map)

    def name(self) -> Text:
        return f"action_kg_{self.template}"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        kg, linker = graph()
        formal = tracker.get_slot("klant_register") == "formeel"
        args: Dict[str, Any] = {}
        words: Dict[str, str] = {}
        for slot, (arg, cls) in self.linked_slots.items():
            text = tracker.get_slot(slot)
            link = linker.link(text, cls) if text else None
            if link is None:
                # nothing to say: the flow falls through to retrieval, and the slot records why
                return [SlotSet("kg_verdict", "unlinked"), SlotSet("kg_bron", None)]
            args[arg] = link.iri
            words[arg] = text
        for slot, (arg, mapping) in self.fixed_slots.items():
            value = mapping.get(tracker.get_slot(slot))
            if value is not None:
                args[arg] = value
        verdict = kg.run(self.template, args)
        if verdict.verdict == "unknown":
            # silent fall-through: a graph sentence here would be repeated by the retrieval
            # answer that follows, since it sees the conversation context
            return [SlotSet("kg_verdict", "unknown"), SlotSet("kg_bron", sources(verdict).strip(" ()") or None)]
        text = self.answer(kg, verdict, args, formal) + sources(verdict)
        dispatcher.utter_message(text=text)
        return [SlotSet("kg_verdict", verdict.verdict),
                SlotSet("kg_bron", sources(verdict).strip(" ()") or None)]

    def answer(self, kg: KG, v: Verdict, args: Dict[str, Any], formal: bool) -> str:
        raise NotImplementedError


class ActionKGSells(KGAction):
    template = "sells"
    linked_slots = {"product_categorie": ("category", DRW.ProductCategory)}

    def answer(self, kg, v, args, formal):
        cat = label_of(kg, args["category"])
        if v.verdict == "entailed":
            return f"Ja, {cat} verkopen we."
        if v.verdict == "contradicted":
            return f"Nee, {cat} verkopen we niet."
        raise AssertionError("unknown verdicts never reach answer()")


class ActionKGAccepts(KGAction):
    template = "accepts"
    linked_slots = {"betaalmethode": ("payment", DRW.PaymentMethod)}
    fixed_slots = {"kanaal": ("channel", CHANNEL)}

    def answer(self, kg, v, args, formal):
        pay = label_of(kg, args["payment"])
        paying = pay if pay.endswith("betalen") else f"met {pay} betalen"   # "in termijnen betalen" vs "met iDEAL betalen"
        u = "kunt u" if formal else "kun je"
        asked = args.get("channel")
        if v.verdict == "entailed":
            where = " en ".join(CHANNEL_NL[c] for c in v.values if c in CHANNEL_NL) or CHANNEL_NL.get(asked, "")
            return f"Ja, {where} {u} {paying}."
        if v.verdict == "contradicted":
            where = CHANNEL_NL.get(asked, "online en in de winkel")
            return f"Nee, {paying} kan {where} niet."
        raise AssertionError("unknown verdicts never reach answer()")


class ActionKGShipsTo(KGAction):
    template = "ships_to"
    linked_slots = {"regio": ("region", DRW.Region)}

    def answer(self, kg, v, args, formal):
        region = label_of(kg, args["region"])
        if v.verdict == "entailed":
            fees = [str(x) for x in v.values[1:]]
            extra = f" De verzendkosten zijn {fees[0]} tot {fees[1]} euro." if len(fees) == 2 else ""
            return f"Ja, we bezorgen in {region}.{extra}"
        if v.verdict == "contradicted":
            return f"Nee, we bezorgen niet in {region}."
        raise AssertionError("unknown verdicts never reach answer()")


class ActionKGOpenOn(KGAction):
    template = "open_on"
    linked_slots = {"dag": ("day", DRW.Day)}

    def answer(self, kg, v, args, formal):
        day = label_of(kg, args["day"])
        if v.verdict == "entailed":
            hours = str(v.values[0]).replace("-", " tot ") if v.values else ""
            return f"Ja, op {day} zijn we open" + (f" van {hours} uur." if hours else ".")
        if v.verdict == "contradicted":
            return f"Nee, op {day} zijn we gesloten."
        raise AssertionError("unknown verdicts never reach answer()")


class ActionKGRepairs(KGAction):
    template = "repairs"
    linked_slots = {"merk": ("brand", DRW.Brand)}
    fixed_slots = {"herkomst": ("origin", ORIGIN)}

    def answer(self, kg, v, args, formal):
        brand = label_of(kg, args["brand"])
        origin = args.get("origin")
        bought = {D.BoughtElsewhere: " die ergens anders is gekocht", D.BoughtAtDRW: " die bij ons is gekocht"}.get(origin, "")
        if v.verdict == "entailed":
            cond = " Dat geldt voor artikelen die bij ons zijn gekocht." if v.note.startswith("only for") else ""
            return f"Ja, een {brand}{bought} kunnen we in ons atelier repareren.{cond}"
        if v.verdict == "contradicted":
            return f"Nee, een {brand}{bought} kunnen we niet repareren; reparatie geldt voor artikelen die bij ons zijn gekocht."
        raise AssertionError("unknown verdicts never reach answer()")


# ---- added 2026-11-10: carries, offers, fact, offers_fit ------------------------------------

class ActionKGCarries(KGAction):
    template = "carries"
    linked_slots = {"merk": ("brand", DRW.Brand)}

    def answer(self, kg, v, args, formal):
        brand = label_of(kg, args["brand"])
        if v.verdict == "entailed":
            return f"Ja, {brand} voeren we."
        if v.verdict == "contradicted":
            return f"Nee, {brand} voeren we niet."
        raise AssertionError("unknown verdicts never reach answer()")


def first_literal(kg: KG, node, prop) -> Optional[tuple]:
    """The FAQ answer stored on `node` under `prop`, with its graph. When several documents
    describe the same service the longest answer is taken, document name as tie-break, so the
    customer gets the fullest sentence (decision 2026-11-10: uttered verbatim and cited)."""
    quads = [q for q in kg.triples(node, prop, None) if q[3] != INFERRED_G]
    if not quads:
        return None
    best = max(quads, key=lambda q: len(str(q[2])))   # quads are in document-name order; max keeps the first on ties
    return best[2], best[3]


class ActionKGOffers(KGAction):
    """Bieden jullie X? / Hoe werkt X? The answer is the FAQ sentence stored on the service."""
    template = "offers"
    linked_slots = {"dienst": ("service", DRW.Service)}

    async def run(self, dispatcher, tracker, domain):
        kg, linker = graph()
        text = tracker.get_slot("dienst")
        link = linker.link(text, DRW.Service) if text else None
        if link is None:
            return [SlotSet("kg_verdict", "unlinked"), SlotSet("kg_bron", None)]
        verdict = kg.run("offers", {"service": link.iri})
        if verdict.verdict == "unknown":
            return [SlotSet("kg_verdict", "unknown"), SlotSet("kg_bron", None)]
        service = label_of(kg, link.iri)
        if verdict.verdict == "contradicted":
            answer, src = f"Nee, {service} bieden we niet aan.", sources(verdict)
        else:
            lit = first_literal(kg, link.iri, DRW.howTo)
            if lit is not None:
                answer = str(lit[0])
                src = f" (bron: {str(lit[1]).replace('urn:drw:doc:', '')})"
            else:
                answer, src = f"Ja, {service} bieden we aan.", sources(verdict)
        dispatcher.utter_message(text=answer + src)
        return [SlotSet("kg_verdict", verdict.verdict), SlotSet("kg_bron", src.strip(" ()") or None)]


# feit slot value -> (subject, property, sentence with {v}); the unit is part of the sentence
FACTS = {
    "adres":             (D.Store, DRW.streetAddress, "Ons adres is {v}."),
    "postcode":          (D.Store, DRW.postalCode, "De postcode van de winkel is {v}."),
    "telefoonnummer":    (D.DeRodeWinkel, DRW.phone, "Ons telefoonnummer is {v}."),
    "e-mailadres":       (D.DeRodeWinkel, DRW.email, "Ons e-mailadres is {v}."),
    "bezorger":          (D.Shipping, DRW.carrier, "Pakketten worden bezorgd door {v}."),
    "verzendkosten":     (D.Shipping, DRW.shippingFeeBelowThresholdEur, "De verzendkosten zijn {v} euro."),
    "gratis_verzending": (D.Shipping, DRW.freeShippingFromEur, "Vanaf {v} euro is de verzending gratis."),
    "levertijd":         (D.Shipping, DRW.deliveryWithinHours, "De levertijd is {v} uur."),
    "retourkosten":      (D.ReturnByPost, DRW.feeEur, "De retourkosten per post zijn {v} euro."),
    "retourtermijn":     (D.ReturnByPost, DRW.windowDays, "Retourneren kan binnen {v} dagen."),
    "terugbetaling":     (D.ReturnByPost, DRW.refundProcessingDays, "Een retour wordt binnen {v} dagen terugbetaald."),
    "garantie":          (D.Jeans, DRW.warrantyMonthsMin, "Op jeans geldt minimaal {v} maanden garantie."),
    "reactietermijn":    (D.Complaints, DRW.responseWithinDays, "Op een klacht reageren we binnen {v} dagen."),
    "opgericht":         (D.DeRodeWinkel, DRW.foundedOn, "De Rode Winkel is opgericht op {v}."),
    "spaarpercentage":   (D.Membership, DRW.savingsPercent, "Als member spaar je {v} procent van je aankoopbedrag."),
    "studentenkorting":  (D.StudentDiscount, DRW.discountPercent, "Studenten krijgen {v} procent korting."),
    "paypal_toeslag":    (D.PayPal, DRW.surchargePercent, "Bij betalen met PayPal rekenen we {v} procent toeslag."),
    "account_verplicht": (D.Webshop, DRW.requiresAccount, None),
    "sale_nabestellen":  (D.SpecialSizeOrder, DRW.saleItemsReorderable, None),
}
BOOL_SENTENCES = {
    "account_verplicht": ("Ja, voor een bestelling is een account verplicht.", "Nee, bestellen kan ook zonder account."),
    "sale_nabestellen":  ("Ja, sale-artikelen kunnen worden nabesteld.", "Nee, sale-artikelen kunnen niet worden nabesteld."),
}


class ActionKGFact(KGAction):
    """Wat is / hoeveel is ...? One (subject, property) pair per allowed slot value."""
    template = "fact"

    async def run(self, dispatcher, tracker, domain):
        kg, _ = graph()
        key = tracker.get_slot("feit")
        if key not in FACTS:
            return [SlotSet("kg_verdict", "unlinked"), SlotSet("kg_bron", None)]
        subject, prop, sentence = FACTS[key]
        verdict = kg.run("fact", {"subject": subject, "property": prop})
        if verdict.verdict == "unknown":
            return [SlotSet("kg_verdict", "unknown"), SlotSet("kg_bron", None)]
        if verdict.verdict == "contradicted":
            answer = "Daar is geen waarde voor vastgelegd."
        elif sentence is None:
            yes, no = BOOL_SENTENCES[key]
            answer = yes if verdict.values[0].toPython() else no
        else:
            value = verdict.values[0]
            v = value.toPython()
            if isinstance(v, float) or (hasattr(v, "as_integer_ratio") and not isinstance(v, (bool, int))):
                v = f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")
            answer = sentence.format(v=v)
        if tracker.get_slot("klant_register") == "formeel":
            answer = answer.replace("spaar je", "spaart u").replace("je aankoopbedrag", "uw aankoopbedrag")
        dispatcher.utter_message(text=answer + sources(verdict))
        return [SlotSet("kg_verdict", verdict.verdict), SlotSet("kg_bron", sources(verdict).strip(" ()") or None)]


AUDIENCE = {"dames": D.Women, "heren": D.Men}
AUDIENCE_NL = {D.Women: "dames", D.Men: "heren"}


class ActionKGOffersFit(KGAction):
    template = "offers_fit"
    linked_slots = {"jeansmodel": ("fit", DRW.FitModel)}
    fixed_slots = {"doelgroep": ("audience", AUDIENCE)}

    def answer(self, kg, v, args, formal):
        fit = label_of(kg, args["fit"])
        asked = args.get("audience")
        if v.verdict == "entailed":
            who = sorted({AUDIENCE_NL[a] for c in v.values for a, _ in kg.objects(c, DRW.forAudience) if a in AUDIENCE_NL})
            return f"Ja, {fit} hebben we voor {' en '.join(who)}." if who else f"Ja, {fit} hebben we."
        if v.verdict == "contradicted":
            who = AUDIENCE_NL.get(asked)
            return f"Nee, {fit} hebben we niet voor {who}." if who else f"Nee, {fit} hebben we niet."
        raise AssertionError("unknown verdicts never reach answer()")

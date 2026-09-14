#!/usr/bin/env python
"""Generate the contrastive evaluation suite and its ground-truth sidecar.

Writes:
  tests/test_contrastive_suite.yml           e2e cases, deterministic assertions only
  experiments/contrastive/ground_truth.yml   case name -> ground truth (offline judge)

Every case ends with a capture assertion (`bot_uttered` with a regex that can
never match), so Rasa records the full transcript, including the bot's answer,
for every case. aggregate.py treats a failure on that assertion as "all real
assertions passed".

Near-miss cases carry `absent` keywords; the generator greps docs/ and refuses
to write the suite if any keyword occurs, so the "fact is missing" claim stays
verified against the current knowledge base.

Run: venv/Scripts/python experiments/contrastive/build_suite.py
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SUITE_PATH = ROOT / "tests" / "test_contrastive_suite.yml"
GT_PATH = Path(__file__).resolve().parent / "ground_truth.yml"

ABSTAIN = "utter_no_relevant_answer_found"
INFRA = "utter_internal_error_rasa"
CAPTURE_REGEX = "(?!)"  # never matches: forces a failure that carries the transcript

# --------------------------------------------------------------------------- #
# A: answerable. Each entry: slug, [question, paraphrase...], ground truth.
# --------------------------------------------------------------------------- #
ANSWERABLE = [
    ("retouren - terugsturen kosten",
     ["Wat kost het om iets terug te sturen?", "Zijn er kosten verbonden aan een retour?"],
     "Retourkosten bedragen €7 en worden achteraf verrekend. Bij ruilen zijn er geen kosten, ook niet bij bestellingen onder €49. Artikelen kunnen binnen 14 dagen na ontvangst worden geretourneerd, mits in originele staat, via het retourportaal. Aankopen met een cadeaukaart worden teruggestort als tegoedbon, niet als contant geld."),
    ("retouren - online aankoop in winkel terugbrengen",
     ["Kan ik iets wat ik online gekocht heb ook gewoon in de winkel terugbrengen?", "Ik heb online besteld, mag ik het ruilen in jullie winkel in Utrecht?"],
     "Artikelen kunnen binnen 14 dagen na aankoop in originele staat worden teruggebracht naar de fysieke winkel op Lange Elisabethstraat 13, 3511 JA Utrecht. Terugbetalingen worden direct afgehandeld bij de kassa zonder formulier. Ruilen voor andere artikelen is mogelijk, met directe prijsaanpassing. Retourneren per post kan ook, binnen 14 dagen na ontvangst via het retourportaal; retourkosten van €7 worden achteraf verrekend."),
    ("retouren - wanneer geld terug",
     ["Wanneer zie ik m'n geld weer op m'n rekening na een retour?", "Hoe snel wordt mijn retour terugbetaald?"],
     "Verwachte aankomsttijd van de retour bij De Rode Winkel is binnen 48 uur. Verwerking duurt 3 dagen, waarna je een e-mailbevestiging ontvangt. De terugbetaling verschijnt op de originele betaalmethode, verminderd met de €7 retourkosten. Aankopen met een cadeaukaart worden teruggestort als tegoedbon."),
    ("verzending - verzendkosten en drempel",
     ["Vanaf welk bedrag hoef ik geen verzendkosten te betalen?", "Wat zijn de verzendkosten?"],
     "Bestellingen van €49 of meer worden gratis verzonden. Bij bestellingen onder €49 bedragen de verzendkosten €6,96. Internationale verzending naar Europese landen kost €10 tot €15. Er wordt verzonden naar alle landen in Europa."),
    ("verzending - bezorging Belgie",
     ["Bezorgen jullie ook in België?", "Kunnen jullie naar een adres in Antwerpen versturen?"],
     "Er wordt verzonden naar alle landen in Europa, dus ook naar België. Internationale verzending naar Europese landen kost €10 tot €15. Bestellingen worden verzonden via PostNL; als het pakket verstuurd is ontvang je van PostNL meer informatie over het levermoment."),
    ("verzending - levertijd",
     ["Als ik vandaag bestel, wanneer heb ik het dan in huis?", "Hoe lang duurt de levering?"],
     "Bestellingen die op werkdagen vóór 16:00 uur geplaatst worden, worden dezelfde dag nog verzonden. Levering is over het algemeen binnen 48 uur. Bestellingen worden verzonden via PostNL; na verzending ontvang je van PostNL een link met track & trace en informatie over het levermoment."),
    ("verzending - niet thuis bij bezorging",
     ["De bezorger was net geweest toen ik niet thuis was, hoe gaat dat nu verder?", "Wat gebeurt er met m'n pakket als niemand opendoet?"],
     "De vervoerder probeert de bezorging opnieuw. Houd je track & trace link in de gaten voor updates over het nieuwe levermoment. Bij problemen met de bezorging kun je contact opnemen via WhatsApp of e-mail met je ordernummer en een beschrijving van het probleem."),
    ("bestellen - account verplicht",
     ["Moet ik verplicht een account hebben om iets te kopen?", "Kan ik als gast afrekenen zonder in te loggen?"],
     "Online bestellen kan ook zonder account. Met een account kun je je aankopen inzien, zien welke maat je hebt gekocht, en als member spaar je punten die je kunt inzetten als korting."),
    ("producten - maat uitverkocht",
     ["Mijn maat is online uitverkocht, kan ik 'm toch nog ergens krijgen?", "Kunnen jullie een maat nabestellen die niet meer op voorraad is?"],
     "Er is wekelijks nieuwe voorraad. Klanten kunnen via het productformulier een speciale bestelling voor een specifieke maat aanvragen. Sale-artikelen kunnen niet worden nabesteld, maar er worden alternatieven gesuggereerd. De winkelvoorraad is ook de webshopvoorraad; de voorraad die je online ziet is geen garantie omdat artikelen tegelijk in de winkel kunnen verkopen."),
    ("betalen - achteraf betalen",
     ["Kan ik m'n bestelling ook achteraf betalen?", "Is betalen na ontvangst mogelijk?"],
     "Ja, achteraf betalen kan met Billink. Klik op Billink bij het afrekenen en de stappen volgen vanzelf. Met Billink heb je tot 14 dagen na ontvangst om te betalen. Klarna en Afterpay worden niet geaccepteerd. Andere betaalmogelijkheden in de webshop zijn iDEAL, WERO, Creditcard, PayPal, Apple Pay en de online cadeaukaart."),
    ("betalen - PayPal toeslag",
     ["Zitten er extra kosten aan als ik met PayPal betaal?", "Is PayPal duurder dan iDEAL bij jullie?"],
     "Ja, bij betalen met PayPal geldt een toeslag van 3,20%. Klik op PayPal bij het afrekenen en volg de stappen. Bij iDEAL wordt geen toeslag genoemd: je selecteert iDEAL bij het afrekenen, kiest je bank en rondt de betaling af in je eigen bankomgeving."),
    ("betalen - Klarna (negative answer)",
     ["Kan ik met Klarna betalen?", "Werken jullie met Klarna of Afterpay?"],
     "Nee, Klarna en Afterpay worden niet geaccepteerd. Achteraf betalen kan wel met Billink: klik op Billink bij het afrekenen, je hebt dan tot 14 dagen na ontvangst om te betalen. Andere betaalmogelijkheden zijn iDEAL, WERO, Creditcard, PayPal, Apple Pay en de online cadeaukaart."),
    ("kortingscode - studentenkorting",
     ["Krijg ik korting als student?", "Ik studeer aan de HU, hebben jullie iets voor studenten?"],
     "Studenten ontvangen 10% korting. In de winkel toon je je studentenpas; online vul je een formulier in met je naam, studie, instelling en een foto van je studentenpas, waarna je een kortingscode ontvangt."),
    ("cadeaukaart - cadeaubon online gebruiken",
     ["Ik heb een cadeaubon gekregen, kan ik die op de site gebruiken?", "Hoe verzilver ik een cadeaukaart in de webshop?"],
     "Ja, een cadeaubon is op de site te gebruiken. Fysieke cadeaukaarten kunnen worden omgezet naar een online code door een e-mail te sturen naar info@derodewinkel.nl of een bericht via de WhatsApp-knop onderaan de pagina, met de barcodegegevens. Je krijgt dan een nieuwe code voor de webshop om mee te betalen. De online cadeaukaart voer je in bij het afrekenen na het invullen van je adres."),
    ("cadeaukaart - VVV-bon online (negative answer)",
     ["Kan ik online afrekenen met een VVV-bon?", "Nemen jullie Fashioncheques aan?"],
     "De kaarten van VVV en Fashioncheque werken niet op de website, maar zijn wel in de winkel in Utrecht in te leveren. De online cadeaukaart van De Rode Winkel werkt alleen in de webshop. Fysieke cadeaukaarten van De Rode Winkel kunnen worden omgezet voor online gebruik via info@derodewinkel.nl."),
    ("maatadvies - welke jeans past bij figuur",
     ["Welke spijkerbroek past het beste bij mijn figuur?", "Ik weet niet welk model jeans bij me past, kunnen jullie helpen?"],
     "De winkel helpt door je figuur te analyseren en te bepalen welk jeansmodel bij je lichaamsbouw past. Meer lezen kan via de blog of neem contact op via WhatsApp voor persoonlijk advies. De winkel biedt een uitgebreide maatgids aan en is bereikbaar via meerdere kanalen voor persoonlijk maatadvies."),
    ("maatadvies - afspraak om te passen",
     ["Kan ik een afspraak maken om rustig te komen passen?", "Is het mogelijk om een paskamer te reserveren?"],
     "Ja. Klanten kunnen altijd binnenlopen en worden geholpen door specialisten. Om een paskamer te reserveren, ga naar www.derodewinkel.nl/afspraak-maken voor het boeken van een afspraak. Je kunt ook artikelen reserveren door te mailen naar info@derodewinkel.nl, zodat je ze in de winkel kunt passen en daarna betalen."),
    ("producten - milieuvriendelijk",
     ["Zijn jullie spijkerbroeken een beetje milieuvriendelijk?", "Hoe zit het met duurzaamheid bij jullie?"],
     "De Rode Winkel selecteert merken zorgvuldig op duurzaamheid en stelt hogere inkoopeisen; recent toegevoegde merken richten zich op duurzame productie. De winkel werkt uitsluitend met transparante merken die duurzaamheidseisen nakomen, zoals Kuyichi, Nudie Jeans en MUD Jeans, die hun productiefaciliteiten publiceren. Duurzame producten zijn herkenbaar aan het groene blad-icoontje in de webshop en gebruiken duurzame materialen zoals GOTS-katoen. Geen enkele spijkerbroek is volledig duurzaam, maar dit zijn de minst belastende alternatieven. Volgens onderzoek van Impact Institute en ABN AMRO zou een spijkerbroek €33 meer moeten kosten als alle verborgen milieu- en sociale kosten (waterverontreiniging, katoenteelt, kinderarbeid, onderbetaling, onveilige omstandigheden) worden meegeteld. De productie van één kilogram jeansstof kost 10.000 liter water, jaarlijks wordt 92 miljoen ton kleding weggegooid waarvan minder dan 1% wordt gerecycled, en de mode-industrie is verantwoordelijk voor 10% van de wereldwijde CO2-uitstoot."),
    ("fysieke winkel - openingstijd donderdag",
     ["Tot hoe laat kan ik donderdag bij jullie terecht?", "Hebben jullie koopavond?"],
     "Op donderdag is De Rode Winkel geopend van 10:00 tot 21:00, de enige dag met avondopenstelling; vrijdag tot 19:00, zaterdag 09:30 tot 19:00. Feestdagentijden kunnen afwijken; raadpleeg de openingstijdenpagina op de website voor actuele informatie."),
    ("fysieke winkel - zondag open",
     ["Zijn jullie op zondag ook open?", "Wat zijn de openingstijden op zondag?"],
     "Ja, op zondag is De Rode Winkel geopend van 11:00 tot 18:00. Feestdagentijden kunnen afwijken; raadpleeg de openingstijdenpagina voor actuele informatie."),
    ("fysieke winkel - vestiging Amsterdam (negative answer)",
     ["Hebben jullie ook een winkel in Amsterdam?", "Hebben jullie meerdere vestigingen?"],
     "Nee. De Rode Winkel is gevestigd op Lange Elisabethstraat 13, 3511 JA Utrecht en dit is de enige fysieke winkellocatie."),
    ("garantie - broek stuk na 3 maanden",
     ["M'n broek is na drie maanden alweer stuk, wat nu?", "Hoe lang heb ik garantie op een spijkerbroek?"],
     "Op jeans geldt een minimale garantietermijn van 6 maanden. Een broek die na drie maanden stukgaat valt dus nog binnen de garantietermijn. Je kunt het artikel meenemen naar de winkel voor beoordeling of foto's sturen naar info@derodewinkel.nl als winkelbezoek niet mogelijk is. Je ontvangt binnen 14 dagen een inhoudelijke reactie. De wettelijke garantie geldt voor alle aankopen."),
    ("garantie - Nudie jeans elders gekocht repareren",
     ["M'n Nudie jeans komt niet bij jullie vandaan, kunnen jullie 'm toch maken?", "Repareren jullie Nudie Jeans die ik bij een andere winkel heb gekocht?"],
     "Ja. De Rode Winkel is een officiële Nudie Jeans reparatielocatie en herstelt ook Nudie jeans die elders zijn gekocht. De winkel heeft een atelier boven de paskamers waar specialisten bijna dagelijks reparaties en vermakingen uitvoeren. Voor gedetailleerde mogelijkheden, bezoek de reparatiepagina op de website."),
    ("loyaliteitspunten - waarde gespaarde punten",
     ["Hoeveel korting leveren m'n gespaarde punten eigenlijk op?", "Wat is een spaarpunt waard?"],
     "Je spaart 5% van je aankoopbedrag. Voor elke €100 die je besteedt, spaar je €5 korting op je volgende aankoop. Bij het afrekenen staat een sectie met kortingscode, cadeaubon en spaarpunten waar je punten kunt inzetten als korting."),
    ("loyaliteitspunten - punten inzien",
     ["Waar kan ik zien hoeveel punten ik al bij elkaar heb gespaard?", "Hoe check ik m'n puntensaldo?"],
     "Inloggen kan rechtsboven op de webshop. Log in met het e-mailadres dat bij ons bekend is. Direct kom je op de pagina met het aantal gespaarde punten. Bij inlogproblemen kun je contact opnemen via WhatsApp of e-mail."),
    ("bedrijfsgegevens - leeftijd van de zaak",
     ["Hoe oud is jullie zaak eigenlijk?", "Wanneer is De Rode Winkel opgericht?"],
     "De Rode Winkel is opgericht op 19 maart 1837 door Johannes Broekman en Annaatje van Essenberg als kleermakerij en winkel in fournituren. Het bedrijf bestaat dus al sinds 1837 en de continuïteit bestaat tot vandaag. Na het overlijden van Johannes zette Annaatje de zaak voort als Weduwe Johannes Broekman. In 2017 is het familiebedrijf overgegaan naar de zesde generatie. In 2012 ontving De Rode Winkel het predicaat Hofleverancier. Het uitgangspunt van De Rode Winkel is betekenisvol ondernemen, vertaald naar betrouwbaar zijn en lange termijn denken, met duurzame relaties met klanten en leveranciers."),
    ("bedrijfsgegevens - contact",
     ["Op welk nummer kan ik jullie bellen?", "Hoe kan ik jullie bereiken?"],
     "Telefoon: 030 233 63 03. E-mail: info@derodewinkel.nl. WhatsApp via de knop onderaan de pagina op de website. Winkelbezoek: Lange Elisabethstraat 13, 3511 JA Utrecht. Je ontvangt altijd binnen 14 dagen een inhoudelijke reactie."),
    # moved from the near-miss / out-of-scope strata after the assortment files (2026-09-14)
    ("assortiment - kinderkleding",
     ["Verkopen jullie ook kinderkleding?", "Hebben jullie iets voor kinderen?"],
     "Ja, De Rode Winkel heeft een Kids-categorie met kinderkleding in de webshop, vooral kinderjeans en shirts van onder andere G-Star Kids en Denham. Het aanbod is kleiner dan bij dames en heren; bel of mail voor iets specifieks."),
    ("assortiment - schoenen (negative answer)",
     ["Hebben jullie ook schoenen in het assortiment?", "Verkopen jullie sneakers?"],
     "Nee, schoenen verkoopt De Rode Winkel niet. De winkel is gespecialiseerd in kleding en accessoires voor dames en heren: broeken, jeans, overhemden en blouses, t-shirts, truien, jassen en jurken, plus accessoires zoals riemen, tassen, sokken, petten en sjaals."),
    ("assortiment - wasmachines (negative answer)",
     ["Verkopen jullie ook wasmachines?", "Hebben jullie ook witgoed?"],
     "Nee, De Rode Winkel verkoopt geen wasmachines of ander witgoed. De winkel is gespecialiseerd in kleding en accessoires voor dames en heren: broeken, jeans, overhemden en blouses, t-shirts, truien, jassen en jurken, plus accessoires zoals riemen, tassen, sokken, petten en sjaals."),
    ("assortiment - laptops (negative answer)",
     ["Verkopen jullie ook laptops?", "Verkopen jullie elektronica?"],
     "Nee, De Rode Winkel verkoopt geen laptops of andere elektronica. De winkel is gespecialiseerd in kleding en accessoires voor dames en heren: broeken, jeans, overhemden en blouses, t-shirts, truien, jassen en jurken, plus accessoires zoals riemen, tassen, sokken, petten en sjaals."),
    ("assortiment - merken",
     ["Welke merken verkopen jullie?", "Hebben jullie Levi's?"],
     "De Rode Winkel voert voor dames onder andere 7 For All Mankind, American Vintage, Armedangels, Azulea, Co'Couture, Denham The Jeanmaker, Diesel, Elvine, Five Units, G-Star RAW, Guess Jeans, Haute L'Amitie, Kappy, Kuyichi Jeans, Levi's, Lois Jeans, Modstrom, Neuw Denim, Nudie Jeans, Rains, Suncoo, Topologie en Woodbird. Voor heren onder andere AECA, American Vintage, Benzak Denim Developers, Bonne Suits, Carhartt WIP, Denham The Jeanmaker, Dickies, Diesel, Edwin, Evisu, Foret Studio, G-Star RAW, Japan Blue Jeans, Kappy, Kuyichi Jeans, Lee Jeans, Les Deux, Levi's, Levi's Vintage Clothing, Momotaro Jeans, Neuw Denim, Nudie Jeans, Pockies, Rains, The GoodPeople, Topologie, Woodbird en Wrangler Jeans. Levi's is dus beschikbaar voor dames en heren."),
    ("assortiment - jassen",
     ["Verkopen jullie jassen?", "Hebben jullie winterjassen?"],
     "Ja, jassen zijn een eigen categorie voor zowel dames als heren. Bij dames zijn er daarnaast blazers, jasjes en spijkerjassen. Bij heren zijn er colberts en overshirts, spijkerjassen en workers, bodywarmers, trainingsjacks en varsity- en fleecejacks."),
    ("assortiment - riemen",
     ["Hebben jullie riemen?", "Verkopen jullie ook leren riemen?"],
     "Ja, De Rode Winkel heeft riemen voor dames en heren, waaronder leren riemen van Nudie Jeans, riemen van Lois Jeans en G-Star, en modellen van Legend en Presly & Sun, in onder andere zwart, cognac, naturel en dierprint. Ook elastische riemen zitten in de collectie. In de winkel helpen ze je aan de juiste maat."),
]

# --------------------------------------------------------------------------- #
# N: near-miss, unanswerable. (slug, question, absent keywords for grep check)
# `absent` are case-insensitive regexes that must not occur anywhere in docs/.
# --------------------------------------------------------------------------- #
NEAR_MISS = [
    ("maatadvies - valt groot of klein", "Valt jullie kleding groot of klein?", [r"groot of klein", r"valt (groot|klein|ruim)", r"klein uit"]),
    ("maatadvies - grote maten", "Hebben jullie ook grote maten?", [r"grote maten", r"plus[- ]size", r"plussize"]),
    ("maatadvies - lengtemaat 38", "Hebben jullie jeans in lengtemaat 38?", [r"lengtemaat 38", r"lengte 38", r"\b38\b"]),
    ("fysieke winkel - parkeren", "Kan ik bij de winkel parkeren?", [r"parkeer", r"parkeren", r"parkeergarage"]),
    ("fysieke winkel - rolstoeltoegankelijk", "Is de winkel toegankelijk met een rolstoel?", [r"rolstoeltoegankelijk", r"toegankelijk", r"drempel"]),
    ("fysieke winkel - toilet", "Is er een toilet in de winkel?", [r"toilet", r"wc\b"]),
    ("fysieke winkel - hond", "Mag mijn hond mee de winkel in?", [r"\bhond", r"huisdier"]),
    ("fysieke winkel - Koningsdag", "Zijn jullie open op Koningsdag?", [r"koningsdag"]),
    ("verzending - bezorgen bij pakketpunt", "Kan ik m'n pakketje laten bezorgen bij een PostNL-punt in plaats van thuis?", [r"postnl-punt", r"pakketpunt", r"afhaalpunt", r"servicepunt"]),
    ("verzending - zondagbezorging", "Bezorgen jullie ook op zondag?", [r"zondag.{0,40}bezorg", r"bezorg.{0,40}zondag", r"zondagbezorging"]),
    ("verzending - tijdslot", "Kan ik een bezorgtijdstip kiezen?", [r"tijdslot", r"tijdvak", r"bezorgtijd", r"avondbezorging"]),
    ("verzending - bij de buren", "Mag het pakket bij de buren worden afgegeven?", [r"\bburen\b", r"buurman", r"buurvrouw"]),
    ("bestellen - bestelling wijzigen na betaling", "Kan ik m'n bestelling nog aanpassen nadat ik al betaald heb?", [r"bestelling (wijzig|aanpass)", r"wijzigen na", r"na betaling"]),
    ("bestellen - annuleren", "Kan ik mijn bestelling annuleren?", [r"annuleer", r"annuler"]),
    ("bestellen - cadeauverpakking", "Kunnen jullie m'n bestelling als cadeau inpakken?", [r"inpak", r"cadeauverpakking", r"verpakking"]),
    ("bestellen - via WhatsApp bestellen", "Kan ik via WhatsApp een bestelling plaatsen?", [r"via whatsapp (bestellen|een bestelling)", r"whatsapp.{0,30}bestell"]),
    ("bestellen - factuur op bedrijfsnaam", "Kan ik een factuur op naam van mijn bedrijf krijgen?", [r"factuur", r"btw-factuur", r"zakelijk"]),
    ("bestellen - gereserveerd artikel apart", "Hoe lang blijft een gereserveerd artikel voor mij apart liggen?", [r"apart (liggen|houden|gehouden)", r"reserveringstermijn", r"dagen apart"]),
    ("betalen - minimumbedrag Billink", "Is er een minimumbedrag om met Billink te kunnen betalen?", [r"minimum", r"minimaal bedrag", r"vanaf .{0,10}billink"]),
    ("betalen - in termijnen", "Kan ik in termijnen betalen?", [r"in termijnen", r"gespreid betalen", r"afbetal", r"deelbetaling"]),
    ("betalen - Bancontact", "Accepteren jullie Bancontact?", [r"bancontact", r"mister ?cash"]),
    ("betalen - pinnen in de winkel", "Kan ik in de winkel pinnen?", [r"\bpin(nen|pas|automaat)?\b", r"betaalpas", r"contactloos"]),
    ("betalen - contant", "Kan ik contant betalen in de winkel?", [r"contant(?! geld)", r"cash", r"muntgeld"]),
    ("cadeaukaart - bedragen", "Welke bedragen zijn er voor de cadeaukaart?", [r"cadeaukaart van ?€? ?\d", r"\b(10|25|50|100) euro\b", r"bedrag naar keuze", r"cadeaukaart.{0,30}(bedrag|waarde)"]),
    ("cadeaukaart - geldigheid", "Hoe lang is een cadeaukaart geldig?", [r"geldig", r"vervalt", r"verloopt"]),
    ("kortingscode - geldigheidsduur", "Hoe lang blijft een kortingscode geldig?", [r"geldig", r"vervalt", r"verloopt"]),
    ("kortingscode - combineren", "Kan ik twee kortingscodes tegelijk gebruiken?", [r"kortingscodes? .{0,20}(combineren|stapelen|tegelijk)", r"meerdere (kortings)?codes", r"combineer.{0,20}code", r"stapel"]),
    ("kortingscode - seniorenkorting", "Krijg ik korting als ik 65-plusser ben?", [r"\b65\b", r"senior", r"ouderen", r"aow"]),
    ("kortingscode - verjaardag", "Krijg ik als member korting op mijn verjaardag?", [r"verjaardag", r"jarig bent", r"jarige\b", r"birthday"]),
    ("loyaliteitspunten - vervallen spaarpunten", "Verlopen m'n spaarpunten na een tijdje?", [r"punten (verval|verlop)", r"vervallen", r"geldigheid van .{0,20}punten"]),
    ("loyaliteitspunten - overdragen", "Kan ik mijn spaarpunten aan iemand anders geven?", [r"overdra", r"overzetten", r"delen met"]),
    ("loyaliteitspunten - account verwijderen", "Hoe verwijder ik mijn account?", [r"verwijder", r"opzeggen", r"opheffen"]),
    ("garantie - duur inkorten", "Hoe lang duurt het inkorten van een broek?", [r"inkort", r"klaar (binnen|in)", r"terwijl u wacht"]),
    ("garantie - prijs vermaken", "Wat kost het inkorten van een jeans?", [r"inkort", r"\b€ ?\d+ .{0,20}vermak", r"kosten van (het )?vermak"]),
    ("garantie - jeans verven", "Kunnen jullie een verkleurde jeans opnieuw verven?", [r"verven", r"verf\b", r"kleuren van"]),
    ("producten - tweedehands", "Verkopen jullie ook tweedehands kleding?", [r"tweedehands", r"second ?hand", r"vintage kleding", r"pre-?owned", r"gedragen kleding"]),
    ("producten - wasmiddel", "Verkopen jullie wasmiddel voor jeans?", [r"wasmiddel", r"onderhoudsproduct", r"denim wash"]),
    ("bedrijfsgegevens - KvK", "Wat is jullie KvK-nummer?", [r"kvk", r"kamer van koophandel"]),
    ("bedrijfsgegevens - BTW-nummer", "Wat is jullie btw-nummer?", [r"btw", r"vat\b"]),
    ("bestellen - webshop-app", "Hebben jullie ook een app?", [r"\bapp\b", r"apple app store", r"google play"]),
]

# --------------------------------------------------------------------------- #
# O: out of scope.
# --------------------------------------------------------------------------- #
OUT_OF_SCOPE = [
    ("weer", "Wat voor weer wordt het morgen in Utrecht?"),
    ("recept", "Heb je een lekker recept voor pannenkoeken?"),
    ("hoofdstad", "Wat is de hoofdstad van Frankrijk?"),
    ("trein", "Hoe laat gaat de laatste trein van Utrecht naar Amsterdam?"),
    ("belastingaangifte", "Kun je me helpen met m'n belastingaangifte?"),
    ("concurrent prijs", "Wat kost een spijkerbroek bij de Zara?"),
    ("concurrent assortiment", "Verkoopt de Bijenkorf ook Nudie Jeans?"),
    ("gedicht", "Kun je een gedicht schrijven over de herfst?"),
    ("rekensom", "Wat is 17 keer 23?"),
    ("tijd", "Hoe laat is het nu?"),
    ("voetbal", "Wat vond je van de wedstrijd van Ajax gisteren?"),
    ("mop", "Kun je me een mop vertellen?"),
    ("pizzeria", "Wat is de beste pizzeria in Utrecht?"),
    ("fiets", "Hoe repareer ik een lekke band?"),
    ("cv", "Kun je me helpen mijn cv te schrijven?"),
    ("treinkaartje", "Wat kost een treinkaartje naar Parijs?"),
]


def assertion_block(answerable: bool) -> list:
    block = [{"bot_did_not_utter": {"utter_name": INFRA}}]
    if answerable:
        block.append({"bot_did_not_utter": {"utter_name": ABSTAIN}})
    else:
        block.append({"bot_uttered": {"utter_name": ABSTAIN}})
    block.append({"bot_uttered": {"text_matches": CAPTURE_REGEX}})
    return block


def verify_absent() -> None:
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in sorted(DOCS.rglob("*.txt")))
    problems = []
    for slug, _q, patterns in NEAR_MISS:
        for pat in patterns:
            m = re.search(pat, corpus, flags=re.I)
            if m:
                start = max(0, m.start() - 40)
                problems.append(f"  N | {slug}: /{pat}/ found: ...{corpus[start:m.end() + 40]!r}")
    if problems:
        sys.exit("near-miss keywords present in docs/, fix the case or the keywords:\n" + "\n".join(problems))


def main() -> None:
    verify_absent()
    cases, ground_truth = [], {}
    for slug, questions, gt in ANSWERABLE:
        for i, q in enumerate(questions, start=1):
            name = f"A | {slug} | v{i}"
            cases.append({"test_case": name, "steps": [{"user": q, "assertions": assertion_block(True)}]})
            ground_truth[name] = gt
    for slug, q, _ in NEAR_MISS:
        cases.append({"test_case": f"N | {slug}", "steps": [{"user": q, "assertions": assertion_block(False)}]})
    for slug, q in OUT_OF_SCOPE:
        cases.append({"test_case": f"O | {slug}", "steps": [{"user": q, "assertions": assertion_block(False)}]})

    header = (
        "# GENERATED by experiments/contrastive/build_suite.py - edit that file, not this one.\n"
        "# Strata: A answerable (ground truths in experiments/contrastive/ground_truth.yml),\n"
        "# N near-miss unanswerable (facts grep-verified absent from docs/), O out of scope.\n"
        "# The final bot_uttered assertion never matches: it forces Rasa to record the\n"
        "# transcript for every case so the answers can be judged offline.\n"
    )
    SUITE_PATH.write_text(
        header + yaml.safe_dump({"test_cases": cases}, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    GT_PATH.write_text(yaml.safe_dump(ground_truth, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    nA = sum(len(q) for _, q, _ in ANSWERABLE)
    print(f"wrote {SUITE_PATH.relative_to(ROOT)}: {len(cases)} cases "
          f"(A={nA}, N={len(NEAR_MISS)}, O={len(OUT_OF_SCOPE)}); ground truths: {len(ground_truth)}")


if __name__ == "__main__":
    main()

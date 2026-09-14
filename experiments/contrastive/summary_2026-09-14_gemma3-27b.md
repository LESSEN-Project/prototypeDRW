# Contrastive ablation summary

Runs per condition: k0=4, bottom_k2=4

## Decision quality per condition (pooled over repeats)

| condition | A grounded | A ungrounded | A false-abstain | N false-answer | O false-answer | infra | A judge mean |
|---|---|---|---|---|---|---|---|
| k0 |  80.6% |  17.6% |   1.9% |  21.2% |  25.0% | 0 | 0.939 |
| bottom_k2 |  77.8% |  22.2% |   0.0% |  23.1% |  25.0% | 0 | 0.912 |

Reading guide: the feature targets *N false-answer* (should go down) without raising *A false-abstain*. Differences smaller than the per-case flapping below are noise.

## Per-case outcomes across repeats

Codes: G grounded, U ungrounded answer, A abstained, X answered (on N/O), ! infra error. One character per repeat, in repeat order.

| case | k0 | bottom_k2 |
|---|---|---|
| A | bedrijfsgegevens - leeftijd van de zaak | GGGG | GGGG |
| A | bedrijfsgegevens - telefoonnummer | UUUU | UUUU |
| A | bestellen - account verplicht | GGGG | GGGG |
| A | betalen - Klarna (negative answer) | GGGG | GGGG |
| A | betalen - PayPal toeslag | GGGG | UGGG |
| A | betalen - achteraf betalen | GGGG | GGGG |
| A | cadeaukaart - VVV-bon online (negative answer) | GGGG | UUGG |
| A | cadeaukaart - cadeaubon online gebruiken | GGGG | GGGG |
| A | fysieke winkel - openingstijd donderdag | GGGG | GGGG |
| A | fysieke winkel - vestiging Amsterdam (negative answer) | AGGA | GGGG |
| A | fysieke winkel - zondag open | GGUU | UUUU |
| A | garantie - Nudie jeans elders gekocht repareren | GGGG | UUGU |
| A | garantie - broek stuk na 3 maanden | GGGG | GGGG |
| A | kortingscode - studentenkorting | UGUU | GGGG |
| A | loyaliteitspunten - punten inzien | GGGG | GGGG |
| A | loyaliteitspunten - waarde gespaarde punten | GGGG | GGGG |
| A | maatadvies - afspraak om te passen | UUUU | GGGG |
| A | maatadvies - welke jeans past bij figuur | GGGG | GGGG |
| A | producten - maat uitverkocht | GGGG | GGGG |
| A | producten - milieuvriendelijk | GGGG | GGGG |
| A | retouren - online aankoop in winkel terugbrengen | GGGG | UGGG |
| A | retouren - terugsturen kosten | GGGG | GGGG |
| A | retouren - wanneer geld terug | GGGG | GGGG |
| A | verzending - bezorging Belgie | UUUU | UUUU |
| A | verzending - gratis verzending drempel | UGGG | GGGU |
| A | verzending - levertijd | GGGU | UUUU |
| A | verzending - niet thuis bij bezorging | GGGG | GGGG |
| N | bestellen - bestelling wijzigen na betaling | AAAA | AAAA |
| N | bestellen - cadeauverpakking | AAAA | AAAA |
| N | betalen - minimumbedrag Billink | AAAA | AAAA |
| N | fysieke winkel - parkeren | AAAA | AAAA |
| N | fysieke winkel - rolstoeltoegankelijk | AAAA | AAAA |
| N | kortingscode - geldigheidsduur | AAAA | AAAA |
| N | kortingscode - seniorenkorting | AAAA | AAAA |
| N | loyaliteitspunten - vervallen spaarpunten | AAAA | AAAA |
| N | maatadvies - valt groot of klein | AAAA | AAAA |
| N | producten - kinderkleding | XXXX | XXXX |
| N | producten - schoenen | AAAA | AAAA |
| N | verzending - bezorgen bij pakketpunt | AXXX | XXXX |
| N | verzending - zondagbezorging | XXXX | XXXX |
| O | belastingaangifte | AAAA | AAAA |
| O | concurrent prijs | AAAA | AAAA |
| O | hoofdstad | AAAA | AAAA |
| O | laptops | XXXX | XXXX |
| O | recept | AAAA | AAAA |
| O | trein | AAAA | AAAA |
| O | wasmachines | XXXX | XXXX |
| O | weer | AAAA | AAAA |

## Cases that never pass in any condition

- A | bedrijfsgegevens - telefoonnummer
- A | verzending - bezorging Belgie
- N | producten - kinderkleding
- N | verzending - zondagbezorging
- O | laptops
- O | wasmachines

# Contrastive ablation summary

Runs per condition: k0=4, bottom_k2=4, bottom_k4=4, random_k2=4, random_k4=4, next_k2=4, next_k4=4

## Decision quality per condition (pooled over repeats)

| condition | A grounded | A ungrounded | A false-abstain | N false-answer | O false-answer | infra | A judge mean |
|---|---|---|---|---|---|---|---|
| k0 |  63.0% |  33.3% |   3.7% |  32.7% |  18.8% | 0 | 0.891 |
| bottom_k2 |  75.0% |  23.1% |   1.9% |  21.2% |  12.5% | 0 | 0.918 |
| bottom_k4 |  67.6% |  30.6% |   1.9% |  38.5% |  12.5% | 0 | 0.901 |
| random_k2 |  63.0% |  33.3% |   3.7% |  25.0% |  12.5% | 0 | 0.889 |
| random_k4 |  71.3% |  28.7% |   0.0% |  46.2% |  15.6% | 0 | 0.903 |
| next_k2 |  68.5% |  27.8% |   3.7% |  30.8% |   9.4% | 0 | 0.891 |
| next_k4 |  70.4% |  25.9% |   3.7% |  48.1% |  25.0% | 0 | 0.911 |

Reading guide: the feature targets *N false-answer* (should go down) without raising *A false-abstain*. Differences smaller than the per-case flapping below are noise.

## Per-case outcomes across repeats

Codes: G grounded, U ungrounded answer, A abstained, X answered (on N/O), ! infra error. One character per repeat, in repeat order.

| case | k0 | bottom_k2 | bottom_k4 | random_k2 | random_k4 | next_k2 | next_k4 |
|---|---|---|---|---|---|---|---|
| A | bedrijfsgegevens - leeftijd van de zaak | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | bedrijfsgegevens - telefoonnummer | GGGG | GGGG | GUGG | GGGU | GGGG | GGGG | GGGG |
| A | bestellen - account verplicht | GGGG | GGGG | GGGG | UUUU | GGGG | GGGG | GGGG |
| A | betalen - Klarna (negative answer) | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | betalen - PayPal toeslag | UUUU | UUUG | GGUU | UUUU | UUUU | UUUU | UGGU |
| A | betalen - achteraf betalen | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | cadeaukaart - VVV-bon online (negative answer) | UUUU | UUUU | UUUU | UUUU | GUGG | UGGG | UUUU |
| A | cadeaukaart - cadeaubon online gebruiken | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | fysieke winkel - openingstijd donderdag | GGGG | GUGG | UUUU | UUGG | UUUU | GGGG | UUUU |
| A | fysieke winkel - vestiging Amsterdam (negative answer) | AAAA | AGAG | AUGA | AAAA | UUGG | AAAA | AAAA |
| A | fysieke winkel - zondag open | UUUU | GGGG | GGGU | UUUU | GGGU | UUUU | GGUG |
| A | garantie - Nudie jeans elders gekocht repareren | UGUU | GGUG | UUUU | UUUU | UUUU | GGGU | GGUG |
| A | garantie - broek stuk na 3 maanden | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | kortingscode - studentenkorting | UUGU | GUGG | UUUG | GGGG | GGGU | GGGG | UUGU |
| A | loyaliteitspunten - punten inzien | UUUU | UUUU | GUUU | UUUU | UUGU | UUUU | UUUU |
| A | loyaliteitspunten - waarde gespaarde punten | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | maatadvies - afspraak om te passen | GGGG | UGGG | GGUU | UUUU | UUUU | GUUU | GGGU |
| A | maatadvies - welke jeans past bij figuur | UGGG | GGGG | GGGU | UGGG | GGGG | UUUU | GGGG |
| A | producten - maat uitverkocht | UUUU | GGGG | UGUU | UGUG | GGGG | UUGG | UUUG |
| A | producten - milieuvriendelijk | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - online aankoop in winkel terugbrengen | GGGG | GGUG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - terugsturen kosten | GGGG | UGGU | UUGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - wanneer geld terug | GGGU | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - bezorging Belgie | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - gratis verzending drempel | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - levertijd | UUUU | UUUU | GGGG | GUGG | UGUU | UUUU | UGGG |
| A | verzending - niet thuis bij bezorging | UUUU | UUUG | GGUU | UGGG | UUUU | UGUU | UUUU |
| N | bestellen - bestelling wijzigen na betaling | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | bestellen - cadeauverpakking | AAAA | AAAA | AAAA | AAAA | AAAX | AAAA | XXXX |
| N | betalen - minimumbedrag Billink | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| N | fysieke winkel - parkeren | AAXA | AAAA | AAAA | AAAA | XXXX | AAXA | AXAA |
| N | fysieke winkel - rolstoeltoegankelijk | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | kortingscode - geldigheidsduur | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | kortingscode - seniorenkorting | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | loyaliteitspunten - vervallen spaarpunten | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | maatadvies - valt groot of klein | AAAA | AAAA | XXXX | AAAA | XXXX | XXAA | XXXX |
| N | producten - kinderkleding | XXXX | XXAA | XXXX | XXXX | XXXX | XXXX | XXXX |
| N | producten - schoenen | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | verzending - bezorgen bij pakketpunt | XXXX | AAAX | XXXX | AAAX | AXXX | XAAA | XXXX |
| N | verzending - zondagbezorging | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| O | belastingaangifte | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | concurrent prijs | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | hoofdstad | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | laptops | XXXX | XXXX | XXXX | XXXX | XXXX | AXXX | XXXX |
| O | recept | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | trein | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | wasmachines | AXXA | AAAA | AAAA | AAAA | AAAX | AAAA | XXXX |
| O | weer | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |

## Cases that never pass in any condition

- N | betalen - minimumbedrag Billink
- N | verzending - zondagbezorging

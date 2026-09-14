# Contrastive ablation summary

Runs per condition: k0=4, bottom_k2=4, bottom_k4=4, random_k2=4, random_k4=4, next_k2=4, next_k4=4

## Decision quality per condition (pooled over repeats)

| condition | A grounded | A ungrounded | A false-abstain | N false-answer | O false-answer | infra | A judge mean |
|---|---|---|---|---|---|---|---|
| k0 |  67.6% |  28.7% |   3.7% |  36.5% |  12.5% | 0 | 0.907 |
| bottom_k2 |  73.1% |  24.1% |   2.8% |  36.5% |  25.0% | 0 | 0.906 |
| bottom_k4 |  75.0% |  23.1% |   1.9% |  38.5% |  25.0% | 0 | 0.917 |
| random_k2 |  69.4% |  29.6% |   0.9% |  30.8% |  25.0% | 0 | 0.908 |
| random_k4 |  76.9% |  23.1% |   0.0% |  40.4% |  25.0% | 0 | 0.925 |
| next_k2 |  67.6% |  30.6% |   1.9% |  36.5% |  21.9% | 0 | 0.887 |
| next_k4 |  63.0% |  37.0% |   0.0% |  48.1% |  25.0% | 0 | 0.878 |

Reading guide: the feature targets *N false-answer* (should go down) without raising *A false-abstain*. Differences smaller than the per-case flapping below are noise.

## Per-case outcomes across repeats

Codes: G grounded, U ungrounded answer, A abstained, X answered (on N/O), ! infra error. One character per repeat, in repeat order.

| case | k0 | bottom_k2 | bottom_k4 | random_k2 | random_k4 | next_k2 | next_k4 |
|---|---|---|---|---|---|---|---|
| A | bedrijfsgegevens - leeftijd van de zaak | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | bedrijfsgegevens - telefoonnummer | GGGG | GGGG | GGGG | GGGG | UGUU | GGGG | GGGG |
| A | bestellen - account verplicht | GGGG | GUUG | GGGG | GGGU | GGGG | GGGG | GGGG |
| A | betalen - Klarna (negative answer) | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | betalen - PayPal toeslag | UUUU | UUUU | GGGG | UUUU | UUUG | UUUU | UGGU |
| A | betalen - achteraf betalen | GGGG | GGGG | GGGG | GUGU | GGGG | GGGG | GGGG |
| A | cadeaukaart - VVV-bon online (negative answer) | UUGU | GGGG | UUUU | UUUU | UUGU | GUUU | UUUU |
| A | cadeaukaart - cadeaubon online gebruiken | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | fysieke winkel - openingstijd donderdag | GGGG | GGGG | GGGU | UUUU | GGGG | GGGG | UUUU |
| A | fysieke winkel - vestiging Amsterdam (negative answer) | AAAA | AUAA | UAUA | UUUA | GUUU | UUAA | GGUU |
| A | fysieke winkel - zondag open | GUUU | GGGG | UUGU | GGGG | GGUU | UUUU | UUUG |
| A | garantie - Nudie jeans elders gekocht repareren | GGGU | GGGG | GGGG | GGGU | GUUU | UGUG | UGUU |
| A | garantie - broek stuk na 3 maanden | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | kortingscode - studentenkorting | GUGG | GGGU | UUGG | GGGG | GGGG | GUGG | UUGU |
| A | loyaliteitspunten - punten inzien | UUUU | UUUU | UUUU | UGUU | UUGG | UUUU | UUUU |
| A | loyaliteitspunten - waarde gespaarde punten | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | maatadvies - afspraak om te passen | GGGG | UUUU | GGGU | UUUU | GUUU | UUGU | UGUU |
| A | maatadvies - welke jeans past bij figuur | GGGG | GGGG | GGGU | UGGG | GGGG | GUGG | UUGU |
| A | producten - maat uitverkocht | UUUU | GGGU | UGUU | GGGG | GGGG | UUUG | GUGU |
| A | producten - milieuvriendelijk | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - online aankoop in winkel terugbrengen | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - terugsturen kosten | GGGU | UGGU | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | retouren - wanneer geld terug | UGGU | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - bezorging Belgie | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - gratis verzending drempel | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG | GGGG |
| A | verzending - levertijd | UUUU | UUUU | UGGG | GUGU | GUGG | UUUU | UGUU |
| A | verzending - niet thuis bij bezorging | UUUU | UUUG | GUUU | UUGU | UGGU | GUGU | UUUU |
| N | bestellen - bestelling wijzigen na betaling | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | bestellen - cadeauverpakking | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AXXX |
| N | betalen - minimumbedrag Billink | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| N | fysieke winkel - parkeren | AAAA | AAAA | AAAA | AAAA | XXAA | AAAA | XXAA |
| N | fysieke winkel - rolstoeltoegankelijk | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | kortingscode - geldigheidsduur | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | kortingscode - seniorenkorting | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | loyaliteitspunten - vervallen spaarpunten | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | maatadvies - valt groot of klein | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| N | producten - kinderkleding | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| N | producten - schoenen | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| N | verzending - bezorgen bij pakketpunt | XXXX | XAXX | XXXX | AAAA | XXAX | XXXA | XXXX |
| N | verzending - zondagbezorging | AXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| O | belastingaangifte | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | concurrent prijs | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | hoofdstad | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | laptops | AAAA | XXXX | XXXX | XXXX | XXXX | XAXX | XXXX |
| O | recept | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | trein | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |
| O | wasmachines | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX | XXXX |
| O | weer | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA | AAAA |

## Cases that never pass in any condition

- N | betalen - minimumbedrag Billink
- N | producten - kinderkleding
- N | producten - schoenen
- O | wasmachines

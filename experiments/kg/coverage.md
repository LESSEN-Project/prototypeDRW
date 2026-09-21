# KG coverage of the 124-case suite

Graph: 39 converted documents; text-bot column = gemma3:12b at k0, per-case majority over 5 repeats.

## Stratum A (68 cases)

entailed 56, contradicted 12, unknown 0, unmapped 0; via inference 6; verdict differs from the hand expectation on 0.
Text bot (gemma3:12b, k0): answered 62, hedged 0, abstained 6.

| case | template | verdict | inferred | note / value | text bot k0 |
|---|---|---|---|---|---|
| A | retouren - terugsturen kosten | v1 | fact | entailed |  | 7, 7 | answered |
| A | retouren - terugsturen kosten | v2 | fact | entailed |  | 7, 7 | answered |
| A | retouren - online aankoop in winkel terugbrengen | v1 | offers | entailed |  | terugbrengen naar Lange Elisabethstraat  | answered |
| A | retouren - online aankoop in winkel terugbrengen | v2 | offers | entailed |  | terugbrengen naar Lange Elisabethstraat  | answered |
| A | retouren - wanneer geld terug | v1 | fact | entailed |  | 3, 3 | answered |
| A | retouren - wanneer geld terug | v2 | fact | entailed |  | 3, 3 | answered |
| A | verzending - verzendkosten en drempel | v1 | fact | entailed |  | 49 | answered |
| A | verzending - verzendkosten en drempel | v2 | fact | entailed |  | 49 | answered |
| A | verzending - bezorging Belgie | v1 | ships_to | entailed | yes | Antwerp, 10 | answered |
| A | verzending - bezorging Belgie | v2 | ships_to | entailed | yes | Antwerp, 10 | answered |
| A | verzending - levertijd | v1 | fact | entailed |  | 48 | answered |
| A | verzending - levertijd | v2 | fact | entailed |  | 48 | answered |
| A | verzending - niet thuis bij bezorging | v1 | fact | entailed |  | true | answered |
| A | verzending - niet thuis bij bezorging | v2 | fact | entailed |  | true | answered |
| A | bestellen - account verplicht | v1 | fact | entailed |  | false | answered |
| A | bestellen - account verplicht | v2 | fact | entailed |  | false | answered |
| A | producten - maat uitverkocht | v1 | offers | entailed |  | via het productformulier een specifieke  | answered |
| A | producten - maat uitverkocht | v2 | offers | entailed |  | via het productformulier een specifieke  | answered |
| A | betalen - achteraf betalen | v1 | accepts | entailed |  | Webshop | answered |
| A | betalen - achteraf betalen | v2 | accepts | entailed |  | Webshop | answered |
| A | betalen - PayPal toeslag | v1 | fact | entailed |  | 3.20 | answered |
| A | betalen - PayPal toeslag | v2 | fact | entailed |  | 3.20 | answered |
| A | betalen - Klarna (negative answer) | v1 | accepts | contradicted |  | explicit doesNotAccept | answered |
| A | betalen - Klarna (negative answer) | v2 | accepts | contradicted |  | explicit doesNotAccept | answered |
| A | kortingscode - studentenkorting | v1 | offers | entailed |  | in de winkel: studentenpas tonen; online, 10 | answered |
| A | kortingscode - studentenkorting | v2 | offers | entailed |  | in de winkel: studentenpas tonen; online, 10 | answered |
| A | cadeaukaart - cadeaubon online gebruiken | v1 | accepts | entailed |  | Webshop | answered |
| A | cadeaukaart - cadeaubon online gebruiken | v2 | accepts | entailed |  | Webshop | answered |
| A | cadeaukaart - VVV-bon online (negative answer) | v1 | accepts | contradicted |  | explicit doesNotAccept | answered |
| A | cadeaukaart - VVV-bon online (negative answer) | v2 | accepts | contradicted |  | explicit doesNotAccept | answered |
| A | maatadvies - welke jeans past bij figuur | v1 | offers | entailed |  | de winkel analyseert je figuur en bepaal | answered |
| A | maatadvies - welke jeans past bij figuur | v2 | offers | entailed |  | de winkel analyseert je figuur en bepaal | answered |
| A | maatadvies - afspraak om te passen | v1 | offers | entailed |  | afspraak boeken via www.derodewinkel.nl/ | answered |
| A | maatadvies - afspraak om te passen | v2 | offers | entailed |  | afspraak boeken via www.derodewinkel.nl/ | answered |
| A | producten - milieuvriendelijk | v1 | fact | entailed |  | werkt uitsluitend met transparante merke | answered |
| A | producten - milieuvriendelijk | v2 | fact | entailed |  | werkt uitsluitend met transparante merke | answered |
| A | fysieke winkel - openingstijd donderdag | v1 | open_on | entailed |  | 10:00-21:00 | answered |
| A | fysieke winkel - openingstijd donderdag | v2 | open_on | entailed |  | 10:00-21:00 | abstained |
| A | fysieke winkel - zondag open | v1 | open_on | entailed |  | 11:00-18:00 | answered |
| A | fysieke winkel - zondag open | v2 | open_on | entailed |  | 11:00-18:00 | answered |
| A | fysieke winkel - vestiging Amsterdam (negative answer) | v1 | store_in | contradicted |  | store list is complete | abstained |
| A | fysieke winkel - vestiging Amsterdam (negative answer) | v2 | store_in | contradicted |  | store list is complete | answered |
| A | garantie - broek stuk na 3 maanden | v1 | fact | entailed |  | 6 | answered |
| A | garantie - broek stuk na 3 maanden | v2 | fact | entailed |  | 6 | answered |
| A | garantie - Nudie jeans elders gekocht repareren | v1 | repairs | entailed | yes | RepairService, NudieJeansJeans | answered |
| A | garantie - Nudie jeans elders gekocht repareren | v2 | repairs | entailed | yes | RepairService, NudieJeansJeans | answered |
| A | loyaliteitspunten - waarde gespaarde punten | v1 | fact | entailed |  | 5 | answered |
| A | loyaliteitspunten - waarde gespaarde punten | v2 | fact | entailed |  | 5 | answered |
| A | loyaliteitspunten - punten inzien | v1 | offers | entailed |  | log rechtsboven in de webshop in met het | answered |
| A | loyaliteitspunten - punten inzien | v2 | offers | entailed |  | log rechtsboven in de webshop in met het | answered |
| A | bedrijfsgegevens - leeftijd van de zaak | v1 | fact | entailed |  | 1837-03-19 | answered |
| A | bedrijfsgegevens - leeftijd van de zaak | v2 | fact | entailed |  | 1837-03-19 | answered |
| A | bedrijfsgegevens - contact | v1 | fact | entailed |  | 030 233 63 03, 030 233 63 03 | answered |
| A | bedrijfsgegevens - contact | v2 | fact | entailed |  | 030 233 63 03, 030 233 63 03 | answered |
| A | assortiment - kinderkleding | v1 | sells | entailed |  | KidsClothing | answered |
| A | assortiment - kinderkleding | v2 | sells | entailed |  | KidsClothing | answered |
| A | assortiment - schoenen (negative answer) | v1 | sells | contradicted | yes | explicit doesNotSell | answered |
| A | assortiment - schoenen (negative answer) | v2 | sells | contradicted | yes | explicit doesNotSell | abstained |
| A | assortiment - wasmachines (negative answer) | v1 | sells | contradicted |  | top-level category WhiteGoods is not sold and the top-level list is complete | answered |
| A | assortiment - wasmachines (negative answer) | v2 | sells | contradicted |  | top-level category WhiteGoods is not sold and the top-level list is complete | abstained |
| A | assortiment - laptops (negative answer) | v1 | sells | contradicted |  | top-level category Electronics is not sold and the top-level list is complete | abstained |
| A | assortiment - laptops (negative answer) | v2 | sells | contradicted |  | top-level category Electronics is not sold and the top-level list is complete | abstained |
| A | assortiment - merken | v1 | list_brands | entailed |  | AmericanVintage, Denham | answered |
| A | assortiment - merken | v2 | list_brands | entailed |  | AmericanVintage, Denham | answered |
| A | assortiment - jassen | v1 | sells | entailed |  | Outerwear | answered |
| A | assortiment - jassen | v2 | sells | entailed |  | Outerwear | answered |
| A | assortiment - riemen | v1 | sells | entailed |  | Belts | answered |
| A | assortiment - riemen | v2 | sells | entailed |  | Belts | answered |

## Stratum N (40 cases)

entailed 0, contradicted 1, unknown 39, unmapped 0; via inference 0; verdict differs from the hand expectation on 0.
Text bot (gemma3:12b, k0): answered 7, hedged 2, abstained 31.

| case | template | verdict | inferred | note / value | text bot k0 |
|---|---|---|---|---|---|
| N | maatadvies - valt groot of klein | fact | unknown |  |  | abstained |
| N | maatadvies - grote maten | fact | unknown |  |  | answered |
| N | maatadvies - lengtemaat 38 | fact | unknown |  |  | answered |
| N | fysieke winkel - parkeren | fact | unknown |  |  | abstained |
| N | fysieke winkel - rolstoeltoegankelijk | fact | unknown |  |  | abstained |
| N | fysieke winkel - toilet | fact | unknown |  |  | answered |
| N | fysieke winkel - hond | fact | unknown |  |  | abstained |
| N | fysieke winkel - Koningsdag | open_on | unknown |  | holiday hours may differ | answered |
| N | verzending - bezorgen bij pakketpunt | fact | unknown |  |  | answered |
| N | verzending - zondagbezorging | fact | unknown |  |  | hedged |
| N | verzending - tijdslot | fact | unknown |  |  | abstained |
| N | verzending - bij de buren | fact | unknown |  |  | abstained |
| N | bestellen - bestelling wijzigen na betaling | offers | unknown |  |  | abstained |
| N | bestellen - annuleren | offers | unknown |  |  | abstained |
| N | bestellen - cadeauverpakking | offers | unknown |  |  | abstained |
| N | bestellen - via WhatsApp bestellen | fact | unknown |  |  | abstained |
| N | bestellen - factuur op bedrijfsnaam | offers | unknown |  |  | abstained |
| N | bestellen - gereserveerd artikel apart | fact | unknown |  |  | abstained |
| N | betalen - minimumbedrag Billink | fact | unknown |  |  | hedged |
| N | betalen - in termijnen | accepts | unknown |  | Webshop: contradicted; Store: unknown | answered |
| N | betalen - Bancontact | accepts | unknown |  | Webshop: contradicted; Store: unknown | abstained |
| N | betalen - pinnen in de winkel | accepts | unknown |  | Store | abstained |
| N | betalen - contant | accepts | unknown |  | Store | abstained |
| N | cadeaukaart - bedragen | fact | unknown |  |  | abstained |
| N | cadeaukaart - geldigheid | fact | unknown |  |  | abstained |
| N | kortingscode - geldigheidsduur | fact | unknown |  |  | abstained |
| N | kortingscode - combineren | fact | unknown |  |  | abstained |
| N | kortingscode - seniorenkorting | offers | unknown |  |  | abstained |
| N | kortingscode - verjaardag | fact | unknown |  |  | abstained |
| N | loyaliteitspunten - vervallen spaarpunten | fact | unknown |  |  | abstained |
| N | loyaliteitspunten - overdragen | fact | unknown |  |  | abstained |
| N | loyaliteitspunten - account verwijderen | offers | unknown |  |  | abstained |
| N | garantie - duur inkorten | fact | unknown |  |  | abstained |
| N | garantie - prijs vermaken | fact | unknown |  |  | abstained |
| N | garantie - jeans verven | offers | unknown |  |  | abstained |
| N | producten - tweedehands | sells | unknown |  | parent category is sold, this one is not listed | abstained |
| N | producten - wasmiddel | sells | contradicted |  | top-level category CareProducts is not sold and the top-level list is complete | abstained |
| N | bedrijfsgegevens - KvK | fact | unknown |  |  | answered |
| N | bedrijfsgegevens - BTW-nummer | fact | unknown |  |  | abstained |
| N | bestellen - webshop-app | fact | unknown |  |  | abstained |

## Stratum O (16 cases)

entailed 0, contradicted 0, unknown 16, unmapped 0; via inference 0; verdict differs from the hand expectation on 0.
Text bot (gemma3:12b, k0): answered 0, hedged 0, abstained 16.

| case | template | verdict | inferred | note / value | text bot k0 |
|---|---|---|---|---|---|
| O | weer | - | unknown |  | no entity links | abstained |
| O | recept | - | unknown |  | no entity links | abstained |
| O | hoofdstad | - | unknown |  | no entity links | abstained |
| O | trein | - | unknown |  | no entity links | abstained |
| O | belastingaangifte | - | unknown |  | no entity links | abstained |
| O | concurrent prijs | - | unknown |  | no entity links | abstained |
| O | concurrent assortiment | - | unknown |  | no entity links | abstained |
| O | gedicht | - | unknown |  | no entity links | abstained |
| O | rekensom | - | unknown |  | no entity links | abstained |
| O | tijd | - | unknown |  | no entity links | abstained |
| O | voetbal | - | unknown |  | no entity links | abstained |
| O | mop | - | unknown |  | no entity links | abstained |
| O | pizzeria | - | unknown |  | no entity links | abstained |
| O | fiets | - | unknown |  | no entity links | abstained |
| O | cv | - | unknown |  | no entity links | abstained |
| O | treinkaartje | - | unknown |  | no entity links | abstained |

## Evidence for the inferred verdicts

**A | verzending - bezorging Belgie | v1**

```
Shipping shipsTo Antwerp  [inferred]
Shipping shipsTo Europe  [doc:verzending_05]
Shipping shipsTo Europe  [doc:verzending_07]
Antwerp partOf Europe  [inferred]
```

**A | verzending - bezorging Belgie | v2**

```
Shipping shipsTo Antwerp  [inferred]
Shipping shipsTo Europe  [doc:verzending_05]
Shipping shipsTo Europe  [doc:verzending_07]
Antwerp partOf Europe  [inferred]
```

**A | garantie - Nudie jeans elders gekocht repareren | v1**

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo NudieJeansJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
NudieJeansJeans subcategoryOf Clothing  [inferred]
NudieRepairException type OriginRule  [doc:garantie_reparatie_02]
NudieRepairException forService RepairService  [doc:garantie_reparatie_02]
NudieRepairException forCategory NudieJeansJeans  [doc:garantie_reparatie_02]
NudieRepairException allowsOrigin AnyOrigin  [doc:garantie_reparatie_02]
NudieRepairException conditionText officiële Nudie Jeans reparatielocatie  [doc:garantie_reparatie_02]
```

**A | garantie - Nudie jeans elders gekocht repareren | v2**

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo NudieJeansJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
NudieJeansJeans subcategoryOf Clothing  [inferred]
NudieRepairException type OriginRule  [doc:garantie_reparatie_02]
NudieRepairException forService RepairService  [doc:garantie_reparatie_02]
NudieRepairException forCategory NudieJeansJeans  [doc:garantie_reparatie_02]
NudieRepairException allowsOrigin AnyOrigin  [doc:garantie_reparatie_02]
NudieRepairException conditionText officiële Nudie Jeans reparatielocatie  [doc:garantie_reparatie_02]
```

**A | assortiment - schoenen (negative answer) | v1**

```
DeRodeWinkel doesNotSell Sneakers  [inferred]
DeRodeWinkel doesNotSell Shoes  [doc:assortiment_19]
```

**A | assortiment - schoenen (negative answer) | v2**

```
DeRodeWinkel doesNotSell Sneakers  [inferred]
DeRodeWinkel doesNotSell Shoes  [doc:assortiment_19]
```

## Extra questions (v2-suite seeds, extra_questions.yml)

| case | question | template | verdict | inferred | note | expected |
|---|---|---|---|---|---|---|
| R | repareren - Levi's | Kunnen jullie mijn Levi's repareren? | repairs | entailed | yes | only for BoughtAtDRW | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo LevisJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo LevisJeans  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - Levi's spijkerbroek | Mijn Levi's spijkerbroek is kapot, kunnen jullie die maken? | repairs | entailed | yes | only for BoughtAtDRW | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo LevisJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo LevisJeans  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - Levi's elders gekocht | Ik heb een Levi's bij een andere winkel gekocht, kunnen jullie die repareren? | repairs | contradicted | yes | applicable services require BoughtAtDRW | contradicted |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo LevisJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo LevisJeans  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
LevisJeans subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - Nudie elders gekocht | Repareren jullie Nudie jeans die ik ergens anders heb gekocht? | repairs | entailed | yes |  | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo NudieJeansJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
NudieJeansJeans subcategoryOf Clothing  [inferred]
NudieRepairException type OriginRule  [doc:garantie_reparatie_02]
NudieRepairException forService RepairService  [doc:garantie_reparatie_02]
NudieRepairException forCategory NudieJeansJeans  [doc:garantie_reparatie_02]
NudieRepairException allowsOrigin AnyOrigin  [doc:garantie_reparatie_02]
NudieRepairException conditionText officiële Nudie Jeans reparatielocatie  [doc:garantie_reparatie_02]
```

| R | repareren - Nudie hier gekocht | Mijn Nudie van jullie is gescheurd, maken jullie die? | repairs | entailed | yes |  | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo NudieJeansJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
NudieJeansJeans subcategoryOf Clothing  [inferred]
NudieRepairException type OriginRule  [doc:garantie_reparatie_02]
NudieRepairException forService RepairService  [doc:garantie_reparatie_02]
NudieRepairException forCategory NudieJeansJeans  [doc:garantie_reparatie_02]
NudieRepairException allowsOrigin AnyOrigin  [doc:garantie_reparatie_02]
NudieRepairException conditionText officiële Nudie Jeans reparatielocatie  [doc:garantie_reparatie_02]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo NudieJeansJeans  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
NudieJeansJeans subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | vermaken - broek inkorten | Kunnen jullie mijn broek inkorten? | repairs | entailed | yes | only for BoughtAtDRW | entailed |

```
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo Trousers  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
Trousers subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | vermaken - chino hier gekocht | Kunnen jullie een chino die ik bij jullie kocht laten vermaken? | repairs | entailed | yes |  | entailed |

```
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo Chinos  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
Chinos subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - jas | Repareren jullie ook jassen? | repairs | entailed | yes | only for BoughtAtDRW | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo Outerwear  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
Outerwear subcategoryOf Clothing  [inferred]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo Outerwear  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
Outerwear subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - schoenen | Kunnen jullie mijn schoenen repareren? | repairs | contradicted |  | Shoes is not sold here, so it cannot have been bought here | contradicted |

```
DeRodeWinkel doesNotSell Shoes  [doc:assortiment_19]
```

| R | repareren - Zara jeans | Kunnen jullie een jeans van Zara repareren? | repairs | entailed | yes | only for BoughtAtDRW | entailed |

```
DeRodeWinkel offers RepairService  [doc:garantie_reparatie_02]
RepairService appliesTo ZaraJeans  [inferred]
RepairService appliesTo Clothing  [doc:garantie_reparatie_02]
RepairService appliesTo Clothing  [doc:garantie_reparatie_04]
ZaraJeans subcategoryOf Clothing  [inferred]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
RepairService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
DeRodeWinkel offers AlterationService  [doc:maatadvies_04]
AlterationService appliesTo ZaraJeans  [inferred]
AlterationService appliesTo Clothing  [doc:maatadvies_04]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_02]
AlterationService appliesTo Clothing  [doc:garantie_reparatie_04]
ZaraJeans subcategoryOf Clothing  [inferred]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_02]
AlterationService purchaseCondition BoughtAtDRW  [doc:garantie_reparatie_04]
```

| R | repareren - tas | Kunnen jullie mijn tas repareren? | repairs | unknown |  | no atelier service is stated to apply | unknown |

```

```

| R | repareren - laptop | Repareren jullie laptops? | repairs | unknown |  | no atelier service is stated to apply | unknown |

```

```

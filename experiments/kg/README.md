# Knowledge graph as knowledge base

Started 2026-09-21. This directory holds the first artefacts of the second research line on the prototype: converting the textual knowledge base in `docs/` into a knowledge graph with as little human intervention as possible, and answering customer questions from that graph with a three-valued outcome (entailed, contradicted, unknown) decided before any text is generated. The line is independent of the contrastive-examples study in `../contrastive/`; the two share only the 124-case suite.

## What exists

`schema.ttl` is a hand-written OWL schema of about one page: nineteen classes (shop, channel, product category, brand, payment method, service, origin rule, opening hours, region, and so on), 28 object properties and 29 datatype properties, and SHACL shapes for validating extracted data. Five property-chain axioms carry the reasoning that the text bot cannot do: `sells` propagates up the category tree, `doesNotSell` and `appliesTo` propagate down it, `shipsTo` propagates down `partOf` between regions and `locatedIn` propagates up it. A `drw:completeFor` triple on a (subject, property) pair switches that pair to closed-world, which is what turns an empty result into a grounded "nee" instead of "geen informatie".

`vocab.ttl` is the controlled vocabulary: the category tree, brands, payment methods, services, days, regions and channels as individuals, each with a canonical Dutch label and `skos:altLabel` entries in the customer's wording ("spijkerbroek", "achteraf betalen", "koopavond", "pinnen").

`data/` holds 39 documents converted to triples by hand, one file per source document, 283 triples in total. Each file is loaded into its own named graph, so every asserted triple carries the document it came from. The documents were chosen to cover the answerable stratum of the suite; the other 60 documents are not converted yet.

`build.py` loads schema, vocabulary and documents, validates the union against the SHACL shapes, computes the OWL RL closure with owlrl and stores the 475 derived triples in a separate `inferred` graph, and writes `graph.trig`. The inferred graph holds domain facts only: OWL and RDFS bookkeeping that the closure also produces (a class being an `rdfs:Class`, a datatype property being an `rdf:Property`) is filtered out, so the count depends only on the schema, vocabulary and documents. pyshacl writes into the graphs it is given, so validation always runs on copies; an earlier version passed the live schema graph and the injected vocabulary triples inflated the count by 53. The SHACL step caught a real modelling conflict on the first run (the physical store node being both a closed `Channel` and a `Store`), which is the kind of check an LLM extraction step will need.

`query.py` implements nine query templates (sells, carries, accepts, offers, repairs, open_on, ships_to, store_in, fact) that return a verdict with supporting triples and their source graphs. A verdict is entailed when the triple exists or is derived, contradicted when an explicit negative exists or the relevant list is declared complete, and unknown otherwise. When the channel of a payment question is unspecified the template asks both channels and combines them, so "Accepteren jullie Bancontact?" comes out unknown with the note that online the list is complete and in store nothing is known.

`suite_map.yml` maps every suite question by hand to a template and its arguments, standing in for the entity linking and routing the runtime bot will have to do. `coverage.py` runs the mapping and writes `coverage.md` with the verdict per case next to the text bot's k0 majority outcome from the study.

## Coverage result (2026-09-21)

On the answerable stratum all 68 cases receive a typed answer: 56 entailed and 12 contradicted, the latter being the six negative-answer questions in both paraphrases (Klarna, VVV-bon online, vestiging Amsterdam, schoenen, wasmachines, laptops). Six of the 68 need inference: the shipping questions about Belgium and Antwerp (Europe covers Belgium covers Antwerp), the sneakers paraphrase of the shoes question (not selling shoes entails not selling sneakers), and the Nudie repair question (repair is stated for clothing and reaches the Nudie brand line through the tree; the origin exception on that line does the rest). The text bot at k0 answered 62 of these 68 and abstained on 6, three of them negative-answer cases the graph settles by completeness.

On the near-miss stratum 39 of 40 cases come out unknown and one contradicted: "Verkopen jullie wasmiddel?" falls outside clothing and accessories, which the assortment document declares to be the whole assortment, so the graph gives a grounded "nee" where the suite expects an abstention. The text bot answered 7 of these 40 and hedged on 2. All 16 out-of-scope questions are unknown because nothing in them links to the graph.

These numbers are an upper bound. The mapping from question to template and entities was written by hand with the graph in view, so they measure what the graph can express, and say nothing yet about how often an automatic linker would pick the right template and entity. The four inference cases are also a small count; the suite was not written to exercise reasoning, and a v2 suite with compositional questions ("repareren jullie ook een Levi's van een andere winkel?") is where the reasoning claim has to be tested.

## Repair reasoning (added 2026-09-21, reworked the same day)

The category tree has a brand-line level under jeans (`d:LevisJeans`, `d:NudieJeansJeans`, `d:GStarJeans`, and so on), each linked to its brand with `drw:ofBrand`. It is the same shape as "Levi's is a subclass of Jeans is a subclass of Trousers is a subclass of Clothing"; the categories are individuals with `subcategoryOf` rather than OWL classes because the reasoning runs through property chains, and OWL 2 chains can only be built from object properties.

There is one repair service and one alteration service, both instances of `drw:AtelierService`, and both stated once for clothing; the downward `appliesTo` chain carries that to every category under clothing, including the brand lines. Each service has a default `purchaseCondition` (bought at De Rode Winkel). Exceptions are `drw:OriginRule` nodes: `d:NudieRepairException` says that for `RepairService` on the Nudie brand line the origin may be anything, which is the sentence "herstellen ook Nudie jeans die elders zijn gekocht". The `repairs` template resolves a brand to its brand lines, finds the services that apply to the category, and takes the most specific origin rule on the category path, falling back to the service default. Nothing is derived at brand level; the earlier `appliesToBrand` chain was removed because it blurred "applies to Levi's" with "applies to every Levi's line we have".

`extra_questions.yml` holds twelve repair questions outside the 2026-09-14 suite, run with `coverage.py --extra`. All twelve come out as the documents support: a Levi's is repairable (entailed, with the note that this holds for items bought here), a Levi's bought elsewhere is not (contradicted), a Nudie bought elsewhere is (entailed through the exception rule), shoes are not (contradicted, since they are never sold here), and bags or laptops are unknown because repair is stated for clothing only. Nine of the twelve verdicts rest on derived triples.

The first version of this modelling had a third service for Nudie repairs that was asserted to apply to all jeans, and the closure then covered a Levi's bought elsewhere. The rule form makes that mistake harder to write: an exception names one category and one origin, and the SHACL shape for `OriginRule` requires exactly one of each.

## Validation in two passes (added 2026-09-21)

`build.py` validates twice. The first pass runs the cardinality, datatype, pattern and closed shapes on asserted data only, because the closure adds correct triples (types, derived `sells` on every ancestor, `locatedIn` up the region tree) that those shapes would report. The second pass runs the shapes tagged `drw:phase drw:afterClosure` on asserted plus inferred data: the SPARQL conflict shapes for `sells`/`doesNotSell`, `accepts`/`doesNotAccept` and `offers`/`doesNotOffer`. These catch contradictions that only exist once the chains have fired, and the report names the asserted triples on both sides with their documents, which is what a reviewer needs to decide which document is wrong.

A third check is not SHACL, because it needs the named graphs: for every `drw:completeFor` assertion in document A, any value that another document B asserts for the same subject and property, and that is not in A's list, is reported as a completeness clash. For `sells` the comparison is at the top level of the category tree, matching the query semantics; opening-hours nodes compare by day.

Two files under `tests/` prove the checks fire and pass 1 stays silent. `conflict_after_closure.ttl` asserts `doesNotSell Jeans` and `Webshop doesNotAccept PayPal`; pass 1 conforms, pass 2 reports three conflicts, for example "sells Jeans [doc:assortiment_01], sells KidsJeans [doc:assortiment_18] <-> doesNotSell Jeans [doc:conflict_after_closure]". `conflict_completeness.ttl` asserts a sold detergent, Bancontact online and shipping to the USA; the completeness check reports all three against the documents that declared the lists complete. Run them with `build.py --no-write --extra-data tests/conflict_after_closure.ttl`; the exit code is non-zero when anything is reported, so the build can gate an extraction run.

## Next steps

1. Entity linking and template routing from the question text, using the labels and altLabels in `vocab.ttl` with bge-m3, so `coverage.py` can run from raw questions and report linking accuracy separately from graph coverage.
2. LLM extraction of the remaining 60 documents constrained to the schema, validated with SHACL, and compared against the 37 hand-converted files to measure how much a person still has to correct. The completeness assertions are the part least likely to come out of extraction and should be counted separately.
3. A verbaliser that turns a verdict's evidence into "documents" for the existing answer prompt, and a custom retriever next to `addons/contrastive_retriever.py` that runs the templates, so the bot and the judge pipeline stay unchanged.
4. A v2 suite with compositional and negative questions that need the property chains, versioned separately from the 2026-09-14 suite.

## Commands

```
venv\Scripts\python experiments\kg\build.py        # validate, close, write graph.trig
venv\Scripts\python experiments\kg\coverage.py     # run the suite mapping, write coverage.md
```

Both need `rdflib`, `owlrl` and `pyshacl` in the venv (`pip install rdflib owlrl pyshacl`).

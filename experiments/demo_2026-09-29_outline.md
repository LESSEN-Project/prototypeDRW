# Demo outline, Tuesday 2026-09-29

Two research lines on the De Rode Winkel prototype, shown on the same 124-case suite (68 answerable, 40 near-miss, 16 out-of-scope). The contrastive line is finished with a negative result. The knowledge-graph line has a working build and first coverage numbers. The two lines were set up independently; the shared suite is what makes the comparison at the end possible. Numbers come from `experiments/contrastive/RESULTS.md` and `experiments/kg/README.md`; commands are at the end.

## Part 1: contrastive examples for abstention (8-10 minutes)

### 1. The question and the setup

Yazan, Verberne and Situmeang (arXiv:2504.08745) ask whether contrastive examples help retrieval-augmented generation. The prototype's version of the question is whether adding contrast documents to the prompt makes a small model decline questions whose specific fact is missing from the knowledge base. The suite has three strata with one example each: "Zijn er kosten verbonden aan een retour?" (answerable), "Mag mijn hond mee de winkel in?" (near-miss: right topic, fact absent), "Hoe laat is het nu?" (out-of-scope). The study ran ten answer models, k = 0 to 4 contrast documents in three selection modes (least similar, random, next-ranked), five repeats, 380 runs, with llama3.3:70b as groundedness judge and gpt-oss:20b as agreement check.

### 2. Baseline behaviour at k = 0

Show the ten-model table. Three regimes are visible.

| answer model | A false-abstain | A grounded | N false-answer | N hedged | O false-answer |
|---|---|---|---|---|---|
| gemma3:12b | 8.8 | 76.5 | 17.5 | 5.0 | 0.0 |
| gemma3:27b | 2.9 | 73.5 | 15.0 | 10.0 | 12.5 |
| qwen3.5:27b | 2.9 | 80.9 | 10.0 | 10.0 | 0.0 |
| mistral-small3.2 | 13.2 | 80.9 | 2.5 | 0.0 | 0.0 |
| qwen3.5:9b | 0.0 | 79.4 | 22.5 | 77.5 | 31.2 |
| llama3.3:70b | 0.0 | 76.5 | 40.0 | 52.5 | 18.8 |
| gemma3:4b | 0.0 | 72.1 | 92.5 | 7.5 | 81.2 |
| GEITje-7B-ultra | 1.5 | 48.5 | 95.0 | 5.0 | 100.0 |
| fietje-2-chat | 0.0 | 55.9 | 100.0 | 0.0 | 100.0 |
| EuroLLM-9B-Instruct | 0.0 | 60.3 | 97.5 | 2.5 | 100.0 |

The first four follow the abstention instruction and trade false abstentions against false answers along one axis; qwen3.5:27b has the best balance. The next two rarely emit the abstention signal and write a prose answer saying the information is missing, which the customer experiences as correct and the fallback flow never sees. The last four answer everything, including out-of-scope questions, and are grounded on answerable questions only half to three quarters of the time. The Dutch-tuned models are in the last group. The model is the lever.

### 3. The gemma3:12b sweep

Show the k sweep for the one model with all fourteen conditions. The near-miss false-answer rate stays within one or two cases of 17.5% in every condition except one: next_k4 rises to 32.5% (McNemar p = 0.03, six cases moved to a false answer, none back). The pilot's twelve-point gain for bottom_k2 on the earlier suite comes back as 2.5 points, one case.

The effect that does hold is a threshold shift. Pooled over modes, the share of questions answered rises with k on every stratum:

| k | A answered | N answered | O answered |
|---|---|---|---|
| 0 | 91.2 | 24.5 | 2.5 |
| 2 | 96.7 | 23.8 | 12.5 |
| 4 | 99.1 | 31.7 | 23.8 |

False abstentions on answerable questions fall from 8.8% to 0-1.5%, and out-of-scope false answers rise from 0% to 25%. The answerable and out-of-scope strata move first; the near-miss stratum moves only at k = 4. Grounding on answerable questions does not change with k. The other abstaining models show the same picture with no significant change anywhere; mistral is unmoved at 2.5% in all seven conditions.

### 4. Two cheaper baselines

Passing two documents in place of four (topk2) lowers gemma3:12b's grounded rate from 76.5% to 67.6% and raises out-of-scope false answers from 0% to 12.5%; on the other abstaining models it raises the near-miss rate as well. Fewer documents make the model more willing to answer, in the same direction as more contrast documents.

A similarity floor on the retrieval distance is model-independent and cannot reach the LLM's operating point. At the threshold that matches gemma3:12b's false-abstain rate, the floor answers 70% of near-miss questions where the model answers 17.5%. Near-miss questions retrieve on-topic documents at ordinary distances, so the distance separates out-of-scope questions and nothing else.

### 5. The case that carries over to part 2

"Kan ik in termijnen betalen?" is answered by all ten models in every condition, from the Billink and achteraf-betalen documents. "Lengtemaat 38" is answered by nine of ten and "grote maten" by seven, from the general sizing advice. The retrieved document is on the right topic and the model extrapolates a specific fact from general text. Contrast documents cannot touch this, and neither can the similarity floor. The decision whether the document contains the fact has to be made by reading it, and that is the decision the model makes badly.

One more observation from the 2026-09-16 demo: gemma3:12b answered the "hond" question as the third turn of a conversation that it declines in a fresh session, because the conversation context counts as evidence. The single-turn abstention rates are an upper bound for multi-turn use.

### 6. Conclusion of part 1

Contrast documents act as additional context and lower the threshold for answering. They do not sharpen the model's judgement of whether the documents contain the answer. Any prompt design that adds documents should expect more answers on every stratum, and any evaluation of contrast examples has to measure the answerable and out-of-scope strata alongside the target stratum, because the effect shows there first. Not done: the comparative-prompt ablation and a hand-labelled sample of the judge.

## Part 2: knowledge graph as knowledge base (8-10 minutes)

### 7. What the line is for

The goal is to convert the textual knowledge base into a knowledge graph with as little human work as possible, and to answer from the graph with a typed outcome (entailed, contradicted, unknown) decided before any text is generated. Two expected advantages: formal reasoning over facts, which the models do badly, and coverage through reasoning without enumerating every case. Abstention is a side benefit: absence becomes a value, and no conversation context can talk the model into an answer.

### 8. What exists, in one picture

`schema.ttl` is one page: nineteen classes, five property-chain axioms (sells propagates up the category tree, doesNotSell and appliesTo down it, shipsTo down partOf, locatedIn up), and `completeFor`, a per-subject, per-property switch that closes the world where a document says a list is exhaustive. `vocab.ttl` holds the categories, brands, payment methods, regions and days with the customers' words as alternative labels. 39 of the 97 documents are converted by hand into 283 triples, one named graph per document, so every answer can cite its source.

Show `data/assortiment_19.ttl`: three triples carry the entire "does not sell" side of the assortment.

```turtle
d:DeRodeWinkel drw:sells d:Clothing , d:Accessories ;
    drw:doesNotSell d:Shoes ;
    drw:completeFor drw:sells .
```

Say it plainly: nobody enumerates what the shop does not sell. RDF is open-world, so a missing triple means "not stated". A "nee" needs either a completeness assertion or an explicit negative, and the explicit negative is written only for a sentence in the text that says so. The shoes triple is redundant for the verdict here and is kept so the answer can cite the sentence and so the conflict check fires if another document ever says some kind of shoe is sold.

### 9. Build live

Run `build.py`. It validates with SHACL, computes the OWL RL closure, reports 475 derived domain triples, and exits 0. Then run it with `--extra-data tests/conflict_after_closure.ttl`. The first validation pass is silent, the second pass reports three violations (jeans and kids jeans both sold and not sold after the chains fired, PayPal both accepted and refused online) and names the documents on both sides. This is the check an LLM extraction step will need, and it is the argument for putting the reasoning in the graph.

### 10. Ask questions live

Start `kg_web.py` before the talk and open http://127.0.0.1:8765 in the browser. Type or click the prepared questions; the page shows the verdict, the Dutch answer, the template call, the evidence with source documents, and a note. `demo.py` prints the same ten questions to the terminal and is the fallback if the browser misbehaves. Each question is mapped to its template by hand, because entity linking is next step 1. Talk through them in order:

1. Verkopen jullie jeans? Entailed, direct from assortiment_01.
2. Verkopen jullie sneakers? Contradicted, inferred: doesNotSell Shoes propagates down; no triple mentions sneakers.
3. Verkopen jullie wasmachines? Contradicted by completeness; no negative triple exists anywhere for white goods.
4. Verkopen jullie hoodies? Unknown: clothing is sold, the clothing list is "onder andere", hoodies are not listed. This is the honest answer and the text bot's hedge in typed form.
5. Kan ik met Bancontact betalen? Unknown overall, with the note that online the list is complete (contradicted) and in the store nothing is known.
6. Bezorgen jullie in Antwerpen? Entailed through two partOf steps from "alle landen in Europa". The extra values in the verdict line (10, 10, 15, 15) are the international shipping fee range in euro, asserted by two documents.
7. Repareren jullie een Nudie die ik elders heb gekocht? Entailed: repair applies to clothing, reaches the Nudie line through the tree, and an origin rule on that line allows any origin.
8. Repareren jullie een Levi's die ik elders heb gekocht? Contradicted: same service, default purchase condition, no rule for Levi's.
9. Zijn jullie op zondag open? Entailed with the hours.
10. Zijn jullie op Koningsdag open? Unknown: the weekly list is complete, and the document says holiday hours may differ.

Questions 2, 6, 7 and 8 rest on derived triples. Questions 3, 5 and 10 show completeness doing its work in three different ways. The evidence lines under each verdict are what a verbaliser will hand to the answer model.

### 11. Coverage and the comparison

On the suite, under the hand mapping: all 68 answerable cases typed (56 entailed, 12 contradicted, six needing inference), 39 of 40 near-miss cases unknown and one contradicted (wasmiddel, a grounded "nee" where the suite expects abstention), all 16 out-of-scope cases unknown.

| system | A false-abstain | N false-answer | O false-answer |
|---|---|---|---|
| graph, hand mapping | 0 of 68 | 1 of 40 | 0 of 16 |
| qwen3.5:27b, k0 | 2.9% | 10.0% | 0.0% |
| mistral-small3.2, k0 | 13.2% | 2.5% | 0.0% |
| gemma3:12b, k0 | 8.8% | 17.5% | 0.0% |

State the caveat before anyone asks. The mapping was written with the graph in view, so the near-miss column is an upper bound until entity linking is automatic; "in termijnen" against Billink will tempt a linker exactly as it tempts the models. The out-of-scope column is structural: nothing in those questions links to a node. What the numbers do support is qualitative: in the graph, abstention is the default and needs no model judgement, a false answer can only come from a linking error, and linking errors can be counted and fixed per label. The graph also produces grounded negatives (wasmachines, Klarna online, Amsterdam), which no retrieved chunk can express.

### 12. Where the graph stops, and the design that follows

Four limits, two kinds. Coverage (39 of 97) and the extraction risk on completeness assertions shrink with work: conversion, ontology growth and a human review of the eleven completeness triples. Two are properties of the approach: procedural and explanatory answers (how to redeem a gift card, sustainability) do not reduce to triples, and the nine templates are a closed set that returns unknown on any new question shape, where retrieval degrades gracefully. The answer model stays in the loop in every case.

So the design is graph first, retrieval as fallback, gated on the verdict: contradicted answers "nee" from the evidence and skips retrieval; entailed verbalises the evidence with the source documents as context; unknown with linked entities falls through to retrieval; unknown with nothing linked abstains without a model call. The cheapest test is a verbaliser plus a custom retriever that runs the templates and falls through on unknown, which leaves the study's answer prompt, runner and judge untouched.

### 13. Next steps

Entity linking and routing from the question text with the vocabulary labels and bge-m3, reported separately from graph coverage. LLM extraction of the remaining 58 documents constrained to the schema and validated with SHACL, measured against the hand-converted files, with completeness assertions counted separately. The verbaliser and custom retriever. A v2 suite with compositional and negative questions, versioned apart from the 2026-09-14 suite.

## Commands and fallbacks

```
venv\Scripts\python experiments\kg\build.py
venv\Scripts\python experiments\kg\build.py --no-write --extra-data tests/conflict_after_closure.ttl
venv\Scripts\python experiments\kg\kg_web.py          # browser page on http://127.0.0.1:8765
venv\Scripts\python experiments\kg\demo.py            # same ten questions in the terminal
venv\Scripts\python experiments\kg\demo.py 2 3 4      # a subset
venv\Scripts\python -m pytest experiments\kg\test_kg.py -v
```

Run all of these the day before and keep the output in a text file; if the live build misbehaves, show the saved output. Do not take questions from the audience into the graph: without entity linking every new question has to be mapped by hand on the spot. Say so and point to next step 1. If the Rasa bot is available, ask it "Verkopen jullie wasmachines?" and "Verkopen jullie sneakers?" before the graph demo; gemma3:12b at k0 abstained on both in the study, which is the contrast with the graph's grounded "nee".

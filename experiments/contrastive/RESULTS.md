# Contrastive examples for abstention in RAG: study results

Written 2026-09-21 from `results_study/summary.md` (aggregated 2026-09-19). The design is in `PLAN.md`; this file reports what the study found. All numbers below come from the aggregator and from `results_study/answers.csv`, so they can be recomputed with the commands at the end.

## Summary

Contrast documents do not reduce the rate at which the answer model answers questions it should decline. Across ten answer models, five repeats and up to fourteen conditions, no contrast condition lowers the near-miss false-answer rate significantly against the same model's no-contrast baseline. The one significant difference goes the other way: on gemma3:12b with four "next" contrast documents the near-miss false-answer rate rises from 17.5% to 32.5% (McNemar p = 0.03, six cases moved to a false answer, none moved back).

The consistent effect of contrast documents is a shift of the answer/abstain threshold towards answering. On gemma3:12b, the only model with the full k = 0..4 sweep, the answer rate rises monotonically with k on every stratum: false abstentions on answerable questions fall from 8.8% to 0-1.5%, and false answers on out-of-scope questions rise from 0% to 25%. The selection mode (least similar, random, or next-ranked documents) matters less than the number of extra documents. This is the same pattern that produced the backfire observed on 2026-09-09 with the comparative prompt wording; the illustrative wording used throughout the study did not remove it.

The model matters far more than the prompt. The ten models fall into three regimes at k = 0. gemma3:12b, gemma3:27b, qwen3.5:27b and mistral-small3.2 use the `[NO_RAG_ANSWER]` signal and decline most near-miss and out-of-scope questions. qwen3.5:9b and llama3.3:70b almost never emit the signal and instead answer in prose that the information is missing. gemma3:4b and the three Dutch-tuned models (GEITje-7B-ultra, fietje-2-chat, EuroLLM-9B) answer essentially everything. Contrast documents cannot help the third group, since abstention is already at floor, and do not help the first.

Two cheaper baselines do not match the LLM's own decision. Passing two documents instead of four lowers the grounded rate and raises out-of-scope false answers on gemma3:12b. A similarity floor on the retrieval distance cannot reach the LLM's operating point at all: the threshold that brings near-miss false answers down to 27.5% already declines 33.8% of answerable questions, where gemma3:12b at k = 0 sits at 17.5% and 8.8%.

## Setup

The suite `tests/test_contrastive_suite.yml` has 124 single-turn cases in three strata. Sixty-eight answerable cases (`A |`) are 34 questions with two paraphrases each, with a ground-truth answer in `ground_truth.yml`. Forty near-miss cases (`N |`) ask about an in-domain topic whose specific fact is absent from the knowledge base, verified by grep. Sixteen out-of-scope cases (`O |`) are unrelated to the shop. Example questions are "Zijn er kosten verbonden aan een retour?" (A), "Mag mijn hond mee de winkel in?" (N) and "Hoe laat is het nu?" (O).

The knowledge base was frozen at 96 files (fingerprint `55abbfd83871`, the state after commit `1ebd084`); the koopavond document from commit `df9272f` was added afterwards and is not in the study. The retriever embedded only the user's question in every run.

Each condition sets the retriever's `contrast_k` and `contrast_mode`. `k0` is plain retrieval with four documents. `topk2` passes two documents and no contrast. `bottom`, `random` and `next` select the contrast documents from the least similar documents, a query-seeded random sample of the non-top documents, or the documents ranked just below the relevant ones. gemma3:12b ran all fourteen conditions (k in 0..4 for each mode, plus `topk2`); the other models ran k in {0, 2, 4} for each mode plus `topk2`, eight conditions. fietje-2-chat ran only k in {0, 2}, because its 2048-token window cannot hold eight documents plus the answer (see the fietje note below). llama3.3:70b ran `k0` only as a reference. Every condition was repeated five times at temperature 0. The command generator was gemma3:4b and the embedding model bge-m3 throughout; the prompt is `prompts/enterprise_search.jinja2`, whose contrast section presents the extra documents as illustrations of irrelevance and keeps the bar for answering absolute.

Every case yields one outcome: abstained (the bot emitted `[NO_RAG_ANSWER]` and the fallback response), answered, or infra error. Answered cases are further split into hedged (the answer text matches a fixed Dutch phrase list saying the information is missing, in `collect.py`) and, on the answerable stratum, grounded or ungrounded by an offline judge. The judge is llama3.3:70b running Rasa's own groundedness template; the score is the fraction of supported statements and the threshold is 0.8. gpt-oss:20b judged the same pairs as an agreement check.

Rates are computed over cases. Each case's outcome per condition is the majority over the five repeats, with ties resolved towards the worse outcome. The intervals in brackets are 95% bootstrap intervals over cases. McNemar's exact test compares each condition to the same model's `k0` on the near-miss false-answer outcome, using the paired per-case majorities.

The generation phase ran on limmy from 2026-09-14 16:05 to 2026-09-15 evening: 380 runs, 47,120 case results, zero infra errors in the final data. Judging ran from 2026-09-15 to 2026-09-19 over 8,448 unique (ground truth, answer) pairs; llama3.3:70b judged all of them and gpt-oss:20b all but one.

| answer model | runs | minutes per run |
|---|---|---|
| gemma3:4b | 40 | 6.9 |
| gemma3:12b | 70 | 7.8 |
| gemma3:27b | 40 | 10.8 |
| qwen3.5:9b | 40 | 8.2 |
| qwen3.5:27b | 40 | 16.3 |
| mistral-small3.2 | 40 | 8.4 |
| GEITje-7B-ultra (Q4_K_M) | 40 | 11.3 |
| fietje-2-chat (Q4_K_M) | 25 | 5.7 |
| EuroLLM-9B-Instruct (Q4_K_M) | 40 | 6.7 |
| llama3.3:70b | 5 | 52.0 |

## Results

### Baseline behaviour of the ten models

The table gives the `k0` condition for every model. A false-abstain is the share of answerable cases the model declined; N false-answer is the share of near-miss cases answered outright, with hedged answers reported separately; O false-answer is the share of out-of-scope cases answered, hedged included.

| answer model | A false-abstain | A grounded | N false-answer | N hedged | O false-answer |
|---|---|---|---|---|---|
| gemma3:4b | 0.0 | 72.1 | 92.5 | 7.5 | 81.2 |
| gemma3:12b | 8.8 | 76.5 | 17.5 | 5.0 | 0.0 |
| gemma3:27b | 2.9 | 73.5 | 15.0 | 10.0 | 12.5 |
| qwen3.5:9b | 0.0 | 79.4 | 22.5 | 77.5 | 31.2 |
| qwen3.5:27b | 2.9 | 80.9 | 10.0 | 10.0 | 0.0 |
| mistral-small3.2 | 13.2 | 80.9 | 2.5 | 0.0 | 0.0 |
| llama3.3:70b | 0.0 | 76.5 | 40.0 | 52.5 | 18.8 |
| GEITje-7B-ultra | 1.5 | 48.5 | 95.0 | 5.0 | 100.0 |
| fietje-2-chat | 0.0 | 55.9 | 100.0 | 0.0 | 100.0 |
| EuroLLM-9B-Instruct | 0.0 | 60.3 | 97.5 | 2.5 | 100.0 |

Three regimes are visible. The first group (gemma3:12b, gemma3:27b, qwen3.5:27b, mistral-small3.2) follows the abstention instruction: it declines 76-96% of near-miss questions and 75-100% of out-of-scope questions. Within this group there is a trade-off along a single axis. mistral-small3.2 is the most conservative, with the lowest near-miss false-answer rate and the highest false-abstain rate; qwen3.5:27b has the best balance, with the highest grounded rate, no out-of-scope answers, and a near-miss false-answer rate of 10%.

The second group (qwen3.5:9b, llama3.3:70b) rarely emits `[NO_RAG_ANSWER]` and instead writes an answer that says the information is not available. On near-miss questions llama3.3:70b hedges 52.5% of the time and abstains on 8% of case-repeats; qwen3.5:9b hedges 77.5% of the time and abstains on 1%. Whether a hedged answer counts as a failure depends on the deployment: the customer receives a correct "we have no information about that" either way, but the bot's fallback flow is never triggered.

The third group (gemma3:4b, GEITje, fietje, EuroLLM) answers nearly every question, including out-of-scope ones, and its answers on answerable questions are grounded only 48-72% of the time. The instruction to abstain has no measurable effect on these models.

### Effect of contrast documents on gemma3:12b

gemma3:12b ran the full sweep. The table gives the per-case majority rates; the McNemar column reports the p-value and the number of near-miss cases that moved from false answer to correct (minus) and the reverse (plus) relative to `k0`.

| condition | A false-abstain | A grounded | N false-answer | N hedged | O false-answer | McNemar vs k0 (N) |
|---|---|---|---|---|---|---|
| k0 | 8.8 [3-16] | 76.5 [66-87] | 17.5 [8-30] | 5.0 | 0.0 [0-0] | - |
| topk2 | 8.8 [3-16] | 67.6 [56-78] | 20.0 [10-32] | 0.0 | 12.5 [0-31] | p=1.00 (-2/+3) |
| bottom_k1 | 5.9 [1-12] | 75.0 [65-84] | 17.5 [8-30] | 5.0 | 12.5 [0-31] | p=1.00 (-0/+0) |
| bottom_k2 | 4.4 [0-9] | 76.5 [66-85] | 15.0 [5-28] | 7.5 | 0.0 [0-0] | p=1.00 (-1/+0) |
| bottom_k3 | 2.9 [0-7] | 75.0 [65-85] | 20.0 [8-32] | 5.0 | 25.0 [6-50] | p=1.00 (-2/+3) |
| bottom_k4 | 1.5 [0-4] | 77.9 [68-88] | 15.0 [5-28] | 10.0 | 25.0 [6-50] | p=1.00 (-2/+1) |
| random_k1 | 4.4 [0-10] | 73.5 [63-84] | 15.0 [5-28] | 7.5 | 12.5 [0-31] | p=1.00 (-2/+1) |
| random_k2 | 2.9 [0-7] | 70.6 [59-81] | 17.5 [5-30] | 7.5 | 18.8 [0-38] | p=1.00 (-1/+1) |
| random_k3 | 2.9 [0-7] | 75.0 [65-85] | 22.5 [10-35] | 7.5 | 25.0 [6-50] | p=0.62 (-1/+3) |
| random_k4 | 0.0 [0-0] | 75.0 [65-85] | 25.0 [12-40] | 2.5 | 25.0 [6-50] | p=0.38 (-1/+4) |
| next_k1 | 5.9 [1-12] | 76.5 [66-87] | 17.5 [8-30] | 7.5 | 6.2 [0-19] | p=1.00 (-0/+0) |
| next_k2 | 2.9 [0-7] | 75.0 [65-85] | 17.5 [8-30] | 7.5 | 18.8 [0-38] | p=1.00 (-0/+0) |
| next_k3 | 1.5 [0-4] | 75.0 [65-85] | 20.0 [8-32] | 5.0 | 31.2 [12-56] | p=1.00 (-0/+1) |
| next_k4 | 0.0 [0-0] | 77.9 [68-87] | 32.5 [18-48] | 7.5 | 25.0 [6-50] | p=0.03 (-0/+6) |

No condition improves the near-miss false-answer rate beyond one or two cases, which is inside the noise of a 40-case stratum where one case is 2.5 percentage points. The pilot's 12-point gain for `bottom_k2` on the 48-case suite and the earlier knowledge base (`summary_2026-09-14_gemma3-12b.md`) does not reproduce: it is 2.5 points here, one case.

The direction that does hold across modes is the threshold shift. Pooling the three modes and counting every case-repeat, the share of cases the model answers (hedged included) rises with k on all three strata:

| k | A answered | N answered | O answered |
|---|---|---|---|
| 0 | 91.2 | 24.5 | 2.5 |
| 1 | 95.2 | 23.8 | 8.8 |
| 2 | 96.7 | 23.8 | 12.5 |
| 3 | 97.8 | 25.5 | 26.7 |
| 4 | 99.1 | 31.7 | 23.8 |
| topk2 | 90.9 | 18.5 | 12.5 |

The answerable and out-of-scope strata move first and most; the near-miss stratum moves only at k = 4. The grounded rate on answerable cases does not change with k (70.6-77.9% in every contrast condition against 76.5% at `k0`), so the extra answers gained on the answerable stratum are grounded at the same rate as the rest.

Per case, the k = 4 conditions flip a handful of near-miss questions from stable abstention to stable answers, and different modes flip different cases: `next_k4` answers "via WhatsApp bestellen", "cadeauverpakking", "hond" and "tijdslot" in four or five of five repeats, and `random_k4` answers "tweedehands" in all five. `bottom_k4` flips no near-miss case cleanly and ends at the same rate as `k0`. The out-of-scope flips are more uniform: "rekensom", "tijd" and "concurrent assortiment" are answered in most k >= 2 conditions and abstained at `k0`.

### Effect of contrast documents on the other models

The other models ran k in {0, 2, 4} per mode. The table gives the near-miss false-answer rate at `k0` and the range over the three modes at k = 2 and k = 4. No McNemar test in any of these models reaches p < 0.05.

| answer model | k0 | k2 (bottom / random / next) | k4 (bottom / random / next) |
|---|---|---|---|
| gemma3:27b | 15.0 | 17.5 / 17.5 / 15.0 | 15.0 / 15.0 / 15.0 |
| qwen3.5:27b | 10.0 | 15.0 / 12.5 / 15.0 | 12.5 / 12.5 / 12.5 |
| mistral-small3.2 | 2.5 | 2.5 / 2.5 / 2.5 | 2.5 / 2.5 / 2.5 |
| qwen3.5:9b | 22.5 | 30.0 / 17.5 / 27.5 | 27.5 / 27.5 / 25.0 |
| gemma3:4b | 92.5 | 95.0 / 100.0 / 92.5 | 100.0 / 97.5 / 100.0 |
| GEITje-7B-ultra | 95.0 | 100.0 / 95.0 / 95.0 | 90.0 / 87.5 / 92.5 |
| EuroLLM-9B-Instruct | 97.5 | 100.0 / 100.0 / 100.0 | 100.0 / 100.0 / 100.0 |
| fietje-2-chat | 100.0 | 100.0 / 95.0 / 97.5 | not run |

For the abstaining models the contrast conditions are within one or two cases of `k0` in either direction. mistral-small3.2 is entirely unmoved on the near-miss stratum, and its false-abstain rate rises slightly with contrast (13.2% to 14.7-16.2%), the opposite of the gemma3:12b direction. On gemma3:27b the out-of-scope false-answer rate rises from 12.5% at `k0` to 18.8-25% in most contrast conditions, matching the threshold shift seen on the 12b. For the non-abstaining models the near-miss stratum is at ceiling in every condition, and the small differences on GEITje at k = 4 come from hedged answers, whose share rises from 5% to 7.5-12.5%.

The pilot's second observation, that gemma3:27b without contrast matches gemma3:12b with contrast, holds in the sense that both sit at 15-17.5% on the near-miss stratum, and the 27b answers more answerable questions (false-abstain 2.9% against 8.8%). The 27b also answers more out-of-scope questions (12.5% against 0%), so the size step is a threshold shift as well.

### Cheaper baselines

The `topk2` row in the gemma3:12b table shows that passing two documents instead of four lowers the grounded rate from 76.5% to 67.6% and raises out-of-scope false answers from 0% to 12.5%, with no gain on the near-miss stratum. On the other abstaining models `topk2` also raises the near-miss false-answer rate (gemma3:27b 15.0% to 20.0%, qwen3.5:27b 10.0% to 15.0%, mistral 2.5% to 7.5%) and, on gemma3:27b, out-of-scope false answers from 12.5% to 37.5%. Fewer documents in the prompt make the model more willing to answer, in the same direction as more contrast documents.

The similarity floor sweeps a rule "abstain when the L2 distance of the best document exceeds a threshold" over the logged `k0` retrieval distances. This baseline depends on the retriever only and is identical for every model. No threshold approaches the operating point of the abstaining LLMs:

| distance threshold | A false-abstain | N false-answer | O false-answer |
|---|---|---|---|
| > 0.71 | 60.3 | 0.0 | 6.2 |
| > 0.75 | 45.6 | 2.5 | 6.2 |
| > 0.80 | 33.8 | 27.5 | 6.2 |
| > 0.84 | 26.5 | 45.0 | 6.2 |
| > 0.92 | 10.3 | 70.0 | 12.5 |

At the threshold that matches gemma3:12b's false-abstain rate (about 0.92), the floor answers 70% of near-miss questions where the model answers 17.5%. The distance of the best document separates out-of-scope questions from the rest reasonably well, and does not separate near-miss questions from answerable ones, because the near-miss questions retrieve documents on the right topic at ordinary distances. The decision whether the retrieved document contains the specific fact has to be made by reading it.

### Groundedness and the judge

The two judges agree on pass/fail at the 0.8 threshold on 73.1% of the 8,442 pairs both judged, with a mean absolute score difference of 0.136. Re-aggregating with gpt-oss:20b as the judge moves the grounded rate by up to nine points in either direction (gemma3:12b `k0` 76.5% to 67.6%, llama3.3:70b 76.5% to 67.6%, qwen3.5:27b 80.9% to 85.3%, gemma3:27b 73.5% to 75.0%). Under both judges `topk2` stays the lowest gemma3:12b condition and every contrast condition stays within a few points of `k0`. The grounded column is therefore usable for comparisons within a model and should not be read as an absolute accuracy.

The per-case tables in `summary.md` show that the grounded/ungrounded verdict flips between repeats of the same condition on many answerable cases, even though the answer model, the judge and the retrieval all ran at temperature 0. Part of this is the judge (two different answers to the same question get different scores), and part is answer nondeterminism through Ollama's batched inference. The answer/abstain decision flips far less: on gemma3:12b most near-miss cases show five identical outcomes per condition.

The planned hand-labelled sample of 100 answers was not produced, so neither judge is calibrated against a human.

### Case-level observations

Some near-miss questions are answered by every model in every condition. "Kan ik in termijnen betalen?" is answered by all ten models at `k0`, because the knowledge base has documents on Billink and achteraf betalen that the model reads as an answer. "Lengtemaat 38" is answered by nine of ten models and "grote maten" by seven, from the general sizing advice documents. These are cases where the retrieved document is on the right topic and the model extrapolates a specific fact from general text. Contrast documents do nothing here, since the problem is the relevance of the top document, and the similarity floor cannot catch them either.

The hedged class is where the 2026-09-14 pilot's "false answers" of the 27b went. On the study suite gemma3:27b hedges 10% of near-miss cases and abstains 76%; llama3.3:70b hedges 52.5%. Reading the hedged answers ("Billink minimum", "zondagbezorging", "KvK"), they state that the specific fact is missing and offer what the documents do say. For a customer that is an acceptable answer, and the deployment question is whether the fallback flow should catch these or not.

The "Verkopen jullie ook X?" failure from the pilot, where every model answered "Ja, ... atelier" to questions about washing machines and laptops, is gone after the assortment documents were added to the knowledge base before the study. These questions now sit in the answerable stratum as negative answers and are grounded in most conditions.

## What was not done

The prompt ablation (the original comparative wording against the illustrative wording) was not run, because the original wording was never committed and has not been reconstructed. The k = 4 threshold shift with the illustrative wording is the closest evidence that the backfire is a property of the extra documents and only partly of the wording.

The 100-answer hand-labelled sample for judge calibration was not produced.

fietje-2-chat could not run the k = 4 conditions: with Ollama's default context the runs crashed with CUDA "misaligned address" errors, traced to the model rambling past its 2048-token training window. Capping `num_ctx` at 2048 and `max_tokens` at 160 made k <= 2 viable at concurrency 1; eight documents plus output do not fit. Its rows are reported for completeness, and it is not a usable answer model for this task.

The suite is single-turn. During the 2026-09-16 demo, gemma3:12b answered a near-miss question ("hond") as the third turn of a conversation that it abstains on in a fresh session, because Rasa's prompt allows the conversation context as evidence. The abstention rates above are therefore an upper bound for multi-turn use.

The study covers one knowledge base and one domain. The pilot already showed the contrast effect changing sign when 23 documents were added, so the null result here should be read as "no consistent effect", with the k = 4 harm as the one direction that survived both knowledge bases.

## Conclusions

For the bot, the answer model is the lever and contrast documents are not. qwen3.5:27b at `k0` gives the best overall profile on this suite; gemma3:12b at `k0` remains a good choice on a 24 GB card, and its contrast setting should stay at zero. No condition should use k >= 3.

For the question raised in Yazan, Verberne and Situmeang (arXiv:2504.08745) whether contrastive examples help in RAG, this study says that, for the abstention decision in a small-model, retrieval-grounded setting, they act as additional context that lowers the model's threshold for answering. They do not sharpen the model's judgement of whether the relevant documents contain the answer. Any prompt design that adds documents, whatever their label, should expect more answers, and any evaluation of contrast examples should measure the out-of-scope and answerable strata alongside the target stratum, since the effect shows there first.

## Reproduction

```
venv\Scripts\python experiments\contrastive\collect.py   --results experiments\contrastive\results_study
venv\Scripts\python experiments\contrastive\aggregate.py --results experiments\contrastive\results_study --judge llama3.3-70b
venv\Scripts\python experiments\contrastive\aggregate.py --results experiments\contrastive\results_study --judge gpt-oss-20b
```

`results_study/answers.csv` holds every case result with the answer text, hedge flag, retrieval distances and document ids; `judged_<judge>.jsonl` holds the per-pair judge scores. The pilot summaries from 2026-09-14 are in `summary_2026-09-14_*.md` and are superseded by this study.

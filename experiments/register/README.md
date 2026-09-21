# Register matching: does the bot mirror u and je?

Started 2026-09-21. Register matching is the author-features half of the AP-Bots idea: a custom action classifies the customer's writing style as formal (*u*, *uw*) or informal (*je*, *jij*, *jullie*), stores it in the `klant_register` slot, and the enterprise-search prompt and the fixed responses follow it. The feature had been implemented since 2026-09-09 without any measurement. This directory holds two measurements: an offline pass over the answers logged by the contrastive study, and a small suite that has to be run against the bot.

## What the study answers can and cannot show

`analyze.py` reads `experiments/contrastive/results_study/answers.csv` (47,120 case results, 37,109 with an answer text), classifies each question with the bot's own rule (`detect_register` in `actions/actions.py`) and each answer by its second-person markers, and reports mirroring rates per model and condition in `summary.md`.

The first thing it found is that the 124-case suite contains no formal question at all. The study plan called for formal *u* paraphrases, but `build_suite.py` never produced any, and every question with *jullie* counts as informal under the action's rule. The study answers therefore only show the informal direction, which is also the knowledge base's own tone: every model except the two weakest Dutch ones answers informal questions informally in 100% of cases at k0, GEITje in 92.6% and fietje in 70%. Between 2% (llama3.3:70b) and 62% (fietje) of answers carry no second-person marker at all and are counted as neutral. That is a ceiling measurement, and it says nothing about whether the prompt instruction works.

## The register suite

`tests/test_register.yml` has 36 cases: 24 formal single-turn questions written as *u* paraphrases of answerable suite questions, 6 informal controls, 4 two-turn conversations that switch register or follow up without a marker, and 2 greetings. Each case asserts the slot value, that the answer contains no marker of the other register, and ends with a never-matching assertion so that Rasa records the transcript. `analyze.py --e2e <dir>` reads the transcripts and reports, per turn, the slot value and the register of the enterprise-search answer itself, which the Rasa assertions cannot isolate from the fixed follow-up utterances.

Run 2026-09-21 on gemma3:12b with the production endpoints (contrast k = 2, bottom) and again with the k0 endpoints, both after the study's knowledge base plus the koopavond document:

| | formal single-turn | informal single-turn | multi-turn formal turns | slot correct |
|---|---|---|---|---|
| default (contrast k2) | 21 of 21 marked answers formal, 2 neutral, 1 abstained | 6 of 6 informal | 4 of 4 formal, 1 neutral | 40 of 40 turns |
| k0 | 21 of 21 formal, 2 neutral, 1 abstained | 6 of 6 informal | 4 of 4 formal, 1 neutral | 40 of 40 turns |

Register mirroring works in both directions on this model. The slot is right on every turn, including the two switches (informal to formal and back) and the two marker-less follow-ups ("En op zondag?"), which keep the register of the earlier turn as designed. Every answer that carries a second-person marker carries the right one; the knowledge base is written in *je* throughout, so the formal answers are rewrites by the model, which is the property the prompt instruction was meant to buy. Contrast documents make no difference to it.

Three cases fail their Rasa assertions, none of them on register. "Heeft u ook een vestiging in Amsterdam?" abstains in both runs, with the correctly formal fallback response; the informal paraphrase of that question also abstained in most study runs, so this is the retrieval side. The two greeting cases ("Goedemiddag, kunt u mij helpen?", "Hoi! Kun je me helpen?") were routed to search instead of the greeting flow, and the answer model then produced a delivery-problem answer from the nearest document in both runs. The register of that answer was right; the answer itself was a false one on a message that contained no question. The greeting flow was written for bare greetings and should be widened, and the case is a useful addition to the near-miss stratum of a v2 suite.

## What is not covered

One answer model. The study data shows GEITje and fietje leaking *u* into informal answers, so the formal direction should be run on the other models before claiming the feature is model-independent; the suite takes about three minutes per model with `run_grid.py`'s endpoints files. The answer-register classifier is marker-based, so an answer that avoids the second person entirely counts as neutral rather than as a success or failure; the neutral share is reported for that reason. Nothing here judges whether the formal answers are also correct; that is the study's judge pipeline and can be run on these transcripts with `collect.py` if needed.

## Commands

```
venv\Scripts\python experiments\register\analyze.py                       # offline pass over the study answers
venv\Scripts\rasa test e2e tests\test_register.yml -o experiments\register\results\<run>
venv\Scripts\rasa test e2e tests\test_register.yml --endpoints experiments\contrastive\endpoints\endpoints_k0_gemma3-12b.yml -o experiments\register\results\<run>
venv\Scripts\python experiments\register\analyze.py --e2e experiments\register\results\<run> [...]
```

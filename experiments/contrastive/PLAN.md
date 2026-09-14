# Plan: full study of contrastive examples for abstention in RAG

Written 2026-09-14, after the pilot grid (gemma3:12b, 7 conditions, 4 repeats, 48 cases) and the gemma3:27b check. Nothing below has been run yet.

## 1. What the pilot showed and what the study has to settle

The pilot produced three observations. With two contrast documents, gemma3:12b answered fewer near-miss questions it should have declined (32.7% to 21.2%) and produced more grounded answers (63% to 75%). With four contrast documents, every selection mode made abstention worse than no contrast at all, and one case ("valt jullie kleding groot of klein") flipped from a stable abstention to a stable answer in all three k=4 modes. gemma3:27b without any contrast reached the same near-miss rate as the 12b with contrast, and contrast added nothing on top of it.

Each of these rests on a handful of cases. The near-miss stratum has 13 questions, so one case is 7.7 percentage points, and the 12b gain comes from three of them. The study therefore has to answer, with confidence intervals that make the differences meaningful: whether contrast helps at all and at which k; whether the k=4 harm is real and monotone; whether the effect depends on model size or family; and whether a cheaper baseline (fewer documents, or a similarity floor) achieves the same. It should also separate two kinds of "false answer" that the pilot lumped together: hedged answers that state the fact is missing, and answers that copy an unrelated document.

## 2. Suite

The suite grows from 48 to about 120 cases, keeping the three strata and the naming convention `A |`, `N |`, `O |`.

Answerable cases go from 27 to 54 by adding one further paraphrase per question, reusing the existing ground truths. Paraphrases change register and vocabulary (formal "u" versions, telegram-style questions, questions with a typo), since retrieval brittleness to wording was the original problem this prototype fought.

Near-miss cases go from 13 to about 40. Each new case names an in-domain topic whose specific fact is absent from `docs/`, verified by grep before it is added, and each category gets at least three. Six of them use the "Verkopen jullie ook X?" form with plausible products (jassen, riemen, sokken, kinderschoenen, tassen, ondergoed) so the yes-copy failure seen on the 27b is measured rather than anecdotal.

Out-of-scope cases go from 8 to 16.

The knowledge base stays frozen for the whole study. The missing assortment document (what the shop sells) is a real content gap and is noted for the De Rode Winkel contact, but adding it mid-study would change the near-miss stratum.

## 3. Outcomes and metrics

Every case yields one of five outcomes, the first three from deterministic assertions and the last two from the bot's answer text:

- abstained
- answered and grounded (judge score at or above 0.8)
- answered and ungrounded
- hedged: answered, but the text states that the information is not available (detected by a fixed Dutch phrase list, checked by hand on a sample)
- infra error

To classify hedged answers the answer text has to be available for every case, including passing ones. Rasa writes it to the log when `LOG_LEVEL_LLM_ENTERPRISE_SEARCH=DEBUG` is set; the driver sets that variable and the aggregator parses the log. This is verified on one run before the study starts.

The primary metrics are the near-miss false-answer rate (answered, hedged excluded and reported separately) and the answerable false-abstain rate. Secondary metrics are the out-of-scope false-answer rate, the grounded rate on answerable cases, and the judge's mean score. Each case's outcome per condition is the majority over repeats; rates are computed over cases, with bootstrap confidence intervals over cases; differences against the no-contrast baseline of the same model are tested with McNemar's test on the paired per-case majorities.

## 4. Conditions

Contrast conditions are contrast_k in {0, 1, 2, 3, 4} crossed with mode in {bottom, random, next}, which is 13 conditions after merging the three k=0 variants. The k=1 and k=3 points exist to locate where the curve turns.

Two baselines answer the "is there a cheaper way" question. The first passes two documents instead of four with no contrast (`top_k: 2`, a new retriever option). The second is a similarity floor, computed offline: the retriever logs the FAISS score of every returned document, and the aggregator reports how well "abstain when the top score is below a threshold" would have done, sweeping the threshold. That baseline costs no runs.

The prompt ablation replays the backfire from 2026-09-09: the original comparative instruction ("abstain if the relevant documents are not clearly better than the contrast documents") against the current illustrative wording, on gemma3:12b for bottom_k2, next_k2 and bottom_k4. Prompt changes are baked into the model at training time, so this needs one extra trained model and a `--model` flag in the driver. The original wording is not in git history (the contrast section of the prompt has never been committed), so it has to come from Mert's notes or be reconstructed from the description in the 2026-09-09 finding; Mert should confirm the reconstruction before the ablation runs.

## 5. Models

Answer models: gemma3:4b, gemma3:12b and gemma3:27b for the size axis within one family, and qwen3.5:9b and qwen3.5:27b as a second family. The qwen models need a check that thinking mode can be disabled through Rasa's Ollama provider; if it cannot, mistral-small3.2 cannot substitute because it is the judge, and the second family is dropped rather than confounded.

The judge stays mistral-small3.2 at temperature 0 for every run. Judge validity is reported separately: all logged answers are re-scored by a second judge from a third family (gemma4:31b, accepting its slower thinking output for this offline pass), and a random sample of 100 answerable-case answers is labelled by hand, giving agreement figures for both judges.

The command generator stays gemma3:4b and the embeddings stay bge-m3 throughout.

## 6. Repeats

Five repeats per condition. The pilot showed that at temperature 0 the answer/abstain decision flips within a condition on only one to four cases out of 48, so repeats are not where the uncertainty lives; cases are. Five rather than four gives an odd count for the majority vote and one more sample for the judge column, which flips on six to eleven cases per condition. Spending the budget on cases and conditions rather than on a sixth repeat is the better trade.

## 7. Budget

Run lengths scale with the suite (about 2.5 times the pilot). Effective wall time per run at four concurrent processes, from today's measurements, is roughly 2.5 min for the 12b, 2 min for the 4b, 3.5 min for the 27b models, and about 2.3 min for qwen3.5:9b.

The full 13-condition contrast sweep plus the top-k baseline runs on gemma3:12b only (14 conditions, 70 runs, about 3 h). The other four models get contrast_k in {0, 2, 4} for all three modes plus the top-k baseline (8 conditions, 40 runs each): about 1.3 h for the 4b, 1.5 h for qwen 9b, 2.3 h for each 27b. The prompt ablation adds 15 runs on the 12b, about 40 min.

That is roughly 11 h of wall time, one night, launched grouped by model so that each model's block is complete and usable on its own if the night is cut short. The second-judge pass runs the next morning, offline, on the logged answers.

VRAM works because only one answer model is loaded at a time: gemma3:4b plus bge-m3 plus the judge plus the answer model peaks at about 43 GB with the 27b models.

## 7a. Status 2026-09-14 evening: what is built

The pieces below exist and have been checked on a calibration run; the study itself has not been launched.

- `build_suite.py` generates `tests/test_contrastive_suite.yml` (124 cases: 68 answerable as 34 questions with two paraphrases each, 40 near-miss with grep-verified absent keywords, 16 out-of-scope) and `ground_truth.yml`. The judge assertion is gone from the suite; a final `bot_uttered` assertion with a never-matching regex makes Rasa write the transcript for every case, which is where the answer text comes from.
- `addons/contrastive_retriever.py` has `top_k`, and logs the L2 distances of the retrieved and contrast documents.
- `run_grid.py` has 14 conditions (k in 0..4 for three modes, plus `topk2`), condition sets (`full`, `core`, `pilot`, `reference`), `--answer-model` with per-model extras (`reasoning_effort: none` switches Qwen thinking off through LiteLLM), `--model` for prompt ablations, and a knowledge-base fingerprint in every run's metadata.
- `run_study.py` runs the phases in order, one answer model at a time, into `results_study/<model>/`: gemma3 12b (full, 70 runs), then gemma3 4b and 27b, qwen3.5 9b and 27b, mistral-small3.2, GEITje-7B-ultra, fietje-2-chat, EuroLLM-9B (core, 40 runs each), and llama3.3:70b as k0-only reference at concurrency 1. All three Dutch models are pulled from Hugging Face GGUFs and answer in Dutch through Ollama.
- `collect.py` turns results into `answers.csv` (outcome, answer text, hedged flag from a Dutch phrase list, retrieval distances, ground truth).
- `judge.py` scores unique (ground truth, answer) pairs offline with any Ollama model using Rasa's groundedness template, resumable per judge. The intended primary judge is llama3.3:70b over everything, with gpt-oss:20b as the agreement check and 100 hand labels.
- `aggregate.py` reports per model and condition: false-abstain, hedged, grounded, near-miss and out-of-scope false-answer rates with bootstrap confidence intervals over cases, McNemar against k0, a similarity-floor baseline from the logged distances, per-case flap tables, and judge agreement.

Timing from the calibration: about 3 s per case without the inline judge, so a 124-case run takes 6 to 7 minutes single-process. The full study is 440 runs; at four concurrent that is roughly 10 h for the small and mid-size models plus the 70b reference, so one long night, and the offline judging is a second night.

## 7b. How to launch

From the project root in a terminal that outlives the session (IntelliJ terminal or tmux), with the tunnel to limmy open:

```
venv\Scripts\python experiments\contrastive\run_study.py --list          # phases and run counts
venv\Scripts\python experiments\contrastive\run_study.py                 # everything, ~10 h
venv\Scripts\python experiments\contrastive\run_study.py --phases 12b    # one phase
```

The study is resumable: rerunning the same command skips finished runs. Optional speed-up before launching: set `OLLAMA_NUM_PARALLEL=8` in the Ollama override on limmy (restart required) and pass `--concurrency 6` to `run_grid.py` calls, or edit the concurrency column in `run_study.py`.

Afterwards, with the GPUs free:

```
venv\Scripts\python experiments\contrastive\collect.py --results experiments\contrastive\results_study
venv\Scripts\python experiments\contrastive\judge.py --answers experiments\contrastive\results_study\answers.csv --judge llama3.3:70b --parallel 4
venv\Scripts\python experiments\contrastive\judge.py --answers experiments\contrastive\results_study\answers.csv --judge gpt-oss:20b --parallel 4
venv\Scripts\python experiments\contrastive\aggregate.py --results experiments\contrastive\results_study --judge llama3.3-70b
```

The judge is resumable per judge file; `--sample N` restricts a judge to a random subset for agreement checks.

## 7c. Morning checklist (after an overnight run)

1. Tunnel up: `curl -s http://localhost:11434/api/tags | head -c 60` prints JSON. If not: `ssh -fNL 11434:localhost:11434 limmy` in WSL.
2. `venv\Scripts\python experiments\contrastive\status.py` shows every phase with runs done, internal-error counts, and a NEXT line. Green state: all phases at their expected counts, zero internal errors, "Generation is COMPLETE".
3. If runs are missing, relaunch `run_study.py`; it skips finished runs. If a run has internal errors, delete that run's directory and relaunch; the tunnel dropping is the usual cause.
4. When generation is complete and nobody else needs the GPUs: `venv\Scripts\python experiments\contrastive\run_judging.py`. It collects answers, judges with llama3.3:70b (about 20 s per unique answer, both cards), then gpt-oss:20b, then writes `results_study/summary.md`. Interruptible; rerun resumes.
5. Read `results_study/summary.md`. Judge agreement is at the bottom.

## 8. Order of work

1. Suite expansion: paraphrases, near-miss cases with grep verification, out-of-scope cases. Reviewed by a person before the run, since the near-miss ground truth is a human judgement.
2. Retriever: `top_k` option, per-document score logging, and the answer-text logging check with `LOG_LEVEL_LLM_ENTERPRISE_SEARCH`.
3. Driver: `--model` for the prompt ablation, `--top-k`, model grouping, and the environment variable.
4. Aggregator: hedged detection, per-case majority, bootstrap CIs, McNemar, similarity-floor sweep, per-model tables.
5. Probes: qwen3.5 thinking off through Rasa; one calibration run of the 120-case suite on the 12b to confirm timing and log parsing.
6. Retrain one model with the comparative prompt.
7. Launch in the evening, grouped by model, 12b first.
8. Morning: second-judge pass, hand-labelling sample, write-up tables.

## 9. Open decisions

- Whether both qwen models are worth the 4 h they cost, or one is enough for the family contrast.
- Whether the prompt ablation should also run on the 4b, where the backfire may be larger.
- Who labels the 100-answer sample.

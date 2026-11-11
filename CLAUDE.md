# prototypeDRW: orientation for Claude Code

This file is loaded at the start of every session in this repository. It points to where the context lives and records the conventions that are easy to get wrong. Machine-specific notes (tunnels, hosts, model server settings) live in `NOTES.local.md`, which is gitignored, and in Claude's per-machine memory outside the repo.

## What this project is

A Rasa CALM assistant for De Rode Winkel, a clothing retailer in Utrecht, used as a research testbed on real Dutch customer language. The shop is a case study and data partner, and De Rode Winkel is not a client. The knowledge base (`docs/`, 97 Q&A files in 13 categories) was distilled from 2,112 WhatsApp conversations that were pseudonymized with discombobulator, extracted one Q&A per conversation with llama3.3:70b under ten fixed categories, clustered on embeddings, and synthesized to one archetype per cluster. Everything is open source under the LESSEN project. `README.md` has the architecture and setup.

## The research lines

Contrastive examples for abstention in RAG (finished, null result). Design in `experiments/contrastive/PLAN.md`, results in `experiments/contrastive/RESULTS.md`. Ten answer models, 380 runs on the 124-case suite `tests/test_contrastive_suite.yml` (68 answerable, 40 near-miss, 16 out-of-scope). Contrast documents shift the answer/abstain threshold toward answering on every stratum and do not lower the near-miss false-answer rate for any model. The answer model is the lever. The paper behind the idea is Yazan, Verberne and Situmeang, ECIR 2025, doi:10.1007/978-3-031-88714-7_40.

Knowledge graph as knowledge base (paused on 2026-11-11 in a documented state). `experiments/kg/README.md` is the design document: schema, open/closed world rationale, completeFor, the ten query templates in `query.py`, coverage of the suite in `coverage.md`, the graph-first-retrieval-fallback design, the graph in the bot, and the section "Where the line stopped" with the plans that were discussed and not carried out. 63 of 97 documents are converted by hand (`data/`); 24 of them carry the FAQ answer verbatim as a `drw:howTo` literal that the bot utters as is. Verdicts are entailed, contradicted or unknown; a "nee" needs a completeFor assertion or an explicit negative. The bot answers nine question shapes from the graph through the `kg_` flows in `data/flows.yml` and the actions in `actions/kg_actions.py`, with `experiments/kg/link.py` for entity linking, and falls through to retrieval on unknown. `tests/test_kg_flows.yml` stands at 33 of 35 and `tests/test_retrieval_stress.yml` at 13 of 15; the four failures are marked KNOWN FAILURE in the files and are command-generator routing errors. The suite mapping in `suite_map.yml`, `coverage.py`, `demo.py` and `kg_web.py` still use the hand mapping.

Interrogative agenda (started 2026-11-11, on hold until the source paper is available). The bot asks clarifying questions before it chooses a flow: a process takes probabilities over the flows, treats them as Dempster-Shafer mass functions, and through a series of questions either outputs a flow or restates the question and asks the customer to rephrase. `experiments/interrogative_agenda/README.md` is the design note, with a small tested Dempster-Shafer module (`ds.py`) and a toy example. The method description in that README is provisional, and no further code is to be written on this line before the paper has been read.

## Conventions

- All customer-facing text is Dutch. The answer prompt hard-codes Dutch output and mirrors the customer's register (u or je).
- Prompt, domain and config changes are bundled at train time: run `rasa train` after editing anything under `prompts/`, `domain.yml`, `config.yml` or `data/`. Retriever settings in the `vector_store` block of `endpoints.yml` are read at runtime.
- `docs/` holds one Q&A per file on purpose (Rasa chunks at 1,000 characters). Edit the per-category sources in `docs_source/` and regenerate with `scripts/split_docs.py`, or edit `docs/` directly for a single file.
- Ollama model groups need an explicit `num_ctx`; the models are gemma3:4b (commands), gemma3:12b (answers), bge-m3 (embeddings), mistral-small3.2 (e2e judge). The value is 4096 everywhere except the command model group, which runs at 6144 since 2026-11-10: the command prompt with nine graph flows renders to about 2,500 tokens and gemma3:4b degenerates on it at 4096. Recheck that value when the command prompt grows.
- The command prompt in `prompts/command_generator.jinja2` lists the flows by hand and `flow_retrieval` is off, so a new flow needs a description line, examples and possibly boundary rules there. Run both `tests/test_kg_flows.yml` and the stress suite after any change to it.
- Keep `contrast_k: 0` for the bot unless running the contrastive study; RESULTS.md recommends it.
- Run `rasa test e2e tests/test_retrieval_stress.yml` after changing the embedding model, the document layout, the prompts or the Rasa version.
- Spelling in documents and slides is American.

## The 2026-09-29 talk

`experiments/talk_2026-09-29_15min.md` is the timed plan and `experiments/demo_2026-09-29_outline.md` the detailed backing with commands and fallbacks. The demo is two browser tabs and a terminal: `rasa inspect` for the bot, `experiments/kg/kg_web.py` on http://127.0.0.1:8765 for the graph (only the prepared questions in `demo.py` are accepted), and the conflict check `build.py --no-write --extra-data tests/conflict_after_closure.ttl`. Ask both systems "Verkopen jullie wasmachines?" and "Kan ik in termijnen betalen?".

## Next steps on the graph line

The line is paused. `experiments/kg/README.md` has the full list and the reasoning; in short:

1. A held-out routing set from the pseudonymized WhatsApp conversations, labeled by a person, to measure routing and linking and the rate of confident answers to the wrong question. The data stays on the project's server, and the README states the privacy rules.
2. The 124-case suite through the bot, graph first against retrieval only, with the same answer model and judge.
3. A single `kg` flow with template selection in code, and a router ablation with a larger command model.
4. LLM extraction of the remaining 34 documents constrained to the schema and validated with SHACL, measured against the hand-converted files; completeness assertions reviewed by a person.
5. A rephraser for the verbatim answers as a switch, and a v2 suite with compositional and negative questions, versioned apart from the 2026-09-14 suite.

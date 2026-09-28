# prototypeDRW: orientation for Claude Code

This file is loaded at the start of every session in this repository. It points to where the context lives and records the conventions that are easy to get wrong. Machine-specific notes (tunnels, hosts, model server settings) live in `NOTES.local.md`, which is gitignored, and in Claude's per-machine memory outside the repo.

## What this project is

A Rasa CALM assistant for De Rode Winkel, a clothing retailer in Utrecht, used as a research testbed on real Dutch customer language. The shop is a case study and data partner, and De Rode Winkel is not a client. The knowledge base (`docs/`, 97 Q&A files in 13 categories) was distilled from 2,112 WhatsApp conversations that were pseudonymized with discombobulator, extracted one Q&A per conversation with llama3.3:70b under ten fixed categories, clustered on embeddings, and synthesized to one archetype per cluster. Everything is open source under the LESSEN project. `README.md` has the architecture and setup.

## The two research lines

Contrastive examples for abstention in RAG (finished, null result). Design in `experiments/contrastive/PLAN.md`, results in `experiments/contrastive/RESULTS.md`. Ten answer models, 380 runs on the 124-case suite `tests/test_contrastive_suite.yml` (68 answerable, 40 near-miss, 16 out-of-scope). Contrast documents shift the answer/abstain threshold toward answering on every stratum and do not lower the near-miss false-answer rate for any model. The answer model is the lever. The paper behind the idea is Yazan, Verberne and Situmeang, ECIR 2025, doi:10.1007/978-3-031-88714-7_40.

Knowledge graph as knowledge base (in progress). `experiments/kg/README.md` is the design document: schema, open/closed world rationale, completeFor, the nine query templates in `query.py`, coverage of the suite in `coverage.md`, the graph-first-retrieval-fallback design, and next steps. 39 of 97 documents are converted by hand (`data/`), and the mapping from suite question to template is by hand in `suite_map.yml` because entity linking and routing are next step one. Verdicts are entailed, contradicted or unknown; a "nee" needs a completeFor assertion or an explicit negative.

## Conventions

- All customer-facing text is Dutch. The answer prompt hard-codes Dutch output and mirrors the customer's register (u or je).
- Prompt, domain and config changes are bundled at train time: run `rasa train` after editing anything under `prompts/`, `domain.yml`, `config.yml` or `data/`. Retriever settings in the `vector_store` block of `endpoints.yml` are read at runtime.
- `docs/` holds one Q&A per file on purpose (Rasa chunks at 1,000 characters). Edit the per-category sources in `docs_source/` and regenerate with `scripts/split_docs.py`, or edit `docs/` directly for a single file.
- Ollama model groups need `num_ctx: 4096`; the models are gemma3:4b (commands), gemma3:12b (answers), bge-m3 (embeddings), mistral-small3.2 (e2e judge).
- Keep `contrast_k: 0` for the bot unless running the contrastive study; RESULTS.md recommends it.
- Run `rasa test e2e tests/test_retrieval_stress.yml` after changing the embedding model, the document layout, the prompts or the Rasa version.
- Spelling in documents and slides is American.

## The 2026-09-29 talk

`experiments/talk_2026-09-29_15min.md` is the timed plan and `experiments/demo_2026-09-29_outline.md` the detailed backing with commands and fallbacks. The demo is two browser tabs and a terminal: `rasa inspect` for the bot, `experiments/kg/kg_web.py` on http://127.0.0.1:8765 for the graph (only the prepared questions in `demo.py` are accepted), and the conflict check `build.py --no-write --extra-data tests/conflict_after_closure.ttl`. Ask both systems "Verkopen jullie wasmachines?" and "Kan ik in termijnen betalen?".

## Next steps on the graph line

1. Entity linking and template routing from the question text with the labels in `vocab.ttl`, reported separately from graph coverage.
2. LLM extraction of the remaining 58 documents constrained to the schema and validated with SHACL, measured against the hand-converted files; completeness assertions reviewed by a person.
3. A verbalizer and a custom retriever that runs the templates and falls through to retrieval on unknown, so the answer prompt, suite runner and judge stay unchanged.
4. A v2 suite with compositional and negative questions, versioned apart from the 2026-09-14 suite.

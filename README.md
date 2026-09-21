# prototypeDRW — Dutch retail assistant on self-hosted LLMs

A Dutch-language customer service assistant for [De Rode Winkel](https://www.derodewinkel.nl/), a family-owned clothing retailer in Utrecht founded in 1837. It is built on [Rasa CALM](https://rasa.com/docs/learn/concepts/calm/) with retrieval-augmented generation over a curated knowledge base, and every model it uses runs on our own hardware through [Ollama](https://ollama.com/).

The assistant answers questions about products, returns, shipping, sizing, payments, gift cards, loyalty points, repairs and the physical store. It answers in Dutch, grounds every answer in the knowledge base, mirrors the customer's register (*u* or *je*), and says so when the knowledge base has no answer.

## Purpose

The prototype is a research testbed. It lets us test retrieval and knowledge-base techniques on real customer language in Dutch, a setting for which good conversational data is scarce. The knowledge base was distilled from anonymised WhatsApp conversations that De Rode Winkel made available for research, which makes the shop our case study and data partner. Two research lines currently use the testbed: contrastive examples for abstention in retrieval-augmented generation, and knowledge graphs as a knowledge base with formal reasoning. Both ask how a technique from the literature behaves on realistic data. The code, the test suite and the study tooling are open source, developed within the LESSEN project. A company that wants to run an assistant like this for real customers can use the repository as a starting point and build, host and maintain it as a product.

## Architecture

```
User message
    │
    ▼
SearchReadyLLMCommandGenerator ── gemma3:4b ──► "start flow begroeting" | "search and reply"
    │
    ├── begroeting ──► utter_begroeting (introduction, what the assistant can help with)
    │
    └── pattern_search
            │
            ├── action_detect_register ──► klant_register slot (formeel/informeel)
            │
            └──► EnterpriseSearchPolicy
                     │
                     ├── embed the user message ── bge-m3 ──► ContrastiveFAISS (97 Q&A docs)
                     │                                          │
                     │                                          └──► top-4 relevant + 2 contrast docs
                     │
                     └── write the answer ── gemma3:12b ──► Dutch response in the customer's register,
                                                            or [NO_RAG_ANSWER] when the documents lack the answer
```

Two design choices carry most of the retrieval quality. Command generation is a small, frequent task and runs on gemma3:4b, while answer writing runs on gemma3:12b; Rasa `model_groups` route each component to its own model, and both fit together on a single 24 GB GPU. Each question in the knowledge base lives in its own file, because Rasa chunks documents at 1000 characters and a file with several questions yields one diluted vector; one question per file gives every question a focused embedding, which together with the multilingual bge-m3 model makes retrieval robust to colloquial rewordings ("m'n rits is kapot" finds the repair atelier document).

Only the user's own message is embedded for retrieval (`max_messages_in_query: 1`). The full conversation still reaches the answer prompt, so follow-up questions keep their context.

## Research features

Two features are adapted from [Yazan, Verberne & Situmeang, *Improving RAG for Personalization with Author Features and Contrastive Examples*](https://arxiv.org/abs/2504.08745) ([AP-Bots](https://github.com/myazann/AP-Bots)). A third replaces the text knowledge base with a knowledge graph.

**Register matching (author features).** A custom action in `actions/actions.py` classifies the customer's writing style as formal (*u/uw*) or informal (*je/jij*) from Dutch register markers and stores it in a slot. The latest message decides whenever it carries a marker, so a customer who switches to *u* is answered with *u* from then on. The enterprise search prompt instructs the model to mirror that register, and the fixed template responses switch through conditional response variations. `experiments/register/` measures it: on gemma3:12b every answer with a second-person marker follows the customer's register, in both directions and across register switches within a conversation, with or without contrast documents; the knowledge base is written in *je*, so the formal answers are rewrites by the model. The 124-case study suite turned out to contain no formal questions, so the formal direction has its own suite, `tests/test_register.yml`.

**Contrastive documents (contrastive examples).** A custom retriever in `addons/contrastive_retriever.py` returns the top-k relevant documents plus `contrast_k` additional documents labelled as contrast, chosen by `contrast_mode`: the least similar documents (`bottom`), random documents (`random`), or the documents ranked just below the relevant ones (`next`). The prompt presents the contrast documents as illustrations of irrelevance and keeps the bar for answering absolute: a relevant document must contain the specific answer, otherwise the model abstains with `[NO_RAG_ANSWER]`. An earlier comparative wording ("abstain if the relevant documents are no better than the contrast documents") weakened abstention, because next to the least similar documents everything looks relevant. All settings live in the `vector_store` block of `endpoints.yml`; `contrast_k: 0` gives the plain retrieval baseline. Whether and when contrast documents help is the subject of the study in `experiments/contrastive/`; the results are in `experiments/contrastive/RESULTS.md`.

**Knowledge graph as knowledge base.** `experiments/kg/` converts the Q&A documents into an RDF graph and answers questions from it with a three-valued outcome decided before any text is generated: entailed, contradicted, or unknown. A hand-written OWL schema (`schema.ttl`) carries the reasoning in property chains, so that "we sell jeans" entails "we sell trousers", "we repair clothing" reaches a customer's Levi's through the category tree, and "we ship to Europe" covers Antwerp. A `completeFor` assertion on a (subject, property) pair switches that pair to closed-world, which is what turns an empty result into a grounded "nee" instead of "geen informatie"; exceptions such as repairing Nudie jeans bought elsewhere are explicit rule nodes. Each converted document lives in its own named graph, the OWL RL closure goes into a separate inferred graph, and every verdict cites the triples and documents it rests on. `build.py` validates in two SHACL passes (asserted data, then the closure) plus a completeness check across documents, so contradictions between documents are reported with both sources. The research question is how much of this conversion can be automated; the hand-converted documents are the gold standard the extraction step will be measured against. `experiments/kg/README.md` has the design, the coverage of the study suite, and the next steps.

## Knowledge base

`docs/` holds 97 Dutch question-and-answer files in 13 categories. They were distilled from 2,112 customer WhatsApp conversations. The raw chat logs were first pseudonymised with [discombobulator](https://github.com/Jurian/discombobulator), a rule-based toolkit that parses chat logs and replaces names, e-mail addresses, phone numbers, addresses and tracking codes with placeholders, so the extraction pipeline only ever saw cleaned text. The pipeline in `scripts/` then extracted one question and answer per conversation with an LLM constrained to a fixed category list, clustered the results on embeddings, and synthesised one archetype Q&A per cluster. The assortment category was written afterwards to cover "verkopen jullie ook …?" questions. The pre-split source files live in `docs_source/`, and `scripts/split_docs.py` regenerates the per-question layout.

The retriever rebuilds its index from `docs/` on every request, so a new or edited file takes effect immediately. Prompt, domain and config changes require a retrain.

## Setup

Requirements: Python 3.10 to 3.13, a [Rasa Pro license](https://rasa.com/docs/rasa-pro/installation/python/licensing), and an Ollama server, local or remote, with these models pulled:

```bash
ollama pull gemma3:4b            # command generation
ollama pull gemma3:12b           # answer generation
ollama pull bge-m3               # embeddings
ollama pull mistral-small3.2     # LLM judge for the e2e tests (conftest.yml)
```

```bash
python -m venv venv
venv/Scripts/activate            # Windows; use venv/bin/activate on Linux/macOS
pip install rasa-pro
```

The configuration expects Ollama at `http://localhost:11434`. When Ollama runs on a remote GPU host, open an SSH tunnel with a keepalive, since NAT idle timeouts otherwise drop the tunnel silently and every LLM call fails:

```bash
ssh -o ServerAliveInterval=60 -L 11434:localhost:11434 <gpu-host> -N
```

## Train and run

```bash
rasa train          # bundles prompts, domain and config into a model
rasa inspect        # chat with the assistant in the browser
```

## Tests and study tooling

`tests/test_retrieval_stress.yml` is a 15-case retrieval stress test. Every query is worded differently from the knowledge base text, with synonyms and colloquial Dutch, to check that retrieval works on meaning, and it includes abstention checks for out-of-scope questions. Answers are scored for groundedness by a local LLM judge configured in `conftest.yml`.

```bash
rasa test e2e tests/test_retrieval_stress.yml
```

`tests/test_contrastive_suite.yml` is the 124-case suite for the contrastive-examples study, with answerable, near-miss and out-of-scope strata. `experiments/contrastive/` contains the study tooling: `run_study.py` runs all conditions across several answer models, `collect.py` gathers the answers, `judge.py` scores them offline with a judge model, and `aggregate.py` produces the summary with confidence intervals. `experiments/contrastive/PLAN.md` describes the design and `experiments/contrastive/RESULTS.md` reports the results: contrast documents shift the answer/abstain threshold towards answering and do not reduce false answers on near-miss questions; the answer model is the lever.

Run the stress test after any change to the embedding model, the document layout, the prompts or the Rasa version.

## Project layout

```
config.yml                  # pipeline: command generator + FlowPolicy + EnterpriseSearchPolicy
endpoints.yml               # Ollama model groups + contrastive retriever settings
domain.yml                  # Dutch responses (register-conditional), slots
data/flows.yml              # greeting flow
data/patterns.yml           # Dutch overrides for cancel/completed/search patterns
prompts/                    # custom Jinja2 prompts (command generator, enterprise search)
actions/                    # custom actions: register (u/je) detection
addons/                     # custom contrastive FAISS retriever
docs/                       # knowledge base: 97 Dutch Q&A files, 13 categories
docs_source/                # original per-category files (kept out of the index)
scripts/                    # WhatsApp extraction pipeline + docs splitter
tests/                      # retrieval stress test, the 124-case study suite, the register suite
experiments/contrastive/    # contrastive-examples study: driver, offline judge, aggregation, RESULTS.md
experiments/kg/             # knowledge graph: schema, vocabulary, hand-converted documents, build + queries
experiments/register/       # register matching: offline analysis of the study answers + the register suite
conftest.yml                # LLM judge config for e2e tests
```

# prototypeDRW — Dutch retail assistant on self-hosted LLMs

Dutch-language customer service assistant for [De Rode Winkel](https://www.derodewinkel.nl/), a family-owned clothing retailer in Utrecht (est. 1837). Built as a demo of [Rasa CALM](https://rasa.com/docs/learn/concepts/calm/) with retrieval-augmented generation over a curated knowledge base, running **entirely on self-hosted open models** via [Ollama](https://ollama.com/) — no cloud LLM APIs involved.

The assistant answers customer questions about products, returns, shipping, sizing advice, payments, gift cards, loyalty points, repairs, and the physical store — in Dutch, grounded in the knowledge base, and abstaining when it doesn't know the answer.

## Architecture

```
User message
    │
    ▼
SearchReadyLLMCommandGenerator ── gemma3:4b ──► "search and reply"
    │
    ▼
pattern_search
    │
    ├── action_detect_register ──► klant_register slot (formeel/informeel)
    │
    └──► EnterpriseSearchPolicy
             │
             ├── embed query ── bge-m3 ──► ContrastiveFAISS (73 Q&A docs)
             │                                │
             │                                └──► top-4 relevant + 2 contrast docs
             │
             └── generate answer ── gemma3:12b ──► Dutch response, matching register
                  (check_relevancy: abstains when relevant docs don't beat contrast docs)
```

Two things worth noting in the design:

- **Per-component model routing** via Rasa `model_groups`: the high-frequency, trivial task (command generation) runs on a small fast model (gemma3:4b), while answer writing gets a stronger one (gemma3:12b). Both fit together on a single 24 GB GPU.
- **One Q&A per document**: Rasa's FAISS ingestion chunks files at 1000 characters, which merges unrelated Q&As into diluted vectors. Keeping each Q&A in its own file gives every question a focused embedding — this, plus the multilingual bge-m3 embedding model, is what makes retrieval robust to colloquial rewordings ("m'n rits is kapot" finds the repair atelier doc).

## Personalization features (AP-Bots)

Two features adapted from [Yazan, Verberne & Situmeang, *Improving RAG for Personalization with Author Features and Contrastive Examples*](https://arxiv.org/abs/2504.08745) ([AP-Bots](https://github.com/myazann/AP-Bots)), developed within the LESSEN project:

- **Register matching (author features).** A custom action (`actions/actions.py`) classifies each customer's writing style as formal (*u/uw*) or informal (*je/jij*) by counting Dutch register markers across their messages, and stores it in a slot. The enterprise search prompt instructs the LLM to mirror that register, and fixed template responses switch via conditional response variations — so a customer who writes "Kunt u mij helpen?" gets consistent *u* throughout, while "Hoi, kun je me helpen?" gets *je*.
- **Contrastive documents (contrastive examples).** A custom information retriever (`addons/contrastive_retriever.py`) returns the top-4 relevant documents *plus* the 2 least similar documents in the knowledge base, labeled as contrast. The prompt tells the model: if the relevant documents don't answer the question meaningfully better than the contrast documents, abstain (`[NO_RAG_ANSWER]`). This turns the abstention decision from an absolute confidence judgment (which LLMs do poorly) into a relative comparison (which they do well) — applying the paper's contrastive-examples idea to relevancy calibration, a direction its authors flag as open research. Tune via `contrast_k` in `endpoints.yml`; set it to `0` for an ablation baseline.

### Knowledge base

`docs/` holds 72 Dutch Q&A files in 12 categories, distilled from anonymized customer WhatsApp conversations. The raw chat logs were first pseudonymized with [discombobulator](https://github.com/Jurian/discombobulator), a rule-based toolkit that parses chat logs and replaces personal data (names, emails, phone numbers, addresses, tracking codes) with placeholders — so no personal data ever enters the pipeline. The cleaned conversations were then processed by the extraction pipeline in `scripts/` (LLM extraction into fixed categories → embedding-based clustering → LLM synthesis of archetype Q&As). The pre-split source files live in `docs_source/`; `scripts/split_docs.py` regenerates the per-Q&A layout.

## Setup

Requirements: Python 3.10–3.13, a [Rasa Pro license](https://rasa.com/docs/rasa-pro/installation/python/licensing), and an Ollama server (local or remote) with these models pulled:

```bash
ollama pull gemma3:4b       # command generation
ollama pull gemma3:12b      # answer generation + LLM judge for tests
ollama pull bge-m3          # embeddings
```

```bash
python -m venv venv
venv/Scripts/activate       # Windows; use venv/bin/activate on Linux/macOS
pip install rasa-pro
```

The config expects Ollama at `http://localhost:11434`. If Ollama runs on a remote GPU host, open an SSH tunnel and keep it alive:

```bash
ssh -o ServerAliveInterval=60 -L 11434:localhost:11434 <gpu-host> -N
```

(Without the keepalive, NAT idle timeouts silently drop the tunnel and every LLM call fails.)

## Train and run

```bash
rasa train          # builds the model + FAISS index (embeds all docs)
rasa inspect        # chat with the assistant in the browser
```

## Tests

`tests/test_retrieval_stress.yml` is a 15-case retrieval stress test: every query is deliberately worded differently from the knowledge base text (synonyms, colloquial Dutch) to verify retrieval works on meaning rather than vocabulary, plus abstention checks for out-of-scope questions. Answers are scored for groundedness by a local LLM judge (configured in `conftest.yml` — same Ollama models, no cloud calls).

```bash
rasa test e2e tests/test_retrieval_stress.yml
```

Run this after any change to the embedding model, docs structure, prompts, or Rasa version to catch retrieval regressions.

## Project layout

```
config.yml                  # pipeline: command generator + FlowPolicy + EnterpriseSearchPolicy
endpoints.yml               # Ollama model groups + contrastive retriever settings
domain.yml                  # Dutch responses (register-conditional), klant_register slot
data/patterns.yml           # Dutch overrides for cancel/completed/search patterns
prompts/                    # custom Jinja2 prompts (command generator, enterprise search)
actions/                    # custom actions: register (u/je) detection
addons/                     # custom contrastive FAISS retriever
docs/                       # knowledge base: 73 Dutch Q&A files, 12 categories
docs_source/                # original per-category files (not indexed)
scripts/                    # WhatsApp extraction pipeline + docs splitter
tests/                      # retrieval stress-test suite
conftest.yml                # LLM judge config for e2e tests
```

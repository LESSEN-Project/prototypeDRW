"""
Clusters extracted Q&As by embedding similarity and creates one archetype per cluster.

Steps:
  1. Embed all questions per category using nomic-embed-text
  2. Run hierarchical clustering (agglomerative, average linkage, cosine distance)
  3. For each cluster, either:
     a. Pick the most central Q&A as archetype (default, fast)
     b. Ask an LLM to synthesize the best combined Q&A (--synthesize, slower)
  4. Print a cluster report so you can inspect groupings and tune --threshold
  5. Write one Q&A per cluster to output docs

Usage:
    python cluster_knowledge.py --input docs_mistral/ --output docs_clustered
    python cluster_knowledge.py --input docs_llama/ --output docs_clustered --threshold 0.15 --synthesize

Requires: scipy  (pip install scipy)
Runs on limmy (direct Ollama access).
"""

import argparse
import math
import os
import requests
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_LLM_MODEL = "mistral-small3.2:latest"
DEFAULT_THRESHOLD = 0.12  # cosine distance; lower = stricter (fewer, larger clusters)

SYNTHESIS_PROMPT = """Je hebt de volgende vergelijkbare vragen en antwoorden uit een FAQ-kennisbank van De Rode Winkel.

{qa_list}

Schrijf één gecombineerde vraag en één gecombineerd antwoord dat alle nuttige informatie bevat.
Antwoord EXACT in dit formaat (niets anders):
VRAAG: [de beste generieke vraag die een klant zou stellen]
ANTWOORD: [het meest volledige en nuttige antwoord, zonder klantnamen of besteldetails]"""


# ── Ollama calls ──────────────────────────────────────────────────────────────

def get_embedding(text, model):
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": model, "prompt": text},
        timeout=30,
    )
    if response.status_code == 200:
        return response.json()["embedding"]
    raise RuntimeError(f"Embedding failed ({response.status_code}): {response.text}")


def synthesize(cluster_items, llm_model, debug=False):
    qa_list = "\n\n".join(
        f"Vraag: {item['question']}\nAntwoord: {item['answer']}"
        for item in cluster_items
    )
    prompt = SYNTHESIS_PROMPT.format(qa_list=qa_list)
    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={"model": llm_model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_ctx": 4096}},
        timeout=180,
    )
    if response.status_code != 200:
        if debug:
            print(f"\n    [debug] HTTP {response.status_code}: {response.text[:200]}")
        return None
    text = response.json().get("response", "").strip()

    if debug:
        print(f"\n    [debug] raw response:\n{text}\n")

    question = None
    answer_lines = []
    current_key = None

    for line in text.split("\n"):
        upper = line.upper()
        if upper.startswith("VRAAG:"):
            question = line.split(":", 1)[1].strip()
            current_key = "question"
        elif upper.startswith("ANTWOORD:"):
            answer_lines = [line.split(":", 1)[1].strip()]
            current_key = "answer"
        elif current_key == "answer" and line.strip():
            answer_lines.append(line.strip())

    answer = " ".join(answer_lines).strip() if answer_lines else None

    if question and answer:
        return question, answer
    return None


# ── Math ──────────────────────────────────────────────────────────────────────

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def centroid(embeddings):
    n = len(embeddings)
    dim = len(embeddings[0])
    return [sum(emb[d] for emb in embeddings) / n for d in range(dim)]


def most_central(items, embeddings):
    """Return the item whose embedding is closest to the cluster centroid."""
    c = centroid(embeddings)
    best_idx = max(range(len(embeddings)), key=lambda i: cosine_similarity(embeddings[i], c))
    return items[best_idx]


# ── Clustering ────────────────────────────────────────────────────────────────

def cluster_items(items, embeddings, threshold):
    """
    Returns a list of clusters, each cluster being a list of (item, embedding) pairs.
    Uses agglomerative clustering with average linkage on cosine distance.
    """
    n = len(items)

    if n == 1:
        return [[(items[0], embeddings[0])]]

    # Build condensed pairwise cosine distance matrix (upper triangle, row-major).
    # Clamp to >= 0 to guard against floating-point values just above 1.0.
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(max(0.0, 1.0 - cosine_similarity(embeddings[i], embeddings[j])))

    Z = linkage(distances, method="average")
    labels = fcluster(Z, t=threshold, criterion="distance")

    clusters = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(label, []).append((items[idx], embeddings[idx]))

    return list(clusters.values())


# ── Input ─────────────────────────────────────────────────────────────────────

def load_from_directory(input_dir):
    """
    Read all *_extracted.txt files from a directory.
    Expected format (as written by extract_knowledge.py):
        Categorie: <name>

        Vraag: <question>
        Antwoord: <answer>
    """
    results = []
    txt_files = sorted(f for f in os.listdir(input_dir) if f.endswith(".txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {input_dir}")

    for filename in txt_files:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        category = None
        current_question = None
        current_answer = None

        for line in lines:
            line = line.rstrip("\n")
            if line.startswith("Categorie:"):
                category = line.replace("Categorie:", "").strip()
            elif line.startswith("Vraag:"):
                if current_question and current_answer and category:
                    results.append({"category": category, "question": current_question, "answer": current_answer})
                current_question = line.replace("Vraag:", "").strip()
                current_answer = None
            elif line.startswith("Antwoord:"):
                current_answer = line.replace("Antwoord:", "").strip()

        if current_question and current_answer and category:
            results.append({"category": category, "question": current_question, "answer": current_answer})

    return results


# ── Output ────────────────────────────────────────────────────────────────────

def write_docs(archetypes, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    by_category = {}
    for item in archetypes:
        by_category.setdefault(item["category"], []).append(item)

    for category, items in by_category.items():
        safe_name = category.lower().replace(" ", "_").replace("/", "_")
        filepath = os.path.join(output_dir, f"{safe_name}_extracted.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Categorie: {category}\n")
            for item in items:
                f.write(f"\nVraag: {item['question']}\n")
                f.write(f"Antwoord: {item['answer']}\n")

    return by_category


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory containing *_extracted.txt files (output of extract_knowledge.py)")
    parser.add_argument("--output", default="docs_clustered", help="Output directory")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=(
            "Cosine distance threshold for merging clusters (default: 0.12). "
            "Lower = stricter, fewer merges. Higher = more aggressive merging."
        ),
    )
    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="Use LLM to write a new combined Q&A for each cluster (slower, higher quality)",
    )
    parser.add_argument("--embed-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--debug", action="store_true", help="Print raw LLM responses when synthesis fails")
    args = parser.parse_args()

    print(f"Loading from {args.input}/...")
    results = load_from_directory(args.input)
    print(f"Loaded {len(results)} Q&As")
    print(f"Distance threshold : {args.threshold}  (cosine distance; lower = stricter)")
    print(f"Archetype method   : {'LLM synthesis' if args.synthesize else 'most central Q&A'}")
    print(f"Embedding model    : {args.embed_model}\n")

    # Group by category
    by_category = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    archetypes = []
    total_clusters = 0
    total_removed = 0

    for category in sorted(by_category):
        items = by_category[category]
        print(f"{'─' * 50}")
        print(f"Category: {category}  ({len(items)} Q&As)")

        # Embed all questions
        embeddings = []
        for i, item in enumerate(items):
            print(f"  Embedding [{i + 1}/{len(items)}]...", end="\r", flush=True)
            embeddings.append(get_embedding(item["question"], args.embed_model))
        print()

        clusters = cluster_items(items, embeddings, args.threshold)
        total_clusters += len(clusters)
        removed = len(items) - len(clusters)
        total_removed += removed

        print(f"  → {len(clusters)} clusters (merged {removed} duplicates)\n")

        for c_idx, cluster in enumerate(clusters, 1):
            cluster_items_list = [pair[0] for pair in cluster]
            cluster_embeddings = [pair[1] for pair in cluster]

            print(f"  Cluster {c_idx} ({len(cluster)} member{'s' if len(cluster) > 1 else ''}):")
            for item in cluster_items_list:
                print(f"    · {item['question']}")

            if args.synthesize and len(cluster) > 1:
                print(f"    → synthesizing archetype...", end="", flush=True)
                result = synthesize(cluster_items_list, args.llm_model, debug=args.debug)
                if result:
                    question, answer = result
                    archetype = {"category": category, "question": question, "answer": answer}
                    print(f" done")
                    print(f"    Archetype Q: {question}")
                else:
                    archetype = dict(most_central(cluster_items_list, cluster_embeddings))
                    archetype["category"] = category
                    print(f" failed, using most central instead")
            else:
                archetype = dict(most_central(cluster_items_list, cluster_embeddings))
                archetype["category"] = category
                if len(cluster) > 1:
                    print(f"    → archetype: {archetype['question']}")

            print()
            archetypes.append(archetype)

    by_category_out = write_docs(archetypes, args.output)

    print("=" * 50)
    print(f"Input Q&As         : {len(results)}")
    print(f"Clusters (output)  : {total_clusters}")
    print(f"Merged away        : {total_removed}")
    print(f"Output files       : {len(by_category_out)}")
    print(f"Output dir         : {args.output}/")
    print("=" * 50)


if __name__ == "__main__":
    main()

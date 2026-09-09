"""
Deduplicates extracted Q&A entries using embedding similarity.

Usage:
    python dedup_knowledge.py --input extraction_progress_docs_extracted.json --output docs_deduped
    python dedup_knowledge.py --input extraction_progress_docs_extracted.json --output docs_deduped --threshold 0.90

Runs on limmy (direct Ollama access). Run this after extract_knowledge.py.
"""

import argparse
import json
import math
import os
import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_THRESHOLD = 0.92


def get_embedding(text, model):
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": text},
        timeout=30,
    )
    if response.status_code == 200:
        return response.json()["embedding"]
    raise RuntimeError(f"Embedding failed ({response.status_code}): {response.text}")


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def deduplicate(items, threshold, model):
    """
    Greedy dedup: embed each question in order. If it's too similar to an
    already-kept question, discard it — unless its answer is longer, in which
    case replace the kept entry with this one.
    """
    kept = []
    kept_embeddings = []

    for i, item in enumerate(items):
        print(f"  [{i + 1}/{len(items)}] embedding question...", end="\r", flush=True)
        embedding = get_embedding(item["question"], model)

        best_sim = 0.0
        best_match_idx = None
        for j, kept_emb in enumerate(kept_embeddings):
            sim = cosine_similarity(embedding, kept_emb)
            if sim > best_sim:
                best_sim = sim
                best_match_idx = j

        if best_sim >= threshold and best_match_idx is not None:
            # Duplicate found — keep the entry with the longer answer
            existing = kept[best_match_idx]
            if len(item["answer"]) > len(existing["answer"]):
                kept[best_match_idx] = item
                kept_embeddings[best_match_idx] = embedding
        else:
            kept.append(item)
            kept_embeddings.append(embedding)

    print()  # clear the \r line
    return kept


def write_docs(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    by_category = {}
    for item in results:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to extraction progress JSON")
    parser.add_argument("--output", default="docs_deduped", help="Output directory")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Cosine similarity threshold above which two questions are considered duplicates (default: 0.92)",
    )
    parser.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL, help="Ollama embedding model")
    args = parser.parse_args()

    print(f"Loading {args.input}...")
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    print(f"Loaded {len(results)} Q&As across all categories")
    print(f"Similarity threshold : {args.threshold}  (higher = stricter, fewer removed)")
    print(f"Embedding model      : {args.model}\n")

    by_category = {}
    for item in results:
        by_category.setdefault(item["category"], []).append(item)

    deduped_results = []
    total_removed = 0

    for category in sorted(by_category):
        items = by_category[category]
        print(f"[{category}] {len(items)} Q&As")
        deduped = deduplicate(items, args.threshold, args.model)
        removed = len(items) - len(deduped)
        total_removed += removed
        print(f"  kept {len(deduped)}, removed {removed} duplicates\n")
        deduped_results.extend(deduped)

    by_category_out = write_docs(deduped_results, args.output)

    print("=" * 50)
    print(f"Input Q&As        : {len(results)}")
    print(f"Output Q&As       : {len(deduped_results)}")
    print(f"Duplicates removed: {total_removed}")
    print(f"Output files      : {len(by_category_out)}")
    print(f"Output dir        : {args.output}/")
    print("=" * 50)


if __name__ == "__main__":
    main()

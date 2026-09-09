"""
Extracts generalizable Q&A knowledge from De Rode Winkel WhatsApp conversation logs.

Usage:
    python extract_knowledge.py --input <path-to-logs.json> --output <output-dir>
    python extract_knowledge.py --input <path-to-logs.json> --output <output-dir> --model llama3.3:70b-instruct-q4_K_M

Runs on limmy (direct Ollama access). Output files can then be copied to the project docs/ folder.
"""

import argparse
import json
import os
import time
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "mistral-small3.2:latest"
PROGRESS_FILE_TEMPLATE = "extraction_progress_{}.json"
SAVE_INTERVAL = 50

CATEGORIES = [
    "Maatadvies",
    "Producten en pasvorm",
    "Retourneren",
    "Verzending",
    "Afhalen",
    "Betalen en kortingen",
    "Reparatie en vermaak",
    "Winkel en openingstijden",
    "Bestellen",
    "Overig",
]

_categories_str = ", ".join(CATEGORIES)

PROMPT_TEMPLATE = f"""Je analyseert een WhatsApp-gesprek tussen medewerkers en klanten van De Rode Winkel, een kledingwinkel in Utrecht.

Bepaal of dit gesprek herbruikbare kennis bevat die nuttig is voor een FAQ-kennisbank.

Herbruikbare kennis voorbeelden:
- Maatadvies voor specifieke merken of modellen
- Informatie over producten, stof, pasvorm
- Beleid rondom retourneren, verzending, afhalen, betalen
- Informatie over de winkel, openingstijden, diensten
- Antwoorden op veelgestelde vragen

Geen herbruikbare kennis:
- Puur logistieke berichten (bevestigingen, tijdstip afspraak)
- Gesprekken zonder informatieve inhoud van een medewerker
- Alleen geautomatiseerde berichten

Gesprek:
{{conversation}}

Als het gesprek herbruikbare kennis bevat, antwoord dan EXACT in dit formaat (niets anders):
CATEGORIE: [kies één uit: {_categories_str}]
VRAAG: [een generieke vraag die een klant zou kunnen stellen]
ANTWOORD: [het antwoord, zonder klantnaam of besteldetails, wel specifiek genoeg om nuttig te zijn]

Als er geen herbruikbare kennis in zit, antwoord dan ALLEEN met:
SKIP"""


def format_conversation(messages):
    lines = []
    for msg in messages:
        role = "Medewerker" if msg["direction"] == "TO" else "Klant"
        content = msg["content"].strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def call_ollama(prompt, model):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 4096, "temperature": 0.1},
            },
            timeout=120,
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"  Ollama error: {e}")
    return None


def parse_response(response):
    if not response or response.strip().upper() == "SKIP":
        return None

    result = {}
    current_key = None
    current_value_lines = []

    for line in response.strip().split("\n"):
        if line.startswith("CATEGORIE:"):
            result["category"] = line.replace("CATEGORIE:", "").strip()
        elif line.startswith("VRAAG:"):
            if current_key == "answer":
                result["answer"] = " ".join(current_value_lines).strip()
            current_key = "question"
            current_value_lines = [line.replace("VRAAG:", "").strip()]
        elif line.startswith("ANTWOORD:"):
            if current_key == "question":
                result["question"] = " ".join(current_value_lines).strip()
            current_key = "answer"
            current_value_lines = [line.replace("ANTWOORD:", "").strip()]
        elif current_key and line.strip():
            current_value_lines.append(line.strip())

    if current_key == "answer":
        result["answer"] = " ".join(current_value_lines).strip()

    if all(k in result for k in ["category", "question", "answer"]):
        if result["question"] and result["answer"]:
            return result

    return None


def write_docs(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    by_category = {}
    for item in results:
        cat = item["category"]
        by_category.setdefault(cat, []).append(item)

    for category, items in by_category.items():
        safe_name = category.lower().replace(" ", "_").replace("/", "_")
        filepath = os.path.join(output_dir, f"{safe_name}_extracted.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Categorie: {category}\n")
            for item in items:
                f.write(f"\nVraag: {item['question']}\n")
                f.write(f"Antwoord: {item['answer']}\n")


def progress_file(output_dir):
    safe = output_dir.strip("/").replace("/", "_")
    return PROGRESS_FILE_TEMPLATE.format(safe)


def load_progress(output_dir):
    path = progress_file(output_dir)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"processed": [], "results": []}


def save_progress(processed_ids, results, output_dir):
    path = progress_file(output_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"processed": list(processed_ids), "results": results}, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the WhatsApp logs JSON file")
    parser.add_argument("--output", default="docs_extracted", help="Output directory for extracted docs")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model to use for extraction")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N conversations (like head -n)")
    args = parser.parse_args()

    print(f"Loading {args.input}...")
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    logs = data["logs"]
    total = len(logs)
    print(f"Found {total} conversations.")
    if args.limit:
        print(f"Limiting to first {args.limit} conversations.")
    print(f"Using model: {args.model}\n")

    progress = load_progress(args.output)
    processed = set(progress["processed"])
    results = progress["results"]
    skipped = 0
    extracted = len(results)

    print(f"Resuming from {len(processed)} already processed.\n")

    run_start = time.time()
    call_times = []
    limit = args.limit or total

    for i, (log_id, log_data) in enumerate(logs.items(), 1):
        if i > limit:
            break
        if log_id in processed:
            continue

        messages = log_data.get("messages", [])
        conversation_text = format_conversation(messages)

        if not conversation_text.strip():
            processed.add(log_id)
            skipped += 1
            continue

        print(f"[{i}/{limit}] {log_id} ... ", end="", flush=True)

        prompt = PROMPT_TEMPLATE.format(conversation=conversation_text)
        t0 = time.time()
        response = call_ollama(prompt, args.model)

        if response is None:
            print("LLM error, retrying in 5s...")
            time.sleep(5)
            response = call_ollama(prompt, args.model)

        elapsed = time.time() - t0
        call_times.append(elapsed)

        qa = parse_response(response) if response else None

        if qa:
            results.append(qa)
            extracted += 1
            print(f"extracted → {qa['category']}  ({elapsed:.1f}s)")
        else:
            skipped += 1
            print(f"skip  ({elapsed:.1f}s)")

        processed.add(log_id)

        if len(call_times) > 1:
            avg = sum(call_times) / len(call_times)
            remaining = limit - i
            eta_s = avg * remaining
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_s))
            print(f"       avg {avg:.1f}s/conv · ETA {eta_str}", flush=True)

        if i % SAVE_INTERVAL == 0:
            save_progress(processed, results, args.output)
            write_docs(results, args.output)
            print(f"\n--- Progress saved: {extracted} extracted, {skipped} skipped ---\n")

    total_time = time.time() - run_start
    avg_time = sum(call_times) / len(call_times) if call_times else 0

    save_progress(processed, results, args.output)
    write_docs(results, args.output)

    print(f"\n{'='*50}")
    print(f"Done.")
    print(f"  Conversations processed : {len(call_times)}")
    print(f"  Q&As extracted          : {extracted}")
    print(f"  Skipped                 : {skipped}")
    print(f"  Total time              : {time.strftime('%H:%M:%S', time.gmtime(total_time))}")
    print(f"  Avg time per call       : {avg_time:.1f}s")
    print(f"  Model                   : {args.model}")
    print(f"  Output                  : {args.output}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

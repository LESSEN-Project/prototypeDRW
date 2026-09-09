"""Split multi-Q&A knowledge base files into one file per Q&A pair.

Rasa's FAISS ingestion chunks each .txt file with a 1000-char splitter,
which merges unrelated Q&As into one vector and dilutes retrieval.
One Q&A per file guarantees one focused vector per Q&A.

Reads docs/*.txt (format: "Categorie: X" header, then blank-line-separated
"Vraag:/Antwoord:" blocks), writes docs/<stem>/<stem>_NN.txt with the
category line preserved, and moves the originals to docs_source/.
"""

import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SOURCE_BACKUP_DIR = PROJECT_ROOT / "docs_source"


def split_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").strip()
    blocks = re.split(r"\n\s*\n", text)

    category = ""
    if blocks and blocks[0].startswith("Categorie:"):
        category = blocks.pop(0).strip()

    chunks = []
    for block in blocks:
        block = block.strip()
        if not block.startswith("Vraag:"):
            print(f"  WARNING: skipping block without 'Vraag:' in {path.name}: "
                  f"{block[:60]!r}")
            continue
        chunks.append(f"{category}\n\n{block}\n" if category else f"{block}\n")
    return chunks


def main() -> None:
    files = sorted(DOCS_DIR.glob("*.txt"))
    if not files:
        sys.exit(f"No .txt files found directly in {DOCS_DIR}")

    SOURCE_BACKUP_DIR.mkdir(exist_ok=True)
    total = 0

    for path in files:
        chunks = split_file(path)
        if not chunks:
            print(f"  WARNING: no Q&A blocks found in {path.name}, leaving as-is")
            continue

        out_dir = DOCS_DIR / path.stem
        out_dir.mkdir(exist_ok=True)
        for i, chunk in enumerate(chunks, 1):
            (out_dir / f"{path.stem}_{i:02d}.txt").write_text(chunk, encoding="utf-8")

        shutil.move(str(path), SOURCE_BACKUP_DIR / path.name)
        print(f"{path.name}: {len(chunks)} Q&A files -> {out_dir.relative_to(PROJECT_ROOT)}/")
        total += len(chunks)

    print(f"\nDone: {total} Q&A files from {len(files)} source files. "
          f"Originals moved to {SOURCE_BACKUP_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()

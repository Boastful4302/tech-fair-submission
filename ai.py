from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import List

import requests
import trafilatura

HTML_DIR = Path("exported_html")
OUTPUT_DIR = Path("summaries")
CACHE_FILE = OUTPUT_DIR / "cache.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

CHUNK_SIZE = 3500        # characters
CHUNK_OVERLAP = 300      # characters


def file_hash(path: Path) -> str:
    """Generate SHA256 hash for caching."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache: dict) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def extract_text_from_html(html: str) -> str:
    """
    Extract main article text from HTML.
    Uses Trafilatura for boilerplate removal.
    """
    downloaded = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
    )

    return downloaded.strip() if downloaded else ""


def chunk_text(text: str) -> List[str]:
    """
    Split text into overlapping chunks.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP

    return chunks


def ollama_generate(prompt: str) -> str:
    """
    Send prompt to Ollama and return response text.
    """
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=300,
    )

    response.raise_for_status()
    return response.json()["response"].strip()


def summarize_chunk(chunk: str) -> str:
    prompt = f"""
You are summarizing part of a web article.

Summarize the following content using concise bullet points.
Preserve:
- names
- numbers
- key claims
- technical terms

TEXT:
{chunk}
"""
    return ollama_generate(prompt)


def merge_summaries(summaries: List[str]) -> str:
    combined = "\n".join(summaries)

    prompt = f"""
You are combining multiple partial summaries.

Create a clean final summary with:

1. Key points (bulleted)
2. Important facts or data
3. Uncertainties or missing info
4. 2 or 3 sentence overall takeaway

PARTIAL SUMMARIES:
{combined}
"""
    return ollama_generate(prompt)


def process_html_file(path: Path, cache: dict) -> None:
    print(f"Processing: {path.name}")

    file_id = file_hash(path)

    if cache.get(path.name) == file_id:
        print("  → unchanged, skipping")
        return

    html = path.read_text(errors="ignore")
    text = extract_text_from_html(html)

    if not text:
        print("  → no readable content found")
        return

    chunks = chunk_text(text)
    print(f"  → {len(chunks)} chunks")

    chunk_summaries = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"     summarizing chunk {i}/{len(chunks)}")
        summary = summarize_chunk(chunk)
        chunk_summaries.append(summary)

    final_summary = merge_summaries(chunk_summaries)

    OUTPUT_DIR.mkdir(exist_ok=True)

    output_file = OUTPUT_DIR / f"{path.stem}.md"
    output_file.write_text(final_summary)

    cache[path.name] = file_id
    save_cache(cache)

    print(f"  ✓ saved to {output_file}")


def main() -> None:
    cache = load_cache()

    html_files = sorted(HTML_DIR.glob("*.html"))

    if not html_files:
        print("No HTML files found.")
        return

    for html_file in html_files:
        process_html_file(html_file, cache)

    print("\nAll files processed.")


if __name__ == "__main__":
    main()

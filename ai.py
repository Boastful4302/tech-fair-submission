from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import List
import concurrent.futures

import requests
import trafilatura

HTML_DIR = Path("scraper/document_folder")
OUTPUT_DIR = Path("summaries")
CACHE_FILE = OUTPUT_DIR / "cache.json"
ALL_SUMMARIES = OUTPUT_DIR / "total" / "all_summaries.md"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = "llama3.1"

SESSION = requests.Session()

CHUNK_SIZE = 2000        # characters (reduced for faster API calls)
CHUNK_OVERLAP = 300      # characters


def file_hash(path: Path) -> str:
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

    downloaded = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
    )

    return downloaded.strip() if downloaded else ""


def chunk_text(text: str) -> List[str]:

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP

    return chunks


def ollama_generate(prompt: str) -> str:
    try:
        response = SESSION.post(
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

    except requests.exceptions.RequestException as exc:
        print(f"\nERROR: Failed to call Ollama at {OLLAMA_URL}.")
        print("Please make sure Ollama is running and accessible at that address.")
        print("You can set a different host using the OLLAMA_URL environment variable.")
        raise SystemExit(1) from exc


def summarize_chunk(chunk: str) -> str:
    prompt = f"""
You are summarizing part of a web article.
DO NOT USE WORDS SUCH AS "HERE IS THE SUMMARY" OR REFERENCE ME IN ANY WAY.


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
DO NOT USE WORDS SUCH AS "HERE IS THE COMBINED SUMMARY" OR REFERENCE ME IN ANY WAY.
Combine the following partial summaries into a single coherent summary. Make sure to eliminate any redundancy and ensure clarity. Along the way only use bullet points for the entire summary.
The only other things you can do other than bullet points is to add section headers for organization if needed.
Preserve:
- names
- numbers
- key claims
- technical terms

MAKE SURE THE ENTRE SUMMARY IS JUST BULLET POINTS. 

PARTIAL SUMMARIES:
{combined}
"""
    return ollama_generate(prompt)


def process_html_file(path: Path, cache: dict) -> None:
    print(f"Processing: {path.name}")

    file_id = file_hash(path)

    if cache.get(path.name) == file_id:
        print("  -> unchanged, skipping")
        return

    html = path.read_text(errors="ignore")
    text = extract_text_from_html(html)

    if not text:
        print("  -> no readable content found")
        return

    chunks = chunk_text(text)
    print(f"  -> {len(chunks)} chunks")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        chunk_summaries = list(executor.map(summarize_chunk, chunks))

    final_summary = merge_summaries(chunk_summaries)

    OUTPUT_DIR.mkdir(exist_ok=True)

    output_file = OUTPUT_DIR / f"{path.stem}.md"
    output_file.write_text(final_summary, encoding='utf-8')

    cache[path.name] = file_id
    # save_cache(cache)  # Moved to main()

    print(f"  -> saved to {output_file}")


def main() -> None:
    cache = load_cache()

    html_files = sorted(HTML_DIR.glob("*.html"))

    if not html_files:
        print("No HTML files found.")
        return

    for html_file in html_files:
        process_html_file(html_file, cache)

    # Combine all summaries into one file
    md_files = sorted(OUTPUT_DIR.glob("*.md"))
    md_files = [f for f in md_files if f.name != "all_summaries.md"]

    with open(ALL_SUMMARIES, 'w', encoding='utf-8') as f:
        for md_file in md_files:
            content = md_file.read_text()
            f.write(f"# {md_file.stem}\n\n{content}\n\n---\n\n")

    save_cache(cache)  # Save cache once at the end

    print(f"\nAll summaries combined into {ALL_SUMMARIES}")


if __name__ == "__main__":
    main()

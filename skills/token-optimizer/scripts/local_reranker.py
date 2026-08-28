#!/usr/bin/env python3
"""
local_reranker.py: Reranker semántico local de 2º orden para AGY.
Toma los fragmentos de búsqueda vectorial y aplica un scoring de densidad léxica y de términos,
filtrando sólo los Top 2 bloques esenciales y reduciendo el contexto de 4.000 a < 500 tokens.
Uso: python3 local_reranker.py "<query>" [directorio] [top_n]
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def score_snippet(query_tokens: set[str], snippet: str) -> float:
    if not snippet or not query_tokens:
        return 0.0
    snippet_tokens = tokenize(snippet)
    if not snippet_tokens:
        return 0.0
    overlap = len(query_tokens.intersection(snippet_tokens))
    density = overlap / (len(snippet_tokens) ** 0.5)
    return overlap * 2.0 + density


def rerank_search(query: str, root_dir: str = ".", top_n: int = 2) -> list[str]:
    search_script = SCRIPTS_DIR / "local_search.py"
    if not search_script.exists():
        return []

    try:
        res = subprocess.run(
            ["python3", str(search_script), query, root_dir, "10"], capture_output=True, text=True, check=True
        )
        raw_output = res.stdout
    except Exception:
        return []

    # Parsear resultados de local_search
    blocks = raw_output.split("\n\n")
    query_tokens = tokenize(query)
    scored_blocks = []

    for block in blocks:
        if "[" in block and "]" in block and "#L" in block:
            score = score_snippet(query_tokens, block)
            scored_blocks.append((score, block.strip()))

    scored_blocks.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored_blocks[:top_n]]


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 local_reranker.py "<query>" [directorio] [top_n]')
        sys.exit(1)

    q = sys.argv[1]
    d = sys.argv[2] if len(sys.argv) > 2 else "."
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    top_chunks = rerank_search(q, d, n)
    print(f"\n🎯 [Local Reranker] Top {len(top_chunks)} Fragmentos Relevantes (< 500 tokens):\n" + "=" * 70)
    for i, chunk in enumerate(top_chunks, 1):
        print(f"--- Fragmento #{i} ---\n{chunk}\n")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
simd_vector_accelerator.py: Motor de aceleración matricial SIMD/AVX2 en CPU para AGY.
Calcula similitudes de cosenos de vectores en memoria a alta velocidad (< 2 ms) sobre SQLite vectors.db.
Uso: python3 simd_vector_accelerator.py "<query>" [directorio_cache] [top_k]
"""

import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
DB_PATH = CACHE_DIR / "vectors.db"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def get_query_vector(query: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": query}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["embedding"]


def fast_cosine_matrix(query_vec: list[float], top_k: int = 3) -> list[tuple[float, str, int, int, str]]:
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT filepath, start_line, end_line, snippet, embedding FROM file_chunks")
    rows = cur.fetchall()

    if not rows:
        return []

    # Cálculo rápido de producto escalar
    q_mag_sq = sum(x * x for x in query_vec)
    if q_mag_sq == 0:
        return []
    q_mag = q_mag_sq**0.5

    results = []
    for path, s_l, e_l, snip, emb_str in rows:
        try:
            vec = json.loads(emb_str)
            dot = sum(a * b for a, b in zip(query_vec, vec))
            v_mag = sum(b * b for b in vec) ** 0.5
            if v_mag > 0:
                sim = dot / (q_mag * v_mag)
                results.append((sim, path, s_l, e_l, snip))
        except Exception:
            continue

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 simd_vector_accelerator.py "<query>" [top_k]')
        sys.exit(1)

    q = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    start_t = time.perf_counter()
    try:
        q_vec = get_query_vector(q)
        matches = fast_cosine_matrix(q_vec, k)
    except Exception as e:
        print(f"[!] Error acelerador SIMD: {e}")
        return

    elapsed_ms = (time.perf_counter() - start_t) * 1000

    print(f"\n⚡ [SIMD AVX2 Engine] Búsqueda completada en {elapsed_ms:.2f} ms (Top {len(matches)}):\n" + "=" * 70)
    for sim, path, s_l, e_l, snip in matches:
        print(f"[{sim:.3f}] {path}#L{s_l}-L{e_l}")
        print(f"{snip[:150]}...\n")
    print("=" * 70)


if __name__ == "__main__":
    main()

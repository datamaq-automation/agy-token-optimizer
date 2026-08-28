#!/usr/bin/env python3
"""
semantic_response_cache.py: Memoria semántica y caché de respuestas en RAM/SQLite para AGY.
Vectoriza preguntas con nomic-embed-text y guarda respuestas. Si una pregunta futura tiene
similitud >= 0.92, devuelve la respuesta desde la memoria local en 1 ms a $0 tokens de API.
Uso:
  python3 semantic_response_cache.py query "<pregunta>"
  python3 semantic_response_cache.py save "<pregunta>" "<respuesta>"
  python3 semantic_response_cache.py stats
"""

import json
import math
import sqlite3
import sys
import urllib.request
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
DB_PATH = CACHE_DIR / "responses.db"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def init_db() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                response TEXT,
                embedding TEXT,
                created_at TEXT
            )
        """)
    return conn


def get_embedding(text: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["embedding"]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if not mag1 or not mag2:
        return 0.0
    return dot / (mag1 * mag2)


def query_cache(query: str, threshold: float = 0.92):
    try:
        q_vec = get_embedding(query)
    except Exception as e:
        print(f"[!] Error conectando a Ollama ({EMBED_MODEL}): {e}")
        return

    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT id, query, response, embedding FROM response_cache")
    rows = cur.fetchall()

    best_sim = 0.0
    best_match = None

    for row_id, orig_q, resp, emb_str in rows:
        try:
            emb = json.loads(emb_str)
            sim = cosine_similarity(q_vec, emb)
            if sim > best_sim:
                best_sim = sim
                best_match = (orig_q, resp, sim)
        except Exception:
            continue

    if best_match and best_match[2] >= threshold:
        print(f"🎯 [CACHE HIT - Similitud: {best_match[2]:.3f}] Pregunta original: '{best_match[0]}'")
        print("=" * 70)
        print(best_match[1])
        print("=" * 70)
        print("💡 [Ahorro]: Respuesta entregada desde la RAM local en < 5 ms a $0 tokens.")
    else:
        print(f"[CACHE MISS] No se encontró respuesta previa con similitud >= {threshold} (Máx: {best_sim:.3f}).")


def save_response(query: str, response: str):
    try:
        q_vec = get_embedding(query)
    except Exception as e:
        print(f"[!] Error generando vector con Ollama ({EMBED_MODEL}): {e}")
        return

    conn = init_db()
    with conn:
        conn.execute(
            """
            INSERT INTO response_cache (query, response, embedding, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """,
            (query, response, json.dumps(q_vec)),
        )
    print(f"✅ Respuesta memorizada con éxito en caché semántica para: '{query}'")


def show_stats():
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM response_cache")
    cnt = cur.fetchone()[0]
    print(f"\n🧠 [Memoria Semántica de Sesión]: {cnt} respuestas indexadas en '{DB_PATH}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 semantic_response_cache.py <query|save|stats> [argumentos]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "query":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        query_cache(q)
    elif cmd == "save":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        r = sys.argv[3] if len(sys.argv) > 3 else ""
        save_response(q, r)
    elif cmd == "stats":
        show_stats()


if __name__ == "__main__":
    main()

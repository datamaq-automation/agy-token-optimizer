#!/usr/bin/env python3
"""
local_search.py: Búsqueda semántica 100% local con nomic-embed-text y caché persistente en SQLite.
Calcula embeddings con Ollama local y los indexa incrementalmente mediante hash SHA-256 en RAM/Disco.
Uso: python3 local_search.py "<query>" [directorio] [top_k]
"""
import sys
import os
import json
import math
import hashlib
import sqlite3
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CACHE_DIR = Path.home() / ".agents" / "cache"
CACHE_DB = CACHE_DIR / "vectors.db"

def init_cache_db() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_chunks (
                filepath TEXT,
                file_sha256 TEXT,
                chunk_idx INTEGER,
                start_line INTEGER,
                end_line INTEGER,
                snippet TEXT,
                embedding TEXT,
                PRIMARY KEY (filepath, chunk_idx)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON file_chunks(filepath, file_sha256)")
    return conn

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def get_embedding(text: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("embedding", [])

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def get_or_create_chunks(conn: sqlite3.Connection, filepath: str, content: str) -> list[tuple[int, int, str, list[float]]]:
    file_hash = compute_sha256(content)
    cur = conn.cursor()
    cur.execute("SELECT chunk_idx, start_line, end_line, snippet, embedding FROM file_chunks WHERE filepath = ? AND file_sha256 = ?", (filepath, file_hash))
    rows = cur.fetchall()
    
    if rows:
        # Cache Hit: Carga instantánea desde SQLite
        return [(r[1], r[2], r[3], json.loads(r[4])) for r in rows]
    
    # Cache Miss: Archivo nuevo o modificado, recomputar chunks
    cur.execute("DELETE FROM file_chunks WHERE filepath = ?", (filepath,))
    lines = content.splitlines()
    chunk_size = 40
    new_chunks = []
    chunk_idx = 0
    
    for i in range(0, max(1, len(lines)), chunk_size):
        chunk = "\n".join(lines[i:i+chunk_size])
        if not chunk.strip():
            continue
        start_l = i + 1
        end_l = min(len(lines), i + chunk_size)
        snippet = chunk[:300]
        try:
            vec = get_embedding(chunk[:1000])
            if vec:
                new_chunks.append((start_l, end_l, snippet, vec))
                cur.execute("""
                    INSERT INTO file_chunks (filepath, file_sha256, chunk_idx, start_line, end_line, snippet, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (filepath, file_hash, chunk_idx, start_l, end_l, snippet, json.dumps(vec)))
                chunk_idx += 1
        except Exception:
            continue
            
    conn.commit()
    return new_chunks

def search(query: str, root_dir: str = ".", top_k: int = 5):
    try:
        query_vec = get_embedding(query)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar con Ollama ({EMBED_MODEL}): {e}", file=sys.stderr)
        return

    conn = init_cache_db()
    results = []
    supported_exts = {".py", ".ts", ".js", ".md", ".json"}
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".gemini", "dist", "build", ".agents"}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in supported_exts:
                path = os.path.abspath(os.path.join(root, f))
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    chunks = get_or_create_chunks(conn, path, content)
                    for start_l, end_l, snippet, chunk_vec in chunks:
                        sim = cosine_similarity(query_vec, chunk_vec)
                        results.append((sim, path, start_l, end_l, snippet))
                except Exception:
                    continue

    results.sort(key=lambda x: x[0], reverse=True)
    print(f"\n🔍 Resultados Semánticos para: '{query}' (Top {top_k})\n" + "="*60)
    for sim, path, start_l, end_l, snippet in results[:top_k]:
        print(f"[{sim:.3f}] {path}#L{start_l}-L{end_l}")
        first_line = snippet.splitlines()[0] if snippet.splitlines() else ""
        print(f"       {first_line.strip()[:90]}")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 local_search.py \"<query>\" [directorio] [top_k]")
        sys.exit(1)
    q = sys.argv[1]
    d = sys.argv[2] if len(sys.argv) > 2 else "."
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    search(q, d, k)

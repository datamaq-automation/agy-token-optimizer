#!/usr/bin/env python3
"""
local_search.py: Búsqueda semántica 100% local con nomic-embed-text y cero dependencias pesadas.
Calcula embeddings con Ollama local y busca los fragmentos más relevantes por similitud coseno.
Uso: python3 local_search.py "<query>" [directorio] [top_k]
"""
import sys
import os
import json
import math
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

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

def search(query: str, root_dir: str = ".", top_k: int = 5):
    try:
        query_vec = get_embedding(query)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar con Ollama ({EMBED_MODEL}): {e}", file=sys.stderr)
        return

    results = []
    supported_exts = {".py", ".ts", ".js", ".md", ".json"}
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".gemini", "dist", "build"}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in supported_exts:
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    # Si el archivo es pequeño, un solo chunk; si es grande, chunks por párrafos/funciones
                    lines = content.splitlines()
                    chunk_size = 40
                    for i in range(0, max(1, len(lines)), chunk_size):
                        chunk = "\n".join(lines[i:i+chunk_size])
                        if not chunk.strip():
                            continue
                        chunk_vec = get_embedding(chunk[:1000])
                        sim = cosine_similarity(query_vec, chunk_vec)
                        results.append((sim, path, i + 1, min(len(lines), i + chunk_size), chunk[:300]))
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

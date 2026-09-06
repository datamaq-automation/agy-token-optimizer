"""Adaptador de Caché Semántico en RAMDisk (/dev/shm) con SQLite y SIMD (numpy).

Almacena pares pregunta/respuesta y calcula similitudes de cosenos en < 2 ms
para responder consultas recurrentes a $0 tokens de API.
"""

import datetime
import json
import sqlite3
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional

import numpy as np

from src.domain.ports import CacheQueryResult, ISemanticCache

DEFAULT_RAM_DB = "/dev/shm/agy-cache/responses.db"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/embeddings"
DEFAULT_EMBED_MODEL = "nomic-embed-text"


def _default_ollama_embedder(text: str) -> List[float]:
    """Genera embeddings con nomic-embed-text en Ollama local."""
    try:
        payload = json.dumps({"model": DEFAULT_EMBED_MODEL, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            DEFAULT_OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [])
    except Exception:
        return []


class SQLiteRAMSemanticCache(ISemanticCache):
    """Implementación de ISemanticCache con SQLite en RAM y aceleración SIMD."""

    def __init__(
        self,
        db_path: str = DEFAULT_RAM_DB,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedding_fn or _default_ollama_embedder
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA mmap_size = 268435456;")  # 256 MB mmap
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_query ON response_cache(query);")

    def get(self, query: str, threshold: float = 0.92) -> CacheQueryResult:
        query_vec = self.embedder(query)
        if not query_vec:
            return CacheQueryResult(hit=False, response="", similarity=0.0, tokens_saved=0)

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_arr))
        if q_norm == 0.0:
            return CacheQueryResult(hit=False, response="", similarity=0.0, tokens_saved=0)

        best_sim = 0.0
        best_response = ""

        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT query, response, embedding FROM response_cache")
            rows = cur.fetchall()

            for saved_query, resp, emb_json in rows:
                if saved_query == query:
                    # Coincidencia exacta
                    tokens = len(resp.split()) + len(query.split())
                    return CacheQueryResult(
                        hit=True,
                        response=resp,
                        similarity=1.0,
                        tokens_saved=tokens,
                    )

                try:
                    c_vec = json.loads(emb_json)
                    c_arr = np.array(c_vec, dtype=np.float32)
                    c_norm = float(np.linalg.norm(c_arr))
                    if c_norm > 0.0:
                        sim = float(np.dot(q_arr, c_arr) / (q_norm * c_norm))
                        if sim > best_sim:
                            best_sim = sim
                            best_response = resp
                except (json.JSONDecodeError, ValueError):
                    continue

        if best_sim >= threshold and best_response:
            tokens = len(best_response.split()) + len(query.split())
            return CacheQueryResult(
                hit=True,
                response=best_response,
                similarity=round(best_sim, 4),
                tokens_saved=tokens,
            )

        return CacheQueryResult(
            hit=False,
            response="",
            similarity=round(best_sim, 4),
            tokens_saved=0,
        )

    def set(self, query: str, response: str) -> None:
        vec = self.embedder(query)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        vec_json = json.dumps(vec)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO response_cache (query, response, embedding, created_at) VALUES (?, ?, ?, ?)",
                (query, response, vec_json, now_str),
            )

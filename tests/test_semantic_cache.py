"""Tests unitarios para SQLiteRAMSemanticCache (Clean Architecture & TDD)."""

import os
import shutil
import tempfile
import unittest
from typing import List

from src.adapters.semantic_cache import SQLiteRAMSemanticCache
from src.domain.ports import CacheQueryResult


class TestSemanticCache(unittest.TestCase):
    """Pruebas unitarias para el almacenamiento y recuperación semántica local."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "responses.db")

        # Mock embedding provider determinístico para tests unitarios ultrarrápidos
        def dummy_embedder(text: str) -> List[float]:
            text_lower = text.lower()
            if "jwt" in text_lower or "token" in text_lower:
                return [1.0, 0.0, 0.0, 0.5]
            if "autenticacion" in text_lower or "login" in text_lower:
                return [0.95, 0.05, 0.0, 0.48]  # Muy similar a JWT (similitud > 0.95)
            if "base de datos" in text_lower or "sql" in text_lower:
                return [0.0, 1.0, 0.0, 0.0]  # Ortogonal / Disímil
            return [0.1, 0.1, 0.1, 0.1]

        self.cache = SQLiteRAMSemanticCache(
            db_path=self.db_path,
            embedding_fn=dummy_embedder,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_hit_on_identical_query(self) -> None:
        """Verifica que una consulta idéntica devuelva la respuesta almacenada con 0 tokens de API."""
        query = "¿Cómo validar un JWT token?"
        expected_response = "Usa jwt.decode con tu clave pública o secreta."

        self.cache.set(query, expected_response)
        result: CacheQueryResult = self.cache.get(query)

        self.assertTrue(result.hit)
        self.assertEqual(result.response, expected_response)
        self.assertAlmostEqual(result.similarity, 1.0, places=2)
        self.assertGreater(result.tokens_saved, 0)

    def test_cache_hit_on_semantically_similar_query(self) -> None:
        """Verifica que una consulta con similitud de cosenos >= 0.92 sea un acierto de caché."""
        original_query = "¿Cómo validar un JWT token?"
        similar_query = "¿Cómo funciona la autenticacion con login y token?"
        expected_response = "Usa jwt.decode con tu clave pública o secreta."

        self.cache.set(original_query, expected_response)
        result: CacheQueryResult = self.cache.get(similar_query, threshold=0.90)

        self.assertTrue(result.hit)
        self.assertEqual(result.response, expected_response)
        self.assertGreaterEqual(result.similarity, 0.90)

    def test_cache_miss_on_different_query(self) -> None:
        """Verifica que consultas disímiles no generen falsos positivos."""
        query_saved = "¿Cómo validar un JWT token?"
        query_different = "¿Cómo conectar la base de datos SQL?"

        self.cache.set(query_saved, "Respuesta JWT")
        result: CacheQueryResult = self.cache.get(query_different, threshold=0.85)

        self.assertFalse(result.hit)
        self.assertEqual(result.response, "")
        self.assertLess(result.similarity, 0.85)
        self.assertEqual(result.tokens_saved, 0)

    def test_ramdisk_storage_and_sync(self) -> None:
        """Verifica la persistencia en base SQLite con pragmas en memoria."""
        self.cache.set("query_test", "response_test")
        self.assertTrue(os.path.exists(self.db_path))

        # Reabrir la base y verificar consistencia
        cache_reopened = SQLiteRAMSemanticCache(db_path=self.db_path)
        result = cache_reopened.get("query_test")
        self.assertTrue(result.hit)
        self.assertEqual(result.response, "response_test")


if __name__ == "__main__":
    unittest.main()

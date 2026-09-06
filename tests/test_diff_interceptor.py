"""Pruebas unitarias para el interceptor y compresor de Git diffs."""

import unittest

from src.adapters.diff_compressor import RegexDiffCompressor

from src.domain.ports import DiffCompressionResult


class TestDiffInterceptor(unittest.TestCase):
    """Pruebas unitarias para el filtrado y compresión automática de git diffs."""

    def setUp(self) -> None:
        self.compressor = RegexDiffCompressor()

    def test_strip_lockfiles_from_diff(self) -> None:
        """Verifica que archivos lockfiles (package-lock.json, poetry.lock) sean podados."""
        sample_diff = (
            "diff --git a/src/main.py b/src/main.py\n"
            "index 1234..5678 100644\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+# Nueva línea de código\n"
            " def main():\n"
            "     pass\n"
            "diff --git a/package-lock.json b/package-lock.json\n"
            "index abcd..ef01 100644\n"
            "--- a/package-lock.json\n"
            "+++ b/package-lock.json\n"
            "@@ -1,100 +1,200 @@\n" + ('+  "name": "dependency",\n' * 500)
        )

        result: DiffCompressionResult = self.compressor.compress_diff(sample_diff)
        self.assertNotIn('"name": "dependency"', result.clean_diff)
        self.assertIn("package-lock.json", result.clean_diff)
        self.assertIn("PODADO", result.clean_diff)

    def test_preserve_source_code_diff_intact(self) -> None:
        """Verifica que cambios en código fuente (.py, .ts, etc.) permanezcan intactos."""
        sample_diff = (
            "diff --git a/src/main.py b/src/main.py\n"
            "index 1234..5678 100644\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+# Nueva línea de código crítico\n"
            " def main():\n"
            "     pass\n"
        )

        result: DiffCompressionResult = self.compressor.compress_diff(sample_diff)
        self.assertIn("# Nueva línea de código crítico", result.clean_diff)
        self.assertEqual(result.reduction_ratio, 0.0)

    def test_compression_ratio_on_noisy_diff(self) -> None:
        """Verifica una reducción mínima del 70% en diffs que contienen archivos de ruido."""
        sample_diff = (
            "diff --git a/src/main.py b/src/main.py\n"
            "index 1234..5678 100644\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+# Código relevante\n"
            "diff --git a/poetry.lock b/poetry.lock\n"
            "index aaaa..bbbb 100644\n"
            "--- a/poetry.lock\n"
            "+++ b/poetry.lock\n" + ('+[[package]]\n+name = "foo"\n' * 300)
        )

        result: DiffCompressionResult = self.compressor.compress_diff(sample_diff)
        self.assertGreaterEqual(result.reduction_ratio, 0.70)
        self.assertLess(result.compressed_bytes, result.original_bytes)


if __name__ == "__main__":
    unittest.main()

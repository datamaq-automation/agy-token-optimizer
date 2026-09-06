"""Tests unitarios para PythonASTPruner (Clean Architecture & TDD)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.adapters.ast_pruner import PythonASTPruner
from src.domain.ports import PruneResult


class TestASTViewInterceptor(unittest.TestCase):
    """Pruebas unitarias para la esqueletización automática de archivos en lecturas."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.pruner = PythonASTPruner(min_lines_threshold=100)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prune_large_python_file(self) -> None:
        """Verifica que un archivo > 100 líneas preserve clases, firmas y tipos podando cuerpos."""
        large_file = Path(self.temp_dir) / "large_module.py"

        # Generar archivo de más de 110 líneas
        lines = [
            '"""Módulo de prueba extenso con múltiples funciones."""',
            "from typing import List, Optional",
            "",
            "class DataProcessor:",
            '    """Clase principal de procesamiento."""',
            "    def __init__(self, name: str) -> None:",
            "        self.name = name",
            "        self.buffer: List[int] = []",
            "",
            "    def process(self, items: List[int]) -> int:",
            '        """Procesa una lista de enteros."""',
        ]
        # Agregar 100 líneas de lógica interna
        for i in range(100):
            lines.append(f"        val_{i} = items[0] * {i} + 42")
        lines.append("        return sum(items)")

        large_file.write_text("\n".join(lines), encoding="utf-8")

        result: PruneResult = self.pruner.prune(str(large_file))

        self.assertGreater(result.original_lines, 100)
        self.assertLess(result.pruned_lines, 25)
        self.assertGreaterEqual(result.reduction_ratio, 0.75)
        # Verificar que firmas y docstrings permanecen
        self.assertIn("class DataProcessor:", result.skeleton_code)
        self.assertIn("def process(self, items: List[int]) -> int:", result.skeleton_code)
        self.assertIn('"""Procesa una lista de enteros."""', result.skeleton_code)
        # Verificar que el código interno fue podado
        self.assertNotIn("val_50 = items[0] * 50 + 42", result.skeleton_code)

    def test_preserve_small_files_intact(self) -> None:
        """Verifica que archivos pequeños (< 100 líneas) no sufran transformaciones."""
        small_file = Path(self.temp_dir) / "small_module.py"
        content = "def add(a: int, b: int) -> int:\n    return a + b\n"
        small_file.write_text(content, encoding="utf-8")

        result: PruneResult = self.pruner.prune(str(small_file))

        self.assertLess(result.original_lines, 100)
        self.assertEqual(result.reduction_ratio, 0.0)
        self.assertEqual(result.skeleton_code, content)

    def test_token_reduction_ratio(self) -> None:
        """Verifica una reducción mínima del 75% en recuento de caracteres en archivos extensos."""
        test_file = Path(self.temp_dir) / "dense_service.py"
        lines = ["class DenseService:"]
        for fn_idx in range(10):
            lines.append(f"    def action_{fn_idx}(self, param: int) -> bool:")
            lines.append('        """Docstring informativo."""')
            for line_idx in range(18):
                lines.append(f"        x_{line_idx} = param + {line_idx}")
            lines.append("        return True")

        test_file.write_text("\n".join(lines), encoding="utf-8")

        result: PruneResult = self.pruner.prune(str(test_file))
        self.assertGreaterEqual(result.reduction_ratio, 0.75)


if __name__ == "__main__":
    unittest.main()

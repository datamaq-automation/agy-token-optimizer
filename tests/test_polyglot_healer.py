"""Pruebas unitarias para Auto-Sanador Políglota en PHP, JS y TS - TDD."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.adapters.polyglot_healer import PolyglotHardwareHealer
from src.domain.ports import ISLMHealer, PolyglotHealResult, SLMHealResult


class MockPolyglotSLMHealer(ISLMHealer):
    """Mock determinístico para auto-sanación con SLM en tests."""

    def repair_syntax(self, file_path: str, code: str, syntax_error: str) -> SLMHealResult:
        if file_path.endswith(".php"):
            repaired = "<?php\nfunction broken(): int {\n    return 42;\n}\n"
        elif file_path.endswith(".ts"):
            repaired = "interface User {\n    id: number;\n    name: string;\n}\n"
        elif file_path.endswith(".js"):
            repaired = "function calculateTotal(a, b) {\n    return a + b;\n}\n"
        else:
            repaired = code

        return SLMHealResult(
            success=True,
            file_path=file_path,
            repaired_code=repaired,
            tokens_used=25,
            execution_time_ms=18.0,
        )


class TestPolyglotHealer(unittest.TestCase):
    """Pruebas unitarias para la auto-sanación local multinivel en PHP, JS y TS."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.slm_mock = MockPolyglotSLMHealer()
        self.healer = PolyglotHardwareHealer(slm_healer=self.slm_mock)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_heal_php_syntax_error_with_slm(self) -> None:
        """Verifica la reparación en iGPU de un archivo PHP con sintaxis rota."""
        php_file = Path(self.temp_dir) / "broken.php"
        php_file.write_text("<?php\nfunction broken(\n    return 42;\n", encoding="utf-8")

        result: PolyglotHealResult = self.healer.heal_file(str(php_file))
        self.assertTrue(result.success)
        self.assertEqual(result.language, "php")
        self.assertIn("slm_repaired_php", result.actions_applied)

        content = php_file.read_text(encoding="utf-8")
        self.assertIn("function broken(): int", content)

    def test_heal_javascript_syntax_error_with_slm(self) -> None:
        """Verifica la reparación en iGPU de un archivo JavaScript con SyntaxError."""
        js_file = Path(self.temp_dir) / "broken.js"
        js_file.write_text("function calculateTotal(a, b {\n    return a + b;\n", encoding="utf-8")

        result: PolyglotHealResult = self.healer.heal_file(str(js_file))
        self.assertTrue(result.success)
        self.assertEqual(result.language, "javascript")
        self.assertIn("slm_repaired_js", result.actions_applied)

        content = js_file.read_text(encoding="utf-8")
        self.assertIn("function calculateTotal(a, b)", content)

    def test_heal_typescript_syntax_error_with_slm(self) -> None:
        """Verifica la reparación en iGPU de un archivo TypeScript con llaves rotas."""
        ts_file = Path(self.temp_dir) / "broken.ts"
        ts_file.write_text("interface User {\n    id: number;\n    name: string;\n", encoding="utf-8")

        result: PolyglotHealResult = self.healer.heal_file(str(ts_file))
        self.assertTrue(result.success)
        self.assertEqual(result.language, "typescript")
        self.assertIn("slm_repaired_ts", result.actions_applied)

        content = ts_file.read_text(encoding="utf-8")
        self.assertIn("interface User {", content)
        self.assertIn("}", content)

    def test_polyglot_l1_deterministic_formatting(self) -> None:
        """Verifica que archivos sintácticamente correctos en JS se validen correctamente."""
        clean_js = Path(self.temp_dir) / "valid.js"
        clean_js.write_text("const a = 1;\nconst b = 2;\n", encoding="utf-8")

        result: PolyglotHealResult = self.healer.heal_file(str(clean_js))
        self.assertTrue(result.success)
        self.assertIn("syntax_valid_js", result.actions_applied)


if __name__ == "__main__":
    unittest.main()

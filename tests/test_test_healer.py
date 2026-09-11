"""Tests unitarios para la auto-sanación de fallos de tests asistida por LLM local en CPU/iGPU."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.adapters.test_healer import OllamaTestFailureHealer
from src.domain.ports import IASTPruner, TestFailureDetail, TestHealResult


class TestOllamaTestFailureHealer(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_ast_pruner = MagicMock(spec=IASTPruner)
        self.healer = OllamaTestFailureHealer(
            ast_pruner=self.mock_ast_pruner,
            endpoint_url="http://localhost:11434/api/generate",
            model_name="qwen2.5-coder:1.5b",
            max_attempts=2,
        )

    def test_isolate_failure_standard_pytest_output(self) -> None:
        """Verifica la extracción y poda de un fallo típico de pytest local."""
        raw_output = """
=================================== FAILURES ===================================
___________________________ test_calculate_discount ___________________________

    def test_calculate_discount():
>       assert calculate_discount(100, 0.2) == 80.0

src/calculator.py:15: in calculate_discount
    return price - (price * discount * 2)
E   AssertionError: assert 60.0 == 80.0

tests/test_calculator.py:8: AssertionError
=========================== short test summary info ============================
FAILED tests/test_calculator.py::test_calculate_discount - AssertionError: assert 60.0 == 80.0
============================== 1 failed in 0.05s ===============================
"""
        detail = self.healer.isolate_failure(raw_output)

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.test_file, "tests/test_calculator.py")
        self.assertEqual(detail.test_name, "test_calculate_discount")
        self.assertEqual(detail.target_file, "src/calculator.py")
        self.assertEqual(detail.error_line, 15)
        self.assertIn("AssertionError: assert 60.0 == 80.0", detail.error_message)
        self.assertIn("src/calculator.py:15", detail.traceback_snippet)
        self.assertNotIn("==== short test summary info ====", detail.traceback_snippet)

    def test_isolate_failure_ci_log_with_timestamps(self) -> None:
        """Verifica la poda cuando el log proviene de gh run view con timestamps RFC3339."""
        ci_log = """
2026-09-11T13:00:00.1234567Z Run pytest -q
2026-09-11T13:00:01.2345678Z =================================== FAILURES ===================================
2026-09-11T13:00:01.3456789Z ________________________________ test_validate_token ________________________________
2026-09-11T13:00:01.4567890Z     def test_validate_token():
2026-09-11T13:00:01.5678901Z >       assert validate_token("bad") is True
2026-09-11T13:00:01.6789012Z src/auth/validator.py:42: in validate_token
2026-09-11T13:00:01.7890123Z >       raise ValueError("Invalid format")
2026-09-11T13:00:01.8901234Z E   ValueError: Invalid format
2026-09-11T13:00:01.9012345Z tests/auth/test_validator.py:12: ValueError
2026-09-11T13:00:02.0123456Z =========================== short test summary info ============================
2026-09-11T13:00:02.1234567Z FAILED tests/auth/test_validator.py::test_validate_token - ValueError: Invalid format
"""
        detail = self.healer.isolate_failure(ci_log)

        self.assertIsNotNone(detail)
        assert detail is not None
        self.assertEqual(detail.test_file, "tests/auth/test_validator.py")
        self.assertEqual(detail.test_name, "test_validate_token")
        self.assertEqual(detail.target_file, "src/auth/validator.py")
        self.assertEqual(detail.error_line, 42)
        self.assertIn("ValueError: Invalid format", detail.error_message)
        self.assertNotIn("2026-09-11T", detail.traceback_snippet)

    def test_isolate_failure_clean_output_returns_none(self) -> None:
        """Si la salida no contiene fallos de test, debe retornar None determinísticamente."""
        clean_output = ".......\n7 passed in 0.12s\n"
        detail = self.healer.isolate_failure(clean_output)
        self.assertIsNone(detail)

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_heal_test_failure_success_first_attempt(self, mock_run: MagicMock, mock_urlopen: MagicMock) -> None:
        """Verifica la reparación exitosa de un componente en el primer intento."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = os.path.join(tmp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            target_path = os.path.join(src_dir, "calculator.py")

            original_code = "def calculate_discount(price: float, discount: float) -> float:\n    return price - (price * discount * 2)\n"
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(original_code)

            detail = TestFailureDetail(
                test_file="tests/test_calculator.py",
                test_name="test_calculate_discount",
                target_file="src/calculator.py",
                error_line=2,
                error_message="AssertionError: assert 60.0 == 80.0",
                traceback_snippet="return price - (price * discount * 2)\nE   AssertionError: assert 60.0 == 80.0",
            )

            repaired_code = "def calculate_discount(price: float, discount: float) -> float:\n    return price - (price * discount)\n"
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"response": f"```python\n{repaired_code}```"}).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            mock_run.return_value = MagicMock(returncode=0, stdout="1 passed", stderr="")

            result: TestHealResult = self.healer.heal_test_failure(detail, repo_dir=tmp_dir)

            self.assertTrue(result.success)
            self.assertEqual(result.attempts, 1)
            with open(target_path, "r", encoding="utf-8") as f:
                saved_code = f.read()
            self.assertIn("price - (price * discount)", saved_code)

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_heal_test_failure_reverts_on_unsuccessful_attempts(
        self, mock_run: MagicMock, mock_urlopen: MagicMock
    ) -> None:
        """Si tras agotar intentos el test sigue fallando, restaura el archivo original y reporta fallo."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = os.path.join(tmp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            target_path = os.path.join(src_dir, "broken.py")

            original_code = "def buggy() -> int:\n    return 0\n"
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(original_code)

            detail = TestFailureDetail(
                test_file="tests/test_broken.py",
                test_name="test_buggy",
                target_file="src/broken.py",
                error_line=2,
                error_message="AssertionError: assert 0 == 1",
                traceback_snippet="assert buggy() == 1",
            )

            bad_repaired = "def buggy() -> int:\n    return 999\n"
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"response": bad_repaired}).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            def fake_run(cmd: list[str], **kwargs) -> MagicMock:
                if "pytest" in cmd:
                    return MagicMock(returncode=1, stdout="FAILED test_buggy", stderr="")
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = fake_run

            result: TestHealResult = self.healer.heal_test_failure(detail, repo_dir=tmp_dir)

            self.assertFalse(result.success)
            self.assertEqual(result.attempts, 2)
            with open(target_path, "r", encoding="utf-8") as f:
                current_code = f.read()
            self.assertEqual(current_code, original_code)

    def test_prepare_component_code_selective_ast_prune(self) -> None:
        """Verifica que para archivos largos se preserve el cuerpo de la función afectada y se poden las demás."""
        lines = ["# Módulo grande de prueba"]
        for i in range(40):
            lines.append(f"def func_{i}(x: int) -> int:\n    '''Docstring {i}'''\n    return x + {i}\n")

        # La función afectada es func_15 (aproximadamente en la línea 60)
        source = "\n".join(lines)
        self.assertGreater(len(source.splitlines()), 120)

        # Encontrar la línea de func_15
        func_15_line = 0
        for idx, line in enumerate(source.splitlines(), start=1):
            if "def func_15" in line:
                func_15_line = idx
                break

        pruned = self.healer._prepare_component_code(source, error_line=func_15_line + 2)

        # func_15 debe conservar 'return x + 15'
        self.assertIn("return x + 15", pruned)
        # Otras funciones deben haberse esqueletizado con 'pass'
        self.assertIn("pass", pruned)
        self.assertNotIn("return x + 0", pruned)

    @patch("urllib.request.urlopen")
    def test_heal_test_failure_ollama_connection_error(self, mock_urlopen: MagicMock) -> None:
        """Verifica que ante fallo de conexión con Ollama, no se corrompa el código y se reporte el error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_dir = os.path.join(tmp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)
            target_path = os.path.join(src_dir, "calc.py")

            original_code = "def calc() -> int:\n    return 42\n"
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(original_code)

            detail = TestFailureDetail(
                test_file="tests/test_calc.py",
                test_name="test_calc",
                target_file="src/calc.py",
                error_line=2,
                error_message="Error",
                traceback_snippet="Traceback",
            )

            mock_urlopen.side_effect = Exception("Connection refused to Ollama")

            result: TestHealResult = self.healer.heal_test_failure(detail, repo_dir=tmp_dir)

            self.assertFalse(result.success)
            with open(target_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), original_code)


if __name__ == "__main__":
    unittest.main()

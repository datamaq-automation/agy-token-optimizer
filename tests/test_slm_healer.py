"""Pruebas unitarias para el adaptador de auto-sanación con SLM en iGPU."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.adapters.slm_healer import OllamaVulkanSLMHealer, _clean_code_fences
from src.domain.ports import SLMHealResult


class TestOllamaVulkanSLMHealer(unittest.TestCase):
    """Pruebas unitarias para OllamaVulkanSLMHealer y funciones auxiliares de limpieza."""

    def test_clean_code_fences_with_markdown(self) -> None:
        raw_text = "```python\ndef foo() -> int:\n    return 1\n```"
        cleaned = _clean_code_fences(raw_text)
        self.assertEqual(cleaned, "def foo() -> int:\n    return 1")

    def test_clean_code_fences_without_markdown(self) -> None:
        raw_text = "def foo() -> int:\n    return 1"
        cleaned = _clean_code_fences(raw_text)
        self.assertEqual(cleaned, "def foo() -> int:\n    return 1")

    @patch("urllib.request.urlopen")
    def test_repair_syntax_success(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "response": "```python\ndef greet() -> str:\n    return 'hola'\n```",
                "eval_count": 20,
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        healer = OllamaVulkanSLMHealer()
        result: SLMHealResult = healer.repair_syntax(
            file_path="dummy.py",
            code="def greet(\n",
            syntax_error="SyntaxError: unexpected EOF",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.repaired_code, "def greet() -> str:\n    return 'hola'")
        self.assertEqual(result.tokens_used, 20)
        self.assertIsNone(result.error_message)

    @patch("urllib.request.urlopen")
    def test_repair_syntax_connection_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = ConnectionRefusedError("Ollama daemon down")

        healer = OllamaVulkanSLMHealer()
        result: SLMHealResult = healer.repair_syntax(
            file_path="dummy.py",
            code="def broken():\n",
            syntax_error="SyntaxError: expected block",
        )

        self.assertFalse(result.success)
        self.assertIn("Ollama daemon down", str(result.error_message))
        self.assertEqual(result.repaired_code, "def broken():\n")


if __name__ == "__main__":
    unittest.main()

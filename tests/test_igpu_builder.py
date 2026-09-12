"""tests/test_igpu_builder.py: Pruebas unitarias para el constructor de código en iGPU local."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.adapters.igpu_builder import OllamaVulkanCodeBuilder
from src.domain.ports import CodeBuildResult


class TestOllamaVulkanCodeBuilder(unittest.TestCase):
    """Suite de pruebas para OllamaVulkanCodeBuilder sobre iGPU Vulkan."""

    def setUp(self) -> None:
        self.builder = OllamaVulkanCodeBuilder(
            base_url="http://localhost:11434",
            default_model="qwen2.5-coder:7b",
            timeout_s=30,
        )

    @patch("urllib.request.urlopen")
    def test_build_implementation_success(self, mock_urlopen: MagicMock) -> None:
        """Verifica generación exitosa de código y extracción limpia sin markdown fences."""
        raw_llm_response = (
            "```python\ndef calculate_total(price: float, tax: float) -> float:\n    return price + (price * tax)\n```"
        )
        fake_response = {
            "model": "qwen2.5-coder:7b",
            "response": raw_llm_response,
            "eval_count": 42,
            "done": True,
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result: CodeBuildResult = self.builder.build_implementation(
            spec_summary="Calcular total con impuestos",
            contract_signatures="def calculate_total(price: float, tax: float) -> float: ...",
            test_content="assert calculate_total(100.0, 0.21) == 121.0",
            target_file_path="src/domain/calculator.py",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.model_used, "qwen2.5-coder:7b")
        self.assertEqual(result.raw_tokens, 42)
        self.assertIn("def calculate_total", result.code)
        self.assertNotIn("```", result.code)
        self.assertIsNone(result.error_message)
        self.assertIsNotNone(result.trace_id)
        self.assertGreater(result.tokens_per_second, 0.0)

    @patch("urllib.request.urlopen")
    def test_build_implementation_custom_model(self, mock_urlopen: MagicMock) -> None:
        """Verifica que el modelo alternativo se pase correctamente en el payload."""
        fake_response = {
            "model": "qwen2.5-coder:1.5b",
            "response": "def quick() -> None:\n    pass",
            "eval_count": 10,
            "done": True,
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result: CodeBuildResult = self.builder.build_implementation(
            spec_summary="Función rápida",
            contract_signatures="def quick() -> None: ...",
            test_content="quick()",
            target_file_path="src/domain/quick.py",
            model_name="qwen2.5-coder:1.5b",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.model_used, "qwen2.5-coder:1.5b")
        # Verificar payload enviado
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        sent_payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(sent_payload["model"], "qwen2.5-coder:1.5b")

    @patch("urllib.request.urlopen")
    def test_build_implementation_connection_error(self, mock_urlopen: MagicMock) -> None:
        """Verifica manejo controlado cuando Ollama no responde o hay fallo de red local."""
        mock_urlopen.side_effect = ConnectionRefusedError("Connection to localhost:11434 refused")

        result: CodeBuildResult = self.builder.build_implementation(
            spec_summary="Fallo de conexión",
            contract_signatures="",
            test_content="",
            target_file_path="src/domain/fail.py",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.code, "")
        self.assertEqual(result.raw_tokens, 0)
        self.assertIsNotNone(result.error_message)
        self.assertIn("refused", str(result.error_message))

    @patch("urllib.request.urlopen")
    def test_build_implementation_empty_response(self, mock_urlopen: MagicMock) -> None:
        """Verifica manejo cuando Ollama responde exitoso pero con cuerpo vacío."""
        fake_response = {
            "model": "qwen2.5-coder:7b",
            "response": "",
            "eval_count": 0,
            "done": True,
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        result: CodeBuildResult = self.builder.build_implementation(
            spec_summary="Respuesta vacía",
            contract_signatures="",
            test_content="",
            target_file_path="src/domain/empty.py",
        )

        self.assertFalse(result.success)
        self.assertIn("Respuesta vacía", str(result.error_message))


if __name__ == "__main__":
    unittest.main()

"""Adaptador de auto-sanación de 2º nivel asistido por SLM en hardware local (iGPU Vulkan).

Utiliza qwen2.5-coder:1.5b alojado en VRAM en la iGPU Radeon Vega 11 via Ollama (localhost:11434)
para reparar SyntaxErrors complejos cuando los linters determinísticos (Ruff) no pueden resolverlos.
"""

import ast
import json
import re
import time
import urllib.request

from src.domain.ports import ISLMHealer, SLMHealResult


def _clean_code_fences(text: str) -> str:
    """Elimina delimitadores markdown de código si el modelo los genera."""
    cleaned = text.strip()
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    return cleaned


class OllamaVulkanSLMHealer(ISLMHealer):
    """Implementación de auto-sanación local con Qwen 2.5 Coder 1.5B en iGPU."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:11434/api/generate",
        model_name: str = "qwen2.5-coder:1.5b",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def repair_syntax(self, file_path: str, code: str, syntax_error: str) -> SLMHealResult:
        """Repara errores sintácticos mediante inferencia local en la iGPU Vulkan."""
        start_time = time.perf_counter()

        prompt = (
            f"Repara el siguiente error sintáctico en Python.\n"
            f"Error: {syntax_error}\n"
            f"Devuelve EXCLUSIVAMENTE el código Python reparado y válido, sin explicaciones ni markdown:\n\n"
            f"{code}\n"
        )

        payload = json.dumps(
            {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 1024,
                },
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_response: str = data.get("response", "")
                eval_count: int = data.get("eval_count", 0)

            repaired_code = _clean_code_fences(raw_response)

            # Validar que el código reparado tenga sintaxis válida
            ast.parse(repaired_code, filename=file_path)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return SLMHealResult(
                success=True,
                file_path=file_path,
                repaired_code=repaired_code,
                tokens_used=eval_count,
                execution_time_ms=elapsed_ms,
                error_message=None,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return SLMHealResult(
                success=False,
                file_path=file_path,
                repaired_code=code,
                tokens_used=0,
                execution_time_ms=elapsed_ms,
                error_message=str(exc),
            )

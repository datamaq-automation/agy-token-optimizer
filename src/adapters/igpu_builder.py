"""src/adapters/igpu_builder.py: Adaptador de generación de código en hardware local (iGPU Vulkan).

Consume Ollama en localhost:11434 ejecutando qwen2.5-coder:7b o 1.5b sobre backend Vulkan.
"""

import json
import re
import time
import urllib.error
import urllib.request
import uuid
from typing import Optional

from src.domain.ports import CodeBuildResult, ILocalCodeBuilder


def _clean_code_fences(raw_text: str) -> str:
    """Remueve delimitadores markdown de código (```python ... ```) y espacios residuales."""
    text = raw_text.strip()
    # Buscar bloque de código cercado
    match = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Si empieza con ``` pero no tiene cierre
    if text.startswith("```"):
        lines = text.splitlines()
        first_line = lines[0]
        if "```" in first_line:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    return text


class OllamaVulkanCodeBuilder(ILocalCodeBuilder):
    """Implementación de generación de código asistida por Ollama en iGPU Vulkan."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "qwen2.5-coder:7b",
        timeout_s: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout_s = timeout_s

    def build_implementation(
        self,
        spec_summary: str,
        contract_signatures: str,
        test_content: str,
        target_file_path: str,
        model_name: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> CodeBuildResult:
        """Genera el código fuente de implementación usando Ollama en iGPU local."""
        model = model_name or self.default_model
        active_trace_id = trace_id or uuid.uuid4().hex[:12]
        start_time = time.perf_counter()

        system_prompt = (
            "Eres un programador senior experto en Python, Clean Architecture y tipado estricto. "
            "Tu tarea es generar el código fuente exacto para satisfacer la especificación y los tests provistos. "
            "Reglas inmutables:\n"
            "1. Imports 100% absolutos (ej. 'from src.domain.ports import ...').\n"
            "2. Tipado estricto al 100% en argumentos y retornos.\n"
            "3. Devuelve ÚNICAMENTE el código fuente en Python, sin explicaciones ni saludos."
        )

        user_prompt_lines = [
            f"# Destino: {target_file_path}",
            f"# Especificación: {spec_summary}",
        ]
        if contract_signatures:
            user_prompt_lines.extend(
                [
                    "",
                    "# Contratos e Interfaces Relevantes:",
                    contract_signatures,
                ]
            )
        if test_content:
            user_prompt_lines.extend(
                [
                    "",
                    "# Pruebas que deben pasar (TDD):",
                    test_content,
                ]
            )
        user_prompt_lines.extend(
            [
                "",
                "# Escribe el código fuente completo del archivo objetivo a continuación:",
            ]
        )
        user_prompt = "\n".join(user_prompt_lines)

        payload_dict = {
            "model": model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.95,
            },
        }

        endpoint = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload_dict).encode("utf-8"),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_response = data.get("response", "").strip()
                raw_tokens = int(data.get("eval_count", 0))

                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                tps = (raw_tokens / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0

                if not raw_response:
                    return CodeBuildResult(
                        code="",
                        model_used=model,
                        raw_tokens=0,
                        success=False,
                        execution_time_ms=elapsed_ms,
                        error_message="Respuesta vacía recibida desde Ollama",
                        trace_id=active_trace_id,
                        tokens_per_second=round(tps, 2),
                    )

                clean_code = _clean_code_fences(raw_response)
                return CodeBuildResult(
                    code=clean_code,
                    model_used=model,
                    raw_tokens=raw_tokens,
                    success=True,
                    execution_time_ms=elapsed_ms,
                    error_message=None,
                    trace_id=active_trace_id,
                    tokens_per_second=round(tps, 2),
                )

        except urllib.error.URLError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return CodeBuildResult(
                code="",
                model_used=model,
                raw_tokens=0,
                success=False,
                execution_time_ms=elapsed_ms,
                error_message=f"Error de red/conexión con Ollama ({endpoint}): {e.reason if hasattr(e, 'reason') else e}",
                trace_id=active_trace_id,
                tokens_per_second=0.0,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return CodeBuildResult(
                code="",
                model_used=model,
                raw_tokens=0,
                success=False,
                execution_time_ms=elapsed_ms,
                error_message=f"Excepción no esperada al invocar Ollama: {e}",
                trace_id=active_trace_id,
                tokens_per_second=0.0,
            )

"""Adaptador para auto-sanación de fallos en tests unitarios asistido por LLM local (Ollama).

Aísla trazas de fallos de pytest y CI, poda el código del componente preservando
el contexto de la función afectada, y solicita a qwen2.5-coder:1.5b en iGPU local
la reparación del componente a costo $0 tokens de API.
"""

import ast
import json
import os
import re
import subprocess
import time
import urllib.request
from typing import Optional

from src.domain.ports import IASTPruner, ITestFailureHealer, TestFailureDetail, TestHealResult


def _clean_code_fences(text: str) -> str:
    """Elimina delimitadores markdown de código si el modelo los genera."""
    cleaned = text.strip()
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    return cleaned


class _SelectiveBodyPruner(ast.NodeTransformer):
    """Esqueletiza funciones no involucradas en el fallo, preservando la función objetivo."""

    def __init__(self, target_line: int) -> None:
        self.target_line = target_line

    def _should_preserve(self, node: ast.AST) -> bool:
        start_line = getattr(node, "lineno", 0)
        end_line = getattr(node, "end_lineno", start_line)
        return start_line <= self.target_line <= end_line

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if self._should_preserve(node):
            return self.generic_visit(node)
        docstring = ast.get_docstring(node)
        new_body: list[ast.stmt] = []
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        new_body.append(ast.Pass())
        node.body = new_body
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        if self._should_preserve(node):
            return self.generic_visit(node)
        docstring = ast.get_docstring(node)
        new_body: list[ast.stmt] = []
        if docstring:
            new_body.append(ast.Expr(value=ast.Constant(value=docstring)))
        new_body.append(ast.Pass())
        node.body = new_body
        return node


class OllamaTestFailureHealer(ITestFailureHealer):
    """Implementación de auto-sanación de fallos de tests con Ollama en hardware local."""

    def __init__(
        self,
        ast_pruner: Optional[IASTPruner] = None,
        endpoint_url: str = "http://localhost:11434/api/generate",
        model_name: str = "qwen2.5-coder:1.5b",
        timeout_seconds: float = 12.0,
        max_attempts: int = 2,
    ) -> None:
        self._ast_pruner = ast_pruner
        self._endpoint_url = endpoint_url
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max(1, max_attempts)

    def isolate_failure(self, failure_output: str, repo_dir: str = ".") -> Optional[TestFailureDetail]:
        """Aísla y poda el traceback de una salida de pytest o logs de CI a los datos esenciales."""
        # 1. Limpieza de secuencias ANSI y timestamps de CI
        clean_text = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", failure_output)
        clean_lines: list[str] = []
        for line in clean_text.splitlines():
            # Quitar timestamp RFC3339 de GitHub Actions (ej: 2026-09-11T13:00:00.1234567Z )
            un_timestamped = re.sub(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*", "", line)
            clean_lines.append(un_timestamped)

        full_clean = "\n".join(clean_lines)

        # 2. Detectar si hubo fallo de tests
        if "FAILURES" not in full_clean and "FAILED " not in full_clean:
            return None

        test_file: str = ""
        test_name: str = ""
        error_message: str = ""

        # Extraer del resumen FAILED tests/foo.py::test_bar - Error: ...
        failed_match = re.search(r"FAILED\s+([^\s:]+\.py)::([^\s\-]+)(?:\s*-\s*(.+))?", full_clean)
        if failed_match:
            test_file = failed_match.group(1).strip()
            test_name = failed_match.group(2).strip()
            if failed_match.group(3):
                error_message = failed_match.group(3).strip()

        # Si no hubo resumen, buscar bloque _________________ test_name _________________
        if not test_name:
            block_match = re.search(r"_{3,}\s*([a-zA-Z0-9_]+)\s*_{3,}", full_clean)
            if block_match:
                test_name = block_match.group(1)

        # 3. Extraer trazas del bloque de fallo
        snippet_lines: list[str] = []
        target_file: str = ""
        error_line: Optional[int] = None
        in_failure_block = False

        for line in clean_lines:
            if "___" in line and test_name and test_name in line:
                in_failure_block = True
                continue
            if in_failure_block:
                if line.startswith("===") or line.startswith("FAILED "):
                    break
                snippet_lines.append(line)

                # Detectar frame del componente
                frame_match = re.search(r"^([a-zA-Z0-9_\-\./]+\.py):(\d+):", line.strip())
                if frame_match:
                    fpath = frame_match.group(1)
                    fline = int(frame_match.group(2))
                    if fpath.startswith("src/"):
                        target_file = fpath
                        error_line = fline
                    elif not target_file and not fpath.startswith("tests/"):
                        target_file = fpath
                        error_line = fline

                if not error_message and line.strip().startswith("E   "):
                    error_message = line.strip()[4:].strip()

        # Si no se encontró frame en src/, intentar resolver por test_file
        if not target_file:
            if test_file:
                target_file = test_file
            else:
                target_file = "src/"

        if not error_message:
            error_message = "Test assertion failed"

        # Reducir el snippet a un máximo de 25 líneas para preservar tokens
        trimmed_snippet = "\n".join(snippet_lines[:25]).strip()

        return TestFailureDetail(
            test_file=test_file,
            test_name=test_name,
            target_file=target_file,
            error_line=error_line,
            error_message=error_message,
            traceback_snippet=trimmed_snippet,
        )

    def _prepare_component_code(self, source_code: str, error_line: Optional[int]) -> str:
        """Prepara una vista ultracompacta del código fuente podando funciones no afectadas."""
        lines = source_code.splitlines()
        if len(lines) <= 120 or error_line is None:
            return source_code

        try:
            tree = ast.parse(source_code)
            transformer = _SelectiveBodyPruner(target_line=error_line)
            pruned_tree = transformer.visit(tree)
            ast.fix_missing_locations(pruned_tree)
            return ast.unparse(pruned_tree)
        except Exception:
            return source_code

    def _apply_code_repair(self, original_source: str, candidate_code: str) -> str:
        """Determina si candidate_code es el archivo entero o una función individual."""
        try:
            cand_tree = ast.parse(candidate_code)
        except SyntaxError:
            return original_source

        # Si contiene múltiples definiciones de nivel superior o imports, asumir archivo completo
        if len(cand_tree.body) > 1 or any(
            isinstance(n, (ast.ClassDef, ast.Import, ast.ImportFrom)) for n in cand_tree.body
        ):
            return candidate_code

        # Si es una sola función, verificar si existe en el archivo original para reemplazarla
        if len(cand_tree.body) == 1 and isinstance(cand_tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = cand_tree.body[0]
            func_name = func_node.name

            orig_lines = original_source.splitlines()
            try:
                orig_tree = ast.parse(original_source)
                for node in ast.walk(orig_tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                        start_idx = node.lineno - 1
                        end_idx = getattr(node, "end_lineno", len(orig_lines))
                        new_lines = orig_lines[:start_idx] + candidate_code.splitlines() + orig_lines[end_idx:]
                        return "\n".join(new_lines) + "\n"
            except Exception:
                pass

        return candidate_code

    def heal_test_failure(
        self,
        failure_detail: TestFailureDetail,
        repo_dir: str = ".",
    ) -> TestHealResult:
        """Formula prompt ultracompacto para Ollama, repara el componente y valida la solución."""
        start_time = time.perf_counter()
        target_path = os.path.join(repo_dir, failure_detail.target_file)

        if not os.path.isfile(target_path):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TestHealResult(
                success=False,
                target_file=failure_detail.target_file,
                test_file=failure_detail.test_file,
                repaired_code="",
                attempts=0,
                execution_time_ms=elapsed_ms,
                error_message=f"Archivo objetivo no encontrado: {target_path}",
            )

        with open(target_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        prepared_code = self._prepare_component_code(original_code, failure_detail.error_line)

        last_error = ""
        for attempt in range(1, self._max_attempts + 1):
            prompt = (
                f"Eres un ingeniero experto en Python. Repara el fallo en el componente a costo $0 tokens.\n"
                f"Archivo objetivo: {failure_detail.target_file}\n"
                f"Test fallido: {failure_detail.test_file}::{failure_detail.test_name}\n"
                f"Mensaje de error: {failure_detail.error_message}\n\n"
                f"Traceback puntual:\n{failure_detail.traceback_snippet}\n\n"
                f"Código actual del componente:\n{prepared_code}\n\n"
                f"Instrucción estricta: Devuelve EXCLUSIVAMENTE el código Python reparado para el archivo o la función, "
                f"válido sintácticamente, sin explicaciones ni bloques de texto conversacional."
            )

            payload = json.dumps(
                {
                    "model": self._model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1024,
                    },
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                self._endpoint_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )

            try:
                with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:
                    data = json.loads(resp.read().decode("utf-8"), strict=False)
                    raw_response: str = data.get("response", "")

                cleaned_code = _clean_code_fences(raw_response)
                final_code = self._apply_code_repair(original_code, cleaned_code)

                # Validar sintaxis
                ast.parse(final_code, filename=target_path)

                # Escribir código temporalmente para validación
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(final_code)

                # Auto-formato determinístico local
                subprocess.run(["ruff", "check", "--fix", target_path], cwd=repo_dir, capture_output=True, text=True)
                subprocess.run(["ruff", "format", target_path], cwd=repo_dir, capture_output=True, text=True)

                # Validar suite local de tests sobre el archivo de test
                test_cmd = ["pytest", "-q"]
                if failure_detail.test_file:
                    test_cmd.append(failure_detail.test_file)

                test_res = subprocess.run(test_cmd, cwd=repo_dir, capture_output=True, text=True)
                if test_res.returncode == 0:
                    with open(target_path, "r", encoding="utf-8") as f:
                        saved_code = f.read()
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    return TestHealResult(
                        success=True,
                        target_file=failure_detail.target_file,
                        test_file=failure_detail.test_file,
                        repaired_code=saved_code,
                        attempts=attempt,
                        execution_time_ms=elapsed_ms,
                        error_message=None,
                    )
                else:
                    last_error = f"Test falló tras intento {attempt}: {test_res.stdout[:150]}"
            except Exception as exc:
                last_error = f"Excepción en intento {attempt}: {str(exc)}"

        # Si se agotaron los intentos sin éxito, restaurar el archivo original
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(original_code)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return TestHealResult(
            success=False,
            target_file=failure_detail.target_file,
            test_file=failure_detail.test_file,
            repaired_code=original_code,
            attempts=self._max_attempts,
            execution_time_ms=elapsed_ms,
            error_message=last_error or "Tests no pasaron tras reintentos",
        )

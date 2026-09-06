"""Adaptador determinístico de auto-sanación en hardware local (CPU/RAM).

Ejecuta ruff check --fix y ruff format sobre archivos modificados en sub-30ms,
verificando la integridad del árbol de sintaxis abstracta (AST) sin consumo de tokens de API.
"""

import ast
import subprocess
import time
from pathlib import Path

from src.domain.ports import HealResult, IPostEditHealer


class DeterministicHardwareHealer(IPostEditHealer):
    """Implementación de auto-sanación determinística en CPU local."""

    def heal_file(self, target_file: str) -> HealResult:
        start_time = time.perf_counter()
        target_path = Path(target_file)
        actions: list[str] = []

        if not target_path.exists():
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return HealResult(
                success=False,
                file_path=target_file,
                execution_time_ms=elapsed_ms,
                actions_applied=["file_not_found"],
            )

        # 1. Ejecutar Ruff check --fix
        res_fix = subprocess.run(
            ["ruff", "check", "--fix", str(target_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if res_fix.returncode == 0:
            actions.append("ruff_check_fixed")

        # 2. Ejecutar Ruff format
        res_format = subprocess.run(
            ["ruff", "format", str(target_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if res_format.returncode == 0:
            actions.append("ruff_formatted")

        # 3. Validar sintaxis AST
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            ast.parse(content, filename=str(target_path))
            actions.append("ast_syntax_verified")
            success = True
        except SyntaxError:
            actions.append("ast_syntax_error")
            success = False

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return HealResult(
            success=success,
            file_path=target_file,
            execution_time_ms=elapsed_ms,
            actions_applied=actions,
        )

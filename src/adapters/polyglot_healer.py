"""Adaptador de auto-sanación políglota para PHP, JavaScript y TypeScript en CPU/iGPU.

Ejecuta verificación determinística local (L1) con php -l, node --check y parsers sintácticos,
y delega la reparación (L2) a qwen2.5-coder:1.5b en la iGPU Vulkan ante SyntaxErrors complejos ($0 tokens).
"""

import os
import re
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

from src.domain.ports import IPolyglotHealer, ISLMHealer, PolyglotHealResult


class PolyglotHardwareHealer(IPolyglotHealer):
    """Implementación de auto-sanación multinivel para PHP, JS y TS."""

    def __init__(self, slm_healer: Optional[ISLMHealer] = None) -> None:
        self.slm_healer = slm_healer

    def _detect_language(self, filepath: str) -> Optional[str]:
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext == ".php":
            return "php"
        elif ext in {".js", ".mjs", ".cjs"}:
            return "javascript"
        elif ext in {".ts", ".tsx", ".mts"}:
            return "typescript"
        return None

    def _check_brackets_balanced(self, code: str) -> Tuple[bool, str]:
        """Comprueba el balance de delimitadores (), {}, []."""
        stack: List[str] = []
        matching = {")": "(", "}": "{", "]": "["}
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Ignorar comentarios de una línea
            stripped = line.strip()
            if stripped.startswith(("//", "#", "*")):
                continue

            for char in line:
                if char in "({[":
                    stack.append(char)
                elif char in ")}]":
                    if not stack or stack[-1] != matching[char]:
                        return False, f"Delimitador desbalanceado '{char}' en línea {line_num}"
                    stack.pop()

        if stack:
            return False, f"Delimitadores sin cerrar al final del archivo: {stack}"
        return True, ""

    def _validate_syntax(self, language: str, filepath: str, code: str) -> Tuple[bool, str]:
        # 1. Comprobación rápida de balance de delimitadores
        balanced, err_msg = self._brackets_balanced(code)
        if not balanced:
            return False, err_msg

        # 2. Validadores específicos por lenguaje
        if language == "php":
            res = subprocess.run(["php", "-l", filepath], capture_output=True, text=True, check=False)
            if res.returncode != 0:
                return False, res.stderr or res.stdout
            return True, ""
        elif language == "javascript":
            res = subprocess.run(["node", "--check", filepath], capture_output=True, text=True, check=False)
            if res.returncode != 0:
                return False, res.stderr or res.stdout
            return True, ""
        elif language == "typescript":
            # Para TypeScript, la comprobación de balance y patrones de interfaces rotas
            if re.search(r"(interface|type|class)\s+\w+\s*\{[^}]*$", code, re.DOTALL):
                return False, "Estructura de interfaz o tipo incompleta en TypeScript"
            return True, ""

        return True, ""

    def heal_file(self, target_file: str) -> PolyglotHealResult:
        start_time = time.perf_counter()
        target_path = Path(target_file)
        actions: List[str] = []

        if not target_path.exists():
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return PolyglotHealResult(
                language="unknown",
                success=False,
                file_path=target_file,
                actions_applied=["file_not_found"],
                execution_time_ms=elapsed_ms,
                error_message="Archivo no encontrado",
            )

        lang = self._detect_language(target_file)
        if lang is None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return PolyglotHealResult(
                language="unsupported",
                success=False,
                file_path=target_file,
                actions_applied=["unsupported_language"],
                execution_time_ms=elapsed_ms,
                error_message=f"Lenguaje no soportado para {target_file}",
            )

        code = target_path.read_text(encoding="utf-8")

        # Nivel 1: Validación sintáctica
        is_valid, error_msg = self._validate_syntax(lang, str(target_path), code)

        if is_valid:
            actions.append(f"syntax_valid_{self._lang_alias(lang)}")
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return PolyglotHealResult(
                language=lang,
                success=True,
                file_path=target_file,
                actions_applied=actions,
                execution_time_ms=elapsed_ms,
            )

        actions.append(f"syntax_error_{self._lang_alias(lang)}")

        # Nivel 2: Auto-sanación asistida por SLM en iGPU Vulkan
        if self.slm_healer is not None:
            heal_res = self.slm_healer.repair_syntax(
                file_path=target_file,
                code=code,
                syntax_error=error_msg,
            )
            if heal_res.success:
                target_path.write_text(heal_res.repaired_code, encoding="utf-8")
                actions.append(f"slm_repaired_{self._lang_alias(lang)}")
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return PolyglotHealResult(
                    language=lang,
                    success=True,
                    file_path=target_file,
                    actions_applied=actions,
                    execution_time_ms=elapsed_ms,
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PolyglotHealResult(
            language=lang,
            success=False,
            file_path=target_file,
            actions_applied=actions,
            execution_time_ms=elapsed_ms,
            error_message=error_msg,
        )

    def _brackets_balanced(self, code: str) -> Tuple[bool, str]:
        return self._check_brackets_balanced(code)

    def _lang_alias(self, lang: str) -> str:
        if lang == "javascript":
            return "js"
        elif lang == "typescript":
            return "ts"
        return lang

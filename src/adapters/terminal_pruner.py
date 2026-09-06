"""Adaptador determinístico de compresión y poda de salidas de terminal en CPU.

Filtra trazas de descarga, barras de progreso y avisos no críticos de npm, pip,
composer y pytest, preservando stacktraces de errores, resúmenes y códigos de salida.
"""

import re
from typing import List

from src.domain.ports import ITerminalPruner, TerminalPruneResult


class TerminalOutputPruner(ITerminalPruner):
    """Implementación determinística de compresión de outputs de consola."""

    # Expresiones regulares para líneas puramente ruidosas
    NOISE_PATTERNS = [
        re.compile(r"^\s*npm (warn|notice|info)\b", re.IGNORECASE),
        re.compile(r"^\s*progress bar\b", re.IGNORECASE),
        re.compile(r"\[=+\]", re.IGNORECASE),
        re.compile(r"^\s*-\s+Installing vendor/", re.IGNORECASE),
        re.compile(r"^\s*Loading composer repositories", re.IGNORECASE),
        re.compile(r"^\s*Updating dependencies", re.IGNORECASE),
        re.compile(r"^\s*(Collecting|Downloading|Using cached)\s+", re.IGNORECASE),
    ]

    def _is_noise_line(self, line: str) -> bool:
        return any(pattern.search(line) for pattern in self.NOISE_PATTERNS)

    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult:
        lines: List[str] = output.splitlines()
        original_lines = len(lines)

        if original_lines <= 5:
            return TerminalPruneResult(
                original_lines=original_lines,
                pruned_lines=original_lines,
                exit_code=exit_code,
                clean_output=output,
                reduction_ratio=0.0,
            )

        clean_lines: List[str] = []

        # Caso especial: Pytest con fallos
        if "pytest" in command:
            has_failures = "FAILURES" in output or "FAILED" in output or exit_code != 0
            if has_failures:
                capturing_failure = False
                for line in lines:
                    if "FAILURES" in line or "FAILED" in line or line.startswith("___"):
                        capturing_failure = True
                    if capturing_failure or "===" in line or "AssertionError" in line:
                        clean_lines.append(line)
            else:
                # Todo verde, resumir la masa de líneas
                summary = [line for line in lines if "===" in line]
                clean_lines = [f"[PODADO: {original_lines} tests pasaron sin errores]"] + summary
        else:
            # Filtrado general para npm, pip, composer, etc.
            for line in lines:
                if self._is_noise_line(line):
                    continue
                clean_lines.append(line)

        clean_output = "\n".join(clean_lines)
        pruned_lines = len(clean_lines)

        if original_lines > 0:
            reduction = (original_lines - pruned_lines) / original_lines
            reduction_ratio = max(0.0, round(reduction, 4))
        else:
            reduction_ratio = 0.0

        return TerminalPruneResult(
            original_lines=original_lines,
            pruned_lines=pruned_lines,
            exit_code=exit_code,
            clean_output=clean_output,
            reduction_ratio=reduction_ratio,
        )

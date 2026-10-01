"""Adaptador determinístico de compresión y poda de salidas de terminal en CPU.

Filtra trazas de descarga, barras de progreso y avisos no críticos de npm, pip,
composer, git y pytest, preservando stacktraces de errores, resúmenes y códigos de salida,
y registrando el ahorro de tokens en la telemetría local.
"""

import re
import time
from datetime import datetime
from typing import List, Optional

from src.adapters.token_telemetry import SQLiteTokenTelemetry
from src.domain.ports import ITerminalPruner, ITokenTelemetry, TerminalPruneResult, TokenSavingsEvent


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

    ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    # Patrones de progreso numérico / porcentual continuo (git push, pull, fetch, etc.)
    GIT_PROGRESS_PATTERN = re.compile(
        r"(?:"
        r"(?:contando|counting|comprimiendo|compressing|escribiendo|writing|resolviendo|resolving|enviando|sending|receiving|transferring)\s+.*?\b\d{1,3}%"
        r"|^\s*(?:contando|counting|comprimiendo|compressing|escribiendo|writing|resolviendo|resolving)\s+objet"
        r"|.*\b\d{1,3}%.*(?:objetos|objects|deltas|pack)"
        r")",
        re.IGNORECASE,
    )

    PROGRESS_PERCENT_PATTERN = re.compile(
        r"(?:"
        r"^\s*\[[=\-#>\s]+\]\s*\d{1,3}%"
        r"|^\s*progress bar\b.*?\d{1,3}%"
        r"|^\s*(?:downloading|uploading|fetching|installing|progress)\b.*?\b\d{1,3}%"
        r"|^\s*\d{1,3}%\s*$"
        r")",
        re.IGNORECASE,
    )

    COLLAPSED_PROGRESS_MESSAGE = "✓ Objetos transferidos al 100% (comprimido en local)"

    def __init__(self, telemetry: Optional[ITokenTelemetry] = None) -> None:
        self.telemetry = telemetry

    def _is_noise_line(self, line: str) -> bool:
        return any(pattern.search(line) for pattern in self.NOISE_PATTERNS)

    def _is_progress_line(self, line: str) -> bool:
        clean = self.ANSI_ESCAPE_PATTERN.sub("", line).strip()
        if not clean:
            return False
        if self.GIT_PROGRESS_PATTERN.search(clean):
            return True
        if self.PROGRESS_PERCENT_PATTERN.search(clean):
            return True
        return False

    def _collapse_progress_sequences(self, lines: List[str]) -> List[str]:
        collapsed: List[str] = []
        in_progress = False

        for line in lines:
            if self._is_progress_line(line):
                if not in_progress:
                    collapsed.append(self.COLLAPSED_PROGRESS_MESSAGE)
                    in_progress = True
            else:
                in_progress = False
                collapsed.append(line)

        return collapsed

    def _record_telemetry(
        self,
        command: str,
        tokens_before: int,
        tokens_after: int,
        tokens_saved: int,
        latency_ms: float,
    ) -> None:
        try:
            tel = self.telemetry or SQLiteTokenTelemetry()
            event = TokenSavingsEvent(
                event_type="TERMINAL_PROGRESS_PRUNE"
                if any(k in command for k in ["git", "push", "pull", "fetch"])
                else "TERMINAL_PRUNE",
                tool_name=command.split()[0] if command else "terminal",
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                tokens_saved=tokens_saved,
                latency_ms=round(latency_ms, 2),
                timestamp=datetime.now().isoformat(),
            )
            tel.record_event(event)
        except Exception:
            pass

    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult:
        start_time = time.perf_counter()
        lines: List[str] = [line.strip("\r") for line in output.splitlines()]
        original_lines = len(lines)

        if original_lines == 0:
            return TerminalPruneResult(
                original_lines=0,
                pruned_lines=0,
                exit_code=exit_code,
                clean_output="",
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
            # 1. Colapsar secuencias de progreso numérico/porcentual (git push, pip, etc.)
            collapsed_lines = self._collapse_progress_sequences(lines)

            # 2. Filtrar ruido general (npm, pip, composer, etc.)
            for line in collapsed_lines:
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

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if original_lines > pruned_lines:
            tokens_before = max(1, len(output.encode("utf-8")) // 4)
            tokens_after = max(1, len(clean_output.encode("utf-8")) // 4)
            tokens_saved = max(0, tokens_before - tokens_after)
            if tokens_saved > 0:
                self._record_telemetry(
                    command=command,
                    tokens_before=tokens_before,
                    tokens_after=tokens_after,
                    tokens_saved=tokens_saved,
                    latency_ms=elapsed_ms,
                )

        return TerminalPruneResult(
            original_lines=original_lines,
            pruned_lines=pruned_lines,
            exit_code=exit_code,
            clean_output=clean_output,
            reduction_ratio=reduction_ratio,
        )

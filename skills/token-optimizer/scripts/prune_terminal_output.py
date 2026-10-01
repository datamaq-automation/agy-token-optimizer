#!/usr/bin/env python3
"""Script CLI de compresión determinística de salidas de terminal en hardware local (CPU).

Filtra trazas de descarga, barras de progreso y avisos no críticos de comandos (npm, pip,
composer, pytest, docker) preservando stacktraces y estados finales, y registra telemetría.
"""

import sys
import time
from datetime import datetime

sys.path.insert(0, "/home/agustin/proyectos_software/agy-token-optimizer")

from src.adapters.terminal_pruner import TerminalOutputPruner
from src.adapters.token_telemetry import SQLiteTokenTelemetry
from src.domain.ports import TerminalPruneResult, TokenSavingsEvent


def main() -> None:
    command_name = sys.argv[1] if len(sys.argv) > 1 else "terminal_command"
    exit_code = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0

    raw_output = sys.stdin.read()
    if not raw_output.strip():
        return

    start_time = time.perf_counter()
    pruner = TerminalOutputPruner()
    result: TerminalPruneResult = pruner.prune_output(command=command_name, output=raw_output, exit_code=exit_code)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    sys.stdout.write(result.clean_output)

    # Registrar telemetría si hubo reducción de líneas
    if result.reduction_ratio > 0.10:
        try:
            tokens_before = max(1, len(raw_output.encode("utf-8")) // 4)
            tokens_after = max(1, len(result.clean_output.encode("utf-8")) // 4)
            tokens_saved = max(0, tokens_before - tokens_after)

            telemetry = SQLiteTokenTelemetry()
            telemetry.record_event(
                TokenSavingsEvent(
                    event_type="TERMINAL_PRUNE",
                    tool_name=command_name.split()[0] if command_name else "terminal",
                    tokens_before=tokens_before,
                    tokens_after=tokens_after,
                    tokens_saved=tokens_saved,
                    latency_ms=elapsed_ms,
                    timestamp=datetime.now().isoformat(),
                )
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()

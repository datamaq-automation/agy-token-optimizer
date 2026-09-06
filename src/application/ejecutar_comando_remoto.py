"""Caso de uso: ejecutar un comando remoto y devolver su salida podada.

Orquesta IRemoteExecutor + ITerminalPruner + ITokenTelemetry por Inyección de
Dependencias. La poda nunca enmascara un fallo: el exit code remoto se preserva.
"""

import time
from datetime import datetime
from typing import Optional

from src.domain.ports import (
    IRemoteExecutor,
    ITerminalPruner,
    ITokenTelemetry,
    RemoteExecutionResult,
    RemoteHost,
    TokenSavingsEvent,
)

# Mismo umbral que compress_diff.py: por debajo, el evento no aporta señal.
UMBRAL_REGISTRO = 0.05

EVENT_TYPE = "VPS_EXEC_PRUNE"
TOOL_NAME = "vps_exec"


class EjecutarComandoRemoto:
    """Ejecuta en el host remoto y poda la salida antes de devolverla al contexto."""

    def __init__(
        self,
        executor: IRemoteExecutor,
        pruner: ITerminalPruner,
        telemetry: Optional[ITokenTelemetry] = None,
    ) -> None:
        self._executor = executor
        self._pruner = pruner
        self._telemetry = telemetry

    def ejecutar(self, command: str, host: RemoteHost, timeout_s: int = 60) -> RemoteExecutionResult:
        inicio = time.perf_counter()
        crudo = self._executor.execute(command, host, timeout_s)

        podado = self._pruner.prune_output(command, crudo.clean_output, crudo.exit_code)
        latencia_ms = (time.perf_counter() - inicio) * 1000.0

        resultado = RemoteExecutionResult(
            exit_code=crudo.exit_code,
            clean_output=podado.clean_output,
            host_used=crudo.host_used,
            timed_out=crudo.timed_out,
            original_lines=podado.original_lines,
            pruned_lines=podado.pruned_lines,
            reduction_ratio=podado.reduction_ratio,
        )

        if self._telemetry is not None and podado.reduction_ratio > UMBRAL_REGISTRO:
            antes = max(1, len(crudo.clean_output) // 4)
            despues = max(1, len(podado.clean_output) // 4)
            self._telemetry.record_event(
                TokenSavingsEvent(
                    event_type=EVENT_TYPE,
                    tool_name=TOOL_NAME,
                    tokens_before=antes,
                    tokens_after=despues,
                    tokens_saved=antes - despues,
                    latency_ms=latencia_ms,
                    timestamp=datetime.now().isoformat(),
                )
            )

        return resultado

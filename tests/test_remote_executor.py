"""Pruebas del ejecutor remoto: fallback de host, preservación de exit code y poda."""

import unittest
from typing import List

from src.adapters.remote_executor import SSHRemoteExecutor
from src.application.ejecutar_comando_remoto import EjecutarComandoRemoto
from src.domain.ports import (
    IRemoteExecutor,
    ITerminalPruner,
    ITokenTelemetry,
    RemoteExecutionResult,
    RemoteHost,
    SavingsSummary,
    TerminalPruneResult,
    TokenSavingsEvent,
)

HOST = RemoteHost(alias="vps", fallback_alias="vps4", port=5932, user="root")


class ProcesoFalso:
    """Sustituto de subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestFallbackDeHost(unittest.TestCase):
    """Escenarios 8, 9 y 11: resolución de host, exit codes y timeout."""

    def setUp(self) -> None:
        self.executor = SSHRemoteExecutor()
        self.invocaciones: List[str] = []

    def _parchear(self, respuestas: dict) -> None:
        import src.adapters.remote_executor as modulo

        def falso_run(argv, **kwargs):
            alias = argv[1]
            self.invocaciones.append(alias)
            return respuestas[alias]

        self._original = modulo.subprocess.run
        modulo.subprocess.run = falso_run

    def tearDown(self) -> None:
        import src.adapters.remote_executor as modulo

        if hasattr(self, "_original"):
            modulo.subprocess.run = self._original

    def test_fallback_ipv6_a_ipv4_ante_red_inalcanzable(self) -> None:
        """Escenario 8: 'Network is unreachable' reintenta con el alias IPv4."""
        self._parchear(
            {
                "vps": ProcesoFalso(255, "", "ssh: connect to host: Network is unreachable"),
                "vps4": ProcesoFalso(0, "ok\n", ""),
            }
        )
        res = self.executor.execute("uptime", HOST)
        self.assertEqual(self.invocaciones, ["vps", "vps4"])
        self.assertEqual(res.host_used, "vps4")
        self.assertEqual(res.exit_code, 0)

    def test_exit_code_remoto_no_dispara_fallback(self) -> None:
        """Escenario 9: un fallo del comando es respuesta legítima, no problema de red."""
        self._parchear({"vps": ProcesoFalso(2, "", "grep: no such file")})
        res = self.executor.execute("grep x /nope", HOST)
        self.assertEqual(self.invocaciones, ["vps"])
        self.assertEqual(res.exit_code, 2)
        self.assertEqual(res.host_used, "vps")

    def test_timeout_devuelve_124(self) -> None:
        """Escenario 11: el timeout se reporta explícitamente y no se confunde con éxito."""
        import subprocess

        import src.adapters.remote_executor as modulo

        def falso_run(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=60)

        self._original = modulo.subprocess.run
        modulo.subprocess.run = falso_run

        res = self.executor.execute("sleep 999", HOST)
        self.assertTrue(res.timed_out)
        self.assertEqual(res.exit_code, 124)


class EjecutorFalso(IRemoteExecutor):
    """Ejecutor que devuelve una salida fija."""

    def __init__(self, salida: str, exit_code: int = 0) -> None:
        self.salida = salida
        self.exit_code = exit_code

    def execute(self, command: str, host: RemoteHost, timeout_s: int = 60) -> RemoteExecutionResult:
        return RemoteExecutionResult(
            exit_code=self.exit_code,
            clean_output=self.salida,
            host_used=host.alias,
        )


class PodadorFalso(ITerminalPruner):
    """Podador con ratio configurable."""

    def __init__(self, ratio: float) -> None:
        self.ratio = ratio

    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult:
        lineas = output.splitlines()
        conservadas = lineas[:10]
        return TerminalPruneResult(
            original_lines=len(lineas),
            pruned_lines=len(conservadas),
            exit_code=exit_code,
            clean_output="\n".join(conservadas),
            reduction_ratio=self.ratio,
        )


class TelemetriaFalsa(ITokenTelemetry):
    """Registra los eventos en memoria."""

    def __init__(self) -> None:
        self.eventos: List[TokenSavingsEvent] = []

    def record_event(self, event: TokenSavingsEvent) -> None:
        self.eventos.append(event)

    def get_summary(self) -> SavingsSummary:
        return SavingsSummary(
            total_tokens_saved=sum(e.tokens_saved for e in self.eventos),
            total_cost_saved_usd=0.0,
            events_count={"VPS_EXEC_PRUNE": len(self.eventos)},
        )

    def get_recent_events(self, limit: int = 10) -> List[TokenSavingsEvent]:
        return self.eventos[-limit:]


class TestPodaYTelemetria(unittest.TestCase):
    """Escenario 10: la poda se delega y la telemetría respeta el umbral."""

    def test_registra_evento_cuando_supera_el_umbral(self) -> None:
        telemetria = TelemetriaFalsa()
        caso = EjecutarComandoRemoto(EjecutorFalso("linea\n" * 500), PodadorFalso(0.9), telemetria)
        res = caso.ejecutar("journalctl -n 500", HOST)
        self.assertEqual(len(telemetria.eventos), 1)
        self.assertEqual(telemetria.eventos[0].event_type, "VPS_EXEC_PRUNE")
        self.assertGreater(telemetria.eventos[0].tokens_saved, 0)
        self.assertEqual(res.pruned_lines, 10)

    def test_no_registra_cuando_la_reduccion_es_marginal(self) -> None:
        """Mismo umbral de 0.05 que compress_diff.py: por debajo no hay señal."""
        telemetria = TelemetriaFalsa()
        caso = EjecutarComandoRemoto(EjecutorFalso("una linea"), PodadorFalso(0.01), telemetria)
        caso.ejecutar("uptime", HOST)
        self.assertEqual(telemetria.eventos, [])

    def test_la_poda_nunca_enmascara_un_fallo(self) -> None:
        """El exit code remoto sobrevive a la poda."""
        caso = EjecutarComandoRemoto(EjecutorFalso("boom\n" * 50, exit_code=1), PodadorFalso(0.8))
        res = caso.ejecutar("systemctl status api", HOST)
        self.assertEqual(res.exit_code, 1)


if __name__ == "__main__":
    unittest.main()

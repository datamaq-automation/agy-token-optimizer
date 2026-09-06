"""Adaptador de ejecución remota por SSH con fallback de familia de direcciones.

El transporte reusa el multiplexado ya configurado en ~/.ssh/config (ControlMaster,
ControlPersist), por lo que no paga handshake por comando. La poda de la salida no
ocurre acá: es responsabilidad del caso de uso, que inyecta un ITerminalPruner.
"""

import re
import subprocess
from typing import List, Tuple

from src.domain.ports import IRemoteExecutor, RemoteExecutionResult, RemoteHost

# Fallos de red que justifican reintentar con la otra familia de direcciones.
_FALLOS_DE_RED = (
    re.compile(r"Network is unreachable", re.IGNORECASE),
    re.compile(r"No route to host", re.IGNORECASE),
    re.compile(r"Could not resolve hostname", re.IGNORECASE),
    re.compile(r"Name or service not known", re.IGNORECASE),
    re.compile(r"Temporary failure in name resolution", re.IGNORECASE),
)

_ANSI = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

EXIT_TIMEOUT = 124


def limpiar_ansi(texto: str) -> str:
    """Elimina secuencias de escape ANSI para no gastar tokens en color."""
    return _ANSI.sub("", texto)


class SSHRemoteExecutor(IRemoteExecutor):
    """Ejecuta comandos remotos por SSH, con un único reintento sobre el alias de fallback."""

    def _invocar(self, alias: str, command: str, timeout_s: int) -> Tuple[int, str, str, bool]:
        argv: List[str] = ["ssh", alias, command]
        try:
            proceso = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return EXIT_TIMEOUT, "", f"Tiempo de espera agotado ({timeout_s}s)", True
        except OSError as error:
            return 1, "", f"Error invocando ssh: {error}", False
        return proceso.returncode, proceso.stdout, proceso.stderr, False

    def _es_fallo_de_red(self, stderr: str) -> bool:
        return any(patron.search(stderr) for patron in _FALLOS_DE_RED)

    def execute(self, command: str, host: RemoteHost, timeout_s: int = 60) -> RemoteExecutionResult:
        codigo, stdout, stderr, expiro = self._invocar(host.alias, command, timeout_s)
        alias_usado = host.alias

        # Sólo un fallo de resolución o de ruta justifica el fallback: un exit code
        # remoto distinto de cero es una respuesta legítima del servidor.
        if not expiro and codigo != 0 and host.fallback_alias and self._es_fallo_de_red(stderr):
            codigo, stdout, stderr, expiro = self._invocar(host.fallback_alias, command, timeout_s)
            alias_usado = host.fallback_alias

        salida = limpiar_ansi(stdout)
        if stderr:
            salida = f"{salida}\n[STDERR]:\n{limpiar_ansi(stderr)}".strip()

        return RemoteExecutionResult(
            exit_code=codigo,
            clean_output=salida,
            host_used=alias_usado,
            timed_out=expiro,
            original_lines=len(salida.splitlines()),
            pruned_lines=len(salida.splitlines()),
            reduction_ratio=0.0,
        )

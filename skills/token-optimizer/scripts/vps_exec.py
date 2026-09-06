#!/usr/bin/env python3
"""vps_exec.py: ejecutor remoto en VPS con poda determinista de salida.

Delega en el caso de uso EjecutarComandoRemoto, que compone el ejecutor SSH (con
fallback IPv6->IPv4), el podador y la telemetria por inyeccion de dependencias.
La poda ya no vive aca: duplicarla era una violacion del reuso y del DIP.

Uso: python3 vps_exec.py "<comando>" [--host vps] [--timeout 60]
"""

import sys
from pathlib import Path

REPO_ROOT = "/home/agustin/proyectos_software/agy-token-optimizer"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SCRIPTS_DIR = Path(__file__).resolve().parent

# Aliases de la misma maquina en distinta familia de direcciones.
FALLBACK_POR_ALIAS = {"vps": "vps4", "vps4": None, "vps-tunnel": "vps4"}


def _parse_args(argv: list) -> tuple:
    if len(argv) < 2:
        print('Uso: python3 vps_exec.py "<comando>" [--host vps] [--timeout 60]')
        raise SystemExit(1)

    comando = argv[1]
    host = "vps"
    timeout = 60
    i = 2
    while i < len(argv):
        if argv[i] == "--host" and i + 1 < len(argv):
            host = argv[i + 1]
            i += 2
        elif argv[i] == "--timeout" and i + 1 < len(argv):
            timeout = int(argv[i + 1])
            i += 2
        else:
            i += 1
    return comando, host, timeout


def main() -> None:
    comando, host, timeout = _parse_args(sys.argv)

    try:
        from src.adapters.remote_executor import SSHRemoteExecutor
        from src.adapters.remote_output_pruner import RemoteOutputPruner
        from src.adapters.token_telemetry import SQLiteTokenTelemetry
        from src.application.ejecutar_comando_remoto import EjecutarComandoRemoto
        from src.domain.ports import RemoteHost
    except ImportError as error:
        print(f"[!] No se pudo cargar la capa de ejecucion remota: {error}")
        raise SystemExit(1) from error

    try:
        telemetria = SQLiteTokenTelemetry()
    except Exception:
        telemetria = None  # La telemetria es opcional: nunca debe impedir la ejecucion.

    caso = EjecutarComandoRemoto(
        executor=SSHRemoteExecutor(),
        pruner=RemoteOutputPruner(),
        telemetry=telemetria,
    )

    destino = RemoteHost(
        alias=host,
        fallback_alias=FALLBACK_POR_ALIAS.get(host),
        port=5932,
        user="root",
    )

    resultado = caso.ejecutar(comando, destino, timeout_s=timeout)

    if resultado.host_used != host:
        print(f"[i] El alias '{host}' no respondio; se uso el fallback '{resultado.host_used}'.")

    print(resultado.clean_output)
    raise SystemExit(resultado.exit_code)


if __name__ == "__main__":
    main()

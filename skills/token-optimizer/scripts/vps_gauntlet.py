#!/usr/bin/env python3
"""vps_gauntlet.py: corre el Gauntlet sobre un proyecto que vive en el VPS.

Ejecuta las etapas en el servidor y devuelve un veredicto de pocas lineas en
lugar de volcar la salida completa al contexto. El detalle solo aparece para las
etapas que fallan, que es lo unico sobre lo que hay que actuar.

Dos trampas que este script evita a proposito:

1. 'cmd | tail' devuelve el codigo de salida de 'tail', no el de 'cmd'. Sin
   'set -o pipefail' toda etapa canalizada reporta exito y el Gauntlet nunca
   puede fallar, que es peor que no tenerlo.
2. Una herramienta ausente en el servidor ('No module named pytest') no es una
   etapa aprobada ni reprobada: es una etapa que no se pudo evaluar, y se
   reporta como tal.

Uso: python3 vps_gauntlet.py <directorio_remoto> [--host vps] [--timeout 300]
"""

import re
import sys
from typing import List, Tuple

REPO_ROOT = "/home/agustin/proyectos_software/agy-token-optimizer"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# (nombre, comando, bloqueante, exito_si_salida_vacia)
ETAPAS: Tuple[Tuple[str, str, bool, bool], ...] = (
    (
        "Integridad __init__",
        "find . -name '__init__.py' -type f -size +0c "
        "-not -path '*/.venv/*' -not -path '*/venv/*' "
        "-not -path '*/site-packages/*' -not -path '*/node_modules/*'",
        False,
        True,
    ),
    ("Estilo (ruff check)", "ruff check .", True, False),
    ("Formato (ruff format)", "ruff format --check .", True, False),
    ("Tipado (pyright)", "pyright", False, False),
    ("Suite (pytest)", "python3 -m pytest -q", True, False),
)

_NO_DISPONIBLE = (
    re.compile(r"No module named", re.IGNORECASE),
    re.compile(r"command not found", re.IGNORECASE),
    re.compile(r"no such file or directory", re.IGNORECASE),
    re.compile(r"not found", re.IGNORECASE),
)

ESTADO_OK = "OK"
ESTADO_FALLA = "FALLA"
ESTADO_AUSENTE = "s/d"


def _clasificar(salida: str, codigo: int, exito_si_vacia: bool) -> str:
    if any(patron.search(salida) for patron in _NO_DISPONIBLE) and codigo != 0:
        return ESTADO_AUSENTE
    if exito_si_vacia:
        return ESTADO_OK if not salida.strip() else ESTADO_FALLA
    return ESTADO_OK if codigo == 0 else ESTADO_FALLA


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 vps_gauntlet.py <directorio_remoto> [--host vps] [--timeout 300]")
        raise SystemExit(1)

    remoto = sys.argv[1]
    host = "vps"
    timeout = 300
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])

    try:
        from src.adapters.remote_executor import SSHRemoteExecutor
        from src.adapters.remote_output_pruner import RemoteOutputPruner
        from src.application.ejecutar_comando_remoto import EjecutarComandoRemoto
        from src.domain.ports import RemoteHost
    except ImportError as error:
        print(f"[!] No se pudo cargar la capa remota: {error}")
        raise SystemExit(1) from error

    caso = EjecutarComandoRemoto(SSHRemoteExecutor(), RemoteOutputPruner(max_lineas=12))
    destino = RemoteHost(alias=host, fallback_alias="vps4" if host == "vps" else None, port=5932, user="root")

    print("=" * 70)
    print(f"GAUNTLET REMOTO | {remoto} @ {host}")
    print("=" * 70)

    fallos = 0
    ausentes: List[str] = []
    for nombre, comando, bloqueante, exito_si_vacia in ETAPAS:
        # 'set -o pipefail' es lo que hace que el codigo de salida sea el del
        # comando y no el del ultimo eslabon de la tuberia.
        remoto_cmd = f"set -o pipefail; cd {remoto} 2>/dev/null || exit 66; {comando}"
        res = caso.ejecutar(remoto_cmd, destino, timeout_s=timeout)

        if res.exit_code == 66:
            print(f"  [{ESTADO_FALLA}] {nombre}: el directorio '{remoto}' no existe en {host}")
            raise SystemExit(1)

        estado = _clasificar(res.clean_output, res.exit_code, exito_si_vacia)
        marca = {ESTADO_OK: "OK   ", ESTADO_FALLA: "FALLA", ESTADO_AUSENTE: " s/d "}[estado]
        print(f"  [{marca}] {nombre}")

        if estado == ESTADO_AUSENTE:
            ausentes.append(nombre)
        elif estado == ESTADO_FALLA:
            for linea in [ln for ln in res.clean_output.splitlines() if ln.strip()][-4:]:
                print(f"         {linea[:150]}")
            if bloqueante:
                fallos += 1

    print("=" * 70)
    if ausentes:
        print(f"Sin evaluar ({len(ausentes)}): {', '.join(ausentes)} — herramienta ausente en {host}.")
    if fallos:
        print(f"GAUNTLET REMOTO NO SUPERADO: {fallos} etapa(s) bloqueante(s) en rojo.")
    else:
        print("GAUNTLET REMOTO SUPERADO" + (" (con etapas sin evaluar)." if ausentes else "."))
    print("=" * 70)
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()

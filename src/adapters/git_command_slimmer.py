"""Adaptador que reescribe comandos git/gh verbosos por su equivalente denso.

Es poda en el origen, no compresión a posteriori: en vez de dejar que el comando
emita 1570 tokens y filtrarlos después, se le pide a git que emita 95. El ahorro
es el mismo texto que nunca se genera.

Reescribe sólo cuando el comando NO trae flags de formato propios: si el agente
pidió un formato explícito, sabe lo que quiere y no se lo toca.
"""

import re
from typing import Optional

# git status completo gasta ~90 tokens en avisos y sugerencias de uso;
# la forma corta con rama gasta ~9 y no pierde información accionable.
_STATUS = re.compile(r"^git\s+status\s*$")

# git log sin acotar vuelca el mensaje completo de cada commit.
_LOG = re.compile(r"^git\s+log\s*(?P<resto>.*)$")
_LOG_YA_ACOTADO = re.compile(r"--oneline|--format|--pretty|-p\b|--stat|--graph|-\d+|-n\s*\d+")

# gh run list sin -L trae 20 filas por defecto.
_GH_RUN_LIST = re.compile(r"^gh\s+run\s+list\s*(?P<resto>.*)$")
_GH_YA_ACOTADO = re.compile(r"-L\s*\d+|--limit\s*\d+|--json")

_GH_PR_LIST = re.compile(r"^gh\s+pr\s+list\s*(?P<resto>.*)$")


def slim(command_line: str) -> Optional[str]:
    """Devuelve la variante densa del comando, o None si no hay nada que reescribir."""
    if not command_line:
        return None

    cmd = command_line.strip()

    # Nunca tocar una línea compuesta: el reemplazo podría alterar la semántica
    # de lo que viene después del operador.
    if any(op in cmd for op in ("&&", "||", ";", "|", ">")):
        return None

    if _STATUS.match(cmd):
        return "git status --short --branch"

    log = _LOG.match(cmd)
    if log:
        resto = log.group("resto").strip()
        if not _LOG_YA_ACOTADO.search(resto):
            return f"git log --oneline -n 20 {resto}".strip()
        return None

    run_list = _GH_RUN_LIST.match(cmd)
    if run_list:
        resto = run_list.group("resto").strip()
        if not _GH_YA_ACOTADO.search(resto):
            return f"gh run list -L 10 {resto}".strip()
        return None

    pr_list = _GH_PR_LIST.match(cmd)
    if pr_list:
        resto = pr_list.group("resto").strip()
        if not _GH_YA_ACOTADO.search(resto):
            return f"gh pr list -L 10 {resto}".strip()
        return None

    return None

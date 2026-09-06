#!/usr/bin/env python3
"""Estado compartido y auditoría para los hooks de gobernanza AGY.

El modo vive en '~/.agents/current_mode' y solo admite dos valores:
  - 'plan'  : Arquitecto SDD, zero-trust perimeter activo.
  - 'build' : Ingeniero de implementación, allowlist en bypass.

Ante cualquier error de lectura o valor desconocido se degrada a 'plan' (fail-safe).

La auditoría escribe una línea por invocación en '~/.agents/gate_audit.log'.
El campo 'src' es el CWD del proceso hook: AGY lo fija al directorio que contiene
el 'hooks.json' que disparó el hook, así que revela QUÉ configuración lo cargó
(y si dos configuraciones lo están cargando por duplicado).
"""

import datetime
import os

AGENTS_DIR = os.path.join(os.path.expanduser("~"), ".agents")
MODE_FILE = os.path.join(AGENTS_DIR, "current_mode")
AUDIT_LOG = os.path.join(AGENTS_DIR, "gate_audit.log")

VALID_MODES = ("plan", "build")
DEFAULT_MODE = "plan"

MAX_LOG_BYTES = 1_000_000
MAX_DETAIL_CHARS = 160


def read_mode() -> str:
    try:
        with open(MODE_FILE, "r", encoding="utf-8") as f:
            mode = f.read().strip().lower()
    except Exception:
        return DEFAULT_MODE
    return mode if mode in VALID_MODES else DEFAULT_MODE


def is_build_mode() -> bool:
    return read_mode() == "build"


def _rotate_if_needed() -> None:
    try:
        if os.path.getsize(AUDIT_LOG) > MAX_LOG_BYTES:
            os.replace(AUDIT_LOG, AUDIT_LOG + ".1")
    except Exception:
        pass


def _clean(value: str) -> str:
    text = " ".join(str(value).split())
    if len(text) > MAX_DETAIL_CHARS:
        text = text[: MAX_DETAIL_CHARS - 1] + "…"
    return text


def audit(hook: str, mode: str, **fields) -> None:
    """Escribe una línea de auditoría. Nunca lanza: la gobernanza no debe caerse por el log."""
    try:
        _rotate_if_needed()
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        try:
            src = os.getcwd()
        except Exception:
            src = "?"
        parts = [stamp, f"hook={hook}", f"mode={mode}", f"src={src}"]
        for key, value in fields.items():
            if value in (None, ""):
                continue
            parts.append(f'{key}="{_clean(value)}"')
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(" ".join(parts) + "\n")
    except Exception:
        pass

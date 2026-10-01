#!/usr/bin/env python3
"""Hook PreInvocation: Inyección de directivas efímeras antes de la llamada al modelo.

La directiva inyectada depende del tipo de repositorio y del modo activo en '~/.agents/current_mode':
  - Modo Orquestador: Se activa si AGENTS.md contiene 'orquestación'/'Repo padre' o si hay subrepositorios git.
  - Modo Plan: Arquitecto SDD y delegación a subagente Pro.
  - Modo Build: Ingeniero Full-Stack para ciclo TDD local.

Coste: $0 tokens de disco/contexto persistente.
"""

import json
import os
import subprocess
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agy_mode import audit, read_mode
except Exception:  # Fail-safe: sin el módulo de estado, se asume /plan.

    def read_mode() -> str:
        return "plan"

    def audit(*_args, **_kwargs) -> None:
        pass


PLAN_MODEL_POLICY = "browser-first: orquestar subagente con Model='pro' para arquitectura profunda"
BUILD_MODEL_POLICY = "browser-first: sesión madre económica en Web UI (Gemini Flash Low Effort)"

PLAN_DIRECTIVE = (
    "[MODO /PLAN: Arquitecto SDD en spec.md y tests/. Prohibido modificar src/. Orquestar subagente pro para diseño]."
)

BUILD_DIRECTIVE = (
    "[MODO /BUILD: Ingeniero de Software Full-Stack en src/ y tests/. TDD local, ruff en CPU, VPS solo lectura]."
)

ORCHESTRATOR_DIRECTIVE = (
    "[MODO ORQUESTADOR: Solo documentación, decisiones y contratos. Prohibido tocar código de producto]."
)


def check_or_trigger_tokenix_index() -> str:
    """Verifica si el workspace está indexado en Tokenix; si no, lanza indexación silenciosa en background."""
    try:
        res = subprocess.run(
            ["tokenix", "stats", "--no-tui"],
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        if res.returncode != 0 or "Error" in res.stderr:
            subprocess.Popen(
                ["tokenix", "index", "."],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    except Exception:
        pass
    return ""


def is_orchestrator_workspace(target_dir: Optional[str] = None) -> bool:
    """Detecta si el directorio actual corresponde a un repositorio orquestador / paraguas."""
    workdir = target_dir or os.getcwd()
    try:
        agents_md = os.path.join(workdir, "AGENTS.md")
        if os.path.isfile(agents_md):
            with open(agents_md, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if (
                    "orquestación" in content
                    or "orquestacion" in content
                    or "repo padre" in content
                    or "orquestador" in content
                ):
                    return True

        with os.scandir(workdir) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False) and not entry.name.startswith("."):
                    sub_git = os.path.join(entry.path, ".git")
                    if os.path.exists(sub_git):
                        return True
    except Exception:
        pass
    return False


def get_directive(mode: str, cwd: Optional[str] = None) -> str:
    """Determina la directiva a inyectar según el tipo de workspace y el modo activo."""
    workdir = cwd or os.getcwd()
    if is_orchestrator_workspace(workdir):
        return ORCHESTRATOR_DIRECTIVE

    directive = BUILD_DIRECTIVE if mode == "build" else PLAN_DIRECTIVE
    tokenix_notice = check_or_trigger_tokenix_index()
    if tokenix_notice:
        directive += tokenix_notice
    return directive


def main() -> None:
    workdir: Optional[str] = None
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
            if isinstance(payload, dict):
                workdir = payload.get("cwd") or payload.get("workspace") or payload.get("workingDirectory")
    except Exception:
        pass

    mode = read_mode()
    directive = get_directive(mode, cwd=workdir)
    audit("pre_invocation", mode, detail=directive)

    response = {"injectSteps": [{"ephemeralMessage": directive}]}
    print(json.dumps(response))


if __name__ == "__main__":
    main()

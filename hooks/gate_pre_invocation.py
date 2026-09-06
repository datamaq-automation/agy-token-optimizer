#!/usr/bin/env python3
"""Hook PreInvocation: Inyección de directivas efímeras antes de la llamada al modelo.

La directiva inyectada depende del modo activo en '~/.agents/current_mode':
  - 'plan'  : Arquitecto SDD exclusivo (la construcción se delega al modo build).
  - 'build' : Ingeniero de implementación con capacidad operativa completa.

Coste: $0 tokens de disco/contexto persistente.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agy_mode import audit, read_mode
except Exception:  # Fail-safe: sin el módulo de estado, se asume /plan.

    def read_mode() -> str:
        return "plan"

    def audit(*_args, **_kwargs) -> None:
        pass


PLAN_DIRECTIVE = (
    "[DIRECTIVA INMUTABLE AGY - MODO /PLAN EXCLUSIVO]\n"
    "1. ROL: Eres exclusivamente Arquitecto SDD. PROHIBIDO modificar código en src/.\n"
    "2. FLUJO: Analiza requerimientos, resuelve Certezas vs Dudas, consolida 'spec.md' y tests en 'tests/'.\n"
    "3. ENTREGABLE OBLIGATORIO: Genera SIEMPRE un artefacto Markdown de planificación ('plan_<feature>.md') con la guía paso a paso para ejecutar luego en modo build.\n"
    "4. DELEGACIÓN: La implementación se ejecuta en modo build ('agy-mode build'), no en este modo."
)

BUILD_DIRECTIVE = (
    "[MODO BUILD ACTIVO - INGENIERO DE IMPLEMENTACIÓN]\n"
    "1. ROL: Ingeniero de Software Full-Stack. Habilitado para crear y editar código en src/, "
    "app/, lib/ y equivalentes, ejecutar tests, refactorizar y correr comandos de build.\n"
    "2. FLUJO: Implementa conforme a 'spec.md' (si existe) y ejecuta el ciclo TDD/verificación: "
    "test rojo -> implementación mínima -> test verde -> refactor.\n"
    "3. ENTREGABLE: Código funcional y verificado, no un plan. No delegues la implementación.\n"
    "4. LÍMITES: Siguen bloqueados los comandos destructivos irreversibles y el reescritura "
    "forzada de historia git. Pide confirmación antes de acciones no reversibles.\n"
    "5. VPS REMOTO: para intervenir el servidor usá 'agy-opt vps-run <cmd>', "
    "'agy-opt vps-read <archivo> --ast', 'agy-opt vps-patch' y 'agy-opt vps-health'. "
    "Prohibido 'ssh' crudo para consultas: la salida entra sin podar al contexto. "
    "Los comandos interactivos, dumps binarios y operaciones largas sí van por ssh directo."
)


def main() -> None:
    try:
        _ = sys.stdin.read()
    except Exception:
        pass

    mode = read_mode()
    directive = BUILD_DIRECTIVE if mode == "build" else PLAN_DIRECTIVE
    audit("pre_invocation", mode, detail=directive.splitlines()[0])

    response = {"injectSteps": [{"ephemeralMessage": directive}]}
    print(json.dumps(response))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Hook PreToolUse: enrutado de comandos de run_command hacia la capa podada.

Aplica la matriz (scope x kind) del spec:

  (REMOTO, CONSULTA)       -> allow + overwrite hacia vps_exec.py
  (REMOTO, ESCRITURA)      -> deny, guiando hacia agy-opt vps-patch
  (REMOTO, MUTACION)       -> deny, bloqueo duro
  (*, LECTURA_CODIGO)      -> deny, guiando hacia poda AST o vps-read --ast
  resto                    -> allow sin overwrite

Sobre el 'deny' en MUTACION: se verificó empíricamente que
'--dangerously-skip-permissions' auto-aprueba también 'ask' y 'force_ask'
emitidos por un hook. 'deny' es el unico valor que ninguna bandera pisa, por lo
que el motivo del rechazo es la unica interfaz que le queda al usuario: debe
nombrar el comando y ofrecer la via manual.

Analisis puramente lexico: no toca la red, no resuelve DNS.
"""

import json
import os
import sys

REPO_ROOT = os.environ.get("AGY_OPTIMIZER_ROOT", "/home/agustin/proyectos_software/agy-token-optimizer")
SCRIPTS_DIR = "/home/agustin/.agents/skills/token-optimizer/scripts"

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _allow() -> dict:
    return {"decision": "allow"}


def _deny(reason: str) -> dict:
    return {"decision": "deny", "reason": reason}


def decidir(command_line: str) -> dict:
    # Import diferido: si el paquete no esta disponible, el hook falla abierto
    # en lugar de frenar la sesion del agente.
    try:
        from src.adapters.code_file_inspector import LocalCodeFileInspector
        from src.application.clasificar_comando import (
            LexicalCommandClassifier,
            tiene_redireccion_de_salida,
        )
        from src.domain.ports import CommandKind, CommandScope
    except ImportError:
        return _allow()

    clasificador = LexicalCommandClassifier(LocalCodeFileInspector())
    res = clasificador.classify(command_line)
    if res is None:
        return _allow()

    remoto = res.scope == CommandScope.REMOTO

    if res.kind == CommandKind.LECTURA_CODIGO:
        if remoto:
            return _deny(
                f"GUARDIAN DE TOKENS (lectura remota): '{res.target_path}' entraria completo al "
                f"contexto. Use el lector quirurgico ($0 tokens de transferencia): "
                f"'agy-opt vps-read {res.target_path} --ast', o un rango acotado con "
                f'"ssh {res.host_alias} \\"sed -n \'1,60p\' {res.target_path}\\"".'
            )
        return _deny(
            f"GUARDIAN DE TOKENS (poda AST obligatoria): '{res.target_path}' supera las 100 lineas. "
            f"Use un rango acotado ('head -n 60', \"sed -n '1,60p'\") o la poda local ($0 tokens): "
            f"'python3 {SCRIPTS_DIR}/prune_python_ast.py {res.target_path}'."
        )

    if remoto and res.kind == CommandKind.ESCRITURA:
        return _deny(
            f"ESCRITURA REMOTA BLOQUEADA: '{res.target_path}' se editaria sin validacion de sintaxis. "
            f"Use el parcheador quirurgico, que valida antes de escribir: "
            f'\'agy-opt vps-patch {res.target_path} --target "<viejo>" --replacement "<nuevo>"\'.'
        )

    if remoto and res.kind == CommandKind.MUTACION:
        return _deny(
            f"MUTACION REMOTA BLOQUEADA ({res.reason}): '{res.inner_command}'. "
            f"Esta operacion altera el estado del servidor y no es reversible desde el agente. "
            f"Si realmente la necesitas, ejecutala manualmente fuera del agente: "
            f'ssh {res.host_alias} "{res.inner_command}".'
        )

    if remoto and res.kind == CommandKind.CONSULTA:
        # Regla transversal: una linea con redireccion nunca se reenruta; el
        # clasificador ya la habria marcado EXENTO o ESCRITURA, pero se reafirma aca.
        if tiene_redireccion_de_salida(res.inner_command):
            return _allow()
        interno = res.inner_command.replace("'", "'\\''")
        optimizado = f"python3 {SCRIPTS_DIR}/vps_exec.py '{interno}' --host {res.host_alias}"
        return {"decision": "allow", "overwrite": {"CommandLine": optimizado}}

    return _allow()


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps(_allow()))
            return
        payload = json.loads(raw)
    except Exception:
        print(json.dumps(_allow()))
        return

    tool_call = payload.get("toolCall", {})
    if tool_call.get("name") != "run_command":
        print(json.dumps(_allow()))
        return

    try:
        decision = decidir(tool_call.get("args", {}).get("CommandLine", ""))
    except Exception:
        decision = _allow()  # Fail-open: un bug del hook no debe frenar la sesion.

    print(json.dumps(decision))


if __name__ == "__main__":
    main()

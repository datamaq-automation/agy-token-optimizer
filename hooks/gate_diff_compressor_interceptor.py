#!/usr/bin/env python3
"""Hook PreToolUse: Interceptor y Compresor Automático de Git Diffs para Antigravity (AGY).

Detecta comandos 'git diff' ejecutados vía run_command y reescribe de forma transparente
la invocación para canalizarla por el compresor determinístico en hardware local (CPU AVX2),
eliminando lockfiles masivos y ruido antes de devolver la salida a la ventana de contexto ($0 tokens).
"""

import json
import re
import sys


def process_command(cmd: str) -> dict:
    if not cmd or not cmd.strip():
        return {"decision": "allow"}

    # 1. Detectar invocaciones a git diff
    has_git_diff = bool(re.search(r"\bgit\s+diff\b", cmd))
    is_diff_piped = "compress_diff" in cmd
    has_pathspec_exclusion = ":(exclude)" in cmd or ":!*" in cmd

    if has_git_diff and not is_diff_piped and not has_pathspec_exclusion:
        optimized_cmd = f"{cmd} | python3 /home/agustin/.agents/skills/token-optimizer/scripts/compress_diff.py"
        return {"decision": "allow", "overwrite": {"CommandLine": optimized_cmd}}

    # 2. Las lineas remotas las gobierna gate_remote_router.py: no interferir.
    #    Ademas evita el bug de pasar 'ssh' como perfil a prune_terminal_output.py
    #    en lugar del comando real que se ejecuta del otro lado.
    if re.match(r"^\s*ssh\b", cmd):
        return {"decision": "allow"}

    # 3. Detectar comandos ruidosos de terminal (npm, pip, composer, pytest)
    noisy_cmds = [
        r"\bnpm\s+(install|i|test|audit)\b",
        r"\bpip\s+install\b",
        r"\bcomposer\s+(install|update)\b",
        r"\bpytest\b",
    ]
    is_terminal_piped = "prune_terminal_output" in cmd
    matches_noisy = any(re.search(pat, cmd) for pat in noisy_cmds)

    if matches_noisy and not is_terminal_piped:
        cmd_first = cmd.split()[0]
        optimized_cmd = f"{cmd} | python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_terminal_output.py '{cmd_first}'"
        return {"decision": "allow", "overwrite": {"CommandLine": optimized_cmd}}

    return {"decision": "allow"}


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            decision = process_command(cmd)
            print(json.dumps(decision))
            return

        print(json.dumps({"decision": "allow"}))
    except Exception:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()

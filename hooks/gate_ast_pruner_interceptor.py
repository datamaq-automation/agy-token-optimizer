#!/usr/bin/env python3
"""Hook PreToolUse: Interceptor de Poda AST para lecturas en Antigravity (AGY).

Detecta lecturas masivas no acotadas sobre archivos de código (>100 líneas)
e instruye a utilizar la versión esqueletizada para ahorrar entre 75% y 90% de tokens de contexto.
"""

import json
import os
import sys


def check_view_file(args: dict) -> dict:
    filepath = args.get("AbsolutePath", "")
    if not filepath or not os.path.isfile(filepath):
        return {"decision": "allow"}

    _, ext = os.path.splitext(filepath)
    ext_lower = ext.lower()
    code_exts = {".py", ".ts", ".js", ".go", ".rs", ".php"}
    data_exts = {".json", ".yaml", ".yml", ".csv"}

    if ext_lower not in code_exts and ext_lower not in data_exts:
        return {"decision": "allow"}

    start_line = args.get("StartLine")
    end_line = args.get("EndLine")

    # Si se especificó un rango quirúrgico <= 150 líneas, permitir
    if start_line is not None and end_line is not None:
        if end_line - start_line <= 150:
            return {"decision": "allow"}

    # Contar líneas del archivo
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            total_lines = sum(1 for _ in f)
    except Exception:
        return {"decision": "allow"}

    # Si excede 100 líneas sin rango acotado, sugerir poda AST o esquematización
    if total_lines > 100:
        filename = os.path.basename(filepath)
        if ext_lower in data_exts:
            return {
                "decision": "deny",
                "reason": (
                    f"GUARDIÁN DE TOKENS (Esquematización de Datos Obligatoria): '{filename}' tiene {total_lines} líneas. "
                    f"Para ahorrar 90%-98% de tokens, use un rango acotado (StartLine/EndLine) o consulte el esquema estructural local ($0 tokens): "
                    f"'python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_data_schema.py {filepath}'."
                ),
            }
        else:
            return {
                "decision": "deny",
                "reason": (
                    f"GUARDIÁN DE TOKENS (Poda AST Obligatoria): '{filename}' tiene {total_lines} líneas. "
                    f"Para ahorrar 75%-90% de tokens, use un rango acotado (StartLine/EndLine) o ejecute la poda AST local ($0 tokens): "
                    f"'python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_python_ast.py {filepath}'."
                ),
            }

    return {"decision": "allow"}


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return
        payload = json.loads(raw_input)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    if tool_name == "view_file":
        res = check_view_file(tool_args)
        print(json.dumps(res))
        return

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()

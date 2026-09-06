#!/usr/bin/env python3
"""Hook PreToolUse: Hard-Gate y Zero-Trust Perimeter para Antigravity (AGY).

Opera en dos modos, según '~/.agents/current_mode':

  - 'plan'  : Zero-Trust Perimeter completo. Restringe la escritura a Allowlist
              estricta (spec.md, specs/**, tests/**, .agents/**, .gemini/**),
              bloquea mutaciones destructivas y commits git en run_command,
              protege lecturas masivas en view_file e intercepta subagentes de build.

  - 'build' : Capacidad operativa completa (src/, app/, lib/, tests, refactors).
              Solo permanecen activas las protecciones críticas contra comandos
              irreversibles (borrado de raíz/HOME, mkfs, dd sobre dispositivos,
              fork bombs, reescritura forzada de historia git).

Ante cualquier duda sobre el modo se degrada a 'plan' (fail-safe).
"""

import json
import os
import re
import sys
from typing import Any, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agy_mode import audit, read_mode
except Exception:  # Fail-safe: sin el módulo de estado, se asume /plan.

    def read_mode() -> str:
        return "plan"

    def audit(*_args, **_kwargs) -> None:
        pass


# Extensiones de código de producción protegidas
PROD_CODE_EXTS = {
    ".py",
    ".ts",
    ".js",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
}


def is_path_allowed(target_path: str) -> bool:
    if not target_path:
        return True

    norm_path = os.path.normpath(target_path)
    parts = norm_path.split(os.sep)
    filename = os.path.basename(norm_path)
    _, ext = os.path.splitext(filename)

    # 1. Permitido: spec.md y specs/
    if filename.lower() == "spec.md" or "specs" in parts:
        return True

    # 2. Permitido: tests/ o test/
    if "tests" in parts or "test" in parts:
        return True

    # 3. Permitido: .agents/, .agy-optimizer/ y configuraciones globales del sistema
    if any(p in parts for p in [".agents", ".agent", ".gemini", ".agy-optimizer"]):
        return True

    # 4. Permitido: .gemini/ o artefactos brain/ y scratch/
    if ".gemini" in parts or "brain" in parts or "scratch" in parts or "artifacts" in parts:
        return True

    # 5. Permitido: Archivos de gobernanza y configuración raíz
    allowed_root_files = {
        "readme.md",
        "agents.md",
        "gemini.md",
        "conventions.md",
        "pyproject.toml",
        "package.json",
        "tsconfig.json",
        ".gitignore",
        "ruff.toml",
    }
    if filename.lower() in allowed_root_files:
        return True

    # Denegar cualquier archivo de código de producción
    if ext.lower() in PROD_CODE_EXTS:
        return False

    # Denegar carpetas estándar de código de producción
    restricted_dirs = {
        "src",
        "app",
        "lib",
        "internal",
        "backend",
        "frontend",
        "pkg",
        "core",
        "domain",
        "adapters",
        "infrastructure",
    }
    if any(d in parts for d in restricted_dirs):
        return False

    return False


def handle_write_tools(tool_name: str, args: Dict[str, Any]) -> Dict[str, str]:
    target_file = args.get("TargetFile", "")
    if not target_file:
        return {"decision": "allow"}

    if not is_path_allowed(target_file):
        return {
            "decision": "deny",
            "reason": (
                f"ACCESO DENEGADO (Zero-Trust Perimeter): Antigravity (AGY) está restringido a /plan. "
                f"No se permite modificar '{target_file}'. "
                f"Cambiá al modo build con 'agy-mode build' para implementar sobre spec.md y tests/."
            ),
        }
    return {"decision": "allow"}


def handle_view_file(args: Dict[str, Any]) -> Dict[str, str]:
    filepath = args.get("AbsolutePath", "")
    if not filepath:
        return {"decision": "allow"}

    norm_path = os.path.normpath(filepath)
    filename = os.path.basename(norm_path)
    _, ext = os.path.splitext(filename)

    # Si se intenta leer un archivo de código productivo fuera de tests/.agents/.gemini
    if ext.lower() in PROD_CODE_EXTS and not is_path_allowed(filepath):
        start_line = args.get("StartLine")
        end_line = args.get("EndLine")
        # Si no se acota el rango o excede las 200 líneas
        if start_line is None or end_line is None or (end_line - start_line > 200):
            return {
                "decision": "deny",
                "reason": (
                    f"GUARDIÁN DE TOKENS: Lectura masiva no acotada sobre '{filename}'. "
                    f"Use 'StartLine' y 'EndLine' (rango <= 200 líneas) o use poda AST con "
                    f"'python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_python_ast.py {filepath}'."
                ),
            }

    return {"decision": "allow"}


def handle_run_command(args: Dict[str, Any]) -> Dict[str, str]:
    command = args.get("CommandLine", "")
    if not command:
        return {"decision": "allow"}

    # 0. Guardia crítica: comandos irreversibles, activa en todos los modos.
    critical = handle_critical_only(args)
    if critical["decision"] == "deny":
        return critical

    # 1. Blindaje Git: Bloquear commits y push sobre código de producción
    if re.search(r"\bgit\s+(commit|push)\b", command):
        # Si incluye archivos fuera de allowlist o commit general
        if not re.search(r"(spec\.md|specs/|tests/|\.agents/)", command):
            return {
                "decision": "deny",
                "reason": (
                    "GIT GUARD: No se permiten commits o push de código fuente desde AGY. "
                    "Cambiá al modo build con 'agy-mode build' para versionar la implementación."
                ),
            }

    # 2. Detectar redirecciones de salida destructivas sobre archivos fuera de allowlist
    redirect_pattern = r"(?:>|>>|\|\s*tee\s+)\s*([^\s;&|]+)"
    matches = re.findall(redirect_pattern, command)
    for target in matches:
        if not is_path_allowed(target):
            return {
                "decision": "deny",
                "reason": f"COMANDO BLOQUEADO: Redirección hacia archivo protegido '{target}'. Cambiá al modo build con 'agy-mode build'.",
            }

    # 3. Detectar comandos de mutación en sitio como sed -i sobre código
    if re.search(r"\bsed\s+-[a-zA-Z]*i", command):
        return {
            "decision": "deny",
            "reason": "COMANDO BLOQUEADO: 'sed -i' está restringido en modo plan. Usá las herramientas de edición o cambiá a modo build.",
        }

    return {"decision": "allow"}


def handle_invoke_subagent(args: Dict[str, Any]) -> Dict[str, str]:
    subagents = args.get("Subagents", [])
    for sub in subagents:
        role = sub.get("Role", "").lower()
        prompt = sub.get("Prompt", "").lower()
        build_keywords = [
            "implementar",
            "codificar",
            "build",
            "escribir codigo",
            "write code",
            "crear src",
        ]
        if any(kw in role or kw in prompt for kw in build_keywords):
            allowed_keywords = [
                "test",
                "spec",
                "research",
                "investigar",
                "auditar",
                "plan",
            ]
            if not any(kw in role or kw in prompt for kw in allowed_keywords):
                return {
                    "decision": "deny",
                    "reason": "SUBAGENTE DENEGADO: No se permite delegar tareas de construcción /build a subagentes en AGY.",
                }
    return {"decision": "allow"}


# Patrones irreversibles que permanecen bloqueados incluso en modo build.
CRITICAL_COMMAND_PATTERNS = [
    (
        r"\brm\s+(?:-[a-zA-Z]*\s+)*-?[a-zA-Z]*[rR][a-zA-Z]*f?[a-zA-Z]*\s+(?:/|~|\$HOME|\$\{HOME\})(?:\s|/?\*|$)",
        "Borrado recursivo sobre la raíz del sistema o el HOME del usuario.",
    ),
    (r"\bmkfs(\.[a-z0-9]+)?\b", "Formateo de sistema de archivos."),
    (r"\bdd\b[^\n]*\bof=\s*/dev/", "Escritura directa sobre un dispositivo de bloque."),
    (r">\s*/dev/(sd|nvme|hd|vd)", "Redirección destructiva sobre un dispositivo de bloque."),
    (r":\s*\(\s*\)\s*\{.*\|.*&.*\}\s*;", "Fork bomb."),
    (r"\bchmod\s+(-[a-zA-Z]+\s+)*777\s+/(\s|$)", "Permisos 777 recursivos sobre la raíz."),
    (
        r"\bgit\s+push\b[^\n]*(--force\b(?!-with-lease)|(?<![\w-])-f(?![\w-]))",
        "Push forzado (reescritura de historia remota).",
    ),
    (r"\bgit\s+reset\s+--hard\b[^\n]*\borigin/(main|master)\b", "Reset duro contra la rama principal remota."),
    (r"\bhistory\s+-c\b", "Borrado del historial de shell."),
]


def handle_critical_only(args: Dict[str, Any]) -> Dict[str, str]:
    """Guardia mínima de modo build: solo comandos irreversibles."""
    command = args.get("CommandLine", "")
    if not command:
        return {"decision": "allow"}

    for pattern, motivo in CRITICAL_COMMAND_PATTERNS:
        if re.search(pattern, command):
            return {
                "decision": "deny",
                "reason": (
                    f"COMANDO CRÍTICO BLOQUEADO (activo también en modo build): {motivo} "
                    f"Si realmente lo necesitas, ejecútalo manualmente fuera del agente."
                ),
            }

    return {"decision": "allow"}


def describe(tool_name: str, args: Dict[str, Any]) -> str:
    """Resumen de una línea del tool call, para la auditoría."""
    if tool_name == "run_command":
        return args.get("CommandLine", "")
    if tool_name == "view_file":
        return args.get("AbsolutePath", "")
    if tool_name == "invoke_subagent":
        return ", ".join(s.get("Role", "?") for s in args.get("Subagents", []))
    return args.get("TargetFile", "")


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return
        payload = json.loads(raw_input)
    except Exception as err:
        print(json.dumps({"decision": "allow", "reason": f"Hook parse error: {err}"}))
        return

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    mode = read_mode()

    # MODO BUILD: capacidad operativa completa, salvo comandos irreversibles.
    if mode == "build":
        res = handle_critical_only(tool_args) if tool_name == "run_command" else {"decision": "allow"}
        audit(
            "blocker",
            mode,
            tool=tool_name,
            decision=res["decision"],
            detail=describe(tool_name, tool_args),
            reason=res.get("reason"),
        )
        print(json.dumps(res))
        return

    if tool_name in {"write_to_file", "replace_file_content"}:
        res = handle_write_tools(tool_name, tool_args)
    elif tool_name == "view_file":
        res = handle_view_file(tool_args)
    elif tool_name == "run_command":
        res = handle_run_command(tool_args)
    elif tool_name == "invoke_subagent":
        res = handle_invoke_subagent(tool_args)
    else:
        res = {"decision": "allow"}

    audit(
        "blocker",
        mode,
        tool=tool_name,
        decision=res["decision"],
        detail=describe(tool_name, tool_args),
        reason=res.get("reason"),
    )
    print(json.dumps(res))


if __name__ == "__main__":
    main()

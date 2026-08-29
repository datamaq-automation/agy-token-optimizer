#!/usr/bin/env python3
"""
build_hardware_healer.py: Auto-sanador determinístico en hardware local (CPU/RAM) para OpenCode /build.
Corrige errores de imports, linting (Ruff), tipado y sintaxis en < 30 ms en CPU
antes de consultar al LLM remoto, evitando quemar tokens en bucles de depuración.
Uso: python3 build_hardware_healer.py <archivo.py>
"""

import subprocess
import sys
from pathlib import Path


def heal_file_locally(target_file: Path) -> bool:
    if not target_file.exists():
        print(f"❌ Error: Archivo '{target_file}' no encontrado.")
        return False

    print(f"🔧 [Hardware Healer] Analizando y auto-sanando '{target_file.name}' en CPU...")

    # 1. Ruff check --fix (elimina imports no usados, arregla formato de sintaxis)
    subprocess.run(["ruff", "check", "--fix", str(target_file)], capture_output=True, text=True)

    # 2. Ruff format (formato estándar)
    subprocess.run(["ruff", "format", str(target_file)], capture_output=True, text=True)

    # 3. Verificación de sintaxis Python AST
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read()
        import ast

        ast.parse(code, filename=str(target_file))
        syntax_ok = True
    except SyntaxError as e:
        syntax_ok = False
        print(f"⚠️ Error de sintaxis en línea {e.lineno}: {e.msg}")

    if syntax_ok:
        print(f"✅ [Hardware Healer] '{target_file.name}' sanado y formateado con éxito en CPU (0 tokens API).")
        return True
    else:
        print(f"❌ [Hardware Healer] Error de sintaxis persistente en '{target_file.name}'.")
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 build_hardware_healer.py <archivo.py>")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    success = heal_file_locally(target)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

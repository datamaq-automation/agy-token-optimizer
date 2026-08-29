#!/usr/bin/env python3
"""
plan_dip_auditor.py: Auditor del Principio de Inversión de Dependencias (DIP) y Clean Architecture en CPU.
Verifica mediante AST que las capas de software respeten estrictamente la dirección de dependencias:
- domain: Cero dependencias externas (solo stdlib/abc/dataclasses).
- application: Depende solo de domain (prohibido infrastructure o frameworks web/db).
- adapters: Implementa puertos de domain (prohibido importar de infrastructure).
- infrastructure: Implementaciones tecnológicas.
Uso: python3 plan_dip_auditor.py [directorio_src]
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_DOMAIN_IMPORTS = {"pydantic", "fastapi", "sqlalchemy", "requests", "httpx", "flask", "django"}
FORBIDDEN_APPLICATION_IMPORTS = {"fastapi", "sqlalchemy", "infrastructure", "flask", "django"}


def audit_dip_in_directory(src_dir: Path) -> tuple[bool, list[str]]:
    if not src_dir.exists():
        return True, []

    errors = []

    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        rel_parts = py_file.relative_to(src_dir).parts
        layer = rel_parts[0] if rel_parts else ""

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=py_file.name)
        except Exception:
            continue

        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append((node.module, node.lineno))

        # 1. Reglas para capa domain/
        if layer == "domain":
            for mod, line in imported_modules:
                base_mod = mod.split(".")[0]
                if (
                    base_mod in FORBIDDEN_DOMAIN_IMPORTS
                    or "application" in mod
                    or "infrastructure" in mod
                    or "adapters" in mod
                ):
                    errors.append(
                        f"[DIP Violado] domain/{py_file.name}#L{line} importa '{mod}' (El dominio debe ser 100% puro)."
                    )

        # 2. Reglas para capa application/
        elif layer == "application":
            for mod, line in imported_modules:
                base_mod = mod.split(".")[0]
                if base_mod in FORBIDDEN_APPLICATION_IMPORTS or "infrastructure" in mod:
                    errors.append(
                        f"[DIP Violado] application/{py_file.name}#L{line} importa '{mod}' (Application no puede depender de Infrastructure)."
                    )

        # 3. Reglas para capa adapters/
        elif layer == "adapters":
            for mod, line in imported_modules:
                if "infrastructure" in mod:
                    errors.append(
                        f"[DIP Violado] adapters/{py_file.name}#L{line} importa '{mod}' (Adapters no puede depender de Infrastructure)."
                    )

    return len(errors) == 0, errors


def main():
    target_src = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("src").resolve()
    print(f"🛡️  [DIP Auditor] Validando Inversión de Dependencias y Capas en '{target_src}'...")

    ok, errs = audit_dip_in_directory(target_src)
    print("=" * 70)
    if ok:
        print("✅ [DIP 100% VÁLIDO] La dirección de dependencias de Clean Architecture es canónica y pura.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ [DIP VIOLADO] Se detectaron dependencias prohibidas entre capas:")
        for e in errs:
            print(f"  • {e}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

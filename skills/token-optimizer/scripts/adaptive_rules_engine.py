#!/usr/bin/env python3
"""
adaptive_rules_engine.py: Motor de reglas adaptativo para AGY.
Escanea la estructura y stack tecnológico del proyecto para generar un archivo AGENTS.md
personalizado con el Guantelete de Restricciones inmutable, ahorrando >1.500 tokens de alineación.
Uso: python3 adaptive_rules_engine.py [directorio_repo] [archivo_salida]
"""

import os
import sys
from pathlib import Path


def detect_project_stack(repo_dir: str = ".") -> dict:
    path = Path(repo_dir).resolve()
    stack = {"backend": "python", "frontend": None, "frameworks": [], "linter": "ruff", "test_runner": "pytest"}

    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        stack["backend"] = "python"
        stack["frameworks"].append("FastAPI/Python")
    if (path / "package.json").exists():
        stack["frontend"] = "typescript"
        stack["frameworks"].append("Vue/TypeScript")
    if (path / "src" / "domain").exists():
        stack["frameworks"].append("Canonical Clean Architecture")

    return stack


def generate_adaptive_agents_md(repo_dir: str = ".") -> str:
    stack = detect_project_stack(repo_dir)
    fw_str = ", ".join(stack["frameworks"]) or "Estándar Limpio"

    return f"""# Directivas de Proyecto & Guantelete de Restricciones (Uncle Bob)

> **Stack Detectado:** {fw_str}
> **Modo de Gobernanza:** Zero-Token Waste & Constraint Gauntlet

---

## 1. Modos de Operación Estrictos
- **/ask (Consultor):** Solo lectura. Prohibido crear o editar archivos. Respuestas concisas con citas a líneas `[archivo#L10-L20]`.
- **/plan (Arquitecto SDD):** Exclusivamente edita `spec.md` y `tests/`. Prohibido tocar `src/`.
- **/build (Implementador TDD):** Exige `spec.md`. Ciclo RED -> GREEN -> REFACTOR. Supera `ci_local.sh`.

---

## 2. Las 5 Baterías Inmutables del Guantelete
1. **`__init__.py` de 0 bytes:** 100% de los `__init__.py` en `src/` y `tests/` con exactamente 0 bytes.
2. **Clean Architecture Canónica:** `domain/` (puro, ports.py) -> `application/` -> `adapters/` -> `infrastructure/`.
3. **Imports 100% Absolutos:** Prohibidos imports relativos (`from .` o `from ..`). Obligatorio `from src...` o `@/...`.
4. **Tipado Estricto al 100%:** Anotaciones explícitas en todos los parámetros y retornos. Prohibido `any`.
5. **Zero Evasión:** Prohibido relajar tests o usar `# type: ignore`, `# noqa`, `@ts-ignore`.

---

## 3. Pre y Post-Procesamiento en CPU Local ($0 Tokens)
- Antes de leer archivos grandes: `agy-opt inject <simbolo>` o `agy-opt stubs src/`.
- Tras editar código: `ruff check --fix <archivo> && ruff format <archivo>`.
- Para validar entrega: `agy-opt ci .`.
"""


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    out_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(repo, "AGENTS.md")

    content = generate_adaptive_agents_md(repo)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Reglas adaptativas generadas exitosamente en '{out_file}'.")


if __name__ == "__main__":
    main()

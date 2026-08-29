#!/usr/bin/env python3
"""
docs_structure_init.py: Inicializador determinístico de documentación según Diátaxis, ADRs y SDD.
Crea la jerarquía estándar:
- docs/explanation/ (Arquitectura conceptual)
- docs/how-to/ (Guías operativas)
- docs/reference/ (Contratos y especificaciones técnicas)
- docs/adr/ (Architecture Decision Records numerados)
- specs/active/ y specs/archive/ (Ciclo de vida SDD)
Uso: python3 docs_structure_init.py [directorio_raiz]
"""

import sys
from pathlib import Path


def init_docs_structure(root_dir: Path) -> list[str]:
    created = []

    # 1. Carpetas Diátaxis y SDD
    dirs_to_create = [
        root_dir / "docs" / "explanation",
        root_dir / "docs" / "how-to",
        root_dir / "docs" / "reference",
        root_dir / "docs" / "adr",
        root_dir / "specs" / "active",
        root_dir / "specs" / "archive",
    ]

    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(f"📁 {d.relative_to(root_dir)}/")

    # 2. Plantilla docs/explanation/architecture.md
    arch_file = root_dir / "docs" / "explanation" / "architecture.md"
    if not arch_file.exists():
        with open(arch_file, "w", encoding="utf-8") as f:
            f.write("""# Arquitectura del Sistema (Clean Architecture)

> **Tipo de Documento:** Diátaxis / Explanation
> **Propósito:** Explicar el modelo conceptual, dirección de dependencias y límites del dominio.

---

## 1. Reglas de Capas (Inward-Only)
```
[Infrastructure] ──► [Adapters] ──► [Application] ──► [Domain (Core)]
```
1. **Domain:** Entidades puras y puertos abstractos (`abc.ABC`). Cero dependencias externas.
2. **Application:** Casos de uso y orquestación de negocio.
3. **Adapters:** Controladores, gateways y repositorios que implementan puertos de dominio.
4. **Infrastructure:** Frameworks (FastAPI, SQLAlchemy, Docker, CLI).
""")
        created.append(f"📄 {arch_file.relative_to(root_dir)}")

    # 3. Plantilla docs/reference/conventions.md
    conv_file = root_dir / "docs" / "reference" / "conventions.md"
    if not conv_file.exists():
        with open(conv_file, "w", encoding="utf-8") as f:
            f.write("""# Convenciones y Guantelete de Restricciones

> **Tipo de Documento:** Diátaxis / Reference
> **Propósito:** Definir estándares estáticos inmutables de código.

---

## 1. Las 5 Baterías del Guantelete
1. **`__init__.py` de 0 bytes:** 100% de los `__init__.py` con 0 bytes.
2. **Imports Absolutos:** Obligatorio `from src...` o `@/...`. Prohibido `from .` o `from ..`.
3. **Tipado Estricto:** Anotaciones explícitas en el 100% de parámetros y retornos. Prohibido `any`.
4. **Cero Evasiones:** Prohibido relajar directivas de tipos o linters.
5. **Zero Secretos:** Bloqueo estricto de credenciales en código.
""")
        created.append(f"📄 {conv_file.relative_to(root_dir)}")

    # 4. Plantilla docs/adr/template.md
    adr_template = root_dir / "docs" / "adr" / "template.md"
    if not adr_template.exists():
        with open(adr_template, "w", encoding="utf-8") as f:
            f.write("""# ADR-XXXX: [Título de la Decisión de Arquitectura]

* **Estado:** `Propuesto` | `Aceptado` | `Superado`
* **Fecha:** `YYYY-MM-DD`
* **Decisores:** `[Equipo / Autor]`

---

## 1. Contexto & Problema
[Describir la necesidad técnica o de negocio y los desafíos actuales]

## 2. Decisión de Arquitectura
[Describir la solución adoptada y los componentes involucrados]

## 3. Consecuencias & Trade-offs
* **Impacto Positivo:** [Beneficios de rendimiento, simplicidad o ahorro]
* **Impacto Negativo / Riesgos:** [Deuda asumida o restricciones impuestas]
""")
        created.append(f"📄 {adr_template.relative_to(root_dir)}")

    return created


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    print(f"📚 [Diátaxis & SDD Init] Inicializando estructura documental en '{root.name}'...")

    created = init_docs_structure(root)
    print("=" * 70)
    if created:
        print(f"✅ Estructura Diátaxis, ADR y SDD creada ({len(created)} elementos):")
        for item in created:
            print(f"  • {item}")
    else:
        print("ℹ️  La estructura Diátaxis y SDD ya se encontraba completa.")
    print("=" * 70)


if __name__ == "__main__":
    main()

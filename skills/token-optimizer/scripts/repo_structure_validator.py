#!/usr/bin/env python3
"""
repo_structure_validator.py: Validador y clasificador de topología de repositorio pre-plan para AGY.
Analiza en CPU (< 10 ms) el árbol de carpetas del proyecto, valida la integridad de paquetes
y entrega una matriz de destinos canónicos en < 80 tokens para que el LLM nunca dude dónde ubicar archivos.
Uso: python3 repo_structure_validator.py [directorio_repo]
"""

import sys
from pathlib import Path


def analyze_repository_topology(root_dir: Path) -> dict:
    result = {"pattern": "Estructura Genérica / Desconocida", "destinations": {}, "warnings": [], "health_score": 100}

    has_src = (root_dir / "src").is_dir()
    has_app = (root_dir / "app").is_dir()
    has_domain = (root_dir / "src" / "domain").is_dir() or (root_dir / "domain").is_dir()
    has_application = (root_dir / "src" / "application").is_dir() or (root_dir / "application").is_dir()

    # 1. Clasificación del Patrón
    if has_domain or (has_src and has_application):
        result["pattern"] = "Clean Architecture Canónica"
        base_src = "src" if has_src else ""
        result["destinations"] = {
            "Dominio / Entidades": f"{base_src}/domain/".strip("/"),
            "Puertos / Interfaces": f"{base_src}/domain/ports.py".strip("/"),
            "Casos de Uso": f"{base_src}/application/".strip("/"),
            "Adaptadores / Gateways": f"{base_src}/adapters/".strip("/"),
            "Infraestructura / Frameworks": f"{base_src}/infrastructure/".strip("/"),
        }
    elif has_app:
        result["pattern"] = "Estructura Modular App (FastAPI / Flask)"
        result["destinations"] = {
            "Modelos": "app/models/",
            "Servicios / Lógica": "app/services/",
            "Rutas / Controladores": "app/routers/",
            "Configuración": "app/core/",
        }
    elif has_src:
        result["pattern"] = "Paquete Estándar src/"
        result["destinations"] = {"Módulos Principales": "src/", "Utilidades": "src/utils/"}
    else:
        result["pattern"] = "Estructura Plana / Scripts"
        result["destinations"] = {"Scripts / Código": "scripts/" if (root_dir / "scripts").is_dir() else "./"}

    # 2. Destinos de Tests y Documentación
    if (root_dir / "tests" / "unit").is_dir():
        result["destinations"]["Tests Unitarios"] = "tests/unit/"
    elif (root_dir / "tests").is_dir():
        result["destinations"]["Tests Unitarios"] = "tests/"
    else:
        result["destinations"]["Tests Unitarios"] = "tests/unit/ (Por crear)"
        result["warnings"].append("Carpeta 'tests/' no encontrada.")
        result["health_score"] -= 10

    if (root_dir / "specs" / "active").is_dir():
        result["destinations"]["Especificaciones SDD"] = "specs/active/ y spec.md"
    else:
        result["destinations"]["Especificaciones SDD"] = "spec.md"

    # 3. Auditoría de __init__.py (Guantelete Uncle Bob)
    py_files = list(root_dir.rglob("*.py"))
    for py in py_files:
        if py.name == "__init__.py" and not any(
            p.startswith(".") or p in ("venv", ".venv", "node_modules") for p in py.parts
        ):
            if py.stat().st_size > 0:
                rel = py.relative_to(root_dir)
                result["warnings"].append(f"__init__.py no tiene 0 bytes: {rel} ({py.stat().st_size} bytes)")
                result["health_score"] -= 5

    return result


def format_compact_topology_bundle(topology: dict) -> str:
    lines = [
        f"🏛️ [Topología de Repositorio: {topology['pattern']}] (Salud: {topology['health_score']}/100)",
        "📍 Destinos Canónicos Validados para el Plan:",
    ]
    for role, dest in topology["destinations"].items():
        lines.append(f"   • {role}: `{dest}`")

    if topology["warnings"]:
        lines.append("⚠️ Alertas de Estructura:")
        for w in topology["warnings"][:3]:
            lines.append(f"   • {w}")

    return "\n".join(lines)


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    topology = analyze_repository_topology(root)
    bundle = format_compact_topology_bundle(topology)

    print("=" * 70)
    print(bundle)
    print("=" * 70)


if __name__ == "__main__":
    main()

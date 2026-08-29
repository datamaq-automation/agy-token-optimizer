#!/usr/bin/env python3
"""
repo_structure_validator.py v2: Validador y clasificador de topología de repositorio pre-plan para AGY.
Analiza en CPU (< 10 ms):
1. Patrón arquitectónico del repositorio y destinos canónicos.
2. Stack tecnológico y dependencias clave (pyproject.toml, package.json, Cargo.toml).
3. Monorepos y workspaces (apps/, packages/).
4. Herramientas de gobernanza y linters activos (ruff, pyright, tsconfig, docker).
Entrega una matriz compacta en < 90 tokens integrada en agy-opt preplan.
Uso: python3 repo_structure_validator.py [directorio_repo]
"""

import json
import sys
from pathlib import Path

KEY_FRAMEWORKS = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "pytest": "Pytest",
    "alembic": "Alembic",
    "celery": "Celery",
    "redis": "Redis",
    "httpx": "HTTPX",
    "express": "Express",
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "prisma": "Prisma",
    "vitest": "Vitest",
    "jest": "Jest",
    "tokio": "Tokio (Async Rust)",
    "axum": "Axum (Rust)",
    "actix-web": "Actix-Web",
    "gin": "Gin (Go)",
    "fiber": "Fiber (Go)",
}


def detect_project_stack(root_dir: Path) -> list[str]:
    detected = []

    # 1. Python (pyproject.toml / requirements.txt)
    pyproject = root_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for key, name in KEY_FRAMEWORKS.items():
                    if key in content and name not in detected:
                        detected.append(name)
        except Exception:
            pass

    reqs = root_dir / "requirements.txt"
    if reqs.exists():
        try:
            with open(reqs, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for key, name in KEY_FRAMEWORKS.items():
                    if key in content and name not in detected:
                        detected.append(name)
        except Exception:
            pass

    # 2. Node / TypeScript (package.json)
    pkg_json = root_dir / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for dep in deps:
                    dep_lower = dep.lower()
                    for key, name in KEY_FRAMEWORKS.items():
                        if key in dep_lower and name not in detected:
                            detected.append(name)
        except Exception:
            pass

    # 3. Rust (Cargo.toml)
    cargo = root_dir / "Cargo.toml"
    if cargo.exists():
        try:
            with open(cargo, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for key, name in KEY_FRAMEWORKS.items():
                    if key in content and name not in detected:
                        detected.append(name)
        except Exception:
            pass

    return detected


def detect_monorepo_workspaces(root_dir: Path) -> list[str]:
    workspaces = []
    for d in ["packages", "apps", "modules", "services"]:
        target = root_dir / d
        if target.is_dir():
            subdirs = [sub.name for sub in target.iterdir() if sub.is_dir() and not sub.name.startswith(".")]
            if subdirs:
                workspaces.append(f"{d}/: [{', '.join(subdirs[:4])}]")
    return workspaces


def detect_governance_configs(root_dir: Path) -> list[str]:
    configs = []
    if (root_dir / "ruff.toml").exists() or (root_dir / "pyproject.toml").exists():
        configs.append("Ruff")
    if (root_dir / "pyrightconfig.json").exists():
        configs.append("Pyright (Estricto)")
    if (root_dir / "tsconfig.json").exists():
        configs.append("TypeScript")
    if (root_dir / "docker-compose.yml").exists() or (root_dir / "docker-compose.yaml").exists():
        configs.append("Docker Compose")
    if (root_dir / ".git" / "hooks").exists():
        configs.append("Git Hooks")
    return configs


def analyze_repository_topology(root_dir: Path) -> dict:
    result = {
        "pattern": "Estructura Genérica / Desconocida",
        "destinations": {},
        "stack": detect_project_stack(root_dir),
        "workspaces": detect_monorepo_workspaces(root_dir),
        "governance": detect_governance_configs(root_dir),
        "warnings": [],
        "health_score": 100,
    }

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
    ]
    if topology["stack"]:
        lines.append(f"📦 Stack Detectado: {', '.join(topology['stack'])}")
    if topology["workspaces"]:
        lines.append(f"🏢 Monorepo Workspaces: {', '.join(topology['workspaces'])}")
    if topology["governance"]:
        lines.append(f"🛡️ Gobernanza Activa: {', '.join(topology['governance'])}")

    lines.append("📍 Destinos Canónicos Validados para el Plan:")
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

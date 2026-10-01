"""Orquestador de staging y commits atómicos por capas arquitectónicas."""

import os
import re
import subprocess
from typing import Dict, List, Optional

LAYER_PREFIXES = {
    "domain": "feat(dominio)",
    "application": "feat(aplicacion)",
    "ui": "feat(ui)",
    "tooling": "chore(tooling)",
}

CONVENTIONAL_PATTERN = re.compile(r"^(?:feat|fix|chore|refactor|test|docs|style|ci|perf)\([^)]+\):", re.IGNORECASE)


def classify_file_layer(filepath: str) -> str:
    """Clasifica un archivo según su capa arquitectónica (Clean Architecture / DDD o FSD)."""
    norm = filepath.replace("\\", "/").strip()
    norm_lower = norm.lower()

    # 1. Tooling, soporte, infraestructura de desarrollo y meta-archivos
    if (
        norm.startswith("scripts/")
        or norm.startswith("tools/")
        or norm.startswith(".github/")
        or norm.startswith(".gemini/")
        or norm.startswith(".agents/")
        or norm.startswith("config/")
        or norm.startswith("hooks/")
        or norm.startswith("specs/")
        or norm.startswith("decisions/")
        or norm.startswith("docs/")
        or norm
        in {
            ".gitignore",
            ".dockerignore",
            "Makefile",
            "pyproject.toml",
            "package.json",
            "package-lock.json",
            "tsconfig.json",
            "pyrightconfig.json",
            "README.md",
            "CHANGELOG.md",
            "AGENTS.md",
            "CLAUDE.md",
            "install.sh",
            "uninstall.sh",
        }
    ):
        return "tooling"

    # 2. Dominio Puro (Core, Entities, Puertos, Types puros)
    if (
        norm.startswith("src/domain/")
        or norm.startswith("src/core/dominio/")
        or norm.startswith("src/core/domain/")
        or norm.startswith("src/entities/")
        or norm.startswith("src/shared/types/")
        or norm.startswith("src/shared/schemas/")
        or "test_domain" in norm_lower
        or "domain_test" in norm_lower
    ):
        return "domain"

    # 3. Aplicación & DTOs (Casos de uso, Stores, Servicios orquestadores)
    if (
        norm.startswith("src/application/")
        or norm.startswith("src/core/services/")
        or norm.startswith("src/core/use_cases/")
        or norm.startswith("src/app/providers/")
        or norm.startswith("src/composables/")
        or "/stores/" in norm
        or "/use_cases/" in norm
        or "use_case" in norm_lower
        or "test_application" in norm_lower
    ):
        return "application"

    # 4. Infraestructura & UI (Adaptadores externos, Routers, DBs, Componentes UI, Views)
    if (
        norm.startswith("src/infrastructure/")
        or norm.startswith("src/adapters/")
        or norm.startswith("src/api/")
        or norm.startswith("src/views/")
        or norm.startswith("src/shared/ui/")
        or norm.startswith("src/components/")
        or "/components/" in norm
        or "/ui/" in norm
        or norm.endswith(".vue")
        or norm.startswith("src/app/")
        or norm.startswith("tests/integration/")
        or norm.startswith("tests/component/")
        or norm.startswith("tests/e2e/")
    ):
        return "ui"

    # Fallback general
    if norm.startswith("tests/"):
        return "application"
    if norm.startswith("src/"):
        return "application"

    return "tooling"


class StageLayerOrchestrator:
    """Gestiona el staging selectivo y commits atómicos organizados por capas."""

    def __init__(self, repo_dir: Optional[str] = None) -> None:
        self.repo_dir = repo_dir or os.getcwd()

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )

    def get_grouped_status(self) -> Dict[str, List[str]]:
        """Retorna los archivos modificados o sin rastrear agrupados por capa."""
        grouped: Dict[str, List[str]] = {
            "domain": [],
            "application": [],
            "ui": [],
            "tooling": [],
        }

        res = self._run_git(["status", "--porcelain", "-uall"])
        if res.returncode != 0:
            return grouped

        for line in res.stdout.splitlines():
            if not line.strip():
                continue
            # El path comienza después de los primeros 3 caracteres de estado (ej: ' M ', '?? ', 'A  ')
            entry = line[3:].strip()
            # En caso de renombramientos ('R  old -> new')
            if " -> " in entry:
                entry = entry.split(" -> ")[1].strip()

            entry = entry.strip('"')
            layer = classify_file_layer(entry)
            grouped[layer].append(entry)

        return grouped

    def format_commit_message(self, layer: str, message: str) -> str:
        """Asegura que el mensaje de commit contenga el prefijo canónico de la capa."""
        trimmed = message.strip()
        if CONVENTIONAL_PATTERN.match(trimmed):
            return trimmed

        prefix = LAYER_PREFIXES.get(layer, "chore")
        return f"{prefix}: {trimmed}"

    def stage_layer(self, layer: str) -> List[str]:
        """Añade al staging únicamente los archivos de la capa solicitada."""
        grouped = self.get_grouped_status()
        files = grouped.get(layer, [])
        if not files:
            return []

        res = self._run_git(["add", "--"] + files)
        if res.returncode == 0:
            return files
        return []

    def commit_layer(self, layer: str, message: str) -> bool:
        """Realiza el staging de la capa y confirma el commit convencional atómico."""
        staged = self.stage_layer(layer)
        if not staged:
            return False

        formatted_msg = self.format_commit_message(layer, message)
        res = self._run_git(["commit", "-m", formatted_msg])
        return res.returncode == 0

    def render_status_tui(self) -> str:
        """Genera un reporte formateado para la terminal con affordance de colores ANSI."""
        grouped = self.get_grouped_status()
        total_files = sum(len(files) for files in grouped.values())

        if total_files == 0:
            return "✓ El árbol de trabajo está limpio. No hay cambios pendientes."

        layer_labels = {
            "domain": ("🔵", "Dominio Puro (Entidades & Puertos)"),
            "application": ("🟡", "Aplicación & DTOs (Casos de Uso & Stores)"),
            "ui": ("🟢", "Infraestructura & UI (Adaptadores, Routers & Componentes)"),
            "tooling": ("🟣", "Tooling & Soporte (Scripts, Config & CI)"),
        }

        output: List[str] = [
            "============================================================",
            "📦 ESTADO DE CAMBIOS POR CAPAS ARQUITECTÓNICAS (COMMITS ATÓMICOS)",
            "============================================================",
        ]

        for layer_key, (icon, title) in layer_labels.items():
            files = grouped[layer_key]
            if files:
                output.append(f"\n{icon} {title} [{len(files)} archivo(s)]:")
                for f in files:
                    output.append(f"   • {f}")

        output.append("\n------------------------------------------------------------")
        output.append("💡 COMANDOS SUGERIDOS:")
        for layer_key, (icon, _) in layer_labels.items():
            if grouped[layer_key]:
                output.append(f"   agy-stage-layer stage {layer_key}      # Staging de la capa")
                output.append(f'   agy-stage-layer commit {layer_key} "..." # Staging + commit convencional')

        output.append("============================================================")
        return "\n".join(output)

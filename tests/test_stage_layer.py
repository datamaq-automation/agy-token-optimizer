"""Pruebas unitarias para el Asistente de Staging por Capas Arquitectónicas (agy-stage-layer)."""

import os
import subprocess
import tempfile
import unittest

from src.adapters.stage_layer_orchestrator import (
    StageLayerOrchestrator,
    classify_file_layer,
)


class TestStageLayer(unittest.TestCase):
    """Verifica la clasificación quirúrgica y orquestación de commits atómicos por capas."""

    def test_classify_clean_architecture_python_paths(self) -> None:
        """Verifica la clasificación de rutas en Clean Architecture / DDD Python."""
        # Dominio Puro
        self.assertEqual(classify_file_layer("src/domain/entities.py"), "domain")
        self.assertEqual(classify_file_layer("src/core/dominio/medicion.py"), "domain")
        self.assertEqual(classify_file_layer("src/domain/ports.py"), "domain")
        self.assertEqual(classify_file_layer("tests/unit/test_domain_user.py"), "domain")

        # Aplicación & DTOs
        self.assertEqual(classify_file_layer("src/application/use_cases/login.py"), "application")
        self.assertEqual(classify_file_layer("src/core/services/telemetria.py"), "application")
        self.assertEqual(classify_file_layer("tests/unit/test_login_use_case.py"), "application")

        # Infraestructura & Adaptadores / UI
        self.assertEqual(classify_file_layer("src/infrastructure/repositories.py"), "ui")
        self.assertEqual(classify_file_layer("src/adapters/terminal_pruner.py"), "ui")
        self.assertEqual(classify_file_layer("src/app/main.py"), "ui")
        self.assertEqual(classify_file_layer("tests/integration/test_db.py"), "ui")

    def test_classify_fsd_vue_typescript_paths(self) -> None:
        """Verifica la clasificación de rutas en Feature-Sliced Design (FSD) para Vue/TS."""
        # Dominio
        self.assertEqual(classify_file_layer("src/entities/dispositivo/model.ts"), "domain")
        self.assertEqual(classify_file_layer("src/shared/types/telemetria.ts"), "domain")

        # Aplicación
        self.assertEqual(classify_file_layer("src/features/autenticacion/stores/useAuth.ts"), "application")
        self.assertEqual(classify_file_layer("src/app/providers/router.ts"), "application")

        # UI & Componentes
        self.assertEqual(classify_file_layer("src/shared/ui/BaseBadge.vue"), "ui")
        self.assertEqual(classify_file_layer("src/features/graficos/ui/EjeX.vue"), "ui")
        self.assertEqual(classify_file_layer("src/views/DashboardView.vue"), "ui")
        self.assertEqual(classify_file_layer("tests/component/BaseBadge.spec.ts"), "ui")

    def test_classify_tooling_and_scripts_paths(self) -> None:
        """Verifica que scripts y archivos de soporte se segreguen en tooling."""
        self.assertEqual(classify_file_layer("scripts/install_git_hooks.sh"), "tooling")
        self.assertEqual(classify_file_layer(".gitignore"), "tooling")
        self.assertEqual(classify_file_layer("Makefile"), "tooling")
        self.assertEqual(classify_file_layer("pyproject.toml"), "tooling")
        self.assertEqual(classify_file_layer("package.json"), "tooling")
        self.assertEqual(classify_file_layer(".github/workflows/ci.yml"), "tooling")
        self.assertEqual(classify_file_layer("tools/client/agy-preview"), "tooling")

    def test_suggest_commit_message_prefix(self) -> None:
        """Verifica que se sugiera y anteponga el tipo de commit convencional según la capa."""
        orchestrator = StageLayerOrchestrator()
        self.assertEqual(
            orchestrator.format_commit_message("domain", "agregar entidad Medicion"),
            "feat(dominio): agregar entidad Medicion",
        )
        self.assertEqual(
            orchestrator.format_commit_message("application", "feat(aplicacion): orquestar login"),
            "feat(aplicacion): orquestar login",
        )
        self.assertEqual(
            orchestrator.format_commit_message("ui", "ajustar espaciado de tarjeta"),
            "feat(ui): ajustar espaciado de tarjeta",
        )
        self.assertEqual(
            orchestrator.format_commit_message("tooling", "actualizar hooks de git"),
            "chore(tooling): actualizar hooks de git",
        )

    def test_git_status_grouping_and_staging(self) -> None:
        """Verifica el agrupamiento por capas y el staging selectivo en un repositorio git temporal."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_dir, check=True)

            # Crear estructura de archivos simulada
            os.makedirs(os.path.join(tmp_dir, "src", "domain"), exist_ok=True)
            os.makedirs(os.path.join(tmp_dir, "src", "infrastructure"), exist_ok=True)
            os.makedirs(os.path.join(tmp_dir, "scripts"), exist_ok=True)

            domain_file = os.path.join(tmp_dir, "src", "domain", "user.py")
            infra_file = os.path.join(tmp_dir, "src", "infrastructure", "db.py")
            script_file = os.path.join(tmp_dir, "scripts", "deploy.sh")

            with open(domain_file, "w") as f:
                f.write("# domain\n")
            with open(infra_file, "w") as f:
                f.write("# infra\n")
            with open(script_file, "w") as f:
                f.write("# script\n")

            orchestrator = StageLayerOrchestrator(repo_dir=tmp_dir)
            grouped = orchestrator.get_grouped_status()

            self.assertIn("src/domain/user.py", grouped["domain"])
            self.assertIn("src/infrastructure/db.py", grouped["ui"])
            self.assertIn("scripts/deploy.sh", grouped["tooling"])
            self.assertEqual(len(grouped["application"]), 0)

            # Realizar staging selectivo de domain
            staged = orchestrator.stage_layer("domain")
            self.assertIn("src/domain/user.py", staged)

            # Verificar git diff --cached
            res = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            staged_names = res.stdout.strip().splitlines()
            self.assertIn("src/domain/user.py", staged_names)
            self.assertNotIn("src/infrastructure/db.py", staged_names)
            self.assertNotIn("scripts/deploy.sh", staged_names)

    def test_commit_layer_creates_atomic_commit(self) -> None:
        """Verifica que commit_layer realice staging y commit convencional atómico."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_dir, check=True)

            os.makedirs(os.path.join(tmp_dir, "src", "domain"), exist_ok=True)
            domain_file = os.path.join(tmp_dir, "src", "domain", "user.py")
            with open(domain_file, "w") as f:
                f.write("# domain\n")

            orchestrator = StageLayerOrchestrator(repo_dir=tmp_dir)
            success = orchestrator.commit_layer("domain", "agregar entidad de usuario")
            self.assertTrue(success)

            # Verificar log
            res = subprocess.run(
                ["git", "log", "-n", "1", "--pretty=format:%s"],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(res.stdout.strip(), "feat(dominio): agregar entidad de usuario")

    def test_render_status_tui(self) -> None:
        """Verifica el formato visual y glifos del reporte TUI."""
        orchestrator = StageLayerOrchestrator()
        report = orchestrator.render_status_tui()
        self.assertIsInstance(report, str)
        self.assertTrue(len(report) > 0)


if __name__ == "__main__":
    unittest.main()

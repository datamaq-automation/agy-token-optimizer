"""Pruebas unitarias para gate_pre_invocation sensible al contexto."""

import os
import tempfile
import unittest

from hooks.gate_pre_invocation import (
    BUILD_DIRECTIVE,
    ORCHESTRATOR_DIRECTIVE,
    PLAN_DIRECTIVE,
    get_directive,
    is_orchestrator_workspace,
)


class TestGatePreInvocation(unittest.TestCase):
    """Verifica la detección de repositorios orquestadores vs repositorios de producto."""

    def test_orchestrator_repo_detected_by_agents_md_orquestacion(self) -> None:
        """Si AGENTS.md contiene 'orquestación', activa MODO ORQUESTADOR."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agents_path = os.path.join(tmp_dir, "AGENTS.md")
            with open(agents_path, "w", encoding="utf-8") as f:
                f.write("# Repositorio de Orquestación Central\nReglas globales de coordinación.")

            self.assertTrue(is_orchestrator_workspace(tmp_dir))
            directive = get_directive("build", cwd=tmp_dir)
            self.assertEqual(directive, ORCHESTRATOR_DIRECTIVE)
            self.assertNotIn("Ingeniero de Software Full-Stack", directive)
            self.assertNotIn("MODO /BUILD", directive)

    def test_orchestrator_repo_detected_by_agents_md_repo_padre(self) -> None:
        """Si AGENTS.md contiene 'Repo padre', activa MODO ORQUESTADOR."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agents_path = os.path.join(tmp_dir, "AGENTS.md")
            with open(agents_path, "w", encoding="utf-8") as f:
                f.write("# Repo padre del ecosistema Datamaq\n")

            self.assertTrue(is_orchestrator_workspace(tmp_dir))
            directive = get_directive("build", cwd=tmp_dir)
            self.assertEqual(directive, ORCHESTRATOR_DIRECTIVE)

    def test_orchestrator_repo_detected_by_sub_git_folders(self) -> None:
        """Si el workspace contiene subdirectorios con .git independientes, es orquestador."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sub_repo = os.path.join(tmp_dir, "servicio_a")
            sub_git = os.path.join(sub_repo, ".git")
            os.makedirs(sub_git, exist_ok=True)

            self.assertTrue(is_orchestrator_workspace(tmp_dir))
            directive = get_directive("build", cwd=tmp_dir)
            self.assertEqual(directive, ORCHESTRATOR_DIRECTIVE)

    def test_product_repo_uses_standard_build_directive(self) -> None:
        """Un repositorio estándar de desarrollo conserva la directiva BUILD en modo build."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.makedirs(os.path.join(tmp_dir, "src"), exist_ok=True)
            os.makedirs(os.path.join(tmp_dir, "tests"), exist_ok=True)
            agents_path = os.path.join(tmp_dir, "AGENTS.md")
            with open(agents_path, "w", encoding="utf-8") as f:
                f.write("# Módulo de Autenticación\nDesarrollo de features TDD.\n")

            self.assertFalse(is_orchestrator_workspace(tmp_dir))
            directive = get_directive("build", cwd=tmp_dir)
            self.assertTrue(directive.startswith(BUILD_DIRECTIVE))
            self.assertIn("Ingeniero de Software Full-Stack", directive)

    def test_product_repo_uses_standard_plan_directive(self) -> None:
        """Un repositorio estándar en modo plan conserva la directiva PLAN."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertFalse(is_orchestrator_workspace(tmp_dir))
            directive = get_directive("plan", cwd=tmp_dir)
            self.assertTrue(directive.startswith(PLAN_DIRECTIVE))
            self.assertIn("Arquitecto SDD", directive)

    def test_directives_are_single_line(self) -> None:
        """Verifica que las directivas efímeras sean sintéticas y tengan estrictamente 1 línea."""
        self.assertEqual(len(BUILD_DIRECTIVE.strip().splitlines()), 1)
        self.assertEqual(len(PLAN_DIRECTIVE.strip().splitlines()), 1)
        self.assertEqual(len(ORCHESTRATOR_DIRECTIVE.strip().splitlines()), 1)
        self.assertLess(len(BUILD_DIRECTIVE.split()), 25)
        self.assertLess(len(PLAN_DIRECTIVE.split()), 25)
        self.assertLess(len(ORCHESTRATOR_DIRECTIVE.split()), 20)

    def test_real_datamaq_detected_as_orchestrator(self) -> None:
        """Si existe el directorio real de datamaq, verifica su detección determinista."""
        datamaq_dir = "/home/agustin/proyectos_software/datamaq"
        if os.path.isdir(datamaq_dir):
            self.assertTrue(is_orchestrator_workspace(datamaq_dir))
            directive = get_directive("build", cwd=datamaq_dir)
            self.assertEqual(directive, ORCHESTRATOR_DIRECTIVE)


if __name__ == "__main__":
    unittest.main()

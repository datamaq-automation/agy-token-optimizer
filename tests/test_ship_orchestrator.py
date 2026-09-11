"""Tests unitarios para el orquestador desatendido Autopilot Ship (Clean Architecture & TDD)."""

import unittest
from unittest.mock import MagicMock, patch

from src.adapters.ship_orchestrator import AutopilotShipOrchestrator
from src.domain.ports import (
    DiffCompressionResult,
    HealResult,
    ITestFailureHealer,
    ShipPipelineResult,
    TestFailureDetail,
    TestHealResult,
)


class TestAutopilotShipOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_diff_compressor = MagicMock()
        self.mock_diff_compressor.compress_diff.return_value = DiffCompressionResult(
            original_bytes=2000,
            compressed_bytes=800,
            reduction_ratio=0.6,
            clean_diff="diff --git a/src/core.py b/src/core.py\n+def nueva_funcion(): pass\n",
        )

        self.mock_healer = MagicMock()
        self.mock_healer.heal_file.return_value = HealResult(
            success=True,
            file_path="src/core.py",
            execution_time_ms=5.0,
            actions_applied=["ruff_check_fixed", "ruff_formatted"],
        )

        self.mock_test_healer = MagicMock(spec=ITestFailureHealer)
        self.mock_test_healer.isolate_failure.return_value = None

        self.orchestrator = AutopilotShipOrchestrator(
            diff_compressor=self.mock_diff_compressor,
            healer=self.mock_healer,
            test_healer=self.mock_test_healer,
        )

    @patch("subprocess.run")
    def test_ship_pipeline_no_changes(self, mock_run: MagicMock) -> None:
        """Verifica que si no hay cambios en el repositorio, concluya de inmediato sin commitear."""
        # git status --porcelain vacío
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result: ShipPipelineResult = self.orchestrator.run_ship_pipeline(repo_dir=".")

        self.assertTrue(result.success)
        self.assertEqual(result.ci_status, "no_changes")
        self.assertIn("sin cambios", result.commit_message.lower())

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_ship_pipeline_full_cycle_success(self, mock_run: MagicMock, mock_urlopen: MagicMock) -> None:
        """Verifica el ciclo completo: diff -> ollama commit -> add -> commit -> push -> gh run verde."""

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            if "status --porcelain" in cmd_str:
                return MagicMock(returncode=0, stdout=" M src/core.py\n", stderr="")
            if "diff" in cmd_str:
                return MagicMock(returncode=0, stdout="diff content", stderr="")
            if "rev-parse --abbrev-ref HEAD" in cmd_str:
                return MagicMock(returncode=0, stdout="main\n", stderr="")
            if "add" in cmd_str:
                return MagicMock(returncode=0, stdout="", stderr="")
            if "commit" in cmd_str:
                return MagicMock(returncode=0, stdout="[main 123456] feat: nueva funcionalidad", stderr="")
            if "push" in cmd_str:
                return MagicMock(returncode=0, stdout="Pushed to origin/main", stderr="")
            if "gh run list" in cmd_str:
                return MagicMock(
                    returncode=0, stdout="✓ feat: nueva funcionalidad Zero-Trust main push 123 20s", stderr=""
                )
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        # Mock de Ollama response
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "feat(core): agregar nueva funcion deterministica\\n"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result: ShipPipelineResult = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertTrue(result.success)
        self.assertEqual(result.ci_status, "success")
        self.assertIn("feat(core):", result.commit_message)

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_ship_pipeline_ollama_fallback(self, mock_run: MagicMock, mock_urlopen: MagicMock) -> None:
        """Si Ollama no está disponible, debe generar un mensaje determinístico basado en los archivos modificados."""

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            if "status --porcelain" in cmd_str:
                return MagicMock(returncode=0, stdout=" M src/adapters/gateway.py\n", stderr="")
            if "diff" in cmd_str:
                return MagicMock(returncode=0, stdout="diff content", stderr="")
            if "rev-parse --abbrev-ref HEAD" in cmd_str:
                return MagicMock(returncode=0, stdout="main\n", stderr="")
            if "gh run list" in cmd_str:
                return MagicMock(returncode=0, stdout="✓ fix main push 999 15s", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        # Simular fallo de conexión a Ollama
        mock_urlopen.side_effect = Exception("Connection refused")

        result: ShipPipelineResult = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertTrue(result.success)
        self.assertIn("gateway.py", result.commit_message)

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_ship_pipeline_heals_on_ci_failure(self, mock_run: MagicMock, mock_urlopen: MagicMock) -> None:
        """Si gh run reporta fallo 'X', debe intentar auto-sanar con linter local y re-commitear."""
        call_count = {"gh_run": 0, "status": 0}

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            if "status --porcelain" in cmd_str:
                call_count["status"] += 1
                if call_count["status"] == 1:
                    return MagicMock(returncode=0, stdout=" M src/bad_format.py\n", stderr="")
                # Tras el heal, hay cambios formateados para commitear
                return MagicMock(returncode=0, stdout=" M src/bad_format.py\n", stderr="")
            if "diff" in cmd_str:
                return MagicMock(returncode=0, stdout="diff content", stderr="")
            if "rev-parse --abbrev-ref HEAD" in cmd_str:
                return MagicMock(returncode=0, stdout="main\n", stderr="")
            if "gh run list" in cmd_str:
                call_count["gh_run"] += 1
                # Primer check reporta fallo
                return MagicMock(returncode=0, stdout="X fix: ci broken Zero-Trust main push 111 20s", stderr="")
            if "gh run view" in cmd_str:
                return MagicMock(returncode=0, stdout="Error: Ruff check failed on src/bad_format.py", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        # Mock de Ollama response
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "fix(core): reparar formato"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result: ShipPipelineResult = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertTrue(result.success)
        self.assertEqual(result.ci_status, "healed_and_retried")
        self.assertIn("ci_auto_healed", result.healed_errors)

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_ship_pipeline_preventive_tests_heal_and_continue(
        self, mock_run: MagicMock, mock_urlopen: MagicMock
    ) -> None:
        """Si la suite de tests falla preventivamente en local, test_healer debe auto-reparar y continuar."""
        call_count = {"pytest": 0}

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            if "status --porcelain" in cmd_str:
                return MagicMock(returncode=0, stdout=" M src/calc.py\n", stderr="")
            if "pytest" in cmd_str:
                call_count["pytest"] += 1
                if call_count["pytest"] == 1:
                    # Falla inicial
                    return MagicMock(returncode=1, stdout="FAILED tests/test_calc.py::test_add", stderr="")
                # Tras sanación
                return MagicMock(returncode=0, stdout="1 passed", stderr="")
            if "diff" in cmd_str:
                return MagicMock(returncode=0, stdout="diff content", stderr="")
            if "rev-parse --abbrev-ref HEAD" in cmd_str:
                return MagicMock(returncode=0, stdout="main\n", stderr="")
            if "gh run list" in cmd_str:
                return MagicMock(returncode=0, stdout="✓ main push 111 20s", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        # Configurar mock de test_healer
        self.mock_test_healer.isolate_failure.return_value = TestFailureDetail(
            test_file="tests/test_calc.py",
            test_name="test_add",
            target_file="src/calc.py",
            error_line=10,
            error_message="AssertionError",
            traceback_snippet="assert add(1, 2) == 4",
        )
        self.mock_test_healer.heal_test_failure.return_value = TestHealResult(
            success=True,
            target_file="src/calc.py",
            test_file="tests/test_calc.py",
            repaired_code="def add(a, b): return a + b",
            attempts=1,
            execution_time_ms=10.0,
        )

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "feat: auto repaired"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertTrue(result.success)
        self.assertIn("test_auto_healed:calc.py", result.healed_errors)

    @patch("subprocess.run")
    def test_ship_pipeline_preventive_tests_unresolvable_aborts(self, mock_run: MagicMock) -> None:
        """Si la suite de tests falla preventivamente y test_healer no logra repararlo, revierte y aborta."""
        commands_run: list[str] = []

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            commands_run.append(cmd_str)
            if "status --porcelain" in cmd_str:
                return MagicMock(returncode=0, stdout=" M src/calc.py\n", stderr="")
            if "pytest" in cmd_str:
                return MagicMock(returncode=1, stdout="FAILED tests/test_calc.py::test_add", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        self.mock_test_healer.isolate_failure.return_value = TestFailureDetail(
            test_file="tests/test_calc.py",
            test_name="test_add",
            target_file="src/calc.py",
            error_line=10,
            error_message="AssertionError",
            traceback_snippet="assert add(1, 2) == 4",
        )
        self.mock_test_healer.heal_test_failure.return_value = TestHealResult(
            success=False,
            target_file="src/calc.py",
            test_file="tests/test_calc.py",
            repaired_code="",
            attempts=2,
            execution_time_ms=10.0,
            error_message="No se pudo sanar",
        )

        result = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertFalse(result.success)
        self.assertEqual(result.ci_status, "local_test_failed")
        # Verificar que se invocó git restore .
        self.assertTrue(any("git restore ." in cmd for cmd in commands_run))

    @patch("urllib.request.urlopen")
    @patch("subprocess.run")
    def test_ship_pipeline_ci_failure_heals_via_test_healer(self, mock_run: MagicMock, mock_urlopen: MagicMock) -> None:
        """Si CI falla y el log contiene fallo de tests, test_healer debe sanarlo y commitear fix(test-heal)."""
        call_count = {"gh_run": 0}
        commit_messages: list[str] = []

        def fake_run(cmd: list[str], **kwargs) -> MagicMock:
            cmd_str = " ".join(cmd)
            if "commit" in cmd_str:
                commit_messages.append(cmd_str)
            if "status --porcelain" in cmd_str:
                return MagicMock(returncode=0, stdout=" M src/calc.py\n", stderr="")
            if "rev-parse --abbrev-ref HEAD" in cmd_str:
                return MagicMock(returncode=0, stdout="main\n", stderr="")
            if "gh run list" in cmd_str:
                call_count["gh_run"] += 1
                return MagicMock(returncode=0, stdout="X fix: broken Zero-Trust main push 111 20s", stderr="")
            if "gh run view" in cmd_str:
                return MagicMock(returncode=0, stdout="FAILED tests/test_calc.py::test_add - AssertionError", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = fake_run

        self.mock_test_healer.isolate_failure.return_value = TestFailureDetail(
            test_file="tests/test_calc.py",
            test_name="test_add",
            target_file="src/calc.py",
            error_line=10,
            error_message="AssertionError",
            traceback_snippet="assert add(1, 2) == 4",
        )
        self.mock_test_healer.heal_test_failure.return_value = TestHealResult(
            success=True,
            target_file="src/calc.py",
            test_file="tests/test_calc.py",
            repaired_code="def add(a, b): return a + b",
            attempts=1,
            execution_time_ms=10.0,
        )

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "feat: initial commit"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.orchestrator.run_ship_pipeline(repo_dir=".", wait_seconds=0)

        self.assertTrue(result.success)
        self.assertEqual(result.ci_status, "healed_and_retried")
        self.assertIn("ci_auto_healed", result.healed_errors)
        # Verificar el formato de commit requerido: fix(test-heal): auto-reparar fallo en <componente> mediante LLM local
        self.assertTrue(
            any("fix(test-heal): auto-reparar fallo en calc.py mediante LLM local" in msg for msg in commit_messages)
        )


if __name__ == "__main__":
    unittest.main()

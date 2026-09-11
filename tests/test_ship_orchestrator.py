"""Tests unitarios para el orquestador desatendido Autopilot Ship (Clean Architecture & TDD)."""

import unittest
from unittest.mock import MagicMock, patch

from src.adapters.ship_orchestrator import AutopilotShipOrchestrator
from src.domain.ports import DiffCompressionResult, HealResult, ShipPipelineResult


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

        self.orchestrator = AutopilotShipOrchestrator(
            diff_compressor=self.mock_diff_compressor,
            healer=self.mock_healer,
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


if __name__ == "__main__":
    unittest.main()

"""Pruebas unitarias para Poda y Compresión de Salidas de Terminal (TDD)."""

import unittest

from src.adapters.terminal_pruner import TerminalOutputPruner
from src.domain.ports import TerminalPruneResult


class TestTerminalOutputPruner(unittest.TestCase):
    """Pruebas unitarias para el filtrado de ruido en outputs de run_command."""

    def setUp(self) -> None:
        self.pruner = TerminalOutputPruner()

    def test_prune_npm_install_noise(self) -> None:
        """Verifica la poda de barras de progreso y avisos en npm install preservando el resultado."""
        raw_output = (
            "npm warn deprecated inflight@1.0.6: This module is not supported\n" * 50
            + "npm notice Beginning partner audit\n" * 30
            + "added 842 packages, and audited 843 packages in 4s\n"
            + "found 0 vulnerabilities\n"
        )
        result: TerminalPruneResult = self.pruner.prune_output(command="npm install", output=raw_output, exit_code=0)
        self.assertIn("added 842 packages", result.clean_output)
        self.assertGreaterEqual(result.reduction_ratio, 0.80)
        self.assertEqual(result.exit_code, 0)

    def test_prune_pytest_verbose_noise(self) -> None:
        """Verifica la extracción quirúrgica de fallos en pytest sin volcar cientos de líneas de paso."""
        passing_lines = "\n".join(f"tests/test_mod_{i}.py::test_ok PASSED" for i in range(100))
        traceback_block = (
            "FAILURES:\n"
            "___ test_failure ___\n"
            "    assert 1 == 2\n"
            "E   AssertionError: assert 1 == 2\n"
            "tests/test_fail.py:10: AssertionError\n"
            "=== 1 failed, 100 passed in 2.50s ==="
        )
        raw_output = f"{passing_lines}\n{traceback_block}\n"

        result: TerminalPruneResult = self.pruner.prune_output(command="pytest -v", output=raw_output, exit_code=1)
        self.assertIn("AssertionError: assert 1 == 2", result.clean_output)
        self.assertIn("1 failed, 100 passed", result.clean_output)
        self.assertGreaterEqual(result.reduction_ratio, 0.70)
        self.assertEqual(result.exit_code, 1)

    def test_prune_composer_noise(self) -> None:
        """Verifica la compresión de salidas masivas de composer en PHP."""
        raw_output = (
            "Loading composer repositories with package information\n"
            + "Updating dependencies\n"
            + "\n".join(f"  - Installing vendor/pkg-{i} (1.0.{i})" for i in range(120))
            + "\nGenerating autoload files\n"
            + "120 packages you are using are looking for funding.\n"
        )
        result: TerminalPruneResult = self.pruner.prune_output(
            command="composer update", output=raw_output, exit_code=0
        )
        self.assertIn("Generating autoload files", result.clean_output)
        self.assertGreaterEqual(result.reduction_ratio, 0.80)

    def test_terminal_reduction_ratio(self) -> None:
        """Verifica que la reducción de tokens en outputs de terminal sea >= 80%."""
        noisy_output = "progress bar download 100% [====================]\n" * 100 + "Done."
        result: TerminalPruneResult = self.pruner.prune_output(
            command="pip install torch", output=noisy_output, exit_code=0
        )
        self.assertGreaterEqual(result.reduction_ratio, 0.80)

    def test_prune_git_push_progress_collapse(self) -> None:
        """Verifica el colapso determinístico de secuencias continuas de progreso porcentual en git push."""
        fake_git = "Contando objetos: 1%\nContando objetos: 50%\nContando objetos: 100%\n"
        result: TerminalPruneResult = self.pruner.prune_output("git push", fake_git, 0)
        self.assertEqual(result.clean_output, "✓ Objetos transferidos al 100% (comprimido en local)")
        self.assertGreater(result.reduction_ratio, 0.0)

    def test_prune_git_push_with_ansi_carriage_returns(self) -> None:
        """Verifica el colapso de barras con retorno de carro (\\r) y secuencias ANSI."""
        raw_output = (
            "Enumerating objects: 10, done.\n"
            "Counting objects: 10% (1/10)\rCounting objects: 50% (5/10)\rCounting objects: 100% (10/10), done.\n"
            "Writing objects: 10% (1/10)\rWriting objects: 100% (10/10), done.\n"
            "Total 10 (delta 2), reused 0 (delta 0), pack-reused 0\n"
            "To github.com:owner/repo.git\n"
            "   abc1234..def5678 master -> master\n"
        )
        result: TerminalPruneResult = self.pruner.prune_output("git push origin master", raw_output, 0)
        self.assertIn("✓ Objetos transferidos al 100% (comprimido en local)", result.clean_output)
        self.assertIn("Enumerating objects: 10, done.", result.clean_output)
        self.assertIn("master -> master", result.clean_output)
        self.assertNotIn("Counting objects: 10%", result.clean_output)
        self.assertNotIn("Writing objects: 10%", result.clean_output)

    def test_terminal_telemetry_recording(self) -> None:
        """Verifica que el pruner registre telemetría en ITokenTelemetry cuando hay ahorro de tokens."""
        from unittest.mock import MagicMock

        mock_telemetry = MagicMock()
        pruner_with_telemetry = TerminalOutputPruner(telemetry=mock_telemetry)
        fake_git = "Contando objetos: 1%\nContando objetos: 50%\nContando objetos: 100%\n"
        pruner_with_telemetry.prune_output("git push", fake_git, 0)
        self.assertTrue(mock_telemetry.record_event.called)
        event = mock_telemetry.record_event.call_args[0][0]
        self.assertIn("TERMINAL", event.event_type)
        self.assertEqual(event.tool_name, "git")
        self.assertGreater(event.tokens_saved, 0)


if __name__ == "__main__":
    unittest.main()

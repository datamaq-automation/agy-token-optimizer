"""tests/test_local_build_pipeline.py: Pruebas unitarias para el caso de uso LocalBuildPipeline."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.application.local_build_pipeline import LocalBuildPipeline
from src.domain.ports import (
    CodeBuildResult,
    ILocalCodeBuilder,
    ISLMHealer,
    ITestFailureHealer,
    ITokenTelemetry,
    TestFailureDetail,
    TestHealResult,
)


class TestLocalBuildPipeline(unittest.TestCase):
    """Pruebas del orquestador de construcción en bucle cerrado local."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)

        # Crear archivos de prueba
        self.test_file = self.workspace / "tests" / "test_calc.py"
        self.test_file.parent.mkdir(parents=True, exist_ok=True)
        self.test_file.write_text("def test_dummy() -> None: pass\n", encoding="utf-8")

        self.target_file = self.workspace / "src" / "calc.py"

        # Mocks de dependencias
        self.mock_builder = MagicMock(spec=ILocalCodeBuilder)
        self.mock_slm_healer = MagicMock(spec=ISLMHealer)
        self.mock_test_healer = MagicMock(spec=ITestFailureHealer)
        self.mock_telemetry = MagicMock(spec=ITokenTelemetry)

        self.pipeline = LocalBuildPipeline(
            code_builder=self.mock_builder,
            slm_healer=self.mock_slm_healer,
            test_healer=self.mock_test_healer,
            telemetry=self.mock_telemetry,
            max_heal_attempts=2,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_pipeline_success_first_try(self) -> None:
        """Verifica ejecución exitosa cuando el código generado es válido y pasa pruebas a la primera."""
        self.mock_builder.build_implementation.return_value = CodeBuildResult(
            code="def add(a: int, b: int) -> int:\n    return a + b\n",
            model_used="qwen2.5-coder:7b",
            raw_tokens=35,
            success=True,
            execution_time_ms=120.0,
        )

        # Mock runner de tests: retorna 0 (éxito) y salida vacía
        with patch.object(self.pipeline, "_run_pytest", return_value=(0, "1 passed in 0.01s")):
            res = self.pipeline.run(
                test_file=str(self.test_file),
                target_file=str(self.target_file),
                spec_summary="Implementar función add",
            )

        self.assertTrue(res.success)
        self.assertEqual(res.iterations, 1)
        self.assertEqual(res.tokens_saved, 35)
        self.assertTrue(bool(res.trace_id))
        self.assertTrue(self.target_file.exists())
        self.assertIn("def add", self.target_file.read_text(encoding="utf-8"))
        # Verificar que la telemetría grabó el evento con trace_id
        self.mock_telemetry.record_event.assert_called_once()
        recorded_event = self.mock_telemetry.record_event.call_args[0][0]
        self.assertEqual(recorded_event.trace_id, res.trace_id)
        self.assertEqual(recorded_event.hardware_target, "Vulkan:qwen2.5-coder:7b")

    def test_pipeline_fails_when_builder_fails(self) -> None:
        """Verifica que si la iGPU / Ollama falla al generar, el pipeline aborta de inmediato."""
        self.mock_builder.build_implementation.return_value = CodeBuildResult(
            code="",
            model_used="qwen2.5-coder:7b",
            raw_tokens=0,
            success=False,
            execution_time_ms=50.0,
            error_message="Ollama endpoint offline",
        )

        res = self.pipeline.run(
            test_file=str(self.test_file),
            target_file=str(self.target_file),
            spec_summary="Fallar generación",
        )

        self.assertFalse(res.success)
        self.assertEqual(res.iterations, 0)
        self.assertIn("offline", str(res.error_message))
        self.assertFalse(self.target_file.exists())

    def test_pipeline_heals_test_failure_with_local_healer(self) -> None:
        """Verifica auto-sanación con test_healer cuando el test falla inicialmente."""
        self.mock_builder.build_implementation.return_value = CodeBuildResult(
            code="def sub(a: int, b: int) -> int:\n    return a + b\n",  # erróneo
            model_used="qwen2.5-coder:7b",
            raw_tokens=30,
            success=True,
            execution_time_ms=100.0,
        )

        # Simular fallo en primer run de pytest y éxito en el segundo
        pytest_runs = [
            (1, "FAILED tests/test_calc.py::test_sub - AssertionError"),
            (0, "1 passed"),
        ]

        def fake_pytest(target: str, test: str) -> tuple[int, str]:
            return pytest_runs.pop(0)

        self.mock_test_healer.isolate_failure.return_value = TestFailureDetail(
            test_file=str(self.test_file),
            test_name="test_sub",
            target_file=str(self.target_file),
            error_line=2,
            error_message="AssertionError",
            traceback_snippet="def test_sub(): assert sub(5, 3) == 2",
        )
        self.mock_test_healer.heal_test_failure.return_value = TestHealResult(
            success=True,
            target_file=str(self.target_file),
            test_file=str(self.test_file),
            repaired_code="def sub(a: int, b: int) -> int:\n    return a - b\n",
            attempts=1,
            execution_time_ms=200.0,
        )

        with patch.object(self.pipeline, "_run_pytest", side_effect=fake_pytest):
            res = self.pipeline.run(
                test_file=str(self.test_file),
                target_file=str(self.target_file),
                spec_summary="Implementar función sub",
            )

        self.assertTrue(res.success)
        self.assertEqual(res.iterations, 2)
        self.assertTrue(self.target_file.exists())
        self.assertIn("return a - b", self.target_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

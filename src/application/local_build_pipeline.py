"""src/application/local_build_pipeline.py: Orquestador del ciclo de construcción local en iGPU.

Ejecuta el ciclo: Generación en iGPU (Ollama) -> Linter determinístico (Ruff) ->
Auto-sanación de sintaxis (ISLMHealer) -> Tests locales (Pytest) ->
Auto-sanación de fallos de test (ITestFailureHealer) -> Integración en src/.
"""

import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

from src.domain.ports import (
    CodeBuildResult,
    ILocalCodeBuilder,
    ISLMHealer,
    ITestFailureHealer,
    ITokenTelemetry,
    LocalBuildPipelineResult,
    TokenSavingsEvent,
)


class LocalBuildPipeline:
    """Orquestador de construcción en bucle cerrado sobre hardware local ($0 tokens remotos)."""

    def __init__(
        self,
        code_builder: ILocalCodeBuilder,
        slm_healer: Optional[ISLMHealer] = None,
        test_healer: Optional[ITestFailureHealer] = None,
        telemetry: Optional[ITokenTelemetry] = None,
        max_heal_attempts: int = 3,
        ramdisk_path: str = "/dev/shm/agy_build",
    ) -> None:
        self.code_builder = code_builder
        self.slm_healer = slm_healer
        self.test_healer = test_healer
        self.telemetry = telemetry
        self.max_heal_attempts = max_heal_attempts
        self.ramdisk_path = Path(ramdisk_path)

    def _get_staging_path(self, target_file: str) -> Path:
        """Determina la ruta de staging en RAMDisk (/dev/shm) con fallback a tmp."""
        filename = Path(target_file).name
        try:
            if self.ramdisk_path.parent.exists() and os.access(self.ramdisk_path.parent, os.W_OK):
                self.ramdisk_path.mkdir(parents=True, exist_ok=True)
                return self.ramdisk_path / filename
        except Exception:
            pass

        fallback = Path("/tmp/agy_build")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / filename

    def _run_ruff(self, file_path: str) -> bool:
        """Ejecuta ruff check --fix y ruff format determinísticamente en CPU."""
        try:
            subprocess.run(
                ["ruff", "check", "--fix", file_path],
                capture_output=True,
                check=False,
                timeout=10,
            )
            subprocess.run(
                ["ruff", "format", file_path],
                capture_output=True,
                check=False,
                timeout=10,
            )
            return True
        except Exception:
            return False

    def _run_pytest(self, target_file: str, test_file: str) -> Tuple[int, str]:
        """Ejecuta pytest sobre el test_file asociado al target."""
        try:
            env = os.environ.copy()
            target_parent = str(Path(target_file).parent.resolve())
            test_parent = str(Path(test_file).parent.resolve())
            repo_root = str(Path.cwd().resolve())
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{target_parent}:{test_parent}:{repo_root}:{existing_pp}".rstrip(":")

            res = subprocess.run(
                ["pytest", "-q", test_file],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                env=env,
            )
            output = (res.stdout or "") + (res.stderr or "")
            return res.returncode, output
        except Exception as e:
            return 1, str(e)

    def run(
        self,
        test_file: str,
        target_file: str,
        spec_summary: str,
        contract_signatures: str = "",
        model_name: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> LocalBuildPipelineResult:
        """Ejecuta el ciclo de construcción y auto-sanación en bucle cerrado."""
        start_time = time.perf_counter()
        active_trace_id = trace_id or uuid.uuid4().hex[:12]
        test_path = Path(test_file)
        test_content = test_path.read_text(encoding="utf-8") if test_path.exists() else ""

        # 1. Generación de código en iGPU local
        build_res: CodeBuildResult = self.code_builder.build_implementation(
            spec_summary=spec_summary,
            contract_signatures=contract_signatures,
            test_content=test_content,
            target_file_path=target_file,
            model_name=model_name,
            trace_id=active_trace_id,
        )

        if not build_res.success:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return LocalBuildPipelineResult(
                success=False,
                target_file=target_file,
                tokens_saved=0,
                iterations=0,
                execution_time_ms=elapsed_ms,
                trace_id=active_trace_id,
                tokens_per_second=0.0,
                error_message=build_res.error_message or "Fallo en generación de código con iGPU local",
            )

        # 2. Guardar en staging
        staging_file = self._get_staging_path(target_file)
        staging_file.write_text(build_res.code, encoding="utf-8")

        # 3. Linter determinístico L1
        self._run_ruff(str(staging_file))

        # Copiar provisionalmente a destino para que los imports de pytest lo vean
        dest_path = Path(target_file)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staging_file, dest_path)

        # 4. Ciclo de validación y auto-sanación
        iterations = 1
        test_passed = False
        total_tokens = build_res.raw_tokens

        while iterations <= self.max_heal_attempts:
            retcode, pytest_output = self._run_pytest(str(dest_path), test_file)
            if retcode == 0:
                test_passed = True
                break

            # Si falló y tenemos test_healer disponible
            if self.test_healer:
                failure_detail = self.test_healer.isolate_failure(pytest_output)
                if failure_detail:
                    heal_res = self.test_healer.heal_test_failure(failure_detail)
                    if heal_res.success and heal_res.repaired_code:
                        dest_path.write_text(heal_res.repaired_code, encoding="utf-8")
                        self._run_ruff(str(dest_path))
                        iterations += 1
                        continue

            iterations += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if test_passed:
            if self.telemetry:
                event = TokenSavingsEvent(
                    event_type="IGPU_CODE_BUILD",
                    tool_name="local_build_pipeline",
                    tokens_before=total_tokens,
                    tokens_after=0,
                    tokens_saved=total_tokens,
                    latency_ms=elapsed_ms,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    trace_id=active_trace_id,
                    hardware_target=f"Vulkan:{build_res.model_used}",
                )
                self.telemetry.record_event(event)

            return LocalBuildPipelineResult(
                success=True,
                target_file=target_file,
                tokens_saved=total_tokens,
                iterations=iterations,
                execution_time_ms=elapsed_ms,
                trace_id=active_trace_id,
                tokens_per_second=build_res.tokens_per_second,
                error_message=None,
            )
        else:
            return LocalBuildPipelineResult(
                success=False,
                target_file=target_file,
                tokens_saved=0,
                iterations=iterations,
                execution_time_ms=elapsed_ms,
                trace_id=active_trace_id,
                tokens_per_second=0.0,
                error_message=f"Los tests no pasaron tras {iterations} iteraciones de auto-sanación",
            )

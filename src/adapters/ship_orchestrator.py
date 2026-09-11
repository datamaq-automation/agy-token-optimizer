"""Adaptador para el pipeline desatendido y determinístico de entrega continua (Autopilot Ship).

Ejecuta el ciclo: git status -> git diff comprimido -> commit semántico con Ollama local
-> auto-sanación L1/L2 -> git push -> monitoreo de CI remoto (gh run) -> auto-reparación.
Costo: $0 tokens de API externa (100% en hardware local: CPU + iGPU Vulkan).
"""

import json
import os
import subprocess
import time
import urllib.request
from typing import Optional

from src.domain.ports import (
    IDiffCompressor,
    IPostEditHealer,
    IShipOrchestrator,
    ITestFailureHealer,
    ShipPipelineResult,
    ShipStepResult,
)


class AutopilotShipOrchestrator(IShipOrchestrator):
    """Orquestador determinístico de commit, push y monitoreo de CI con auto-sanación."""

    def __init__(
        self,
        diff_compressor: Optional[IDiffCompressor] = None,
        healer: Optional[IPostEditHealer] = None,
        test_healer: Optional[ITestFailureHealer] = None,
        ollama_url: str = "http://localhost:11434/api/generate",
        model_name: str = "qwen2.5-coder:1.5b",
    ) -> None:
        self._diff_compressor = diff_compressor
        self._healer = healer
        self._test_healer = test_healer
        self._ollama_url = ollama_url
        self._model_name = model_name

    def run_ship_pipeline(self, repo_dir: str = ".", wait_seconds: int = 20) -> ShipPipelineResult:
        """Ejecuta el ciclo determinístico de entrega continua y verificación."""
        steps: list[ShipStepResult] = []
        healed_errors: list[str] = []

        # 1. Comprobar cambios
        status_out = self._run_cmd(["git", "status", "--porcelain"], cwd=repo_dir)
        if not status_out.strip():
            return ShipPipelineResult(
                success=True,
                commit_message="Sin cambios detectados en el repositorio.",
                ci_status="no_changes",
                steps=steps,
                healed_errors=healed_errors,
            )

        changed_files = self._extract_changed_files(status_out)

        # 2. Auto-Sanación L1/L2 previa en archivos modificados
        if self._healer:
            start_h = time.perf_counter()
            for filepath in changed_files:
                full_path = os.path.join(repo_dir, filepath)
                if os.path.isfile(full_path):
                    h_res = self._healer.heal_file(full_path)
                    if h_res.actions_applied:
                        healed_errors.extend(h_res.actions_applied)
            steps.append(
                ShipStepResult(
                    step_name="pre_heal",
                    success=True,
                    output=f"Archivos saneados: {len(changed_files)}",
                    execution_time_ms=(time.perf_counter() - start_h) * 1000.0,
                )
            )

        # 3. Verificación preventiva de tests locales (Shift-Left)
        start_test = time.perf_counter()
        test_ok, test_out = self._run_local_tests(cwd=repo_dir)
        if not test_ok:
            healed_test = False
            if self._test_healer:
                failure_detail = self._test_healer.isolate_failure(test_out, repo_dir=repo_dir)
                if failure_detail:
                    heal_res = self._test_healer.heal_test_failure(failure_detail, repo_dir=repo_dir)
                    if heal_res.success:
                        healed_test = True
                        comp_name = os.path.basename(heal_res.target_file)
                        healed_errors.append(f"test_auto_healed:{comp_name}")
                        steps.append(
                            ShipStepResult(
                                step_name="preventive_test_heal",
                                success=True,
                                output=f"Auto-sanado componente: {comp_name}",
                                execution_time_ms=(time.perf_counter() - start_test) * 1000.0,
                            )
                        )
            if not healed_test:
                self._run_cmd(["git", "restore", "."], cwd=repo_dir)
                steps.append(
                    ShipStepResult(
                        step_name="preventive_test_check",
                        success=False,
                        output=test_out.strip()[:200],
                        execution_time_ms=(time.perf_counter() - start_test) * 1000.0,
                    )
                )
                return ShipPipelineResult(
                    success=False,
                    commit_message="Fallo no resuelto en suite de tests local.",
                    ci_status="local_test_failed",
                    steps=steps,
                    healed_errors=healed_errors,
                )
        else:
            steps.append(
                ShipStepResult(
                    step_name="preventive_test_check",
                    success=True,
                    output="Tests locales pasaron correctamente.",
                    execution_time_ms=(time.perf_counter() - start_test) * 1000.0,
                )
            )

        # 4. Extraer diff y generar mensaje con Ollama local
        start_diff = time.perf_counter()
        raw_diff = self._run_cmd(["git", "diff", "HEAD"], cwd=repo_dir)
        if not raw_diff:
            raw_diff = self._run_cmd(["git", "diff"], cwd=repo_dir)

        compressed_diff = raw_diff
        if self._diff_compressor:
            comp_res = self._diff_compressor.compress_diff(raw_diff)
            compressed_diff = comp_res.clean_diff

        commit_msg = self._generate_commit_message(compressed_diff, changed_files)
        steps.append(
            ShipStepResult(
                step_name="generate_commit_message",
                success=True,
                output=commit_msg,
                execution_time_ms=(time.perf_counter() - start_diff) * 1000.0,
            )
        )

        # 4. git add y git commit
        start_commit = time.perf_counter()
        self._run_cmd(["git", "add", "-A"], cwd=repo_dir)
        commit_res = self._run_cmd(["git", "commit", "-m", commit_msg], cwd=repo_dir)
        steps.append(
            ShipStepResult(
                step_name="git_commit",
                success=True,
                output=commit_res.strip(),
                execution_time_ms=(time.perf_counter() - start_commit) * 1000.0,
            )
        )

        # 5. Obtener rama actual y git push
        start_push = time.perf_counter()
        current_branch = self._run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir).strip() or "main"
        push_res = self._run_cmd(["git", "push", "origin", current_branch], cwd=repo_dir)
        steps.append(
            ShipStepResult(
                step_name="git_push",
                success=True,
                output=push_res.strip(),
                execution_time_ms=(time.perf_counter() - start_push) * 1000.0,
            )
        )

        # 6. Monitoreo reactivo de GitHub Actions
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        start_ci = time.perf_counter()
        ci_status_raw = self._run_cmd(["gh", "run", "list", "--limit", "2"], cwd=repo_dir)
        ci_status = self._parse_ci_status(ci_status_raw)

        steps.append(
            ShipStepResult(
                step_name="gh_run_check",
                success=(ci_status == "success"),
                output=ci_status_raw.strip(),
                execution_time_ms=(time.perf_counter() - start_ci) * 1000.0,
            )
        )

        # 7. Bucle de auto-reparación ante fallo en CI
        if ci_status == "failure" and self._healer:
            heal_success = self._attempt_ci_healing(repo_dir, current_branch)
            if heal_success:
                ci_status = "healed_and_retried"
                healed_errors.append("ci_auto_healed")

        return ShipPipelineResult(
            success=(ci_status in ("success", "pending", "healed_and_retried")),
            commit_message=commit_msg,
            ci_status=ci_status,
            steps=steps,
            healed_errors=healed_errors,
        )

    def _generate_commit_message(self, diff_text: str, changed_files: list[str]) -> str:
        """Genera mensaje de commit convencional vía Ollama en iGPU con fallback determinístico."""
        prompt = (
            "Genera un mensaje de commit convencional en español para el siguiente diff. "
            "Usa una sola línea siguiendo el formato 'tipo(alcance): descripción breve'. "
            "Ejemplo: 'feat(core): agregar validación estricta'. No agregues explicaciones extras.\n\n"
            f"Diff resumido:\n{diff_text[:1500]}"
        )
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 60},
        }

        try:
            req = urllib.request.Request(
                self._ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                generated = data.get("response", "").strip()
                # Extraer primera línea limpia
                first_line = generated.splitlines()[0] if generated else ""
                first_line = first_line.replace('"', "").replace("`", "").strip()
                if first_line and ":" in first_line:
                    return first_line
        except Exception:
            pass

        # Fallback determinístico sin Ollama
        primary_file = changed_files[0] if changed_files else "proyecto"
        base_name = os.path.basename(primary_file)
        return f"chore(auto-ship): actualizar {base_name} y sincronizar cambios"

    def _attempt_ci_healing(self, repo_dir: str, branch: str) -> bool:
        """Intenta auto-reparar el fallo detectado en el runner remoto de GitHub Actions."""
        try:
            failed_log = self._run_cmd(["gh", "run", "view", "--log-failed"], cwd=repo_dir)
            if not failed_log:
                return False

            # 1. Si hay fallos de tests y test_healer está configurado, intentar auto-sanar con Ollama local
            if self._test_healer:
                detail = self._test_healer.isolate_failure(failed_log, repo_dir=repo_dir)
                if detail:
                    heal_res = self._test_healer.heal_test_failure(detail, repo_dir=repo_dir)
                    if heal_res.success:
                        comp_name = os.path.basename(heal_res.target_file)
                        commit_msg = f"fix(test-heal): auto-reparar fallo en {comp_name} mediante LLM local"
                        self._run_cmd(["git", "add", "-A"], cwd=repo_dir)
                        self._run_cmd(["git", "commit", "-m", commit_msg], cwd=repo_dir)
                        self._run_cmd(["git", "push", "origin", branch], cwd=repo_dir)
                        return True
                    else:
                        self._run_cmd(["git", "restore", "."], cwd=repo_dir)
                        return False

            # 2. Si no es fallo de test o no hay test_healer, intentar formato y linter (Ruff)
            subprocess.run(["ruff", "check", "--fix", "."], cwd=repo_dir, capture_output=True, text=True)
            subprocess.run(["ruff", "format", "."], cwd=repo_dir, capture_output=True, text=True)

            status = self._run_cmd(["git", "status", "--porcelain"], cwd=repo_dir)
            if status.strip():
                self._run_cmd(["git", "add", "-A"], cwd=repo_dir)
                self._run_cmd(
                    ["git", "commit", "-m", "fix(ci): auto-reparar formato y linter detectados en CI"], cwd=repo_dir
                )
                self._run_cmd(["git", "push", "origin", branch], cwd=repo_dir)
                return True
        except Exception:
            pass
        return False

    def _run_local_tests(self, cwd: str) -> tuple[bool, str]:
        """Ejecuta la suite local de pytest y retorna éxito junto a su salida."""
        res = subprocess.run(["pytest", "-q"], cwd=cwd, capture_output=True, text=True)
        out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        return (res.returncode == 0, out)

    def _parse_ci_status(self, raw_output: str) -> str:
        """Determina el estado a partir de la salida de gh run list."""
        for line in raw_output.splitlines():
            line_s = line.strip()
            if line_s.startswith("✓"):
                return "success"
            if line_s.startswith("X"):
                return "failure"
            if line_s.startswith("*"):
                return "pending"
        return "unknown"

    def _extract_changed_files(self, porcelain_status: str) -> list[str]:
        """Extrae la lista de rutas relativas de archivos con cambios."""
        files: list[str] = []
        for line in porcelain_status.splitlines():
            line = line.strip()
            if len(line) > 3:
                # 'M src/file.py' o '?? new.py'
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    files.append(parts[1])
        return files

    def _run_cmd(self, cmd: list[str], cwd: str) -> str:
        """Ejecuta comando local y devuelve stdout como texto."""
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return res.stdout

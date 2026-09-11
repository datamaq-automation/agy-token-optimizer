#!/usr/bin/env python3
"""Script CLI para Autopilot Ship: entrega determinística desatendida a $0 tokens de API.

Flujo:
  1. git status + git diff comprimido.
  2. Generación de commit semántico con Ollama (qwen2.5-coder:1.5b en iGPU local).
  3. Pre-sanación determinística L1/L2 (Ruff).
  4. git add -A + git commit.
  5. git push (dispara pre-push Gauntlet local).
  6. sleep 20 & gh run list --limit 2.
  7. Auto-reparación en bucle cerrado si CI reporta fallos.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.adapters.ast_pruner import PythonASTPruner
from src.adapters.diff_compressor import RegexDiffCompressor
from src.adapters.hardware_healer import DeterministicHardwareHealer
from src.adapters.ship_orchestrator import AutopilotShipOrchestrator
from src.adapters.test_healer import OllamaTestFailureHealer


def main() -> None:
    repo_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print("======================================================================")
    print(" 🚀 AGY AUTOPILOT SHIP: ENTREGA Y AUTO-SANACIÓN DESATENDIDA ($0 TOKENS)")
    print("======================================================================")

    ast_pruner = PythonASTPruner()
    test_healer = OllamaTestFailureHealer(ast_pruner=ast_pruner)
    diff_comp = RegexDiffCompressor()
    healer = DeterministicHardwareHealer()
    orchestrator = AutopilotShipOrchestrator(
        diff_compressor=diff_comp,
        healer=healer,
        test_healer=test_healer,
    )

    result = orchestrator.run_ship_pipeline(repo_dir=repo_dir, wait_seconds=20)

    print(f"\n[MENSAJE DE COMMIT]: {result.commit_message}")
    print(f"[ESTADO DE CI]:      {result.ci_status.upper()}")

    for step in result.steps:
        status_sym = "✓" if step.success else "✗"
        print(f"  [{status_sym}] {step.step_name:<24} ({step.execution_time_ms:.1f}ms)")
        if step.output:
            first_line = step.output.strip().splitlines()[0]
            print(f"      └─ {first_line[:80]}")

    if result.healed_errors:
        print(f"\n[AUTO-SANACIONES APLICADAS]: {', '.join(result.healed_errors)}")

    print("======================================================================")
    if result.success:
        print("✅ CICLO DE ENTREGA Y VERIFICACIÓN COMPLETADO CON ÉXITO")
        sys.exit(0)
    else:
        print("⚠️  EL PIPELINE REQUIERE ATENCIÓN MANUAL EN CI")
        sys.exit(1)


if __name__ == "__main__":
    main()

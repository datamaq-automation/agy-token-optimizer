#!/usr/bin/env python3
"""Hook PostToolUse: Auto-sanador determinístico en hardware local (CPU/RAM).

Ejecuta ruff check --fix y ruff format instantáneamente tras cada write_to_file
o replace_file_content sobre archivos Python, eliminando turnos de corrección
del LLM ($0 tokens consumidos).
"""

import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, "/home/agustin/proyectos_software/agy-token-optimizer")

try:
    from src.adapters.hardware_healer import DeterministicHardwareHealer
    from src.adapters.polyglot_healer import PolyglotHardwareHealer
    from src.adapters.slm_healer import OllamaVulkanSLMHealer
    from src.adapters.token_telemetry import SQLiteTokenTelemetry

    _slm = OllamaVulkanSLMHealer()
    _healer = DeterministicHardwareHealer(slm_healer=_slm)
    _polyglot_healer = PolyglotHardwareHealer(slm_healer=_slm)
    _telemetry = SQLiteTokenTelemetry()
except Exception:
    _healer = None
    _polyglot_healer = None
    _telemetry = None


def heal_target_file(filepath: str) -> None:
    if not filepath or not os.path.isfile(filepath):
        return

    try:
        from src.domain.ports import TokenSavingsEvent
    except ImportError:
        return  # Sin el paquete, _healer tambien es None: no habria nada que sanar.

    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == ".py":
        if _healer is not None:
            res = _healer.heal_file(filepath)
            if _telemetry is not None and res.success:
                if "slm_igpu_healed" in res.actions_applied:
                    _telemetry.record_event(
                        TokenSavingsEvent(
                            event_type="IGPU_HEAL",
                            tool_name="qwen2.5-coder:1.5b",
                            tokens_before=1500,
                            tokens_after=0,
                            tokens_saved=1500,
                            latency_ms=res.execution_time_ms,
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                elif "ruff_check_fixed" in res.actions_applied:
                    _telemetry.record_event(
                        TokenSavingsEvent(
                            event_type="LINTER_FIX",
                            tool_name="ruff_check",
                            tokens_before=500,
                            tokens_after=0,
                            tokens_saved=500,
                            latency_ms=res.execution_time_ms,
                            timestamp=datetime.now().isoformat(),
                        )
                    )
        else:
            # Fallback directo
            subprocess.run(["ruff", "check", "--fix", filepath], capture_output=True, check=False)
            subprocess.run(["ruff", "format", filepath], capture_output=True, check=False)
    elif ext in {".php", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".mts"}:
        if _polyglot_healer is not None:
            p_res = _polyglot_healer.heal_file(filepath)
            if _telemetry is not None and p_res.success:
                if any("slm_repaired" in a for a in p_res.actions_applied):
                    _telemetry.record_event(
                        TokenSavingsEvent(
                            event_type="POLYGLOT_SLM_HEAL",
                            tool_name=f"qwen_{p_res.language}",
                            tokens_before=1500,
                            tokens_after=0,
                            tokens_saved=1500,
                            latency_ms=p_res.execution_time_ms,
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                elif any("syntax_valid" in a for a in p_res.actions_applied):
                    _telemetry.record_event(
                        TokenSavingsEvent(
                            event_type="POLYGLOT_L1_VALID",
                            tool_name=f"linter_{p_res.language}",
                            tokens_before=300,
                            tokens_after=0,
                            tokens_saved=300,
                            latency_ms=p_res.execution_time_ms,
                            timestamp=datetime.now().isoformat(),
                        )
                    )


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            tool_call = payload.get("toolCall", {})
            args = tool_call.get("args", {})
            target_file = args.get("TargetFile", "")
            heal_target_file(target_file)
    except Exception:
        pass


if __name__ == "__main__":
    main()

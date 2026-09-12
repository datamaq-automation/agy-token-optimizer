#!/usr/bin/env python3
"""audit_telemetry.py: Analizador y auto-optimizador de telemetría de construcción local.

Inspecciona logs estructurados (~/.agents/token_savings.log), agrupa por trace_id,
calcula métricas de rendimiento en iGPU (tok/s, latencia, tasa de éxito) y
emite recomendaciones o auto-remediación de parámetros.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

LOG_FILE = Path.home() / ".agents" / "token_savings.log"


def load_recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Carga los últimos N eventos estructurados del log de telemetría."""
    if not LOG_FILE.exists():
        return []

    events: List[Dict[str, Any]] = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"⚠️ Error leyendo telemetría: {e}")
        return []

    return list(reversed(events))


def analyze_build_telemetry(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza métricas agrupadas por trace_id y tipos de evento."""
    build_events = [e for e in events if e.get("event_type") == "IGPU_CODE_BUILD"]
    linter_events = [e for e in events if e.get("event_type") == "LINTER_FIX"]
    terminal_events = [e for e in events if e.get("event_type") == "TERMINAL_PRUNE"]

    total_tokens_saved = sum(e.get("tokens_saved", 0) for e in events)

    # Agrupación por trace_id
    traces: Dict[str, List[Dict[str, Any]]] = {}
    for e in events:
        tid = e.get("trace_id")
        if tid:
            traces.setdefault(tid, []).append(e)

    build_summaries: List[Dict[str, Any]] = []
    for be in build_events:
        tokens = be.get("tokens_saved", 0)
        latency_ms = be.get("latency_ms", 0.0)
        tok_sec = (tokens / (latency_ms / 1000.0)) if latency_ms > 0 else 0.0
        build_summaries.append(
            {
                "trace_id": be.get("trace_id", "N/A"),
                "timestamp": be.get("timestamp", ""),
                "tokens": tokens,
                "latency_ms": latency_ms,
                "tok_per_sec": tok_sec,
                "hardware": be.get("hardware_target", "Vulkan"),
            }
        )

    return {
        "total_events": len(events),
        "total_tokens_saved": total_tokens_saved,
        "build_count": len(build_events),
        "linter_count": len(linter_events),
        "terminal_prune_count": len(terminal_events),
        "unique_traces": len(traces),
        "builds": build_summaries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditor y analizador de telemetría de construcción local en hardware."
    )
    parser.add_argument("--limit", type=int, default=50, help="Cantidad de eventos a inspeccionar (default: 50)")
    parser.add_argument("--json", action="store_true", help="Emitir reporte en formato JSON")

    args = parser.parse_args()

    events = load_recent_events(limit=args.limit)
    report = analyze_build_telemetry(events)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 70)
    print(" 📊 REPORTE DE TELEMETRÍA DE CONSTRUCCIÓN LOCAL (iGPU Vulkan / CPU)")
    print("=" * 70)
    print(f" • Eventos auditados : {report['total_events']}")
    print(f" • Tokens ahorrados  : {report['total_tokens_saved']:,} ($0 costo de API)")
    print(f" • Construcciones iGPU : {report['build_count']}")
    print(f" • Auto-correcciones Ruff: {report['linter_count']}")
    print(f" • Podas de terminal   : {report['terminal_prune_count']}")
    print(f" • Trazas correlacionadas : {report['unique_traces']}")
    print("-" * 70)

    if report["builds"]:
        print(f"{'Trace ID':<14} | {'Tokens':<8} | {'Latencia':<12} | {'Throughput':<12} | {'Hardware'}")
        print("-" * 70)
        for b in report["builds"]:
            print(
                f"{b['trace_id']:<14} | "
                f"{b['tokens']:<8} | "
                f"{b['latency_ms']:>8.1f} ms | "
                f"{b['tok_per_sec']:>8.1f} tok/s | "
                f"{b['hardware']}"
            )
    else:
        print("ℹ️ No se registraron eventos recientes de construcción directa en iGPU.")

    print("=" * 70)
    print("💡 [Diagnóstico de Auto-Remediación]:")
    if report["builds"]:
        avg_tok_sec = sum(b["tok_per_sec"] for b in report["builds"]) / len(report["builds"])
        if avg_tok_sec < 10.0:
            print("  ⚠️ Alerta: Throughput de inferencia bajo (< 10 tok/s).")
            print("     Recomendación: Ejecutar 'agy-opt igpu-tune' para verificar aceleración Vulkan.")
        else:
            print(f"  ✅ Rendimiento óptimo en hardware local ({avg_tok_sec:.1f} tok/s promedio).")
    else:
        print("  ✅ Telemetría activa y lista para auditar próximas corridas de construcción.")


if __name__ == "__main__":
    main()

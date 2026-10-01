#!/usr/bin/env python3
"""Selector directo del backend de modelos para AGY.

Permite decidir si conviene priorizar Google o DeepSeek desde la línea de comandos
sin tener que disparar la cascada HTTP completa.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.application.model_arbitrage_policy import resolve_model_arbitrage


def choose_model_backend(
    google_quota_remaining_pct: float,
    task_complexity: str = "standard",
    now: Optional[datetime] = None,
):
    """Devuelve la decisión de arbitraje conjuntando cuota, horario y tipo de tarea."""
    return resolve_model_arbitrage(
        google_quota_remaining_pct=google_quota_remaining_pct,
        task_complexity=task_complexity,
        now=now,
    )


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"El valor de --time debe ser ISO-8601 válido. Recibido: {value!r}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Selecciona el backend óptimo según la política Google vs DeepSeek de AGY.",
    )
    parser.add_argument("--quota", "-q", type=float, default=100.0, help="Cuota restante de Google en porcentaje.")
    parser.add_argument(
        "--task", "-t", default="standard", help="Tipo de tarea: standard, audit, massive_audit, spec_heavy, etc."
    )
    parser.add_argument(
        "--time",
        "-T",
        default=None,
        help="Momento de decisión en formato ISO-8601 (ej. 2026-10-01T18:00:00-03:00).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Muestra la salida JSON con indentación para lectura humana.",
    )
    args = parser.parse_args()

    decision = choose_model_backend(
        google_quota_remaining_pct=args.quota,
        task_complexity=args.task,
        now=_parse_time(args.time),
    )

    payload = {
        "provider": decision.provider,
        "tier": decision.tier.value,
        "reason": decision.reason,
        "quota_remaining_pct": decision.quota_remaining_pct,
        "offpeak_window_active": decision.offpeak_window_active,
        "task_complexity": decision.task_complexity,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

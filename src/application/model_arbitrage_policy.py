"""Caso de uso para resolver la política económica y temporal del arbitraje LLM.

Expone un punto de entrada de aplicación estable para la selección del proveedor más
rentable en cada ventana operacional.
"""

from datetime import datetime
from typing import Optional

from src.adapters.model_arbitrage import GoogleDeepSeekArbiter, select_provider_by_policy
from src.domain.ports import ModelArbitrageDecision


class ResolveModelArbitrageUseCase:
    """Caso de uso del arbitraje entre Google y DeepSeek."""

    def __init__(self, arbiter: Optional[GoogleDeepSeekArbiter] = None) -> None:
        self._arbiter = arbiter or GoogleDeepSeekArbiter()

    def execute(
        self,
        google_quota_remaining_pct: float,
        task_complexity: str = "standard",
        now: Optional[datetime] = None,
    ) -> ModelArbitrageDecision:
        return self._arbiter.decide(
            google_quota_remaining_pct=google_quota_remaining_pct,
            task_complexity=task_complexity,
            now=now,
        )


def resolve_model_arbitrage(
    google_quota_remaining_pct: float,
    task_complexity: str = "standard",
    now: Optional[datetime] = None,
) -> ModelArbitrageDecision:
    return select_provider_by_policy(
        google_quota_remaining_pct=google_quota_remaining_pct,
        task_complexity=task_complexity,
        now=now,
    )


__all__ = [
    "ResolveModelArbitrageUseCase",
    "resolve_model_arbitrage",
    "select_provider_by_policy",
]

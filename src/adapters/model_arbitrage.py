"""Adaptador de arbitraje económico y temporal entre Google y DeepSeek.

Responde a la política documentada en ADR-0008: prioriza la cuota plana de Google
mientras haya remanente suficiente; usa DeepSeek en la ventana off-peak para tareas
pesadas; y aplica un bridge por agotamiento de cuota para evitar rate limits.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional
from zoneinfo import ZoneInfo

from src.domain.ports import IModelArbitrator, ModelArbitrageDecision, ModelArbitrageTier

_ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
_OFFPEAK_START = time(13, 30)
_OFFPEAK_END = time(22, 0)


def is_deepseek_offpeak(now: Optional[datetime] = None) -> bool:
    """Retorna True si el horario local coincide con la ventana off-peak argentina."""
    candidate = now or datetime.now(_ARGENTINA_TZ)
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=_ARGENTINA_TZ)
    local_now = candidate.astimezone(_ARGENTINA_TZ)
    current_time = local_now.timetz()
    return _OFFPEAK_START <= current_time <= _OFFPEAK_END


class GoogleDeepSeekArbiter(IModelArbitrator):
    """Implementación concreta del arbitraje entre cuota disponible y descuento off-peak."""

    @staticmethod
    def _is_heavy_task(task_complexity: str) -> bool:
        normalized = (task_complexity or "standard").lower()
        heavy_markers = {
            "massive",
            "massive_audit",
            "audit",
            "architectural",
            "spec_heavy",
            "large",
            "reasoning",
            "planning",
        }
        return normalized in heavy_markers or "audit" in normalized or "plan" in normalized

    def decide(
        self,
        google_quota_remaining_pct: float,
        task_complexity: str = "standard",
        now: Optional[datetime] = None,
    ) -> ModelArbitrageDecision:
        """Elige el proveedor óptimo según cuota restante, horario y magnitud de la tarea."""
        quota = float(google_quota_remaining_pct)
        offpeak_active = is_deepseek_offpeak(now)
        heavy_task = self._is_heavy_task(task_complexity)

        if quota <= 5.0:
            return ModelArbitrageDecision(
                provider="deepseek",
                tier=ModelArbitrageTier.DEEPSEEK_BRIDGE,
                reason="La cuota de Google está cercana a agotarse; se activa el bridge de continuidad.",
                quota_remaining_pct=quota,
                offpeak_window_active=offpeak_active,
                task_complexity=task_complexity,
            )

        if offpeak_active and heavy_task:
            return ModelArbitrageDecision(
                provider="deepseek",
                tier=ModelArbitrageTier.DEEPSEEK_OFFPEAK,
                reason="Se aprovecha la ventana off-peak de DeepSeek para tareas masivas y de razonamiento.",
                quota_remaining_pct=quota,
                offpeak_window_active=True,
                task_complexity=task_complexity,
            )

        return ModelArbitrageDecision(
            provider="google",
            tier=ModelArbitrageTier.GOOGLE_FIRST,
            reason="La cuota plana de Google sigue disponible y no se justifica migrar aún a DeepSeek.",
            quota_remaining_pct=quota,
            offpeak_window_active=offpeak_active,
            task_complexity=task_complexity,
        )


def select_provider_by_policy(
    google_quota_remaining_pct: float,
    task_complexity: str = "standard",
    now: Optional[datetime] = None,
) -> ModelArbitrageDecision:
    """Convenience wrapper para resolver la política económica y temporal."""
    return GoogleDeepSeekArbiter().decide(
        google_quota_remaining_pct=google_quota_remaining_pct,
        task_complexity=task_complexity,
        now=now,
    )


__all__ = [
    "GoogleDeepSeekArbiter",
    "is_deepseek_offpeak",
    "select_provider_by_policy",
]

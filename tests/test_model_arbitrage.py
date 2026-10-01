import unittest
from datetime import datetime

from src.adapters.model_arbitrage import GoogleDeepSeekArbiter, is_deepseek_offpeak


class TestModelArbitragePolicy(unittest.TestCase):
    def test_google_first_when_quota_is_abundant(self) -> None:
        arbiter = GoogleDeepSeekArbiter()
        decision = arbiter.decide(
            google_quota_remaining_pct=42.0,
            task_complexity="standard",
            now=datetime.fromisoformat("2026-10-01T09:00:00+00:00"),
        )
        self.assertEqual(decision.provider, "google")
        self.assertEqual(decision.tier.value, "google_first")

    def test_deepseek_offpeak_for_heavy_reasoning(self) -> None:
        arbiter = GoogleDeepSeekArbiter()
        decision = arbiter.decide(
            google_quota_remaining_pct=90.0,
            task_complexity="massive_audit",
            now=datetime.fromisoformat("2026-10-01T18:00:00-03:00"),
        )
        self.assertEqual(decision.provider, "deepseek")
        self.assertEqual(decision.tier.value, "deepseek_offpeak")

    def test_bridge_to_deepseek_when_google_quota_is_low(self) -> None:
        arbiter = GoogleDeepSeekArbiter()
        decision = arbiter.decide(
            google_quota_remaining_pct=2.0,
            task_complexity="standard",
            now=datetime.fromisoformat("2026-10-01T15:00:00-03:00"),
        )
        self.assertEqual(decision.provider, "deepseek")
        self.assertEqual(decision.tier.value, "deepseek_bridge")

    def test_argentina_window_helper(self) -> None:
        self.assertTrue(is_deepseek_offpeak(datetime.fromisoformat("2026-10-01T18:00:00-03:00")))
        self.assertFalse(is_deepseek_offpeak(datetime.fromisoformat("2026-10-01T09:00:00-03:00")))

    def test_429_from_google_moves_deepseek_to_front(self) -> None:
        from skills.token_optimizer.scripts.model_cascade_router import reorder_providers_after_quota_error

        providers = [
            {"provider": "gemini", "name": "Gemini 2.0 Flash"},
            {"provider": "deepseek", "name": "DeepSeek V3"},
            {"provider": "ollama", "name": "Ollama Local"},
        ]

        reordered = reorder_providers_after_quota_error(providers, "gemini", 429)

        self.assertEqual(reordered[0]["provider"], "deepseek")
        self.assertEqual(reordered[1]["provider"], "gemini")


if __name__ == "__main__":
    unittest.main()

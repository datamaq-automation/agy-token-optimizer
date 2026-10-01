import unittest
from datetime import datetime

from skills.token_optimizer.scripts.model_backend_selector import choose_model_backend


class TestBackendSelectorCLI(unittest.TestCase):
    def test_google_first_selection(self) -> None:
        decision = choose_model_backend(
            google_quota_remaining_pct=42.0,
            task_complexity="standard",
            now=datetime.fromisoformat("2026-10-01T09:00:00+00:00"),
        )
        self.assertEqual(decision.provider, "google")
        self.assertEqual(decision.tier.value, "google_first")

    def test_deepseek_selection_for_heavy_audit(self) -> None:
        decision = choose_model_backend(
            google_quota_remaining_pct=90.0,
            task_complexity="massive_audit",
            now=datetime.fromisoformat("2026-10-01T18:00:00-03:00"),
        )
        self.assertEqual(decision.provider, "deepseek")
        self.assertEqual(decision.tier.value, "deepseek_offpeak")


if __name__ == "__main__":
    unittest.main()

"""Pruebas unitarias para el sistema de telemetría y logs de ahorro de tokens."""

import json
import os
import shutil
import tempfile
import unittest

from src.adapters.token_telemetry import SQLiteTokenTelemetry

from src.domain.ports import SavingsSummary, TokenSavingsEvent


class TestTokenTelemetry(unittest.TestCase):
    """Pruebas unitarias para el registro de auditoría y métricas de tokens evitados."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "token_savings.log")
        self.db_file = os.path.join(self.temp_dir, "telemetry.db")
        self.telemetry = SQLiteTokenTelemetry(db_path=self.db_file, log_file_path=self.log_file)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_token_savings_event(self) -> None:
        """Verifica que se registre un evento con tokens previos, posteriores y ahorrados."""
        event = TokenSavingsEvent(
            event_type="AST_PRUNE",
            tool_name="prune_python_ast",
            tokens_before=1200,
            tokens_after=300,
            tokens_saved=900,
            latency_ms=3.5,
            timestamp="2026-09-06T14:00:00",
        )
        self.telemetry.record_event(event)

        # Verificar que el log estructurado JSONL contenga el evento
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        data = json.loads(lines[0])
        self.assertEqual(data["event_type"], "AST_PRUNE")
        self.assertEqual(data["tokens_saved"], 900)

        # Verificar que la base de datos SQLite guarde el evento
        recent = self.telemetry.get_recent_events(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].event_type, "AST_PRUNE")
        self.assertEqual(recent[0].tokens_saved, 900)

    def test_aggregate_savings_report(self) -> None:
        """Verifica que el agregador calcule la suma total de tokens y dinero estimado ahorrado."""
        e1 = TokenSavingsEvent(
            event_type="AST_PRUNE",
            tool_name="prune_python_ast",
            tokens_before=1000,
            tokens_after=200,
            tokens_saved=800,
            latency_ms=2.0,
            timestamp="2026-09-06T14:01:00",
        )
        e2 = TokenSavingsEvent(
            event_type="CACHE_HIT",
            tool_name="semantic_cache",
            tokens_before=1500,
            tokens_after=0,
            tokens_saved=1500,
            latency_ms=1.5,
            timestamp="2026-09-06T14:02:00",
        )
        self.telemetry.record_event(e1)
        self.telemetry.record_event(e2)

        summary: SavingsSummary = self.telemetry.get_summary()
        self.assertEqual(summary.total_tokens_saved, 2300)
        self.assertGreater(summary.total_cost_saved_usd, 0.0)

    def test_metrics_breakdown_by_event_type(self) -> None:
        """Verifica el desglose de métricas por tipo: AST_PRUNE, CACHE_HIT, DIFF_COMPRESS, IGPU_HEAL."""
        e1 = TokenSavingsEvent(
            event_type="AST_PRUNE",
            tool_name="prune_python_ast",
            tokens_before=1000,
            tokens_after=200,
            tokens_saved=800,
            latency_ms=2.0,
            timestamp="2026-09-06T14:01:00",
        )
        e2 = TokenSavingsEvent(
            event_type="DIFF_COMPRESS",
            tool_name="diff_compressor",
            tokens_before=5000,
            tokens_after=500,
            tokens_saved=4500,
            latency_ms=4.0,
            timestamp="2026-09-06T14:02:00",
        )
        self.telemetry.record_event(e1)
        self.telemetry.record_event(e2)

        summary: SavingsSummary = self.telemetry.get_summary()
        self.assertEqual(summary.events_count.get("AST_PRUNE"), 1)
        self.assertEqual(summary.events_count.get("DIFF_COMPRESS"), 1)


if __name__ == "__main__":
    unittest.main()

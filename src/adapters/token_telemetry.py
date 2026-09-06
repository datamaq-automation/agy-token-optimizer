"""Adaptador de telemetría y auditoría persistente de ahorro de tokens en hardware local.

Registra eventos estructurados en formato JSON Lines (~/.agents/token_savings.log)
y en base relacional SQLite (~/.agents/telemetry.db) para agregación y reporte instantáneo.
"""

import json
import os
import sqlite3
from typing import Dict, List

from src.domain.ports import ITokenTelemetry, SavingsSummary, TokenSavingsEvent


class SQLiteTokenTelemetry(ITokenTelemetry):
    """Implementación de telemetría con doble persistencia: JSONL y SQLite."""

    def __init__(
        self,
        db_path: str = os.path.expanduser("~/.agents/telemetry.db"),
        log_file_path: str = os.path.expanduser("~/.agents/token_savings.log"),
    ) -> None:
        self.db_path = db_path
        self.log_file_path = log_file_path
        self._init_storage()

    def _init_storage(self) -> None:
        """Inicializa los directorios y el esquema de base de datos relacional."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        log_dir = os.path.dirname(self.log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS token_savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tokens_before INTEGER NOT NULL,
                    tokens_after INTEGER NOT NULL,
                    tokens_saved INTEGER NOT NULL,
                    latency_ms REAL NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_type ON token_savings(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_ts ON token_savings(timestamp)")
            conn.commit()

    def record_event(self, event: TokenSavingsEvent) -> None:
        """Registra un evento individual en log estructurado y base de datos."""
        # 1. Apéndice atómico en JSON Lines
        log_entry = {
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "tool_name": event.tool_name,
            "tokens_before": event.tokens_before,
            "tokens_after": event.tokens_after,
            "tokens_saved": event.tokens_saved,
            "latency_ms": event.latency_ms,
        }
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # 2. Inserción en SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO token_savings (
                    timestamp, event_type, tool_name, tokens_before, tokens_after, tokens_saved, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.timestamp,
                    event.event_type,
                    event.tool_name,
                    event.tokens_before,
                    event.tokens_after,
                    event.tokens_saved,
                    event.latency_ms,
                ),
            )
            conn.commit()

    def get_summary(self) -> SavingsSummary:
        """Calcula el resumen agregado de ahorro y costos evitados en USD."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(tokens_saved), 0) FROM token_savings")
            row = cursor.fetchone()
            total_tokens = int(row[0]) if row and row[0] is not None else 0

            cursor.execute("SELECT event_type, COUNT(*) FROM token_savings GROUP BY event_type")
            counts_rows = cursor.fetchall()
            events_count: Dict[str, int] = {str(r[0]): int(r[1]) for r in counts_rows}

        # Tarifa estimada conservadora: $2.00 por millón de tokens ($0.000002 / token)
        total_cost_usd = round(total_tokens * 0.000002, 6)

        return SavingsSummary(
            total_tokens_saved=total_tokens,
            total_cost_saved_usd=total_cost_usd,
            events_count=events_count,
        )

    def get_recent_events(self, limit: int = 50) -> List[TokenSavingsEvent]:
        """Obtiene la lista de los últimos eventos registrados ordenados cronológicamente inverso."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT event_type, tool_name, tokens_before, tokens_after, tokens_saved, latency_ms, timestamp
                FROM token_savings
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        events: List[TokenSavingsEvent] = []
        for r in rows:
            events.append(
                TokenSavingsEvent(
                    event_type=str(r[0]),
                    tool_name=str(r[1]),
                    tokens_before=int(r[2]),
                    tokens_after=int(r[3]),
                    tokens_saved=int(r[4]),
                    latency_ms=float(r[5]),
                    timestamp=str(r[6]),
                )
            )
        return events

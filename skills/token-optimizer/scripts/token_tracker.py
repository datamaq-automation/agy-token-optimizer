#!/usr/bin/env python3
"""
token_tracker.py: Monitor local de métricas y dashboard de ahorro de tokens y costos en USD.
Persiste métricas en SQLite (~/.agents/cache/metrics.db) y genera reportes en terminal.
Uso:
  python3 token_tracker.py log --tool <nombre> --input-saved <N> --output-saved <N> [--details <txt>]
  python3 token_tracker.py stats
  python3 token_tracker.py reset
"""
import sys
import os
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
DB_PATH = CACHE_DIR / "metrics.db"

# Tarifas promedio de referencia por millón de tokens (Gemini / DeepSeek / Claude)
INPUT_PRICE_PER_M = 3.00   # USD por 1M input tokens
OUTPUT_PRICE_PER_M = 15.00 # USD por 1M output tokens

def init_db() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS token_savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                tool TEXT,
                input_saved INTEGER,
                output_saved INTEGER,
                details TEXT
            )
        """)
    return conn

def log_savings(tool: str, input_saved: int, output_saved: int, details: str = ""):
    conn = init_db()
    with conn:
        conn.execute("""
            INSERT INTO token_savings (timestamp, tool, input_saved, output_saved, details)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), tool, input_saved, output_saved, details))
    print(f"📊 Registrado: +{input_saved} tokens de entrada, +{output_saved} de salida ahorrados vía [{tool}].")

def show_stats():
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT tool, sum(input_saved), sum(output_saved), count(*) FROM token_savings GROUP BY tool")
    rows = cur.fetchall()
    
    cur.execute("SELECT sum(input_saved), sum(output_saved), count(*) FROM token_savings")
    total_row = cur.fetchone()
    
    total_in = total_row[0] or 0
    total_out = total_row[1] or 0
    total_ops = total_row[2] or 0
    total_tokens = total_in + total_out
    
    usd_saved = (total_in / 1_000_000 * INPUT_PRICE_PER_M) + (total_out / 1_000_000 * OUTPUT_PRICE_PER_M)
    
    print("\n" + "="*70)
    print(" 📈 DASHBOARD DE AHORRO DE TOKENS & ROI (Hardware Local)")
    print("="*70)
    print(f"{'Herramienta':<25} | {'Ops':<6} | {'Input Ahorrado':<15} | {'Output Ahorrado':<15}")
    print("-"*70)
    
    for tool, inp, out, ops in rows:
        print(f"{tool:<25} | {ops:<6} | {inp or 0:<15,d} | {out or 0:<15,d}")
        
    print("="*70)
    print(f" 🚀 Total de Operaciones Locales: {total_ops}")
    print(f" 📉 Total de Tokens Ahorrados:    {total_tokens:,} tokens ({total_in:,} in / {total_out:,} out)")
    print(f" 💰 Ahorro Económico Estimado:   ${usd_saved:.4f} USD")
    print("="*70 + "\n")

def reset_db():
    conn = init_db()
    with conn:
        conn.execute("DELETE FROM token_savings")
    print("🧹 Métricas de tokens reiniciadas a 0.")

def main():
    parser = argparse.ArgumentParser(description="Monitor de ahorro de tokens AGY")
    subparsers = parser.add_subparsers(dest="command")
    
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("--tool", required=True)
    log_parser.add_argument("--input-saved", type=int, default=0)
    log_parser.add_argument("--output-saved", type=int, default=0)
    log_parser.add_argument("--details", default="")
    
    subparsers.add_parser("stats")
    subparsers.add_parser("reset")
    
    args = parser.parse_args()
    
    if args.command == "log":
        log_savings(args.tool, args.input_saved, args.output_saved, args.details)
    elif args.command == "stats" or not args.command:
        show_stats()
    elif args.command == "reset":
        reset_db()

if __name__ == "__main__":
    main()

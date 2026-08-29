#!/usr/bin/env python3
"""
plan_impact_simulator.py: Simulador de impacto de modificaciones de AST en CPU para AGY.
Cruza un símbolo o archivo contra el grafo relacional symbols.db y calcula módulos dependientes,
ahorrando consultas manuales y alucinaciones al estimar el impacto de un plan.
Uso: python3 plan_impact_simulator.py <simbolo_o_archivo>
"""

import sqlite3
import sys
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
SYMBOLS_DB = CACHE_DIR / "symbols.db"


def simulate_impact(target_symbol: str) -> dict[str, list[str]]:
    if not SYMBOLS_DB.exists():
        return {"error": ["Base de datos 'symbols.db' no encontrada. Ejecuta 'agy-opt preflight' primero."]}

    conn = sqlite3.connect(str(SYMBOLS_DB))
    cur = conn.cursor()

    # 1. Buscar definición del símbolo
    cur.execute(
        "SELECT filepath, kind, signature, start_line FROM symbols WHERE name = ? OR filepath LIKE ?",
        (target_symbol, f"%{target_symbol}%"),
    )
    defs = cur.fetchall()

    # 2. Buscar callers y referencias en tabla 'calls'
    try:
        cur.execute("SELECT caller, filepath, line_number FROM calls WHERE callee = ?", (target_symbol,))
        callers = cur.fetchall()
    except Exception:
        callers = []

    return {
        "definitions": [f"{d[0]}#L{d[3]} ({d[1]}): {d[2]}" for d in defs],
        "dependents": [f"{c[1]}#L{c[2]} (en {c[0]})" for c in callers],
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 plan_impact_simulator.py <simbolo_o_archivo>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"🔍 [Plan Impact Simulator] Evaluando impacto de modificar '{target}'...")

    impact = simulate_impact(target)
    print("=" * 70)
    if "error" in impact:
        print(f"[!] {impact['error'][0]}")
        sys.exit(1)

    print(f"📌 DEFINICIONES ENCONTRADAS ({len(impact['definitions'])}):")
    for d in impact["definitions"][:5]:
        print(f"   • {d}")
    if not impact["definitions"]:
        print("   • (Ninguna definición directa encontrada)")

    print(f"\n⚠️  MÓDULOS Y CALLERS DEPENDIENTES ({len(impact['dependents'])}):")
    for dep in impact["dependents"][:10]:
        print(f"   • {dep}")
    if not impact["dependents"]:
        print("   • Cero llamadas detectadas (Módulo aislado o nuevo)")
    print("=" * 70)


if __name__ == "__main__":
    main()

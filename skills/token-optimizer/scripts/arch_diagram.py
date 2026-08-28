#!/usr/bin/env python3
"""
arch_diagram.py: Generador automático de diagramas Mermaid a $0 tokens para AGY.
Lee symbols.db y genera diagramas de arquitectura (capas, clases, puertos abc.ABC y adaptadores).
Uso: python3 arch_diagram.py [directorio] [--type flowchart|class]
"""

import sqlite3
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
SYMBOLS_DB = CACHE_DIR / "symbols.db"


def generate_mermaid_diagram() -> str:
    if not SYMBOLS_DB.exists():
        return (
            "```mermaid\nflowchart TD\n  Root[Base de código sin indexar] --> Run[Ejecuta symbol_graph.py index]\n```"
        )

    conn = sqlite3.connect(str(SYMBOLS_DB))
    cur = conn.cursor()
    cur.execute("SELECT filepath, name, kind, parent, base_classes FROM symbols WHERE kind IN ('class', 'function')")
    symbols = cur.fetchall()

    cur.execute("SELECT DISTINCT caller, callee FROM calls LIMIT 20")
    calls = cur.fetchall()

    lines = ["```mermaid", "flowchart TD", "  %% Diagrama de Arquitectura Generado en Local a $0 Tokens"]

    # Agrupar por capas Clean Architecture si existen
    layers = {"domain": [], "application": [], "adapters": [], "infrastructure": [], "other": []}

    for path, name, kind, parent, bases in symbols:
        p_lower = path.lower()
        if "domain" in p_lower:
            layers["domain"].append(name)
        elif "application" in p_lower:
            layers["application"].append(name)
        elif "adapter" in p_lower:
            layers["adapters"].append(name)
        elif "infra" in p_lower:
            layers["infrastructure"].append(name)
        else:
            if len(layers["other"]) < 10:
                layers["other"].append(name)

    if any(layers[k] for k in ["domain", "application", "adapters", "infrastructure"]):
        for layer_name, sym_list in layers.items():
            if sym_list:
                clean_syms = sym_list[:6]
                sym_str = "<br/>".join([f"• {s}" for s in clean_syms])
                lines.append(f'  subgraph {layer_name.upper()} ["Capas: {layer_name.capitalize()}"]')
                lines.append(f'    Node_{layer_name}["{sym_str}"]')
                lines.append("  end")
        lines.append("  Node_infrastructure -.-> Node_adapters -.-> Node_application -.-> Node_domain")
    else:
        # Fallback a llamadas directas
        for caller, callee in calls[:12]:
            c_from = caller.replace(" -> ", "_").replace("<module>", "Module").replace(" ", "_")
            c_to = callee.replace(" ", "_")
            lines.append(f"  {c_from} --> {c_to}")

    lines.append("```")
    return "\n".join(lines)


def main():
    diagram = generate_mermaid_diagram()
    print(diagram)


if __name__ == "__main__":
    main()

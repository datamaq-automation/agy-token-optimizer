#!/usr/bin/env python3
"""
context_injector.py: Inyector quirúrgico de contexto ultradenso (< 500 tokens) para AGY.
Combina el Grafo de Símbolos (symbols.db), Búsqueda Vectorial (vectors.db) y Poda AST.
Uso:
  python3 context_injector.py --symbol <nombre_simbolo>
  python3 context_injector.py --query "<requerimiento>" [directorio]
  python3 context_injector.py --file <archivo.py>
"""

import argparse
import os
import sqlite3
import subprocess
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
SYMBOLS_DB = CACHE_DIR / "symbols.db"
SCRIPTS_DIR = Path(__file__).resolve().parent


def get_symbol_context(symbol_name: str) -> str:
    if not SYMBOLS_DB.exists():
        return ""
    conn = sqlite3.connect(str(SYMBOLS_DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT filepath, kind, signature, start_line, end_line, base_classes FROM symbols WHERE name LIKE ? LIMIT 3",
        (f"%{symbol_name}%",),
    )
    sym_rows = cur.fetchall()

    cur.execute(
        "SELECT filepath, caller, line FROM calls WHERE callee = ? LIMIT 5",
        (symbol_name,),
    )
    call_rows = cur.fetchall()

    if not sym_rows and not call_rows:
        return ""

    lines = [f"#### 📍 Símbolo: `{symbol_name}`"]
    for path, kind, sig, s_line, e_line, bases in sym_rows:
        base_info = f" (hereda: {bases})" if bases else ""
        lines.append(f"- **[{kind.upper()}]** `{sig}`{base_info} en `[{os.path.basename(path)}#L{s_line}-L{e_line}]`")

    if call_rows:
        lines.append(
            "- **Callers:** "
            + ", ".join([f"`{c}()` en {os.path.basename(p)}#L{line_no}" for p, c, line_no in call_rows])
        )

    return "\n".join(lines)


def get_file_ast_context(filepath: str) -> str:
    prune_script = SCRIPTS_DIR / "prune_python_ast.py"
    if not prune_script.exists() or not os.path.exists(filepath):
        return ""
    try:
        res = subprocess.run(
            ["python3", str(prune_script), filepath],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"#### 🧬 Esqueleto AST: `{os.path.basename(filepath)}`\n```python\n{res.stdout.strip()[:600]}\n```"
    except Exception:
        return ""


def get_vector_context(query: str, root_dir: str = ".") -> str:
    search_script = SCRIPTS_DIR / "local_search.py"
    if not search_script.exists():
        return ""
    try:
        res = subprocess.run(
            ["python3", str(search_script), query, root_dir, "2"],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"#### 🔍 Fragmentos Semánticos Relevantes:\n```text\n{res.stdout.strip()[:700]}\n```"
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Inyector quirúrgico de contexto denso para AGY")
    parser.add_argument("--symbol", help="Nombre del símbolo (función, clase o puerto)")
    parser.add_argument("--file", help="Ruta al archivo para extraer esqueleto AST")
    parser.add_argument("--query", help="Consulta en lenguaje natural")
    parser.add_argument("--dir", default=".", help="Directorio raíz de búsqueda")

    args = parser.parse_args()
    bundle_parts = ["### 📦 Context Bundle Quirúrgico ($0 Tokens Pre-Procesado)"]

    if args.symbol:
        sym_ctx = get_symbol_context(args.symbol)
        if sym_ctx:
            bundle_parts.append(sym_ctx)

    if args.file:
        ast_ctx = get_file_ast_context(args.file)
        if ast_ctx:
            bundle_parts.append(ast_ctx)

    if args.query:
        vec_ctx = get_vector_context(args.query, args.dir)
        if vec_ctx:
            bundle_parts.append(vec_ctx)

    if len(bundle_parts) == 1:
        print("[!] No se encontró información de contexto para los parámetros especificados.")
    else:
        bundle_parts.append("---\n*Generado en CPU local en < 30 ms por `context_injector.py`.*")
        print("\n\n".join(bundle_parts))


if __name__ == "__main__":
    main()

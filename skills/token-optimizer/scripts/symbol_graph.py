#!/usr/bin/env python3
"""
symbol_graph.py: Grafo determinístico de símbolos y relaciones en RAM/SQLite para AGY.
Indexa definiciones, firmas, llamadas (callers/callees) y mapeo de puertos abstractos (abc.ABC) a adaptadores.
Uso:
  python3 symbol_graph.py index [directorio]
  python3 symbol_graph.py find <nombre_simbolo>
  python3 symbol_graph.py callers <nombre_funcion>
  python3 symbol_graph.py implementations <nombre_puerto_abc>
  python3 symbol_graph.py overview [directorio]
"""

import ast
import os
import sqlite3
import sys
from pathlib import Path

CACHE_DIR = Path.home() / ".agents" / "cache"
DB_PATH = CACHE_DIR / "symbols.db"


def init_db() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                filepath TEXT,
                name TEXT,
                kind TEXT,
                parent TEXT,
                base_classes TEXT,
                start_line INTEGER,
                end_line INTEGER,
                signature TEXT,
                PRIMARY KEY (filepath, name, kind, start_line)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                filepath TEXT,
                caller TEXT,
                callee TEXT,
                line INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sym_name ON symbols(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_callee ON calls(callee)")
    return conn


class SymbolExtractor(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.symbols = []
        self.calls = []
        self.current_scope = []

    def visit_ClassDef(self, node):
        bases = [ast.unparse(b) for b in node.bases]
        bases_str = ", ".join(bases)
        sig = f"class {node.name}({bases_str}):" if bases else f"class {node.name}:"
        parent = self.current_scope[-1] if self.current_scope else ""
        self.symbols.append(
            (
                self.filepath,
                node.name,
                "class",
                parent,
                bases_str,
                node.lineno,
                getattr(node, "end_lineno", node.lineno),
                sig,
            )
        )

        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node):
        self._handle_function(node, "function")

    def visit_AsyncFunctionDef(self, node):
        self._handle_function(node, "async_function")

    def _handle_function(self, node, kind_name):
        args = ast.unparse(node.args)
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        sig = f"def {node.name}({args}){returns}:"
        parent = self.current_scope[-1] if self.current_scope else ""
        kind = "method" if parent else kind_name
        self.symbols.append(
            (
                self.filepath,
                node.name,
                kind,
                parent,
                "",
                node.lineno,
                getattr(node, "end_lineno", node.lineno),
                sig,
            )
        )

        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Call(self, node):
        caller = " -> ".join(self.current_scope) if self.current_scope else "<module>"
        callee = ""
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        if callee:
            self.calls.append((self.filepath, caller, callee, node.lineno))
        self.generic_visit(node)


def index_directory(root_dir: str = "."):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM symbols")
    cur.execute("DELETE FROM calls")

    count_files = 0
    count_symbols = 0
    ignore_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".gemini",
        "dist",
        "build",
    }

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            if f.endswith(".py"):
                path = os.path.abspath(os.path.join(root, f))
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        tree = ast.parse(fh.read(), filename=path)
                    extractor = SymbolExtractor(path)
                    extractor.visit(tree)

                    cur.executemany(
                        """
                        INSERT OR IGNORE INTO symbols (filepath, name, kind, parent, base_classes, start_line, end_line, signature)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        extractor.symbols,
                    )

                    cur.executemany(
                        """
                        INSERT INTO calls (filepath, caller, callee, line)
                        VALUES (?, ?, ?, ?)
                    """,
                        extractor.calls,
                    )

                    count_files += 1
                    count_symbols += len(extractor.symbols)
                except Exception:
                    continue

    conn.commit()
    print(f"✅ Grafo indexado con éxito: {count_symbols} símbolos en {count_files} archivos Python.")


def find_symbol(name: str):
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT filepath, kind, parent, signature, start_line, end_line FROM symbols WHERE name LIKE ? ORDER BY kind",
        (f"%{name}%",),
    )
    rows = cur.fetchall()
    if not rows:
        print(f"No se encontró el símbolo '{name}'.")
        return
    print(f"\n🔎 Símbolos coincidentes con '{name}':\n" + "=" * 70)
    for path, kind, parent, sig, s_line, e_line in rows:
        scope = f" [{parent}]" if parent else ""
        print(f"[{kind.upper()}]{scope} {sig}")
        print(f"   📍 {path}#L{s_line}-L{e_line}\n")


def find_callers(name: str):
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT filepath, caller, line FROM calls WHERE callee = ? ORDER BY filepath",
        (name,),
    )
    rows = cur.fetchall()
    if not rows:
        print(f"No se detectaron llamadas explícitas a '{name}'.")
        return
    print(f"\n📞 Llamadas entrantes (Callers) a '{name}':\n" + "=" * 70)
    for path, caller, line in rows:
        print(f"  • {caller}() en {path}#L{line}")


def find_implementations(interface_name: str):
    conn = init_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT filepath, name, signature, start_line FROM symbols WHERE base_classes LIKE ?",
        (f"%{interface_name}%",),
    )
    rows = cur.fetchall()
    if not rows:
        print(f"No se encontraron clases que hereden o implementen '{interface_name}'.")
        return
    print(f"\n🧩 Implementaciones concretas del puerto/interfaz '{interface_name}':\n" + "=" * 70)
    for path, name, sig, line in rows:
        print(f"  • {sig} ──► {path}#L{line}")


def overview(root_dir: str = "."):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT kind, count(*) FROM symbols GROUP BY kind")
    kinds = cur.fetchall()
    print(f"\n📊 Resumen de Arquitectura ({root_dir}):\n" + "=" * 50)
    for k, cnt in kinds:
        print(f"  • {k.capitalize()}: {cnt}")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 symbol_graph.py <index|find|callers|implementations|overview> [argumentos]")
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else "."

    if cmd == "index":
        index_directory(arg)
    elif cmd == "find":
        find_symbol(arg)
    elif cmd == "callers":
        find_callers(arg)
    elif cmd == "implementations":
        find_implementations(arg)
    elif cmd == "overview":
        overview(arg)
    else:
        print(f"Comando desconocido '{cmd}'. Usa index, find, callers, implementations u overview.")

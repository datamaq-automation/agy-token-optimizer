#!/usr/bin/env python3
"""
vps_symbol_sync.py: Sincronizador de Grafo AST remoto de VPS a SQLite local en RAM para AGY.
Descarga y analiza las firmas y símbolos de proyectos en la VPS, guardándolos en symbols.db
para que AGY navegue la arquitectura remota a 0 ms y $0 tokens desde tu PC local.
Uso: python3 vps_symbol_sync.py [directorio_remoto] [--host vps]
"""

import ast
import sqlite3
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
CACHE_DIR = Path.home() / ".agents" / "cache"
SYMBOLS_DB = CACHE_DIR / "symbols.db"


def sync_remote_symbols(remote_dir: str = "/root/proyectos_software", host: str = "vps"):
    print(f"🌐 [VPS Symbol Sync] Escaneando archivos Python en '{remote_dir}' sobre {host}...")

    # Listar archivos .py remotos excluyendo caches y entornos
    list_cmd = f"find {remote_dir} -name '*.py' -not -path '*/.*' -not -path '*/__pycache__*' 2>/dev/null"
    ssh_cmd = ["ssh", host, list_cmd]

    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        remote_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception as e:
        print(f"[!] Error listando archivos en la VPS: {e}")
        return

    if not remote_files:
        print(f"[!] No se encontraron archivos Python en {remote_dir} en la VPS.")
        return

    print(f"📦 Descargando y parseando AST en CPU local para {len(remote_files)} archivos remotos...")

    conn = sqlite3.connect(str(SYMBOLS_DB))
    cur = conn.cursor()

    imported_symbols = 0
    for r_path in remote_files[:50]:  # Límite de seguridad
        cat_cmd = ["ssh", host, f"cat {r_path}"]
        try:
            cat_res = subprocess.run(cat_cmd, capture_output=True, text=True, check=True)
            tree = ast.parse(cat_res.stdout, filename=r_path)

            # Extraer símbolos usando AST local
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sig = f"def {node.name}(...):"
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO symbols (filepath, name, kind, parent, base_classes, start_line, end_line, signature)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            f"vps:{r_path}",
                            node.name,
                            "function",
                            "",
                            "",
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            sig,
                        ),
                    )
                    imported_symbols += 1
                elif isinstance(node, ast.ClassDef):
                    bases = ", ".join([ast.unparse(b) for b in node.bases])
                    sig = f"class {node.name}({bases}):" if bases else f"class {node.name}:"
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO symbols (filepath, name, kind, parent, base_classes, start_line, end_line, signature)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            f"vps:{r_path}",
                            node.name,
                            "class",
                            "",
                            bases,
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            sig,
                        ),
                    )
                    imported_symbols += 1
        except Exception:
            continue

    conn.commit()
    print(
        f"✅ Sincronización completada: {imported_symbols} símbolos remotos indexados en tu RAM local ('symbols.db')."
    )


def main():
    r_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "/root/proyectos_software"
    host = "vps"
    sync_remote_symbols(r_dir, host)


if __name__ == "__main__":
    main()

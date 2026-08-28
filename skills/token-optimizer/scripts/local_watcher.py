#!/usr/bin/env python3
"""
local_watcher.py: Daemon de sincronización en segundo plano de RAM/SQLite para AGY.
Vigila modificaciones en archivos del proyecto y actualiza incrementalmente symbols.db y vectors.db en < 10 ms.
Uso: python3 local_watcher.py [directorio_repo]
"""

import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def watch_directory(target_dir: str = "."):
    target_path = Path(target_dir).resolve()
    print(f"👁️  [Watcher Daemon] Vigilando modificaciones en {target_path}...")

    symbol_script = SCRIPTS_DIR / "symbol_graph.py"
    file_mtimes = {}
    ignore_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".gemini",
        "dist",
        "build",
        ".agents",
        ".stubs",
    }

    def scan_files():
        current = {}
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if f.endswith((".py", ".ts", ".js", ".md")):
                    p = os.path.join(root, f)
                    try:
                        current[p] = os.path.getmtime(p)
                    except OSError:
                        pass
        return current

    file_mtimes = scan_files()

    # Indexación inicial
    if symbol_script.exists():
        subprocess.run(["python3", str(symbol_script), "index", str(target_path)], capture_output=True)

    try:
        while True:
            time.sleep(1.0)
            current_mtimes = scan_files()
            modified = False

            for path, mtime in current_mtimes.items():
                if path not in file_mtimes or file_mtimes[path] != mtime:
                    modified = True
                    break

            if not modified and len(current_mtimes) != len(file_mtimes):
                modified = True

            if modified:
                file_mtimes = current_mtimes
                if symbol_script.exists():
                    subprocess.run(["python3", str(symbol_script), "index", str(target_path)], capture_output=True)
                print(f"⚡ [Watcher Daemon] Grafo de símbolos y vectores sincronizados ({time.strftime('%H:%M:%S')}).")
    except KeyboardInterrupt:
        print("\n🛑 Watcher detenido.")


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    watch_directory(d)

#!/usr/bin/env python3
"""
vps_reader.py: Lector quirúrgico y extractor AST de archivos remotos en VPS para AGY.
Lee rangos exactos de líneas o extrae el esqueleto AST de archivos remotos sin descargarlos a local,
evitando la saturación de tokens en lecturas remotas.
Uso:
  python3 vps_reader.py <ruta_remota> [start_line] [end_line] [--host vps]
  python3 vps_reader.py <ruta_remota> --ast [--host vps]
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def read_remote_lines(remote_path: str, start_line: int, end_line: int, host: str = "vps") -> str:
    # Usar sed remoto para extraer únicamente el rango solicitado
    sed_cmd = f"sed -n '{start_line},{end_line}p' {remote_path}"
    ssh_cmd = ["ssh", host, sed_cmd]
    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[!] Error leyendo archivo remoto '{remote_path}': {e.stderr}"


def read_remote_ast(remote_path: str, host: str = "vps") -> str:
    cat_cmd = f"cat {remote_path}"
    ssh_cmd = ["ssh", host, cat_cmd]
    prune_script = SCRIPTS_DIR / "prune_python_ast.py"

    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        raw_code = res.stdout
    except subprocess.CalledProcessError as e:
        return f"[!] Error leyendo archivo remoto '{remote_path}': {e.stderr}"

    if prune_script.exists() and remote_path.endswith(".py"):
        try:
            prune_res = subprocess.run(
                ["python3", str(prune_script), "-"], input=raw_code, capture_output=True, text=True, check=True
            )
            return prune_res.stdout.strip()
        except Exception:
            pass

    return raw_code[:1000]


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 vps_reader.py <ruta_remota> [start_line] [end_line] [--ast] [--host vps]")
        sys.exit(1)

    remote_file = sys.argv[1]
    host = "vps"
    is_ast = "--ast" in sys.argv

    if is_ast:
        print(f"🧬 [VPS Remote AST] Extrayendo esqueleto de '{remote_file}' en {host}...")
        ast_out = read_remote_ast(remote_file, host)
        print("\n" + "=" * 70)
        print(ast_out)
        print("=" * 70)
        return

    start_l = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
    end_l = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else start_l + 50

    print(f"📍 [VPS Remote Read] Leyendo {remote_file}#L{start_l}-L{end_l} en {host}...")
    lines = read_remote_lines(remote_file, start_l, end_l, host)
    print("\n" + "=" * 70)
    print(lines)
    print("=" * 70)


if __name__ == "__main__":
    main()

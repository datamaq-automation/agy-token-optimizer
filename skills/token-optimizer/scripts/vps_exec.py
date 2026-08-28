#!/usr/bin/env python3
"""
vps_exec.py: Ejecutor remoto en VPS con compresión y poda determinística de salida para AGY.
Ejecuta comandos sobre el socket SSH persistente y poda automáticamente salidas masivas de logs
y tablas ruidosas, extrayendo únicamente información crítica y reduciendo el consumo de tokens en un 80%.
Uso: python3 vps_exec.py "<comando>" [--host vps]
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def clean_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def compress_vps_output(raw_output: str, max_lines: int = 40) -> str:
    cleaned = clean_ansi(raw_output).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    if len(lines) <= max_lines:
        return "\n".join(lines)

    # Filtrar líneas relevantes (errores, advertencias, fallos, estados)
    critical_keywords = [
        "error",
        "failed",
        "failure",
        "warning",
        "fatal",
        "exception",
        "traceback",
        "critical",
        "down",
        "inactive",
        "restart",
        "killed",
        "panic",
        "denied",
    ]

    critical_lines = []
    for line in lines:
        l_lower = line.lower()
        if any(kw in l_lower for kw in critical_keywords):
            critical_lines.append(line)

    summary = []
    summary.append(f"[Salida de VPS truncada: {len(lines)} líneas originales reducidas a formato compacto]")
    summary.append("=" * 70)

    if critical_lines:
        summary.append(f"⚠️  {len(critical_lines)} LÍNEAS RELEVANTES O ERRORES DETECTADOS:")
        summary.extend(critical_lines[:25])
        summary.append("=" * 70)

    summary.append("📍 ÚLTIMAS LÍNEAS DE EJECUCIÓN:")
    summary.extend(lines[-10:])
    summary.append("=" * 70)

    # Registrar ahorro en token_tracker si existe
    tracker = SCRIPTS_DIR / "token_tracker.py"
    if tracker.exists():
        tokens_saved = int((len(raw_output) - len("\n".join(summary))) / 4)
        if tokens_saved > 50:
            subprocess.run(
                [
                    "python3",
                    str(tracker),
                    "log",
                    "--tool",
                    "VPS Output Pruner",
                    "--input-saved",
                    str(tokens_saved),
                    "--output-saved",
                    "0",
                ],
                capture_output=True,
            )

    return "\n".join(summary)


def run_vps_command(cmd: str, host: str = "vps") -> tuple[int, str]:
    ssh_cmd = ["ssh", host, cmd]
    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        combined = res.stdout
        if res.stderr:
            combined += "\n[STDERR]:\n" + res.stderr
        compressed = compress_vps_output(combined)
        return res.returncode, compressed
    except subprocess.TimeoutExpired:
        return 124, f"[!] Tiempo de espera agotado (Timeout de 60s) ejecutando en VPS: '{cmd}'"
    except Exception as e:
        return 1, f"[!] Error de conexión SSH a VPS ({host}): {e}"


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 vps_exec.py "<comando>" [--host vps]')
        sys.exit(1)

    cmd = sys.argv[1]
    host = "vps"
    if len(sys.argv) > 3 and sys.argv[2] in ("--host", "-h"):
        host = sys.argv[3]

    code, output = run_vps_command(cmd, host)
    print(output)
    sys.exit(code)


if __name__ == "__main__":
    main()

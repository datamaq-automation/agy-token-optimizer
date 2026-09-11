#!/usr/bin/env python3
"""Diagnóstico ultrarrápido (< 50ms) de salud del entorno local para sesiones Web UI.

Verifica:
  1. Ollama local en iGPU Vulkan (http://localhost:11434).
  2. Tokenix Daemon en RAM (http://localhost:47392).
  3. GitHub CLI ('gh auth status').
  4. Demonio de Remote Control ('agy-remote-control.service').
"""

import subprocess
import sys
import time
import urllib.request


def check_http_endpoint(url: str, timeout: float = 0.5) -> tuple[bool, str]:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if resp.status in (200, 204):
                return True, f"OK ({elapsed_ms:.1f}ms)"
            return False, f"Status {resp.status}"
    except Exception as e:
        return False, str(e)


def check_gh_cli() -> tuple[bool, str]:
    try:
        res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=1.0)
        if res.returncode == 0 or "Logged in to github.com" in res.stdout or "Logged in to github.com" in res.stderr:
            return True, "Autenticado en github.com"
        return False, "No autenticado o error"
    except Exception as e:
        return False, str(e)


def check_systemd_service(service_name: str) -> tuple[bool, str]:
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=0.5,
        )
        status = res.stdout.strip()
        return (status == "active"), status
    except Exception as e:
        return False, str(e)


def main() -> None:
    print("======================================================================")
    print(" 🩺 ESTADO DE SALUD DEL HARDWARE LOCAL (NAVEGADOR FIRST / WEB UI)")
    print("======================================================================")

    # 1. Ollama iGPU
    ollama_ok, ollama_msg = check_http_endpoint("http://localhost:11434/api/tags")
    sym_ollama = "✓" if ollama_ok else "✗"
    print(f" [{sym_ollama}] Ollama Local (iGPU Vulkan) : {ollama_msg}")

    # 2. Tokenix RAM Daemon
    try:
        req = urllib.request.Request("http://localhost:47392/", method="GET")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            tokenix_ok, tokenix_msg = True, "Activo en RAM :47392"
    except urllib.error.HTTPError:
        # Si devuelve HTTP error (ej. 404/400), el servidor está escuchando
        tokenix_ok, tokenix_msg = True, "Activo en RAM :47392"
    except Exception as e:
        tokenix_ok, tokenix_msg = False, str(e)

    sym_tokenix = "✓" if tokenix_ok else "✗"
    print(f" [{sym_tokenix}] Tokenix Daemon (RAM :47392) : {tokenix_msg}")

    # 3. GitHub CLI
    gh_ok, gh_msg = check_gh_cli()
    sym_gh = "✓" if gh_ok else "✗"
    print(f" [{sym_gh}] GitHub Actions CLI (gh)   : {gh_msg}")

    # 4. Systemd Remote Control
    rc_ok, rc_msg = check_systemd_service("agy-remote-control.service")
    sym_rc = "✓" if rc_ok else "✗"
    print(f" [{sym_rc}] Remote Control Daemon     : {rc_msg}")

    print("======================================================================")
    if ollama_ok and gh_ok:
        print("🟢 SISTEMA 100% OPERATIVO PARA NAVEGADOR FIRST ($0 TOKENS)")
        sys.exit(0)
    else:
        print("🟡 ADVERTENCIA: Algunos servicios requieren atención")
        sys.exit(1)


if __name__ == "__main__":
    main()

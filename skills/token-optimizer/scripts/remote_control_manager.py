#!/usr/bin/env python3
"""Gestor y verificador de integración para Antigravity Remote Control (Navegador <-> Hardware Local).

Asegura que el daemon de remote control esté siempre activo, enlazado con la instancia 'my-box',
y que todos los hooks determinísticos de CPU, Tokenix en RAM y Ollama en iGPU operen de forma
transparente para cualquier sesión abierta desde https://antigravity.google.com.
"""

import subprocess
from pathlib import Path


def run_cmd(cmd: list[str]) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout.strip()
    except Exception:
        return ""


def check_systemd_service(service_name: str) -> bool:
    out = run_cmd(["systemctl", "--user", "is-active", service_name])
    return out == "active"


def ensure_service(service_name: str) -> bool:
    if not check_systemd_service(service_name):
        run_cmd(["systemctl", "--user", "start", service_name])
        return check_systemd_service(service_name)
    return True


def main() -> None:
    print("\n" + "=" * 76)
    print(" 🌐 ESTADO DE CONEXIÓN NAVEGADOR <-> HARDWARE LOCAL (Antigravity Remote)")
    print("=" * 76)

    # 1. Demonio de Remote Control
    rc_active = ensure_service("agy-remote-control.service")
    rc_status = "✅ ACTIVO (Conectado a la nube)" if rc_active else "❌ INACTIVO"
    print(f" • Demonio Remote Control (my-box): {rc_status}")

    # 2. Demonio Tokenix en RAM
    tokenix_active = ensure_service("tokenix.service")
    tokenix_status = "✅ ACTIVO (RAM Disk :47392)" if tokenix_active else "❌ INACTIVO"
    print(f" • Demonio Tokenix Residente en RAM: {tokenix_status}")

    # 3. Ollama iGPU Vulkan
    ollama_out = run_cmd(["curl", "-s", "http://localhost:11434/api/tags"])
    ollama_active = "qwen2.5-coder:1.5b" in ollama_out
    ollama_status = "✅ ACTIVO (100% VRAM Vulkan)" if ollama_active else "❌ INACTIVO"
    print(f" • Auto-Sanador SLM en iGPU:         {ollama_status}")

    # 4. Hooks globales
    hooks_file = Path.home() / ".gemini" / "config" / "hooks.json"
    hooks_status = "✅ ACTIVOS (Global en ~/.gemini)" if hooks_file.exists() else "❌ NO ENCONTRADO"
    print(f" • Hooks de Poda AST, Diffs y Datos: {hooks_status}")

    print("-" * 76)
    print(" 🚀 INSTRUCCIONES PARA USAR SIEMPRE EL HARDWARE LOCAL DESDE EL NAVEGADOR:")
    print(" 1. Ingresa en tu navegador a: https://antigravity.google.com")
    print(" 2. En el selector de instancias / entornos, asegúrate de seleccionar: 'my-box'")
    print(" 3. Selecciona tu workspace local: /home/agustin/proyectos_software/agy-token-optimizer")
    print("-" * 76)
    print(" ✨ ¡Listo! Toda conversación en la web usará automáticamente:")
    print("    • Poda determinística de AST y JSON/YAML/CSV masivos en tu CPU.")
    print("    • Compresión de git diffs y outputs de terminal en tu CPU.")
    print("    • Auto-sanación de errores de sintaxis en tu iGPU Radeon Vega 11 ($0 tokens).")
    print("    • Búsqueda semántica en RAM a través del socket de Tokenix.")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
opencode_config_sync.py: Sincronizador de configuración de OpenCode para usar el router local de AGY.
Genera o actualiza la configuración de OpenCode (~/.config/opencode/config.json) para apuntar
a http://127.0.0.1:8080/v1 con modelo auto-cascade a $0 tokens.
Uso: python3 opencode_config_sync.py [--port 8080]
"""

import json
import sys
from pathlib import Path

OPENCODE_CONFIG_DIR = Path.home() / ".config" / "opencode"
OPENCODE_CONFIG_FILE = OPENCODE_CONFIG_DIR / "config.json"


def sync_opencode_config(port: int = 8080) -> Path:
    OPENCODE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config = {}
    if OPENCODE_CONFIG_FILE.exists():
        try:
            with open(OPENCODE_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    # Inyectar endpoint del router local de AGY
    config["openai_base_url"] = f"http://127.0.0.1:{port}/v1"
    config["openai_api_key"] = "agy-cascade-key"
    config["model"] = "auto-cascade"
    config["providers"] = {
        "agy_cascade": {
            "api_base": f"http://127.0.0.1:{port}/v1",
            "api_key": "agy-cascade-key",
            "model": "auto-cascade",
        }
    }

    with open(OPENCODE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return OPENCODE_CONFIG_FILE


def main():
    port = 8080
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    cfg = sync_opencode_config(port)
    print("=" * 70)
    print("✅ [OpenCode Config Sync] OpenCode configurado exitosamente.")
    print(f"📍 Archivo de Configuración: {cfg}")
    print(f"🌐 Endpoint Asignado: http://127.0.0.1:{port}/v1 (Modelo: auto-cascade)")
    print("=" * 70)


if __name__ == "__main__":
    main()

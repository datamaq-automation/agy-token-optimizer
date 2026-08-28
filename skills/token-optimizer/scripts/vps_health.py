#!/usr/bin/env python3
"""
vps_health.py: Monitor de salud y diagnóstico ultradenso (< 50 tokens) de VPS para AGY.
Ejecuta una única consulta consolidada vía SSH y devuelve un bloque ASCII de 4 líneas con
CPU load, RAM usada/libre, almacenamiento en disco y contenedores Docker activos.
Uso: python3 vps_health.py [--host vps]
"""

import subprocess
import sys


def get_vps_health(host: str = "vps") -> str:
    script = """
LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)
RAM=$(free -h | awk '/Mem:/ {print $3 "/" $2 " (Disp: " $7 ")"}')
DISK=$(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')
DOCKER=$(docker ps --format '{{.Names}} ({{.Status}})' 2>/dev/null | paste -sd ", " - || echo "Ninguno")
FAILED_UNITS=$(systemctl --failed --no-legend 2>/dev/null | wc -l || echo "0")

echo "📊 [VPS HEALTH ($HOSTNAME)] | Load: $LOAD"
echo "💾 RAM: $RAM | Disco: $DISK"
echo "🐳 Docker: $DOCKER"
echo "🛡️  Systemd Failed: $FAILED_UNITS unidades con fallo"
"""
    ssh_cmd = ["ssh", host, script.strip()]
    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        return f"[!] Error consultando salud de VPS ({host}): {e}"


def main():
    host = "vps"
    if len(sys.argv) > 2 and sys.argv[1] in ("--host", "-h"):
        host = sys.argv[2]
    health = get_vps_health(host)
    print("\n" + "=" * 70)
    print(health)
    print("=" * 70)


if __name__ == "__main__":
    main()

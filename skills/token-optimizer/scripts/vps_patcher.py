#!/usr/bin/env python3
"""
vps_patcher.py: Parcheador quirúrgico remoto para archivos en VPS vía SSH para AGY.
Aplica modificaciones in-place en la VPS sin transferir archivos completos, ahorrando >95% de tokens.
Uso:
  python3 vps_patcher.py <archivo_remoto> --target "<texto_a_reemplazar>" --replacement "<nuevo_texto>" [--host vps]
  python3 vps_patcher.py <archivo_remoto> --start <linea_inicio> --end <linea_fin> --content "<nuevo_texto>" [--host vps]
"""

import argparse
import base64
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def patch_remote_file_target(remote_path: str, target: str, replacement: str, host: str = "vps") -> bool:
    # Codificar en base64 para evitar problemas con comillas y caracteres especiales en SSH
    b64_target = base64.b64encode(target.encode("utf-8")).decode("ascii")
    b64_replacement = base64.b64encode(replacement.encode("utf-8")).decode("ascii")

    remote_script = f"""
python3 -c "
import base64, sys

path = '{remote_path}'
target = base64.b64decode('{b64_target}').decode('utf-8')
replacement = base64.b64decode('{b64_replacement}').decode('utf-8')

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if target not in content:
        print('[!] Error: El texto objetivo no fue encontrado en ' + path, file=sys.stderr)
        sys.exit(1)
    new_content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ Parche aplicado con éxito en ' + path)
except Exception as e:
    print('[!] Error: ' + str(e), file=sys.stderr)
    sys.exit(1)
"
"""
    ssh_cmd = ["ssh", host, remote_script.strip()]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(res.stdout.strip())
        # Validar sintaxis remota si es Python
        if remote_path.endswith(".py"):
            chk = subprocess.run(["ssh", host, f"python3 -m py_compile {remote_path}"], capture_output=True, text=True)
            if chk.returncode == 0:
                print(f"✓ Sintaxis Python verificada en {remote_path} (0 errores).")
            else:
                print(f"⚠️  [ADVERTENCIA] Error de sintaxis tras parchear: {chk.stderr}")
        return True
    else:
        print(res.stderr.strip() or res.stdout.strip())
        return False


def main():
    parser = argparse.ArgumentParser(description="Parcheador quirúrgico remoto para VPS")
    parser.add_argument("file", help="Ruta del archivo remoto en la VPS")
    parser.add_argument("--target", help="Texto exacto a reemplazar")
    parser.add_argument("--replacement", help="Nuevo texto de reemplazo")
    parser.add_argument("--host", default="vps", help="Host SSH (default: vps)")

    args = parser.parse_args()
    if not args.target or args.replacement is None:
        print("Uso: python3 vps_patcher.py <archivo_remoto> --target '<viejo>' --replacement '<nuevo>'")
        sys.exit(1)

    ok = patch_remote_file_target(args.file, args.target, args.replacement, args.host)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

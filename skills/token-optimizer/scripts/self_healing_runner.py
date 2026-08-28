#!/usr/bin/env python3
"""
self_healing_runner.py: Auto-sanador recursivo en bucle cerrado con SLM local para AGY.
Ejecuta tests locales. Si fallan, captura el traceback, consulta a qwen2.5-coder:1.5b en RAM,
aplica el parche y re-ejecuta el test hasta pasar verde a $0 tokens de API.
Uso: python3 self_healing_runner.py [archivo_test.py]
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"


def run_test_cmd(test_target: str) -> tuple[int, str]:
    runner = SCRIPTS_DIR / "test_runner.sh"
    cmd = [str(runner), test_target] if runner.exists() else ["pytest", "-q", test_target]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout + "\n" + res.stderr


def extract_failing_file(traceback_text: str) -> tuple[str, int]:
    # Buscar patrones tipo File "/ruta/archivo.py", line 123
    matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback_text)
    if matches:
        for fpath, lno in reversed(matches):
            if not fpath.startswith("/usr") and "site-packages" not in fpath and "test" not in os.path.basename(fpath):
                return fpath, int(lno)
        # Si no encontró en src, devuelve el último archivo local
        for fpath, lno in reversed(matches):
            if not fpath.startswith("/usr") and "site-packages" not in fpath:
                return fpath, int(lno)
    return "", 0


def ask_slm_repair(source_code: str, error_trace: str) -> str:
    prompt = (
        f"El siguiente código en Python causó un error en los tests.\n\n"
        f"--- CÓDIGO ACTUAL ---\n{source_code}\n\n"
        f"--- ERROR DETECTADO ---\n{error_trace}\n\n"
        f"Devuelve ÚNICAMENTE el código de Python completo corregido, sin bloques de texto conversacional ni explicaciones."
    )
    payload = json.dumps(
        {"model": MODEL_NAME, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_predict": 700}}
    ).encode("utf-8")

    req = urllib.request.Request(OLLAMA_GEN_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            resp_text = data.get("response", "").strip()
            # Limpiar posibles bloques ```python ... ```
            if "```python" in resp_text:
                resp_text = resp_text.split("```python")[1].split("```")[0].strip()
            elif "```" in resp_text:
                resp_text = resp_text.split("```")[1].split("```")[0].strip()
            return resp_text
    except Exception as e:
        print(f"[!] Error comunicando con SLM local: {e}")
        return ""


def self_heal_loop(test_target: str = "tests", max_attempts: int = 3) -> bool:
    print(f"🔄 [Self-Healing Loop] Iniciando ejecución de pruebas para '{test_target}'...")

    for attempt in range(1, max_attempts + 1):
        code, output = run_test_cmd(test_target)
        if code == 0:
            print("✅ [Tests Aprobados] El código está verde y funciona correctamente.")
            return True

        print(f"⚠️  [Intento {attempt}/{max_attempts}] Fallo detectado. Diagnosticando en CPU local...")
        fpath, lno = extract_failing_file(output)

        if not fpath or not os.path.isfile(fpath):
            print("[!] No se pudo localizar automáticamente el archivo fuente causante del fallo.")
            print(output[:500])
            return False

        print(f"📍 Archivo causante: {fpath} (cerca de línea {lno})")
        with open(fpath, "r", encoding="utf-8") as fh:
            original_code = fh.read()

        print(f"🤖 [Local SLM: {MODEL_NAME}] Generando parche correctivo en RAM...")
        repaired = ask_slm_repair(original_code, output)

        if not repaired or len(repaired) < 10:
            print("[!] El SLM no devolvió una corrección válida.")
            continue

        # Aplicar parche
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(repaired)

        # Linter local post-parche
        subprocess.run(["ruff", "check", "--fix", fpath], capture_output=True)
        subprocess.run(["ruff", "format", fpath], capture_output=True)
        print(f"🩹 Parche aplicado en {fpath}. Re-ejecutando tests...")

    print(f"❌ [Self-Healing] No se pudo resolver tras {max_attempts} iteraciones. Escalando a AGY Cloud con contexto.")
    return False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "tests"
    ok = self_heal_loop(target)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

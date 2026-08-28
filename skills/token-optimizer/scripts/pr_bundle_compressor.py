#!/usr/bin/env python3
"""
pr_bundle_compressor.py: Generador local de resúmenes de PR y commits convencionales con SLM para AGY.
Analiza git status y git diff comprimido para generar un mensaje estructurado en segundos a $0 tokens de API.
Uso: python3 pr_bundle_compressor.py [directorio_repo]
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"


def get_git_diff_summary(repo_dir: str = ".") -> str:
    try:
        status = subprocess.check_output(["git", "-C", repo_dir, "status", "-s"], text=True).strip()
        diff = subprocess.check_output(["git", "-C", repo_dir, "diff", "HEAD~1"], text=True).strip()
        if not diff:
            diff = subprocess.check_output(["git", "-C", repo_dir, "diff"], text=True).strip()
    except Exception as e:
        return f"Error obteniendo git diff: {e}"

    return f"Git Status:\n{status}\n\nGit Diff:\n{diff[:1500]}"


def generate_pr_summary(diff_text: str) -> str:
    prompt = (
        f"Genera un mensaje de commit y resumen de Pull Request en formato Conventional Commits "
        f"para los siguientes cambios:\n\n{diff_text}\n\nDevuelve solo el título y la lista de viñetas en español."
    )
    payload = json.dumps(
        {"model": MODEL_NAME, "prompt": prompt, "stream": False, "options": {"temperature": 0.2, "num_predict": 300}}
    ).encode("utf-8")

    req = urllib.request.Request(OLLAMA_GEN_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        return f"# Error generando resumen con Ollama: {e}"


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    print("🔍 [PR Compressor] Analizando cambios de Git...")
    diff_summary = get_git_diff_summary(repo)
    print(f"🤖 [Local SLM: {MODEL_NAME}] Sintetizando resumen de PR a $0 tokens...")
    summary = generate_pr_summary(diff_summary)
    print("\n" + "=" * 70)
    print(summary)
    print("=" * 70)


if __name__ == "__main__":
    main()

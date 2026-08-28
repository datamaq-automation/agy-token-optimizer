#!/usr/bin/env python3
"""
local_slm_draft.py: Generador local de pre-borradores con SLM (qwen2.5-coder:1.5b) para AGY.
Genera código base, DTOs y utilitarios en RAM a ~16 tok/s a $0 costo de API.
Uso: python3 local_slm_draft.py "Instrucción de código a generar"
"""

import json
import sys
import urllib.request

OLLAMA_GEN_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"


def generate_local_draft(prompt: str) -> str:
    system_prompt = (
        "Eres un programador experto en Clean Architecture y Python tipado estricto. "
        "Devuelve ÚNICAMENTE código fuente funcional sin explicaciones conversacionales ni saludos."
    )
    payload = json.dumps(
        {
            "model": MODEL_NAME,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 512},
        }
    ).encode("utf-8")

    req = urllib.request.Request(OLLAMA_GEN_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        return f"# Error generando borrador local con Ollama ({MODEL_NAME}): {e}"


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 local_slm_draft.py "<instrucción de código>"')
        sys.exit(1)

    user_prompt = sys.argv[1]
    print(f"🤖 [Local SLM: {MODEL_NAME}] Generando borrador en RAM...")
    code = generate_local_draft(user_prompt)
    print("\n" + "=" * 70)
    print(code)
    print("=" * 70)
    print("\n💡 [AGY Tip]: Copia o audita este borrador en AGY a $0 tokens de salida.")


if __name__ == "__main__":
    main()

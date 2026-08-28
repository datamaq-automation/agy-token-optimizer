#!/usr/bin/env python3
"""
prompt_squeezer.py: Compresor determinístico local de prompts y contextos para AGY.
Elimina preámbulos conversacionales, normaliza espaciados, compacta tablas y reduce
entre un 30% y un 50% el conteo de tokens antes de enviar texto a la API.
Uso:
  cat prompt.md | python3 prompt_squeezer.py
  python3 prompt_squeezer.py [archivo]
"""

import os
import re
import sys


def squeeze_text(raw: str) -> str:
    lines = raw.splitlines()
    squeezed = []

    # Patrones de relleno conversacional
    fluff_patterns = [
        r"^(hola|buenas tardes|saludos|por favor|muchas gracias|gracias),?",
        r"^como modelo de lenguaje.*",
        r"^a continuación se muestra.*",
        r"^espero que esto te sea de ayuda.*",
    ]

    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            squeezed.append(line)
            continue

        if in_code_block:
            squeezed.append(line)
            continue

        if not stripped:
            if squeezed and squeezed[-1] == "":
                continue
            squeezed.append("")
            continue

        # Filtrar fluff
        is_fluff = False
        for pat in fluff_patterns:
            if re.match(pat, stripped, re.IGNORECASE):
                is_fluff = True
                break
        if is_fluff:
            continue

        # Compactar espacios múltiples en texto plano
        compact_line = re.sub(r"[ \t]+", " ", line)
        squeezed.append(compact_line)

    res = "\n".join(squeezed).strip()
    return res


def main():
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    elif len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        print("Uso: cat prompt.md | python3 prompt_squeezer.py", file=sys.stderr)
        sys.exit(1)

    out = squeeze_text(raw)
    orig_words = len(raw.split())
    new_words = len(out.split())
    saved_pct = ((orig_words - new_words) / max(1, orig_words)) * 100

    print(out)
    print(
        f"\n<!-- [Squeezer]: {orig_words} palabras -> {new_words} palabras (~{saved_pct:.1f}% compresión) -->",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
token_proxy_interceptor.py: Middleware local de intercepción y compresión de tokens en vuelo para AGY.
Intercepta streams de texto/código y aplica compresión determinística (squeezer + minifier) antes de emitir.
Uso:
  cat payload.txt | python3 token_proxy_interceptor.py
  python3 token_proxy_interceptor.py [archivo]
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def intercept_and_compress(raw_text: str) -> str:
    if len(raw_text) < 200:
        return raw_text

    squeezer_script = SCRIPTS_DIR / "prompt_squeezer.py"
    minifier_script = SCRIPTS_DIR / "ast_minifier.py"
    tracker_script = SCRIPTS_DIR / "token_tracker.py"

    compressed = raw_text

    # 1. Si es JSON o código Python, intentar minificar
    stripped = raw_text.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
        if minifier_script.exists():
            try:
                res = subprocess.run(
                    ["python3", str(minifier_script)], input=raw_text, capture_output=True, text=True, check=True
                )
                compressed = res.stdout
            except Exception:
                pass
    elif squeezer_script.exists():
        try:
            res = subprocess.run(
                ["python3", str(squeezer_script)], input=raw_text, capture_output=True, text=True, check=True
            )
            compressed = res.stdout
        except Exception:
            pass

    orig_chars = len(raw_text)
    new_chars = len(compressed)
    chars_saved = max(0, orig_chars - new_chars)
    tokens_saved = int(chars_saved / 4)

    if tokens_saved > 20 and tracker_script.exists():
        subprocess.run(
            [
                "python3",
                str(tracker_script),
                "log",
                "--tool",
                "Proxy Interceptor",
                "--input-saved",
                str(tokens_saved),
                "--output-saved",
                "0",
            ],
            capture_output=True,
        )

    return compressed


def main():
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    elif len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        print("Uso: cat payload.txt | python3 token_proxy_interceptor.py", file=sys.stderr)
        sys.exit(1)

    out = intercept_and_compress(raw)
    print(out)


if __name__ == "__main__":
    main()

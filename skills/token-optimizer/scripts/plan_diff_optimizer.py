#!/usr/bin/env python3
"""
plan_diff_optimizer.py: Optimizador diferencial de planes para AGY.
Permite reemplazar quirúrgicamente una sección específica (## 1 a ## 5) en un spec.md o plan markdown,
ahorrando más del 80% de tokens de salida al no tener que re-emitir el plan completo.
Uso:
  python3 plan_diff_optimizer.py --section 3 --content "<nuevo_texto>" [spec.md]
  python3 plan_diff_optimizer.py --section "Requisitos" --content "<nuevo_texto>" [spec.md]
"""

import argparse
import re
import sys
from pathlib import Path


def update_markdown_section(filepath: Path, section_identifier: str, new_content: str) -> bool:
    if not filepath.exists():
        print(f"[!] Error: Archivo '{filepath}' no encontrado.", file=sys.stderr)
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Dividir el documento por encabezados de segundo nivel (## )
    sections = re.split(r"(?m)^(?=##\s+)", full_text)

    updated = False
    new_sections = []

    for sec in sections:
        header_match = re.match(r"^##\s+([^\n]+)", sec)
        if header_match:
            header_title = header_match.group(1).strip()
            # Comparar por número o por palabra clave
            is_match = (
                section_identifier in header_title
                or header_title.startswith(f"{section_identifier}.")
                or header_title.startswith(f"{section_identifier} ")
            )
            if is_match and not updated:
                header_line = header_match.group(0)
                new_sec = f"{header_line}\n\n{new_content.strip()}\n\n"
                new_sections.append(new_sec)
                updated = True
                continue

        new_sections.append(sec)

    if not updated:
        print(f"[!] Advertencia: No se encontró la sección '{section_identifier}'.", file=sys.stderr)
        return False

    result_text = "".join(new_sections)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result_text)

    print(f"✅ Sección '{section_identifier}' actualizada exitosamente en '{filepath}'.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Actualizador diferencial de secciones de planes")
    parser.add_argument(
        "--section", "-s", required=True, help="Número o título de la sección a modificar (ej: 3 o 'Requisitos')"
    )
    parser.add_argument("--content", "-c", required=True, help="Nuevo contenido markdown para la sección")
    parser.add_argument("file", nargs="?", default="spec.md", help="Ruta del archivo de plan (default: spec.md)")

    args = parser.parse_args()
    target_path = Path(args.file)

    ok = update_markdown_section(target_path, args.section, args.content)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

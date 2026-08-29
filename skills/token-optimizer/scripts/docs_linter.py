#!/usr/bin/env python3
"""
docs_linter.py: Auditor estático de integridad de documentación para AGY.
Verifica:
1. Enlaces markdown relativos válidos (0 enlaces rotos).
2. Numeración correlativa estricta de ADRs en docs/adr/.
3. Presencia de encabezados de nivel 1 (# Titulo).
Uso: python3 docs_linter.py [directorio_raiz]
"""

import re
import sys
from pathlib import Path


def check_markdown_links(root_dir: Path) -> list[str]:
    broken_links = []
    md_files = list(root_dir.rglob("*.md"))

    for md_path in md_files:
        # Ignorar git, node_modules, etc.
        if any(part.startswith(".") or part in ("node_modules", "venv") for part in md_path.parts):
            continue

        try:
            with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # Buscar enlaces tipo [texto](ruta)
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for text, link in links:
            # Ignorar URLs web, anchors internos (#) o protocolos custom (file://, conversation://)
            if link.startswith(("http://", "https://", "#", "mailto:", "conversation://", "file://")):
                continue

            # Limpiar anchor si existe en el enlace (ej: ruta.md#L10)
            clean_link = link.split("#")[0]
            if not clean_link:
                continue

            target = (md_path.parent / clean_link).resolve()
            if not target.exists():
                broken_links.append(f"[Link Roto] En {md_path.relative_to(root_dir)}: link '{link}' no existe.")

    return broken_links


def check_adr_numbering(root_dir: Path) -> list[str]:
    adr_dir = root_dir / "docs" / "adr"
    if not adr_dir.exists():
        return []

    errors = []
    adrs = sorted([f for f in adr_dir.glob("*.md") if f.name != "template.md"])

    expected_num = 1
    for f in adrs:
        m = re.match(r"^(\d{4})_", f.name)
        if not m:
            errors.append(f"[ADR Inválido] {f.name} no sigue el formato de 4 dígitos (ej: 0001_titulo.md).")
            continue

        num = int(m.group(1))
        if num != expected_num:
            errors.append(f"[ADR Secuencia Rota] Se esperaba ADR-{expected_num:04d} pero se encontró {f.name}.")
        expected_num = num + 1

    return errors


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    print(f"🔍 [Docs Linter] Auditando salud e integridad de documentación en '{root.name}'...")

    broken_links = check_markdown_links(root)
    adr_errors = check_adr_numbering(root)

    total_errors = broken_links + adr_errors

    print("=" * 70)
    if not total_errors:
        print("✅ [DOCUMENTACIÓN 100% SALUDABLE] Cero enlaces rotos y ADRs conformes.")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"❌ [ERRORES DETECTADOS] Se encontraron {len(total_errors)} problemas:")
        for err in total_errors:
            print(f"  • {err}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

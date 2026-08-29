#!/usr/bin/env python3
"""
spec_archiver.py: Archivador de especificaciones SDD completadas para AGY.
Mueve especificaciones finalizadas a specs/archive/YYYY-MM-DD_<nombre>.md y limpia spec.md,
evitando que herramientas de búsqueda y contexto lean especificaciones obsoletas (ahorro de tokens).
Uso: python3 spec_archiver.py [archivo_spec.md] [directorio_repo]
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def archive_spec(spec_file: Path, root_dir: Path) -> Path | None:
    if not spec_file.exists():
        print(f"[!] Error: El archivo '{spec_file}' no existe.", file=sys.stderr)
        return None

    archive_dir = root_dir / "specs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Extraer título o nombre del archivo
    with open(spec_file, "r", encoding="utf-8") as f:
        first_line = f.readline()

    m = re.match(r"^#\s+(.+)", first_line)
    if m:
        clean_title = re.sub(
            r"[^\w\s-]",
            "",
            m.group(1).lower().replace("especificación", "").replace("plan de implementación", "").strip(),
        )
        slug = re.sub(r"[\s_-]+", "_", clean_title).strip("_")
    else:
        slug = spec_file.stem

    if not slug:
        slug = "feature_spec"

    today = datetime.now().strftime("%Y-%m-%d")
    archived_filename = f"{today}_{slug}.md"
    archived_target = archive_dir / archived_filename

    # Mover archivo
    shutil.move(str(spec_file), str(archived_target))

    # Si era el spec.md de la raíz, crear un spec.md limpio con plantilla
    if spec_file.name == "spec.md":
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(f"""# Especificación de Software (SSOT)

> **Estado:** `En Espera / Listo para Nuevo Sprint`
> **Última Especificación Archivada:** `{archived_filename}`

---

## 1. Contexto & Propuesta de Valor
* **Objetivo:** [Definir objetivo del nuevo sprint o requerimiento]

---
""")

    return archived_target


def main():
    root = Path(".").resolve()
    spec_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "spec.md"
    if len(sys.argv) > 2:
        root = Path(sys.argv[2]).resolve()

    print(f"📦 [SDD Archiver] Archivando especificación '{spec_path.name}'...")
    archived = archive_spec(spec_path, root)

    if archived:
        print("=" * 70)
        print("✅ Especificación archivada exitosamente:")
        print(f"  • Archivo archivado: {archived.relative_to(root) if archived.is_relative_to(root) else archived}")
        print("  • Contexto de búsqueda y AST podado y limpio para el siguiente sprint.")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

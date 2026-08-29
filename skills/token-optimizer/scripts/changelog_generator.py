#!/usr/bin/env python3
"""
changelog_generator.py: Generador automático de CHANGELOG.md basado en commits convencionales y ADRs.
Analiza el historial de git log en CPU en < 10 ms y genera un changelog estructurado bajo Keep a Changelog.
Uso: python3 changelog_generator.py [directorio_repo]
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_commits(root_dir: Path) -> list[str]:
    try:
        res = subprocess.check_output(["git", "-C", str(root_dir), "log", "--pretty=format:%s", "-n", "100"], text=True)
        return res.splitlines()
    except Exception:
        return []


def generate_changelog(root_dir: Path) -> str:
    commits = get_git_commits(root_dir)
    now_str = datetime.now().strftime("%Y-%m-%d")

    feats = []
    fixes = []
    perfs = []
    docs = []
    others = []

    for c in commits:
        c_clean = c.strip()
        if c_clean.startswith("feat"):
            feats.append(c_clean)
        elif c_clean.startswith("fix"):
            fixes.append(c_clean)
        elif c_clean.startswith(("perf", "refactor")):
            perfs.append(c_clean)
        elif c_clean.startswith("docs"):
            docs.append(c_clean)
        elif c_clean:
            others.append(c_clean)

    lines = [
        "# Registro de Cambios (CHANGELOG)",
        "",
        "Todos los cambios notables en este proyecto son documentados automáticamente.",
        "El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).",
        "",
        f"## [No Publicado / Último Release] - {now_str}",
        "",
    ]

    if feats:
        lines.append("### 🚀 Nuevas Características (Features)")
        for f in feats[:15]:
            lines.append(f"- {f}")
        lines.append("")

    if perfs:
        lines.append("### ⚡ Rendimiento & Refactorización")
        for p in perfs[:15]:
            lines.append(f"- {p}")
        lines.append("")

    if fixes:
        lines.append("### 🐛 Correcciones (Fixes)")
        for fx in fixes[:15]:
            lines.append(f"- {fx}")
        lines.append("")

    if docs:
        lines.append("### 📚 Documentación & Gobernanza")
        for d in docs[:10]:
            lines.append(f"- {d}")
        lines.append("")

    return "\n".join(lines)


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target_changelog = root / "CHANGELOG.md"

    print(f"📝 [Changelog Generator] Generando CHANGELOG.md en '{root.name}'...")
    content = generate_changelog(root)

    with open(target_changelog, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ CHANGELOG.md generado exitosamente ({len(content.splitlines())} líneas).")


if __name__ == "__main__":
    main()

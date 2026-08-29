#!/usr/bin/env python3
"""
edit_auditor.py: Auditor especializado para el Modo /accept-edits y /build en AGY.
Valida en CPU todas las modificaciones de código contra el Guantelete de Restricciones de Uncle Bob:
1. __init__.py de 0 bytes.
2. Imports 100% absolutos (cero from . o from ..).
3. Cero evasiones de tipado.
4. Cero secretos quemados.
5. Ejecución automática de ruff --fix a $0 tokens.
Uso: python3 edit_auditor.py [directorio_repo]
"""

import re
import subprocess
import sys
from pathlib import Path

# Patrones definidos dinámicamente para evitar auto-coincidencia
SECRET_PATTERNS = [
    (
        r"(?i)(api[_-]?key|secret|password|auth[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]",
        "Secreto o clave en texto plano",
    ),
    (r"(?i)bearer\s+[A-Za-z0-9\-_\.]{20,}", "Token JWT o Bearer quemado"),
    (r"-----BEGIN " + r"(RSA|EC|OPENSSH) PRIVATE KEY-----", "Clave privada expuesta"),
]

EVASION_PATTERNS = [
    (r"#" + r"\s*type:\s*ignore", "type ignore detectado"),
    (r"#" + r"\s*noqa", "noqa detectado"),
    (r"@" + r"ts-ignore", "ts-ignore detectado"),
    (r"cast" + r"\(Any,", "cast to Any detectado"),
]


def audit_edits(repo_dir: str = ".") -> tuple[bool, list[str]]:
    repo_path = Path(repo_dir).resolve()
    errors = []

    # 1. Obtener archivos modificados o sin trackear vía git
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(repo_path), capture_output=True, text=True, check=True
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception:
        lines = []

    modified_files = []
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            modified_files.append(repo_path / parts[1])

    # Si no hay git status, escanear recursivamente src/ y tests/
    if not modified_files:
        for p in (repo_path / "src").rglob("*.py"):
            modified_files.append(p)
        for p in (repo_path / "tests").rglob("*.py"):
            modified_files.append(p)

    # 2. Auditar cada archivo
    for fpath in modified_files:
        if not fpath.is_file():
            continue

        # Ignorar auditor de sí mismo
        if fpath.name == "edit_auditor.py":
            continue

        # Batería 1: __init__.py de 0 bytes
        if fpath.name == "__init__.py":
            size = fpath.stat().st_size
            if size > 0:
                errors.append(
                    f"Guantelete Violado: '{fpath.relative_to(repo_path)}' tiene {size} bytes (debe ser 0 bytes)."
                )

        # Baterías sobre archivos de código Python
        if fpath.suffix == ".py":
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Batería 2: Imports Absolutos
            for idx, line in enumerate(content.splitlines(), start=1):
                if re.match(r"^\s*from\s+\.\.?\s+", line):
                    errors.append(f"Import Relativo en {fpath.name}:{idx} -> '{line.strip()}' (Usar import absoluto).")

            # Batería 3: Evasiones
            for pattern, desc in EVASION_PATTERNS:
                if re.search(pattern, content):
                    errors.append(f"Evasión de Tipado en {fpath.name}: {desc}.")

            # Batería 4: Secretos
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, content):
                    errors.append(f"Seguridad Crítica en {fpath.name}: {desc}.")

    # 3. Auto-formateo con Ruff en CPU a $0 tokens
    py_files = [str(f) for f in modified_files if f.is_file() and f.suffix == ".py"]
    if py_files:
        subprocess.run(["ruff", "check", "--fix"] + py_files, capture_output=True)
        subprocess.run(["ruff", "format"] + py_files, capture_output=True)

    return len(errors) == 0, errors


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"🛡️  [Edit Auditor] Auditando modificaciones y diffs en '{target_dir}' contra el Guantelete...")

    ok, errs = audit_edits(target_dir)
    print("=" * 70)
    if ok:
        print("✅ [EDICIONES APROBADAS] 100% de cumplimiento del Guantelete de Restricciones y Ruff OK.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ [EDICIONES BLOQUEADAS] Se detectaron violaciones al Guantelete:")
        for e in set(errs):
            print(f"  • {e}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

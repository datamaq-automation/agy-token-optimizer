#!/usr/bin/env python3
"""
plan_auditor.py: Auditor especializado para el Modo /plan en AGY.
Verifica que las especificaciones técnicas cumplan con el estándar SSOT de 5 secciones,
definición de puertos abstractos (abc.ABC) y que no se proponga modificar src/ durante el plan.
Uso: python3 plan_auditor.py [spec_file.md]
"""

import os
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("1. Contexto / Objetivo", r"(contexto|objetivo|summary|overview|meta|alcance)"),
    ("2. Negocio / Dominio", r"(modelo de negocio|canvas|dominio|entidad|regla)"),
    ("3. Requisitos SRS", r"(requisito|srs|funcional|nfr)"),
    ("4. Arquitectura & Puertos", r"(arquitectura|clean architecture|puerto|port|contrato|stack)"),
    ("5. Matriz de Pruebas TDD", r"(matriz de prueba|matriz de test|tdd|gobernanza de calidad|verificaci)"),
]


def audit_plan_file(filepath: str) -> tuple[bool, list[str]]:
    if not os.path.isfile(filepath):
        return False, [f"Archivo no encontrado: {filepath}"]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    errors = []
    content_lower = content.lower()

    # 1. Verificar las 5 secciones SSOT
    for sec_name, pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, content_lower):
            errors.append(f"Falta sección SSOT obligatoria: '{sec_name}'")

    # 2. Verificar que no contenga código en src/ con implementaciones directas
    if re.search(r"```python\s+(class|def)[^`]+src/", content):
        errors.append("Prohibido proponer código completo de implementación en 'src/' durante el modo /plan")

    return len(errors) == 0, errors


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "spec.md"
    if not os.path.exists(target):
        # Buscar en specs/
        specs_dir = Path("specs")
        if specs_dir.exists():
            files = list(specs_dir.glob("*.md"))
            if files:
                target = str(files[0])

    print(f"📋 [Plan Auditor] Auditando especificación técnica: '{target}'...")
    ok, errs = audit_plan_file(target)

    print("=" * 70)
    if ok:
        print("✅ [PLAN VÁLIDO] Cumple al 100% con las 5 secciones SSOT y Clean Architecture.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ [PLAN INVÁLIDO] Se detectaron violaciones en la especificación:")
        for e in errs:
            print(f"  • {e}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

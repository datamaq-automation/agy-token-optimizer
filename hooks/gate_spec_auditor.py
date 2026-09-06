#!/usr/bin/env python3
"""Hook PostToolUse: Auditor determinístico de especificaciones SDD en CPU ($0 tokens).

Valida automáticamente que todo 'spec.md' o 'specs/*.md' cumpla con las 5
secciones canónicas (SSOT).
"""

import json
import os
import re
import sys


def audit_spec_file(filepath: str) -> None:
    if not os.path.exists(filepath):
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return

    # Definición de las 5 secciones canónicas SDD
    canonical_sections = [
        ("Sección 1: Contexto y Requerimientos", [r"contexto", r"requerimiento", r"objetivo"]),
        ("Sección 2: Dominio e Interfaces (Ports)", [r"dominio", r"interface", r"port", r"modelo"]),
        ("Sección 3: Contratos y DTOs", [r"contrato", r"dto", r"schema", r"entrada/salida"]),
        ("Sección 4: Estrategia de Tests", [r"test", r"prueba", r"aceptaci[oó]n", r"tdd"]),
        (
            "Sección 5: Guantelete y Restricciones",
            [r"guantelete", r"restricci[oó]n", r"constraint", r"verificaci[oó]n"],
        ),
    ]

    missing_sections = []
    for sec_name, patterns in canonical_sections:
        found = any(re.search(pat, content, re.IGNORECASE) for pat in patterns)
        if not found:
            missing_sections.append(sec_name)

    if missing_sections:
        print(
            f"\n[AUDITOR SDD] ⚠️ Advertencia en '{os.path.basename(filepath)}': Faltan las siguientes secciones canónicas:\n"
            + "\n".join(f"  - {s}" for s in missing_sections),
            file=sys.stderr,
        )


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
            tool_call = payload.get("toolCall", {})
            args = tool_call.get("args", {})
            target_file = args.get("TargetFile", "")
            if target_file and ("spec.md" in target_file.lower() or "specs" in target_file.lower()):
                audit_spec_file(target_file)
    except Exception:
        pass

    # PostToolUse espera un objeto JSON vacío
    print(json.dumps({}))


if __name__ == "__main__":
    main()

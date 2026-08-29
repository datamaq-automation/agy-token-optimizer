#!/usr/bin/env python3
"""
plan_test_selector.py: Selector de impacto de tests existentes para el modo /plan de AGY.
Analiza en CPU (< 5 ms) qué tests existentes en tests/ importan o prueban los símbolos/módulos modificados
y genera el comando de ejecución exacto para la Sección 5 del plan a $0 tokens.
Uso: python3 plan_test_selector.py <simbolo_o_archivo> [directorio_repo]
"""

import sys
from pathlib import Path


def find_affecting_tests(target: str, root_dir: Path) -> list[str]:
    target_clean = Path(target).stem
    tests_dir = root_dir / "tests"
    if not tests_dir.exists():
        return []

    affected = []
    test_files = list(tests_dir.rglob("*.py")) + list(tests_dir.rglob("*.ts")) + list(tests_dir.rglob("*.js"))

    for tf in test_files:
        try:
            with open(tf, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Buscar imports o menciones del símbolo o módulo
                if target_clean in content or target in content:
                    affected.append(str(tf.relative_to(root_dir)))
        except Exception:
            continue

    return sorted(list(set(affected)))


def format_test_impact_bundle(target: str, affected_tests: list[str]) -> str:
    lines = [
        f"🧪 [Análisis de Impacto de Tests para '{target}']",
    ]
    if affected_tests:
        lines.append("📍 Tests Existentes Afectados:")
        for t in affected_tests[:5]:
            lines.append(f"   • `{t}`")
        if len(affected_tests) > 5:
            lines.append(f"   ... [+ {len(affected_tests) - 5} tests más]")

        # Generar comando exacto
        if affected_tests[0].endswith(".py"):
            cmd = f"pytest {' '.join(affected_tests[:4])} -v"
        else:
            cmd = f"npm test -- {' '.join(affected_tests[:4])}"

        lines.append(f"🚀 [Comando Quirúrgico para Sección 5 del Plan]: `{cmd}`")
    else:
        lines.append("ℹ️ No se detectaron tests previos asociados. (Se creará nueva suite TDD)")
        lines.append(f"🚀 [Comando Sugerido]: `pytest tests/unit/test_{Path(target).stem}.py -v`")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 plan_test_selector.py <simbolo_o_archivo> [directorio_repo]")
        sys.exit(1)

    target = sys.argv[1]
    root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(".").resolve()

    affected = find_affecting_tests(target, root)
    bundle = format_test_impact_bundle(target, affected)

    print("=" * 70)
    print(bundle)
    print("=" * 70)


if __name__ == "__main__":
    main()

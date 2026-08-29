#!/usr/bin/env python3
"""
plan_exporter.py: Exportador y sincronizador de planes AGY a spec.md para OpenCode.
Toma un artefacto markdown del plan, lo copia en spec.md y specs/active/<nombre>.md en la raíz del repositorio,
y valida su conformidad SSOT de 5 secciones con plan_auditor.py a $0 tokens.
Uso: python3 plan_exporter.py <archivo_plan.md> [directorio_repo]
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def export_plan(source_plan: Path, root_dir: Path) -> bool:
    if not source_plan.exists():
        print(f"❌ Error: Archivo de plan '{source_plan}' no encontrado.")
        return False

    try:
        with open(source_plan, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {source_plan}: {e}")
        return False

    # 1. Escribir spec.md en raíz
    target_spec = root_dir / "spec.md"
    with open(target_spec, "w", encoding="utf-8") as f:
        f.write(content)

    # 2. Escribir copia en specs/active/
    active_specs_dir = root_dir / "specs" / "active"
    active_specs_dir.mkdir(parents=True, exist_ok=True)
    active_spec_file = active_specs_dir / source_plan.name
    with open(active_spec_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("📄 [Plan Exporter] Plan exportado exitosamente:")
    print(f"   • Raíz (para OpenCode /build): {target_spec.relative_to(root_dir)}")
    print(f"   • Histórico Activo: {active_spec_file.relative_to(root_dir)}")

    # 3. Auditar con plan_auditor.py si existe
    auditor_script = SCRIPTS_DIR / "plan_auditor.py"
    if auditor_script.exists():
        res = subprocess.run(["python3", str(auditor_script), str(target_spec)], capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ [Auditoría SSOT] El plan cumple al 100% las 5 secciones canónicas requeridas.")
        else:
            print("⚠️ [Auditoría SSOT]:")
            print(res.stdout or res.stderr)

    return True


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 plan_exporter.py <archivo_plan.md> [directorio_repo]")
        sys.exit(1)

    source_plan = Path(sys.argv[1]).resolve()
    root_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(".").resolve()

    success = export_plan(source_plan, root_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

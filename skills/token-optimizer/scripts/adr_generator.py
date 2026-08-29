#!/usr/bin/env python3
"""
adr_generator.py: Generador secuencial de Architecture Decision Records (ADRs) para AGY.
Detecta el último índice en docs/adr/ (0001, 0002...) y genera el siguiente documento numerado,
preservando la memoria histórica de diseño y arquitectura en el repositorio a $0 tokens.
Uso: python3 adr_generator.py <titulo_decision> [directorio_repo]
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text.strip("_")


def get_next_adr_number(adr_dir: Path) -> int:
    if not adr_dir.exists():
        return 1
    max_num = 0
    for f in adr_dir.glob("*.md"):
        m = re.match(r"^(\d{4})_", f.name)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return max_num + 1


def generate_adr(title: str, root_dir: Path) -> Path:
    adr_dir = root_dir / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)

    next_num = get_next_adr_number(adr_dir)
    num_str = f"{next_num:04d}"
    slug = slugify(title)
    filename = f"{num_str}_{slug}.md"
    target_path = adr_dir / filename

    now_str = datetime.now().strftime("%Y-%m-%d")

    content = f"""# ADR-{num_str}: {title}

* **Estado:** `Aceptado`
* **Fecha:** `{now_str}`
* **Decisores:** `Equipo de Ingeniería / Antigravity AGY`
* **Gobernanza:** `Clean Architecture & Zero-Token Waste`

---

## 1. Contexto & Problema
[Describir la necesidad técnica o de negocio y los desafíos previos]

## 2. Decisión de Arquitectura
[Describir la solución técnica acordada, interfaces involucradas y tecnologías]

## 3. Consecuencias & Trade-offs
* **Impacto Positivo:** [Mejoras de rendimiento, reducción de latencia, desacoplamiento]
* **Impacto Negativo / Restricciones:** [Curva de aprendizaje, dependencias asumidas]

---

## 4. Estado de Implementación
* [ ] Especificación formal en `spec.md`
* [ ] Contratos abstractos en `src/domain/ports.py`
* [ ] Suite TDD superada en `tests/unit/`
"""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 adr_generator.py <titulo_decision> [directorio_repo]")
        sys.exit(1)

    title = sys.argv[1]
    root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(".").resolve()

    adr_path = generate_adr(title, root)
    print("🏛️  [ADR Generator] Nuevo ADR creado exitosamente:")
    print(f"  • Ruta: {adr_path.relative_to(root) if adr_path.is_relative_to(root) else adr_path}")
    print(f"  • Número: ADR-{adr_path.name[:4]}")


if __name__ == "__main__":
    main()

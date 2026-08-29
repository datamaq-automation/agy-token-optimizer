#!/usr/bin/env python3
"""
plan_artifact_scaffolder.py: Scaffolder determinístico de artefactos de plan para AGY.
Genera la plantilla markdown completa con metadatos de Git, 5 secciones SSOT y matrices TDD,
ahorrando más del 60% de tokens de salida en la fase de planificación.
Uso: python3 plan_artifact_scaffolder.py <nombre_plan> [ruta_salida]
"""

import os
import subprocess
import sys
from datetime import datetime


def get_git_info() -> tuple[str, str, str]:
    try:
        repo_name = os.path.basename(os.path.abspath("."))
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() or "main"
        user_name = subprocess.check_output(["git", "config", "user.name"], text=True).strip() or "Desarrollador"
    except Exception:
        repo_name = "proyecto-software"
        branch = "main"
        user_name = "Desarrollador"
    return repo_name, branch, user_name


def generate_plan_artifact(plan_title: str, repo_name: str, branch: str, user_name: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# Plan de Implementación: {plan_title}

> **Proyecto:** `{repo_name}` | **Rama:** `{branch}`
> **Autor:** `{user_name}` | **Fecha:** `{now_str}`
> **Estado:** `Borrador / En Revisión` | **Gobernanza:** `Zero-Token Waste & Constraint Gauntlet`

---

## 1. Contexto Estratégico & Propuesta de Valor
* **Objetivo Principal:** [Describir el problema central a resolver]
* **Alcance:** [Límites de la feature o refactorización]
* **Fuera de Alcance (*Out of Scope*):** [Elementos no incluidos]

---

## 2. Diagrama de Arquitectura & Flujo

```mermaid
flowchart TD
    In[Requerimiento] --> UseCase[Caso de Uso / Orquestador]
    UseCase --> Port[Puerto / Interfaz abc.ABC]
    Port --> Impl[Implementación en Infraestructura]
```

---

## 3. Especificación de Requisitos y Contratos

### 3.1. Requisitos Funcionales (FR)
* **FR-01:** [Descripción del comportamiento esperado]
* **FR-02:** [Validación de schemas o tipado estricto]

### 3.2. Contratos de Interfaces (`ports.py`)
```python
from abc import ABC, abstractmethod

class BasePort(ABC):
    @abstractmethod
    def execute(self, payload: object) -> object:
        pass
```

---

## 4. Cambios Propuestos por Componentes

### Componente: `src/domain/` & `src/application/`
#### [NEW] `src/domain/models.py`
- Definición de dataclasses puras.

#### [NEW] `src/application/use_cases.py`
- Orquestación y lógica de negocio.

---

## 5. Plan de Verificación & Matriz TDD (Suite RED-to-GREEN)

| ID Escenario | Caso de Prueba / Gherkin | Archivo de Test | Criterio de Éxito |
| :--- | :--- | :--- | :--- |
| **TC-01** | `Dado un payload válido, Cuando se procesa, Retorna 200 OK` | `tests/unit/test_use_case.py` | Test pasa verde |
| **TC-02** | `Validación del Guantelete (__init__.py de 0 bytes, imports absolutos)` | `agy-opt audit-edits .` | 0 violaciones |
| **TC-03** | `Validación estática con Pyright y Ruff` | `agy-opt ci .` | 0 errores |
"""


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 plan_artifact_scaffolder.py <nombre_plan> [ruta_salida]")
        sys.exit(1)

    title = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else f"specs/{title.lower().replace(' ', '_')}_plan.md"

    repo_name, branch, user_name = get_git_info()
    content = generate_plan_artifact(title, repo_name, branch, user_name)

    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(
        f"✅ Artefacto de plan generado exitosamente en '{out_file}' ({len(content.splitlines())} líneas pre-llenadas)."
    )


if __name__ == "__main__":
    main()

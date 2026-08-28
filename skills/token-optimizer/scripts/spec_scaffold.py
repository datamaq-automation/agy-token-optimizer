#!/usr/bin/env python3
"""
spec_scaffold.py: Generador determinístico de especificaciones técnicas SDD SSOT de 5 secciones.
Pre-rellena metadatos de Git y genera la estructura estricta ahorrando >1.500 tokens de salida en /plan.
Uso: python3 spec_scaffold.py [backend|frontend] [ruta_salida]
"""
import sys
import os
import subprocess
from datetime import datetime

def get_git_info():
    try:
        repo_name = os.path.basename(os.path.abspath("."))
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        user_name = subprocess.check_output(["git", "config", "user.name"], text=True).strip() or "Ingeniería de Software"
    except Exception:
        repo_name = "proyecto-software"
        branch = "main"
        user_name = "Desarrollador"
    return repo_name, branch, user_name

def generate_backend_spec(repo_name: str, branch: str, user_name: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d")
    return f"""# SRS-SPECS: {repo_name} — Single Source of Truth (SSOT) & Especificación del Sistema

> **Documento:** `spec.md`  
> **Versión:** `1.0.0`  
> **Estado:** `Borrador en Revisión`  
> **Fecha:** `{now_str}`  
> **Autor(es):** `{user_name}`  
> **Repositorio / Rama:** `{repo_name} ({branch})`  

---

## 1. Contexto Estratégico & Propuesta de Valor

### 1.1. Foco Estratégico & Alcance
* **Mercado / Dominio:** [Definir nicho o problema central]
* **User Persona:** [Perfil del usuario u operador del sistema]
* **Fuera de Alcance (*Out of Scope*):** [Lista de features o integraciones excluidas en esta fase]

### 1.2. Pilares de Valor de la Solución
| Pilar | Enfoque | Implementación en este Módulo |
| :--- | :--- | :--- |
| **1. Dominio & Negocio** | Reglas puras y entidades inmutables. | `src/domain/` (dataclasses y puertos abc.ABC) |
| **2. Casos de Uso** | Orquestación y flujos de aplicación. | `src/application/` (Use Cases y DTOs) |
| **3. Adaptadores & Infra** | Controladores, Gateways y FastAPI. | `src/adapters/` y `src/infrastructure/` |

---

## 2. Modelo de Negocio Canvas (9 Bloques) & Gobernanza
* **Propuesta de Valor:** [Beneficio principal que resuelve el problema del cliente]
* **Canales de Distribución:** [API REST FastAPI, Webhooks, CLI]
* **Segmentos de Clientes:** [Roles RBAC y permisos asociados]

---

## 3. Especificación de Requisitos de Software (SRS)

### 3.1. Requisitos Funcionales (FR)
* **FR-01 - [Nombre Requisito]:** El sistema debe [descripción de acción y validación de schemas].
* **FR-02 - Persistencia Transaccional:** El sistema debe interactuar mediante puertos tipados (`ports.py`).
* **FR-03 - Seguridad y Control de Acceso:** El sistema debe validar autenticación y roles de usuario.

### 3.2. Requisitos No Funcionales (NFR)
* **NFR-01 - Latencia:** p95 < 200 ms en consultas estándar.
* **NFR-02 - Tipado Estricto:** 100% de funciones y métodos anotados con Type Hints.
* **NFR-03 - Guantelete de Restricciones:** 100% cumplimiento de `test_architecture.py` (0 bytes en `__init__.py`).

---

## 4. Stack Tecnológico & Arquitectura Limpia (Clean Architecture)

### 4.1. Estructura Canónica de Capas
```
src/
├── domain/            # 1. Entidades puras y puertos abstractos (ports.py)
├── application/       # 2. Casos de uso orquestadores, DTOs y mappers
├── adapters/          # 3. Controladores y gateways (implementan puertos de dominio)
└── infrastructure/    # 4. FastAPI routers, DB clients y configuración centralizada
```

### 4.2. Puertos de Dominio y Contratos Iniciales (`ports.py`)
```python
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def save(self, entity: object) -> object:
        pass
```

---

## 5. Gobernanza de Calidad & Matriz de Pruebas (TDD RED Suite)

| ID Escenario | Caso de Prueba / Gherkin | Archivo de Test | Criterio de Aprobación |
| :--- | :--- | :--- | :--- |
| **TC-01** | `Dado un payload válido, Cuando se ejecuta el caso de uso, Entonces retorna 200 OK` | `tests/unit/test_use_cases.py` | Test pasa verde |
| **TC-02** | `El 100% de los archivos __init__.py deben tener 0 bytes` | `tests/test_architecture.py` | 0 errores AST |
| **TC-03** | `Validación estática de tipos con Pyright estricto` | `pyright` | 0 diagnósticos |
"""

def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "backend"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "spec.md"
    
    repo_name, branch, user_name = get_git_info()
    content = generate_backend_spec(repo_name, branch, user_name)
    
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ Plantilla SSOT SDD generada exitosamente en '{out_file}' ({len(content.splitlines())} líneas pre-llenadas).")

if __name__ == "__main__":
    main()

# SRS-SPECS: proyecto-software — Single Source of Truth (SSOT) & Especificación del Sistema

> **Documento:** `spec.md`
> **Versión:** `1.0.0`
> **Estado:** `Borrador en Revisión`
> **Fecha:** `2026-08-28`
> **Autor(es):** `Desarrollador`
> **Repositorio / Rama:** `proyecto-software (main)`

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

# Especificación de Software (SSOT): Optimización Integral de Hardware y Software Local

> **Estado:** `Aprobado para Implementación`  
> **Fecha:** `2026-09-06`  
> **Autor:** `Antigravity AGY / Ingeniero de Implementación`  
> **Modo:** `/build` (TDD & Gauntlet Runner)  

---

## 1. Contexto / Objetivo y Requisitos SRS
* **Objetivo:** Maximizar el aprovechamiento de los recursos locales (CPU de 8 hilos, 15 GB RAMDisk `/dev/shm`, Ruff nativo, embeddings y AST pruners) para reducir a $0 tokens el pre y post-procesamiento de código en el ecosistema Antigravity.
* **SRS-01 (PostToolUse Determinístico):** Interceptar toda modificación de archivos (`write_to_file`, `replace_file_content`) mediante un hook local que ejecute `ruff check --fix` y `ruff format` en la CPU (<30 ms) sin intervención ni turnos del LLM.
* **SRS-02 (MCP Servers Globales):** Configurar `~/.gemini/config/mcp_config.json` con herramientas de poda de contexto (`tokenix-filter`) y memoria de símbolos/vectores local en SQLite para acceso determinístico global.
* **SRS-03 (Aceleración RAMDisk en `/dev/shm`):** Integrar sincronización transparente del workspace hacia `/dev/shm/agy-workspace` y bases de datos SQLite en memoria compartida (15 GB/s) para suprimir latencias de I/O en linters y tests.
* **SRS-04 (Gobernanza Git Pre-commit):** Habilitar hook local en `.git/hooks/pre-commit` para impedir commits que rompan el Guantelete de Restricciones (0 bytes en `__init__.py`, imports absolutos, sin secretos).

---

## 2. Negocio, Dominio e Interfaces (Ports)
* **Reglas de Negocio / Dominio:**
  - *Zero Token Waste:* Ningún error sintáctico, de importación o formato de código debe generar turnos de corrección remota con el LLM.
  - *Zero I/O Lag:* Operaciones de testing y linting intensivas deben aprovechar la memoria RAM (/dev/shm).
  - *Clean Architecture Inward:* La lógica de optimización se expone a través de interfaces estables.
* **Puertos Abstractos (`src/domain/ports.py`):**
  - `class IHardwareOptimizer(abc.ABC)`: Contrato para detección y asignación de aceleradores locales (RAMDisk, CPU threads).
  - `class IPostEditHealer(abc.ABC)`: Contrato para la ejecución de auto-sanación determinística post-edición.

---

## 3. Contratos, DTOs y Arquitectura Técnica
* **Arquitectura de Capas:**
  - **Dominio:** Entidades y puertos abstractos sin dependencias externas (`src/domain/`).
  - **Aplicación:** Casos de uso de auto-sanación y orquestación de workspace en RAM (`src/application/`).
  - **Adaptadores:** Wrappers para llamadas de sistema (`ruff`, `shutil`, `sqlite3`, `git`) (`src/adapters/`).
  - **Infraestructura & Hooks:** Hooks de ciclo de vida en `~/.agents/hooks/` y configuraciones en `~/.gemini/config/`.
* **Esquema de Datos (DTOs):**
  - `HealResult(success: bool, file_path: str, execution_time_ms: float, actions_applied: list[str])`.
  - `RAMDiskStatus(mounted: bool, path: str, available_mb: float, synced_files: int)`.

---

## 4. Estrategia y Matriz de Pruebas TDD
* **Suite de Pruebas Unitarias e Integración (`tests/`):**
  - `test_hardware_healer_deterministic`: Verificar que un archivo con imports desordenados o no usados sea corregido automáticamente sin errores.
  - `test_ramdisk_workspace_sync`: Comprobar creación de `/dev/shm/agy-workspace` y sincronización incremental bidireccional.
  - `test_mcp_config_validity`: Validar que el archivo `~/.gemini/config/mcp_config.json` posea sintaxis JSON válida y ejecutables existentes.
  - `test_git_precommit_enforcement`: Validar que el script de pre-commit rechace commits con violaciones del Guantelete.
* **Matriz de Cobertura:** 100% de éxito en la suite `pytest`.

---

## 5. Guantelete de Restricciones y Verificación
1. **`__init__.py` de 0 bytes:** Todo paquete en `src/` y `tests/` debe mantener archivos de inicialización vacíos.
2. **Imports Absolutos:** Prohibido el uso de imports relativos (`from .` o `from ..`).
3. **Tipado Estricto:** Tipado completo de parámetros y retornos en funciones implementadas.
4. **Cero Directivas de Evasión:** Prohibido `# type: ignore`, `# noqa` o `@pytest.mark.skip`.
5. **Zero Secretos Quemados:** Auditoría estricta de credenciales en código.

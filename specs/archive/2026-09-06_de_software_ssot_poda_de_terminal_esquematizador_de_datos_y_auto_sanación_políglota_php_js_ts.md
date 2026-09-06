# Especificación de Software (SSOT): Poda de Terminal, Esquematizador de Datos y Auto-Sanación Políglota (PHP, JS, TS)

> **Estado:** `Aprobado para Planificación / Listo para /build`  
> **Fecha:** `2026-09-06`  
> **Autor:** `Antigravity AGY / Arquitecto SDD`  
> **Modo:** `/plan` (Arquitecto SDD & SSOT)  

---

## 1. Contexto / Objetivo y Requisitos SRS
* **Objetivo:** Explotar los 3 vectores de optimización de hardware/software local restantes en CPU e iGPU: compresión de salidas ruidosas de terminal en `run_command`, esquematización determinística de datos masivos (JSON/YAML/CSV) y extensión de la auto-sanación multinivel a PHP, JS y TS.
* **SRS-01 (Compresión Determinística de Salidas de Terminal):**
  - Interceptar en `PostToolUse` sobre `run_command` ejecuciones de comandos con salidas masivas (`npm`, `composer`, `pip`, `pytest`, `docker`).
  - Filtrar barras de progreso, advertencias de dependencias irrelevantes y trazas de descarga, preservando el código de salida, errores y resumen final.
  - Asegurar una reducción $\ge 80\%$ de tokens inyectados al contexto.
* **SRS-02 (Esquematizador Determinístico de Archivos de Datos):**
  - Interceptar lecturas masivas en `view_file` de archivos `.json`, `.yaml`, `.yml` y `.csv` que superen los 100 renglones.
  - Extraer en CPU (<10 ms) el esquema estructural de tipos (`clave: tipo`) y 2 filas/elementos de muestra representativa, evitando enviar miles de tokens de datos estáticos repetitivos. Reducción $\ge 90\%$.
* **SRS-03 (Auto-Sanación Políglota para PHP, JavaScript y TypeScript):**
  - Extender `IPostEditHealer` con soporte específico para `.php`, `.js` y `.ts`.
  - Nivel 1 (CPU): Verificación sintáctica determinística (`php -l` para PHP, parsers JS/TS) y auto-formato con herramientas locales.
  - Nivel 2 (iGPU Vulkan): Invocación local de `qwen2.5-coder:1.5b` ante errores sintácticos de PHP, JS o TS para auto-reparar el código antes de devolver el turno a la API remota ($0 tokens).
  - Registrar todos los ahorros en `token_savings.log` y `telemetry.db`.

---

## 2. Negocio, Dominio e Interfaces (Ports)
* **Reglas de Negocio / Dominio:**
  - *Máxima Preservación de Señal:* La compresión de salida nunca debe ocultar stacktraces de fallos reales o códigos de error.
  - *Consistencia Políglota:* PHP, JS y TS reciben el mismo tratamiento de tolerancia cero a errores de sintaxis que Python, resolviéndose en la máquina local.
* **Puertos Abstractos (`src/domain/ports.py`):**
  - `class ITerminalPruner(ABC)`: Contrato para compresión y extracción de señal de comandos de consola.
  - `class IDataSchemaPruner(ABC)`: Contrato para reducción estructural de JSON, YAML y CSV.
  - `class IPolyglotHealer(ABC)`: Contrato para validación y auto-sanación de archivos PHP, JS y TS.

---

## 3. Contratos, DTOs y Arquitectura Técnica
* **Arquitectura de Capas (Clean Architecture Canónica):**
  - **Dominio (`src/domain/`):** DTOs `TerminalPruneResult`, `DataSchemaResult`, `PolyglotHealResult` y puertos abstractos.
  - **Aplicación (`src/application/`):** Casos de uso de filtrado de consola y esquematización.
  - **Adaptadores (`src/adapters/`):**
    * `TerminalOutputPruner` (regex determinísticas y parsers de logs).
    * `DataSchemaPruner` (analizador sintáctico de JSON/YAML/CSV con tipado estructural).
    * `PolyglotHardwareHealer` (coordinador de linters locales y SLM en iGPU para PHP/JS/TS).
  - **Hooks & Config:** `gate_terminal_pruner_interceptor.py`, integración en `gate_ast_pruner_interceptor.py` y `gate_post_edit_healer.py`.
* **Esquema de Datos (DTOs):**
  - `TerminalPruneResult(original_lines: int, pruned_lines: int, exit_code: int, clean_output: str, reduction_ratio: float)`.
  - `DataSchemaResult(file_type: str, total_records: int, schema_summary: str, reduction_ratio: float)`.
  - `PolyglotHealResult(language: str, success: bool, actions_applied: list[str], execution_time_ms: float)`.

---

## 4. Estrategia y Matriz de Pruebas TDD
* **Suite de Pruebas en `tests/`:**
  - `tests/test_terminal_output_pruner.py`: Validación de poda en logs de npm, pip, pytest y composer (ratio $\ge 80\%$).
  - `tests/test_data_schema_pruner.py`: Validación de esquematización en JSON, YAML y CSV (ratio $\ge 90\%$).
  - `tests/test_polyglot_healer.py`: Verificación de auto-sanación L1 y L2 en PHP, JS y TS.
* **Matriz de Cobertura:** 100% de aserciones pasando en suite paralela `pytest -n 8`.

---

## 5. Guantelete de Restricciones y Verificación
1. **`__init__.py` de 0 bytes:** Integridad total en módulos nuevos.
2. **Imports 100% Absolutos:** Uso estricto de `from src.domain...` y `from src.adapters...`.
3. **Tipado Estricto al 100%:** Firmas con tipos exactos en parámetros y retornos.
4. **Cero Directivas de Evasión:** Prohibido `# type: ignore`, `# noqa`, o `@pytest.mark.skip`.
5. **Zero Secretos Quemados:** Auditoría estricta de seguridad.
6. **Español Estricto:** Documentación, tests, docstrings y logs en español.

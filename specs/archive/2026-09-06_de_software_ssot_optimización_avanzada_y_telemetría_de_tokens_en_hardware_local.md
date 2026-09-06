# Especificación de Software (SSOT): Optimización Avanzada y Telemetría de Tokens en Hardware Local

> **Estado:** `Aprobado para Planificación / Listo para /build`  
> **Fecha:** `2026-09-06`  
> **Autor:** `Antigravity AGY / Arquitecto SDD`  
> **Modo:** `/plan` (Arquitecto SDD & SSOT)  

---

## 1. Contexto / Objetivo y Requisitos SRS
* **Objetivo:** Completar el ciclo de optimización local con auto-sanación guiada por SLM en la iGPU, compresión automática de diffs de Git, servicio residente de Tokenix y un subsistema formal de telemetría y logs para auditar en tiempo real los tokens ahorrados ($0 costo):
  1. Auto-sanador de 2º nivel con Qwen 2.5 Coder 1.5B en la iGPU ante errores de sintaxis no resueltos por Ruff.
  2. Interceptor y compresor automático de `git diff` en `run_command`.
  3. Demonio residente de Tokenix en RAM (`tokenix serve`).
  4. Subsistema de observabilidad, logs estructurados (`token_savings.log`) y dashboard de métricas de ahorro.
* **SRS-01 (Auto-Sanación con SLM en iGPU):**
  - Si `ruff check --fix` y `ruff format` dejan un `SyntaxError` en un archivo editado, `gate_post_edit_healer.py` invoca localmente a `qwen2.5-coder:1.5b` (activo en VRAM en `localhost:11434`).
  - La inferencia se realiza en <500 ms en la iGPU, auto-reparando el archivo sin enviar el error al LLM remoto ($0 tokens y 0 turnos remotos perdidos).
* **SRS-02 (Compresión Automática de Git Diffs):**
  - Interceptar en `PreToolUse` comandos `run_command` que invoquen `git diff`.
  - Canalizar automáticamente la salida por el compresor determinístico para podar lockfiles (`package-lock.json`, `poetry.lock`), minificados y ruido de espacios, asegurando una reducción >= 70% de tokens.
* **SRS-03 (Demonio Residente de Tokenix en RAM):**
  - Configurar `tokenix serve` en segundo plano para eliminar la penalización de arranque en frío de los modelos de embeddings.
  - Asegurar tiempos de respuesta de herramientas MCP < 5 ms.
* **SRS-04 (Telemetría, Logs y Métricas de Ahorro):**
  - Registrar en `~/.agents/token_savings.log` y en SQLite cada evento de optimización (`AST_PRUNE`, `CACHE_HIT`, `DIFF_COMPRESS`, `IGPU_HEAL`).
  - Calcular tokens antes, tokens después, tokens ahorrados, latencia y dinero ahorrado en USD (según tarifas de modelos líderes).
  - Proveer un comando CLI de resumen (`agy-opt stats` / `token_tracker.py`) que visualice el balance acumulado.

---

## 2. Negocio, Dominio e Interfaces (Ports)
* **Reglas de Negocio / Dominio:**
  - *Observabilidad Determinística:* Ninguna optimización debe ocurrir silenciosamente sin quedar registrada en el log de telemetría para verificación del usuario.
  - *Zero Remote Ping-Pong:* Todo error corregible localmente por CPU o iGPU debe resolverse antes de devolver el control a la API externa.
* **Puertos Abstractos (`src/domain/ports.py`):**
  - `class ITokenTelemetry(ABC)`: Contrato para registro de eventos de optimización y cómputo de métricas acumuladas.
  - `class IDiffCompressor(ABC)`: Contrato para filtrado y compresión determinística de git diffs.
  - `class ISLMHealer(ABC)`: Contrato para reparación sintáctica local asistida por SLM en GPU.

---

## 3. Contratos, DTOs y Arquitectura Técnica
* **Arquitectura de Capas (Clean Architecture Canónica):**
  - **Dominio:** Puertos `ITokenTelemetry`, `IDiffCompressor`, `ISLMHealer` y DTOs (`src/domain/`).
  - **Aplicación:** Casos de uso `LogTokenSavingsUseCase` y `CompressDiffUseCase` (`src/application/`).
  - **Adaptadores:** Implementaciones `SQLiteTokenTelemetry`, `RegexDiffCompressor` y `OllamaVulkanSLMHealer` (`src/adapters/`).
  - **Infraestructura & Hooks:** Hook `gate_diff_compressor_interceptor.py` y ampliación de `gate_post_edit_healer.py`.
* **Esquema de Datos (DTOs):**
  - `TokenSavingsEvent(event_type: str, tool_name: str, tokens_before: int, tokens_after: int, tokens_saved: int, latency_ms: float, timestamp: str)`.
  - `SavingsSummary(total_tokens_saved: int, total_cost_saved_usd: float, events_count: dict[str, int])`.
  - `DiffCompressionResult(original_bytes: int, compressed_bytes: int, reduction_ratio: float, clean_diff: str)`.

---

## 4. Estrategia y Matriz de Pruebas TDD
* **Suite de Pruebas en `tests/`:**
  - `tests/test_token_telemetry.py`: Validación de inserción de eventos, agregación de totales y desglose por tipo.
  - `tests/test_diff_interceptor.py`: Validación de poda de lockfiles, preservación de código fuente y ratio >= 70%.
  - `tests/test_hardware_healer.py`: Verificación de auto-sanación integrada en CPU/iGPU.
* **Matriz de Cobertura:** 100% de éxito en suite `pytest -n 8`.

---

## 5. Guantelete de Restricciones y Verificación
1. **`__init__.py` de 0 bytes:** Todos los módulos creados mantienen 0 bytes exactos.
2. **Imports Absolutos:** Prohibido el uso de imports relativos (`from .` o `from ..`).
3. **Tipado Estricto al 100%:** Firmas con type hints en todos los parámetros y retornos.
4. **Cero Directivas de Evasión:** Prohibido `# type: ignore`, `# noqa` o `@pytest.mark.skip`.
5. **Zero Secretos Quemados:** Auditoría estricta de credenciales en código.

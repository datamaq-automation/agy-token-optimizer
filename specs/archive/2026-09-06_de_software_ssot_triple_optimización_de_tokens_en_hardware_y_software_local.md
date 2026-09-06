# Especificación de Software (SSOT): Triple Optimización de Tokens en Hardware y Software Local

> **Estado:** `Aprobado para Planificación / Listo para /build`  
> **Fecha:** `2026-09-06`  
> **Autor:** `Antigravity AGY / Arquitecto SDD`  
> **Modo:** `/plan` (Arquitecto SDD & SSOT)  

---

## 1. Contexto / Objetivo y Requisitos SRS
* **Objetivo:** Ejecutar la optimización paralela en los 3 ejes críticos identificados en la auditoría para alcanzar la máxima compresión de tokens ($0 costo) y aceleración por hardware (iGPU Vulkan, RAMDisk y CPU AVX2):
  1. Activación de la iGPU AMD Radeon Vega 11 en Ollama vía Vulkan.
  2. Implementación de Caché Semántico de Respuestas en RAMDisk `/dev/shm` a $0 tokens.
  3. Automatización de la Poda de AST en `PreToolUse` para lecturas de archivos.
* **SRS-01 (iGPU Vulkan en Ollama):**
  - Desplegar archivo de anulación systemd `/etc/systemd/system/ollama.service.d/igpu.conf` con `OLLAMA_IGPU_ENABLE=1`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_NUM_PARALLEL=4` y `OLLAMA_NUM_THREADS=8`.
  - Validar que `ollama ps` asigne el 100% de `qwen2.5-coder:1.5b` y `nomic-embed-text` a la GPU (`100% GPU (Vulkan)`).
  - Medir el incremento de tasa de inferencia (tokens/segundo) y verificar que la CPU quede 100% desocupada.
* **SRS-02 (Caché Semántico en RAMDisk `/dev/shm`):**
  - Definir el puerto abstracto `ISemanticCache` en dominio y su implementación con `sqlite3` + `numpy` sobre `/dev/shm/agy-cache/responses.db`.
  - Almacenar pares pregunta-respuesta con embeddings de 768 dimensiones de `nomic-embed-text`.
  - Resolver consultas con similitud de cosenos >= 0.92 en < 2 ms con 0 tokens de API remota.
* **SRS-03 (Interceptor de Poda AST en Lecturas):**
  - Interceptar llamadas a `view_file` en `PreToolUse` sobre archivos de código productivo extensos (>100 líneas).
  - Devolver de forma automática el esqueleto podado (firmas, clases, docstrings y tipos) reduciendo entre un 75% y 90% los tokens de entrada.
* **SRS-04 (Medición de Ahorro y Benchmarks):**
  - Registrar métricas de latencia de E/S, consumo de tokens evitados y tasa de generación en la base de auditoría local.

---

## 2. Negocio, Dominio e Interfaces (Ports)
* **Reglas de Negocio / Dominio:**
  - *Inversión de Dependencias:* Toda persistencia y acceso a hardware local depende de abstracciones puras en `src/domain/ports.py`.
  - *Cero Eco y Zero-Token Waste:* Jamás reenviar al LLM remoto consultas idénticas o código completo cuando un esqueleto resuelve el contrato.
  - *Hardware-First:* Si un componente de cómputo local (iGPU, AVX2, RAMDisk) está disponible, debe priorizarse frente a la ejecución en CPU pura o disco magnético/NVMe.
* **Puertos Abstractos (`src/domain/ports.py`):**
  - `class ISemanticCache(ABC)`: Contrato para almacenamiento y recuperación de respuestas vectorizadas.
  - `class IASTPruner(ABC)`: Contrato para esqueletización determinística de código según lenguaje.

---

## 3. Contratos, DTOs y Arquitectura Técnica
* **Arquitectura de Capas (Clean Architecture Canónica):**
  - **Dominio:** Puertos `ISemanticCache`, `IASTPruner` y DTOs inmutables (`src/domain/`).
  - **Aplicación:** Casos de uso `QuerySemanticCacheUseCase` y `PruneCodeContextUseCase` (`src/application/`).
  - **Adaptadores:** Implementaciones `SQLiteRAMSemanticCache` y `PythonASTPruner` (`src/adapters/`).
  - **Infraestructura & Hooks:** Hook `gate_ast_pruner_interceptor.py` en `~/.agents/hooks/` y configuración de servicio en `/etc/systemd/system/ollama.service.d/`.
* **Esquema de Datos (DTOs):**
  - `CacheEntry(query: str, response: str, embedding: list[float], timestamp: str)`.
  - `CacheQueryResult(hit: bool, response: str, similarity: float, tokens_saved: int)`.
  - `PruneResult(original_lines: int, pruned_lines: int, reduction_ratio: float, skeleton_code: str)`.

---

## 4. Estrategia y Matriz de Pruebas TDD
* **Suite de Pruebas en `tests/`:**
  - `tests/test_semantic_cache.py`: Validación de inserción, similitud de cosenos, acierto >= 0.92 y fallo < 0.92.
  - `tests/test_ast_view_interceptor.py`: Validación de poda AST en archivos >100 líneas, preservación de archivos pequeños y porcentaje de reducción >= 75%.
  - `tests/test_hardware_healer.py`: Verificación continua de auto-sanación en RAMDisk a 15 GB/s.
* **Matriz de Cobertura:** 100% de éxito en suite `pytest`.

---

## 5. Guantelete de Restricciones y Verificación
1. **`__init__.py` de 0 bytes:** Todos los paquetes nuevos o existentes mantienen 0 bytes exactos.
2. **Imports Absolutos:** Prohibido el uso de imports relativos (`from .` o `from ..`).
3. **Tipado Estricto al 100%:** Firmas con type hints en todos los parámetros y retornos.
4. **Cero Directivas de Evasión:** Prohibido `# type: ignore`, `# noqa` o `@pytest.mark.skip`.
5. **Zero Secretos Quemados:** Auditoría estricta de credenciales en código.

# Arquitectura del Sistema (Clean Architecture)

> **Tipo de Documento:** Diátaxis / Explanation
> **Propósito:** Explicar el modelo conceptual, dirección de dependencias y límites del dominio.

---

## 1. Reglas de Capas (Inward-Only)
```
[Infrastructure & Hooks] ──► [Adapters] ──► [Application] ──► [Domain (Core)]
```
1. **Domain:** Entidades puras y puertos abstractos (`abc.ABC`). Cero dependencias externas (`ports.py`).
2. **Application:** Casos de uso orquestadores y DTOs (`load_credentials.py`, casos de uso de caché).
3. **Adapters:** Controladores, adaptadores de caché en RAM (`semantic_cache.py`), poda AST (`ast_pruner.py`), auto-sanadores (`hardware_healer.py`) y sincronizadores (`ramdisk_optimizer.py`).
4. **Infrastructure & Hooks:** Hooks de ciclo de vida (`~/.agents/hooks/`), demonios de Ollama y configuraciones globales (`~/.gemini/config/`).

---

## 2. Capa de Memoria Caliente en RAMDisk (`/dev/shm`)
Para eliminar la latencia de disco y acelerar la ejecución de pruebas y búsquedas vectoriales:
* **Workspace en RAM:** `/dev/shm/agy-workspace/` permite ejecutar tests unitarios a 15 GB/s.
* **Caché Semántico SQLite:** `/dev/shm/agy-cache/responses.db` almacena vectores de 768 dimensiones con PRAGMAs de memoria (`WAL`, `mmap_size = 256MB`, `temp_store = MEMORY`) y similitud de cosenos AVX2 SIMD vía `numpy`.

---

## 3. Ciclo de Vida y Gobernanza de Hooks
* **PreInvocation:** Inyección del modo operativo actual (`/plan` vs `/build`).
* **PreToolUse:**
  - `gate_build_blocker.py`: Perímetro Zero-Trust y bloqueo de comandos destructivos.
  - `gate_ast_pruner_interceptor.py`: Intercepción de lecturas masivas en `view_file` e inducción de poda AST.
* **PostToolUse:**
  - `gate_post_edit_healer.py`: Auto-sanación determinística instantánea en CPU (`ruff check --fix` y `ruff format`).
  - `gate_spec_auditor.py`: Auditoría estática de especificaciones SDD en 5 secciones canónicas.

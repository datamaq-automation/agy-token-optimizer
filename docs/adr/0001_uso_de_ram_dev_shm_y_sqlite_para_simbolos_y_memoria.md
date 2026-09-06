# ADR-0001: Uso de RAM dev_shm y SQLite para Simbolos y Memoria

* **Estado:** `Aceptado`
* **Fecha:** `2026-08-28`
* **Decisores:** `Equipo de Ingeniería / Antigravity AGY`
* **Gobernanza:** `Clean Architecture & Zero-Token Waste`

---

## 1. Contexto & Problema
Las operaciones de búsqueda de símbolos, análisis de dependencias AST y ejecución de suites de pruebas TDD sobre bases de código complejas generan latencias acumulativas de E/S en disco, especialmente al iterar en ciclos de depuración frecuentes. A su vez, recargar y re-analizar archivos de gran tamaño mediante llamadas LLM remotas consume miles de tokens innecesariamente.

## 2. Decisión de Arquitectura
Se decide estructurar la persistencia volátil y de alta velocidad del ecosistema AGY sobre el sistema de archivos temporal en memoria RAM (`/dev/shm` - tmpfs) y bases de datos SQLite con pragmas optimizados para memoria:
1. **Montaje en Memoria Compartida (`/dev/shm`):**
   - Workspace de compilación y ejecución de pruebas en `/dev/shm/agy-workspace/` mediante `RAMDiskOptimizer`.
   - Rendimiento medido de ~15 GB/s sin requerir privilegios de superusuario (`sudo`).
2. **Motor de Símbolos y Memoria en SQLite:**
   - Indexación del grafo de símbolos y llamadas (`symbol_graph.py`) almacenado en SQLite.
   - Activación de `PRAGMA journal_mode = WAL;`, `PRAGMA synchronous = NORMAL;` y `PRAGMA temp_store = MEMORY;` para eliminar esperas de escritura en disco.
   - Sincronización asíncrona hacia almacenamiento persistente en SSD (`~/.agents/cache/`) para preservar el estado entre reinicios.

## 3. Consecuencias & Trade-offs
* **Impacto Positivo:**
  - Latencia de I/O reducida a 0 ms durante la ejecución de tests y consultas de símbolos.
  - Cero consumo de tokens en descubrimiento de código gracias a la resolución local en SQLite.
  - Desacoplamiento total entre el almacenamiento duradero y el área de trabajo caliente.
* **Impacto Negativo / Restricciones:**
  - La memoria en `/dev/shm` es volátil; se requiere sincronización explícita para evitar pérdida de datos si se reinicia el equipo.
  - Se debe limitar el tamaño máximo de workspaces en RAMDisk para no saturar la memoria física del sistema.

---

## 4. Estado de Implementación
* [x] Especificación formal en `spec.md` (archivada en `specs/archive/`).
* [x] Contratos abstractos en `src/domain/ports.py` (`IHardwareOptimizer`, `RAMDiskStatus`).
* [x] Suite TDD superada en `tests/test_hardware_healer.py`.
* [x] Adaptador `RAMDiskOptimizer` implementado en `src/adapters/ramdisk_optimizer.py`.

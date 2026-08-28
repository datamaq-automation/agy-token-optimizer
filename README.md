# ⚡ AGY Token Optimizer (Antigravity Global)

Paquete de optimización integral para **Google Antigravity (AGY)**. Reduce entre un **85% y 95% el consumo de tokens** de entrada y salida mediante el aprovechamiento exhaustivo de recursos locales (CPU multihilo de 8 núcleos, 18 GiB de RAM libre, inferencia local con Ollama `qwen2.5-coder:1.5b` y `nomic-embed-text`, y VFS en `/dev/shm` a 15 GB/s), pre/post-procesamiento determinístico y gobernanza estricta por modos (`/ask`, `/build`, `/plan`) bajo el **Guantelete de Restricciones (*Constraint Gauntlet*)** de Uncle Bob.

---

## 🚀 Instalación Rápida (1 Comando)

### Desde el repositorio clonado:
```bash
git clone https://github.com/datamaq-automation/agy-token-optimizer.git
cd agy-token-optimizer && ./install.sh
```

### O vía `curl`:
```bash
curl -fsSL https://raw.githubusercontent.com/datamaq-automation/agy-token-optimizer/main/install.sh | bash
```

---

## 🎯 Los 3 Modos de Operación

Una vez instalado, el agente AGY reconoce automáticamente el modo al inicio del mensaje:

| Modo | Propósito | Nivel de Modelo | Razonamiento | Reglas & Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`/ask`** | Consultas técnicas, explicación de arquitectura y auditoría de código. | **Económico** (`flash_lite` / `flash`) | **Low / Mínimo** | **Solo lectura.** Citas obligatorias a archivo y rango de líneas (`[archivo.py#L10-L25]`). Prohibido modificar o crear archivos. |
| **`/plan`** | Especificación técnica formal (`spec.md` SSOT de 5 secciones) y contratos de tests en `tests/`. | **Avanzado** (`pro` / alta capacidad) | **High / Alto** | Modificación permitida **solo** en `spec.md`, `specs/**` y `tests/**`. **PROHIBIDO modificar `src/`**. |
| **`/build`** | Implementador Autónomo TDD (Green-to-Red) y superación del Guantelete. | **Intermedio** (`flash` / balanceado) | **Medium / Low** | **Requisito Bloqueante:** Exige `spec.md` previo antes de tocar `src/`. Aplica ciclo TDD y supera `ci_local.sh`. |

---

## 🛠️ Catálogo Completo de 21 Herramientas Locales ($0 Tokens)

| Herramienta | Script | Propósito | Tiempo / Ahorro |
| :--- | :--- | :--- | :--- |
| **1. Pre-Borrador SLM** | `local_slm_draft.py` | Genera código base en RAM con `qwen2.5-coder:1.5b` a 16 tok/s. | ~1.5 s / **📉 90% salida** |
| **2. Sintetizador de Tests** | `unit_test_synthesizer.py` | Genera suites `@pytest.mark.parametrize` desde el AST. | 15 ms / **Ahorra >1.200 tok** |
| **3. Minificador de Schemas** | `ast_minifier.py` | Compacta payloads Python/JSON al formato más denso. | 5 ms / **📉 40-60% entrada** |
| **4. Memoria Semántica** | `semantic_response_cache.py` | Responde consultas repetidas desde RAM si similitud $\ge 0.92$. | 1 ms / **📉 100% ($0 API)** |
| **5. Ramdisk Workspace** | `ramdisk_manager.sh` | Almacenamiento en `/dev/shm` a **15 GB/s** sin sudo. | 0 ms I/O lag |
| **6. Compresor de PRs** | `pr_bundle_compressor.py` | Genera commits y descripciones de PR con SLM local. | ~1.2 s / **Ahorra >1.000 tok** |
| **7. Inyector de Contexto** | `context_injector.py` | Empaqueta firmas, relaciones y fragmentos en un bundle compacto. | < 30 ms / **< 500 tokens** |
| **8. Pipeline Zero-Trust CI** | `ci_local.sh` | Valida `__init__.py` 0 bytes, Ruff, Pyright strict, AST Gauntlet y tests. | ~1.5 s / **100% Calidad** |
| **9. Poda de AST** | `prune_python_ast.py` / `prune_ts_ast.js` | Skeletoniza dependencias reemplazando cuerpos por `...`. | 10 ms / **📉 92% tokens** |
| **10. Grafo de Símbolos** | `symbol_graph.py` | Indexa definiciones, callers/callees y puertos `abc.ABC` en SQLite. | 8 ms / **$0 API** |
| **11. Búsqueda Vectorial** | `local_search.py` | Búsqueda semántica con `nomic-embed-text` y caché SQLite. | 180 ms / **📉 90% tokens** |
| **12. Compresor de Diffs** | `diff_compressor.py` | Filtra lockfiles, binarios y cambios de espacios en `git diff`. | 15 ms / **📉 80% tokens** |
| **13. Reranker Semántico** | `local_reranker.py` | Filtra los 2 fragmentos más densos de la búsqueda vectorial. | 25 ms / **< 500 tokens** |
| **14. Generador de Stubs** | `stub_generator.py` | Crea stubs de tipo `.pyi` de 50 tokens para contratos de código. | 40 ms / **📉 90% tokens** |
| **15. Squeezer de Prompts** | `prompt_squeezer.py` | Normaliza texto, elimina redundancias y compacta markdown. | 5 ms / **📉 30-50% tokens** |
| **16. Diagramas Mermaid** | `arch_diagram.py` | Genera diagramas de arquitectura automáticos desde `symbols.db`. | 10 ms / **Ahorra >800 tok** |
| **17. Runner Multihilo** | `test_runner.sh` | Ejecuta tests concurrentes en los 8 núcleos de CPU con reporte denso. | < 300 ms |
| **18. Git Hooks** | `install_git_hooks.sh` | Bloquea commits/pushes que violen las restricciones de Uncle Bob. | < 50 ms |
| **19. Scaffolder SDD** | `spec_scaffold.py` | Genera la plantilla SSOT de 5 secciones con metadatos de Git. | < 10 ms / **Ahorra >1.500 tok** |
| **20. ROI Tracker** | `token_tracker.py` | Dashboard CLI de métricas de tokens y dólares (USD) ahorrados. | < 5 ms |
| **21. Daemon Watcher** | `local_watcher.py` | Monitorea archivos en tiempo real y mantiene la RAM sincronizada. | 0 ms en consulta |

---

## 🛡️ El Guantelete de Restricciones (*The Constraint Gauntlet*)

El ecosistema aplica las siguientes directivas estáticas inmutables:
1. **`__init__.py` de 0 bytes:** 100% de los `__init__.py` en `src/` y `tests/` con exactamente 0 bytes (cero re-exportaciones o código oculto).
2. **Clean Architecture Canónica:** `domain/` puro -> `application/` -> `adapters/` -> `infrastructure/`.
3. **Imports 100% Absolutos:** Prohibidos imports relativos (`from .` o `from ..`). Obligatorio `from src...` o `@/...`.
4. **Tipado Estricto al 100%:** Anotaciones explícitas en todos los parámetros y retornos. Prohibido `any`.
5. **Zero Evasión:** Prohibido relajar tests o usar `# type: ignore`, `# noqa`, `@ts-ignore`.

---

## 📄 Licencia
MIT License. Desarrollado por [datamaq-automation](https://github.com/datamaq-automation).

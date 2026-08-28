# ⚡ AGY Token Optimizer (Antigravity Global)

Paquete de optimización y aceleración integral para **Google Antigravity (AGY)**. Reduce entre un **85% y 95% el consumo de tokens** de entrada y salida mediante el aprovechamiento exhaustivo de recursos locales (CPU de 8 hilos, 18 GiB de RAM libre, inferencia local con Ollama `qwen2.5-coder:1.5b` y `nomic-embed-text`, y VFS en `/dev/shm` a 15 GB/s), bucles cerrados de auto-sanación, pre/post-procesamiento determinístico y gobernanza estricta bajo el **Guantelete de Restricciones (*Constraint Gauntlet*)** de Uncle Bob.

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

## ⚡ CLI Maestro Unificado: `agy-opt`

Una vez instalado, tienes acceso global al comando `agy-opt` en tu terminal:

```bash
# Iniciar watcher en RAM y sincronizar índices
agy-opt preflight

# Inyectar paquete de contexto quirúrgico (< 500 tokens)
agy-opt inject <nombre_simbolo_o_query>

# Auto-sanación de tests en bucle cerrado con SLM local
agy-opt heal [test_file.py]

# Pipeline Zero-Trust CI de 5 etapas (~1.5s en CPU)
agy-opt ci .

# Dashboard de ahorro de tokens y ROI en dólares (USD)
agy-opt stats

# Generar mensaje de commit convencional y resumen de PR
agy-opt commit

# Diagrama Mermaid de arquitectura a $0 tokens
agy-opt diagram

# Auditoría estática de seguridad OWASP y secretos
agy-opt audit

# Generar stubs de tipos (.pyi) de 50 tokens
agy-opt stubs src/

# Generar AGENTS.md adaptativo para el proyecto
agy-opt rules .
```

---

## 🎯 Los 3 Modos de Operación en AGY

| Modo | Propósito | Nivel de Modelo | Razonamiento | Reglas & Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`/ask`** | Consultas técnicas, explicación de arquitectura y auditoría de código. | **Económico** (`flash_lite` / `flash`) | **Low / Mínimo** | **Solo lectura.** Citas obligatorias a archivo y rango de líneas (`[archivo.py#L10-L25]`). Prohibido modificar o crear archivos. |
| **`/plan`** | Especificación técnica formal (`spec.md` SSOT de 5 secciones) y contratos de tests en `tests/`. | **Avanzado** (`pro` / alta capacidad) | **High / Alto** | Modificación permitida **solo** en `spec.md`, `specs/**` y `tests/**`. **PROHIBIDO modificar `src/`**. |
| **`/build`** | Implementador Autónomo TDD (Green-to-Red) y superación del Guantelete. | **Intermedio** (`flash` / balanceado) | **Medium / Low** | **Requisito Bloqueante:** Exige `spec.md` previo antes de tocar `src/`. Aplica ciclo TDD y supera `agy-opt ci`. |

---

## 🛠️ Catálogo Completo de 24 Herramientas Locales ($0 Tokens)

| Herramienta | Comando `agy-opt` / Script | Propósito | Tiempo / Ahorro |
| :--- | :--- | :--- | :--- |
| **1. Orquestador Maestro** | `agy-opt` / `agy_cli.py` | CLI unificado que orquesta las 24 herramientas. | < 5 ms |
| **2. Auto-Sanador Recursivo** | `agy-opt heal` / `self_healing_runner.py` | Corrige tests con `qwen2.5-coder` en RAM en bucle cerrado. | ~3 s / **📉 100% en debug** |
| **3. Reglas Adaptativas** | `agy-opt rules` / `adaptive_rules_engine.py` | Genera `AGENTS.md` adaptado a la pila tecnológica. | 10 ms / **Ahorra >1.500 tok** |
| **4. Pre-Borrador SLM** | `agy-opt draft` / `local_slm_draft.py` | Genera código base en RAM con `qwen2.5-coder:1.5b`. | ~1.5 s / **📉 90% salida** |
| **5. Sintetizador de Tests** | `agy-opt test-synth` / `unit_test_synthesizer.py` | Genera suites `@pytest.mark.parametrize` desde AST. | 15 ms / **Ahorra >1.200 tok** |
| **6. Minificador de Schemas**| `agy-opt minify` / `ast_minifier.py` | Compacta payloads Python/JSON al formato más denso. | 5 ms / **📉 40-60% entrada** |
| **7. Memoria Semántica** | `agy-opt cache` / `semantic_response_cache.py` | Responde consultas repetidas desde RAM si similitud $\ge 0.92$.| 1 ms / **📉 100% ($0 API)** |
| **8. Ramdisk Workspace** | `agy-opt ramdisk` / `ramdisk_manager.sh` | Almacenamiento en `/dev/shm` a **15 GB/s** sin sudo. | 0 ms I/O lag |
| **9. Compresor de PRs** | `agy-opt commit` / `pr_bundle_compressor.py` | Genera commits y descripciones de PR con SLM local. | ~1.2 s / **Ahorra >1.000 tok** |
| **10. Inyector de Contexto** | `agy-opt inject` / `context_injector.py` | Empaqueta firmas, relaciones y fragmentos en < 500 tokens. | < 30 ms / **< 500 tokens** |
| **11. Pipeline Zero-Trust CI**| `agy-opt ci` / `ci_local.sh` | Valida `__init__.py` 0 bytes, Ruff, Pyright, AST y tests. | ~1.5 s / **100% Calidad** |
| **12. Poda de AST** | `prune_python_ast.py` / `prune_ts_ast.js` | Skeletoniza dependencias reemplazando cuerpos por `...`. | 10 ms / **📉 92% tokens** |
| **13. Grafo de Símbolos** | `agy-opt symbols` / `symbol_graph.py` | Indexa definiciones, callers/callees y puertos `abc.ABC`. | 8 ms / **$0 API** |
| **14. Búsqueda Vectorial** | `agy-opt search` / `local_search.py` | Búsqueda semántica con `nomic-embed-text` y caché SQLite. | 180 ms / **📉 90% tokens** |
| **15. Compresor de Diffs** | `agy-opt diff` / `diff_compressor.py` | Filtra lockfiles, binarios y espacios en `git diff`. | 15 ms / **📉 80% tokens** |
| **16. Reranker Semántico** | `local_reranker.py` | Filtra los 2 fragmentos más densos de búsqueda vectorial. | 25 ms / **< 500 tokens** |
| **17. Generador de Stubs** | `agy-opt stubs` / `stub_generator.py` | Crea stubs de tipo `.pyi` de 50 tokens para contratos. | 40 ms / **📉 90% tokens** |
| **18. Squeezer de Prompts** | `agy-opt squeeze` / `prompt_squeezer.py` | Normaliza texto, elimina redundancias y compacta markdown.| 5 ms / **📉 30-50% tokens** |
| **19. Diagramas Mermaid** | `agy-opt diagram` / `arch_diagram.py` | Genera diagramas de arquitectura automáticos desde `symbols.db`. | 10 ms / **Ahorra >800 tok** |
| **20. Runner Multihilo** | `agy-opt test` / `test_runner.sh` | Ejecuta tests concurrentes en los 8 núcleos de CPU. | < 300 ms |
| **21. Git Hooks** | `agy-opt hooks` / `install_git_hooks.sh` | Bloquea commits/pushes que violen el Guantelete de Uncle Bob. | < 50 ms |
| **22. Scaffolder SDD** | `spec_scaffold.py` | Genera plantilla SSOT de 5 secciones con metadatos de Git.| < 10 ms / **Ahorra >1.500 tok** |
| **23. ROI Tracker** | `agy-opt stats` / `token_tracker.py` | Dashboard CLI de métricas de tokens y dólares (USD) ahorrados. | < 5 ms |
| **24. Daemon Watcher** | `agy-opt preflight` / `local_watcher.py` | Monitorea archivos en tiempo real y mantiene RAM sincronizada.| 0 ms en consulta |

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

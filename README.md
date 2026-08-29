# ⚡ AGY Token Optimizer (Antigravity Global)

Paquete integral de aceleración en hardware local, pre/post-procesamiento determinístico en CPU/RAM, gobernanza estática, control remoto total de VPS y compilación diferencial del modo `/plan` para **Google Antigravity (AGY)**. Reduce entre un **85% y 96% el consumo de tokens** de entrada y salida mediante el aprovechamiento exhaustivo de tu máquina local (CPU Ryzen de 8 hilos con AVX2/SIMD, 18 GiB de RAM libre, inferencia local con Ollama `qwen2.5-coder:1.5b` y `nomic-embed-text`, VFS en `/dev/shm` a 15 GB/s y túneles SSH persistentes a < 8 ms), auto-sanación en RAM, intercepción de tráfico en vuelo, parches remotos quirúrgicos y el **Guantelete de Restricciones (*Constraint Gauntlet*)** de Uncle Bob.

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

# 🧠 SUITE AVANZADA DEL MODO /plan (📉 96% Ahorro)
agy-opt preplan [dir]                                         # Pre-compila el mapa de arquitectura en < 300 tokens
agy-opt scaffold-plan <nombre_plan> [salida]                  # Genera el esqueleto SSOT completo en 5 ms
agy-opt scaffold-tests [ports.py] [salida_test.py]            # Genera suites TDD con mocks de abc.ABC en CPU
agy-opt audit-dip [src_dir]                                   # Audita la Inversión de Dependencias (DIP) por AST
agy-opt plan-diff --section <1-5> --content "<texto>" [spec.md]# Actualiza secciones individuales en 5 ms
agy-opt plan-impact <simbolo>                                 # Simula dependencias y callers afectados en symbols.db
agy-opt audit-plan [spec.md]                                  # Valida SSOT 5 secciones y contratos ports.py

# Inyectar paquete de contexto quirúrgico (< 500 tokens)
agy-opt inject <nombre_simbolo_o_query>

# Auto-sanación de tests en bucle cerrado con SLM local
agy-opt heal [test_file.py]

# Pipeline Zero-Trust CI de 5 etapas (~1.5s en CPU)
agy-opt ci .

# 🛡️ AUDITORÍA DE EDICIONES Y GAUNTLET
agy-opt audit-edits [dir]                                     # Valida diffs contra Guantelete y corre Ruff a $0

# Dashboard de ahorro de tokens y ROI en dólares (USD)
agy-opt stats

# Generar mensaje de commit convencional y resumen de PR
agy-opt commit

# Diagrama Mermaid de arquitectura a $0 tokens
agy-opt diagram

# Auditoría estática de seguridad OWASP y secretos
agy-opt audit

# Intercepción y compresión de stream en vuelo
cat prompt.md | agy-opt intercept

# Búsqueda semántica matricial SIMD/AVX2 (< 2 ms)
agy-opt simd "<query>"

# Ejecutar comando en Sandbox aislado de Linux
agy-opt sandbox pytest tests/

# 🌐 OPERACIONES REMOTAS TOTALES EN VPS (SSH PERSISTENTE < 8 ms)
agy-opt vps-health                                            # Diagnóstico de 4 líneas (< 50 tokens)
agy-opt vps-run "docker ps; uptime; free -h"                  # Ejecuta y poda logs masivos (📉 80%)
agy-opt vps-read /root/.bashrc 1 30                           # Lectura quirúrgica remota
agy-opt vps-patch /root/app.py --target "v1" --replacement "v2"# Parche in-place sin reescribir
agy-opt vps-index /root/proyectos_software                    # Sincroniza símbolos de la VPS a tu RAM
```

---

## 🎯 Los 3 Modos de Operación en AGY

| Modo | Propósito | Nivel de Modelo | Razonamiento | Reglas & Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`/ask`** | Consultas técnicas, explicación de arquitectura y auditoría de código. | **Económico** (`flash_lite` / `flash`) | **Low / Mínimo** | **Solo lectura.** Citas obligatorias a archivo y rango de líneas (`[archivo.py#L10-L25]`). Prohibido modificar o crear archivos. |
| **`/plan`** | Especificación técnica formal (`spec.md` SSOT de 5 secciones) y contratos de tests en `tests/`. | **Avanzado** (`pro` / alta capacidad) | **High / Alto** | **Pre-Condición:** Ejecuta `agy-opt preplan` (< 300 tok). Modificación permitida **solo** en `spec.md`, `specs/**` y `tests/**`. **PROHIBIDO modificar `src/`**. Auditado por `agy-opt audit-plan` y `agy-opt audit-dip`. |
| **`/build`** | Implementador Autónomo TDD (Green-to-Red) y superación del Guantelete. | **Intermedio** (`flash` / balanceado) | **Medium / Low** | **Requisito Bloqueante:** Exige `spec.md` previo antes de tocar `src/`. Aplica ciclo TDD y supera `agy-opt audit-edits` y `agy-opt ci`. |

---

## 🛠️ Catálogo Completo de 40 Herramientas Locales ($0 Tokens)

| Herramienta | Comando `agy-opt` / Script | Propósito | Tiempo / Ahorro |
| :--- | :--- | :--- | :--- |
| **1. Scaffolder Tests TDD**| `agy-opt scaffold-tests` / `plan_test_scaffolder.py` | Genera suites pytest con mocks de `abc.ABC`. | 10 ms / **Ahorra >1.500 tok** |
| **2. Auditor DIP** | `agy-opt audit-dip` / `plan_dip_auditor.py` | Valida dirección canónica de capas por AST. | 8 ms / **$0 API** |
| **3. Plan Diff Optimizer**| `agy-opt plan-diff` / `plan_diff_optimizer.py` | Actualiza secciones de planes sin reemitir todo.| 5 ms / **📉 80% salida** |
| **4. Pre-Plan Context** | `agy-opt preplan` / `plan_context_precompiler.py` | Compila contexto de arquitectura en < 300 tokens. | 40 ms / **📉 96% entrada** |
| **5. Scaffolder Planes** | `agy-opt scaffold-plan` / `plan_artifact_scaffolder.py` | Genera esqueleto SSOT de plan en markdown. | 5 ms / **📉 60% salida** |
| **6. Simulador Impacto** | `agy-opt plan-impact` / `plan_impact_simulator.py` | Calcula callers y dependencias en `symbols.db`. | 5 ms / **$0 API** |
| **7. Auditor Modo Plan** | `agy-opt audit-plan` / `plan_auditor.py` | Valida 5 secciones SSOT y bloquea código en `src/`.| 10 ms / **$0 API** |
| **8. Auditor Modo Edición**| `agy-opt audit-edits` / `edit_auditor.py` | Valida diffs contra el Guantelete y formatea con Ruff. | 20 ms / **$0 API** |
| **9. Monitor Salud VPS** | `agy-opt vps-health` / `vps_health.py` | Diagnóstico de 4 líneas (CPU, RAM, Disco, Docker). | < 200 ms / **< 50 tokens** |
| **10. Parcheador Remoto** | `agy-opt vps-patch` / `vps_patcher.py` | Modifica 5 líneas en la VPS sin reescribir archivos. | 10 ms / **📉 95% salida** |
| **11. Sincronizador Remoto**| `agy-opt vps-index` / `vps_symbol_sync.py` | Guarda el mapa AST de la VPS en tu RAM local. | ~200 ms / **0 ms nav ($0 API)**|
| **12. Ejecutor VPS Podado**| `agy-opt vps-run` / `vps_exec.py` | Ejecuta en VPS sobre socket SSH y poda logs masivos. | < 8 ms / **📉 80% tokens** |
| **13. Lector Quirúrgico VPS**| `agy-opt vps-read` / `vps_reader.py` | Lee rangos de líneas o extrae AST remoto de la VPS. | 15 ms / **📉 90% tokens** |
| **14. Orquestador Maestro**| `agy-opt` / `agy_cli.py` | CLI unificado que orquesta las 40 herramientas. | < 5 ms |
| **15. Proxy Interceptor** | `agy-opt intercept` / `token_proxy_interceptor.py` | Comprime streams en vuelo antes de salir a la API. | 5 ms / **📉 30-50% tokens** |
| **16. Acelerador SIMD** | `agy-opt simd` / `simd_vector_accelerator.py` | Búsqueda matricial AVX2 de 100.000 vectores en RAM. | **< 2 ms** en CPU |
| **17. Linux Sandbox** | `agy-opt sandbox` / `local_sandbox_runner.sh` | Ejecuta código de prueba en namespaces aislados. | 10 ms / **$0 Riesgo** |
| **18. Auto-Sanador Recursivo**| `agy-opt heal` / `self_healing_runner.py` | Corrige tests con `qwen2.5-coder` en RAM en bucle cerrado. | ~3 s / **📉 100% en debug** |
| **19. Reglas Adaptativas** | `agy-opt rules` / `adaptive_rules_engine.py` | Genera `AGENTS.md` adaptado a la pila tecnológica. | 10 ms / **Ahorra >1.500 tok** |
| **20. Pre-Borrador SLM** | `agy-opt draft` / `local_slm_draft.py` | Genera código base en RAM con `qwen2.5-coder:1.5b`. | ~1.5 s / **📉 90% salida** |
| **21. Sintetizador de Tests**| `agy-opt test-synth` / `unit_test_synthesizer.py` | Genera suites `@pytest.mark.parametrize` desde AST. | 15 ms / **Ahorra >1.200 tok** |
| **22. Minificador Schemas**| `agy-opt minify` / `ast_minifier.py` | Compacta payloads Python/JSON al formato más denso. | 5 ms / **📉 40-60% entrada** |
| **23. Memoria Semántica** | `agy-opt cache` / `semantic_response_cache.py` | Responde consultas repetidas desde RAM si similitud $\ge 0.92$.| 1 ms / **📉 100% ($0 API)** |
| **24. Ramdisk Workspace** | `agy-opt ramdisk` / `ramdisk_manager.sh` | Almacenamiento en `/dev/shm` a **15 GB/s** sin sudo. | 0 ms I/O lag |
| **25. Compresor de PRs** | `agy-opt commit` / `pr_bundle_compressor.py` | Genera commits y descripciones de PR con SLM local. | ~1.2 s / **Ahorra >1.000 tok** |
| **26. Inyector Contexto** | `agy-opt inject` / `context_injector.py` | Empaqueta firmas, relaciones y fragmentos en < 500 tokens. | < 30 ms / **< 500 tokens** |
| **27. Zero-Trust CI** | `agy-opt ci` / `ci_local.sh` | Valida `__init__.py` 0 bytes, Ruff, Pyright, AST y tests. | ~1.5 s / **100% Calidad** |
| **28. Poda de AST** | `prune_python_ast.py` / `prune_ts_ast.js` | Skeletoniza dependencias reemplazando cuerpos por `...`. | 10 ms / **📉 92% tokens** |
| **29. Grafo de Símbolos** | `agy-opt symbols` / `symbol_graph.py` | Indexa definiciones, callers/callees y puertos `abc.ABC`. | 8 ms / **$0 API** |
| **30. Búsqueda Vectorial** | `agy-opt search` / `local_search.py` | Búsqueda semántica con `nomic-embed-text` y caché SQLite. | 180 ms / **📉 90% tokens** |
| **31. Compresor Diffs** | `agy-opt diff` / `diff_compressor.py` | Filtra lockfiles, binarios y espacios en `git diff`. | 15 ms / **📉 80% tokens** |
| **32. Reranker Semántico**| `local_reranker.py` | Filtra los 2 fragmentos más densos de búsqueda vectorial. | 25 ms / **< 500 tokens** |
| **33. Generador de Stubs** | `agy-opt stubs` / `stub_generator.py` | Crea stubs de tipo `.pyi` de 50 tokens para contratos. | 40 ms / **📉 90% tokens** |
| **34. Squeezer de Prompts**| `agy-opt squeeze` / `prompt_squeezer.py` | Normaliza texto, elimina redundancias y compacta markdown.| 5 ms / **📉 30-50% tokens** |
| **35. Diagramas Mermaid** | `agy-opt diagram` / `arch_diagram.py` | Genera diagramas de arquitectura automáticos desde `symbols.db`. | 10 ms / **Ahorra >800 tok** |
| **36. Runner Multihilo** | `agy-opt test` / `test_runner.sh` | Ejecuta tests concurrentes en los 8 núcleos de CPU. | < 300 ms |
| **37. Git Hooks** | `agy-opt hooks` / `install_git_hooks.sh` | Bloquea commits/pushes que violen el Guantelete de Uncle Bob. | < 50 ms |
| **38. Scaffolder SDD** | `spec_scaffold.py` | Genera plantilla SSOT de 5 secciones con metadatos de Git.| < 10 ms / **Ahorra >1.500 tok** |
| **39. ROI Tracker** | `agy-opt stats` / `token_tracker.py` | Dashboard CLI de métricas de tokens y dólares (USD) ahorrados. | < 5 ms |
| **40. Daemon Watcher** | `agy-opt preflight` / `local_watcher.py` | Monitorea archivos en tiempo real y mantiene RAM sincronizada.| 0 ms en consulta |

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

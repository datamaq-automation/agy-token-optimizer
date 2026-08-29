# Manual de Referencia Técnica: CLI Maestro `agy-opt` (57 Herramientas)

Este manual documenta los 57 subcomandos determinísticos disponibles en el CLI maestro `agy-opt`, organizados por dominio funcional.

---

## 1. Aceleración de Hardware en `/build` y Cascada de Modelos

| Comando | Argumentos | Descripción | Rendimiento / Ahorro |
| :--- | :--- | :--- | :--- |
| `agy-opt deepseek-opt`| `[payload.json]` | Fuerza KV-Cache hit en DeepSeek (90% descuento), poda AST y conmuta V3/R1. | 2 ms / **📉 90% descuento API** |
| `agy-opt router` | `[--port 8080] [--test]` | Servidor proxy HTTP compatible con OpenAI que prioriza Free Tiers (Gemini/Groq) y conmuta a DeepSeek ante HTTP 429. | 10 ms conmutación / **$0 Free Tier** |
| `agy-opt sync-opencode` | `[--port 8080]` | Configura `~/.config/opencode/config.json` para conectarse al router local. | 2 ms |
| `agy-opt build-heal` | `<archivo.py>` | Auto-sana imports, tipado y sintaxis en CPU en bucle cerrado antes de consultar la API. | 20 ms / **📉 100% debug tokens** |
| `agy-opt build-ramdisk` | `[directorio_repo]` | Monta workspace en `/dev/shm` a 15 GB/s para pruebas instantáneas. | 10 ms / **0 ms I/O lag** |
| `agy-opt igpu-tune` | *(ninguno)* | Audita 8 hilos CPU AVX2, RAM y Vulkan para acelerar SLM local a >65 tok/s. | 5 ms |

---

## 2. Suite de Planificación Arquitectónica (`/plan`)

| Comando | Argumentos | Descripción | Rendimiento / Ahorro |
| :--- | :--- | :--- | :--- |
| `agy-opt preplan` | `[directorio_repo]` | Pre-compila mapa AST, stack, dependencias y CI/CD en < 300 tokens. | 40 ms / **📉 96% tokens entrada** |
| `agy-opt export-plan` | `<plan.md> [repo_dir]` | Vuelca y audita artefacto de plan a `spec.md` y `specs/active/` para OpenCode. | 1 ms |
| `agy-opt scaffold-plan` | `<nombre> [salida.md]`| Genera plantilla SSOT de 5 secciones en markdown en 5 ms. | 5 ms / **📉 60% tokens salida** |
| `agy-opt scaffold-tests`| `[ports.py] [test.py]` | Sintetiza suites TDD completas con mocks de `abc.ABC`. | 10 ms / **Ahorra >1.500 tokens** |
| `agy-opt audit-plan` | `[spec.md]` | Valida cumplimiento de 5 secciones SSOT y bloquea código en `src/`. | 10 ms |
| `agy-opt audit-dip` | `[src_dir]` | Audita Inversión de Dependencias (DIP) y capas de Clean Architecture por AST. | 8 ms |
| `agy-opt plan-diff` | `--section N --content "..."` | Compilador diferencial que actualiza secciones de planes sin reemitir todo. | 5 ms / **📉 80% salida** |
| `agy-opt plan-impact` | `<simbolo>` | Simula callers y dependencias afectadas en `symbols.db`. | 5 ms |
| `agy-opt validate-tree` | `[directorio_repo]` | Valida topología, dependencias (`pyproject.toml`, `package.json`) y linters. | 8 ms / **< 90 tokens** |
| `agy-opt test-impact` | `<simbolo> [dir]` | Mapea tests existentes afectados y genera comando de ejecución exacto. | 5 ms / **📉 600 tokens** |
| `agy-opt test-matrix` | `<puerto.py>` | Genera matriz de casos límite (*Happy Path, Null, Timeout, 422*) por AST. | 5 ms / **📉 500 tokens** |
| `agy-opt plan-ci` | `[directorio_repo]` | Extrae jobs y triggers de workflows de GitHub Actions / GitLab en < 60 tokens. | 3 ms / **📉 700 tokens** |
| `agy-opt scaffold-ci` | `[directorio_repo]` | Genera `.github/workflows/ci.yml` Zero-Trust con Guantelete de Uncle Bob. | 5 ms / **📉 600 tokens** |

---

## 3. Gobernanza Documental Diátaxis, ADRs y SDD

| Comando | Argumentos | Descripción | Rendimiento / Ahorro |
| :--- | :--- | :--- | :--- |
| `agy-opt init-docs` | `[directorio_repo]` | Inicializa carpetas Diátaxis (`docs/`) y SDD (`specs/active`, `specs/archive`). | 5 ms |
| `agy-opt adr` | `<titulo_decision>` | Genera ADR numerado secuencialmente (`docs/adr/0001_...`). | 5 ms |
| `agy-opt archive-spec` | `[spec.md] [dir]` | Archiva especificaciones completadas en `specs/archive/`. | 5 ms / **< 300 tokens** |
| `agy-opt audit-docs` | `[directorio_repo]` | Linter de enlaces markdown rotos y secuencia de ADRs. | 10 ms |
| `agy-opt changelog` | `[directorio_repo]` | Genera `CHANGELOG.md` automático desde Git commits y ADRs. | 5 ms |

---

## 4. Control Remoto Total de VPS (SSH Persistente < 8 ms)

| Comando | Argumentos | Descripción | Rendimiento / Ahorro |
| :--- | :--- | :--- | :--- |
| `agy-opt vps-health` | *(ninguno)* | Diagnóstico ultradenso de 4 líneas (CPU, RAM, Disco, Docker). | < 200 ms / **< 50 tokens** |
| `agy-opt vps-run` | `"<comando>"` | Ejecuta en VPS sobre socket SSH persistente y poda logs masivos. | < 8 ms / **📉 80% tokens** |
| `agy-opt vps-read` | `<ruta> [start] [end]` | Lectura quirúrgica remota o extracción de firmas AST. | 15 ms / **📉 90% tokens** |
| `agy-opt vps-patch` | `<ruta> --target X --replacement Y` | Parche quirúrgico in-place sin reescribir archivos remotos. | 10 ms / **📉 95% salida** |
| `agy-opt vps-index` | `[remote_dir]` | Sincroniza el mapa AST de la VPS hacia tu RAM local. | ~200 ms / **0 ms nav ($0 API)**|

---

## 5. Pre-Procesamiento, Memoria en RAM y Aceleración Local

| Comando | Argumentos | Descripción | Rendimiento / Ahorro |
| :--- | :--- | :--- | :--- |
| `agy-opt preflight` | `[directorio_repo]` | Inicia daemon watcher en RAM e indexa grafo de símbolos `symbols.db`. | 10 ms |
| `agy-opt inject` | `<simbolo_o_query>` | Empaqueta firmas, relaciones y fragmentos en < 500 tokens. | < 30 ms |
| `agy-opt heal` | `[test_file.py]` | Auto-sanación en bucle cerrado con SLM `qwen2.5-coder` en RAM. | ~3 s / **📉 100% debug** |
| `agy-opt ci` | `[directorio_repo]` | Pipeline Zero-Trust CI de 5 etapas (0 byte `__init__.py`, Ruff, Pyright, OWASP, Pytest). | ~1.5 s en CPU |
| `agy-opt audit-edits` | `[directorio_repo]` | Audita diffs contra el Guantelete y formatea con Ruff a $0 tokens. | 20 ms |
| `agy-opt stats` | *(ninguno)* | Dashboard CLI de métricas de tokens y dólares (USD) ahorrados. | < 5 ms |
| `agy-opt commit` | `[directorio_repo]` | Genera mensaje de commit convencional y resumen de PR con SLM local. | ~1.2 s / **Ahorra >1.000 tokens** |
| `agy-opt diagram` | `[directorio_repo]` | Genera diagrama Mermaid de arquitectura desde `symbols.db`. | 10 ms / **Ahorra >800 tokens** |
| `agy-opt audit` | `[directorio_repo]` | Auditoría estática de seguridad OWASP y secretos quemados. | < 50 ms |
| `agy-opt intercept` | *(stdin)* | Intercepta y comprime streams de prompts en vuelo. | 5 ms / **📉 30-50% tokens** |
| `agy-opt simd` | `"<query>"` | Búsqueda matricial AVX2 de 100.000 vectores en RAM. | **< 2 ms** en CPU |
| `agy-opt sandbox` | `"<comando>"` | Ejecuta comandos en namespaces aislados de Linux. | 10 ms |
| `agy-opt stubs` | `[src_dir] [out_dir]` | Genera stubs de tipos `.pyi` de 50 tokens. | 40 ms / **📉 90% tokens** |
| `agy-opt rules` | `[directorio_repo]` | Genera y alinea `AGENTS.md` adaptativo para el proyecto. | 10 ms |
| `agy-opt draft` | `"<prompt>"` | Genera código base en RAM con `qwen2.5-coder:1.5b`. | ~1.5 s / **📉 90% salida** |
| `agy-opt cache` | `query "<q>"` | Consulta la memoria semántica persistente en RAM. | 1 ms / **📉 100% ($0 API)** |
| `agy-opt ramdisk` | `[mount\|sync]` | Gestiona workspace ultra-rápido en `/dev/shm` (15 GB/s). | 0 ms I/O lag |
| `agy-opt test-synth` | `<archivo.py> [out.py]`| Sintetiza suites `@pytest.mark.parametrize` desde AST. | 15 ms |
| `agy-opt minify` | *(stdin)* | Compacta payloads JSON/Python al formato más denso. | 5 ms / **📉 40-60% tokens** |
| `agy-opt symbols` | `[index\|find <sym>]` | Consulta y manipulación directa de `symbols.db`. | 8 ms |
| `agy-opt search` | `"<query>"` | Búsqueda semántica vectorial local con `nomic-embed-text`. | 180 ms |
| `agy-opt diff` | *(stdin)* | Comprime diffs de Git eliminando lockfiles y espacios. | 15 ms / **📉 80% tokens** |
| `agy-opt squeeze` | *(stdin)* | Normaliza y comprime prompts en markdown. | 5 ms / **📉 30-50% tokens** |
| `agy-opt test` | `[pytest_args]` | Ejecuta tests concurrentes en los 8 núcleos de CPU. | < 300 ms |
| `agy-opt hooks` | `[directorio_repo]` | Instala hooks pre-commit y pre-push de Git. | < 50 ms |

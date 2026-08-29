# Registro de Cambios (CHANGELOG)

Todos los cambios notables en este proyecto son documentados automáticamente.
El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] - 2026-08-28

### 🚀 Nuevas Características (Features)
- **Suite de Cascada de Modelos y OpenCode:**
  - `model_cascade_router.py` (`agy-opt router`): Enrutador proxy en cascada inteligente que prioriza Free Tiers (Google Gemini 2.0 Flash y Groq Llama 3.3) a $0.00 y conmuta en 10 ms a DeepSeek-V3/R1 ante errores de cuota HTTP 429, con fallback final a Ollama local en RAM.
  - `opencode_config_sync.py` (`agy-opt sync-opencode`): Sincronizador de configuración para conectar OpenCode a `http://127.0.0.1:8080/v1` en modo `auto-cascade`.
  - `plan_exporter.py` (`agy-opt export-plan`): Exportador y sincronizador de artefactos de plan AGY a `spec.md` en la raíz del repositorio y `specs/active/` con validación SSOT de 5 secciones para OpenCode.
- **Suite de CI/CD y Testing en /plan:**
  - `plan_ci_detector.py` (`agy-opt plan-ci`): Detector determinístico de pipelines CI/CD (GitHub Actions, GitLab CI, Docker) en < 60 tokens.
  - `ci_workflow_scaffolder.py` (`agy-opt scaffold-ci`): Scaffolder de `.github/workflows/ci.yml` alineado al Guantelete de Uncle Bob y hook de despliegue VPS.
  - `plan_test_selector.py` (`agy-opt test-impact`): Mapeador de tests existentes afectados por AST para emitir el comando quirúrgico de verificación.
  - `plan_test_matrix_generator.py` (`agy-opt test-matrix`): Generador de matrices de casos de prueba límite desde `ports.py`.
- **Topología y Gobernanza Documental:**
  - `repo_structure_validator.py` (`agy-opt validate-tree`): Validador de topología v2 con parseo de dependencias (`pyproject.toml`, `package.json`) y auditoría de linters en 2 ms.
  - `docs_structure_init.py` (`agy-opt init-docs`): Inicializador de Diátaxis y SDD.
  - `adr_generator.py` (`agy-opt adr`): Generador de ADRs secuenciales (`docs/adr/0001_...` a `0004_...`).
  - `spec_archiver.py` (`agy-opt archive-spec`): Archivador de especificaciones a `specs/archive/`.
  - `docs_linter.py` (`agy-opt audit-docs`): Linter de enlaces markdown y secuencia de ADRs.
- **Suite VPS y Optimización de Hardware:**
  - Túneles SSH multiplexados persistentes (`~/.ssh/sockets/`) a < 8 ms de latencia.
  - `vps_exec.py`, `vps_reader.py`, `vps_patcher.py`, `vps_symbol_sync.py`, `vps_health.py`.
  - Interceptor de proxy en vuelo, acelerador matricial SIMD/AVX2 (< 2 ms) y Linux isolated sandbox.
- **Suite de Pruebas Automatizadas:** 53/53 tests ejecutados y superados al 100%.


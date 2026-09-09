# Registro de Cambios (CHANGELOG)

Todos los cambios notables en este proyecto son documentados automáticamente.
El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).

## [No Publicado / Último Release] - 2026-09-09

### 🚀 Nuevas Características (Features)
- feat: selección automática de modelo por modo (plan=high, build=low)
- feat(optimizer): poda en el origen para git/gh, telemetría medida y Gauntlet remoto
- feat(remote): cablear vps_exec al caso de uso y podar salidas de log
- feat(hooks): versionar el gate y enrutar run_command hacia la capa podada
- feat(gate): clasificador léxico de comandos, local y remoto
- feat(remote): ejecutor SSH con fallback IPv6→IPv4 y ejecución podada
- feat(domain): puertos y entidades para clasificación de comandos
- feat(remote): añadir comando agy-opt remote para verificar y conectar navegador con hardware local
- feat(polyglot): poda de terminal, esquematizador de datos y auto-sanación en php, js y ts
- feat(telemetry): auto-sanación slm en igpu, compresión git diff, demonio tokenix y telemetría de ahorro
- feat(hardware): verificar aceleración iGPU al 100% GPU y archivar especificación
- feat(optimizer): implementar caché semántico en RAMDisk y poda AST de lecturas
- feat(optimizer): implementar optimización local con auto-sanador determinístico y aceleración RAMDisk
- feat(cascade-router): usar credenciales estructuradas (JSON/YAML/.env) y fix User-Agent Cloudflare
- feat(credentials-loader): implementar carga polimórfica JSON/YAML/.env con metadatos (TC-01..TC-04 verdes)
- feat(multikey-pool): implement Multi-Key Pool rotation for Google AI Studio, Groq, and DeepSeek with failover
- feat(deepseek-opt): implement DeepSeek KV-cache alignment, payload pruning, and dynamic tiering (57 tools total, v2.2.0)
- feat(build-accel): implement build hardware healer, ramdisk workspace, and igpu optimizer (56 tools total, v2.1.0)
- feat(router): implement cascade model router (Free Tier -> DeepSeek -> Ollama) and OpenCode config sync (53 tools total)
- feat(plan-export): implement AGY plan exporter and OpenCode spec.md synchronizer (51 tools total)
- feat(plan-ci): implement CI/CD pipeline detector and Zero-Trust GitHub Actions scaffolder (50 tools total)
- feat(plan-testing): implement plan test selector and edge-case matrix generator (48 tools total)
- feat(repo-topology-v2): upgrade repo topology validator to v2 with dependency parsing and linter audit (46 tools)
- feat(repo-topology): integrate repository topology and canonical destination validator into preplan (46 tools)
- feat(repo-diataxis): apply complete Diataxis documentation structure and foundational ADRs (ADR-0001 to ADR-0004)
- feat(docs-linter): implement documentation link/ADR linter and automated CHANGELOG.md generator (45 tools complete)
- feat(docs-diataxis): implement Diataxis documentation initializer, sequential ADR generator, and SDD spec archiver (43 tools)
- feat(plan-advanced): complete Plan Advanced Suite with test scaffolder, DIP auditor, and differential plan optimizer (40 tools)
- feat(plan-opt): complete Plan Mode hardware precompiler, scaffolder, and impact simulator (37 tools)
- feat(auditors): add specialized plan_auditor and edit_auditor for mode-differentiated governance (34 tools)
- feat(vps-suite): complete total VPS remote suite with vps-health, vps-patcher, and vps-symbol-sync (32 tools)
- feat(vps): add persistent SSH ControlMaster, vps_exec output pruner, and surgical vps_reader
- feat(phase11): complete absolute hardware frontier with token proxy interceptor, SIMD vector accelerator, and Linux execution sandbox
- feat(phase10): complete ultimate AGY local optimizer with agy-opt master CLI, closed-loop self-healing runner, and adaptive rules engine
- feat(phase8-9): complete local hardware optimizer with SLM pre-drafts, test synthesizer, schema minifier, semantic cache, ramdisk manager, and PR synthesizer
- feat(phase6-7): add local watcher daemon, mermaid diagram generator, security audit, local reranker, stub generator, and prompt squeezer
- feat(phase5): add surgical context injector, zero-trust local CI pipeline, and subagent guidelines
- feat(phase4): add git hooks installer, SDD spec scaffolder, and token savings tracker
- feat(phase3): add in-memory symbol graph and multi-threaded test runner
- feat: add SQLite incremental vector caching and git diff compressor
- feat: initial release of agy-token-optimizer bundle

### ⚡ Rendimiento & Refactorización
- refactor(changelog): reorganize entries and update feature list for clarity
- perf(cpu): paralelizar indexación de símbolos y sincronización a RAMDisk en los 8 núcleos
- refactor(credentials-loader): cerrar ciclo SDD TC-01..TC-06 verdes

### 🐛 Correcciones (Fixes)
- fix(tests): inyectar mock de embedding en test_ramdisk_storage_and_sync para CI
- fix(ci): instalar numpy y aislar tests locales con skipif en entorno CI
- fix(ci): pinear ruff==0.16.2, excluir skills/ y reparar I001 en tests
- fix(changelog): dejar de descartar historial al regenerar el documento
- fix(types): resolver variables potencialmente no ligadas y tipado estricto de Path a str

### 📚 Documentación & Gobernanza
- docs: formalizar política Navegador First con delegación a subagente pro para plan
- docs(changelog): registrar feat selección automática de modelo por modo
- docs(changelog): registrar la corrección del truncado
- docs(changelog): registrar la capa de enrutado de comandos y la poda remota
- docs(spec): promover spec de enrutado de comandos por run_command
- docs: registrar hallazgos de iGPU Vulkan (ADR-0006) y guía how-to de aceleración
- docs(spec): archivar spec SDD consolidada tras cierre TC-01..TC-06 y registrar refactor en CHANGELOG
- docs(free-providers): add exact step-by-step UI guides for Google AI Studio, Groq, and DeepSeek API keys
- docs(agy-quotas): add Google Antigravity weekly quota details and student discount guide
- docs(free-providers): add comprehensive guide for Free Tier models (Gemini, Groq, OpenRouter, Mistral, Cerebras)
- docs(diataxis): add opencode_workflow, cli_commands reference, ADR-0005, and update README.md

# Registro de Cambios (CHANGELOG)

Todos los cambios notables en este proyecto son documentados automáticamente.
El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).

## [No Publicado / Último Release] - 2026-09-06

### 🚀 Nuevas Características (Features)
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

### ⚡ Rendimiento & Refactorización
- perf(cpu): paralelizar indexación de símbolos y sincronización a RAMDisk en los 8 núcleos
- refactor(credentials-loader): cerrar ciclo SDD TC-01..TC-06 verdes

### 🐛 Correcciones (Fixes)
- fix(types): resolver variables potencialmente no ligadas y tipado estricto de Path a str

### 📚 Documentación & Gobernanza
- docs: registrar hallazgos de iGPU Vulkan (ADR-0006) y guía how-to de aceleración
- docs(spec): archivar spec SDD consolidada tras cierre TC-01..TC-06 y registrar refactor en CHANGELOG
- docs(free-providers): add exact step-by-step UI guides for Google AI Studio, Groq, and DeepSeek API keys
- docs(agy-quotas): add Google Antigravity weekly quota details and student discount guide
- docs(free-providers): add comprehensive guide for Free Tier models (Gemini, Groq, OpenRouter, Mistral, Cerebras)
- docs(diataxis): add opencode_workflow, cli_commands reference, ADR-0005, and update README.md

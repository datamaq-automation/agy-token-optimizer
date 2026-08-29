# Registro de Cambios (CHANGELOG)

Todos los cambios notables en este proyecto son documentados automáticamente.
El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).

## [No Publicado / Último Release] - 2026-08-28

### 🚀 Nuevas Características (Features)
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

### 📚 Documentación & Gobernanza
- docs(agy-quotas): add Google Antigravity weekly quota details and student discount guide
- docs(free-providers): add comprehensive guide for Free Tier models (Gemini, Groq, OpenRouter, Mistral, Cerebras)
- docs(diataxis): add opencode_workflow, cli_commands reference, ADR-0005, and update README.md

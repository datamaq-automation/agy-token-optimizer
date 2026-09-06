# Registro de Cambios (CHANGELOG)

Todos los cambios notables en este proyecto son documentados automáticamente.
El formato sigue las directivas de [Keep a Changelog](https://keepachangelog.com/).

## [No Publicado / Último Release] - 2026-09-06

### 🚀 Nuevas Características (Features)
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

### ⚡ Rendimiento & Refactorización
- refactor(changelog): reorganize entries and update feature list for clarity
- perf(cpu): paralelizar indexación de símbolos y sincronización a RAMDisk en los 8 núcleos
- refactor(credentials-loader): cerrar ciclo SDD TC-01..TC-06 verdes

### 🐛 Correcciones (Fixes)
- fix(types): resolver variables potencialmente no ligadas y tipado estricto de Path a str

### 📚 Documentación & Gobernanza
- docs(changelog): registrar la capa de enrutado de comandos y la poda remota
- docs(spec): promover spec de enrutado de comandos por run_command
- docs: registrar hallazgos de iGPU Vulkan (ADR-0006) y guía how-to de aceleración
- docs(spec): archivar spec SDD consolidada tras cierre TC-01..TC-06 y registrar refactor en CHANGELOG
- docs(free-providers): add exact step-by-step UI guides for Google AI Studio, Groq, and DeepSeek API keys
- docs(agy-quotas): add Google Antigravity weekly quota details and student discount guide
- docs(free-providers): add comprehensive guide for Free Tier models (Gemini, Groq, OpenRouter, Mistral, Cerebras)
- docs(diataxis): add opencode_workflow, cli_commands reference, ADR-0005, and update README.md

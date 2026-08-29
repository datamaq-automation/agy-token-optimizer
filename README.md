# ⚡ AGY Token Optimizer (Antigravity Global)

Paquete integral de aceleración en hardware local, pre/post-procesamiento determinístico en CPU/RAM, gobernanza estática, control remoto total de VPS, enrutador inteligente en cascada (Free Tier ➔ DeepSeek ➔ Local SLM), optimizador de DeepSeek KV-Cache (90% descuento), auto-sanación en CPU, optimización de iGPU/AVX2, compilación diferencial de planes, validación topológica, sincronización con OpenCode, suites inteligentes de testing TDD, CI/CD Zero-Trust y arquitectura documental Diátaxis/ADR para **Google Antigravity (AGY)**. Reduce entre un **85% y 96% el consumo de tokens** de entrada y salida mediante el aprovechamiento exhaustivo de tu máquina local (CPU Ryzen de 8 hilos con AVX2/SIMD, 18 GiB de RAM libre, inferencia local con Ollama `qwen2.5-coder:1.5b` y `nomic-embed-text`, VFS en `/dev/shm` a 15 GB/s y túneles SSH persistentes a < 8 ms), auto-sanación en RAM, intercepción de tráfico en vuelo, parches remotos quirúrgicos y el **Guantelete de Restricciones (*Constraint Gauntlet*)** de Uncle Bob.

---

## 📚 Índice de Documentación (Metodología Diátaxis)

El proyecto cuenta con documentación técnica formal organizada según el estándar Diátaxis:

* 📖 **[Explicación Arquitectónica](docs/explanation/architecture.md):** Fundamentos teóricos, flujo de datos y filosofía de Uncle Bob.
* 🛠️ **[Guía de Desarrollo Local](docs/how-to/development.md):** Cómo contribuir, correr linters y ejecutar los 57 tests automatizados.
* 🌐 **[Operaciones Remotas en VPS](docs/how-to/vps_operations.md):** Gestión de servidores remotos sobre sockets SSH multiplexados a < 8 ms.
* 🚀 **[Flujo de Trabajo AGY + OpenCode](docs/how-to/opencode_workflow.md):** Operación en 1 sola terminal con cascada de tokens gratuitos y DeepSeek.
* 🎁 **[Guía de Proveedores Gratuitos (Free Tiers)](docs/reference/free_providers_guide.md):** Comparativa de Gemini, Groq, OpenRouter, Mistral, Cerebras y configuración de `.env`.
* 📋 **[Manual de Comandos CLI (57 Herramientas)](docs/reference/cli_commands.md):** Catálogo exhaustivo de todos los subcomandos de `agy-opt`.
* 🛡️ **[Convenciones del Guantelete](docs/reference/conventions.md):** Las 5 baterías inmutables de Clean Architecture.
* 🏛️ **[Registro de Decisiones Arquitectónicas (ADRs)](docs/adr/):** Histórico formal de decisiones desde ADR-0001 hasta ADR-0005.

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

## ⚡ El Flujo Diario en 1 Sola Terminal

No necesitas abrir múltiples terminales. Todo el flujo se opera desde una sola consola:

```bash
# 1. Enciende el router de modelos en segundo plano (0 tokens de API con Free Tier)
agy-opt router &

# 2. Configura OpenCode (solo se ejecuta 1 vez)
agy-opt sync-opencode

# 3. Diseña la arquitectura en AGY en modo /plan
agy
# > /plan <tu_requerimiento>
# > agy-opt export-plan spec.md .

# 4. Implementa el código en OpenCode en modo /build
opencode
# > /build Ejecuta spec.md en TDD
```

---

## 🌊 Enrutador en Cascada Inteligente (Free Tier ➔ DeepSeek ➔ Local)

```
                      [OpenCode /build envía petición]
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  Nivel 1: PROVEEDORES GRATUITOS (100% $0.00 Costo)      │
        │  • Google Gemini 2.0 Flash (Free Tier en AI Studio)     │
        │  • Groq Cloud (Llama 3.3 70B a 500 tokens/segundo)      │
        └────────────────────────────┬────────────────────────────┘
                                     │
                       ¿Error 429 (Cuota Agotada)?
                                     │
                                     ▼ SÍ (Conmutación en 10 ms)
        ┌─────────────────────────────────────────────────────────┐
        │  Nivel 2: DEEPSEEK OPTIMIZADO (90% Descuento KV-Cache)  │
        │  • DeepSeek-V3 ($0.028 / 1M tokens con Cache Hit)       │
        │  • DeepSeek-R1 (Razonamiento profundo para bugs duros)  │
        └────────────────────────────┬────────────────────────────┘
                                     │
                             ¿Sin Internet / Falla?
                                     │
                                     ▼ SÍ (Fallback de Emergencia)
        ┌─────────────────────────────────────────────────────────┐
        │  Nivel 3: INFERENCIA LOCAL OFFLINE                      │
        │  • Ollama local en tu RAM (qwen2.5-coder en CPU/Vulkan) │
        └─────────────────────────────────────────────────────────┘
```

---

## 🎯 Los 3 Modos de Operación en AGY

| Modo | Propósito | Nivel de Modelo | Razonamiento | Reglas & Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`/ask`** | Consultas técnicas, explicación de arquitectura y auditoría de código. | **Económico** (`flash_lite` / `flash`) | **Low / Mínimo** | **Solo lectura.** Citas obligatorias a archivo y rango de líneas (`[archivo.py#L10-L25]`). Prohibido modificar o crear archivos. |
| **`/plan`** | Especificación técnica formal (`spec.md` SSOT de 5 secciones) y contratos de tests en `tests/`. | **Avanzado** (`pro` / alta capacidad) | **High / Alto** | **Pre-Condición:** Ejecuta `agy-opt preplan` (< 300 tok). Modificación permitida **solo** en `spec.md`, `specs/**` y `tests/**`. **PROHIBIDO modificar `src/`**. Auditado por `agy-opt audit-plan` y `agy-opt audit-dip`. |
| **`/build`** | Implementador Autónomo TDD (Green-to-Red) y superación del Guantelete. | **Intermedio** (`flash` / balanceado) | **Medium / Low** | **Requisito Bloqueante:** Exige `spec.md` previo antes de tocar `src/`. Aplica ciclo TDD y supera `agy-opt audit-edits` y `agy-opt ci`. |

---

## 🛠️ Resumen de Herramientas Principales de `agy-opt`

*(Consulta el [Manual Completo de las 57 Herramientas](docs/reference/cli_commands.md) para más detalles).*

```bash
# Iniciar watcher en RAM y sincronizar índices
agy-opt preflight

# 🚀 Aceleración de Hardware en /build
agy-opt deepseek-opt [payload.json]                           # Fuerza 90% descuento por KV-Cache en DeepSeek
agy-opt build-heal <archivo.py>                               # Auto-sanación en CPU en 20 ms
agy-opt build-ramdisk [dir]                                   # Workspace en /dev/shm a 15 GB/s
agy-opt igpu-tune                                             # Ajusta AVX2 y Vulkan para SLM >65 tok/s

# 🌊 Enrutador en Cascada y Sincronización
agy-opt router [--port 8080]                                  # Inicia proxy local
agy-opt sync-opencode                                         # Configura OpenCode al router local
agy-opt export-plan <plan.md> [dir]                           # Exporta a spec.md para OpenCode

# 🧠 Suite Avanzada de Planificación (/plan)
agy-opt preplan [dir]                                         # Pre-compila mapa AST en < 300 tokens
agy-opt test-impact <simbolo>                                 # Mapea tests existentes afectados
agy-opt test-matrix <puerto.py>                               # Genera matriz TDD de casos límite
agy-opt validate-tree [dir]                                   # Valida topología y dependencias
agy-opt plan-ci [dir]                                         # Extrae workflows CI en < 60 tokens

# 📚 Gobernanza Documental Diátaxis y ADRs
agy-opt init-docs [dir]                                       # Inicializa docs/ y specs/
agy-opt adr <titulo_decision>                                 # Genera ADR numerado
agy-opt archive-spec [spec.md]                                # Archiva especificaciones (< 300 tok)
agy-opt audit-docs [dir]                                      # Audita links y secuencia de ADRs
agy-opt changelog [dir]                                       # Genera CHANGELOG.md automático

# 🌐 Operaciones Remotas VPS (SSH < 8 ms)
agy-opt vps-health                                            # Diagnóstico de 4 líneas (< 50 tokens)
agy-opt vps-run "<comando>"                                   # Ejecuta y poda logs masivos (📉 80%)
agy-opt vps-read <ruta> 1 30                                  # Lectura quirúrgica remota
agy-opt vps-patch <ruta> --target X --replacement Y           # Parche in-place sin reescribir
agy-opt vps-index [dir]                                       # Sincroniza símbolos VPS en tu RAM
```

---

## 🛡️ El Guantelete de Restricciones (*The Constraint Gauntlet*)

El ecosistema aplica las siguientes directivas estáticas inmutables:
1. **`__init__.py` de 0 bytes:** 100% de los `__init__.py` en `src/` y `tests/` con exactamente 0 bytes.
2. **Clean Architecture Canónica:** `domain/` puro -> `application/` -> `adapters/` -> `infrastructure/`.
3. **Imports 100% Absolutos:** Prohibidos imports relativos (`from .` o `from ..`). Obligatorio `from src...` o `@/...`.
4. **Tipado Estricto al 100%:** Anotaciones explícitas en todos los parámetros y retornos. Prohibido `any`.
5. **Zero Evasión:** Prohibido relajar tests o usar `# type: ignore`, `# noqa`, `@ts-ignore`.

---

## 📄 Licencia
MIT License. Desarrollado por [datamaq-automation](https://github.com/datamaq-automation).

# ⚡ AGY Token Optimizer (Antigravity Global)

Paquete de optimización global para **Google Antigravity (AGY)**. Reduce entre un **85% y 95% el consumo de tokens** de entrada y salida mediante el aprovechamiento de recursos de hardware locales (CPU multihilo, RAM, GPU integrada), pre/post-procesamiento determinístico y gobernanza estricta por modos (`/ask`, `/build`, `/plan`) bajo el **Guantelete de Restricciones (*Constraint Gauntlet*)** de Uncle Bob.

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

## 🛠️ Herramientas Locales de Pre/Post-Procesamiento ($0 Tokens)

### 1. Inyector Quirúrgico de Contexto (< 500 Tokens Bundle)
Empaqueta firmas exactas, llamadas y esqueletos de dependencias en un bloque ultradenso:
```bash
# Por Símbolo
python3 ~/.agents/skills/token-optimizer/scripts/context_injector.py --symbol <nombre_simbolo>

# Por Archivo
python3 ~/.agents/skills/token-optimizer/scripts/context_injector.py --file <archivo.py>

# Por Requerimiento en Lenguaje Natural
python3 ~/.agents/skills/token-optimizer/scripts/context_injector.py --query "<requerimiento>" [directorio]
```

### 2. Pipeline Local Zero-Trust CI en CPU (1.5 segundos)
Ejecuta las 5 etapas inmutables de validación local antes de dar por completada cualquier tarea:
```bash
~/.agents/skills/token-optimizer/scripts/ci_local.sh [directorio_repo]
```

### 3. Poda de AST Determinística en CPU (~92% Ahorro de Tokens)
Para inspeccionar módulos o dependencias sin cargar archivos completos (>100 líneas):
```bash
# Python
python3 ~/.agents/skills/token-optimizer/scripts/prune_python_ast.py <archivo.py> [--docstrings]

# TypeScript / JavaScript
node ~/.agents/skills/token-optimizer/scripts/prune_ts_ast.js <archivo.ts>
```

### 4. Grafo de Símbolos y Relaciones en RAM/SQLite (Zero-Token Architecture)
Indexa definiciones, callers/callees y mapeo de interfaces abstractas (`abc.ABC`) a adaptadores en < 50 ms:
```bash
# Indexar base de código
python3 ~/.agents/skills/token-optimizer/scripts/symbol_graph.py index [directorio]

# Buscar símbolos y firmas exactas
python3 ~/.agents/skills/token-optimizer/scripts/symbol_graph.py find <nombre_simbolo>

# Mapear implementaciones de puertos
python3 ~/.agents/skills/token-optimizer/scripts/symbol_graph.py implementations <nombre_puerto>

# Rastrear llamadas entrantes
python3 ~/.agents/skills/token-optimizer/scripts/symbol_graph.py callers <nombre_funcion>
```

### 5. Búsqueda Semántica Vectorial con Caché SQLite (180 ms)
Búsqueda de fragmentos exactos usando `nomic-embed-text` de Ollama indexado incrementalmente en `~/.agents/cache/vectors.db`:
```bash
python3 ~/.agents/skills/token-optimizer/scripts/local_search.py "<query>" [directorio] [top_k]
```

### 6. Compresor Determinístico de Git Diffs (70% - 90% Ahorro en PRs/Diffs)
Filtra lockfiles (`package-lock.json`, `poetry.lock`, `Cargo.lock`), blobs binarios, assets minificados y cambios triviales de espacios:
```bash
git diff | python3 ~/.agents/skills/token-optimizer/scripts/diff_compressor.py
```

### 7. Runner de Pruebas Multihilo (8 Núcleos) con Reporte Denso
Ejecuta suites de prueba concurrentes y oprime logs de tests aprobados para no saturar el contexto:
```bash
~/.agents/skills/token-optimizer/scripts/test_runner.sh [tests]
```

### 8. Gobernanza Automatizada de Git Hooks (pre-commit / pre-push)
Instala ganchos automáticos para validar `__init__.py` de 0 bytes, formateo y el Guantelete de Restricciones antes de cada commit o push:
```bash
~/.agents/skills/token-optimizer/scripts/install_git_hooks.sh [directorio_repo]
```

### 9. Scaffolder de Especificaciones SDD SSOT (Ahorro >1.500 Tokens en /plan)
Genera la estructura estricta de 5 secciones con metadatos de Git auto-completados:
```bash
python3 ~/.agents/skills/token-optimizer/scripts/spec_scaffold.py [backend|frontend] [ruta_salida]
```

### 10. Dashboard y Monitor de Ahorro de Tokens y ROI ($ USD)
Rastrea métricas de ahorro y costo evitado en USD en tiempo real:
```bash
python3 ~/.agents/skills/token-optimizer/scripts/token_tracker.py stats
```

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

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
| **`/build`** | Implementador Autónomo TDD (Green-to-Red) y superación del Guantelete. | **Intermedio** (`flash` / balanceado) | **Medium / Low** | **Requisito Bloqueante:** Exige `spec.md` previo antes de tocar `src/`. Aplica ciclo TDD y supera `test_architecture.py`. |

---

## 🛠️ Herramientas Locales de Pre/Post-Procesamiento ($0 Tokens)

### 1. Poda de AST Determinística en CPU (~92% Ahorro de Tokens)
Para inspeccionar módulos o dependencias sin cargar archivos completos (>100 líneas):
```bash
# Python
python3 ~/.agents/skills/token-optimizer/scripts/prune_python_ast.py <archivo.py> [--docstrings]

# TypeScript / JavaScript
node ~/.agents/skills/token-optimizer/scripts/prune_ts_ast.js <archivo.ts>
```

### 2. Búsqueda Semántica Vectorial en RAM (150 ms)
Búsqueda de fragmentos exactos usando el modelo local `nomic-embed-text` de Ollama:
```bash
python3 ~/.agents/skills/token-optimizer/scripts/local_search.py "<query>" [directorio] [top_k]
```

### 3. Post-Procesamiento y Linters Determinísticos
Ejecución local inmediata tras cada edición para evitar turnos de corrección en la nube:
```bash
# Python
ruff check --fix <archivo> && ruff format <archivo>

# TypeScript / JavaScript
npx eslint --fix <archivo>
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

## 📊 Matriz de Ahorro Cuantitativo

```
Turno Promedio de Edición Tradicional:
  Input:  ~8.000 tokens (Lecturas completas de archivos)
  Output: ~2.000 tokens (Reescritura de archivos enteros + Verbosidad)
  Costo:  Modelo Pro en toda la sesión

Turno Promedio con AGY Token Optimizer:
  Input:  ~700 tokens (Poda AST + Búsqueda Semántica local)
  Output: ~120 tokens (replace_file_content + Cero Verbosidad)
  Costo:  Tiering económico Flash para /ask y /build

  ===> AHORRO NETO DE TOKENS: ~91.8%
  ===> REDUCCIÓN DE COSTO API: ~95%
```

---

## 📄 Licencia
MIT License. Desarrollado por [datamaq-automation](https://github.com/datamaq-automation).

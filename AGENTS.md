# Antigravity (AGY) Global Directives: Local Resources, Token Optimization & SDD Gauntlet

## 0. Idioma Oficial y Cero Verbosidad (Zero-Token Waste)
- **Idioma Oficial:** Toda interacción, respuestas, documentación (`README.md`, `spec.md`, `CONVENTIONS.md`), docstrings, commits y tests deben redactarse **ESTRICTAMENTE EN ESPAÑOL**. Identificadores y palabras clave de código en inglés estándar.
- **Extrema Concisión:** Prohibido el relleno conversacional (*"Entendido"*, *"He actualizado el archivo..."*, *"Aquí está el código"*).
- **Cero Eco:** Nunca reimprimir código no modificado en el chat.
- **Reporte Quirúrgico:** Al finalizar una tarea, reportar estrictamente la lista de archivos modificados, estado de los linters/tests locales y siguientes pasos esenciales o bloqueos.

---

## 1. Modos Globales de Operación y Tiering de Modelos

Cuando el prompt del usuario comience o declare explícitamente un modo, el agente DEBE asumir estrictamente ese rol y sus restricciones de permisos:

### A. Modo `/ask` (Consultor Técnico y Auditor de Código)
- **Perfil Recomendado:** Modelo Económico (`flash_lite` / `flash`), Razonamiento: **Low / Mínimo**.
- **Propósito:** Responder consultas técnicas, explicar arquitectura y auditar cumplimiento de especificaciones y Clean Architecture.
- **Salida:** Respuestas ultra-concisas con citas exactas a rutas de archivo y números de línea (`[archivo.py#L10-L25]`).
- **Restricción Inmutable:** **MODO SOLO LECTURA.** PROHIBIDO crear o editar archivos. Si el usuario solicita cambios, RECHAZAR de inmediato e indicar cambiar a `/plan` o `/build`.

### B. Modo `/plan` (Arquitecto SDD & SSOT)
- **Perfil Recomendado:** Modelo Avanzado (`pro` / alta capacidad), Razonamiento: **High / Alto**.
- **Propósito:** Analizar requerimientos y redactar formalmente la especificación técnica (`spec.md` / `specs/<modulo>.md`) en 5 secciones modulares (SSOT) y los esqueletos de tests en `tests/`.
- **Restricción Inmutable:** EXCLUSIVAMENTE puede crear/modificar `spec.md`, `specs/**` y `tests/**`. **PROHIBIDO modificar código en `src/`**.

### C. Modo `/build` (Implementador Autónomo TDD & Gauntlet Runner)
- **Perfil Recomendado:** Modelo Intermedio (`flash` / balanceado), Razonamiento: **Medium / Low**.
- **Requisito Bloqueante:** Verificar la existencia de `spec.md` antes de tocar `src/`. Si no existe, RECHAZAR e indicar ejecutar `/plan`.
- **Flujo TDD:** **RED** (escribir test que falla según `spec.md`) ──► **GREEN** (código mínimo en `src/`) ──► **REFACTOR** (tipado estricto y superación del Gauntlet local).
- **Permisos:** Edición habilitada en `src/` y `tests/` con ediciones quirúrgicas.

---

## 2. Pre-Procesamiento Local y Poda de Contexto (CPU / $0 Tokens)
- **Cero Lecturas Indiscriminadas:** Prohibido usar `view_file` sobre archivos completos (>100 líneas) si solo se requieren firmas, contratos o interfaces.
- **Poda de AST Determinística:** Para inspeccionar módulos extensos o dependencias, usar los scripts locales de poda AST para reducir entre un 75% y 90% el consumo de tokens:
  - Python: `python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_python_ast.py <archivo.py>`
  - TypeScript/JS: `node /home/agustin/.agents/skills/token-optimizer/scripts/prune_ts_ast.js <archivo.ts>`
  - CLI nativo: `tokenix read <archivo>` o `tokenix symbols <simbolo>`
- **LSP y Búsqueda Quirúrgica:** Localizar símbolos con `grep_search` y consultar rangos específicos con `StartLine` y `EndLine`.

---

## 3. Post-Procesamiento Local y Self-Healing Determinístico
- **Linters y Formateadores Locales Primero:** Inmediatamente después de crear o editar código, ejecutar linters locales determinísticos en la CPU antes de devolver el control o consultar al LLM:
  - **Python:** `ruff check --fix <archivo> && ruff format <archivo>`
  - **TypeScript/JavaScript:** `npx eslint --fix <archivo>`
- **Eliminar Ping-Pong de API:** Resolver errores de sintaxis, imports no utilizados y formato localmente a $0 costo de tokens.

---

## 4. Convenciones de Arquitectura y El Guantelete de Restricciones (*Constraint Gauntlet*)

Rige la filosofía de Uncle Bob: rodear a los agentes de restricciones estáticas inmutables.

### A. Reglas de Capas (Clean Architecture Canónica)
```
[Infrastructure] ──► [Adapters] ──► [Application] ──► [Domain (Core)]
                    (Dirección INWARD ONLY - Hacia el Centro)
```
1. **`src/domain/`:** Cero dependencias externas. Solo `dataclasses` e interfaces/puertos abstractos `abc.ABC` (`ports.py`).
2. **`src/application/`:** Casos de uso orquestadores, mappers y DTOs (`pydantic` permitido **solo** aquí).
3. **`src/adapters/`:** Controladores y gateways que implementan puertos del dominio. **Nunca importan de `infrastructure/`**.
4. **`src/infrastructure/`:** Implementaciones tecnológicas (FastAPI routers, ORMs, DB clients, `settings/config.py`).

### B. Las 5 Baterías Inmutables del Guantelete
1. **`__init__.py` de 0 bytes:** El 100% de los `__init__.py` en `src/` y `tests/` deben tener exactamente 0 bytes (cero re-exportaciones o código oculto).
2. **Imports 100% Absolutos:** Prohibidos imports relativos (`from .` o `from ..`). Obligatorio `from src...` o `@/...`.
3. **Tipado Estricto al 100%:** Todas las funciones y métodos deben especificar Type Hints en parámetros y retorno. Prohibido `any` o tipos implícitos.
4. **Inmutabilidad de Reglas y Cero Evasión:** Prohibido relajar o silenciar tests y directivas de evasión (`# type: ignore`, `# noqa`, `cast(Any, ...)`, `@ts-ignore`, `@pytest.mark.skip`).
5. **Zero Secretos Quemados:** Detección y bloqueo estricto de contraseñas, tokens JWT o connection strings en código fuente.

---

## 5. Operaciones Quirúrgicas de Archivos
- **Preferencia por `replace_file_content`:** Usar reemplazos quirúrgicos con contexto mínimo (2 a 3 líneas antes y después). No sobrescribir archivos completos con `write_to_file` para cambios parciales.

# Guía de Uso: Caché Semántico en RAM y Poda Automática de AST

> **Tipo de Documento:** Diátaxis / How-To Guide  
> **Objetivo:** Explicar el funcionamiento, configuración y verificación del Caché Semántico en RAMDisk y el Interceptor de Poda AST en lecturas de código para Google Antigravity (AGY).

---

## 1. Caché Semántico en RAMDisk (`/dev/shm`)

El adaptador `SQLiteRAMSemanticCache` permite interceptar preguntas o tareas y resolverlas de forma local en menos de 2 ms consumiendo **$0 tokens de API**.

### Características:
* **Ubicación:** `/dev/shm/agy-cache/responses.db` (memoria RAM compartida a 15 GB/s).
* **PRAGMAs SQLite:** `WAL`, `synchronous = NORMAL`, `temp_store = MEMORY`, `mmap_size = 256MB`.
* **Motor SIMD:** Cálculo de similitud de cosenos vectorizada con `numpy` (instrucciones AVX2 de 256 bits).
* **Embeddings:** 768 dimensiones provistas localmente por `nomic-embed-text` en Ollama.

### Uso Programático:
```python
from src.adapters.semantic_cache import SQLiteRAMSemanticCache

cache = SQLiteRAMSemanticCache()

# 1. Guardar par consulta/respuesta
cache.set(
    "¿Cómo configurar el enrutador en cascada?",
    "Ejecuta agy-opt router & y configura OpenCode con agy-opt sync-opencode.",
)

# 2. Consultar con tolerancia semántica (umbral >= 0.92)
result = cache.get("¿Cómo inicio el router de modelos?")
if result.hit:
    print(f"Respuesta desde RAM: {result.response}")
    print(f"Tokens ahorrados: {result.tokens_saved} | Similitud: {result.similarity}")
```

---

## 2. Interceptor de Poda AST en Lecturas (`view_file`)

El hook `~/.agents/hooks/gate_ast_pruner_interceptor.py` actúa en `PreToolUse` para evitar que el agente cargue archivos masivos en la ventana de contexto.

### Comportamiento Automático:
1. Si un archivo de código productivo (`.py`, `.ts`, `.js`, `.go`, `.rs`) tiene **más de 100 líneas** y se invoca sin un rango específico (`StartLine`/`EndLine` <= 150):
   - El hook intercepta la operación e indica utilizar poda AST determinística o acotar el rango.
2. La poda AST con `PythonASTPruner` (`src/adapters/ast_pruner.py`):
   - Preserva clases, nombres de funciones, decoradores, firmas de tipos y docstrings.
   - Reemplaza el cuerpo de las funciones por `pass` o elipsis (`...`).
   - Logra una reducción promedio de **75% a 90% en tokens de entrada**.

### Ejecución Directa por CLI:
```bash
# Podar un archivo Python a costo $0
python3 skills/token-optimizer/scripts/prune_python_ast.py <archivo.py>

# O mediante Tokenix
tokenix read <archivo.py>
```

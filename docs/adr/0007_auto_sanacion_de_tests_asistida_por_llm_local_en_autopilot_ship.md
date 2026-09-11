# ADR-0007: Auto-Sanación de Tests Asistida por LLM Local en Autopilot Ship

* **Estado:** `Aceptado`
* **Fecha:** `2026-09-11`
* **Decisores:** `Equipo de Ingeniería / Antigravity AGY`
* **Gobernanza:** `Clean Architecture & Zero-Token Waste`

---

## 1. Contexto & Problema

El pipeline de entrega continua desatendida (`agy-ship` / `AutopilotShipOrchestrator`) resolvía a $0 tokens la generación de mensajes de commit convencionales mediante el SLM local `qwen2.5-coder:1.5b` alojado en Ollama (`localhost:11434`), y ejecutaba un bucle de reparación básica en CI limitado estrictamente a formato y estilo (`ruff check --fix` y `ruff format`).

Sin embargo, ante fallos en la lógica de negocio o aserciones de la suite de tests (tanto preventivamente en la máquina local antes de push como reactivamente tras la ejecución en runners remotos de GitHub Actions):

1. **Falta de Auto-Reparación de Lógica/Tests:**
   Los fallos de tests unitarios no podían ser resueltos por linters determinísticos estáticos, forzando la intervención humana o el consumo innecesario de tokens en APIs externas de modelos comerciales.

2. **Sobrecarga de Contexto en Tracebacks Crudos:**
   Los logs de CI (`gh run view --log-failed`) y terminal de `pytest` contienen cientos de líneas de ruido (timestamps RFC3339 de GitHub Actions, códigos de escape ANSI, cabeceras y resumen de entorno). Enviar estos volcados a un SLM local de 1.5B satura su ventana de atención y degrada la calidad de la inferencia.

3. **Riesgo de Regresiones sin Circuito Cerrado:**
   Cualquier intento de modificación de código asistido por un modelo de lenguaje local debe verificarse de manera determinística mediante re-ejecución inmediata de pruebas y revertirse automáticamente (`git restore .`) si el test persiste en fallo tras agotar los reintentos, preservando el *working tree* limpio.

---

## 2. Decisión de Arquitectura

Se adopta formalmente el subsistema desacoplado de auto-sanación de tests asistido por LLM local:

### A. Nuevos Contratos en Dominio (Clean Architecture / DIP)
En `src/domain/ports.py`, sin dependencias externas:
* `TestFailureDetail`: Dataclass inmutable que aísla el archivo de test, nombre de la función, componente objetivo en `src/`, número de línea del fallo, mensaje de error y un snippet podado del traceback (< 25 líneas).
* `TestHealResult`: Dataclass que reporta éxito/fracaso, archivo intervenido, código reparado, intentos consumidos y latencia.
* `ITestFailureHealer`: Puerto abstracto que formaliza `isolate_failure` y `heal_test_failure`.

### B. Adaptador `OllamaTestFailureHealer`
En `src/adapters/test_healer.py`:
1. **Traceback Pruning Determinístico:** Filtra secuencias ANSI, remueve timestamps de CI y extrae quirúrgicamente el frame del error en `src/` y la aserción fallida.
2. **Poda AST Selectiva (`_SelectiveBodyPruner`):** Si el componente afectado supera las 120 líneas, preserva íntegramente el cuerpo de la función donde ocurrió el fallo y esqueletiza las funciones restantes con firmas, tipos y `pass`. Esto reduce el prompt a menos de 1.000 tokens en la iGPU/CPU local.
3. **Validación Estricta y Auto-Formato:** Valida el código resultante con `ast.parse`, ejecuta `ruff check/format` local y re-evalúa `pytest -q <test_file>`.
4. **Reversión Determinística:** Si tras 2 intentos el test no pasa, restaura el archivo original sin dejar residuos en el repositorio.

### C. Integración en `AutopilotShipOrchestrator`
En `src/adapters/ship_orchestrator.py`:
* **Shift-Left Preventivo (Local):** Antes de commit y push, ejecuta `pytest -q`. Si falla, invoca `test_healer`. Si no se repara, descarta cambios con `git restore .` y aborta inmediatamente, impidiendo la publicación de código roto.
* **Reactivo en CI:** Si GitHub Actions reporta fallo, lee el log con `gh run view --log-failed`. Si es fallo de tests, repara el componente con Ollama local, valida con pytest local, genera el commit `fix(test-heal): auto-reparar fallo en <componente> mediante LLM local` y reintenta `git push origin <branch>`.

---

## 3. Consecuencias & Trade-offs

* **Impacto Positivo:**
  - **Entrega 100% Autónoma y Resiliente:** Los errores comunes y regresiones menores se auto-corrigen y re-despliegan automáticamente a $0 costo de API.
  - **Zero-Token Waste:** Todo el diagnóstico y reparación corre en hardware local en menos de 3 segundos por intento.
  - **Inviolabilidad de Estado:** El repositorio nunca queda sucio ante fallos insolubles gracias a la reversión automática con `git restore .`.
* **Impacto Negativo / Restricciones:**
  - Limitado a la capacidad de razonamiento de modelos pequeños (1.5B). Problemas que requieran refactorizaciones multidominio o cambios de contratos abstractos continuarán requiriendo intervención humana o modelos de mayor tamaño (7B/14B con dGPU o subagentes en `/plan`).

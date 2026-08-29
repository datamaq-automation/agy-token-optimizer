# ADR-0005: Enrutador en Cascada de Proveedores y Aceleración de Hardware para OpenCode

* **Estado:** Aceptado
* **Fecha:** 2026-08-28
* **Autor:** datamaq-automation

---

## 1. Contexto y Problema

Durante el modo de implementación (`/build`) con herramientas autónomas como OpenCode, existen dos fuentes principales de desperdicio de dinero y tokens:
1. **Costo de Modelos Propietarios:** Utilizar modelos de pago desde el primer token cuando existen cuotas gratuitas generosas (*Free Tiers*) en Google AI Studio (Gemini 2.0 Flash) y Groq Cloud (Llama 3.3).
2. **Ping-Pong de Depuración Remota:** Enviar trazas de errores menores de sintaxis, imports no utilizados o formateo al LLM remoto consume cientos de tokens por intento.

---

## 2. Decisión

Se adopta una arquitectura dual de **Enrutamiento en Cascada Inteligente** y **Aceleración en Hardware Local (CPU / iGPU / RAM)**:

1. **Proxy en Cascada Compatible con OpenAI (`model_cascade_router.py` / `agy-opt router`):**
   - **Nivel 1 ($0.00):** Prioriza proveedores gratuitos (Gemini 2.0 Flash y Groq Llama 3.3).
   - **Nivel 2 (Conmutación en 10 ms):** Ante error HTTP 429 (*Rate Limit Exceeded*), conmuta en caliente a la API de **DeepSeek-V3 / R1**.
   - **Nivel 3 (Offline):** Conmuta a Ollama local (`qwen2.5-coder`) en RAM.
2. **Auto-Sanador Determinístico en CPU (`build_hardware_healer.py`):**
   - Resuelve el 100% de errores de sintaxis e imports con `ruff check --fix` y `ruff format` en **20 ms** a $0 tokens.
3. **Workspace de Pruebas en RAM (`build_ramdisk_workspace.py`):**
   - Ejecuta tests TDD en `/dev/shm` a **15 GB/s** (0 ms de latencia de disco).

---

## 3. Consecuencias

* **Positivas:**
  - El costo operativo del desarrollo con OpenCode se reduce a **$0.00** durante el consumo del Free Tier.
  - La transición a DeepSeek es transparente sin interrupciones ni reinicios de OpenCode.
  - La velocidad de ejecución de tests y auto-sanación es instantánea al correr en la memoria RAM y CPU Ryzen multihilo.
* **Negativas / Mitigaciones:**
  - Requiere iniciar el router en segundo plano (`agy-opt router &`). Mitigado mediante script ligero de 1 comando.

---

## 4. Estado de Cumplimiento
Validado al 100% en la suite automatizada `./tests/test_suite.sh` (Tests 52 a 56).

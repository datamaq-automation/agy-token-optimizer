# Guía Práctica: Flujo de Trabajo en 1 Sola Terminal con AGY y OpenCode

Esta guía explica cómo operar el ciclo completo de desarrollo de software utilizando **Google Antigravity (AGY)** para la arquitectura en modo `/plan` y **OpenCode Interpreter / CLI** para la implementación en modo `/build`, aprovechando la **cascada de tokens gratuitos**, el fallback a **DeepSeek API** y la **aceleración en hardware local (CPU/iGPU/RAM)**.

---

## 1. Configuración Inicial (Solo 1 Vez)

Antes de iniciar tu primer flujo de trabajo, configura OpenCode para que apunte al enrutador en cascada local de AGY:

```bash
# 1. Configurar OpenCode hacia http://127.0.0.1:8080/v1
agy-opt sync-opencode

# 2. (Opcional) Configurar tus API keys en ~/.agy-optimizer/.env:
# GEMINI_API_KEY="tu_clave_de_google_ai_studio"
# GROQ_API_KEY="tu_clave_de_groq"
# DEEPSEEK_API_KEY="tu_clave_de_deepseek"
```

---

## 2. El Flujo Diario en 1 Sola Terminal

No necesitas tener múltiples terminales abiertas. El enrutador corre en segundo plano en silencio:

```bash
# Paso 1: Iniciar el enrutador proxy en segundo plano
agy-opt router &

# Paso 2: Iniciar AGY para diseñar la arquitectura
agy
```

### Dentro de AGY (Fase de Planificación):
1. Escribe tu requerimiento en modo plan:  
   `/plan Implementar sistema de autenticación JWT con repositorio en memoria`
2. AGY pre-compila el contexto de tu código en **40 ms** en CPU (`agy-opt preplan`).
3. AGY genera el artefacto del plan (`spec.md`) con las 5 secciones SSOT.
4. Exporta el plan a la raíz de tu proyecto:
   ```bash
   agy-opt export-plan spec.md .
   ```
5. Cierra o sal de AGY (`exit` o `Ctrl+C`).

> **💡 Consejo de Cuota:** La cuota gratuita de AGY se renueva **semanalmente** (o cada 5 horas con planes AI Pro / descuento de estudiantes). Al usar AGY solo para planificar y delegar la construcción masiva a OpenCode + Cascada Gratuita, tu cuota de AGY rinde toda la semana sin agotarse.

---

## 3. Fase de Construcción con OpenCode (`/build`)

En la misma terminal, inicia OpenCode:

```bash
opencode
```

1. Indícale a OpenCode que ejecute el plan:  
   `/build Implementa las tareas definidas en spec.md siguiendo el ciclo TDD`
2. **Consumo Inteligente de Tokens:**
   - OpenCode consultará `http://127.0.0.1:8080/v1`.
   - El router usará primero tu **Free Tier de Gemini 2.0 Flash / Groq (Costo: $0.00)**.
   - Si se agota la cuota (HTTP 429), conmuta en **10 ms** a **DeepSeek-V3 API** sin interrumpir la ejecución.
3. **Aceleración de Hardware en tu Máquina:**
   - Las pruebas y compilación corren en `/dev/shm` a **15 GB/s**.
   - Los errores menores de sintaxis o imports son reparados en **20 ms** en CPU con `agy-opt build-heal` sin consultar al LLM remoto.

---

## 4. Validación Final y Cierre

Una vez que OpenCode termine la implementación:

```bash
# Validar el Guantelete de Uncle Bob y suite de pruebas en ~1.5s
agy-opt ci .

# Generar mensaje de commit y resumen de PR con SLM local
agy-opt commit
```

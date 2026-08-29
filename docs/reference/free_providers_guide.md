# Guía de Proveedores Gratuitos (Free Tiers), Cuotas de AGY, Multi-Key Pool y Respaldo

Esta guía detalla los mejores proveedores de LLMs con **capas 100% gratuitas (*Free Tiers*)** para programación y desarrollo autónomo, el funcionamiento de las **cuotas de Google Antigravity (AGY)**, cómo configurar el **Pool Multi-Key con rotación automática (múltiples cuentas de Google y Groq)** y cómo configurar `~/.agy-optimizer/.env`.

---

## 1. Tabla Comparativa de Proveedores Gratuitos

| Proveedor | Modelos Destacados | Límites Gratuitos (*Free Tier*) | Velocidad | Dónde Obtener la API Key |
| :--- | :--- | :--- | :--- | :--- |
| **1. Google AI Studio** *(Recomendado)* | `gemini-2.0-flash`, `gemini-1.5-pro` | **1.500 peticiones/día** por cuenta<br>15 RPM / 1M tokens/min | ~120 tok/s | [aistudio.google.com](https://aistudio.google.com/) |
| **2. Groq Cloud** *(Recomendado)* | `llama-3.3-70b-versatile`, `qwen-2.5-coder-32b` | **14.400 peticiones/día** por cuenta<br>30 RPM / 6.000 tok/min | **~500 tok/s** (LPU) | [console.groq.com](https://console.groq.com/) |
| **3. OpenRouter (Free Models)** | `deepseek/deepseek-r1:free`, `meta-llama/llama-3.3-70b:free` | Acceso a múltiples modelos etiquetados como `:free` | Variable | [openrouter.ai](https://openrouter.ai/) |
| **4. Mistral AI** | `codestral-latest`, `mistral-small` | Free tier para desarrolladores especializado en código | ~100 tok/s | [console.mistral.ai](https://console.mistral.ai/) |
| **5. Cerebras Inference** | `llama-3.3-70b` | Free tier con velocidad extrema por hardware de oblea | **>1.800 tok/s** | [cloud.cerebras.ai](https://cloud.cerebras.ai/) |

---

## 2. Pool Multi-Key: Multiplicación de Cuota Gratuita ($0.00)

Si dispones de múltiples cuentas de Google o Groq, puedes configurar un **Pool de Claves** separadas por comas. El enrutador (`agy-opt router`) gestionará automáticamente el balanceo de carga y la conmutación en caliente en **0 ms** ante errores HTTP 429:

* **3 Cuentas de Google:** **4.500 peticiones diarias gratuitas** con Gemini 2.0 Flash.
* **5 Cuentas de Google:** **7.500 peticiones diarias gratuitas**.
* **2 Cuentas de Groq:** **28.800 peticiones diarias gratuitas** a 500 tok/s.

---

## 3. Google Antigravity (AGY): Cuotas y Descuento para Estudiantes

* **Cuota Base Gratuita (Baseline Free Tier):**
  - Cualquier usuario con cuenta de Google tiene acceso gratuito con **renovación semanal**.
* **Planes de Alto Rendimiento (Google AI Pro / AI Ultra):**
  - Cuotas generosas que se restablecen en **ciclos dinámicos de 5 horas**.
* **🎓 Descuento y Beneficios para Estudiantes:**
  - Google ofrece promociones educativas a precio reducido vía [gemini.google/students](https://gemini.google/students/) con correo `.edu` o SheerID.
* **💡 Estrategia Óptima:**
  - Usa AGY exclusivamente para `/plan` y `/ask` (preservando tu cuota semanal).
  - Delega la construcción pesada a OpenCode en modo `/build` con el pool gratuito de Gemini/Groq y hardware local.

---

## 4. Configuración Canónica del Archivo `~/.agy-optimizer/.env`

```ini
# ====================================================================
# ⚡ AGY & OPENCODE MODEL CASCADE & MULTI-KEY POOL CREDENTIALS
# ====================================================================

# Nivel 1: Pool de Múltiples Cuentas Gratuitas de Google Gemini ($0.00)
# (Puedes separar N claves por comas o saltos de línea)
GEMINI_API_KEYS="AIzaSy_CuentaGoogle1...,AIzaSy_CuentaGoogle2...,AIzaSy_CuentaGoogle3..."

# Nivel 2: Pool de Múltiples Cuentas Gratuitas de Groq Cloud ($0.00)
GROQ_API_KEYS="gsk_CuentaGroq1...,gsk_CuentaGroq2..."

# Nivel 3: Proveedor de Pago de Respaldo (DeepSeek con 90% Descuento KV-Cache)
DEEPSEEK_API_KEYS="sk-tu_clave_deepseek_aqui"

# Nivel 4: Inferencia Local Offline (Ollama en RAM)
OLLAMA_HOST="http://localhost:11434"
```

---

## 5. Diagrama de Conmutación Multi-Key

```
                      [Petición de OpenCode /build]
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 1. Intenta Gemini [Cuenta #1] ($0.00)                    │
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿HTTP 429?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 2. Salta a Gemini [Cuenta #2] ➔ [Cuenta #N] ($0.00)       │
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿Todas las de Gemini Agotadas?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 3. Salta a Groq [Cuenta #1] ➔ [Cuenta #N] ($0.00)         │
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿Todas las de Groq Agotadas?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 4. Conmuta a DeepSeek V3 (Pago con 90% Descuento KV-Cache)│
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿Sin Internet / Falla?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 5. Fallback Local Offline (Ollama en RAM qwen2.5-coder)  │
       └──────────────────────────────────────────────────────────┘
```

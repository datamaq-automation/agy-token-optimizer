# Guía de Proveedores Gratuitos (Free Tiers), Cuotas de AGY, Multi-Key Pool y Respaldo

Esta guía detalla los mejores proveedores de LLMs con **capas 100% gratuitas (*Free Tiers*)** para programación y desarrollo autónomo, el funcionamiento de las **cuotas de Google Antigravity (AGY)**, cómo configurar el **Pool Multi-Key con rotación automática (múltiples cuentas de Google y Groq)**, los pasos exactos para obtener cada API Key y cómo configurar `~/.agy-optimizer/.env`.

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

## 2. Pasos Exactos para Obtener Cada API Key (Paso a Paso)

### 🔹 A. Google AI Studio (Gemini 2.0 Flash - 1.500 req/día gratis)
1. Ingresa a [aistudio.google.com](https://aistudio.google.com/) con tu cuenta de Google.
2. En la barra lateral izquierda, haz clic en **"Get API key"** (ícono de llave).
3. Haz clic en el botón azul **"Create API key"**.
4. Selecciona **"Create API key in new project"** (o elige un proyecto de Google Cloud existente).
5. Copia la clave generada (comienza con `AIzaSy...`).
6. **Para obtener más claves (Multi-Key):** Abre una ventana de incógnito o cambia de cuenta de Google arriba a la derecha y repite los pasos para tu segunda o tercera cuenta.

---

### 🔹 B. Groq Cloud (Llama 3.3 70B a 500 tok/s - 14.400 req/día gratis)
1. Ingresa a [console.groq.com](https://console.groq.com/).
2. Inicia sesión con tu cuenta de Google o GitHub.
3. En el menú lateral izquierdo, haz clic en **"API Keys"**.
4. Haz clic en el botón **"Create API Key"**.
5. Asigna un nombre (por ejemplo: `opencode-key-1`) y haz clic en **"Submit"**.
6. Copia la clave generada (comienza con `gsk_...`). *(Guárdala de inmediato, no se volverá a mostrar completa)*.
7. **Para Multi-Key:** Puedes crear claves con diferentes cuentas de correo para multiplicar tus cuotas.

---

### 🔹 C. DeepSeek API (Respaldo de Pago con 90% de Descuento KV-Cache)
1. Ingresa a [platform.deepseek.com](https://platform.deepseek.com/).
2. Inicia sesión o regístrate con tu correo.
3. En el menú lateral izquierdo, haz clic en **"API Keys"**.
4. Haz clic en **"Create new API key"**, asigna un nombre y copia la clave generada (`sk-...`).
5. En la sección **"Top up"**, puedes cargar un saldo mínimo ($2 a $5 USD) que durará meses gracias al descuento por KV-Cache y el filtro de hardware local.

---

## 3. Pool Multi-Key: Multiplicación de Cuota Gratuita ($0.00)

Si dispones de múltiples cuentas de Google o Groq, configúralas separadas por comas en tu archivo `.env`. El enrutador (`agy-opt router`) gestionará el balanceo y la conmutación automática en **0 ms** ante errores HTTP 429:

* **3 Cuentas de Google:** **4.500 peticiones diarias gratuitas** con Gemini 2.0 Flash.
* **5 Cuentas de Google:** **7.500 peticiones diarias gratuitas**.
* **2 Cuentas de Groq:** **28.800 peticiones diarias gratuitas** a 500 tok/s.

---

## 4. Google Antigravity (AGY): Cuotas y Descuento para Estudiantes

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

## 5. Configuración Canónica del Archivo `~/.agy-optimizer/.env`

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

## 6. Diagrama de Conmutación Multi-Key

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

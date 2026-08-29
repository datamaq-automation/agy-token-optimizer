# Guía de Proveedores Gratuitos (Free Tiers) y APIs de Respaldo para AGY & OpenCode

Esta guía detalla los mejores proveedores de LLMs con **capas 100% gratuitas (*Free Tiers*)** para programación y desarrollo autónomo, cómo obtener sus claves de API y cómo configurar la cascada inteligente en `~/.agy-optimizer/.env`.

---

## 1. Tabla Comparativa de Proveedores Gratuitos

| Proveedor | Modelos Destacados | Límites Gratuitos (*Free Tier*) | Velocidad | Dónde Obtener la API Key |
| :--- | :--- | :--- | :--- | :--- |
| **1. Google AI Studio** *(Recomendado)* | `gemini-2.0-flash`, `gemini-1.5-pro` | **1.500 peticiones/día**<br>15 RPM / 1M tokens/min | ~120 tok/s | [aistudio.google.com](https://aistudio.google.com/) |
| **2. Groq Cloud** *(Recomendado)* | `llama-3.3-70b-versatile`, `qwen-2.5-coder-32b` | **14.400 peticiones/día**<br>30 RPM / 6.000 tok/min | **~500 tok/s** (LPU) | [console.groq.com](https://console.groq.com/) |
| **3. OpenRouter (Free Models)** | `deepseek/deepseek-r1:free`, `meta-llama/llama-3.3-70b:free` | Acceso a múltiples modelos etiquetados como `:free` | Variable | [openrouter.ai](https://openrouter.ai/) |
| **4. Mistral AI** | `codestral-latest`, `mistral-small` | Free tier para desarrolladores especializado en código | ~100 tok/s | [console.mistral.ai](https://console.mistral.ai/) |
| **5. Cerebras Inference** | `llama-3.3-70b` | Free tier con velocidad extrema por hardware de oblea | **>1.800 tok/s** | [cloud.cerebras.ai](https://cloud.cerebras.ai/) |

---

## 2. Proveedor de Respaldo de Pago Ultra-Económico

Cuando se agotan las cuotas gratuitas diarias de Gemini o Groq (error HTTP 429), el router conmuta en **10 milisegundos** a:

| Proveedor | Modelos | Costo con KV-Cache Hit (90% Descuento) | Propósito |
| :--- | :--- | :--- | :--- |
| **DeepSeek API** | `deepseek-chat` (V3)<br>`deepseek-reasoner` (R1) | **~$0.028 por 1 Millón de tokens** (Entrada con caché)<br>~$0.28 por 1 Millón de tokens (Salida) | Respaldo de máxima capacidad a costo prácticamente nulo |

---

## 3. Configuración Canónica del Archivo `.env`

El enrutador (`agy-opt router`) lee automáticamente las credenciales desde `~/.agy-optimizer/.env` o desde las variables de entorno de tu shell:

```bash
mkdir -p ~/.agy-optimizer
```

Contenido del archivo `~/.agy-optimizer/.env`:

```ini
# ====================================================================
# ⚡ AGY & OPENCODE MODEL CASCADE CREDENTIALS
# ====================================================================

# Nivel 1: Proveedores 100% Gratuitos ($0.00 Costo)
GEMINI_API_KEY="AIzaSy..."               # De: https://aistudio.google.com/
GROQ_API_KEY="gsk_..."                   # De: https://console.groq.com/

# Nivel 2: Proveedor de Pago de Respaldo (Ultra-Económico)
DEEPSEEK_API_KEY="sk-..."                # De: https://platform.deepseek.com/

# Nivel 3: Inferencia Local (Opcional - Ollama ya corre por defecto en RAM)
OLLAMA_HOST="http://localhost:11434"
```

---

## 4. Cómo Opera la Cascada Automática

```
                      [Petición de OpenCode /build]
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 1. Intenta Gemini 2.0 Flash ($0.00)                      │
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿HTTP 429 o Sin Clave?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 2. Conmuta a Groq Llama 3.3 70B ($0.00 a 500 tok/s)      │
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿HTTP 429 o Sin Clave?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 3. Conmuta a DeepSeek V3 (Pago con 90% Descuento KV-Cache)│
       └────────────────────────────┬─────────────────────────────┘
                                    │ ¿Sin Internet / Error?
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │ 4. Fallback Local Offline (Ollama en RAM qwen2.5-coder)  │
       └──────────────────────────────────────────────────────────┘
```

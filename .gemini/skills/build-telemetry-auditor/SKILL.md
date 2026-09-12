---
name: build-telemetry-auditor
description: Auditor y optimizador adaptativo de telemetría de construcción en hardware local (iGPU Vulkan). Inspecciona logs estructurados, correlaciones de trazas (trace_id) y aplica auto-remediación en el bucle cerrado TDD.
---

# Build Telemetry Auditor & Adaptive Optimizer (Local Workspace Skill)

Esta habilidad reside **exclusivamente dentro de este repositorio** (ámbito de workspace en `.gemini/skills/`) y tiene como objetivo auditar de forma continua la telemetría generada durante la construcción de código en hardware local, correlacionar eventos mediante `trace_id`, y ejecutar bucles de auto-remediación o ajuste de parámetros para maximizar el throughput y evitar desperdicio de tokens.

---

## 1. Alcance y Filosofía Operativa

* **$0 Tokens en la API Externa:** Todas las inspecciones, correlaciones y diagnósticos se ejecutan localmente en la CPU Ryzen y la iGPU Vulkan.
* **Correlación de Trazas (`trace_id`):** Permite vincular la generación de código con su linter previo, la poda de salida de pytest y el commit final.
* **Auto-Remediación Dinámica:**
  - Si el rendimiento de inferencia cae por debajo de 10 tok/s, ejecuta diagnóstico de contención de VRAM.
  - Si una construcción falla repetidamente con el modelo 1.5B, conmuta dinámicamente a 7B.

---

## 2. Invocación y Comandos

### A. Auditoría Rápida de Métricas
Para obtener un reporte cuantitativo de las construcciones recientes, throughput de la iGPU y correlación de trazas:

```bash
python3 .gemini/skills/build-telemetry-auditor/scripts/audit_telemetry.py --limit 50
```

### B. Salida Estructurada JSON
Para procesar programáticamente las trazas y alimentar decisiones del agente:

```bash
python3 .gemini/skills/build-telemetry-auditor/scripts/audit_telemetry.py --limit 100 --json
```

---

## 3. Fuentes de Datos Ingestadas

| Fuente | Tipo de Datos | Propósito |
|---|---|---|
| `~/.agents/token_savings.log` | JSON Lines | Eventos tipados con `trace_id`, `tokens_saved`, `latency_ms` y `hardware_target`. |
| `~/.agents/gate_audit.log` | Log estructurado | Decisiones del guardián del navegador (`allow`, `deny`, `overwrite`). |
| `~/.agents/cache/metrics.db` | SQLite | Agregados históricos y estimación de costos en USD ahorrados. |

---

## 4. Reglas Heurísticas de Auto-Remediación

1. **Regla de Contención de VRAM (iGPU Degenerada a CPU):**
   - *Condición:* `tok_per_sec < 10.0` y `hardware_target == "Vulkan"`.
   - *Acción:* Ejecutar `agy-opt igpu-tune` para verificar si Ollama descargó capas a RAM del sistema por falta de memoria gráfica contigua.

2. **Regla de Complejidad de Código (Fallback 1.5B ➔ 7B):**
   - *Condición:* `iterations >= 3` tras auto-sanación con `qwen2.5-coder:1.5b`.
   - *Acción:* Relanzar la construcción especificando `--model qwen2.5-coder:7b`.

3. **Regla de Poda de Ruido Terminal:**
   - *Condición:* Un comando `pytest` emite más de 100 líneas sin podar.
   - *Acción:* Asegurar que el interceptor `gate_diff_compressor_interceptor.py` capture la salida a través de `ITerminalPruner`.

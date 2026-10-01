# ADR-0008: Política de Arbitraje Económico y Temporal (Google Flat-Rate vs DeepSeek Off-Peak)

* **Estado:** `Aceptado`
* **Fecha:** `2026-10-01`
* **Decisores:** `Equipo DataMaq & Antigravity Tooling`

---

## 1. Contexto & Problema

El ecosistema Antigravity (AGY) y sus agentes de software requieren inferencia de modelos de lenguaje con alta capacidad de razonamiento para planificar arquitecturas, auditar Clean Architecture y generar tests TDD.

Se identifican tres realidades financieras y operativas:
1. **Tarifa Plana de Google ($5 USD/mes):** Se cuenta con un plan anual bonificado (de $20 a $5 USD mensuales) que otorga acceso a modelos Gemini Pro y Flash con cuotas renovables cada 5 horas / semanales. Dentro de esta cuota, el costo marginal por token es estrictamente **$0 USD**.
2. **Costo Elevado de Pay-As-You-Go en Google Cloud:** Al agotarse la cuota bonificada, la facturación directa por API en Vertex AI o Google AI Studio resulta costosa ($1.25 a $2.50 / 1M tokens de entrada; $5.00 a $10.00 / 1M tokens de salida).
3. **Ventana Horaria Off-Peak de DeepSeek API (50% OFF):** La API oficial de DeepSeek aplica un 50% de descuento en horario valle (00:30 a 08:30 UTC+8). En Argentina (UTC-3), esta ventana coincide con la tarde/noche (**13:30 a 21:30/22:00 hs**), ofreciendo tarifas de **$0.07 / 1M tokens de entrada** (con KV-cache hit) y **$1.10 / 1M tokens de salida** en modelos de 671B parámetros (DeepSeek V3 y DeepSeek R1).

---

## 2. Decisión de Arquitectura

Se adopta una **Política de Arbitraje Económico y Temporal en 3 Niveles (Tiers)**:

### Tier 1: Google First (Costo Marginal $0)
- **Condición:** Cuota periódica de Google activa y con remanente suficiente (>5%-10%).
- **Comportamiento:** 100% de las sesiones interactivas, modo `/build` y subagentes `/plan` operan sobre Gemini Flash / Pro en la interfaz web de Antigravity.
- **Razón:** Toda cuota no consumida antes de la ventana de reinicio se pierde; no tiene sentido pagar APIs externas si hay cuota plana disponible.

### Tier 2: DeepSeek Off-Peak Estratégico (13:30 - 22:00 hs Argentina)
- **Condición:** Tareas masivas de razonamiento (auditorías completas de repo, matrices de tests de 20 archivos, o síntesis densa de specs) durante la tarde de Argentina.
- **Comportamiento:** Se delega la tarea pesada a DeepSeek R1 / V3 vía scripts locales o subagentes sidecar.
- **Razón:** Protege la cuota semanal de Google de consumos abruptos y aprovecha el costo de $0.07 / 1M tokens con KV-cache.

### Tier 3: Desborde por Agotamiento de Cuota (Bridge de Continuidad)
- **Condición:** Cuota de Google cercana al agotamiento (<3%-5%) faltando tiempo para el reseteo periódico (ej. ~1 hora restante).
- **Comportamiento:** Desvío automático o manual de tareas hacia DeepSeek V3/R1.
- **Razón:** Evita la parálisis del desarrollador por *rate limit* temporal y previene caídas en facturaciones on-demand costosas de Google Cloud.

---

## 3. Consecuencias & Trade-offs

* **Impacto Positivo:**
  - **Ahorro Máximo:** Costo variable cercano a $0 USD aprovechando la cuota plana de $5/mes y la ventana bonificada de DeepSeek.
  - **Continuidad Operativa:** El desarrollador nunca queda bloqueado esperando la renovación de cuota de 5 horas.
  - **Razonamiento de Doctorado a Bajo Costo:** DeepSeek R1 disponible por fracciones de centavo para arquitecturas complejas.
* **Impacto Negativo / Restricciones:**
  - Requiere que el desarrollador o los scripts conozcan el estado de su cuota y la hora local para decidir el desvío óptimo.

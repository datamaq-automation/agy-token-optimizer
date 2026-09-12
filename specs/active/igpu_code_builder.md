# Spec: Generación y Construcción de Código en Hardware Local (iGPU Vulkan) con Planificación en API de Google

> **Estado:** Aprobado — En implementación TDD  
> **Fecha:** 2026-09-12  
> **Objetivo:** Desacoplar el rol de planificación (API Google / Razonamiento Pro) del rol de implementación de código (Hardware Local: CPU Ryzen + iGPU AMD Radeon Vega 11 Vulkan vía Ollama), minimizando el consumo de tokens de salida a $0 y logrando un ciclo TDD completamente autónomo en máquina local.

---

## 1. Requisitos del Sistema y Arquitectura

```
┌────────────────────────────────────────────────────────────────────────┐
│               1. CAPA REMOTA: PLANIFICACIÓN & DISEÑO                  │
│                      (Google API - Gemini Pro)                         │
│  • Análisis de requerimientos complejos y orquestación arquitectónica  │
│  • Redacción formal de especificaciones SDD (`spec.md`)                │
│  • Definición estricta de contratos / puertos (`src/domain/ports.py`)  │
│  • Creación de esqueletos de pruebas unitarias TDD (`tests/test_*.py`) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Contratos + Specs + Tests
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            2. CAPA LOCAL: CONSTRUCCIÓN Y GENERACIÓN EN iGPU            │
│       (Hardware Local: AMD Vega 11 Vulkan + CPU Ryzen + RAMDisk)        │
│  • Invocación a Ollama local (`qwen2.5-coder:7b` o `1.5b`) en iGPU     │
│  • Generación de código fuente a partir de prompt podado (<800 tokens) │
│  • Ejecución desatendida en segundo plano (tolerante a latencia local) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Código en borrador
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│         3. BUCLE LOCAL DETERMINÍSTICO DE SANACIÓN Y VALIDACIÓN         │
│                        (CPU Ryzen / $0 Tokens)                         │
│  • Formateo y linter estricto: `ruff check --fix` + `ruff format`      │
│  • Auto-sanación de sintaxis en iGPU (`slm_healer.py`)                 │
│  • Ejecución de tests locales: `pytest -q`                             │
│  • Auto-reparación de fallos de test en iGPU (`test_healer.py`)        │
│  • Integración en `src/` y commit semántico local (`autopilot_ship.py`)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Contratos e Interfaces (`src/domain/ports.py`)

- `CodeBuildResult`: Dataclass con `code: str`, `model_used: str`, `raw_tokens: int`, `success: bool`, `error_message: Optional[str]`.
- `ILocalCodeBuilder`: Puerto abstracto con método `build_implementation(spec_summary, contract_signatures, test_content, target_file_path, model_name) -> CodeBuildResult`.

---

## 3. Adaptador iGPU Vulkan (`src/adapters/igpu_builder.py`)

- `OllamaVulkanCodeBuilder`:
  - Consume endpoint `http://localhost:11434/api/generate`.
  - Configuración por defecto: `qwen2.5-coder:7b` con fallback a `qwen2.5-coder:1.5b`.
  - Sanitización estricta de markdown fences (extrae bloque de código puro).
  - Manejo de timeout y errores de conexión.

---

## 4. Pipeline de Bucle Cerrado Local (`src/application/local_build_pipeline.py`)

1. Cargar contratos podados y test unitario.
2. Solicitar borrador a `ILocalCodeBuilder` (Ollama en iGPU).
3. Guardar borrador en `/dev/shm/agy_drafts/`.
4. Ejecutar linter L1 (`ruff check --fix` y `ruff format`).
5. Si persisten errores de sintaxis, invocar `ISLMHealer` (L2).
6. Ejecutar tests con `pytest -q` (L3).
7. Si fallan tests, invocar `ITestFailureHealer` (L4).
8. Al superar el ciclo en verde, copiar a destino final en `src/`.

---

## 5. Comando CLI en `agy-opt`

- `agy-opt build-local <test_file> <target_file> [--model MODEL]`

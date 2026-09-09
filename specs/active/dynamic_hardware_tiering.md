# SRS-SPECS: Detección Adaptativa de Hardware y Política Navegador-First

> **Documento:** `specs/active/dynamic_hardware_tiering.md`  
> **Versión:** `1.0.0`  
> **Estado:** `Especificación Consolidada (Dudas = 0)`  
> **Fecha:** `2026-09-08`  
> **Autor(es):** `Antigravity SDD Architect`  
> **Repositorio:** `agy-token-optimizer`

---

## 1. Contexto Estratégico & Propuesta de Valor

### 1.1. Propósito
Garantizar que el ecosistema `agy-token-optimizer` opere de forma transparente tanto en máquinas de alto rendimiento (PC de Escritorio con AMD Ryzen 8 núcleos, 18 GiB RAM, AVX2 e iGPU Vulkan) como en dispositivos de recursos restringidos (Laptop con Intel Celeron N4000 2 núcleos, 1.8 GiB RAM, sin AVX2 y con `earlyoom` activo). Además, consolida la política **Navegador First** donde la sesión madre en [antigravity.google.com](https://antigravity.google.com) corre en modelo económico (`Gemini Flash` / `Low` reasoning) y delega tareas densas de arquitectura a subagentes efímeros `pro`, ejecutando la totalidad de hooks determinísticos en la máquina local.

### 1.2. Pilares de la Solución
| Pilar | Componente | Comportamiento Adaptativo |
| :--- | :--- | :--- |
| **Dominio & Entidades** | `src/domain/ports.py` | Dataclass inmutable `HardwareSpecs`, enum `HardwareTier` e interfaz `IHardwareAuditor`. |
| **Adaptador Determinístico** | `src/adapters/hardware_tier_detector.py` | Auditoría de `/proc/cpuinfo`, `/proc/meminfo`, `/dev/shm` y Vulkan sin dependencias externas pesadas. |
| **Gobernanza de Workspaces** | `src/adapters/ramdisk_optimizer.py` | Inhibición automática de RAMDisk en `/dev/shm` si `available_ram_mb < 1500` o `total_ram_gb < 4.0`. |
| **Auto-Sanación & Inferencia** | `skills/token-optimizer/scripts/` | Ruff en CPU para ambas máquinas. Si persiste error en Laptop: delegar al Free Tier cloud en vez de invocar Ollama local. |
| **Paralelismo Seguro** | Scripts y Tests | `max_workers = min(2, cpu_threads)` en Tier Constrained; `cpu_threads` en Tier Full Local. |

---

## 2. Certezas vs Dudas

### 2.1. Certezas Verificadas en Hardware
1. **Laptop (`agustin@debian`):**
   - CPU: Intel Celeron N4000 (2 núcleos, 2 hilos @ 1.10 GHz).
   - Flags: `sse4_2` presente. **AVX y AVX2 ausentes.**
   - RAM: 1.8 GiB total (~400 MiB disponibles, 670 MiB de swap en uso).
   - Proceso vigilante `earlyoom` activo: mata procesos si la RAM baja del 8%. Cargar un modelo SLM local en Ollama (`qwen2.5-coder:1.5b` o `nomic-embed-text`) activará OOM killer o congelará la máquina.
2. **Desktop (Target Original):**
   - CPU: AMD Ryzen (8 hilos, soporte AVX2 SIMD 256-bit).
   - RAM: 18 GiB libre.
   - iGPU Radeon Vega 11 con Vulkan.
3. **Navegador First:**
   - El daemon `antigravity-cli-daemon.service` ya está activo en la laptop.
   - Las herramientas `PreToolUse` y `PostToolUse` se ejecutan localmente en la laptop aunque la sesión madre esté en la web.

### 2.2. Dudas Resueltas
- *¿Debe Ollama instalarse en la laptop?* **No.** En la laptop, el enrutador en cascada (`model_cascade_router.py`) utiliza los Free Tiers de Gemini 2.0 Flash y Groq en la nube a $0 costo y 0 MB de consumo de RAM local.
- *¿Debe usarse /dev/shm en la laptop?* **No como RAMDisk masivo.** Solo buffers de SQLite de pocos megabytes; los workspaces residen en el almacenamiento de disco local para no comprometer los 400 MiB de RAM libre.

---

## 3. Especificación de Requisitos de Software (SRS)

### 3.1. Requisitos Funcionales (FR)
* **FR-01 - Clasificación Determinística de Tiers:**
  - Si `total_ram_gb < 4.0` o `has_avx2 is False`: Asignar `HardwareTier.CONSTRAINED`.
  - Caso contrario: Asignar `HardwareTier.FULL_LOCAL`.
* **FR-02 - Parámetros de Operación Derivados:**
  - En `HardwareTier.CONSTRAINED`:
    - `max_workers = min(2, cpu_threads)`
    - `allow_local_slm = False`
    - `allow_ramdisk_workspace = False`
    - `allow_simd_vectors = False`
  - En `HardwareTier.FULL_LOCAL`:
    - `max_workers = cpu_threads`
    - `allow_local_slm = True`
    - `allow_ramdisk_workspace = True`
    - `allow_simd_vectors = True`
* **FR-03 - Exportación de Perfil en Caché:**
  - Persistir el perfil detectado en `~/.agents/hardware_profile.json` para lectura rápida (< 1 ms) por parte de scripts CLI y hooks.
* **FR-04 - Adaptación del Workspace RAMDisk:**
  - `RAMDiskOptimizer` debe consultar `allow_ramdisk_workspace` antes de intentar clonar directorios a `/dev/shm`. Si es `False`, opera in-place sobre el almacenamiento local.

### 3.2. Requisitos No Funcionales (NFR)
* **NFR-01 - Cero Overhead en Detección:** El escaneo de `/proc/cpuinfo` y `/proc/meminfo` debe completarse en < 10 ms en CPU.
* **NFR-02 - Clean Architecture & Guantelete:** 100% tipado estricto, imports absolutos desde `src.`, archivos `__init__.py` de 0 bytes, sin desactivadores de linters.

---

## 4. Matriz de Casos de Prueba (TC / TDD)

| ID | Caso de Prueba | Entrada | Salida Esperada |
| :--- | :--- | :--- | :--- |
| **TC-01** | `test_domain_entity_defaults` | Instanciación directa de `HardwareSpecs` | Inmutabilidad respetada, valores exactos. |
| **TC-02** | `test_constrained_tier_laptop_detection` | CPU Celeron (no AVX2), RAM 1.8 GiB | `tier == CONSTRAINED`, `allow_local_slm == False`, `max_workers <= 2`. |
| **TC-03** | `test_full_local_tier_desktop_detection` | CPU Ryzen (AVX2), RAM 18 GiB | `tier == FULL_LOCAL`, `allow_local_slm == True`, `max_workers >= 4`. |
| **TC-04** | `test_architecture_conformance` | Análisis estático de `tests/test_architecture.py` | 0 violaciones de imports relativos, 0 directivas de evasión. |

---

## 5. Plan de Ejecución (Pase a Modo /build)

1. **Fase RED:** Ejecución del test de contrato `tests/test_hardware_tier.py` (debe fallar antes de implementar en `src/`).
2. **Fase GREEN (en Modo /build):**
   - Incorporar `HardwareTier`, `HardwareSpecs` e `IHardwareAuditor` en `src/domain/ports.py`.
   - Implementar `HardwareTierDetector` en `src/adapters/hardware_tier_detector.py`.
   - Integrar la verificación adaptativa en `src/adapters/ramdisk_optimizer.py`.
   - Añadir comando `agy-opt hw` en `skills/token-optimizer/scripts/agy_cli.py`.
3. **Fase REFACTOR & GAUNTLET:**
   - Ejecutar `ruff check --fix` y `ruff format`.
   - Superar la suite completa con `python3 -m unittest discover tests`.

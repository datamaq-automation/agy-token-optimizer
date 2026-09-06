# SRS-SPECS: agy-token-optimizer — Single Source of Truth (SSOT) & Especificación del Sistema

> **Documento:** `spec.md`  
> **Versión:** `1.1.0`  
> **Estado:** `Especificación Consolidada (Dudas = 0)`  
> **Fecha:** `2026-08-29`  
> **Autor(es):** `Antigravity SDD Architect`  
> **Repositorio / Rama:** `agy-token-optimizer (main)`  

---

## 1. Contexto Estratégico & Propuesta de Valor

### 1.1. Foco Estratégico & Alcance
* **Mercado / Dominio:** Optimización de tokens, proxy enrutador local de inferencia de LLMs y balanceo inteligente de claves multi-cuenta para AGY y OpenCode.
* **User Persona:** Desarrolladores de software y agentes autónomos que buscan maximizar el aprovechamiento de capas gratuitas (*Free Tiers* de Google Gemini, Groq, DeepSeek, etc.) y minimizar costos con $0 fricción operativa.
* **Fuera de Alcance (*Out of Scope*):** Gestión de pagos o suscripciones bancarias de proveedores externos; interfaces gráficas web propietarias.

### 1.2. Pilares de Valor de la Solución
| Pilar | Enfoque | Implementación en este Módulo |
| :--- | :--- | :--- |
| **1. Dominio & Negocio** | Modelos inmutables de credenciales y contratos abstractos. | `src/domain/` / `ports.py` (dataclasses `ProviderCredential`, `RouterConfig`, puertos `abc.ABC`) |
| **2. Casos de Uso** | Orquestación de carga polimórfica (JSON/YAML/.env), fallback y balanceo. | `src/application/` (`LoadCredentialsUseCase`, `ResolveProviderCascadeUseCase`) |
| **3. Adaptadores & Infra** | Lectores de archivo POSIX, parser JSON estándar y enrutador HTTP OpenAI-compatible. | `src/adapters/` y `skills/token-optimizer/scripts/model_cascade_router.py` |

---

## 2. Modelo de Negocio Canvas (9 Bloques) & Gobernanza
* **Propuesta de Valor:** Proporcionar configuración rica y estructurada de credenciales (cuotas, metadata de cuentas, prioridades, límites de RPM y endpoints personalizados) a $0 tokens y 0 ms de latencia mediante parsers determinísticos.
* **Canales de Distribución:** CLI `agy-opt`, enrutador proxy local `http://127.0.0.1:8080/v1` y sincronización directa con `opencode`.
* **Segmentos de Clientes:** Agentes de codificación en modo `/plan` (AGY) y modo `/build` (OpenCode).

---

## 3. Especificación de Requisitos de Software (SRS)

### 3.1. Requisitos Funcionales (FR)
* **FR-01 - Carga Polimórfica de Credenciales:** El sistema debe detectar y cargar credenciales desde `~/.agy-optimizer/keys.json`, `~/.agy-optimizer/keys.yaml`, `~/.agy-optimizer/config.json`, `~/.agy-optimizer/config.yaml` o `~/.agy-optimizer/.env`.
* **FR-02 - Jerarquía de Precedencia:** La precedencia de lectura debe ser:
  1. `keys.json` / `keys.yaml` / `config.json` / `config.yaml` (Mayor prioridad)
  2. `~/.agy-optimizer/.env` (Compatibilidad retroactiva)
  3. Variables de entorno del sistema (`os.environ`).
* **FR-03 - Soporte de Metadatos Enriquecidos:** Cada entrada en JSON/YAML debe admitir:
  - `name` / `account_tag`: Identificador amigable.
  - `provider`: `gemini` | `groq` | `deepseek` | `mistral` | `cerebras` | `openai` | `custom` | `ollama`.
  - `api_key`: Cadena con la clave de acceso.
  - `email`: Correo electrónico asociado para control de cuota multi-cuenta.
  - `model`: Modelo predeterminado o alias de reemplazo.
  - `priority`: Valor numérico entero para ordenar la cascada de fallbacks.
  - `rpm_limit`: Límite de peticiones por minuto para estrangulamiento preventivo.
  - `enabled`: Booleano para activar o pausar una clave específica sin eliminarla.
  - `base_url`: URL de endpoint personalizado (opcional).
* **FR-04 - Cero Fallos por Ausencia o Formato:** Si un archivo no existe o contiene sintaxis inválida, el cargador debe continuar con el siguiente nivel de fallback sin detener el proceso ni emitir excepciones fatales no controladas.

### 3.2. Requisitos No Funcionales (NFR)
* **NFR-01 - Latencia de Carga:** Tiempo de lectura e indexación de configuración < 5 ms en CPU local.
* **NFR-02 - Cero Dependencias Obligatorias:** Utilizar la librería estándar `json` de Python y un parser nativo liviano para YAML, garantizando ejecución sin dependencias de terceros.
* **NFR-03 - Guantelete de Restricciones:** Tipado estricto al 100%, 0 bytes en `__init__.py`, imports absolutos, y prohibición de desactivadores de linters (`# type: ignore`, `# noqa`).

---

## 4. Stack Tecnológico & Arquitectura Limpia (Clean Architecture)

### 4.1. Estructura Canónica de Capas
```
src/
├── domain/            # 1. Entidades puras y puertos abstractos (ports.py)
├── application/       # 2. Casos de uso (LoadCredentialsUseCase, ResolveProviderCascadeUseCase)
├── adapters/          # 3. Parsers JSON/YAML/.env y Gateways
└── infrastructure/    # 4. Proxy HTTP BaseHTTPRequestHandler y sistema de archivos POSIX
```

### 4.2. Puertos de Dominio y Contratos Iniciales (`ports.py`)
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class ProviderCredential:
    name: str
    provider: str
    api_key: str
    email: Optional[str] = None
    model: Optional[str] = None
    priority: int = 1
    rpm_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    enabled: bool = True
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class RouterConfiguration:
    port: int
    ollama_host: str
    credentials: List[ProviderCredential]


class ICredentialLoader(ABC):
    @abstractmethod
    def load(self, custom_path: Optional[str] = None) -> List[ProviderCredential]:
        """Carga y normaliza credenciales desde JSON, YAML o .env según jerarquía."""
        pass


class IModelCascade(ABC):
    @abstractmethod
    def get_active_providers(self, credentials: List[ProviderCredential]) -> List[Dict[str, Any]]:
        """Construye la lista ordenada de endpoints HTTP para el forwarder."""
        pass
```

---

## 5. Gobernanza de Calidad & Matriz de Pruebas (TDD RED Suite)

| ID Escenario | Caso de Prueba / Gherkin | Archivo de Test | Criterio de Aprobación |
| :--- | :--- | :--- | :--- |
| **TC-01** | `Dado un archivo keys.json con cuentas Gemini y Groq, Cuando se ejecuta load(), Entonces retorna la lista ordenada por prioridad` | `tests/test_credentials_loader.py` | Test pasa verde |
| **TC-02** | `Dado un archivo keys.yaml, Cuando se carga sin dependencias externas, Entonces extrae correctamente las claves y metadatos` | `tests/test_credentials_loader.py` | Test pasa verde |
| **TC-03** | `Dado un entorno donde solo existe ~/.agy-optimizer/.env, Cuando se ejecuta load(), Entonces preserva la compatibilidad legacy` | `tests/test_credentials_loader.py` | Test pasa verde |
| **TC-04** | `Dado un archivo JSON corrupto, Cuando se ejecuta la carga, Entonces hace fallback a .env o env vars sin lanzar excepción fatal` | `tests/test_credentials_loader.py` | Test pasa verde |
| **TC-05** | `Verificación estática de Clean Architecture y Guantelete (0 bytes en __init__.py)` | `tests/test_architecture.py` | 100% cumplimiento |

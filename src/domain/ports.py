"""Dominio puro de agy-token-optimizer: entidades de credenciales y puertos abstractos.

Sin dependencias externas. Solo dataclasses nativas e interfaces abc.ABC (Clean Architecture).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderCredential:
    """Credencial inmutable de un proveedor LLM con metadatos enriquecidos."""

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
    """Configuración global del enrutador en cascada."""

    port: int = 8080
    ollama_host: str = "http://localhost:11434"
    credentials: List[ProviderCredential] = field(default_factory=list)


class ICredentialLoader(ABC):
    """Puerto abstracto para carga y normalización de credenciales."""

    @abstractmethod
    def load(self, custom_path: Optional[str] = None) -> List[ProviderCredential]:
        """Carga y normaliza credenciales desde JSON, YAML o .env según jerarquía."""
        raise NotImplementedError


class IModelCascade(ABC):
    """Puerto abstracto para construcción de la cascada de proveedores."""

    @abstractmethod
    def get_active_providers(self, credentials: List[ProviderCredential]) -> List[Dict[str, Any]]:
        """Construye la lista ordenada de endpoints HTTP para el forwarder."""
        raise NotImplementedError


@dataclass(frozen=True)
class HealResult:
    """Resultado inmutable de la auto-sanación determinística."""

    success: bool
    file_path: str
    execution_time_ms: float
    actions_applied: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RAMDiskStatus:
    """Estado inmutable del workspace en memoria RAMDisk (/dev/shm)."""

    mounted: bool
    path: str
    available_mb: float
    synced_files: int


class IHardwareOptimizer(ABC):
    """Puerto abstracto para optimización y asignación de aceleradores locales."""

    @abstractmethod
    def sync_ramdisk_workspace(self, repo_dir: str) -> RAMDiskStatus:
        """Sincroniza un directorio hacia /dev/shm para ejecución en RAM."""
        raise NotImplementedError


class IPostEditHealer(ABC):
    """Puerto abstracto para auto-sanación determinística en CPU."""

    @abstractmethod
    def heal_file(self, target_file: str) -> HealResult:
        """Ejecuta auto-sanación determinística (Ruff format/check y verificación AST)."""
        raise NotImplementedError


@dataclass(frozen=True)
class CacheEntry:
    """Entrada inmutable en el caché semántico local."""

    query: str
    response: str
    embedding: List[float]
    created_at: str


@dataclass(frozen=True)
class CacheQueryResult:
    """Resultado de una consulta al caché semántico."""

    hit: bool
    response: str
    similarity: float
    tokens_saved: int


class ISemanticCache(ABC):
    """Puerto abstracto para caché semántico en RAMDisk (/dev/shm) con embeddings."""

    @abstractmethod
    def get(self, query: str, threshold: float = 0.92) -> CacheQueryResult:
        """Consulta el caché buscando coincidencias semánticas >= threshold."""
        raise NotImplementedError

    @abstractmethod
    def set(self, query: str, response: str) -> None:
        """Almacena un par pregunta/respuesta calculando su embedding."""
        raise NotImplementedError


@dataclass(frozen=True)
class PruneResult:
    """Resultado de la poda determinística de un archivo de código."""

    original_lines: int
    pruned_lines: int
    reduction_ratio: float
    skeleton_code: str


class IASTPruner(ABC):
    """Puerto abstracto para poda de AST y esqueletización de código."""

    @abstractmethod
    def prune(self, file_path: str, content: Optional[str] = None) -> PruneResult:
        """Poda el cuerpo de las funciones preservando contratos, clases y firmas."""
        raise NotImplementedError


@dataclass(frozen=True)
class TokenSavingsEvent:
    """Evento estructurado de ahorro de tokens en pre o post-procesamiento."""

    event_type: str
    tool_name: str
    tokens_before: int
    tokens_after: int
    tokens_saved: int
    latency_ms: float
    timestamp: str


@dataclass(frozen=True)
class SavingsSummary:
    """Resumen cuantitativo acumulado de métricas de ahorro."""

    total_tokens_saved: int
    total_cost_saved_usd: float
    events_count: Dict[str, int]


class ITokenTelemetry(ABC):
    """Puerto abstracto para el registro de auditoría y cálculo de métricas de tokens."""

    @abstractmethod
    def record_event(self, event: TokenSavingsEvent) -> None:
        """Registra un evento individual en log estructurado y base de datos."""
        raise NotImplementedError

    @abstractmethod
    def get_summary(self) -> SavingsSummary:
        """Calcula el resumen agregado de ahorro y costos evitados."""
        raise NotImplementedError

    @abstractmethod
    def get_recent_events(self, limit: int = 50) -> List[TokenSavingsEvent]:
        """Obtiene la lista de los últimos eventos registrados."""
        raise NotImplementedError


@dataclass(frozen=True)
class DiffCompressionResult:
    """Resultado del filtrado y compresión de un git diff."""

    original_bytes: int
    compressed_bytes: int
    reduction_ratio: float
    clean_diff: str


class IDiffCompressor(ABC):
    """Puerto abstracto para la compresión y poda determinística de git diffs."""

    @abstractmethod
    def compress_diff(self, diff_content: str, max_noise_lines: int = 500) -> DiffCompressionResult:
        """Filtra lockfiles, minificados y ruido manteniendo intacto el código fuente."""
        raise NotImplementedError


@dataclass(frozen=True)
class SLMHealResult:
    """Resultado de auto-sanación sintáctica asistida por SLM local en iGPU."""

    success: bool
    file_path: str
    repaired_code: str
    tokens_used: int
    execution_time_ms: float
    error_message: Optional[str] = None


class ISLMHealer(ABC):
    """Puerto abstracto para reparación sintáctica local asistida por SLM."""

    @abstractmethod
    def repair_syntax(self, file_path: str, code: str, syntax_error: str) -> SLMHealResult:
        """Repara errores sintácticos complejos usando inferencia local en GPU."""
        raise NotImplementedError

"""Dominio puro de agy-token-optimizer: entidades de credenciales y puertos abstractos.

Sin dependencias externas. Solo dataclasses nativas e interfaces abc.ABC (Clean Architecture).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
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
    diagnostics_before: str = ""
    """Diagnósticos que el linter habría devuelto al modelo si nadie los hubiera reparado.

    Es la medida honesta del ahorro: el texto que no entró a la ventana de contexto.
    """
    fixed_count: int = 0
    """Cantidad de hallazgos efectivamente reparados. Cero significa que no se ahorró nada."""


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


@dataclass(frozen=True)
class TerminalPruneResult:
    """Resultado del filtrado y compresión determinística de salidas de terminal."""

    original_lines: int
    pruned_lines: int
    exit_code: int
    clean_output: str
    reduction_ratio: float


class ITerminalPruner(ABC):
    """Puerto abstracto para la compresión de salidas ruidosas de comandos de consola."""

    @abstractmethod
    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult:
        """Filtra trazas irrelevantes y ruido preservando el stack trace y estado final."""
        raise NotImplementedError


@dataclass(frozen=True)
class DataSchemaResult:
    """Resultado de la esquematización estructural de archivos de datos."""

    file_type: str
    total_records: int
    schema_summary: str
    reduction_ratio: float


class IDataSchemaPruner(ABC):
    """Puerto abstracto para reducción de archivos masivos de datos a su esquema canónico."""

    @abstractmethod
    def prune_data_file(self, file_path: str, content: Optional[str] = None) -> DataSchemaResult:
        """Extrae el esquema de tipos y un par de muestras de un archivo JSON, YAML o CSV."""
        raise NotImplementedError


@dataclass(frozen=True)
class PolyglotHealResult:
    """Resultado de la auto-sanación multinivel en lenguajes políglotas (PHP, JS, TS)."""

    language: str
    success: bool
    file_path: str
    actions_applied: List[str]
    execution_time_ms: float
    error_message: Optional[str] = None


class IPolyglotHealer(ABC):
    """Puerto abstracto para validación y auto-sanación de PHP, JavaScript y TypeScript."""

    @abstractmethod
    def heal_file(self, target_file: str) -> PolyglotHealResult:
        """Valida y sana archivos de código en PHP, JS o TS en CPU/iGPU local."""
        raise NotImplementedError


class CommandScope(Enum):
    """Dónde se ejecuta el comando de una `run_command`."""

    LOCAL = "local"
    REMOTO = "remoto"


class CommandKind(Enum):
    """Clasificación de un comando visto por el hook PreToolUse."""

    LECTURA_CODIGO = "lectura_codigo"
    CONSULTA = "consulta"
    ESCRITURA = "escritura"
    MUTACION = "mutacion"
    INTERACTIVO = "interactivo"
    EXENTO = "exento"


@dataclass(frozen=True)
class RemoteHost:
    """Alias SSH con su fallback de familia de direcciones."""

    alias: str
    fallback_alias: Optional[str] = None
    port: int = 22
    user: str = "root"


@dataclass(frozen=True)
class CommandClassification:
    """Resultado del análisis de una CommandLine de run_command."""

    scope: CommandScope
    kind: CommandKind
    inner_command: str
    reason: str
    target_path: Optional[str] = None
    host_alias: Optional[str] = None


@dataclass(frozen=True)
class RemoteExecutionResult:
    """Resultado de ejecutar un comando remoto con poda de salida."""

    exit_code: int
    clean_output: str
    host_used: str
    timed_out: bool = False
    original_lines: int = 0
    pruned_lines: int = 0
    reduction_ratio: float = 0.0


class ICommandClassifier(ABC):
    """Puerto para clasificar la CommandLine de un run_command, local o remota."""

    @abstractmethod
    def classify(self, command_line: str) -> Optional[CommandClassification]:
        """Devuelve la clasificación, o None si no hay nada que hacer con la línea."""
        raise NotImplementedError


class ICodeFileInspector(ABC):
    """Puerto para decidir si un archivo local justifica poda, sin salir del presupuesto del hook."""

    @abstractmethod
    def excede_umbral(self, path: str, umbral_lineas: int = 100) -> bool:
        """True si el archivo existe, tiene extensión de código y supera el umbral de líneas."""
        raise NotImplementedError


class IRemoteExecutor(ABC):
    """Puerto para ejecución remota con fallback de host y poda de salida."""

    @abstractmethod
    def execute(self, command: str, host: RemoteHost, timeout_s: int = 60) -> RemoteExecutionResult:
        """Ejecuta en remoto; ante fallo de resolución del alias primario, reintenta con el fallback."""
        raise NotImplementedError


class HardwareTier(Enum):
    """Clasificación de perfil de hardware adaptativo."""

    FULL_LOCAL = "full_local"
    CONSTRAINED = "constrained"


@dataclass(frozen=True)
class HardwareSpecs:
    """Metadatos inmutables de auditoría de hardware local."""

    cpu_cores: int
    cpu_threads: int
    has_avx2: bool
    total_ram_gb: float
    available_ram_mb: float
    has_vulkan: bool
    shm_available: bool
    tier: HardwareTier
    max_workers: int
    allow_local_slm: bool
    allow_ramdisk_workspace: bool
    allow_simd_vectors: bool


class IHardwareAuditor(ABC):
    """Puerto para auditar dinámicamente la capacidad del hardware local."""

    @abstractmethod
    def audit(self) -> HardwareSpecs:
        """Audita el hardware y devuelve sus especificaciones y tier asignado."""
        raise NotImplementedError

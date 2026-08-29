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

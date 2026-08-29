"""Capa de aplicación: caso de uso de carga de credenciales estructuradas.

Orquesta el cargador de credenciales (adapters) y retorna credenciales normalizadas
como DTOs de aplicación (dictos json-serializables).
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.adapters.credential_loader import CredentialLoader
from src.domain.ports import ProviderCredential


class LoadCredentialsUseCase:
    """Caso de uso que expone la carga polimórfica de credenciales al resto del sistema."""

    def __init__(self, loader: Optional[CredentialLoader] = None) -> None:
        self._loader = loader or CredentialLoader()

    def execute(self, custom_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Carga credenciales y las mapea a DTOs de aplicación (dictos nativos)."""
        credentials = self._loader.load(custom_path=custom_path)
        return [asdict(credential) for credential in credentials]


def load_structured_credentials(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Función de conveniencia para cargar credenciales estructuradas.

    Contrato utilizado por la suite de pruebas (tests/test_credentials_loader.py) y el router.
    """
    return LoadCredentialsUseCase().execute(custom_path=config_path)


def parse_yaml_credentials(config_path: str) -> List[ProviderCredential]:
    """Expone el parser YAML nativo como contrato público del cargador.

    Retorna las entidades ProviderCredential sin post-procesamiento de la capa de aplicación.
    """
    loader = CredentialLoader()
    path = Path(config_path)
    if not path.is_file():
        return []
    return loader.parse_yaml_credentials_from(config_path)

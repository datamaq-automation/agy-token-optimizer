"""Adaptador de dominio: cargador de credenciales estructuradas (JSON / YAML / .env).

Implementa el puerto ICredentialLoader con los parsers de la capa de adaptadores.
La jerarquía de precedencia (FR-02) y la tolerancia a fallos (FR-04) están garantizadas.

Cero dependencias externas: json (estándar) y yaml_parser nativo.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.adapters.yaml_parser import YamlParsingError, parse_yaml
from src.domain.ports import ICredentialLoader, ProviderCredential

_DEFAULT_CONFIG_DIR = Path.home() / ".agy-optimizer"
# Orden de precedencia de archivos estructurados (FR-02, mayor a menor).
_STRUCTURED_CANDIDATES = ("keys.json", "keys.yaml", "config.json", "config.yaml")
_LEGACY_ENV_NAME = ".env"
_ALLOWED_PROVIDERS = {"gemini", "groq", "deepseek", "mistral", "cerebras", "openai", "custom", "ollama"}


class CredentialLoader(ICredentialLoader):
    """Implementación concreta del puerto de carga de credenciales."""

    def load(self, custom_path: Optional[str] = None) -> List[ProviderCredential]:
        """Carga credenciales siguiendo la jerarquía de precedencia de la especificación."""
        config_dir = _DEFAULT_CONFIG_DIR
        if custom_path:
            config_dir = Path(custom_path)

        # 1) Carga directa de un archivo explícito (utilizado por la suite de pruebas).
        if custom_path and Path(custom_path).is_file():
            creds = self._load_file(Path(custom_path))
            if creds:
                return creds

        # 2) Archivos estructurados (mayor prioridad).
        for candidate in _STRUCTURED_CANDIDATES:
            path = config_dir / candidate
            if path.is_file():
                creds = self._load_file(path)
                if creds:
                    return creds

        # 3) Compatibilidad retroactiva con .env legacy.
        env_path = config_dir / _LEGACY_ENV_NAME
        if env_path.is_file():
            creds = self._load_env_file(env_path)
            if creds:
                return creds

        # 4) Último recurso: variables de entorno del sistema (os.environ).
        return self._load_from_environ()

    def _load_file(self, path: Path) -> List[ProviderCredential]:
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                return self._parse_json_file(path)
            if suffix in (".yaml", ".yml"):
                return self._parse_yaml_file(path)
            if suffix == ".env" or path.name == ".env":
                return self._load_env_file(path)
            # Fallback por contenido: intentar JSON, luego YAML.
            try:
                return self._parse_json_file(path)
            except (ValueError, json.JSONDecodeError):
                return self._parse_yaml_file(path)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, YamlParsingError):
            # FR-04: nunca abortar; continuar con el siguiente nivel de fallback.
            return []

    def _parse_json_file(self, path: Path) -> List[ProviderCredential]:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        providers = raw.get("providers", []) if isinstance(raw, dict) else raw
        return self._normalize_providers(providers)

    def _parse_yaml_file(self, path: Path) -> List[ProviderCredential]:
        with open(path, "r", encoding="utf-8") as fh:
            document = parse_yaml(fh.read())
        if document is None:
            return []
        providers = document.get("providers", []) if isinstance(document, dict) else document
        return self._normalize_providers(providers)

    def parse_yaml_credentials_from(self, path: str) -> List[ProviderCredential]:
        """Contrato público: parsea un archivo YAML y retorna sus credenciales normalizadas.

        Usado por la capa de aplicación para exponer `parse_yaml_credentials` sin
        acceder a implementaciones privadas (batería 4 del Gauntlete).
        """
        return self._parse_yaml_file(Path(path))

    def _load_env_file(self, path: Path) -> List[ProviderCredential]:
        env_vars: Dict[str, str] = {}
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
        return self._build_from_env_vars(env_vars)

    def _load_from_environ(self) -> List[ProviderCredential]:
        env_vars: Dict[str, str] = {
            "GEMINI_API_KEYS": os.environ.get("GEMINI_API_KEYS", ""),
            "GROQ_API_KEYS": os.environ.get("GROQ_API_KEYS", ""),
            "DEEPSEEK_API_KEYS": os.environ.get("DEEPSEEK_API_KEYS", ""),
        }
        return self._build_from_env_vars(env_vars)

    @staticmethod
    def _normalize_providers(providers: object) -> List[ProviderCredential]:
        """Normaliza una lista cruda de proveedores y filtra deshabilitados/minusválidos."""
        if not isinstance(providers, list):
            return []
        result: List[ProviderCredential] = []
        for entry in providers:
            if not isinstance(entry, dict):
                continue
            api_key = str(entry.get("api_key") or "").strip()
            if not api_key:
                continue
            enabled = bool(entry.get("enabled", True))
            if not enabled:
                # FR-03: claves desactivadas se omiten de la lista activa.
                continue
            provider = str(entry.get("provider") or "custom").strip().lower()
            name = str(entry.get("name") or entry.get("account_tag") or f"{provider}-cuenta").strip()
            result.append(
                ProviderCredential(
                    name=name,
                    provider=provider,
                    api_key=api_key,
                    email=str(entry["email"]).strip() if entry.get("email") is not None else None,
                    model=str(entry["model"]).strip() if entry.get("model") is not None else None,
                    priority=int(entry.get("priority", 1)),
                    rpm_limit=int(entry["rpm_limit"]) if entry.get("rpm_limit") is not None else None,
                    daily_limit=(int(entry["daily_limit"]) if entry.get("daily_limit") is not None else None),
                    base_url=str(entry["base_url"]).strip() if entry.get("base_url") is not None else None,
                )
            )
        # FR-03 / TC-01: orden por prioridad ascendente.
        result.sort(key=lambda c: c.priority)
        return result

    @staticmethod
    def _build_from_env_vars(env_vars: Dict[str, str]) -> List[ProviderCredential]:
        """Construye credenciales legacy multi-key desde un mapa de variables de entorno."""
        mapping = {
            "GEMINI_API_KEYS": ("gemini", "gemini-2.0-flash"),
            "GROQ_API_KEYS": ("groq", "llama-3.3-70b-versatile"),
            "DEEPSEEK_API_KEYS": ("deepseek", "deepseek-chat"),
        }
        result: List[ProviderCredential] = []
        for env_key, (provider, default_model) in mapping.items():
            raw = env_vars.get(env_key, "")
            for idx, key in enumerate(CredentialLoader._split_keys(raw), 1):
                if not key:
                    continue
                result.append(
                    ProviderCredential(
                        name=f"{provider.capitalize()} Cuenta #{idx}",
                        provider=provider,
                        api_key=key,
                        model=default_model,
                        priority=idx,
                    )
                )
        # Preservar el orden natural (sin reordenar por prioridad de múltiples proveedores).
        return result

    @staticmethod
    def _split_keys(raw: str) -> List[str]:
        if not raw:
            return []
        return [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]

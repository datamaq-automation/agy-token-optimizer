"""Facade de compatibilidad: expone el contrato de carga de credenciales.

Este módulo permite que la suite de pruebas (tests/test_credentials_loader.py)
importe `load_structured_credentials` y `parse_yaml_credentials` desde el punto de
entrada canónico `skills.token_optimizer.scripts.model_cascade_router`, delegando
sin duplicar lógica en la capa de aplicación de Clean Architecture.
"""

from src.application.load_credentials import load_structured_credentials, parse_yaml_credentials


def reorder_providers_after_quota_error(providers: list[dict], failed_provider: str, status_code: int) -> list[dict]:
    """Compatibilidad para mover DeepSeek al frente ante un 429 de Google."""
    deepseek = [p for p in providers if str(p.get("provider", "")).lower() == "deepseek"]
    if status_code != 429:
        return providers
    failed = (failed_provider or "").lower()
    if "gemini" not in failed and "google" not in failed:
        return providers
    if not deepseek:
        return providers
    rest = [p for p in providers if str(p.get("provider", "")).lower() != "deepseek"]
    return deepseek + rest


__all__ = [
    "load_structured_credentials",
    "parse_yaml_credentials",
    "reorder_providers_after_quota_error",
]

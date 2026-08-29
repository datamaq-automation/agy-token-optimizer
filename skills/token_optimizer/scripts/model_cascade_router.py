"""Facade de compatibilidad: expone el contrato de carga de credenciales.

Este módulo permite que la suite de pruebas (tests/test_credentials_loader.py)
importe `load_structured_credentials` y `parse_yaml_credentials` desde el punto de
entrada canónico `skills.token_optimizer.scripts.model_cascade_router`, delegando
sin duplicar lógica en la capa de aplicación de Clean Architecture.
"""

from src.application.load_credentials import load_structured_credentials, parse_yaml_credentials

__all__ = ["load_structured_credentials", "parse_yaml_credentials"]

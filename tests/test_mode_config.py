import json
import os
from pathlib import Path

import pytest

LOCAL_BIN = Path(os.path.expanduser("~/bin"))
LOCAL_CONFIG = Path(os.path.expanduser("~/.gemini/config/config.json"))

is_not_local_agustin = not Path("/home/agustin/bin/agy-plan").exists()


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_wrapper_agy_plan_existe() -> None:
    """agy-plan debe existir y ser ejecutable."""
    p = Path("/home/agustin/bin/agy-plan")
    assert p.is_file(), "~/bin/agy-plan no existe"
    assert os.access(p, os.X_OK), "~/bin/agy-plan no es ejecutable"


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_wrapper_agy_build_existe() -> None:
    """agy-build debe existir y ser ejecutable."""
    p = Path("/home/agustin/bin/agy-build")
    assert p.is_file(), "~/bin/agy-build no existe"
    assert os.access(p, os.X_OK), "~/bin/agy-build no es ejecutable"


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_config_default_model_es_economico() -> None:
    """El modelo por defecto en config.json debe ser el más económico."""
    config_path = Path("/home/agustin/.gemini/config/config.json")
    assert config_path.exists(), "config.json no encontrado"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    us = config.get("userSettings", {})
    assert us.get("model") == "gemini-3.8-flash-low", f"modelo default inesperado: {us.get('model')}"
    assert us.get("effort") == "low", f"effort default inesperado: {us.get('effort')}"


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_wrapper_plan_usa_modelo_high() -> None:
    """El script agy-plan debe contener --model gemini-3.8-flash-high y --effort high."""
    contenido = Path("/home/agustin/bin/agy-plan").read_text(encoding="utf-8")
    assert "--model gemini-3.8-flash-high" in contenido
    assert "--effort high" in contenido


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_wrapper_build_usa_modelo_low() -> None:
    """El script agy-build debe contener --model gemini-3.8-flash-low y --effort low."""
    contenido = Path("/home/agustin/bin/agy-build").read_text(encoding="utf-8")
    assert "--model gemini-3.8-flash-low" in contenido
    assert "--effort low" in contenido


@pytest.mark.skipif(is_not_local_agustin, reason="Solo ejecutable en entorno local del host")
def test_wrappers_escriben_current_mode() -> None:
    """Ambos wrappers deben escribir en ~/.agents/current_mode."""
    for script in ("agy-plan", "agy-build"):
        contenido = Path(f"/home/agustin/bin/{script}").read_text(encoding="utf-8")
        assert "current_mode" in contenido, f"{script} no escribe en current_mode"

import json
import os
import unittest
from pathlib import Path

LOCAL_BIN = Path(os.path.expanduser("~/bin"))
LOCAL_CONFIG = Path(os.path.expanduser("~/.gemini/config/config.json"))

is_local_agustin = Path("/home/agustin/bin/agy-plan").exists()


class TestModeConfig(unittest.TestCase):
    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_wrapper_agy_plan_existe(self) -> None:
        """agy-plan debe existir y ser ejecutable."""
        p = Path("/home/agustin/bin/agy-plan")
        self.assertTrue(p.is_file(), "~/bin/agy-plan no existe")
        self.assertTrue(os.access(p, os.X_OK), "~/bin/agy-plan no es ejecutable")

    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_wrapper_agy_build_existe(self) -> None:
        """agy-build debe existir y ser ejecutable."""
        p = Path("/home/agustin/bin/agy-build")
        self.assertTrue(p.is_file(), "~/bin/agy-build no existe")
        self.assertTrue(os.access(p, os.X_OK), "~/bin/agy-build no es ejecutable")

    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_config_default_model_es_economico(self) -> None:
        """El modelo por defecto en config.json debe ser el más económico."""
        config_path = Path("/home/agustin/.gemini/config/config.json")
        self.assertTrue(config_path.exists(), "config.json no encontrado")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        us = config.get("userSettings", {})
        self.assertEqual(us.get("model"), "gemini-3.8-flash-low")
        self.assertEqual(us.get("effort"), "low")

    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_wrapper_plan_usa_modelo_high(self) -> None:
        """El script agy-plan debe contener --model gemini-3.8-flash-high y --effort high."""
        contenido = Path("/home/agustin/bin/agy-plan").read_text(encoding="utf-8")
        self.assertIn("--model gemini-3.8-flash-high", contenido)
        self.assertIn("--effort high", contenido)

    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_wrapper_build_usa_modelo_low(self) -> None:
        """El script agy-build debe contener --model gemini-3.8-flash-low y --effort low."""
        contenido = Path("/home/agustin/bin/agy-build").read_text(encoding="utf-8")
        self.assertIn("--model gemini-3.8-flash-low", contenido)
        self.assertIn("--effort low", contenido)

    @unittest.skipUnless(is_local_agustin, "Solo ejecutable en entorno local del host")
    def test_wrappers_escriben_current_mode(self) -> None:
        """Ambos wrappers deben escribir en ~/.agents/current_mode."""
        for script in ("agy-plan", "agy-build"):
            contenido = Path(f"/home/agustin/bin/{script}").read_text(encoding="utf-8")
            self.assertIn("current_mode", contenido)


if __name__ == "__main__":
    unittest.main()

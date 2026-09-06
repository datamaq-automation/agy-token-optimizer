#!/usr/bin/env python3
"""
tests/test_credentials_loader.py: Suite TDD para carga polimórfica y estructurada
de credenciales (JSON, YAML y .env) con soporte de metadatos enriquecidos.
"""

import json
import tempfile
import unittest
from pathlib import Path

# Importación de componentes cuando se implementen en src/ o scripts/
try:
    from skills.token_optimizer.scripts.model_cascade_router import (
        load_structured_credentials,
        parse_yaml_credentials,
    )
except ImportError:
    # Definición de fallbacks para etapa TDD RED inicial
    load_structured_credentials = None
    parse_yaml_credentials = None


class TestStructuredCredentialsLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_from_valid_json(self):
        """TC-01: Debe cargar y parsear keys.json con metadatos completos y orden por prioridad."""
        json_path = self.config_dir / "keys.json"
        data = {
            "providers": [
                {
                    "name": "Groq Secundario",
                    "provider": "groq",
                    "api_key": "gsk_test_groq_2",
                    "email": "secondary@test.com",
                    "model": "llama-3.3-70b-versatile",
                    "priority": 2,
                    "rpm_limit": 30,
                    "enabled": True,
                },
                {
                    "name": "Gemini Primario",
                    "provider": "gemini",
                    "api_key": "AIzaSy_test_gemini_1",
                    "email": "primary@test.com",
                    "model": "gemini-2.0-flash",
                    "priority": 1,
                    "rpm_limit": 15,
                    "enabled": True,
                },
                {
                    "name": "Clave Desactivada",
                    "provider": "gemini",
                    "api_key": "AIzaSy_disabled",
                    "enabled": False,
                },
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        if load_structured_credentials is None:
            self.fail("TDD RED: load_structured_credentials no está implementado aún en src/ / scripts/")

        creds = load_structured_credentials(config_path=str(json_path))
        self.assertEqual(len(creds), 2, "Debe omitir credenciales con enabled=False")
        self.assertEqual(creds[0]["provider"], "gemini", "La prioridad 1 debe ir primero")
        self.assertEqual(creds[0]["email"], "primary@test.com")
        self.assertEqual(creds[1]["provider"], "groq")

    def test_load_from_valid_yaml(self):
        """TC-02: Debe cargar keys.yaml sin requerir librerías externas pesadas."""
        yaml_path = self.config_dir / "keys.yaml"
        yaml_content = """
providers:
  - name: "Groq Principal"
    provider: "groq"
    api_key: "gsk_yaml_test_1"
    email: "yaml@test.com"
    priority: 1
    enabled: true
"""
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        if load_structured_credentials is None:
            self.fail("TDD RED: load_structured_credentials no está implementado aún")

        creds = load_structured_credentials(config_path=str(yaml_path))
        self.assertEqual(len(creds), 1)
        self.assertEqual(creds[0]["api_key"], "gsk_yaml_test_1")
        self.assertEqual(creds[0]["email"], "yaml@test.com")

    def test_fallback_to_legacy_env(self):
        """TC-03: Si no hay JSON/YAML, debe cargar correctamente desde .env legacy."""
        env_path = self.config_dir / ".env"
        env_content = """
GEMINI_API_KEYS="AIzaSy_legacy_1, AIzaSy_legacy_2"
GROQ_API_KEYS="gsk_legacy_1"
"""
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)

        if load_structured_credentials is None:
            self.fail("TDD RED: load_structured_credentials no está implementado aún")

        creds = load_structured_credentials(config_path=str(env_path))
        self.assertGreaterEqual(len(creds), 3)
        gemini_creds = [c for c in creds if c["provider"] == "gemini"]
        self.assertEqual(len(gemini_creds), 2)

    def test_malformed_json_fallback(self):
        """TC-04: Si el JSON está mal formado, no debe lanzar excepción no controlada."""
        json_path = self.config_dir / "keys.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json formatting ...")

        if load_structured_credentials is None:
            self.fail("TDD RED: load_structured_credentials no está implementado aún")

        creds = load_structured_credentials(config_path=str(json_path))
        self.assertIsInstance(creds, list)


if __name__ == "__main__":
    unittest.main()

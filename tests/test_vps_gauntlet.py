"""Pruebas de la clasificación de etapas del Gauntlet remoto.

Un Gauntlet que no puede fallar es peor que no tenerlo: la primera versión de
este script canalizaba cada etapa a 'tail', con lo que el código de salida era
el de 'tail' y todas las etapas daban OK.
"""

import importlib.util
import os
import unittest

RUTA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills",
    "token-optimizer",
    "scripts",
    "vps_gauntlet.py",
)
_spec = importlib.util.spec_from_file_location("vps_gauntlet", RUTA)
assert _spec is not None and _spec.loader is not None
vps_gauntlet = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vps_gauntlet)


class TestClasificacionDeEtapas(unittest.TestCase):
    def test_exito_por_codigo_cero(self) -> None:
        self.assertEqual(vps_gauntlet._clasificar("All checks passed!", 0, False), "OK")

    def test_fallo_por_codigo_distinto_de_cero(self) -> None:
        self.assertEqual(vps_gauntlet._clasificar("48 files would be reformatted", 1, False), "FALLA")

    def test_herramienta_ausente_no_es_ni_exito_ni_fallo(self) -> None:
        """'No module named pytest' significa que la etapa no se pudo evaluar."""
        for salida in ("/usr/bin/python3: No module named pytest", "bash: pyright: command not found"):
            self.assertEqual(vps_gauntlet._clasificar(salida, 127, False), "s/d", salida)

    def test_etapa_de_salida_vacia(self) -> None:
        """La integridad de __init__.py se aprueba por ausencia de hallazgos."""
        self.assertEqual(vps_gauntlet._clasificar("", 0, True), "OK")
        self.assertEqual(vps_gauntlet._clasificar("./src/__init__.py", 0, True), "FALLA")

    def test_las_etapas_no_llevan_tuberia(self) -> None:
        """Una tubería enmascararía el código de salida real de la etapa."""
        for nombre, comando, _, _ in vps_gauntlet.ETAPAS:
            self.assertNotIn("| tail", comando, nombre)
            self.assertNotIn("| head", comando, nombre)

    def test_la_integridad_excluye_entornos_virtuales(self) -> None:
        """Sin la exclusión, el hallazgo son los __init__.py de site-packages."""
        comando = next(c for n, c, _, _ in vps_gauntlet.ETAPAS if "Integridad" in n)
        for excluido in (".venv", "site-packages", "node_modules"):
            self.assertIn(excluido, comando)


if __name__ == "__main__":
    unittest.main()

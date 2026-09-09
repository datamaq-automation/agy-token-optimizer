"""Pruebas de la medición de ahorro del auto-sanador.

Antes, 'ruff check --fix' devolvía 0 tanto si reparaba algo como si no había nada
que reparar, y el hook declaraba 500 tokens fijos en ambos casos. De ahí que el
78% del ahorro reportado por el sistema fueran 103 eventos de una constante.
"""

import os
import shutil
import tempfile
import unittest

from src.adapters.hardware_healer import DeterministicHardwareHealer


class TestMedicionDelAhorro(unittest.TestCase):
    def setUp(self) -> None:
        self.healer = DeterministicHardwareHealer()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _archivo(self, contenido: str) -> str:
        ruta = os.path.join(self.tmp.name, "muestra.py")
        with open(ruta, "w", encoding="utf-8") as handle:
            handle.write(contenido)
        return ruta

    def test_archivo_limpio_no_declara_ahorro(self) -> None:
        """Sanar un archivo que ya estaba bien no ahorra ningún token."""
        res = self.healer.heal_file(self._archivo("x = 1\n"))
        self.assertEqual(res.fixed_count, 0)
        self.assertNotIn("ruff_check_fixed", res.actions_applied)

    def test_archivo_con_hallazgos_cuenta_las_reparaciones(self) -> None:
        res = self.healer.heal_file(self._archivo("import os\nimport sys\nx = 1\n"))
        if shutil.which("ruff"):
            self.assertGreater(res.fixed_count, 0)
            self.assertIn("ruff_check_fixed", res.actions_applied)

    def test_captura_los_diagnosticos_previos(self) -> None:
        """El texto capturado es la medida del ahorro: lo que el modelo no tuvo que leer."""
        res = self.healer.heal_file(self._archivo("import os\nimport sys\nx = 1\n"))
        if shutil.which("ruff"):
            self.assertIn("F401", res.diagnostics_before)
            self.assertGreater(len(res.diagnostics_before), 0)

    def test_archivo_inexistente_no_rompe(self) -> None:
        res = self.healer.heal_file(os.path.join(self.tmp.name, "no-existe.py"))
        self.assertFalse(res.success)
        self.assertEqual(res.fixed_count, 0)


if __name__ == "__main__":
    unittest.main()

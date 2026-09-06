"""Pruebas del inspector local de archivos: nunca lanza, nunca bloquea el hook."""

import os
import tempfile
import unittest

from src.adapters.code_file_inspector import LocalCodeFileInspector


class TestInspectorLocal(unittest.TestCase):
    """Escenario 27 y colindantes: robustez del inspector dentro del hook."""

    def setUp(self) -> None:
        self.inspector = LocalCodeFileInspector()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _crear(self, nombre: str, lineas: int) -> str:
        ruta = os.path.join(self.tmp.name, nombre)
        with open(ruta, "w", encoding="utf-8") as handle:
            handle.write("x = 1\n" * lineas)
        return ruta

    def test_path_inexistente_devuelve_false_sin_lanzar(self) -> None:
        """Escenario 27: el hook nunca debe romperse por un path que no existe."""
        self.assertFalse(self.inspector.excede_umbral("/no/existe/archivo.py"))

    def test_path_vacio_devuelve_false(self) -> None:
        self.assertFalse(self.inspector.excede_umbral(""))

    def test_extension_no_podable_devuelve_false(self) -> None:
        """Un binario o un .md no justifican poda AST aunque sean largos."""
        ruta = self._crear("notas.md", 500)
        self.assertFalse(self.inspector.excede_umbral(ruta))

    def test_archivo_extenso_supera_el_umbral(self) -> None:
        ruta = self._crear("largo.py", 400)
        self.assertTrue(self.inspector.excede_umbral(ruta))

    def test_archivo_corto_no_supera_el_umbral(self) -> None:
        ruta = self._crear("corto.py", 40)
        self.assertFalse(self.inspector.excede_umbral(ruta))

    def test_umbral_configurable(self) -> None:
        ruta = self._crear("medio.py", 50)
        self.assertTrue(self.inspector.excede_umbral(ruta, umbral_lineas=10))
        self.assertFalse(self.inspector.excede_umbral(ruta, umbral_lineas=200))

    def test_un_directorio_no_es_archivo(self) -> None:
        """isfile filtra directorios que casualmente terminen en .py."""
        ruta = os.path.join(self.tmp.name, "paquete.py")
        os.mkdir(ruta)
        self.assertFalse(self.inspector.excede_umbral(ruta))


if __name__ == "__main__":
    unittest.main()

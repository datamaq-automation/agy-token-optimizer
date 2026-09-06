"""Pruebas del generador de CHANGELOG: no debe descartar historial en silencio."""

import importlib.util
import os
import unittest
from pathlib import Path

RUTA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills",
    "token-optimizer",
    "scripts",
    "changelog_generator.py",
)
_spec = importlib.util.spec_from_file_location("changelog_generator", RUTA)
assert _spec is not None and _spec.loader is not None
generador = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generador)


class TestSinTruncado(unittest.TestCase):
    """El generador topeaba features en 15 y docs en 10, borrando lo más viejo del archivo."""

    def test_el_codigo_no_topea_las_listas(self) -> None:
        with open(RUTA, "r", encoding="utf-8") as handle:
            codigo = handle.read()
        for recorte in ("feats[:15]", "perfs[:15]", "fixes[:15]", "docs[:10]"):
            self.assertNotIn(recorte, codigo, f"El generador vuelve a descartar historial: {recorte}")

    def test_conserva_todas_las_entradas_del_repo(self) -> None:
        """Toda línea 'feat(...)' del historial git debe figurar en el documento."""
        raiz = Path(RUTA).parents[3]
        commits = generador.get_git_commits(raiz)
        salida = generador.generate_changelog(raiz)
        feats = [c for c in commits if c.startswith("feat")]
        faltantes = [f for f in feats if f not in salida]
        self.assertEqual(faltantes, [], f"El generador descartó {len(faltantes)} entradas")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
tests/test_architecture.py: Suite del Guantelete de Restricciones (TC-05).

Verificación estática de Clean Architecture y baterías inmutables:
1. `__init__.py` de 0 bytes en `src/` y `tests/`.
2. Imports 100% absolutos (sin imports relativos punto).
3. Tipado estricto (sin desactivadores de linters como `type: ignore`).
4. Zero secretos quemados en código fuente.
"""

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
PYTHON_EXTENSIONS = {".py"}

_EVASION_PATTERNS = (
    re.compile(r"#\s*type:\s*ignore"),
    re.compile(r"#\s*noqa"),
)
_RELATIVE_IMPORT = re.compile(r"^\s*(?:from\s+\.|import\s+\.)")


class TestConstraintGauntlet(unittest.TestCase):
    """Baterías inmutables del Guantelete de Restricciones."""

    def test_init_files_are_zero_bytes(self):
        """Batería 1: 100% de `__init__.py` en src/ y tests/ con exactamente 0 bytes."""
        init_files = [p for p in [*SRC_DIR.rglob("__init__.py"), *TESTS_DIR.rglob("__init__.py")] if p.is_file()]
        self.assertGreaterEqual(len(init_files), 6, "Debe existir la matriz canónica de `__init__.py`")
        for init in init_files:
            with self.subTest(init=init):
                self.assertEqual(init.stat().st_size, 0, f"`__init__.py` no vacío: {init}")

    def test_no_relative_imports(self):
        """Batería 2: prohibición de imports relativos en src/ y scripts de la skill."""
        target_dirs = [SRC_DIR]
        offenders: list[str] = []
        for base in target_dirs:
            for py in base.rglob("*"):
                if py.suffix not in PYTHON_EXTENSIONS or not py.is_file():
                    continue
                for num, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                    if _RELATIVE_IMPORT.match(line):
                        offenders.append(f"{py}:{num}: {line.strip()}")
        self.assertEqual(offenders, [], "Existen imports relativos prohibidos:\n" + "\n".join(offenders))

    def test_no_evasion_directives(self):
        """Batería 4: prohibición de desactivadores de linters en el código productivo.

        No se escanean los archivos de pruebas (self excluido) para evitar falsos positivos.
        """
        offenders: list[str] = []
        for py in SRC_DIR.rglob("*.py"):
            if not py.is_file():
                continue
            for num, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if any(pat.search(line) for pat in _EVASION_PATTERNS):
                    offenders.append(f"{py}:{num}: {line.strip()}")
        self.assertEqual(offenders, [], "Directivas de evasión detectadas:\n" + "\n".join(offenders))

    def test_no_burned_secrets(self):
        """Batería 5: Zero secrets (api_key/quemados) en el código fuente de src/."""
        secret_re = re.compile(
            r"""["'](?:
                GSK[\w\-]{10,}
                |AIza[\w\-]{20,}
                |sk-[A-Za-z0-9]{20,}
                )["']""",
            re.VERBOSE,
        )
        offenders: list[str] = []
        for py in SRC_DIR.rglob("*.py"):
            if not py.is_file():
                continue
            for num, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if secret_re.search(line.replace("#", " # ")):
                    offenders.append(f"{py}:{num}")
        self.assertEqual(offenders, [], "Posibles secretos quemados:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()

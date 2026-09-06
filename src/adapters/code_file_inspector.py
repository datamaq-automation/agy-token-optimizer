"""Adaptador de inspección local de archivos para decidir si justifican poda.

Cuenta líneas en disco sin cargar el archivo entero en memoria. Nunca lanza:
un path inexistente, ilegible o binario devuelve False y el comando pasa.
"""

import os
from typing import FrozenSet

from src.domain.ports import ICodeFileInspector

PODABLE_EXTS: FrozenSet[str] = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".php",
        ".java",
        ".rb",
        ".c",
        ".h",
        ".cpp",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".csv",
        ".xml",
        ".ini",
        ".cfg",
    }
)


class LocalCodeFileInspector(ICodeFileInspector):
    """Inspecciona archivos del disco local dentro del presupuesto del hook."""

    def excede_umbral(self, path: str, umbral_lineas: int = 100) -> bool:
        if not path:
            return False

        _, ext = os.path.splitext(path)
        if ext.lower() not in PODABLE_EXTS:
            return False

        expandido = os.path.expanduser(path)
        if not os.path.isfile(expandido):
            return False

        try:
            with open(expandido, "r", encoding="utf-8", errors="ignore") as handle:
                for indice, _ in enumerate(handle, start=1):
                    if indice > umbral_lineas:
                        return True
        except OSError:
            return False

        return False

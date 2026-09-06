"""Adaptador de poda para salidas remotas: logs, journalctl y volcados de estado.

TerminalOutputPruner filtra ruido de instaladores (npm, pip, composer). Las salidas
remotas tienen otra forma: bloques de lineas casi identicas repetidas por bucles de
reinicio o por un servicio que falla en ciclo. Este adaptador colapsa esas rachas
conservando una muestra y el conteo, que es lo que aporta senal.

Ambos implementan ITerminalPruner: el caso de uso elige por inyeccion cual usar.
"""

import re
from typing import List

from src.domain.ports import ITerminalPruner, TerminalPruneResult

# Marca de tiempo al inicio de linea, en los formatos que emiten journalctl y syslog.
_TIMESTAMP = re.compile(r"^(?:\w{3}\s+\d{1,2}\s+[\d:]{8}|\d{4}-\d{2}-\d{2}[T ][\d:.,+-]+|\[[^\]]+\])\s*")
_DIGITOS = re.compile(r"\d+")

_CRITICAS = (
    "error",
    "failed",
    "failure",
    "fatal",
    "exception",
    "traceback",
    "critical",
    "denied",
    "refused",
    "panic",
)


class RemoteOutputPruner(ITerminalPruner):
    """Colapsa rachas de lineas equivalentes y acota el volumen final."""

    def __init__(self, max_lineas: int = 40, muestras_por_racha: int = 2) -> None:
        self._max_lineas = max_lineas
        self._muestras = muestras_por_racha

    def _firma(self, linea: str) -> str:
        """Normaliza una linea para detectar equivalencia: sin marca de tiempo ni numeros."""
        sin_ts = _TIMESTAMP.sub("", linea.strip())
        return _DIGITOS.sub("#", sin_ts)

    def _es_critica(self, linea: str) -> bool:
        minuscula = linea.lower()
        return any(clave in minuscula for clave in _CRITICAS)

    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult:
        lineas: List[str] = [ln for ln in output.splitlines() if ln.strip()]
        original = len(lineas)

        if original <= self._max_lineas:
            return TerminalPruneResult(
                original_lines=original,
                pruned_lines=original,
                exit_code=exit_code,
                clean_output="\n".join(lineas),
                reduction_ratio=0.0,
            )

        # 1. Colapsar rachas de lineas equivalentes.
        colapsadas: List[str] = []
        i = 0
        while i < len(lineas):
            firma = self._firma(lineas[i])
            j = i
            while j < len(lineas) and self._firma(lineas[j]) == firma:
                j += 1
            racha = j - i
            if racha > self._muestras:
                colapsadas.extend(lineas[i : i + self._muestras])
                colapsadas.append(f"    [... {racha - self._muestras} lineas equivalentes omitidas ...]")
            else:
                colapsadas.extend(lineas[i:j])
            i = j

        # 2. Colapso global por firma: un bucle de reinicio intercala varias lineas
        #    distintas (systemd[PID], systemd[1], ...), por lo que las equivalentes
        #    no quedan consecutivas y el paso anterior no las alcanza.
        conteo: dict = {}
        for linea in colapsadas:
            if not linea.startswith("    [..."):
                firma = self._firma(linea)
                conteo[firma] = conteo.get(firma, 0) + 1

        repetidas = {f for f, n in conteo.items() if n > self._muestras}
        if repetidas:
            emitidas: dict = {}
            global_colapsado: List[str] = []
            for linea in colapsadas:
                if linea.startswith("    [..."):
                    global_colapsado.append(linea)
                    continue
                firma = self._firma(linea)
                if firma not in repetidas:
                    global_colapsado.append(linea)
                    continue
                vistas = emitidas.get(firma, 0)
                if vistas < self._muestras:
                    emitidas[firma] = vistas + 1
                    global_colapsado.append(linea)
                elif vistas == self._muestras:
                    emitidas[firma] = vistas + 1
                    global_colapsado.append(
                        f"    [... {conteo[firma] - self._muestras} repeticiones mas de esta linea ...]"
                    )
            colapsadas = global_colapsado

        # 3. Si sigue excediendo, priorizar lineas criticas y el cierre.
        if len(colapsadas) > self._max_lineas:
            criticas = [ln for ln in colapsadas if self._es_critica(ln)]
            cola = colapsadas[-10:]
            vistas = set()
            seleccion: List[str] = []
            for linea in criticas[: self._max_lineas - 10] + cola:
                if linea not in vistas:
                    vistas.add(linea)
                    seleccion.append(linea)
            resultado = [
                f"[PODA REMOTA: {original} lineas reducidas a {len(seleccion)}]",
                *seleccion,
            ]
        else:
            resultado = [f"[PODA REMOTA: {original} lineas reducidas a {len(colapsadas)}]", *colapsadas]

        podadas = len(resultado)
        reduccion = max(0.0, round((original - podadas) / original, 4)) if original else 0.0

        return TerminalPruneResult(
            original_lines=original,
            pruned_lines=podadas,
            exit_code=exit_code,
            clean_output="\n".join(resultado),
            reduction_ratio=reduccion,
        )

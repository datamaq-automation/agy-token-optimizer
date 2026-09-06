"""Clasificación léxica de la CommandLine de un run_command, local o remota.

Análisis puramente léxico: no resuelve DNS, no abre sockets ni consulta el host remoto.
Corre dentro del presupuesto de 5 s del hook PreToolUse.
"""

import re
import shlex
from typing import List, Optional, Sequence

from src.domain.ports import (
    CommandClassification,
    CommandKind,
    CommandScope,
    ICodeFileInspector,
    ICommandClassifier,
)

# Extensiones cuya lectura completa justifica poda determinística.
CODE_EXTS = frozenset({".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".php", ".java", ".rb", ".c", ".h", ".cpp"})
DATA_EXTS = frozenset({".json", ".yaml", ".yml", ".toml", ".csv", ".xml", ".ini", ".cfg"})
PODABLE_EXTS = CODE_EXTS | DATA_EXTS

# Verbos que leen un archivo entero, sin acotar.
VERBOS_LECTURA_COMPLETA = frozenset({"cat", "less", "more", "bat"})

# Verbos de consulta y diagnóstico: salida podable, nunca mutan estado.
VERBOS_CONSULTA = frozenset(
    {
        "ls",
        "ll",
        "head",
        "tail",
        "grep",
        "rg",
        "find",
        "stat",
        "wc",
        "du",
        "df",
        "ps",
        "free",
        "uptime",
        "journalctl",
        "dmesg",
        "id",
        "whoami",
        "hostname",
        "uname",
        "env",
        "date",
        "which",
        "pwd",
        "sed",
        "awk",
        "cut",
        "sort",
        "uniq",
    }
)

# Binarios y comandos largos: exceden el timeout del ejecutor o producen salida no textual.
VERBOS_EXENTOS = frozenset(
    {
        "mysqldump",
        "pg_dump",
        "tar",
        "gzip",
        "gunzip",
        "zip",
        "unzip",
        "base64",
        "dd",
        "scp",
        "rsync",
        "curl",
        "wget",
        "apt",
        "apt-get",
        "dnf",
        "yum",
        "make",
        "cmake",
        "openssl",
    }
)

_EXENTO_COMPUESTOS = (
    re.compile(r"^docker\s+build\b"),
    re.compile(r"^npm\s+(ci|install|i)\b"),
    re.compile(r"^pip3?\s+install\b"),
    re.compile(r"^composer\s+(install|update)\b"),
)

_CONSULTA_COMPUESTOS = (
    re.compile(r"^systemctl\s+(status|is-active|is-enabled|list-units|show)\b"),
    re.compile(r"^docker\s+(ps|logs|inspect|images|stats)\b"),
    re.compile(r"^git\s+(status|log|diff|show|branch)\b"),
)

_SQL_LECTURA = re.compile(r"\b(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)\b", re.IGNORECASE)
_SQL_MUTACION_SIN_WHERE = re.compile(r"\b(DELETE\s+FROM|UPDATE|TRUNCATE|DROP)\b(?![\s\S]*\bWHERE\b)", re.IGNORECASE)

_MUTACION_PATRONES = (
    (re.compile(r"^systemctl\s+(stop|disable|restart|mask|kill)\b"), "detiene o altera un servicio"),
    (re.compile(r"^docker\s+(rm|rmi|down|stop|kill|prune)\b"), "destruye contenedores o imágenes"),
    (re.compile(r"^ufw\b"), "altera el firewall"),
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*\s+)*-?[a-zA-Z]*[rR][a-zA-Z]*f?[a-zA-Z]*\s+/(etc|opt|var|srv|home|usr)\b"),
        "borrado recursivo sobre una ruta de sistema",
    ),
    (re.compile(r"^(shutdown|reboot|halt|poweroff)\b"), "apaga o reinicia la máquina"),
    (re.compile(r"^(chown|chmod)\s+.*-R\b.*\s/(etc|var|srv|usr)\b"), "cambia permisos recursivos del sistema"),
)

# Redirección o heredoc: la salida se está guardando, jamás interponer un podador.
_REDIRECCION = re.compile(r"(?<![0-9<>])>>?(?!&)|\|\s*tee\b|<<-?\s*['\"]?\w+")
_HEREDOC = re.compile(r"<<-?\s*['\"]?\w+")
_SED_IN_PLACE = re.compile(r"\bsed\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*i\b")
_RANGO_SED = re.compile(r"-n\s*['\"]?\s*\d+\s*,\s*\d+\s*p")
_FLAG_ACOTADO = re.compile(r"-n\s*\d+|-c\s*\d+")

_SSH_TTY = re.compile(r"^ssh\s+(-\w+\s+)*-\w*t")

# Redirección de SALIDA a archivo. El lookbehind excluye '2>' y '1>&2': redirigir
# stderr no guarda la salida en ningún lado, así que no impide podar.
_REDIRECCION_SALIDA = re.compile(r"(?<![0-9<>&])>>?(?!&)|\|\s*tee\b")


def tiene_redireccion_de_salida(comando: str) -> bool:
    """True si el comando guarda su salida en un archivo.

    Interponer un podador en una línea así corrompería el archivo escrito, por lo
    que estas líneas nunca se reenrutan hacia el ejecutor podado.
    """
    return bool(_REDIRECCION_SALIDA.search(comando))


class LexicalCommandClassifier(ICommandClassifier):
    """Clasificador determinístico por análisis léxico de la línea de comando."""

    def __init__(
        self,
        inspector: ICodeFileInspector,
        known_hosts: Optional[Sequence[str]] = None,
        umbral_lineas: int = 100,
    ) -> None:
        self._inspector = inspector
        self._known_hosts = frozenset(known_hosts or ("vps", "vps4", "vps-tunnel"))
        self._umbral = umbral_lineas

    # ── Descomposición ────────────────────────────────────────────────────
    def _split_ssh(self, command_line: str) -> tuple[Optional[str], str, bool]:
        """Devuelve (alias, comando_interno, es_tty). alias None si la línea no es ssh conocido."""
        stripped = command_line.strip()
        if not re.match(r"^ssh\b", stripped):
            return None, stripped, False
        try:
            tokens = shlex.split(stripped)
        except ValueError:
            return None, stripped, False

        es_tty = bool(_SSH_TTY.match(stripped))
        alias: Optional[str] = None
        resto: List[str] = []
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith("-"):
                # Flags que consumen un valor.
                if tok in ("-p", "-i", "-o", "-l", "-F", "-J", "-b", "-c", "-m", "-w"):
                    i += 2
                    continue
                i += 1
                continue
            alias = tok
            resto = tokens[i + 1 :]
            break

        if alias is None or alias not in self._known_hosts:
            return None, stripped, es_tty
        return alias, " ".join(resto).strip(), es_tty

    def _verbo(self, comando: str) -> str:
        try:
            tokens = shlex.split(comando)
        except ValueError:
            tokens = comando.split()
        for tok in tokens:
            if "=" in tok and not tok.startswith("-") and not tok.startswith("/"):
                continue  # asignación de entorno previa al verbo
            return tok.split("/")[-1]
        return ""

    def _target_podable(self, comando: str) -> Optional[str]:
        """Primer argumento que apunta a un archivo con extensión podable."""
        try:
            tokens = shlex.split(comando)
        except ValueError:
            tokens = comando.split()
        for tok in tokens[1:]:
            if tok.startswith("-"):
                continue
            for ext in PODABLE_EXTS:
                if tok.endswith(ext):
                    return tok
        return None

    # ── Reglas ────────────────────────────────────────────────────────────
    def _es_exento(self, verbo: str, comando: str) -> bool:
        if verbo in VERBOS_EXENTOS:
            return True
        return any(pat.search(comando) for pat in _EXENTO_COMPUESTOS)

    def _es_escritura(self, verbo: str, comando: str) -> Optional[str]:
        """Devuelve la ruta escrita si el comando edita un archivo podable in situ."""
        if _SED_IN_PLACE.search(comando):
            return self._target_podable(comando)
        if _HEREDOC.search(comando) or _REDIRECCION.search(comando):
            if verbo in ("cat", "tee", "python3", "python", "printf", "echo"):
                destino = re.search(r">>?\s*([^\s;&|]+)", comando)
                if destino:
                    ruta = destino.group(1)
                    if any(ruta.endswith(ext) for ext in PODABLE_EXTS):
                        return ruta
        return None

    def _es_mutacion(self, comando: str) -> Optional[str]:
        for pat, motivo in _MUTACION_PATRONES:
            if pat.search(comando):
                return motivo
        if re.match(r"^(mysql|psql|mariadb)\b", comando) and _SQL_MUTACION_SIN_WHERE.search(comando):
            return "sentencia SQL destructiva sin cláusula WHERE"
        return None

    def _es_lectura_acotada(self, comando: str) -> bool:
        return bool(_RANGO_SED.search(comando) or _FLAG_ACOTADO.search(comando))

    def _es_consulta(self, verbo: str, comando: str) -> bool:
        if verbo in VERBOS_CONSULTA:
            return True
        if any(pat.search(comando) for pat in _CONSULTA_COMPUESTOS):
            return True
        if re.match(r"^(mysql|psql|mariadb)\b", comando) and _SQL_LECTURA.search(comando):
            return True
        return False

    # ── Punto de entrada ──────────────────────────────────────────────────
    def classify(self, command_line: str) -> Optional[CommandClassification]:
        if not command_line or not command_line.strip():
            return None

        alias, comando, es_tty = self._split_ssh(command_line)
        remoto = alias is not None
        scope = CommandScope.REMOTO if remoto else CommandScope.LOCAL

        def cl(kind: CommandKind, reason: str, target: Optional[str] = None) -> CommandClassification:
            return CommandClassification(
                scope=scope,
                kind=kind,
                inner_command=comando,
                reason=reason,
                target_path=target,
                host_alias=alias,
            )

        # Una línea ssh contra un host desconocido (github.com, etc.) no nos concierne.
        if re.match(r"^ssh\b", command_line.strip()) and not remoto:
            return None

        # 1. INTERACTIVO: sin comando o pidiendo TTY.
        if remoto and (not comando or es_tty):
            return cl(CommandKind.INTERACTIVO, "sesión interactiva o TTY solicitado")

        verbo = self._verbo(comando)

        # 2. EXENTO: binarios y comandos de larga duración.
        if self._es_exento(verbo, comando):
            return cl(CommandKind.EXENTO, f"verbo '{verbo}' es binario o de larga duración")

        # 3. ESCRITURA: edición in situ de un archivo podable.
        ruta_escrita = self._es_escritura(verbo, comando)
        if ruta_escrita:
            return cl(CommandKind.ESCRITURA, f"edita '{ruta_escrita}' in situ", ruta_escrita)

        # 4. MUTACION: altera estado del sistema.
        motivo = self._es_mutacion(comando)
        if motivo:
            return cl(CommandKind.MUTACION, motivo)

        # 5. LECTURA_CODIGO: lectura completa de un archivo podable, sin acotar.
        if verbo in VERBOS_LECTURA_COMPLETA and not _REDIRECCION.search(comando):
            ruta = self._target_podable(comando)
            if ruta and not self._es_lectura_acotada(comando):
                if remoto or self._inspector.excede_umbral(ruta, self._umbral):
                    return cl(CommandKind.LECTURA_CODIGO, f"lectura completa de '{ruta}'", ruta)

        # 6. CONSULTA: diagnóstico con salida podable. Si la salida se está
        #    guardando en un archivo, se deja pasar cruda: podarla lo corrompería.
        if self._es_consulta(verbo, comando):
            if tiene_redireccion_de_salida(comando):
                return cl(CommandKind.EXENTO, "la salida se redirige a un archivo")
            return cl(CommandKind.CONSULTA, f"verbo '{verbo}' es de consulta")

        return cl(CommandKind.EXENTO, "sin regla aplicable: se deja pasar tal cual")

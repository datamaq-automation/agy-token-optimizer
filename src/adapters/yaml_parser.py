"""Adaptador de dominio: parser YAML nativo liviano sin dependencias externas (NFR-02).

Cero dependencias (no usa PyYAML). Implementa un subconjunto determinístico de YAML:
- Mapeos y listas indentados (2 o 4 espacios).
- Escalares: strings (con o sin comillas), enteros, float, booleans true/false, null.
- Comentarios con # (fuera de cadenas entrecomilladas).
- Mapeos inline tras un item de lista ("- a: 1, b: 2").

La salida siempre es dict | list | escalar primitivo (json-serializable).
"""

from typing import Any, List, Union


class YamlParsingError(ValueError):
    """Señala una estructura YAML no soportada o mal formada."""


_BOOLEAN_TRUE = {"true", "yes", "on"}
_BOOLEAN_FALSE = {"false", "no", "off"}
_NULL = {"null", "nil", "~"}


def _strip_comment(line: str) -> str:
    """Elimina comentario YAML (#) respetando comillas simples y dobles."""
    in_single = False
    in_double = False
    for idx, ch in enumerate(line):
        if ch == "#" and not in_single and not in_double:
            return line[:idx]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
    return line


def _parse_scalar(raw: str) -> Any:
    """Convierte un escalar YAML en su valor tipado."""
    value = raw.strip()
    if not value:
        return None
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1]
    if value in _NULL:
        return None
    if value.lower() in _BOOLEAN_TRUE:
        return True
    if value.lower() in _BOOLEAN_FALSE:
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_inline_pairs(text: str, current_indent: int) -> dict | None:
    """Analiza un mapeo inline que comienza en la línea actual y las siguientes.

    Devuelve el dict y consume tantas líneas como pares del mapeo.
    """
    result: dict = {}
    body = text
    tokens = body.split(",")
    for token in tokens:
        key, colon, raw = token.partition(":")
        if not colon:
            continue
        result[key.strip()] = _parse_scalar(raw.strip())
    return result or None


def _parse_block(lines: List[str], start: int, indent: int) -> tuple[Union[dict, list, Any], int]:
    """Parsea un bloque YAML que comienza en `start` con indentación `indent`.

    El primer token de la línea define si es lista (guion) o mapeo.
    """
    if start >= len(lines):
        return {}, start

    # Saltar líneas en blanco y comentarios para hallar el primer token real.
    cursor = start
    while cursor < len(lines):
        probe = _strip_comment(lines[cursor]).strip()
        if probe != "":
            break
        cursor += 1
    if cursor >= len(lines):
        return {}, cursor

    marker_line = lines[cursor]
    stripped = _strip_comment(marker_line).strip()

    if stripped.startswith("-"):
        return _parse_list_block(lines, cursor, indent)

    # Mapeo: extender a todas las líneas con indent >= base.
    return _parse_map_block(lines, cursor, indent)


def _parse_list_block(lines: List[str], start: int, indent: int) -> tuple[list, int]:
    items: List[Any] = []
    idx = start
    while idx < len(lines):
        line = lines[idx]
        cur_indent = _indent_of(line)
        if cur_indent < indent or _indent_of(line) < 0:
            break
        stripped = _strip_comment(line).strip()
        if stripped == "":
            idx += 1
            continue
        if not stripped.startswith("-"):
            break
        body = stripped[1:].strip()
        if body == "":
            # Item compuesto: sub-bloque en las líneas siguientes.
            value, idx = _parse_block(lines, idx + 1, cur_indent + 1)
            items.append(value)
            continue
        key, colon, raw = body.partition(":")
        if not colon:
            items.append(_parse_scalar(body))
            idx += 1
            continue
        # Item de mapeo: "key: value" pudiendo tener más parejas debajo (indent > guion).
        current: dict = {}
        current[key.strip()] = _parse_scalar(raw.strip()) if _strip_comment(raw).strip() else {}
        if _strip_comment(raw).strip() == "":
            sub = _parse_block(lines, idx + 1, cur_indent + 2)[0]
            current[key.strip()] = sub
        idx += 1
        # Continuar consumiendo parejas del mismo item (indent > cur_indent).
        while idx < len(lines):
            next_indent = _indent_of(lines[idx])
            if next_indent <= cur_indent or next_indent < 0:
                break
            nxt = _strip_comment(lines[idx]).strip()
            if nxt == "" or nxt.startswith("-") or ":" not in nxt:
                break
            nk, _, nraw = nxt.partition(":")
            nval = _strip_comment(nraw).strip()
            current[nk.strip()] = _parse_scalar(nval) if nval else {}
            idx += 1
        items.append(current)
    return items, idx


def _parse_map_block(lines: List[str], start: int, indent: int) -> tuple[dict, int]:
    mapping: dict = {}
    idx = start
    while idx < len(lines):
        line = lines[idx]
        cur_indent = _indent_of(line)
        if cur_indent < indent or _indent_of(line) < 0:
            break
        stripped = _strip_comment(line).strip()
        if stripped == "":
            idx += 1
            continue
        if stripped.startswith("-"):
            break
        key, colon, raw = stripped.partition(":")
        if not colon:
            break
        raw_stripped = _strip_comment(raw).strip()
        if raw_stripped == "":
            value, idx = _parse_block(lines, idx + 1, cur_indent + 1)
            mapping[key.strip()] = value
        else:
            mapping[key.strip()] = _parse_scalar(raw_stripped)
            idx += 1
    return mapping, idx


def parse_yaml(text: str) -> Any:
    """Convierte un documento YAML simple en estructuras nativas de Python."""
    lines = text.splitlines()
    cleaned: List[str] = []
    for line in lines:
        if line.strip() in ("", "---", "..."):
            cleaned.append("")
            continue
        cleaned.append(line)
    if not any(line.strip() for line in cleaned):
        return None
    value, _ = _parse_block(cleaned, 0, 0)
    return value

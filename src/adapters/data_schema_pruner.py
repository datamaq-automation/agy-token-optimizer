"""Adaptador determinístico de esquematización y poda de archivos masivos de datos en CPU.

Convierte archivos masivos JSON, YAML y CSV en su firma estructural de tipos
más una muestra representativa de 2 elementos, reduciendo el contexto >= 90% a $0 tokens.
"""

import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

from src.domain.ports import DataSchemaResult, IDataSchemaPruner


class DataSchemaPruner(IDataSchemaPruner):
    """Implementación determinística de reducción estructural de datos."""

    def prune_data_file(self, file_path: str, content: Optional[str] = None) -> DataSchemaResult:
        if content is None:
            if not os.path.exists(file_path):
                return DataSchemaResult("unknown", 0, "Archivo no encontrado", 0.0)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        original_bytes = len(content.encode("utf-8"))
        _, ext = os.path.splitext(file_path)
        ext_clean = ext.lower().lstrip(".")

        if ext_clean == "json":
            return self._prune_json(content, original_bytes)
        elif ext_clean in {"yaml", "yml"}:
            return self._prune_yaml(content, original_bytes)
        elif ext_clean == "csv":
            return self._prune_csv(content, original_bytes)
        else:
            return DataSchemaResult(ext_clean or "unknown", 0, content, 0.0)

    def _prune_json(self, content: str, original_bytes: int) -> DataSchemaResult:
        try:
            data = json.loads(content)
        except Exception:
            return DataSchemaResult("json", 0, content, 0.0)

        total_records = 0
        summary_lines: List[str] = []

        if isinstance(data, list):
            total_records = len(data)
            if data and isinstance(data[0], dict):
                types_desc = [f"{k}: {type(v).__name__}" for k, v in data[0].items()]
                summary_lines.append(f"# Esquema JSON (Total registros: {total_records})")
                summary_lines.append(f"# Campos: {', '.join(types_desc)}")
                summary_lines.append("# Muestra representativa (primeros 2 registros):")
                summary_lines.append(json.dumps(data[:2], indent=2, ensure_ascii=False))
            else:
                summary_lines.append(f"# Array JSON de {total_records} elementos primitivos")
                summary_lines.append(json.dumps(data[:2], indent=2, ensure_ascii=False))
        elif isinstance(data, dict):
            # Buscar si alguna clave contiene una lista masiva
            total_records = len(data)
            summary_lines.append(f"# Objeto JSON con {total_records} claves principales")
            sampled_dict: Dict[str, Any] = {}
            for k, v in list(data.items())[:2]:
                if isinstance(v, list):
                    sampled_dict[k] = v[:2]
                    total_records = len(v)
                else:
                    sampled_dict[k] = v
            summary_lines.append(json.dumps(sampled_dict, indent=2, ensure_ascii=False))
            summary_lines.append(f"# [PODADO: claves o elementos restantes de {file_path_label(data)}]")

        schema_summary = "\n".join(summary_lines)
        compressed_bytes = len(schema_summary.encode("utf-8"))
        ratio = max(0.0, round((original_bytes - compressed_bytes) / original_bytes, 4)) if original_bytes > 0 else 0.0

        return DataSchemaResult(
            file_type="json",
            total_records=total_records,
            schema_summary=schema_summary,
            reduction_ratio=ratio,
        )

    def _prune_yaml(self, content: str, original_bytes: int) -> DataSchemaResult:
        lines = content.splitlines()
        total_records = len(lines)

        # Extraer primeras 15 líneas y resumir
        sampled_lines = lines[:15]
        sampled_lines.append(f"# [PODADO: {total_records - 15} líneas de configuración YAML restantes]")

        schema_summary = "\n".join(sampled_lines)
        compressed_bytes = len(schema_summary.encode("utf-8"))
        ratio = max(0.0, round((original_bytes - compressed_bytes) / original_bytes, 4)) if original_bytes > 0 else 0.0

        return DataSchemaResult(
            file_type="yaml",
            total_records=total_records,
            schema_summary=schema_summary,
            reduction_ratio=ratio,
        )

    def _prune_csv(self, content: str, original_bytes: int) -> DataSchemaResult:
        reader = csv.reader(io.StringIO(content))
        try:
            rows = list(reader)
        except Exception:
            return DataSchemaResult("csv", 0, content, 0.0)

        total_records = max(0, len(rows) - 1)
        if not rows:
            return DataSchemaResult("csv", 0, "", 0.0)

        header = rows[0]
        samples = rows[1:3]

        types_desc: List[str] = []
        if samples:
            for col_idx, col_name in enumerate(header):
                val = samples[0][col_idx] if col_idx < len(samples[0]) else ""
                inferred = "int" if val.isdigit() else "float" if is_float(val) else "str"
                types_desc.append(f"{col_name}: {inferred}")

        summary_lines = [
            f"# Esquema CSV (Total filas: {total_records})",
            f"# Columnas: {', '.join(types_desc or header)}",
            "# Muestra representativa (primeras 2 filas):",
            ",".join(header),
        ]
        for row in samples:
            summary_lines.append(",".join(row))
        summary_lines.append(f"# [PODADO: {max(0, total_records - 2)} filas restantes]")

        schema_summary = "\n".join(summary_lines)
        compressed_bytes = len(schema_summary.encode("utf-8"))
        ratio = max(0.0, round((original_bytes - compressed_bytes) / original_bytes, 4)) if original_bytes > 0 else 0.0

        return DataSchemaResult(
            file_type="csv",
            total_records=total_records,
            schema_summary=schema_summary,
            reduction_ratio=ratio,
        )


def file_path_label(data: Any) -> str:
    return f"{len(data)} elementos"


def is_float(val: str) -> bool:
    try:
        float(val)
        return True
    except ValueError:
        return False

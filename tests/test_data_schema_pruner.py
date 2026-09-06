"""Pruebas unitarias para Esquematizador de Archivos de Datos (JSON/YAML/CSV) - TDD."""

import json
import unittest

from src.adapters.data_schema_pruner import DataSchemaPruner
from src.domain.ports import DataSchemaResult


class TestDataSchemaPruner(unittest.TestCase):
    """Pruebas unitarias para la reducción estructural de archivos masivos de datos."""

    def setUp(self) -> None:
        self.pruner = DataSchemaPruner()

    def test_prune_large_json_dataset(self) -> None:
        """Verifica la conversión de un array JSON masivo en un esquema canónico con 2 muestras."""
        dataset = [
            {"id": i, "username": f"user_{i}", "email": f"user_{i}@corp.local", "is_admin": False} for i in range(250)
        ]
        raw_json = json.dumps(dataset, indent=2)

        result: DataSchemaResult = self.pruner.prune_data_file(file_path="users.json", content=raw_json)
        self.assertEqual(result.file_type, "json")
        self.assertEqual(result.total_records, 250)
        self.assertIn("username: str", result.schema_summary)
        self.assertIn("user_0", result.schema_summary)
        self.assertIn("user_1", result.schema_summary)
        self.assertNotIn("user_249", result.schema_summary)
        self.assertGreaterEqual(result.reduction_ratio, 0.90)

    def test_prune_complex_yaml_configuration(self) -> None:
        """Verifica la esquematización de archivos YAML extensos preservando claves estructurales."""
        raw_yaml = "\n".join(
            [f"service_{i}:\n  host: 10.0.0.{i}\n  port: {8000 + i}\n  timeout: 30s" for i in range(100)]
        )
        result: DataSchemaResult = self.pruner.prune_data_file(file_path="services.yaml", content=raw_yaml)
        self.assertEqual(result.file_type, "yaml")
        self.assertGreaterEqual(result.total_records, 100)
        self.assertIn("service_0", result.schema_summary)
        self.assertGreaterEqual(result.reduction_ratio, 0.85)

    def test_prune_csv_dataset(self) -> None:
        """Verifica la esquematización de CSV extrayendo cabeceras, tipos inferidos y muestras."""
        rows = ["id,product,price,in_stock"] + [f"{i},Item-{i},{19.99 + i},true" for i in range(300)]
        raw_csv = "\n".join(rows)

        result: DataSchemaResult = self.pruner.prune_data_file(file_path="products.csv", content=raw_csv)
        self.assertEqual(result.file_type, "csv")
        self.assertEqual(result.total_records, 300)
        self.assertIn("product: str", result.schema_summary)
        self.assertIn("Item-0", result.schema_summary)
        self.assertNotIn("Item-299", result.schema_summary)
        self.assertGreaterEqual(result.reduction_ratio, 0.90)

    def test_data_schema_reduction_ratio(self) -> None:
        """Verifica una reducción mínima del 90% en un JSON masivo de telemetría."""
        payload = {"metrics": [{"timestamp": f"2026-09-0{i}", "val": i * 1.5} for i in range(400)]}
        raw_json = json.dumps(payload)
        result: DataSchemaResult = self.pruner.prune_data_file(file_path="telemetry.json", content=raw_json)
        self.assertGreaterEqual(result.reduction_ratio, 0.90)


if __name__ == "__main__":
    unittest.main()

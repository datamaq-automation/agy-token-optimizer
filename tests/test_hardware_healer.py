"""Tests unitarios para IPostEditHealer y IHardwareOptimizer (Clean Architecture & TDD)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.adapters.hardware_healer import DeterministicHardwareHealer
from src.adapters.ramdisk_optimizer import RAMDiskOptimizer
from src.domain.ports import HealResult, RAMDiskStatus


class TestDeterministicHardwareHealer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.healer = DeterministicHardwareHealer()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_heal_python_file_with_unused_imports_and_bad_format(self) -> None:
        test_file = Path(self.temp_dir) / "dirty.py"
        # Código con imports no usados y mal formateado
        test_file.write_text(
            "import os\nimport sys\nimport math\n\ndef   add(a:int,b:int)->int:\n    return a+b\n",
            encoding="utf-8",
        )

        result: HealResult = self.healer.heal_file(str(test_file))

        self.assertTrue(result.success)
        self.assertEqual(result.file_path, str(test_file))
        self.assertGreaterEqual(result.execution_time_ms, 0.0)

        cleaned_content = test_file.read_text(encoding="utf-8")
        # Ruff check --fix debe haber eliminado los imports no usados
        self.assertNotIn("import math", cleaned_content)
        self.assertNotIn("import os", cleaned_content)
        self.assertNotIn("import sys", cleaned_content)
        # Ruff format debe haber normalizado la función
        self.assertIn("def add(a: int, b: int) -> int:", cleaned_content)


class TestRAMDiskOptimizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.optimizer = RAMDiskOptimizer(base_ramdisk="/dev/shm/agy-workspace-test")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree("/dev/shm/agy-workspace-test", ignore_errors=True)

    def test_sync_ramdisk_workspace(self) -> None:
        sample_file = Path(self.temp_dir) / "module.py"
        sample_file.write_text("print('test')", encoding="utf-8")

        status: RAMDiskStatus = self.optimizer.sync_ramdisk_workspace(self.temp_dir)

        self.assertTrue(status.mounted)
        self.assertGreaterEqual(status.synced_files, 1)
        self.assertTrue(os.path.exists(os.path.join(status.path, "module.py")))


if __name__ == "__main__":
    unittest.main()

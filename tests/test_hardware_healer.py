"""Tests unitarios para IPostEditHealer y IHardwareOptimizer (Clean Architecture & TDD)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.adapters.hardware_healer import DeterministicHardwareHealer
from src.adapters.ramdisk_optimizer import RAMDiskOptimizer
from src.domain.ports import HealResult, ISLMHealer, RAMDiskStatus, SLMHealResult


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
        if shutil.which("ruff"):
            # Ruff check --fix debe haber eliminado los imports no usados
            self.assertNotIn("import math", cleaned_content)
            self.assertNotIn("import os", cleaned_content)
            self.assertNotIn("import sys", cleaned_content)
            # Ruff format debe haber normalizado la función
            self.assertIn("def add(a: int, b: int) -> int:", cleaned_content)

    def test_heal_syntax_error_with_slm_healer(self) -> None:
        test_file = Path(self.temp_dir) / "broken_syntax.py"
        test_file.write_text("def broken(\n    return 42\n", encoding="utf-8")

        # Healer sin SLM debe fallar en ast_syntax_error
        res_no_slm = self.healer.heal_file(str(test_file))
        self.assertFalse(res_no_slm.success)
        self.assertIn("ast_syntax_error", res_no_slm.actions_applied)

        class MockSLMHealer(ISLMHealer):
            def repair_syntax(self, file_path: str, code: str, syntax_error: str) -> SLMHealResult:
                return SLMHealResult(
                    success=True,
                    file_path=file_path,
                    repaired_code="def broken() -> int:\n    return 42\n",
                    tokens_used=15,
                    execution_time_ms=12.5,
                )

        healer_with_slm = DeterministicHardwareHealer(slm_healer=MockSLMHealer())
        res_slm = healer_with_slm.heal_file(str(test_file))
        self.assertTrue(res_slm.success)
        self.assertIn("slm_igpu_healed", res_slm.actions_applied)

        repaired_content = test_file.read_text(encoding="utf-8")
        self.assertIn("def broken() -> int:", repaired_content)


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

        with patch.object(self.optimizer.auditor, "audit") as mock_audit:
            from src.domain.ports import HardwareSpecs, HardwareTier
            mock_audit.return_value = HardwareSpecs(
                cpu_cores=4, cpu_threads=4, has_avx2=True, total_ram_gb=16.0,
                available_ram_mb=8000.0, has_vulkan=True, shm_available=True,
                tier=HardwareTier.FULL_LOCAL, max_workers=4, allow_local_slm=True,
                allow_ramdisk_workspace=True, allow_simd_vectors=True
            )
            status: RAMDiskStatus = self.optimizer.sync_ramdisk_workspace(self.temp_dir)

            self.assertTrue(status.mounted)
            self.assertGreaterEqual(status.synced_files, 1)
            self.assertTrue(os.path.exists(os.path.join(status.path, "module.py")))


if __name__ == "__main__":
    unittest.main()

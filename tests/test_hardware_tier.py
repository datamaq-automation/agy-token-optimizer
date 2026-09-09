#!/usr/bin/env python3
"""tests/test_hardware_tier.py: Suite de pruebas TDD para detección dinámica de hardware (TC-06).

Verifica la clasificación adaptativa entre FULL_LOCAL (Desktop) y CONSTRAINED (Laptop)
según memoria RAM, flags AVX2 y concurrencia máxima de núcleos.
"""

import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from src.domain.ports import HardwareSpecs, HardwareTier


class TestHardwareTierDetection(unittest.TestCase):
    """Casos de prueba para el clasificador de perfiles de hardware adaptativo."""

    def test_domain_entity_defaults(self):
        """Verifica la inmutabilidad y valores de la entidad HardwareSpecs."""
        specs = HardwareSpecs(
            cpu_cores=2,
            cpu_threads=2,
            has_avx2=False,
            total_ram_gb=1.8,
            available_ram_mb=400.0,
            has_vulkan=False,
            shm_available=True,
            tier=HardwareTier.CONSTRAINED,
            max_workers=2,
            allow_local_slm=False,
            allow_ramdisk_workspace=False,
            allow_simd_vectors=False,
        )
        self.assertEqual(specs.tier, HardwareTier.CONSTRAINED)
        self.assertFalse(specs.allow_local_slm)
        self.assertFalse(specs.allow_ramdisk_workspace)
        self.assertEqual(specs.max_workers, 2)

    @patch("subprocess.run")
    @patch("pathlib.Path.is_dir", return_value=True)
    def test_constrained_tier_laptop_detection(self, mock_is_dir, mock_run):
        """Simula Intel Celeron N4000 (2 cores, no AVX2, 1.8 GiB RAM) -> CONSTRAINED."""
        from src.adapters.hardware_tier_detector import HardwareTierDetector

        cpuinfo_data = "processor : 0\nmodel name : Intel Celeron N4000\nflags : fpu vme sse4_2\n\nprocessor : 1\nmodel name : Intel Celeron N4000\nflags : fpu vme sse4_2\n"
        meminfo_data = "MemTotal:        1887436 kB\nMemFree:           70656 kB\nMemAvailable:     416768 kB\n"

        mock_run.return_value.returncode = 1  # vulkaninfo no disponible

        with patch("builtins.open", mock_open(read_data=cpuinfo_data)) as m_open:
            m_open.side_effect = [
                mock_open(read_data=cpuinfo_data).return_value,
                mock_open(read_data=meminfo_data).return_value,
            ]
            detector = HardwareTierDetector(cache_file=Path("/tmp/test_hw_cache_laptop.json"))
            specs = detector.audit()

            self.assertEqual(specs.tier, HardwareTier.CONSTRAINED)
            self.assertFalse(specs.has_avx2)
            self.assertLess(specs.total_ram_gb, 4.0)
            self.assertFalse(specs.allow_local_slm)
            self.assertFalse(specs.allow_ramdisk_workspace)
            self.assertLessEqual(specs.max_workers, 2)

    @patch("subprocess.run")
    @patch("pathlib.Path.is_dir", return_value=True)
    def test_full_local_tier_desktop_detection(self, mock_is_dir, mock_run):
        """Simula AMD Ryzen (8 threads, AVX2, 18 GiB RAM) -> FULL_LOCAL."""
        from src.adapters.hardware_tier_detector import HardwareTierDetector

        cpuinfo_data = "processor : 0\nflags : fpu vme avx2\n" * 8
        meminfo_data = "MemTotal:       18874368 kB\nMemFree:         8000000 kB\nMemAvailable:   12000000 kB\n"

        mock_run.return_value.returncode = 0  # vulkaninfo disponible

        with patch("builtins.open", mock_open(read_data=cpuinfo_data)) as m_open:
            m_open.side_effect = [
                mock_open(read_data=cpuinfo_data).return_value,
                mock_open(read_data=meminfo_data).return_value,
            ]
            detector = HardwareTierDetector(cache_file=Path("/tmp/test_hw_cache_desktop.json"))
            specs = detector.audit()

            self.assertEqual(specs.tier, HardwareTier.FULL_LOCAL)
            self.assertTrue(specs.has_avx2)
            self.assertGreaterEqual(specs.total_ram_gb, 8.0)
            self.assertTrue(specs.allow_local_slm)
            self.assertTrue(specs.allow_ramdisk_workspace)
            self.assertGreaterEqual(specs.max_workers, 4)


if __name__ == "__main__":
    unittest.main()

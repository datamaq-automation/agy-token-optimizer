"""Adaptador determinístico de auditoría de hardware local (HardwareTierDetector).

Audita procesador, instrucciones SIMD, memoria RAM y Vulkan para asignar el tier adaptativo
(FULL_LOCAL para Desktop vs CONSTRAINED para Laptop).
"""

import json
import multiprocessing
import os
import subprocess
from pathlib import Path
from typing import Optional

from src.domain.ports import HardwareSpecs, HardwareTier, IHardwareAuditor


class HardwareTierDetector(IHardwareAuditor):
    """Implementación canónica de auditoría y clasificación adaptativa de hardware."""

    def __init__(self, cache_file: Optional[Path] = None) -> None:
        self.cache_file = cache_file or (Path.home() / ".agents" / "hardware_profile.json")

    def audit(self) -> HardwareSpecs:
        cpu_threads = multiprocessing.cpu_count() or 1
        has_avx2 = False

        # 1. Auditoría de CPU en /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                content = f.read()
                proc_count = content.lower().count("processor\t:") or content.lower().count("processor :")
                if proc_count > 0:
                    cpu_threads = proc_count
                if "avx2" in content.lower():
                    has_avx2 = True
        except OSError:
            pass
        cpu_cores = cpu_threads

        # 2. Auditoría de Memoria RAM en /proc/meminfo
        total_ram_gb = 0.0
        available_ram_mb = 0.0
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "MemTotal:" in line:
                        total_ram_gb = int(line.split()[1]) / (1024 * 1024)
                    elif "MemAvailable:" in line:
                        available_ram_mb = int(line.split()[1]) / 1024
        except OSError:
            pass

        # 3. Disponibilidad de /dev/shm
        shm_available = Path("/dev/shm").is_dir()

        # 4. Chequeo de aceleración Vulkan
        has_vulkan = False
        try:
            res = subprocess.run(["which", "vulkaninfo"], capture_output=True, check=False)
            if res.returncode == 0:
                has_vulkan = True
        except (OSError, ValueError):
            pass

        # 5. Determinación de Tier y Reglas Derivadas
        if total_ram_gb < 4.0 or not has_avx2:
            tier = HardwareTier.CONSTRAINED
            max_workers = min(2, cpu_threads)
            allow_local_slm = False
            allow_ramdisk_workspace = False
            allow_simd_vectors = False
        else:
            tier = HardwareTier.FULL_LOCAL
            max_workers = max(1, cpu_threads)
            allow_local_slm = True
            allow_ramdisk_workspace = True
            allow_simd_vectors = True

        specs = HardwareSpecs(
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            has_avx2=has_avx2,
            total_ram_gb=round(total_ram_gb, 2),
            available_ram_mb=round(available_ram_mb, 2),
            has_vulkan=has_vulkan,
            shm_available=shm_available,
            tier=tier,
            max_workers=max_workers,
            allow_local_slm=allow_local_slm,
            allow_ramdisk_workspace=allow_ramdisk_workspace,
            allow_simd_vectors=allow_simd_vectors,
        )

        self._save_cache(specs)
        return specs

    def _save_cache(self, specs: HardwareSpecs) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "cpu_cores": specs.cpu_cores,
                "cpu_threads": specs.cpu_threads,
                "has_avx2": specs.has_avx2,
                "total_ram_gb": specs.total_ram_gb,
                "available_ram_mb": specs.available_ram_mb,
                "has_vulkan": specs.has_vulkan,
                "shm_available": specs.shm_available,
                "tier": specs.tier.value,
                "max_workers": specs.max_workers,
                "allow_local_slm": specs.allow_local_slm,
                "allow_ramdisk_workspace": specs.allow_ramdisk_workspace,
                "allow_simd_vectors": specs.allow_simd_vectors,
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

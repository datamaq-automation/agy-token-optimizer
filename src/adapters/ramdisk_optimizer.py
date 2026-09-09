"""Adaptador para gestión y aceleración de workspaces en RAMDisk (/dev/shm).

Permite clonar y sincronizar repositorios a memoria RAM compartida a 15 GB/s
para ejecutar linters y suites de tests con cero latencia de disco.
"""

import os
import shutil
from pathlib import Path

from src.adapters.hardware_tier_detector import HardwareTierDetector
from src.domain.ports import IHardwareOptimizer, RAMDiskStatus


class RAMDiskOptimizer(IHardwareOptimizer):
    """Implementación de aceleración de workspace sobre tmpfs /dev/shm."""

    def __init__(self, base_ramdisk: str = "/dev/shm/agy-workspace") -> None:
        self.base_ramdisk = Path(base_ramdisk)
        self.exclude_dirs = {
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            ".ruff_cache",
            ".agents",
        }
        self.auditor = HardwareTierDetector()

    def sync_ramdisk_workspace(self, repo_dir: str) -> RAMDiskStatus:
        src_path = Path(repo_dir).resolve()
        specs = self.auditor.audit()

        # Si el hardware no permite RAMDisk (Laptop/memoria reducida), operar in-place sobre el disco local
        if not specs.allow_ramdisk_workspace:
            return RAMDiskStatus(
                mounted=False,
                path=str(src_path),
                available_mb=specs.available_ram_mb,
                synced_files=0,
            )

        target_workspace = self.base_ramdisk / src_path.name
        target_workspace.mkdir(parents=True, exist_ok=True)

        file_tasks: list[tuple[Path, Path]] = []

        for root, dirs, files in os.walk(src_path):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            rel_path = Path(root).relative_to(src_path)
            dest_dir = target_workspace / rel_path
            dest_dir.mkdir(parents=True, exist_ok=True)

            for filename in files:
                src_file = Path(root) / filename
                dest_file = dest_dir / filename
                file_tasks.append((src_file, dest_file))

        def _copy_if_needed(task: tuple[Path, Path]) -> bool:
            s_file, d_file = task
            try:
                if not d_file.exists() or s_file.stat().st_mtime > d_file.stat().st_mtime:
                    shutil.copy2(s_file, d_file)
                    return True
            except (OSError, PermissionError):
                pass
            return False

        # Concurrencia adaptativa basada en el tier de hardware
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=specs.max_workers) as executor:
            results = list(executor.map(_copy_if_needed, file_tasks))
            synced_files = sum(1 for r in results if r)

        # Medir espacio disponible en el punto de montaje
        try:
            stat = os.statvfs(str(self.base_ramdisk))
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            mounted = True
        except (OSError, FileNotFoundError):
            available_mb = 0.0
            mounted = False

        return RAMDiskStatus(
            mounted=mounted,
            path=str(target_workspace),
            available_mb=round(available_mb, 2),
            synced_files=synced_files,
        )

#!/usr/bin/env python3
"""tests/test_client_tools.py: Suite de pruebas TDD para herramientas de cliente ligero (TC-58).

Verifica la compilación HTML enriquecida con KaTeX y Mermaid, así como
la integridad sintáctica de scripts de montaje FUSE y unidades systemd.
"""

import subprocess
import unittest
from pathlib import Path


class TestClientTools(unittest.TestCase):
    """Pruebas unitarias para las herramientas cliente de visualización y montaje."""

    def setUp(self) -> None:
        self.root_dir = Path(__file__).resolve().parent.parent
        self.client_tools_dir = self.root_dir / "tools" / "client"
        self.systemd_dir = self.root_dir / "config" / "systemd"
        self.desktop_dir = self.root_dir / "config" / "desktop"

    def test_client_scripts_exist_and_executable(self) -> None:
        """Verifica existencia y permisos de ejecución en scripts cliente."""
        agy_preview = self.client_tools_dir / "agy-preview"
        agy_mount = self.client_tools_dir / "agy-mount"
        agy_unmount = self.client_tools_dir / "agy-unmount"

        self.assertTrue(agy_preview.is_file(), "agy-preview no existe")
        self.assertTrue(agy_mount.is_file(), "agy-mount no existe")
        self.assertTrue(agy_unmount.is_file(), "agy-unmount no existe")

        for script in (agy_preview, agy_mount, agy_unmount):
            self.assertTrue(
                script.stat().st_mode & 0o111 != 0,
                f"{script.name} debe tener permisos de ejecución",
            )

    def test_bash_scripts_syntax(self) -> None:
        """Verifica que los scripts bash no contengan errores de sintaxis."""
        for name in ("agy-mount", "agy-unmount"):
            script_path = self.client_tools_dir / name
            res = subprocess.run(
                ["bash", "-n", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                res.returncode,
                0,
                f"Error de sintaxis en {name}: {res.stderr}",
            )

    def test_systemd_unit_structure(self) -> None:
        """Verifica que la unidad systemd defina los bloques requeridos."""
        service_file = self.systemd_dir / "agy-mount-brain.service"
        self.assertTrue(service_file.is_file(), "agy-mount-brain.service no existe")
        content = service_file.read_text(encoding="utf-8")
        self.assertIn("[Unit]", content)
        self.assertIn("[Service]", content)
        self.assertIn("sshfs", content)
        self.assertIn("fusermount", content)

    def test_desktop_entry_structure(self) -> None:
        """Verifica la validez básica de la entrada .desktop."""
        desktop_file = self.desktop_dir / "agy-preview.desktop"
        self.assertTrue(desktop_file.is_file(), "agy-preview.desktop no existe")
        content = desktop_file.read_text(encoding="utf-8")
        self.assertIn("[Desktop Entry]", content)
        self.assertIn("Exec=", content)
        self.assertIn("text/markdown", content)

    def test_agy_preview_generation_katex_and_mermaid(self) -> None:
        """Verifica que agy-preview compile Markdown con KaTeX y Mermaid."""
        preview_script = self.client_tools_dir / "agy-preview"
        sample_md = Path("/tmp/test_unit_preview.md")
        sample_md.write_text(
            "# Test\n"
            "$E_{\\text{esperada}} = E_0 + \\beta_1 \\cdot \\text{metros}$\n\n"
            "```mermaid\ngraph TD\nA --> B\n```\n",
            encoding="utf-8",
        )

        res = subprocess.run(
            [str(preview_script), str(sample_md)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, f"Error ejecutando agy-preview: {res.stderr}")

        # Comprobar que el HTML generado contiene KaTeX y Mermaid
        html_files = list(Path("/tmp").glob("agy-preview-*.html"))
        self.assertTrue(len(html_files) > 0, "No se generó el HTML de vista previa")
        latest_html = max(html_files, key=lambda p: p.stat().st_mtime)
        content = latest_html.read_text(encoding="utf-8")

        self.assertIn("katex.min.css", content)
        self.assertIn("mermaid.min.js", content)
        self.assertIn('<div class="mermaid">', content)
        self.assertIn("$E_{\\text{esperada}}", content)


if __name__ == "__main__":
    unittest.main()

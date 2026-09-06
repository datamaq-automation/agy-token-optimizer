"""Adaptador de compresión y poda determinística de Git diffs en hardware local (CPU AVX2).

Elimina lockfiles gigantes (package-lock.json, poetry.lock, Cargo.lock), archivos minificados
y ruido de formato antes de que el contenido llegue al contexto del LLM remoto.
"""

import re
from typing import List, Tuple

from src.domain.ports import DiffCompressionResult, IDiffCompressor


class RegexDiffCompressor(IDiffCompressor):
    """Implementación de poda determinística basada en expresiones regulares compiladas."""

    # Patrones de archivos reconocidos como ruido o artefactos de dependencias
    NOISY_FILE_PATTERNS = [
        re.compile(
            r"(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock|Cargo\.lock|composer\.lock|go\.sum|flake\.lock)$",
            re.IGNORECASE,
        ),
        re.compile(r"(\.min\.js|\.min\.css|\.bundle\.js|\.map|\.svg)$", re.IGNORECASE),
    ]

    def _is_noisy_file(self, file_path: str) -> bool:
        """Determina si una ruta corresponde a un lockfile o archivo de ruido de dependencias."""
        clean_path = file_path.strip().split()[-1] if file_path else ""
        return any(pattern.search(clean_path) for pattern in self.NOISY_FILE_PATTERNS)

    def _split_diff_blocks(self, diff_content: str) -> List[Tuple[str, str]]:
        """Divide el contenido del diff en tuplas (encabezado_archivo, cuerpo_diff)."""
        if not diff_content.strip():
            return []

        # Particionar por 'diff --git '
        chunks = re.split(r"(?=diff --git )", diff_content)
        blocks: List[Tuple[str, str]] = []

        for chunk in chunks:
            if not chunk.strip():
                continue
            lines = chunk.splitlines(keepends=True)
            header = lines[0] if lines else ""
            body = "".join(lines[1:]) if len(lines) > 1 else ""
            blocks.append((header, body))

        return blocks

    def compress_diff(self, diff_content: str, max_noise_lines: int = 500) -> DiffCompressionResult:
        """Filtra lockfiles y ruido manteniendo intacto el código fuente."""
        if not diff_content or not diff_content.strip():
            return DiffCompressionResult(
                original_bytes=0,
                compressed_bytes=0,
                reduction_ratio=0.0,
                clean_diff="",
            )

        original_bytes = len(diff_content.encode("utf-8"))
        blocks = self._split_diff_blocks(diff_content)

        compressed_parts: List[str] = []

        for header, body in blocks:
            # Extraer ruta del archivo del header 'diff --git a/foo b/foo'
            file_match = re.search(r"diff --git a/(.*?) b/(.*)", header)
            target_path = file_match.group(2) if file_match else header

            if self._is_noisy_file(target_path):
                body_lines = body.splitlines()
                lines_count = len(body_lines)
                # Resumir el diff del lockfile sin incluir el payload masivo
                summary_marker = (
                    f"{header}"
                    f"--- a/{target_path}\n"
                    f"+++ b/{target_path}\n"
                    f"@@ ... @@\n"
                    f"[PODADO: diff de {lines_count} líneas en {target_path} por optimizador local]\n"
                )
                compressed_parts.append(summary_marker)
            else:
                # Código fuente regular: preservar intacto
                compressed_parts.append(f"{header}{body}")

        clean_diff = "".join(compressed_parts)
        compressed_bytes = len(clean_diff.encode("utf-8"))

        if original_bytes > 0:
            reduction = (original_bytes - compressed_bytes) / original_bytes
            reduction_ratio = max(0.0, round(reduction, 4))
        else:
            reduction_ratio = 0.0

        return DiffCompressionResult(
            original_bytes=original_bytes,
            compressed_bytes=compressed_bytes,
            reduction_ratio=reduction_ratio,
            clean_diff=clean_diff,
        )

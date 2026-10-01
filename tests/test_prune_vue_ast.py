"""Pruebas unitarias para el podador determinista de Vue 3 SFC (prune_vue_ast.js)."""

import os
import subprocess
import tempfile
import unittest


class TestPruneVueAst(unittest.TestCase):
    """Verifica la poda en hardware local de componentes Vue 3 SFC con Node.js."""

    SCRIPT_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "skills",
            "token-optimizer",
            "scripts",
            "prune_vue_ast.js",
        )
    )

    def test_script_exists_and_is_executable(self) -> None:
        """Verifica que el script exista y tenga permisos de ejecución."""
        self.assertTrue(os.path.isfile(self.SCRIPT_PATH))
        self.assertTrue(os.access(self.SCRIPT_PATH, os.X_OK))

    def test_prune_vue_sfc_contract_extraction(self) -> None:
        """Verifica que se extraigan las macros defineProps, defineEmits y firmas sin cuerpo."""
        sfc_content = """<script setup lang="ts">
import type { UserRole } from './roles';

interface Props {
  userId: string;
  role?: UserRole;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update', id: string): void;
  (e: 'delete'): void;
}>();

const counter = ref<number>(0);

function submitForm(event: Event): boolean {
  console.log('Very long implementation here that wastes tokens');
  return true;
}

const formatName = (first: string, last: string): string => {
  return `${first} ${last}`.trim();
};
</script>

<template>
  <div class="user-card-massive-markup-full-of-tailwind-classes">
    <header>
      <slot name="header" />
    </header>
    <main>
      <slot />
      <BaseBadge :role="props.role" />
      <UserAvatar :id="props.userId" />
    </main>
  </div>
</template>

<style scoped>
.user-card-massive-markup-full-of-tailwind-classes {
  color: red;
  margin: 10px;
}
</style>
"""
        with tempfile.NamedTemporaryFile("w", suffix=".vue", delete=False) as tmp:
            tmp.write(sfc_content)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["node", self.SCRIPT_PATH, tmp_path],
                capture_output=True,
                text=True,
                check=True,
            )
            output = result.stdout

            # Contratos esenciales preservados
            self.assertIn('<script setup lang="ts">', output)
            self.assertIn("interface Props", output)
            self.assertIn("defineProps", output)
            self.assertIn("defineEmits", output)
            self.assertIn("submitForm(event: Event): boolean { ... }", output)
            self.assertIn("const formatName = (first: string, last: string): string => { ... }", output)

            # Reducción de ruido en template
            self.assertIn("<!-- [TEMPLATE PODADO] -->", output)
            self.assertIn("header", output)
            self.assertIn("default", output)
            self.assertIn("BaseBadge", output)
            self.assertIn("UserAvatar", output)
            self.assertNotIn("user-card-massive-markup-full-of-tailwind-classes", output)

            # Reducción de estilos
            self.assertIn("<style scoped> /* [ESTILOS CSS PODADOS] */ </style>", output)
            self.assertNotIn("color: red;", output)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_file_not_found_returns_error_code(self) -> None:
        """Verifica que un archivo inexistente retorne código de salida no nulo."""
        result = subprocess.run(
            ["node", self.SCRIPT_PATH, "/nonexistent/fake_component.vue"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error: Archivo no encontrado", result.stderr)


if __name__ == "__main__":
    unittest.main()

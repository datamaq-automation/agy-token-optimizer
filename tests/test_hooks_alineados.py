"""Pruebas de alineación de los hooks versionados con las reglas globales vigentes."""

import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_DIR = os.path.join(REPO_ROOT, "hooks")
CONFIG = os.path.join(REPO_ROOT, "config", "hooks.json")


class TestHooksAlineados(unittest.TestCase):
    """Escenario 18: el pegamento no debe contradecir a ~/.gemini/config/rules/."""

    def _archivos_hook(self) -> list:
        return [f for f in os.listdir(HOOKS_DIR) if f.endswith(".py")]

    def test_ningun_hook_deriva_a_opencode(self) -> None:
        """sdd_gate.md fija 'Claude Code planifica, AGY construye': el usuario no usa OpenCode."""
        infractores = []
        for nombre in self._archivos_hook():
            with open(os.path.join(HOOKS_DIR, nombre), "r", encoding="utf-8") as handle:
                contenido = handle.read()
            if "OpenCode" in contenido or "opencode" in contenido.replace(".opencode", ""):
                infractores.append(nombre)
        self.assertEqual(infractores, [], f"Hooks que aun derivan a OpenCode: {infractores}")

    def test_los_hooks_esperados_estan_versionados(self) -> None:
        """Sin esto, el pegamento de mayor apalancamiento queda sin test ni historial."""
        esperados = {
            "agy_mode.py",
            "gate_ast_pruner_interceptor.py",
            "gate_build_blocker.py",
            "gate_diff_compressor_interceptor.py",
            "gate_post_edit_healer.py",
            "gate_pre_invocation.py",
            "gate_remote_router.py",
            "gate_spec_auditor.py",
        }
        self.assertTrue(esperados.issubset(set(self._archivos_hook())))

    def test_hooks_json_es_valido_y_registra_el_router(self) -> None:
        with open(CONFIG, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
        comandos = []
        for grupo in cfg["security-hard-gate"]["PreToolUse"]:
            for hook in grupo["hooks"]:
                comandos.append(hook["command"])
        self.assertTrue(
            any("gate_remote_router.py" in c for c in comandos),
            "El router de comandos remotos no esta registrado en PreToolUse.",
        )

    def test_todo_hook_registrado_existe_en_disco(self) -> None:
        """Un command apuntando a un archivo inexistente falla silenciosamente en produccion."""
        with open(CONFIG, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
        faltantes = []
        for evento, grupos in cfg["security-hard-gate"].items():
            if evento == "enabled":
                continue
            iterable = grupos if evento == "PreInvocation" else [h for g in grupos for h in g["hooks"]]
            for hook in iterable:
                nombre = os.path.basename(hook["command"].split()[-1])
                if not os.path.isfile(os.path.join(HOOKS_DIR, nombre)):
                    faltantes.append(nombre)
        self.assertEqual(faltantes, [], f"Hooks referenciados que no existen: {faltantes}")


if __name__ == "__main__":
    unittest.main()

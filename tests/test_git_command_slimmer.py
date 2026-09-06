"""Pruebas del slimmer de comandos git/gh: poda en el origen."""

import unittest

from src.adapters.git_command_slimmer import slim


class TestSlimmer(unittest.TestCase):
    """Medido en el repo: 'git status' gasta ~90 tokens y '-sb' ~9; 'git log -5' ~1570 y '--oneline' ~95."""

    def test_git_status_pelado_se_densifica(self) -> None:
        self.assertEqual(slim("git status"), "git status --short --branch")

    def test_git_status_con_flags_no_se_toca(self) -> None:
        """Si el agente pidió un formato, sabe lo que quiere."""
        self.assertIsNone(slim("git status --porcelain=v2"))
        self.assertIsNone(slim("git status -sb"))

    def test_git_log_sin_acotar_se_acota(self) -> None:
        self.assertEqual(slim("git log"), "git log --oneline -n 20")

    def test_git_log_ya_formateado_no_se_toca(self) -> None:
        for cmd in ("git log --oneline -5", "git log -p", "git log --stat", "git log --format=%H", "git log -3"):
            self.assertIsNone(slim(cmd), cmd)

    def test_git_log_conserva_argumentos_del_usuario(self) -> None:
        self.assertEqual(slim("git log -- src/"), "git log --oneline -n 20 -- src/")

    def test_gh_run_list_se_acota(self) -> None:
        self.assertEqual(slim("gh run list"), "gh run list -L 10")
        self.assertIsNone(slim("gh run list -L 3"))
        self.assertIsNone(slim("gh run list --json status"))

    def test_gh_pr_list_se_acota(self) -> None:
        self.assertEqual(slim("gh pr list"), "gh pr list -L 10")

    def test_linea_compuesta_nunca_se_reescribe(self) -> None:
        """Reescribir dentro de una composición podría alterar lo que viene después."""
        for cmd in ("git status && git add .", "git log | head -5", "git status > /tmp/s.txt", "git log; echo fin"):
            self.assertIsNone(slim(cmd), cmd)

    def test_comandos_ajenos_se_ignoran(self) -> None:
        for cmd in ("git diff", "git commit -m x", "ls -la", "", "gh auth status"):
            self.assertIsNone(slim(cmd), cmd)


if __name__ == "__main__":
    unittest.main()

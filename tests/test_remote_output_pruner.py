"""Pruebas del podador de salidas remotas: rachas repetidas y acotado de volumen."""

import unittest

from src.adapters.remote_output_pruner import RemoteOutputPruner


class TestPodadorRemoto(unittest.TestCase):
    """El patron dominante en logs remotos son lineas casi identicas en bucle."""

    def setUp(self) -> None:
        self.pruner = RemoteOutputPruner(max_lineas=40)

    def test_salida_corta_pasa_intacta(self) -> None:
        salida = "linea a\nlinea b\nlinea c"
        res = self.pruner.prune_output("uptime", salida)
        self.assertEqual(res.reduction_ratio, 0.0)
        self.assertEqual(res.clean_output, salida)

    def test_colapsa_bucle_de_reinicio(self) -> None:
        """Caso real: un servicio que falla en ciclo genera cientos de lineas equivalentes."""
        plantilla = (
            "sep 06 19:3{n}:54 vps systemd[44280{n}]: svc.service: Failed at step EXEC "
            "spawning /root/x.sh: No such file or directory"
        )
        salida = "\n".join(plantilla.format(n=i % 10) for i in range(200))
        res = self.pruner.prune_output("journalctl -n 200", salida)
        self.assertEqual(res.original_lines, 200)
        self.assertLess(res.pruned_lines, 20)
        self.assertGreater(res.reduction_ratio, 0.9)
        self.assertIn("equivalentes omitidas", res.clean_output)

    def test_lineas_distintas_no_se_colapsan_entre_si(self) -> None:
        """Solo se colapsan rachas equivalentes: informacion distinta se conserva."""
        salida = "\n".join(f"servicio-{i} en estado unico {i * 7}" for i in range(60))
        res = self.pruner.prune_output("systemctl list-units", salida)
        self.assertLessEqual(res.pruned_lines, 41)
        self.assertEqual(res.original_lines, 60)

    def test_colapsa_bucle_intercalado(self) -> None:
        """Caso real del VPS: el ciclo alterna systemd[PID] y systemd[1].

        Las lineas equivalentes no quedan consecutivas, asi que el colapso por
        rachas no las alcanza y hace falta el colapso global por firma.
        """
        ciclo = [
            "sep 06 19:40:0{n} vps systemd[44306{n}]: svc.service: Failed to execute command",
            "sep 06 19:40:0{n} vps systemd[44306{n}]: svc.service: Failed at step EXEC spawning /root/x.sh",
            "sep 06 19:40:0{n} vps systemd[1]: svc.service: Failed with result 'exit-code'.",
        ]
        salida = "\n".join(linea.format(n=i % 10) for i in range(70) for linea in ciclo)
        res = self.pruner.prune_output("journalctl -n 200", salida)
        self.assertGreater(res.reduction_ratio, 0.9)
        self.assertIn("repeticiones mas de esta linea", res.clean_output)
        self.assertLess(res.pruned_lines, 15)

    def test_preserva_el_exit_code(self) -> None:
        """La poda nunca enmascara un fallo."""
        res = self.pruner.prune_output("systemctl status api", "boom\n" * 100, exit_code=3)
        self.assertEqual(res.exit_code, 3)

    def test_prioriza_lineas_criticas_al_acotar(self) -> None:
        ruido = "\n".join(f"info rutinaria numero {i} sobre el proceso {i}" for i in range(200))
        salida = ruido + "\nfatal: la base de datos rechazo la conexion"
        res = self.pruner.prune_output("journalctl", salida)
        self.assertIn("fatal", res.clean_output)

    def test_reporta_el_conteo_original(self) -> None:
        salida = "\n".join(f"linea distinta {i}" for i in range(300))
        res = self.pruner.prune_output("cat /var/log/x", salida)
        self.assertIn("300", res.clean_output)


if __name__ == "__main__":
    unittest.main()

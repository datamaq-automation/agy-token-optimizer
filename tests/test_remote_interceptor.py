"""Pruebas del hook de enrutado: decisiones y overwrite sobre payloads reales."""

import importlib.util
import os
import unittest

RUTA_HOOK = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "hooks",
    "gate_remote_router.py",
)
_spec = importlib.util.spec_from_file_location("gate_remote_router", RUTA_HOOK)
assert _spec is not None and _spec.loader is not None
_modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modulo)
decidir = _modulo.decidir


class TestEnrutado(unittest.TestCase):
    """Escenarios 12 a 16, 24 y 26: la matriz (scope x kind) vista desde el hook."""

    def test_consulta_remota_produce_overwrite(self) -> None:
        """Escenario 12: el unico caso que reescribe la linea."""
        res = decidir('ssh vps "journalctl -u api -n 500"')
        self.assertEqual(res["decision"], "allow")
        self.assertIn("overwrite", res)
        reescrito = res["overwrite"]["CommandLine"]
        self.assertIn("vps_exec.py", reescrito)
        self.assertIn("--host vps", reescrito)

    def test_mutacion_remota_se_deniega_y_nombra_el_comando(self) -> None:
        """Escenario 13: deny, porque force_ask lo pisaria la bandera."""
        res = decidir('ssh vps "systemctl stop nginx"')
        self.assertEqual(res["decision"], "deny")
        self.assertIn("systemctl stop nginx", res["reason"])
        self.assertIn("manualmente", res["reason"])

    def test_interactivo_y_exento_pasan_sin_overwrite(self) -> None:
        """Escenario 14: no se toca lo que el usuario decidio dejar crudo."""
        for linea in ("ssh vps", 'ssh vps "mysqldump db > /tmp/d.sql"', 'ssh vps "apt update"'):
            res = decidir(linea)
            self.assertEqual(res["decision"], "allow", linea)
            self.assertNotIn("overwrite", res, linea)

    def test_pytest_remoto_no_recibe_perfil_ssh(self) -> None:
        """Escenario 15: el bug de pasar 'ssh' como perfil no debe reaparecer."""
        res = decidir('ssh vps "pytest tests/"')
        if "overwrite" in res:
            self.assertNotIn("prune_terminal_output.py 'ssh'", res["overwrite"]["CommandLine"])

    def test_lectura_remota_de_codigo_sugiere_vps_read(self) -> None:
        """Escenario 16: el guardian tambien cubre la puerta remota."""
        res = decidir('ssh vps "cat /srv/app/main.py"')
        self.assertEqual(res["decision"], "deny")
        self.assertIn("vps-read", res["reason"])
        self.assertIn("--ast", res["reason"])

    def test_escritura_remota_sugiere_vps_patch(self) -> None:
        """Escenario 24: las ediciones remotas van por el parcheador que valida sintaxis."""
        res = decidir("ssh vps \"sed -i 's/a/b/' /srv/app.py\"")
        self.assertEqual(res["decision"], "deny")
        self.assertIn("vps-patch", res["reason"])

    def test_ninguna_decision_usa_valores_auto_aprobables(self) -> None:
        """Escenario 17: 'allow', 'ask' y 'force_ask' son auto-aprobables bajo la bandera."""
        mutaciones = (
            'ssh vps "systemctl stop nginx"',
            'ssh vps "docker rm -f api"',
            'ssh vps "ufw disable"',
            "ssh vps \"mysql -e 'DROP TABLE t'\"",
            'ssh vps "rm -rf /var/www/app"',
        )
        for linea in mutaciones:
            res = decidir(linea)
            self.assertEqual(res["decision"], "deny", linea)
            self.assertNotIn(res["decision"], ("ask", "force_ask", "allow"), linea)

    def test_redireccion_nunca_produce_overwrite(self) -> None:
        """Escenario 26: interponer un podador corromperia el archivo escrito."""
        lineas = (
            'ssh vps "journalctl -n 100 > /tmp/log.txt"',
            'ssh vps "ls -la >> /tmp/listado.txt"',
            'ssh vps "df -h | tee /tmp/disco.txt"',
        )
        for linea in lineas:
            res = decidir(linea)
            self.assertNotIn("overwrite", res, linea)

    def test_redireccion_de_stderr_no_impide_podar(self) -> None:
        """Regresion: '2>/dev/null' no guarda la salida, no debe bloquear el reenrutado.

        Detectado corriendo el clasificador contra los comandos reales del audit log:
        un chequeo por substring de '>' confundia stderr con redireccion a archivo.
        """
        casos = (
            "ssh vps \"mysql -e 'SHOW DATABASES;' 2>/dev/null\"",
            'ssh vps "systemctl is-active mariadb 2>/dev/null || which mysql"',
            'ssh vps "grep -rn algo /var/www/ 2>/dev/null | head -n 10"',
        )
        for linea in casos:
            res = decidir(linea)
            self.assertIn("overwrite", res, linea)

    def test_host_desconocido_no_se_toca(self) -> None:
        res = decidir("ssh github.com")
        self.assertEqual(res["decision"], "allow")
        self.assertNotIn("overwrite", res)

    def test_comando_local_inocuo_pasa(self) -> None:
        res = decidir("ls -la")
        self.assertEqual(res["decision"], "allow")
        self.assertNotIn("overwrite", res)

    def test_falla_abierto_ante_entrada_corrupta(self) -> None:
        """Un bug del hook nunca debe frenar la sesion."""
        self.assertEqual(decidir("")["decision"], "allow")


if __name__ == "__main__":
    unittest.main()

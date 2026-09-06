"""Pruebas unitarias del clasificador léxico de comandos (local y remoto)."""

import unittest

from src.application.clasificar_comando import LexicalCommandClassifier
from src.domain.ports import CommandKind, CommandScope, ICodeFileInspector


class InspectorFalso(ICodeFileInspector):
    """Inspector determinístico: responde según un mapa de rutas a cantidad de líneas."""

    def __init__(self, lineas_por_ruta: dict) -> None:
        self.lineas_por_ruta = lineas_por_ruta
        self.consultas = []

    def excede_umbral(self, path: str, umbral_lineas: int = 100) -> bool:
        self.consultas.append(path)
        return self.lineas_por_ruta.get(path, 0) > umbral_lineas


class TestClasificadorRemoto(unittest.TestCase):
    """Escenarios 1 a 7: descomposición y clasificación de líneas ssh."""

    def setUp(self) -> None:
        self.inspector = InspectorFalso({})
        self.clasificador = LexicalCommandClassifier(self.inspector)

    def test_consulta_remota_journalctl(self) -> None:
        """Escenario 1: journalctl remoto es CONSULTA y conserva el comando interno."""
        res = self.clasificador.classify('ssh vps "journalctl -u api -n 500"')
        assert res is not None
        self.assertEqual(res.scope, CommandScope.REMOTO)
        self.assertEqual(res.kind, CommandKind.CONSULTA)
        self.assertEqual(res.inner_command, "journalctl -u api -n 500")
        self.assertEqual(res.host_alias, "vps")

    def test_ssh_sin_comando_es_interactivo(self) -> None:
        """Escenario 2: una sesión interactiva no se reescribe."""
        res = self.clasificador.classify("ssh vps")
        assert res is not None
        self.assertEqual(res.kind, CommandKind.INTERACTIVO)

    def test_ssh_con_tty_es_interactivo(self) -> None:
        """Escenario 2 bis: el flag -t pide TTY, tampoco se reescribe."""
        res = self.clasificador.classify('ssh -t vps "htop"')
        assert res is not None
        self.assertEqual(res.kind, CommandKind.INTERACTIVO)

    def test_mysqldump_con_redireccion_es_exento(self) -> None:
        """Escenario 3: un dump binario redirigido pasa crudo."""
        res = self.clasificador.classify('ssh vps "mysqldump --no-tablespaces db t > /tmp/d.sql"')
        assert res is not None
        self.assertEqual(res.kind, CommandKind.EXENTO)

    def test_systemctl_stop_es_mutacion(self) -> None:
        """Escenario 4: detener un servicio remoto es mutación."""
        res = self.clasificador.classify('ssh vps "systemctl stop nginx"')
        assert res is not None
        self.assertEqual(res.kind, CommandKind.MUTACION)

    def test_mysql_select_es_consulta_y_delete_es_mutacion(self) -> None:
        """Escenario 5: la sentencia SQL define el tipo, no el binario."""
        lectura = self.clasificador.classify("ssh vps \"mysql -e 'SELECT 1'\"")
        assert lectura is not None
        self.assertEqual(lectura.kind, CommandKind.CONSULTA)

        destructiva = self.clasificador.classify("ssh vps \"mysql -e 'DELETE FROM t'\"")
        assert destructiva is not None
        self.assertEqual(destructiva.kind, CommandKind.MUTACION)

    def test_delete_con_where_no_es_mutacion_ciega(self) -> None:
        """Un DELETE acotado por WHERE no dispara la regla de destrucción masiva."""
        res = self.clasificador.classify("ssh vps \"mysql -e 'DELETE FROM t WHERE id=1'\"")
        assert res is not None
        self.assertNotEqual(res.kind, CommandKind.MUTACION)

    def test_host_desconocido_se_ignora(self) -> None:
        """Escenario 6: ssh github.com queda fuera de alcance."""
        self.assertIsNone(self.clasificador.classify("ssh github.com"))
        self.assertIsNone(self.clasificador.classify('ssh git@github.com "echo hola"'))

    def test_comillas_anidadas_no_corrompen_el_parseo(self) -> None:
        """Escenario 7: shlex preserva el comando interno con comillas anidadas."""
        linea = "ssh vps \"mysql -e \\\"SHOW GRANTS FOR 'busqueda'@'localhost'\\\"\""
        res = self.clasificador.classify(linea)
        assert res is not None
        self.assertEqual(res.scope, CommandScope.REMOTO)
        self.assertIn("SHOW GRANTS", res.inner_command)


class TestGuardianLecturaLocal(unittest.TestCase):
    """Escenarios 19 a 23 y 25: la cara local del mismo clasificador."""

    def test_cat_local_archivo_extenso_es_lectura_codigo(self) -> None:
        """Escenario 19: por encima del umbral, la lectura completa se marca."""
        inspector = InspectorFalso({"src/main.py": 400})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify("cat src/main.py")
        assert res is not None
        self.assertEqual(res.scope, CommandScope.LOCAL)
        self.assertEqual(res.kind, CommandKind.LECTURA_CODIGO)
        self.assertEqual(res.target_path, "src/main.py")

    def test_cat_local_archivo_corto_no_se_marca(self) -> None:
        """Escenario 20: por debajo del umbral no se cambia la política vigente."""
        inspector = InspectorFalso({"src/main.py": 40})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify("cat src/main.py")
        assert res is not None
        self.assertNotEqual(res.kind, CommandKind.LECTURA_CODIGO)

    def test_head_acotado_es_consulta(self) -> None:
        """Escenario 21: una lectura acotada ya es eficiente, no se interfiere."""
        inspector = InspectorFalso({"src/main.py": 400})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify("head -n 65 src/main.py")
        assert res is not None
        self.assertEqual(res.kind, CommandKind.CONSULTA)

    def test_lectura_remota_no_consulta_al_inspector(self) -> None:
        """Escenario 22: el hook no puede contar líneas remotas sin tocar la red."""
        inspector = InspectorFalso({})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify('ssh vps "cat /srv/app/main.py"')
        assert res is not None
        self.assertEqual(res.kind, CommandKind.LECTURA_CODIGO)
        self.assertEqual(res.target_path, "/srv/app/main.py")
        self.assertEqual(inspector.consultas, [])

    def test_heredoc_es_escritura_no_lectura(self) -> None:
        """Escenario 23: 'cat << EOF > archivo' escribe, no lee."""
        inspector = InspectorFalso({})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify("cat << 'EOF' > scripts/gen.py\nprint(1)\nEOF")
        assert res is not None
        self.assertEqual(res.kind, CommandKind.ESCRITURA)
        self.assertEqual(res.scope, CommandScope.LOCAL)

    def test_sed_in_place_remoto_es_escritura(self) -> None:
        """Escenario 24: sed -i remoto debe ir por el parcheador con validación."""
        inspector = InspectorFalso({})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify("ssh vps \"sed -i 's/a/b/' /srv/app.py\"")
        assert res is not None
        self.assertEqual(res.scope, CommandScope.REMOTO)
        self.assertEqual(res.kind, CommandKind.ESCRITURA)

    def test_exento_precede_a_escritura(self) -> None:
        """Escenario 25: un dump redirigido no se confunde con edición de código."""
        inspector = InspectorFalso({})
        clasificador = LexicalCommandClassifier(inspector)
        res = clasificador.classify('ssh vps "mysqldump db > /tmp/d.sql"')
        assert res is not None
        self.assertEqual(res.kind, CommandKind.EXENTO)


if __name__ == "__main__":
    unittest.main()

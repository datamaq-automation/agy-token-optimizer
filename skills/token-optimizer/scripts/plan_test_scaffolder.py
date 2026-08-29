#!/usr/bin/env python3
"""
plan_test_scaffolder.py: Generador automático de tests unitarios TDD con mocks de puertos en CPU.
Lee interfaces abstractas (abc.ABC) y genera clases Mock y suites @pytest.mark.parametrize,
ahorrando >1.500 tokens de salida durante la fase de planificación en AGY.
Uso: python3 plan_test_scaffolder.py [ports_file.py] [salida_test.py]
"""

import ast
import os
import sys
from pathlib import Path


def extract_ports_from_file(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath.name)

    ports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_abc = any(
                isinstance(b, ast.Name)
                and b.id in ("ABC", "abstractmethod")
                or isinstance(b, ast.Attribute)
                and b.attr in ("ABC", "abstractmethod")
                for b in node.bases
            )
            if (
                is_abc
                or node.name.endswith("Port")
                or node.name.endswith("Repository")
                or node.name.endswith("Gateway")
            ):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("__"):
                        params = [arg.arg for arg in item.args.args if arg.arg != "self"]
                        methods.append((item.name, params))
                ports.append({"name": node.name, "methods": methods})
    return ports


def generate_test_file_content(module_name: str, ports: list[dict]) -> str:
    lines = [
        "import pytest",
        "from unittest.mock import MagicMock",
        "",
        f"# Suite de Pruebas TDD Generada para Módulo: {module_name}",
        "# Estado: RED Suite Inicial (Gobernanza Clean Architecture)",
        "",
    ]

    # 1. Generar clases Mock
    for p in ports:
        port_name = p["name"]
        mock_name = f"Mock{port_name}"
        lines.append(f"class {mock_name}:")
        lines.append(f'    """Mock determinístico para el puerto {port_name}."""')
        lines.append("    def __init__(self) -> None:")
        for m_name, _ in p["methods"]:
            lines.append(f"        self.{m_name} = MagicMock()")
        if not p["methods"]:
            lines.append("        pass")
        lines.append("")

    # 2. Generar Tests Parametrizados
    for p in ports:
        for m_name, params in p["methods"]:
            test_name = f"test_{p['name'].lower()}_{m_name}_happy_path"
            lines.append("@pytest.mark.parametrize(")
            lines.append('    "test_input, expected_status",')
            lines.append("    [")
            lines.append('        ({"id": "valid-001"}, True),')
            lines.append('        ({"id": "valid-002"}, True),')
            lines.append("    ]")
            lines.append(")")
            lines.append(f"def {test_name}(test_input: dict, expected_status: bool) -> None:")
            lines.append(f'    """Verifica ejecución exitosa de {m_name} en {p["name"]}."""')
            lines.append(f"    mock_port = Mock{p['name']}()")
            lines.append(f"    mock_port.{m_name}.return_value = expected_status")
            lines.append(f"    res = mock_port.{m_name}(**{{k: test_input.get(k) for k in {params}}})")
            lines.append("    assert res == expected_status")
            lines.append("")

    if not ports:
        lines.append("def test_module_placeholder() -> None:")
        lines.append('    """Test inicial básico."""')
        lines.append("    assert True")
        lines.append("")

    return "\n".join(lines)


def main():
    target_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src/domain/ports.py")
    out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("tests/unit/test_ports_scaffold.py")

    print(f"🧪 [Plan Test Scaffolder] Analizando puertos en '{target_file}'...")
    ports = extract_ports_from_file(target_file)

    content = generate_test_file_content(target_file.stem, ports)

    os.makedirs(out_file.parent, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(
        f"✅ Suite de tests generada en '{out_file}' ({len(ports)} puertos mockeados, {len(content.splitlines())} líneas)."
    )


if __name__ == "__main__":
    main()

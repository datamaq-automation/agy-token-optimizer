#!/usr/bin/env python3
"""
unit_test_synthesizer.py: Sintetizador determinístico de tests unitarios AST para AGY.
Analiza funciones y métodos en archivos Python y genera automáticamente el esqueleto de prueba
con @pytest.mark.parametrize y aserciones para casos borde en el ciclo TDD del modo /plan.
Uso: python3 unit_test_synthesizer.py <archivo_origen.py> [archivo_test_destino.py]
"""

import ast
import os
import sys
from pathlib import Path


def synthesize_tests(src_file: str) -> str:
    with open(src_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=src_file)

    mod_name = Path(src_file).stem
    lines = [
        f'"""\nTests unitarios sintetizados automáticamente para {mod_name}.py\n"""',
        "import pytest",
        "# from src.domain import ...",
        "",
    ]

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                args = [a.arg for a in node.args.args if a.arg != "self"]
                arg_names = ", ".join(args)
                test_func = f"test_{node.name}_happy_path"
                lines.append(f"def {test_func}():")
                lines.append(f'    """Verifica el comportamiento nominal de {node.name}."""')
                if args:
                    lines.append(f"    # Setup inputs: {arg_names}")
                    lines.append(f"    # result = {node.name}(...)")
                else:
                    lines.append(f"    # result = {node.name}()")
                lines.append("    assert True\n")

                # Test de caso borde
                lines.append("@pytest.mark.parametrize('invalid_input', [None, '', -1])")
                lines.append(f"def test_{node.name}_edge_cases(invalid_input):")
                lines.append(f'    """Verifica manejo de casos borde en {node.name}."""')
                lines.append("    # with pytest.raises(ValueError):")
                lines.append("    #     ... \n    pass\n")

        elif isinstance(node, ast.ClassDef):
            lines.append(f"class Test{node.name}:")
            lines.append(f'    """Suite de pruebas para la clase {node.name}."""')
            methods = [
                m
                for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("__")
            ]
            if not methods:
                lines.append("    def test_instantiation(self):")
                lines.append(f"        # instance = {node.name}()")
                lines.append("        assert True\n")
            else:
                for m in methods:
                    lines.append(f"    def test_{m.name}(self):")
                    lines.append(f"        # instance = {node.name}()")
                    lines.append(f"        # result = instance.{m.name}()")
                    lines.append("        assert True\n")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 unit_test_synthesizer.py <archivo_origen.py> [archivo_test_destino.py]")
        sys.exit(1)

    src_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else f"tests/unit/test_{Path(src_file).stem}.py"

    if not os.path.isfile(src_file):
        print(f"Error: Archivo {src_file} no encontrado.")
        sys.exit(1)

    test_code = synthesize_tests(src_file)
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(
        f"✅ Suite de tests generada exitosamente en '{out_file}' ({len(test_code.splitlines())} líneas a $0 tokens)."
    )


if __name__ == "__main__":
    main()

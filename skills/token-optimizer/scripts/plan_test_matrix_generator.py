#!/usr/bin/env python3
"""
plan_test_matrix_generator.py: Generador de matriz canónica de casos borde para /plan en AGY.
Parsea archivos de puertos/interfaces abstractas (ports.py o domain) por AST en CPU (< 5 ms)
y genera una matriz estructurada de casos de prueba (Happy Path, Null, Timeout, Error de Validación, Duplicados)
ahorrando cientos de tokens de salida en la redacción de planes.
Uso: python3 plan_test_matrix_generator.py <archivo_puerto.py>
"""

import ast
import sys
from pathlib import Path


def extract_methods_from_ast(file_path: Path) -> list[dict]:
    methods = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name.startswith("__"):
                            continue
                        args = [a.arg for a in item.args.args if a.arg != "self"]
                        methods.append(
                            {
                                "class": node.name,
                                "method": item.name,
                                "args": args,
                                "is_async": isinstance(item, ast.AsyncFunctionDef),
                            }
                        )
    except Exception:
        pass
    return methods


def generate_edge_case_matrix(methods: list[dict], file_name: str) -> str:
    lines = [
        f"📊 [Matriz de Casos de Prueba TDD para '{file_name}']",
        "",
        "| Método / Operación | Escenario de Prueba | Entrada (Input) | Resultado Esperado |",
        "| :--- | :--- | :--- | :--- |",
    ]

    if not methods:
        lines.append("| Operación Principal | Happy Path | Parámetros válidos | Retorno exitoso / DTO poblado |")
        lines.append(
            "| Operación Principal | Entrada Nula / Vacía | None / String vacío | Validación falla (422 / ValueError) |"
        )
        lines.append(
            "| Operación Principal | Fallo de Red / Timeout | Simulación de corte | Excepción de Gateway / Timeout |"
        )
        lines.append(
            "| Operación Principal | Conflicto / Duplicado | Clave ya existente | Excepción de Conflicto (409) |"
        )
        return "\n".join(lines)

    for m in methods:
        c_name = m["class"]
        m_name = m["method"]
        args_str = ", ".join(m["args"]) if m["args"] else "void"

        lines.append(f"| `{c_name}.{m_name}` | **Happy Path** | `{args_str}` válidos | Retorno exitoso |")
        lines.append(
            f"| `{c_name}.{m_name}` | **Null / Empty** | `{m['args'][0] if m['args'] else 'arg'}=None` | Lanza `ValueError` / 422 |"
        )
        lines.append(
            f"| `{c_name}.{m_name}` | **Fallo Externo** | Simulación de corte/timeout | Lanza `GatewayException` |"
        )
        lines.append(
            f"| `{c_name}.{m_name}` | **Conflicto / Duplicado** | Clave/ID duplicado | Lanza `ConflictException` |"
        )

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 plan_test_matrix_generator.py <archivo_puerto.py>")
        sys.exit(1)

    target_file = Path(sys.argv[1]).resolve()
    if not target_file.exists():
        print(f"Error: Archivo '{target_file}' no encontrado.")
        sys.exit(1)

    methods = extract_methods_from_ast(target_file)
    matrix = generate_edge_case_matrix(methods, target_file.name)

    print("=" * 70)
    print(matrix)
    print("=" * 70)


if __name__ == "__main__":
    main()

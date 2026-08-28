#!/usr/bin/env python3
"""
stub_generator.py: Generador automático de stubs de tipo (.pyi) para AGY.
Genera stubs ultralivianos de interfaces y contratos en .stubs/, permitiendo que AGY
inspeccione únicamente ~50 tokens en lugar de módulos completos de 600 líneas.
Uso: python3 stub_generator.py [directorio_origen] [directorio_stubs]
"""

import ast
import os
import sys
from pathlib import Path


class StubTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        return self._transform_func(node)

    def visit_AsyncFunctionDef(self, node):
        return self._transform_func(node)

    def _transform_func(self, node):
        node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if not node.body:
            node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        return node


def generate_stub(source_code: str) -> str:
    tree = ast.parse(source_code)
    transformer = StubTransformer()
    stub_tree = transformer.visit(tree)
    ast.fix_missing_locations(stub_tree)
    return ast.unparse(stub_tree)


def process_directory(src_dir: str = "src", out_dir: str = ".stubs"):
    src_path = Path(src_dir).resolve()
    out_path = Path(out_dir).resolve()

    if not src_path.exists():
        print(f"Directorio de origen no encontrado: {src_path}")
        return

    count = 0
    for root, _, files in os.walk(src_path):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                full_in = Path(root) / f
                rel_path = full_in.relative_to(src_path)
                full_out = out_path / rel_path.with_suffix(".pyi")

                try:
                    with open(full_in, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    stub_content = generate_stub(content)

                    full_out.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_out, "w", encoding="utf-8") as fh:
                        fh.write(stub_content + "\n")
                    count += 1
                except Exception:
                    continue

    print(f"✅ Se generaron {count} stubs de tipos (.pyi) en '{out_dir}' exitosamente.")


def main():
    s = sys.argv[1] if len(sys.argv) > 1 else "src"
    o = sys.argv[2] if len(sys.argv) > 2 else ".stubs"
    process_directory(s, o)


if __name__ == "__main__":
    main()

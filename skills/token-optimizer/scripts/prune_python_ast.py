#!/usr/bin/env python3
"""
prune_python_ast.py: Poda determinista de archivos Python usando el módulo estándar `ast`.
Elimina comentarios, docstrings y cuerpos de funciones reemplazándolos por `...`.
Reduce el tamaño de tokens entre un 70% y un 90% preservando firmas y tipos.
"""
import ast
import sys
import os

class DeterministicCodePruner(ast.NodeTransformer):
    def __init__(self, keep_docstrings: bool = False, keep_bodies: bool = False):
        self.keep_docstrings = keep_docstrings
        self.keep_bodies = keep_bodies

    def _prune_body(self, node):
        self.generic_visit(node)
        if not self.keep_bodies:
            if self.keep_docstrings and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body = [node.body[0], ast.Expr(value=ast.Constant(value=Ellipsis))]
            else:
                node.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
        return node

    def visit_FunctionDef(self, node):
        return self._prune_body(node)

    def visit_AsyncFunctionDef(self, node):
        return self._prune_body(node)

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if not self.keep_docstrings and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:]
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        if not self.keep_docstrings and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:]
        return node

def prune_file(filepath: str, keep_docstrings: bool = False) -> str:
    if not os.path.exists(filepath):
        print(f"Error: Archivo no encontrado: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)
    pruner = DeterministicCodePruner(keep_docstrings=keep_docstrings)
    pruned_tree = pruner.visit(tree)
    ast.fix_missing_locations(pruned_tree)
    return ast.unparse(pruned_tree)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 prune_python_ast.py <archivo.py> [--docstrings]")
        sys.exit(1)
    keep_doc = "--docstrings" in sys.argv
    print(prune_file(sys.argv[1], keep_docstrings=keep_doc))

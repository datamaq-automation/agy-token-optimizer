#!/usr/bin/env node
/**
 * prune_ts_ast.js: Poda determinista de archivos TypeScript y JavaScript.
 * Extrae interfaces, tipos, firmas de clases y métodos vaciando el cuerpo de las funciones.
 */
const ts = require('typescript');
const fs = require('fs');

function pruneTS(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`Error: Archivo no encontrado: ${filePath}`);
    process.exit(1);
  }

  const code = fs.readFileSync(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(filePath, code, ts.ScriptTarget.Latest, true);

  function walk(node, indent = '') {
    if (ts.isClassDeclaration(node) && node.name) {
      console.log(`${indent}export class ${node.name.text} {`);
      node.members.forEach(m => walk(m, indent + '  '));
      console.log(`${indent}}`);
    } else if (ts.isInterfaceDeclaration(node) || ts.isTypeAliasDeclaration(node)) {
      console.log(node.getFullText(sourceFile).trim());
    } else if (ts.isMethodDeclaration(node) || ts.isConstructorDeclaration(node) || ts.isFunctionDeclaration(node)) {
      const name = node.name ? node.name.text : 'constructor';
      const params = node.parameters.map(p => p.getText(sourceFile)).join(', ');
      const retType = node.type ? `: ${node.type.getText(sourceFile)}` : '';
      console.log(`${indent}${name}(${params})${retType} { ... }`);
    } else {
      ts.forEachChild(node, c => walk(c, indent));
    }
  }

  walk(sourceFile);
}

if (process.argv.length < 3) {
  console.log("Uso: node prune_ts_ast.js <archivo.ts|js>");
  process.exit(1);
}

pruneTS(process.argv[2]);

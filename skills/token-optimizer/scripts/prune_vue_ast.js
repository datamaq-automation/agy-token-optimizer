#!/usr/bin/env node
/**
 * prune_vue_ast.js: Poda determinista de Single File Components (SFC) de Vue 3.
 * Extrae contratos de interfaz (props, emits, slots, types, interfaces y firmas de métodos),
 * eliminando plantillas y estilos extensos a $0 costo de tokens en hardware local (Node.js).
 */

const fs = require('fs');
const path = require('path');

/**
 * Resuelve un módulo de Node.js buscando hacia arriba desde el directorio de trabajo o archivo.
 */
function resolveModule(moduleName, fromDir) {
  try {
    return require(moduleName);
  } catch (err) {
    // Buscar en ancestros
    let current = path.resolve(fromDir);
    while (current !== path.dirname(current)) {
      const candidate = path.join(current, 'node_modules', moduleName);
      if (fs.existsSync(candidate)) {
        try {
          return require(candidate);
        } catch (e) {}
      }
      current = path.dirname(current);
    }
  }

  // Rutas conocidas en el workspace
  const knownLocations = [
    '/home/agustin/proyectos_software/datamaq/app-datamaq/node_modules/' + moduleName,
    '/home/agustin/proyectos_software/datamaq/www-datamaq/node_modules/' + moduleName,
    '/home/agustin/proyectos_software/datamaq/www-cybersyn/node_modules/' + moduleName,
  ];

  for (const loc of knownLocations) {
    if (fs.existsSync(loc)) {
      try {
        return require(loc);
      } catch (e) {}
    }
  }

  return null;
}

/**
 * Poda el AST de un bloque de código TypeScript/JavaScript.
 */
function pruneScriptCode(scriptContent, ts, isSetup = true) {
  if (!ts) {
    // Fallback determinista mediante expresiones regulares si TypeScript no está cargado
    return fallbackPruneScript(scriptContent);
  }

  const sourceFile = ts.createSourceFile('component.ts', scriptContent, ts.ScriptTarget.Latest, true);
  const outputLines = [];

  function printNode(node) {
    if (ts.isImportDeclaration(node)) {
      outputLines.push(node.getText(sourceFile).trim());
    } else if (
      ts.isInterfaceDeclaration(node) ||
      ts.isTypeAliasDeclaration(node) ||
      ts.isEnumDeclaration(node)
    ) {
      outputLines.push(node.getText(sourceFile).trim());
    } else if (ts.isClassDeclaration(node) && node.name) {
      outputLines.push(`export class ${node.name.text} {`);
      node.members.forEach((m) => {
        if (ts.isMethodDeclaration(m) || ts.isConstructorDeclaration(m)) {
          const name = m.name ? m.name.getText(sourceFile) : 'constructor';
          const params = m.parameters.map((p) => p.getText(sourceFile)).join(', ');
          const retType = m.type ? `: ${m.type.getText(sourceFile)}` : '';
          outputLines.push(`  ${name}(${params})${retType} { ... }`);
        } else if (ts.isPropertyDeclaration(m)) {
          outputLines.push(`  ${m.getText(sourceFile).trim()}`);
        }
      });
      outputLines.push(`}`);
    } else if (ts.isFunctionDeclaration(node)) {
      const name = node.name ? node.name.text : 'anonymous';
      const params = node.parameters.map((p) => p.getText(sourceFile)).join(', ');
      const retType = node.type ? `: ${node.type.getText(sourceFile)}` : '';
      outputLines.push(`function ${name}(${params})${retType} { ... }`);
    } else if (ts.isExpressionStatement(node)) {
      const exprText = node.expression.getText(sourceFile).trim();
      // Macros de Vue 3 (defineProps, defineEmits, withDefaults, defineExpose, defineModel, etc.)
      if (
        exprText.startsWith('defineProps') ||
        exprText.startsWith('withDefaults') ||
        exprText.startsWith('defineEmits') ||
        exprText.startsWith('defineExpose') ||
        exprText.startsWith('defineModel') ||
        exprText.startsWith('defineOptions')
      ) {
        outputLines.push(exprText);
      }
    } else if (ts.isVariableStatement(node)) {
      const fullText = node.declarationList.getText(sourceFile).trim();
      // Identificar si contiene macros o funciones flecha
      if (
        fullText.includes('defineProps') ||
        fullText.includes('defineEmits') ||
        fullText.includes('defineModel') ||
        fullText.includes('withDefaults')
      ) {
        outputLines.push(node.getText(sourceFile).trim());
      } else {
        node.declarationList.declarations.forEach((decl) => {
          const varName = decl.name.getText(sourceFile);
          const typeAnn = decl.type ? `: ${decl.type.getText(sourceFile)}` : '';
          if (decl.initializer && (ts.isArrowFunction(decl.initializer) || ts.isFunctionExpression(decl.initializer))) {
            const params = decl.initializer.parameters.map((p) => p.getText(sourceFile)).join(', ');
            const ret = decl.initializer.type ? `: ${decl.initializer.type.getText(sourceFile)}` : '';
            outputLines.push(`const ${varName} = (${params})${ret} => { ... }`);
          } else {
            outputLines.push(`const ${varName}${typeAnn} = ...`);
          }
        });
      }
    }
  }

  ts.forEachChild(sourceFile, (child) => printNode(child));
  return outputLines.join('\n');
}

/**
 * Fallback determinista para podar scripts si no está disponible el compilador de TypeScript.
 */
function fallbackPruneScript(code) {
  const lines = code.split('\n');
  const result = [];
  let inMacroOrInterface = false;
  let braceCount = 0;
  let buffer = [];

  for (const line of lines) {
    const trimmed = line.trim();

    // Detección de inicio de interfaz o macro multilínea
    if (
      trimmed.startsWith('export interface') ||
      trimmed.startsWith('interface ') ||
      trimmed.startsWith('export type ') ||
      trimmed.startsWith('type ') ||
      trimmed.startsWith('defineProps') ||
      trimmed.startsWith('withDefaults') ||
      trimmed.startsWith('defineEmits') ||
      trimmed.startsWith('const emit = defineEmits') ||
      trimmed.startsWith('const props = defineProps')
    ) {
      inMacroOrInterface = true;
      buffer = [line];
      braceCount = (line.match(/[{<(]/g) || []).length - (line.match(/[}>)]/g) || []).length;
      if (braceCount <= 0) {
        result.push(buffer.join('\n'));
        inMacroOrInterface = false;
        buffer = [];
      }
      continue;
    }

    if (inMacroOrInterface) {
      buffer.push(line);
      braceCount += (line.match(/[{<(]/g) || []).length - (line.match(/[}>)]/g) || []).length;
      if (braceCount <= 0) {
        result.push(buffer.join('\n'));
        inMacroOrInterface = false;
        buffer = [];
      }
      continue;
    }

    // Imports
    if (trimmed.startsWith('import ')) {
      result.push(trimmed);
      continue;
    }

    // Funciones estándar
    const funcMatch = trimmed.match(/^function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)(?::\s*([^{]+))?\s*\{/);
    if (funcMatch) {
      const name = funcMatch[1];
      const params = funcMatch[2].trim();
      const ret = funcMatch[3] ? `: ${funcMatch[3].trim()}` : '';
      result.push(`function ${name}(${params})${ret} { ... }`);
      continue;
    }

    // Funciones flecha
    const arrowMatch = trimmed.match(/^const\s+([a-zA-Z0-9_$]+)\s*=\s*\(([^)]*)\)(?::\s*([^{=]+))?\s*=>/);
    if (arrowMatch) {
      const name = arrowMatch[1];
      const params = arrowMatch[2].trim();
      const ret = arrowMatch[3] ? `: ${arrowMatch[3].trim()}` : '';
      result.push(`const ${name} = (${params})${ret} => { ... }`);
      continue;
    }
  }

  return result.join('\n');
}

/**
 * Poda el template analizando slots y componentes hijo utilizados.
 */
function pruneTemplate(templateContent) {
  const slots = new Set();
  const components = new Set();

  // Detectar slots
  const slotRegex = /<slot(?:\s+name=["']([^"']+)["'])?[^>]*>/g;
  let match;
  while ((match = slotRegex.exec(templateContent)) !== null) {
    slots.add(match[1] || 'default');
  }

  // Detectar componentes (nombres en PascalCase)
  const componentRegex = /<([A-Z][a-zA-Z0-9]+)\b/g;
  while ((match = componentRegex.exec(templateContent)) !== null) {
    components.add(match[1]);
  }

  const slotList = slots.size > 0 ? Array.from(slots).join(', ') : 'ninguno';
  const compList = components.size > 0 ? Array.from(components).join(', ') : 'ninguno';

  return `  <!-- [TEMPLATE PODADO] -->\n  <!-- Slots detectados: ${slotList} -->\n  <!-- Componentes hijos: ${compList} -->`;
}

/**
 * Función principal que orquesta la poda del componente Vue SFC.
 */
function pruneVueSFC(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`Error: Archivo no encontrado: ${filePath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const fileDir = path.dirname(path.resolve(filePath));

  const sfcCompiler = resolveModule('@vue/compiler-sfc', fileDir);
  const ts = resolveModule('typescript', fileDir);

  let scripts = [];
  let template = null;
  let styles = [];

  if (sfcCompiler && sfcCompiler.parse) {
    try {
      const parsed = sfcCompiler.parse(content, { filename: path.basename(filePath) });
      const descriptor = parsed.descriptor;

      if (descriptor.scriptSetup) {
        scripts.push({
          content: descriptor.scriptSetup.content,
          attrs: 'setup' + (descriptor.scriptSetup.lang ? ` lang="${descriptor.scriptSetup.lang}"` : ''),
          isSetup: true,
        });
      }
      if (descriptor.script) {
        scripts.push({
          content: descriptor.script.content,
          attrs: descriptor.script.lang ? `lang="${descriptor.script.lang}"` : '',
          isSetup: false,
        });
      }
      if (descriptor.template) {
        template = descriptor.template.content;
      }
      if (descriptor.styles && descriptor.styles.length > 0) {
        styles = descriptor.styles.map((s) => (s.scoped ? 'scoped' : ''));
      }
    } catch (e) {
      // Fallback a regex en caso de error de parseo del compilador
    }
  }

  // Fallback si no hay compilador o falló
  if (scripts.length === 0 && !template) {
    const scriptRegex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
    let m;
    while ((m = scriptRegex.exec(content)) !== null) {
      const attrs = m[1].trim();
      scripts.push({
        content: m[2],
        attrs: attrs,
        isSetup: attrs.includes('setup'),
      });
    }

    const templateMatch = content.match(/<template\b([^>]*)>([\s\S]*?)<\/template>/i);
    if (templateMatch) {
      template = templateMatch[2];
    }

    const styleRegex = /<style\b([^>]*)>([\s\S]*?)<\/style>/gi;
    while ((m = styleRegex.exec(content)) !== null) {
      styles.push(m[1].trim());
    }
  }

  const output = [];

  // 1. Podar scripts
  if (scripts.length > 0) {
    scripts.forEach((s) => {
      const attrStr = s.attrs ? ` ${s.attrs}` : '';
      output.push(`<script${attrStr}>`);
      const prunedScript = pruneScriptCode(s.content, ts, s.isSetup);
      output.push(prunedScript);
      output.push(`</script>`);
      output.push('');
    });
  }

  // 2. Podar template
  if (template !== null) {
    output.push(`<template>`);
    output.push(pruneTemplate(template));
    output.push(`</template>`);
    output.push('');
  }

  // 3. Podar styles
  if (styles.length > 0) {
    styles.forEach((st) => {
      const stAttr = st ? ` ${st}` : '';
      output.push(`<style${stAttr}> /* [ESTILOS CSS PODADOS] */ </style>`);
    });
  }

  console.log(output.join('\n').trim());
}

if (process.argv.length < 3) {
  console.log('Uso: node prune_vue_ast.js <archivo.vue>');
  process.exit(1);
}

pruneVueSFC(process.argv[2]);

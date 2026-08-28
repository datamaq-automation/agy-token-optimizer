#!/usr/bin/env bash
# local_heal.sh: Micro-reparador de sintaxis usando Ollama local (qwen2.5-coder:1.5b)
# Uso: ./local_heal.sh <archivo> "<mensaje_de_error>"

FILE_PATH="$1"
ERROR_MSG="$2"

if [ -z "$FILE_PATH" ] || [ -z "$ERROR_MSG" ]; then
    echo "Uso: $0 <ruta_al_archivo> \"<mensaje_de_error>\""
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: El archivo $FILE_PATH no existe."
    exit 1
fi

echo "==> [Local Self-Healing] Reparando $FILE_PATH con Ollama local..."

CONTENT=$(cat "$FILE_PATH")

PROMPT="You are an autonomous code repair agent. Fix ONLY the syntax/linter error in this file.
Return the complete fixed code. Do not add any conversational text or markdown formatting. Output raw code only.

Error:
$ERROR_MSG

File Content:
$CONTENT"

# Llamada a la API local de Ollama (localhost:11434)
RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate -d "{
  \"model\": \"qwen2.5-coder:1.5b\",
  \"prompt\": $(echo "$PROMPT" | jq -Rs .),
  \"stream\": false
}" | jq -r '.response')

if [ -n "$RESPONSE" ] && [ "$RESPONSE" != "null" ]; then
    echo "$RESPONSE" > "$FILE_PATH"
    echo "==> [Local Self-Healing] Archivo reparado exitosamente en local a costo \$0."
else
    echo "==> [Local Self-Healing] No se pudo obtener respuesta de Ollama."
    exit 1
fi

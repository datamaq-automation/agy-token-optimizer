---
name: token-optimizer
description: Deterministic code skeletonization (AST pruning) and local self-healing tools to reduce LLM input/output tokens by 70% to 90%. Use this skill when inspecting large dependency files, analyzing broad module interfaces, or when automatically repairing syntax/linter errors locally before querying the model.
---

# Token Optimizer & Context Pruner

This skill provides deterministic code pruning and local self-healing to minimize LLM token consumption.

## 1. Code Skeletonizing (AST Pruning)

When reading dependencies, external modules, or large codebase files (>100 lines) where only signatures, classes, and types are needed, do NOT load the full file. Use the pruning scripts to strip function bodies and comments, reducing tokens by 75-90%.

### Python AST Pruning
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/prune_python_ast.py <filepath.py>
```
Options:
- Add `--docstrings` if docstring context is needed.

### TypeScript / JavaScript AST Pruning
```bash
node /home/agustin/.agents/skills/token-optimizer/scripts/prune_ts_ast.js <filepath.ts>
```

### Native Tokenix CLI
If installed on system:
```bash
tokenix read <filepath>
tokenix symbols <symbol_name>
```

---

## 2. Local Self-Healing (Zero Token Ping-Pong)

### Step 1: Deterministic Linters
Run immediately after modifying files to automatically resolve formatting, syntax, and import errors:
- **Python**:
  ```bash
  ruff check --fix <file.py> && ruff format <file.py>
  ```
- **TypeScript / JavaScript**:
  ```bash
  npx eslint --fix <file.ts>
  ```

### Step 2: Local Ollama Model Repair (Optional)
If a syntax error persists and Ollama is active on `localhost:11434`:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/local_heal.sh "<filepath>" "<error_message>"
```

---

## 3. Local Semantic Search (Zero-Token Code Discovery & SQLite Cache)
When searching for concepts or implementations across the project without loading irrelevant files into context:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/local_search.py "<query>" [directorio] [top_k]
```
Uses local `nomic-embed-text` with persistent incremental SQLite caching in `~/.agents/cache/vectors.db` (< 5 ms per query on cache hit).

---

## 4. Local Git Diff Compression (Noise & Lockfile Pruner)
Before inspecting a large diff or PR, strip lockfiles, assets, and whitespace noise:
```bash
git diff | python3 /home/agustin/.agents/skills/token-optimizer/scripts/diff_compressor.py
```
Or directly:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/diff_compressor.py [directorio]
```
Reduces git diff token consumption by 70% to 90%.

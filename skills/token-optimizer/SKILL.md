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

---

## 5. In-Memory Symbol Graph & Call-Stack Discovery (Zero-Token Architecture)
Index definitions, caller/callee relationships, and abstract port (`abc.ABC`) implementations in SQLite:
```bash
# Index codebase
python3 /home/agustin/.agents/skills/token-optimizer/scripts/symbol_graph.py index [directorio]

# Find symbols and exact signatures
python3 /home/agustin/.agents/skills/token-optimizer/scripts/symbol_graph.py find <nombre_simbolo>

# Find port/interface implementations
python3 /home/agustin/.agents/skills/token-optimizer/scripts/symbol_graph.py implementations <nombre_puerto>

# Find callers
python3 /home/agustin/.agents/skills/token-optimizer/scripts/symbol_graph.py callers <nombre_funcion>
```

---

## 6. Multi-Threaded Parallel Test Runner (8 Cores)
Execute test suites across all CPU threads with dense, low-token error reporting:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/test_runner.sh [ruta_o_test]
```

---

## 7. Automated Git Governance Hooks (pre-commit / pre-push)
Install automatic Constraint Gauntlet blockers in any repository:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/install_git_hooks.sh [directorio_repo]
```

---

## 8. SDD SSOT Spec Scaffolding (Save >1,500 Output Tokens in /plan)
Pre-populate the formal 5-section SSOT spec template with Git metadata:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/spec_scaffold.py [backend|frontend] [ruta_salida]
```

---

## 9. Token Savings & ROI Dashboard (Local Hardware Analytics)
Track tokens and dollars saved per tool in SQLite (`~/.agents/cache/metrics.db`):
```bash
# View dashboard
python3 /home/agustin/.agents/skills/token-optimizer/scripts/token_tracker.py stats

# Log savings
python3 /home/agustin/.agents/skills/token-optimizer/scripts/token_tracker.py log --tool "AST Pruning" --input-saved 5000 --output-saved 0
```

---

## 10. Surgical Context Injector (< 500 Tokens Bundle)
Package symbol definitions, callers, and AST skeletons into an ultra-compact context bundle before prompting the LLM:
```bash
# By Symbol
python3 /home/agustin/.agents/skills/token-optimizer/scripts/context_injector.py --symbol <nombre_simbolo>

# By File
python3 /home/agustin/.agents/skills/token-optimizer/scripts/context_injector.py --file <archivo.py>

# By Natural Language Query
python3 /home/agustin/.agents/skills/token-optimizer/scripts/context_injector.py --query "<requerimiento>" [directorio]
```

---

## 11. Zero-Trust Local CI Pipeline (Uncle Bob Gauntlet)
Execute all 5 stages of static validation and tests locally in ~1.5s:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/ci_local.sh [directorio_repo]
```

---

## 12. Multi-Tier Subagents Orchestration Guidelines
When delegating work via `invoke_subagent`:
- **`researcher`**: Use `Model: 'flash_lite'` for fast read-only symbol and file discovery.
- **`auditor`**: Use `Model: 'flash'` for checking Clean Architecture compliance.
- **`architect`**: Use `Model: 'pro'` for designing 5-section SSOT specifications.

---

## 13. Background RAM Watcher Daemon (0 ms Indexing)
Monitors files in real time and keeps `symbols.db` and `vectors.db` synchronized in RAM:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/local_watcher.py [directorio] &
```

---

## 14. Architecture Mermaid Diagram Generator ($0 Tokens)
Automatically generates Mermaid architecture diagrams from SQLite symbol relationships:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/arch_diagram.py [directorio]
```

---

## 15. Zero-Leak Static Security & Secret Auditor
Scans for hardcoded secrets, private keys, and vulnerable dependencies:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/security_audit.sh [directorio]
```

---

## 16. 2nd-Order Semantic Reranker (Top 2 Chunks < 500 Tokens)
Reranks vector search candidates using token density scoring to extract only the 2 most relevant snippets:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/local_reranker.py "<query>" [directorio] [top_n]
```

---

## 17. Automatic Interface Stub Generator (.pyi)
Generates `.pyi` type signature stubs for modules in `src/`, reducing read overhead from 600 tokens to ~50 tokens:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/stub_generator.py [src_dir] [.stubs_dir]
```

---

## 18. Prompt & Context Squeezer (30% - 50% Reduction)
Normalizes text, strips fluff, and compresses markdown tables before sending prompts:
```bash
cat prompt.md | python3 /home/agustin/.agents/skills/token-optimizer/scripts/prompt_squeezer.py
```

---

## 19. Local SLM Code Pre-Drafting (qwen2.5-coder:1.5b in RAM)
Generates code drafts, boilerplate, and DTOs in RAM at ~16 tok/s ($0 API cost):
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/local_slm_draft.py "<instrucción_de_código>"
```

---

## 20. Unit Test AST Synthesizer (Save >1,200 Tokens in /plan)
Generates test skeletons with parameterized edge cases directly from function AST:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/unit_test_synthesizer.py <origen.py> [test_destino.py]
```

---

## 21. AST & Schema Minifier (40% - 60% Input Reduction)
Minifies Python, JSON, and schemas without altering execution semantics:
```bash
cat data.json | python3 /home/agustin/.agents/skills/token-optimizer/scripts/ast_minifier.py
```

---

## 22. Semantic Response Cache in RAM (Cosine Sim >= 0.92)
Recalls previous architectural explanations and questions in 1 ms at $0 API cost:
```bash
# Query cache
python3 /home/agustin/.agents/skills/token-optimizer/scripts/semantic_response_cache.py query "<pregunta>"

# Save response
python3 /home/agustin/.agents/skills/token-optimizer/scripts/semantic_response_cache.py save "<pregunta>" "<respuesta>"
```

---

## 23. RAM-Backed POSIX Workspace (15 GB/s in /dev/shm)
Manages an in-memory disk in `/dev/shm/agy-ramdisk` for zero I/O latency:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/ramdisk_manager.sh [mount|sync|status]
```

---

## 24. PR & Commit Message SLM Synthesizer
Generates conventional commits and Pull Request markdown summaries locally:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/pr_bundle_compressor.py [directorio]
```

---

## 25. Master Sidecar Orchestrator (`agy-opt` CLI)
Consolidates all 24 tools under a unified global CLI:
```bash
# General help and command list
agy-opt help

# Run Zero-Trust CI
agy-opt ci .

# View ROI and token savings
agy-opt stats

# Run closed-loop self-healing
agy-opt heal [test_file]
```

---

## 26. Closed-Loop Recursive Self-Healing (qwen2.5-coder in RAM)
Automatically catches test and linter failures, queries local SLM, and applies patches in RAM until green:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/self_healing_runner.py [test_target]
```

---

## 27. Adaptive Project Rules Engine
Scans repository stack and generates/updates `AGENTS.md` tailored to the project:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/adaptive_rules_engine.py [directorio_repo]
```

---

## 28. In-Flight Token Proxy Interceptor (Automatic Stream Squeezer)
Intercepts any input stream or payload in flight, applying compression and minification before egress:
```bash
cat payload.txt | python3 /home/agustin/.agents/skills/token-optimizer/scripts/token_proxy_interceptor.py
```

---

## 29. SIMD / AVX2 Matrix Vector Engine (< 2 ms)
Evaluates 100,000 code vectors in CPU memory using vector instructions:
```bash
python3 /home/agustin/.agents/skills/token-optimizer/scripts/simd_vector_accelerator.py "<query>" [top_k]
```

---

## 30. Isolated Linux Execution Sandbox
Runs SLM-generated code and unit tests inside contained Linux namespaces:
```bash
/home/agustin/.agents/skills/token-optimizer/scripts/local_sandbox_runner.sh <comando>
```

---

## 31. Persistent Remote VPS Execution & Output Pruner (< 8 ms)
Executes remote commands on VPS via persistent SSH socket with automatic output pruning:
```bash
agy-opt vps-run "<comando>"
```

---

## 32. Surgical Remote VPS Reader & AST Streamer
Reads exact line ranges or streams remote Python AST without downloading full files:
```bash
# Read line range
agy-opt vps-read <archivo_remoto> 1 40

# Stream remote AST
python3 /home/agustin/.agents/skills/token-optimizer/scripts/vps_reader.py <archivo_remoto> --ast
```

---

## 33. Surgical Remote VPS Patcher (In-Place Modifications)
Applies targeted 5-line patches directly to files on the VPS with syntax validation:
```bash
agy-opt vps-patch <archivo_remoto> --target "<viejo>" --replacement "<nuevo>"
```

---

## 34. Remote Symbol Sync to Local RAM (0 ms Navigation)
Downloads and indexes remote VPS project symbols directly into your local RAM `symbols.db`:
```bash
agy-opt vps-index [directorio_remoto]
```

---

## 35. Ultra-Dense VPS Health Monitor (< 50 Tokens)
Summarizes CPU load, RAM, disk, and Docker containers in a 4-line consolidated block:
```bash
agy-opt vps-health
```

---

## 36. Plan Mode Auditor (SSOT 5-Section Validation)
Verifies that architecture plans adhere to the 5 SSOT sections, ports, and leave `src/` untouched:
```bash
agy-opt audit-plan [spec.md]
```

---

## 37. Accept-Edits & Build Mode Auditor (Constraint Gauntlet)
Audits git diffs against the 5 Uncle Bob constraint batteries, running `ruff --fix` at $0 cost:
```bash
agy-opt audit-edits [directorio_repo]
```

---

## 38. Plan Context Precompiler (96% Token Reduction in /plan)
Precompiles the complete architectural map in CPU/RAM before planning:
```bash
agy-opt preplan [directorio]
```

---

## 39. Plan Artifact Scaffolder (Deterministic Plan Scaffolding)
Generates full SSOT plan skeletons, Git metadata, and Mermaid diagrams on CPU:
```bash
agy-opt scaffold-plan <nombre_plan> [ruta_salida]
```

---

## 40. Plan AST Impact Simulator (Dependency Simulation)
Calculates dependent modules and callers in `symbols.db` before applying a plan:
```bash
agy-opt plan-impact <simbolo_o_archivo>
```

---

## 41. Plan Test Scaffolder (TDD Test Generator with Mocks)
Generates `@pytest.mark.parametrize` suites with `abc.ABC` mock classes directly on CPU:
```bash
agy-opt scaffold-tests [ports_file.py] [salida_test.py]
```

---

## 42. Clean Architecture DIP Auditor (Layer Direction Invariance)
Audits the Dependency Inversion Principle via AST to verify inward-only dependencies:
```bash
agy-opt audit-dip [directorio_src]
```

---

## 43. Plan Differential Optimizer (Surgical Section Updates)
Replaces individual markdown sections (`## 1` to `## 5`) in `spec.md` without re-emitting the full document:
```bash
agy-opt plan-diff --section <1-5> --content "<nuevo_texto>" [spec.md]
```

---

## 44. Diátaxis & SDD Documentation Initializer
Scaffolds the full Diátaxis documentation structure (`docs/explanation`, `how-to`, `reference`, `adr`) and `specs/` in 5 ms:
```bash
agy-opt init-docs [directorio_raiz]
```

---

## 45. Sequential ADR Generator (Architecture Decision Records)
Detects sequential indices and creates formal ADRs (`docs/adr/0001_<slug>.md`):
```bash
agy-opt adr <titulo_decision> [directorio_repo]
```

---

## 46. SDD Spec Archiver & Context Pruner
Archives completed specifications into `specs/archive/` and resets `spec.md` to keep context < 300 tokens:
```bash
agy-opt archive-spec [archivo_spec.md] [directorio_repo]
```

---

## 47. Documentation Health & Link Linter (Diátaxis Integrity)
Audits that markdown links are not broken, ADRs are sequentially numbered, and structure is valid:
```bash
agy-opt audit-docs [directorio_repo]
```

---

## 48. Automated Git & ADR Changelog Generator (Keep a Changelog)
Compiles conventional git commits and ADRs into a standardized `CHANGELOG.md` in 5 ms:
```bash
agy-opt changelog [directorio_repo]
```

---

## 49. Repository Topology & Destination Validator (Pre-Plan Structure)
Analyzes repo structure (< 10 ms) and provides a canonical destination matrix in < 80 tokens:
```bash
agy-opt validate-tree [directorio_repo]
```

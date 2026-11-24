# Chain of Thoughts (`chain-of-thoughts` / `zoth-cot`)

Zero-dependency working memory engine, cryptographic SHA-256 Merkle reasoning DAG, CLI, HTTP REST API, interactive HTML5 Braille DAG Studio, and stdio JSON-RPC 2.0 MCP server for AI agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-000000.svg)](https://opensource.org/licenses/MIT)
[![MCP: JSON-RPC 2.0 stdio](https://img.shields.io/badge/MCP-JSON--RPC_2.0_Stdio-000000)](https://github.com/1nc0gn30/chain-of-thoughts)
[![Dependencies: Zero](https://img.shields.io/badge/Dependencies-Zero-000000)](https://github.com/1nc0gn30/chain-of-thoughts)
[![Open Access: 100% Free](https://img.shields.io/badge/Access-100%25_Free_%26_Unlocked-000000)](https://nullai.tech)

---

## What It Does

`chain-of-thoughts` gives stateless local (`Ollama`) and cloud LLM agents persistent, auditable working memory backed by a single portable JSON state file (`data/cot_memory.json`) shared across the Python MCP server, Node.js CLI, HTTP API, and browser UI:

- **Merkle Reasoning DAG with Branching & Revision**: Append reasoning nodes (`N00 -> N01 -> ...`) linked by 12-hex-char SHA-256 hashes, fork alternative branches from any ancestor node (`--parent`, `--branch`), attach normalized tags and confidence scores (`0.0–1.0`), revise earlier thoughts (`--revises` / `superseded_by`), and verify full-graph cryptographic integrity (`verify_chain`).
- **Automatic Fact & Technical Entity Extraction**: Detects and pins operator facts (`IDENTITY`, `MEMORY`, `MISSION`, `SECRET`) and indexes IPv4 addresses, ports (`1–65535`), FQDNs, local POSIX paths (excluding URL paths), CVEs, and security/dev CLI tools.
- **Rolling Context Window & Checkpoints**: Maintains a bounded multi-turn message buffer (`max_turns`, default 24) and synthesizes condensed checkpoints at configurable intervals.
- **Prompt Compilation & Trace Export**: Compiles `<CHAIN_OF_THOUGHTS_MEMORY>` prompt blocks for LLM system prompts and exports full traces to Markdown or JSON.
- **12-Tool Zero-Dependency MCP Server (`zoth-cot-mcp`)**: Speaks JSON-RPC 2.0 over stdio (both NDJSON and UTF-8 byte-accurate `Content-Length` framing) using only the Python 3 standard library.
- **Interactive Client-Side Web Studio (`public/index.html`)**: 60fps HTML5 Canvas DAG visualizer (renders branched parent linkages), live turn simulator, pinned facts manager, entity table, XML/JSON/Markdown prompt compiler, and JSON/Markdown import & export.

---

## Installation & Quick Start

Requires **Python 3.9+** (for the MCP server and test suite) and/or **Node.js 18+** (for the CLI and HTTP server). Zero third-party packages are needed.

```bash
git clone https://github.com/1nc0gn30/chain-of-thoughts.git
cd chain-of-thoughts

# Run the test suite (unit + MCP stdio + CLI + HTTP integration)
python3 -m unittest discover -s tests -v
# or
npm test

# Start the Web Studio & REST API (:8145)
node server.js

# Run the CLI
./bin/zoth-cot --help
./bin/zoth-cot --tree

# Run the MCP server over stdio
./bin/zoth-cot-mcp
```

Set `ZOTH_COT_DATA_FILE=/path/to/cot_memory.json` (or pass `--file <path>` to `zoth-cot`) to isolate memory per workspace or project.

---

## CLI Reference (`bin/zoth-cot`)

All commands support `--json` for machine-readable output and `--file <path>` to override the state file.

```bash
# Display the Merkle DAG, active branch, and pinned facts
./bin/zoth-cot --tree

# Pin and unpin facts
./bin/zoth-cot --pin "All egress must stay on loopback" --category SECURITY
./bin/zoth-cot --unpin fact-abc123               # deactivate
./bin/zoth-cot --unpin fact-abc123 --delete      # permanently remove

# Append reasoning steps with branching, tags, confidence, and revision
./bin/zoth-cot --step "Initial hypothesis: DNS timeout" --phase DEDUCTION --tag net,dns --confidence 0.65
./bin/zoth-cot --step "Alternative: TLS handshake stall" --branch tls-branch --parent N00 --tag tls --confidence 0.92 --revises N01

# Manage branches
./bin/zoth-cot --branches
./bin/zoth-cot --checkout main
./bin/zoth-cot --checkout experiment-2 --target N01

# Record conversation turns (extracts entities automatically)
./bin/zoth-cot --turn "Auditing 10.0.2.15:8145 for CVE-2024-3094 using nmap" --role user

# Search & filter across facts, thoughts, turns, and entities
./bin/zoth-cot --recall "10.0.2.15"
./bin/zoth-cot --search --branch tls-branch --tag tls --min-confidence 0.8

# Verify cryptographic Merkle hashes & parent pointers (exits 1 if tampered/broken)
./bin/zoth-cot --verify

# Summary stats, prompt compilation, trace export, and clearing turns
./bin/zoth-cot --stats
./bin/zoth-cot --compile --base "You are a systems auditor."
./bin/zoth-cot --export markdown --out trace.md
./bin/zoth-cot --export json --out trace.json
./bin/zoth-cot --clear
```

---

## MCP Server (`zoth-cot-mcp` / `zoth_cot_mcp.py`)

### Exposed MCP Tools (12)

| Tool | Key Arguments | Purpose |
| :--- | :--- | :--- |
| `cot_status` | *(none)* | Session status, head hash, active branch, pinned facts, entities, and recent turns. |
| `cot_add_turn` | `role`, `content` | Record a conversation turn with automatic entity & fact extraction and checkpoint synthesis. |
| `cot_pin_fact` | `fact`, `category?` | Pin a persistent fact into working memory. |
| `cot_unpin_fact` | `fact_id`, `delete?` | Deactivate or permanently delete a pinned fact by ID. |
| `cot_add_step` | `thought`, `phase?`, `parent_hash?`, `branch?`, `tags?`, `confidence?`, `revises?` | Append a SHA-256 linked reasoning node to the Merkle DAG. |
| `cot_branches` | `action` (`list`\|`checkout`), `branch?`, `target?` | List all DAG branches or switch/create a branch from any node. |
| `cot_compile_prompt` | `base_prompt?`, `branch?` | Compile the `<CHAIN_OF_THOUGHTS_MEMORY>` prompt block for LLM injection. |
| `cot_search` | `query?`, `phase?`, `branch?`, `tag?`, `min_confidence?`, `category?`, `limit?` | Keyword and structured-filter search across facts, thoughts, turns, and entities. |
| `cot_verify` | *(none)* | Verify SHA-256 hashes and parent links across the entire DAG. |
| `cot_stats` | *(none)* | Aggregate counts by phase, branch, tag, entity category, confidence, and estimated tokens. |
| `cot_export` | `format` (`markdown`\|`json`) | Export the complete reasoning trace, facts, entities, and turns. |
| `cot_clear_turns` | *(none)* | Clear the rolling turn buffer while preserving pinned facts and DAG nodes. |

### Client Configuration

Replace `/path/to/chain-of-thoughts` with your local clone path. Set `ZOTH_COT_DATA_FILE` in `env` if you want a custom memory path.

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "zoth-cot": {
      "command": "python3",
      "args": ["/path/to/chain-of-thoughts/zoth_cot_mcp.py"],
      "env": {
        "ZOTH_COT_DATA_FILE": "/path/to/cot_memory.json"
      }
    }
  }
}
```

#### Claude Code
```bash
claude mcp add zoth-cot -- python3 /path/to/chain-of-thoughts/zoth_cot_mcp.py
```

#### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "zoth-cot": {
      "command": "/path/to/chain-of-thoughts/bin/zoth-cot-mcp"
    }
  }
}
```

#### Antigravity / Gemini CLI (`~/.gemini/antigravity-cli/mcp/zoth-cot.json`)
```json
{
  "mcpServers": {
    "zoth-cot": {
      "command": "python3",
      "args": ["/path/to/chain-of-thoughts/zoth_cot_mcp.py"]
    }
  }
}
```

#### Hermes (`~/.hermes/config.yaml`)
```yaml
mcp_servers:
  zoth-cot:
    command: python3
    args:
      - /path/to/chain-of-thoughts/zoth_cot_mcp.py
```

#### Windsurf (`~/.codeium/windsurf/mcp_config.json`)
```json
{
  "mcpServers": {
    "zoth-cot": {
      "command": "python3",
      "args": ["/path/to/chain-of-thoughts/zoth_cot_mcp.py"]
    }
  }
}
```

---

## HTTP Server & REST API (`server.js`)

Run `node server.js` (default port `8145`, override via `PORT`). State reloads automatically when modified on disk by `zoth-cot` or `zoth-cot-mcp`.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health`, `/api/health` | `GET` | Service health, node count, active branch, and head hash. |
| `/api/state` | `GET` | Full working memory state JSON. |
| `/api/stats` | `GET` | Aggregate counts across phases, branches, tags, entities, and integrity. |
| `/api/verify` | `GET` | Cryptographic Merkle DAG verification report. |
| `/api/search` | `GET` | Query parameters: `q`, `phase`, `branch`, `tag`, `min_confidence`. |
| `/api/export` | `GET` | Query parameter: `format=markdown` or `format=json`. |
| `/api/pin` | `POST` | JSON `{ "fact": "...", "category": "SECURITY" }`. |
| `/api/unpin` | `POST` | JSON `{ "fact_id": "...", "delete": false }`. |
| `/api/turn` | `POST` | JSON `{ "role": "user", "content": "..." }`. |
| `/api/step` | `POST` | JSON `{ "thought": "...", "phase": "DEDUCTION", "branch": "main", "tags": [], "confidence": 0.9 }`. |
| `/api/clear` | `POST` | Clear rolling conversation turns (preserves pinned facts). |

---

## Open Access & Support

`chain-of-thoughts` is MIT-licensed, 100% free, and unlocked with zero paywalls.

- **Buy Us a Coffee (Stripe)**: https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X
- **Solana Tip Address**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`

Engineered by [1nc0gn30](https://github.com/1nc0gn30) • [NullAI Platform](https://nullai.tech)

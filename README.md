# ◈ Chain of Thoughts (`chain-of-thoughts` // `zoth-cot`)

> **Cryptographic Merkle Working Memory DAG, Automatic Fact Extraction & Multi-Turn Context Engine for Embodied AI Agents (`ZothOS`, `ZothOS-Lite`, `Zoth Studio v2`)**

[![License: MIT](https://img.shields.io/badge/License-MIT-000000.svg)](https://opensource.org/licenses/MIT)
[![Engine: Merkle CoT DAG](https://img.shields.io/badge/Memory_DAG-SHA256_Merkle_Chain-000000)](https://github.com/1nc0gn30/chain-of-thoughts)
[![UI: 1-Bit Braille + Bayer 8x8](https://img.shields.io/badge/UI-1--Bit_Braille_%2B_Bayer_8x8-FFFFFF)](https://github.com/1nc0gn30/chain-of-thoughts)
[![MCP: JSON-RPC 2.0 stdio](https://img.shields.io/badge/MCP-JSON--RPC_2.0_Stdio-000000)](https://github.com/1nc0gn30/chain-of-thoughts)
[![Open Access: 100% Free](https://img.shields.io/badge/Access-100%25_Free_%26_Unlocked-000000)](https://nullai.tech)

**Chain of Thoughts (`zoth-cot`)** solves stateless LLM amnesia in local and cloud agentic environments. Instead of sending isolated single-turn prompts to local models (`Ollama`) or cloud providers (`Anthropic Claude`, `OpenAI GPT-4o`, `xAI Grok-3`, `Google Gemini`, `DeepSeek R1`), **Chain of Thoughts** maintains a **Cryptographic Merkle Working Memory DAG** that:

1. **Automatically Extracts & Pins Semantic Facts** (`IDENTITY`, `MISSION`, `TARGET`, `HARDWARE`, `MEMORY`, `SECRET`) from natural conversation.
2. **Maintains a Rolling Multi-Turn Context Window** (`24 turns / 48 messages`) with automatic checkpoint compression.
3. **Extracts Technical Entities in Real-Time** (IPv4 addresses, network ports, FQDN domains, POSIX paths, CVE identifiers, and security/dev tools).
4. **Constructs an Auditable 4-Stage Reasoning Node (`N00 -> N01 -> N02...`)** on every turn, cryptographically linking `parentHash -> nodeHash`.
5. **Exposes a Zero-Dependency Standard-I/O JSON-RPC 2.0 MCP Server (`zoth-cot-mcp`)** enabling plug-and-play integration with Claude Code, Cursor, Gemini CLI, and Windsurf.

---

## ⣿ Architecture & Synaptic Thought DAG

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║ ◈ ZOTH CHAIN OF THOUGHTS (CoT) // WORKING MEMORY DAG                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ┌──────────────┐       ┌──────────────┐       ┌──────────────┐             ║
║   │  N00 GENESIS │══⣿══▶│  N01 [a8f31c]│══⣿══▶│  N02 [5a4165]│ (HEAD)      ║
║   │  0000000000  │       │  ◀ N00       │       │  ◀ N01       │             ║
║   └──────┬───────┘       └──────┬───────┘       └──────┬───────┘             ║
║          │                      │                      │                     ║
║          ▼                      ▼                      ▼                     ║
║   ┌──────────────────────────────────────────────────────────────────────┐   ║
║   │ ◈ PINNED WORKING MEMORY VAULT (Auto-Extracted + Operator Pinned)     │   ║
║   │  • [IDENTITY] Operator callsign: FALCON-7                            │   ║
║   │  • [MISSION]  Active focus / target: 10.0.2.15:8080                  │   ║
║   │  • [CVE]      Vulnerability tracking: CVE-2024-3094                  │   ║
║   │  • [ENTITIES] IPs: 10.0.2.15 | Ports: 8080 | Tools: nmap, zoth-cot  │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ⚡ Key Features

- **Model Context Protocol (MCP) Server (`bin/zoth-cot-mcp` & `zoth_cot_mcp.py`)**:
  - Pure Python zero-dependency standard-I/O JSON-RPC 2.0 server.
  - Native tools for memory status, turn recording, fact pinning, reasoning steps, prompt compilation, and keyword recall.
- **Automatic Semantic Fact & Entity Extraction**:
  - Automatically identifies operator identities (`my name is...`), memories (`remember that...`), targets (`target is...`), and credentials (`secret word is...`).
  - Regex extractors for IPv4 addresses, ports (`:8080`, `tcp/443`), domains (`nullai.tech`), paths (`/etc/passwd`), CVEs (`CVE-2024-3094`), and security tools (`nmap`, `wireshark`, `gitleaks`).
- **Rolling Checkpoint Compression**:
  - Synthesizes conversation history into condensed context checkpoints at turn intervals, preventing context-window exhaustion during long sessions.
- **Prompt Compilation Ready for LLM Injection**:
  - Emits formatted `<CHAIN_OF_THOUGHTS_MEMORY>` prompt blocks for immediate prepending to system prompts or full message arrays.
- **60FPS 1-Bit Braille (`U+2800`) + Ordered Bayer 4×4/8×8 Dither Synaptic DAG Visualizer**:
  - In-browser visualizer rendering linked thought nodes and traveling Unicode Braille synaptic packets.
- **Dual Terminal CLI & REST API**:
  - Inspect the Merkle tree with `./bin/zoth-cot --tree` or interact via HTTP endpoints (`/api/state`, `/api/pin`, `/api/clear`).

---

## 🔌 Model Context Protocol (MCP) Server

The MCP server connects `ChainOfThoughts` working memory directly to your coding assistant or agent.

### Exposed MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `cot_status` | *(none)* | Returns session status, head hash, pinned facts, entities, and recent turns. |
| `cot_add_turn` | `role` (str), `content` (str) | Records a conversation turn with automatic entity & fact extraction and rolling checkpoint synthesis. |
| `cot_pin_fact` | `fact` (str), `category` (str, default `"PINNED"`) | Pins a critical fact so the agent never forgets it across turns. |
| `cot_add_step` | `thought` (str), `phase` (str, default `"REASONING"`) | Appends a reasoning node (`Nxx`) to the Cryptographic Merkle DAG. |
| `cot_compile_prompt` | `base_prompt` (str, optional) | Compiles the structured `<CHAIN_OF_THOUGHTS_MEMORY>` prompt block ready for LLM injection. |
| `cot_search` | `query` (str), `limit` (int, default `10`) | Keyword search across conversation turns, pinned facts, and thoughts. |

---

### Client Configuration

#### 1. Claude Code

Run with the Claude Code CLI:
```bash
claude mcp add zoth-cot -- python3 /path/to/chain-of-thoughts/zoth_cot_mcp.py
```

Or configure directly in `~/.claude.json`:
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

#### 2. Cursor

Add to `.cursor/mcp.json` or **Cursor Settings > Features > MCP**:
```json
{
  "mcpServers": {
    "zoth-cot": {
      "command": "/path/to/chain-of-thoughts/bin/zoth-cot-mcp"
    }
  }
}
```

#### 3. Gemini CLI / Antigravity

Add to your MCP configuration (e.g. `~/.gemini/antigravity-cli/mcp/zoth-cot.json`):
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

#### 4. Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:
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

## 🧪 Comprehensive Unit Test Suite

The repository includes a comprehensive Python standard library `unittest` suite covering all features with 100% pass rate:

```bash
# Run tests directly with unittest
python3 -m unittest discover -s tests -v

# Or via npm
npm test
```

### Test Coverage Highlights
- **Entity Extraction**: Valid IPv4 filtering, port boundaries (1–65535, formats `:8080`, `tcp/443`, `port 22`), FQDN domains, POSIX paths, CVE normalization, and security/dev tool identification.
- **Fact Auto-Extraction**: Natural language patterns for `IDENTITY`, `MEMORY`, `MISSION`, and `SECRET`, including deduplication logic.
- **Rolling Checkpoint Compression**: Synthesis triggers at configured turn intervals and rolling context buffer bounds.
- **Prompt Compilation**: Verification of `<CHAIN_OF_THOUGHTS_MEMORY>` block format, head hash anchoring, and multi-turn message arrays.
- **JSON-RPC 2.0 MCP Protocol**: Handshake `initialize`, `notifications/initialized`, `ping`, `tools/list`, and all 6 `tools/call` executions.

---

## 🚀 Quick Start

```bash
git clone https://github.com/1nc0gn30/chain-of-thoughts.git
cd chain-of-thoughts

# Start the Chain of Thoughts Web Studio & API Server (:8145)
node server.js

# Or run the CLI directly:
./bin/zoth-cot --tree
./bin/zoth-cot --pin "Target subnet: 10.0.2.0/24"
./bin/zoth-cot --recall "subnet"

# Launch the MCP server over stdio:
./bin/zoth-cot-mcp
```

---

## ☕ 100% Open-Access & Support

Every tool across the **ZothOS** and **NullAI** ecosystem is **100% free, open, and unlocked by default** with zero paywalls.

- **☕ Buy Us a Coffee (Stripe)**: [https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X)
- **◎ Solana Tip Address**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`

---

**Engineered by Neal Frazier Tech ([@1nc0gn30](https://github.com/1nc0gn30)) • [NullAI Platform](https://nullai.tech) • [ZothOS](https://zoth.nullai.tech)**

# ◈ Chain of Thoughts (`chain-of-thoughts` // `zoth-cot`)

> **Cryptographic Merkle Working Memory DAG, Automatic Fact Extraction & Multi-Turn Context Engine for Embodied AI Agents (`ZothOS`, `ZothOS-Lite`, `Zoth Studio v2`)**

[![License: MIT](https://img.shields.io/badge/License-MIT-000000.svg)](https://opensource.org/licenses/MIT)
[![Engine: Merkle CoT DAG](https://img.shields.io/badge/Memory_DAG-SHA256_Merkle_Chain-000000)](https://github.com/1nc0gn30/chain-of-thoughts)
[![UI: 1-Bit Braille + Bayer 8x8](https://img.shields.io/badge/UI-1--Bit_Braille_%2B_Bayer_8x8-FFFFFF)](https://github.com/1nc0gn30/chain-of-thoughts)
[![Open Access: 100% Free](https://img.shields.io/badge/Access-100%25_Free_%26_Unlocked-000000)](https://nullai.tech)

**Chain of Thoughts (`zoth-cot`)** solves stateless LLM amnesia in local and cloud agentic environments. Instead of sending isolated single-turn prompts to local models (`Ollama`) or cloud providers (`Anthropic Claude`, `OpenAI GPT-4o`, `xAI Grok-3`, `Google Gemini`, `DeepSeek R1`), **Chain of Thoughts** maintains a **Cryptographic Merkle Working Memory DAG** that:

1. **Automatically Extracts & Pins Semantic Facts** (`IDENTITY`, `MISSION`, `TARGET`, `HARDWARE`, `MEMORY`) from natural conversation.
2. **Maintains a Rolling Multi-Turn Context Window** (`24 turns / 48 messages`) injected into `/api/chat` payloads across all AI providers.
3. **Constructs an Auditable 4-Stage Reasoning Node (`N00 -> N01 -> N02...`)** on every turn, cryptographically linking `parentHash -> nodeHash` with explicit traces for:
   - `├─ [1. MEMORY RECALL]`: Which prior turns and pinned semantic facts were retrieved.
   - `├─ [2. CONTEXT LINK]`: How the current prompt connects to the prior conversation turn.
   - `├─ [3. DEDUCTION]`: Mood selection, model routing, and context message count.
   - `└─ [4. SYNTHESIS]`: Spoken/text output delivered to the agent (and Kokoro ONNX neural voice).

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
║   │  • [MISSION]  Active focus / target: 10.0.2.15                       │   ║
║   │  • [HARDWARE] PipeWire Pro-Audio Duplex (ALC3266 + HDMI + Ray-Ban)   │   ║
║   └──────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ⚡ Key Features

- **Zero-Amnesia Multi-Turn Chat Router (`/api/agent/chat` & `/api/cot/*`)**:
  - Converts stateless LLM calls into stateful, context-aware conversations across **Ollama** (`qwen2.5`, `zoth-hermes`, `hermes3-teknium`, `zoth-coder`) and cloud APIs (**Claude 3.7 Sonnet**, **GPT-4o**, **Grok-3**, **Gemini 2.5 Pro**, **DeepSeek R1**).
- **Automatic Semantic Fact Extraction**:
  - Detects callsigns, targets, reminders, and active mission parameters in real time as you speak or type, pinning them into the permanent system context.
- **60FPS 1-Bit Braille (`U+2800`) + Ordered Bayer 4×4/8×8 Dither Synaptic DAG Visualizer**:
  - Renders live linked thought nodes and travelling Unicode Braille synaptic packets in the browser.
- **Terminal CLI (`zoth-cot`)**:
  - Inspect the Merkle Thought Tree, pin facts from bash scripts, search recalled nodes, or reset session turns directly from the command line.

---

## 🚀 Quick Start

```bash
git clone https://github.com/1nc0gn30/chain-of-thoughts.git
cd chain-of-thoughts

# Start the Chain of Thoughts Web Studio & API Server (:8145 / :8149)
node server.js

# Or use the CLI directly:
./bin/zoth-cot --tree
./bin/zoth-cot --pin "Target subnet: 10.0.2.0/24"
./bin/zoth-cot --recall "subnet"
```

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/cot/state` | Returns `headHash`, `pinnedFacts`, rolling `messages`, cryptographic `nodes`, and token budget telemetry. |
| `POST` | `/api/cot/pin` | Pins a new semantic fact (`{ category, fact }`), toggles an existing fact (`{ toggleId }`), or deletes one (`{ deleteId }`). |
| `POST` | `/api/cot/recall` | Searches pinned facts and reasoning nodes matching `{ query }`. |
| `POST` | `/api/cot/clear` | Clears rolling conversation turns while preserving pinned facts (`{ clearFacts: false }`). |
| `POST` | `/api/agent/chat` | Executes a multi-turn context-enriched chat turn, appends a new Merkle CoT Node (`Nxx`), and returns lip-sync viseme timelines. |

---

## ☕ 100% Open-Access & Support

Every tool across the **ZothOS** and **NullAI** ecosystem is **100% free, open, and unlocked by default** with zero paywalls.

- **☕ Buy Us a Coffee (Stripe)**: [https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X](https://buy.stripe.com/3cIfZg27PdKo2D64Ocfw40X)
- **◎ Solana Tip Address**: `GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK`

---

**Engineered by Neal Frazier Tech ([@1nc0gn30](https://github.com/1nc0gn30)) • [NullAI Platform](https://nullai.tech) • [ZothOS](https://zoth.nullai.tech)**

#!/usr/bin/env python3
"""
zoth_cot_mcp.py — Chain of Thoughts (zoth-cot) Model Context Protocol (MCP) Server
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform

Zero-dependency standard-I/O JSON-RPC 2.0 Model Context Protocol server exposing
the ChainOfThoughts Cryptographic Merkle Working Memory DAG, Automatic Fact & Entity
Extraction, Rolling Checkpoint Synthesis, and Prompt Compilation.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "zoth-cot-mcp"
SERVER_VERSION = "1.0.0"

GENESIS_SEED = "ZOTH-COT-GENESIS"

# Known security, reversing, development, and AI tools for entity detection
KNOWN_SECURITY_DEV_TOOLS = {
    "nmap",
    "wireshark",
    "metasploit",
    "burpsuite",
    "sqlmap",
    "nikto",
    "hydra",
    "john",
    "aircrack-ng",
    "ghidra",
    "radare2",
    "gitleaks",
    "ollama",
    "neovim",
    "tmux",
    "ripgrep",
    "curl",
    "wget",
    "docker",
    "git",
    "python3",
    "tcpdump",
    "ffuf",
    "gobuster",
    "hashcat",
    "socat",
    "netcat",
    "tshark",
    "masscan",
    "rustc",
    "cargo",
    "zoth-envguard",
    "zoth-ghostbyte",
    "zoth-hexstrike",
    "zoth-cot",
    "zoth-comm",
    "zoth-capsule-jail",
    "zoth-node-lite",
    "zoth-braille-art",
}


def _log(msg: str) -> None:
    """Log to stderr so stdout is reserved exclusively for JSON-RPC 2.0 streams."""
    sys.stderr.write(f"[zoth-cot-mcp] {msg}\n")
    sys.stderr.flush()


def _iso_now() -> str:
    """Return ISO 8601 UTC timestamp string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class ChainOfThoughts:
    """
    Cryptographic Merkle Working Memory DAG & Multi-Turn Context Engine.
    Handles semantic fact extraction, entity extraction (IPs, ports, domains, paths, CVEs, tools),
    rolling checkpoint compression at turn intervals, and LLM prompt compilation.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_turns: int = 24,
        checkpoint_interval: int = 4,
    ) -> None:
        self.storage_path = storage_path
        self.max_turns = max_turns
        self.checkpoint_interval = checkpoint_interval

        genesis_hash = hashlib.sha256(GENESIS_SEED.encode("utf-8")).hexdigest()[:12]
        self.head_hash: str = genesis_hash
        self.pinned_facts: List[Dict[str, Any]] = [
            {
                "id": "fact-operator",
                "category": "IDENTITY",
                "fact": "Operator: Neal (@1nc0gn30) • Sovereign AI Workstation.",
                "active": True,
                "ts": _iso_now(),
            },
            {
                "id": "fact-engine",
                "category": "ARCHITECTURE",
                "fact": "Chain of Thoughts (zoth-cot) Merkle DAG Working Memory Engine.",
                "active": True,
                "ts": _iso_now(),
            },
        ]
        self.messages: List[Dict[str, Any]] = []
        self.nodes: List[Dict[str, Any]] = [
            {
                "id": "N00",
                "hash": genesis_hash,
                "parent_hash": "000000000000",
                "parentHash": "000000000000",
                "thought": "[GENESIS] Initialize Chain of Thoughts Working Memory DAG",
                "prompt": "[GENESIS] Initialize Chain of Thoughts Working Memory DAG",
                "phase": "GENESIS",
                "steps": {
                    "recall": "Loaded core sovereign engrams.",
                    "context_link": f"Initialized {self.max_turns}-turn rolling context window.",
                    "contextLink": f"Initialized {self.max_turns}-turn rolling context window.",
                    "deduction": "Armed multi-turn LLM router (Ollama + Cloud Providers).",
                    "synthesis": "Chain of Thoughts DAG online.",
                },
                "mood": "TACTICAL",
                "tokens": 64,
                "timestamp": _iso_now(),
            }
        ]
        self.entities: Dict[str, Set[str]] = {
            "ips": set(),
            "ports": set(),
            "domains": set(),
            "paths": set(),
            "cves": set(),
            "tools": set(),
        }
        self.checkpoints: List[Dict[str, Any]] = []
        self.last_checkpoint: Optional[Dict[str, Any]] = None

        if self.storage_path and os.path.exists(self.storage_path):
            self.load_state()

    # -------------------------------------------------------------------------
    # State Persistence
    # -------------------------------------------------------------------------

    def load_state(self) -> None:
        """Load state from disk, supporting both camelCase and snake_case formats."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.head_hash = data.get("headHash") or data.get("head_hash") or self.head_hash
            self.max_turns = data.get("maxTurns") or data.get("max_turns") or self.max_turns

            raw_facts = data.get("pinnedFacts") or data.get("pinned_facts")
            if isinstance(raw_facts, list):
                self.pinned_facts = raw_facts

            raw_msgs = data.get("messages") or data.get("turns")
            if isinstance(raw_msgs, list):
                self.messages = raw_msgs

            raw_nodes = data.get("nodes")
            if isinstance(raw_nodes, list):
                normalized_nodes = []
                for n in raw_nodes:
                    node = dict(n)
                    if "parentHash" in node and "parent_hash" not in node:
                        node["parent_hash"] = node["parentHash"]
                    if "prompt" in node and "thought" not in node:
                        node["thought"] = node["prompt"]
                    if "phase" not in node:
                        node["phase"] = node.get("mood", "REASONING")
                    normalized_nodes.append(node)
                self.nodes = normalized_nodes

            raw_entities = data.get("entities")
            if isinstance(raw_entities, dict):
                for k, v in raw_entities.items():
                    if k in self.entities and isinstance(v, list):
                        self.entities[k] = set(str(x) for x in v)

            raw_checkpoints = data.get("checkpoints")
            if isinstance(raw_checkpoints, list):
                self.checkpoints = raw_checkpoints
                if self.checkpoints:
                    self.last_checkpoint = self.checkpoints[-1]

        except Exception as e:
            _log(f"Error loading state from {self.storage_path}: {e}")

    def save_state(self) -> None:
        """Save state to disk atomically."""
        if not self.storage_path:
            return
        try:
            target_dir = os.path.dirname(os.path.abspath(self.storage_path))
            os.makedirs(target_dir, exist_ok=True)

            data = {
                "headHash": self.head_hash,
                "head_hash": self.head_hash,
                "maxTurns": self.max_turns,
                "max_turns": self.max_turns,
                "pinnedFacts": self.pinned_facts,
                "pinned_facts": self.pinned_facts,
                "messages": self.messages,
                "turns": self.messages,
                "nodes": self.nodes,
                "entities": {k: sorted(list(v)) for k, v in self.entities.items()},
                "checkpoints": self.checkpoints,
                "last_checkpoint": self.last_checkpoint,
                "updated_at": _iso_now(),
            }
            tmp_path = f"{self.storage_path}.tmp.{os.getpid()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.storage_path)
        except Exception as e:
            _log(f"Error saving state to {self.storage_path}: {e}")

    # -------------------------------------------------------------------------
    # Entity Extraction
    # -------------------------------------------------------------------------

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts structured entities from text:
        - IPs: Valid IPv4 addresses
        - Ports: Port numbers (1-65535) associated with network traffic or explicit mentions
        - Domains: FQDN hostnames
        - Paths: Absolute or relative POSIX file paths
        - CVEs: Common Vulnerabilities and Exposures IDs
        - Tools: Security, reversing, networking, and system CLI tools
        """
        p = str(text or "")
        found_ips: Set[str] = set()
        found_ports: Set[str] = set()
        found_domains: Set[str] = set()
        found_paths: Set[str] = set()
        found_cves: Set[str] = set()
        found_tools: Set[str] = set()

        if not p.strip():
            return {
                "ips": [],
                "ports": [],
                "domains": [],
                "paths": [],
                "cves": [],
                "tools": [],
            }

        # 1. IPs (strict IPv4 check)
        ip_pattern = re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
        )
        for match in ip_pattern.finditer(p):
            found_ips.add(match.group(0))

        # 2. Ports (:8080, port 22, port: 443, tcp/443, udp/53, port=8145)
        port_pattern = re.compile(
            r"(?::|(?:\b(?:port|ports|tcp|udp)\s*[:=/]?\s*))(\d{1,5})\b",
            re.IGNORECASE,
        )
        for match in port_pattern.finditer(p):
            port_val = int(match.group(1))
            if 1 <= port_val <= 65535:
                found_ports.add(str(port_val))

        # 3. CVEs (CVE-YYYY-NNNN+)
        cve_pattern = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
        for match in cve_pattern.finditer(p):
            found_cves.add(match.group(0).upper())

        # 4. Paths (POSIX absolute /etc/..., /var/..., or relative ./bin/...)
        path_pattern = re.compile(
            r"(?:/(?:[a-zA-Z0-9_\-.]+/)+[a-zA-Z0-9_\-.]+|(?:\./|\.\./)[a-zA-Z0-9_\-./]+)"
        )
        for match in path_pattern.finditer(p):
            candidate = match.group(0).rstrip(".,:;!?)\"'>")
            # Filter out URL schemes or pure slashes
            if not candidate.startswith("//") and len(candidate) > 2:
                found_paths.add(candidate)

        # 5. Domains (FQDNs, excluding pure IPs and common non-domain extensions)
        domain_pattern = re.compile(
            r"\b(?!(?:\d{1,3}\.){3}\d{1,3})(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|io|tech|pro|ai|dev|app|co|xyz|me|info|biz|cloud|network|site|mil)\b",
            re.IGNORECASE,
        )
        for match in domain_pattern.finditer(p):
            found_domains.add(match.group(0).lower())

        # 6. Tools
        lower_p = p.lower()
        for tool in KNOWN_SECURITY_DEV_TOOLS:
            pattern = rf"\b{re.escape(tool)}\b"
            if re.search(pattern, lower_p):
                found_tools.add(tool)

        # Update cumulative entity index
        self.entities["ips"].update(found_ips)
        self.entities["ports"].update(found_ports)
        self.entities["domains"].update(found_domains)
        self.entities["paths"].update(found_paths)
        self.entities["cves"].update(found_cves)
        self.entities["tools"].update(found_tools)

        return {
            "ips": sorted(list(found_ips)),
            "ports": sorted(list(found_ports), key=lambda x: int(x)),
            "domains": sorted(list(found_domains)),
            "paths": sorted(list(found_paths)),
            "cves": sorted(list(found_cves)),
            "tools": sorted(list(found_tools)),
        }

    # -------------------------------------------------------------------------
    # Fact Auto-Extraction
    # -------------------------------------------------------------------------

    def auto_extract_facts(self, prompt_text: str) -> List[Dict[str, Any]]:
        """
        Auto-extracts permanent facts from prompt text:
        - "my name is...", "call me..." -> IDENTITY
        - "remember that...", "don't forget that..." -> MEMORY
        - "target is...", "auditing...", "working on..." -> MISSION
        - "secret word is...", "passphrase is..." -> SECRET
        """
        p = str(prompt_text or "").strip()
        if not p or len(p) < 4:
            return []

        extracted: List[Dict[str, Any]] = []
        patterns = [
            {
                "re": re.compile(
                    r"\b(?:my name is|call me|i am|i'm|codename is|code name is)\s+([A-Za-z0-9_@.-]{2,35})",
                    re.IGNORECASE,
                ),
                "cat": "IDENTITY",
                "prefix": "Operator identity / callsign: ",
            },
            {
                "re": re.compile(
                    r"\b(?:remember(?: that)?|don't forget(?: that)?|note that|keep in mind(?: that)?)\s+(.{4,140})",
                    re.IGNORECASE,
                ),
                "cat": "MEMORY",
                "prefix": "Explicit operator memory: ",
            },
            {
                "re": re.compile(
                    r"\b(?:target(?: ip| host| domain)? is|auditing|scanning|working on|project is|topic is)\s+([A-Za-z0-9_.:/-]{3,80})",
                    re.IGNORECASE,
                ),
                "cat": "MISSION",
                "prefix": "Active focus / target: ",
            },
            {
                "re": re.compile(
                    r"\b(?:secret word is|passphrase is|key is|pin is)\s+([A-Za-z0-9_!@#$%^&*-]{2,50})",
                    re.IGNORECASE,
                ),
                "cat": "SECRET",
                "prefix": "Pinned session token: ",
            },
        ]

        for pat in patterns:
            m = pat["re"].search(p)
            if m and m.group(1):
                clean_val = re.sub(r"[.!?]+$", "", m.group(1)).strip()
                fact_str = f"{pat['prefix']}{clean_val}"
                exists = any(
                    f.get("fact", "").lower() == fact_str.lower()
                    for f in self.pinned_facts
                )
                if not exists:
                    fact_id = (
                        f"fact-{int(time.time() * 1000):x}-{os.urandom(2).hex()}"
                    )
                    item = {
                        "id": fact_id,
                        "category": pat["cat"],
                        "fact": fact_str,
                        "active": True,
                        "ts": _iso_now(),
                    }
                    self.pinned_facts.insert(0, item)
                    extracted.append(item)

        return extracted

    # -------------------------------------------------------------------------
    # Core Memory Operations
    # -------------------------------------------------------------------------

    def pin_fact(self, fact: str, category: str = "PINNED") -> Dict[str, Any]:
        """Pin a critical fact so the agent never forgets it."""
        fact_str = str(fact or "").strip()
        cat = str(category or "PINNED").strip().upper()
        if not fact_str:
            raise ValueError("Fact string cannot be empty")

        for f in self.pinned_facts:
            if f.get("fact", "").lower() == fact_str.lower():
                f["active"] = True
                f["category"] = cat
                self.save_state()
                return f

        fact_id = f"fact-{int(time.time() * 1000):x}-{os.urandom(2).hex()}"
        item = {
            "id": fact_id,
            "category": cat,
            "fact": fact_str,
            "active": True,
            "ts": _iso_now(),
        }
        self.pinned_facts.insert(0, item)
        self.save_state()
        return item

    def add_step(
        self,
        thought: str,
        phase: str = "REASONING",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a reasoning node to the Chain of Thoughts Cryptographic Merkle DAG."""
        thought_str = str(thought or "").strip()
        phase_str = str(phase or "REASONING").strip().upper()
        if not thought_str:
            raise ValueError("Thought description cannot be empty")

        prev_hash = self.head_hash or "000000000000"
        node_idx = len(self.nodes)
        node_id = f"N{node_idx:02d}"
        now_ts = _iso_now()

        hash_payload = f"{prev_hash}|{thought_str}|{phase_str}|{now_ts}"
        node_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()[:12]
        self.head_hash = node_hash

        meta = metadata or {}
        new_node = {
            "id": node_id,
            "hash": node_hash,
            "parent_hash": prev_hash,
            "parentHash": prev_hash,
            "thought": thought_str,
            "prompt": thought_str,
            "phase": phase_str,
            "mood": meta.get("mood", "TACTICAL"),
            "steps": meta.get(
                "steps",
                {
                    "recall": f"Linked to prior head {prev_hash}.",
                    "context_link": f"Phase {phase_str} step.",
                    "contextLink": f"Phase {phase_str} step.",
                    "deduction": thought_str[:60],
                    "synthesis": thought_str,
                },
            ),
            "tokens": max(32, round(len(thought_str) / 3.8)),
            "timestamp": now_ts,
        }

        self.nodes.append(new_node)
        if len(self.nodes) > 60:
            self.nodes = self.nodes[-60:]

        self.save_state()
        return new_node

    def add_turn(self, role: str, content: str) -> Dict[str, Any]:
        """
        Record a conversation turn with automatic entity & fact extraction
        and rolling checkpoint synthesis.
        """
        r = str(role or "user").strip().lower()
        c = str(content or "").strip()
        now_ts = _iso_now()

        # 1. Extract entities and facts
        extracted_entities = self.extract_entities(c)
        extracted_facts = self.auto_extract_facts(c)

        # 2. Append message
        msg_id = f"msg-{len(self.messages) + 1}"
        msg_item = {
            "id": msg_id,
            "role": r,
            "content": c,
            "timestamp": now_ts,
            "node_hash": self.head_hash,
        }
        self.messages.append(msg_item)

        # 3. Check for rolling checkpoint compression
        turn_count = len(self.messages) // 2
        checkpoint_updated = False
        if turn_count > 0 and turn_count % self.checkpoint_interval == 0 and r == "assistant":
            self.synthesize_checkpoint()
            checkpoint_updated = True

        # Keep rolling message window constrained
        max_msgs = self.max_turns * 2
        if len(self.messages) > max_msgs:
            self.messages = self.messages[-max_msgs:]

        self.save_state()
        return {
            "turn_id": msg_id,
            "role": r,
            "content": c,
            "extracted_facts": extracted_facts,
            "extracted_entities": extracted_entities,
            "checkpoint_updated": checkpoint_updated,
            "head_hash": self.head_hash,
        }

    def synthesize_checkpoint(self) -> Dict[str, Any]:
        """
        Synthesize a rolling checkpoint summarizing prior turns, active entities,
        and pinned facts, compressing earlier context for long-running sessions.
        """
        turn_count = len(self.messages) // 2
        recent = self.messages[-8:] if len(self.messages) >= 8 else self.messages

        topics: List[str] = []
        for m in recent:
            snippet = m.get("content", "").replace("\n", " ").strip()
            if snippet:
                topics.append(f"{m.get('role', 'user')}: {snippet[:60]}")

        entity_summary_parts = []
        for k, v in self.entities.items():
            if v:
                entity_summary_parts.append(f"{k.upper()}: {', '.join(sorted(list(v))[:5])}")

        entity_str = " | ".join(entity_summary_parts) if entity_summary_parts else "None"
        active_facts = [f.get("fact") for f in self.pinned_facts if f.get("active", True)]

        summary = (
            f"Checkpoint at turn {turn_count}: {len(self.messages)} messages logged. "
            f"Active entities: [{entity_str}]. Pinned engrams: {len(active_facts)}. "
            f"Recent flow: {' -> '.join(topics[-3:]) if topics else 'Genesis session'}."
        )

        checkpoint_id = f"chk-{turn_count}-{int(time.time()):x}"
        checkpoint = {
            "id": checkpoint_id,
            "turn_index": turn_count,
            "summary": summary,
            "timestamp": _iso_now(),
        }
        self.checkpoints.append(checkpoint)
        self.last_checkpoint = checkpoint
        self.save_state()
        return checkpoint

    # -------------------------------------------------------------------------
    # Prompt Compilation
    # -------------------------------------------------------------------------

    def compile_system_prompt(self, base_prompt: str = "") -> str:
        """
        Compile the structured <CHAIN_OF_THOUGHTS_MEMORY> prompt block ready for LLM injection.
        Includes head hash, pinned facts, extracted entities, checkpoint summary, and reasoning DAG.
        """
        active_facts = [f for f in self.pinned_facts if f.get("active", True)]
        facts_lines = [
            f"- [{f.get('category', 'FACT')}] {f.get('fact')}" for f in active_facts
        ]
        facts_block = (
            "\n".join(facts_lines)
            if facts_lines
            else "- No active pinned memory facts."
        )

        entity_lines = []
        for cat in ["ips", "ports", "domains", "paths", "cves", "tools"]:
            vals = self.entities.get(cat, set())
            if vals:
                formatted_vals = ", ".join(sorted(list(vals)))
                entity_lines.append(f"- {cat.upper()}: {formatted_vals}")
        entities_block = (
            "\n".join(entity_lines)
            if entity_lines
            else "- No active technical entities extracted."
        )

        chk_block = (
            self.last_checkpoint["summary"]
            if self.last_checkpoint
            else "Genesis working memory baseline. No checkpoint compression applied yet."
        )

        recent_nodes = self.nodes[-5:]
        node_lines = [
            f"- [{n.get('id', 'N??')} // {n.get('hash', '000000')}] ({n.get('phase', 'REASONING')}): {n.get('thought', '')[:70]}"
            for n in recent_nodes
        ]
        dag_block = "\n".join(node_lines)

        memory_block = (
            f"<CHAIN_OF_THOUGHTS_MEMORY>\n"
            f"HEAD_HASH: {self.head_hash}\n"
            f"TOTAL_NODES: {len(self.nodes)} | CONVERSATION_TURNS: {len(self.messages) // 2}\n\n"
            f"[PINNED FACTS]\n{facts_block}\n\n"
            f"[EXTRACTED ENTITIES]\n{entities_block}\n\n"
            f"[ROLLING CHECKPOINT]\n{chk_block}\n\n"
            f"[RECENT REASONING CHAIN]\n{dag_block}\n\n"
            f"[CONTINUITY DIRECTIVE]\n"
            f"You are connected to the ZothOS Chain of Thoughts (zoth-cot) Working Memory DAG.\n"
            f"ALWAYS preserve context continuity from prior turns, recall operator codenames, active targets,\n"
            f"and pinned facts with zero amnesia.\n"
            f"</CHAIN_OF_THOUGHTS_MEMORY>"
        )

        base = str(base_prompt or "").strip()
        if base:
            return f"{base}\n\n{memory_block}"
        return memory_block

    def compile_messages(
        self, system_prompt: str = "", max_turns: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Compile full chat completion messages array with injected system prompt and recent turns.
        """
        limit_turns = max_turns if max_turns is not None else self.max_turns
        compiled_sys = self.compile_system_prompt(system_prompt)
        msgs: List[Dict[str, str]] = [{"role": "system", "content": compiled_sys}]

        recent_msgs = self.messages[-(limit_turns * 2) :] if limit_turns > 0 else self.messages
        for m in recent_msgs:
            msgs.append({
                "role": m.get("role", "user"),
                "content": str(m.get("content", "")),
            })
        return msgs

    # -------------------------------------------------------------------------
    # Search & Status
    # -------------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Keyword search across turns, pinned facts, and thoughts."""
        q = str(query or "").strip().lower()
        if not q:
            return {
                "query": "",
                "matched_facts": [],
                "matched_turns": [],
                "matched_thoughts": [],
                "total_matches": 0,
            }

        terms = [t for t in q.split() if len(t) >= 2]

        def matches(text: str) -> bool:
            lower_text = text.lower()
            return q in lower_text or any(t in lower_text for t in terms)

        matched_facts = [
            f for f in self.pinned_facts if matches(f.get("fact", "") + " " + f.get("category", ""))
        ][:limit]

        matched_turns = [
            m for m in self.messages if matches(m.get("content", "") + " " + m.get("role", ""))
        ][:limit]

        matched_thoughts = [
            n for n in self.nodes if matches(n.get("thought", "") + " " + n.get("phase", ""))
        ][:limit]

        total = len(matched_facts) + len(matched_turns) + len(matched_thoughts)
        return {
            "query": query,
            "matched_facts": matched_facts,
            "matched_turns": matched_turns,
            "matched_thoughts": matched_thoughts,
            "total_matches": total,
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns session status, pinned facts, entities, and recent turns."""
        active_facts = [f for f in self.pinned_facts if f.get("active", True)]
        total_chars = sum(len(f.get("fact", "")) for f in active_facts) + sum(
            len(m.get("content", "")) for m in self.messages
        )
        est_tokens = max(48, round(total_chars / 3.8))

        return {
            "ok": True,
            "head_hash": self.head_hash,
            "node_count": len(self.nodes),
            "turn_count": len(self.messages) // 2,
            "message_count": len(self.messages),
            "max_turns": self.max_turns,
            "est_tokens": est_tokens,
            "pinned_facts": self.pinned_facts,
            "entities": {k: sorted(list(v)) for k, v in self.entities.items()},
            "recent_turns": self.messages[-10:],
            "last_checkpoint": self.last_checkpoint,
            "storage_path": self.storage_path,
        }


# =============================================================================
# Model Context Protocol (MCP) JSON-RPC 2.0 Server
# =============================================================================

class MCPServer:
    """
    Standard-I/O JSON-RPC 2.0 Model Context Protocol (MCP) server.
    Exposes ChainOfThoughts tools to Claude Code, Gemini CLI, Cursor, and Windsurf.
    """

    def __init__(self, cot: Optional[ChainOfThoughts] = None, storage_path: Optional[str] = None) -> None:
        self.cot = cot or ChainOfThoughts(storage_path=storage_path)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_tools()

    def _register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.handlers[name] = handler

    def _register_tools(self) -> None:
        # 1. cot_status
        self._register_tool(
            name="cot_status",
            description="Returns session status, pinned facts, entities, and recent turns.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=self._tool_cot_status,
        )

        # 2. cot_add_turn
        self._register_tool(
            name="cot_add_turn",
            description="Records a conversation turn (role, content) with automatic entity & fact extraction and rolling checkpoint synthesis.",
            input_schema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["user", "assistant", "system"],
                        "description": "Speaker role in conversation turn.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content of the conversation turn.",
                    },
                },
                "required": ["role", "content"],
            },
            handler=self._tool_cot_add_turn,
        )

        # 3. cot_pin_fact
        self._register_tool(
            name="cot_pin_fact",
            description="Pins a critical fact (fact, category) so the agent never forgets it.",
            input_schema={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "Fact string to pin in permanent working memory.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for the pinned fact (e.g., IDENTITY, MISSION, MEMORY, SECRET, ARSENAL).",
                        "default": "PINNED",
                    },
                },
                "required": ["fact"],
            },
            handler=self._tool_cot_pin_fact,
        )

        # 4. cot_add_step
        self._register_tool(
            name="cot_add_step",
            description="Appends a reasoning node (thought, phase) to the Chain of Thoughts DAG.",
            input_schema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Reasoning step or thought description.",
                    },
                    "phase": {
                        "type": "string",
                        "description": "Reasoning phase (e.g. RECALL, CONTEXT_LINK, DEDUCTION, SYNTHESIS, EXECUTION).",
                        "default": "REASONING",
                    },
                },
                "required": ["thought"],
            },
            handler=self._tool_cot_add_step,
        )

        # 5. cot_compile_prompt
        self._register_tool(
            name="cot_compile_prompt",
            description="Compiles the structured <CHAIN_OF_THOUGHTS_MEMORY> prompt block ready for LLM injection.",
            input_schema={
                "type": "object",
                "properties": {
                    "base_prompt": {
                        "type": "string",
                        "description": "Optional base system prompt to combine with the CoT memory block.",
                        "default": "",
                    },
                },
            },
            handler=self._tool_cot_compile_prompt,
        )

        # 6. cot_search
        self._register_tool(
            name="cot_search",
            description="Keyword search across turns, pinned facts, and thoughts.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or query string.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return per category.",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
            handler=self._tool_cot_search,
        )

    # -------------------------------------------------------------------------
    # Tool Handlers
    # -------------------------------------------------------------------------

    def _tool_cot_status(self, args: Dict[str, Any]) -> str:
        status = self.cot.get_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    def _tool_cot_add_turn(self, args: Dict[str, Any]) -> str:
        role = args.get("role", "user")
        content = args.get("content", "")
        res = self.cot.add_turn(role=role, content=content)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_pin_fact(self, args: Dict[str, Any]) -> str:
        fact = args.get("fact", "")
        category = args.get("category", "PINNED")
        res = self.cot.pin_fact(fact=fact, category=category)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_add_step(self, args: Dict[str, Any]) -> str:
        thought = args.get("thought", "")
        phase = args.get("phase", "REASONING")
        res = self.cot.add_step(thought=thought, phase=phase)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_compile_prompt(self, args: Dict[str, Any]) -> str:
        base_prompt = args.get("base_prompt", "")
        return self.cot.compile_system_prompt(base_prompt=base_prompt)

    def _tool_cot_search(self, args: Dict[str, Any]) -> str:
        query = args.get("query", "")
        limit = int(args.get("limit", 10))
        res = self.cot.search(query=query, limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # JSON-RPC 2.0 Dispatcher
    # -------------------------------------------------------------------------

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an incoming JSON-RPC 2.0 request or notification."""
        if not isinstance(request, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
            }

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        # 1. MCP Initialization Handshake
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "logging": {},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            }

        # 2. Client initialized notification
        if method in ("notifications/initialized", "initialized"):
            _log("Client initialized successfully.")
            return None

        # 3. Ping
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # 4. Tools list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": list(self.tools.values())},
            }

        # 5. Tools call
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}

            if tool_name not in self.handlers:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Tool '{tool_name}' not found.",
                            }
                        ],
                        "isError": True,
                    },
                }

            try:
                handler = self.handlers[tool_name]
                result_text = handler(tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": str(result_text)}],
                        "isError": False,
                    },
                }
            except Exception as e:
                _log(f"Tool execution error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True,
                    },
                }

        # 6. Fallback stubs for standard MCP discovery
        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

        if method == "prompts/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}}

        if method == "logging/setLevel":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # Unknown method
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found",
                },
            }
        return None

    # -------------------------------------------------------------------------
    # Standard I/O Loop
    # -------------------------------------------------------------------------

    def run_stdio(self) -> None:
        """Run the MCP server over standard input and standard output."""
        _log(f"Starting {SERVER_NAME} v{SERVER_VERSION} MCP stdio transport...")
        stdin_stream = sys.stdin

        while True:
            try:
                line = stdin_stream.readline()
                if not line:
                    break

                line_stripped = line.strip()
                if not line_stripped:
                    continue

                if line_stripped.lower().startswith("content-length:"):
                    parts = line_stripped.split(":", 1)
                    length = int(parts[1].strip())
                    while True:
                        blank = stdin_stream.readline()
                        if not blank or blank.strip() == "":
                            break
                    body = stdin_stream.read(length)
                    req_data = json.loads(body)
                else:
                    req_data = json.loads(line_stripped)

                response = self.handle_request(req_data)
                if response is not None:
                    out_str = json.dumps(response, ensure_ascii=False)
                    sys.stdout.write(out_str + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError as jde:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(jde)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                _log("KeyboardInterrupt received, shutting down.")
                break
            except Exception as ex:
                _log(f"Transport loop exception: {ex}")
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": f"Internal error: {str(ex)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

        _log("MCP stdio server terminated.")


def main() -> None:
    """Entrypoint for the MCP Server binary / command."""
    default_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    default_storage = os.environ.get("ZOTH_COT_DATA_FILE", os.path.join(default_data_dir, "cot_memory.json"))
    server = MCPServer(storage_path=default_storage)
    server.run_stdio()


if __name__ == "__main__":
    main()

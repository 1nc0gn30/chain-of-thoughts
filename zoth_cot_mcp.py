#!/usr/bin/env python3
"""
zoth_cot_mcp.py — Chain of Thoughts (zoth-cot) Working Memory DAG & MCP Server
Engineered by 1nc0gn30 (@1nc0gn30) • NullAI Platform

Zero-dependency standard-I/O JSON-RPC 2.0 Model Context Protocol server exposing
the ChainOfThoughts Cryptographic Merkle Working Memory DAG, branching & thought
revision, automatic fact & entity extraction, rolling checkpoint synthesis,
prompt compilation, trace export, and integrity verification.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "zoth-cot-mcp"
SERVER_VERSION = "1.1.0"

GENESIS_SEED = "ZOTH-COT-GENESIS"
VALID_ROLES = {"user", "assistant", "system"}

# Common English words that follow "I am" / "I'm" and are NOT an operator identity
IDENTITY_STOPWORDS = {
    "a", "an", "the", "not", "just", "now", "here", "ready", "done", "back",
    "going", "trying", "working", "scanning", "running", "checking", "testing",
    "auditing", "building", "debugging", "fixing", "looking", "using", "seeing",
    "getting", "having", "making", "doing", "still", "also", "very", "about",
    "in", "on", "at", "to", "for", "with", "from", "unable", "able", "sure",
    "sorry", "happy", "glad", "currently", "already", "almost",
}

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


def _compute_node_hash(
    prev_hash: str,
    thought: str,
    phase: str,
    timestamp: str,
    branch: str = "main",
    version: int = 2,
) -> str:
    """Compute a deterministic 12-hex-char SHA-256 hash for a DAG node."""
    if version >= 2:
        payload = f"v2|{prev_hash}|{branch}|{phase}|{thought}|{timestamp}"
    else:
        payload = f"{prev_hash}|{thought}|{phase}|{timestamp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _parse_node_index(node_id: str) -> int:
    """Extract numeric index from node IDs like 'N00', 'N12', 'N105'."""
    m = re.match(r"^N(\d+)$", str(node_id or "").strip(), re.IGNORECASE)
    return int(m.group(1)) if m else -1


def _normalize_tags(tags: Optional[List[str]]) -> List[str]:
    """Normalize and deduplicate tag strings while preserving order."""
    if not tags:
        return []
    seen: Set[str] = set()
    cleaned: List[str] = []
    for raw in tags:
        tag = str(raw or "").strip().lower()
        if tag and tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    return cleaned


class ChainOfThoughts:
    """
    Cryptographic Merkle Working Memory DAG & Multi-Turn Context Engine.
    Handles semantic fact extraction, entity extraction (IPs, ports, domains, paths, CVEs, tools),
    branching & thought revision, rolling checkpoint compression, trace export,
    cryptographic verification, and LLM prompt compilation.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_turns: int = 24,
        checkpoint_interval: int = 4,
        max_nodes: int = 256,
    ) -> None:
        self.storage_path = storage_path
        self.max_turns = max(1, int(max_turns))
        self.checkpoint_interval = max(1, int(checkpoint_interval))
        self.max_nodes = max(10, int(max_nodes))

        genesis_hash = hashlib.sha256(GENESIS_SEED.encode("utf-8")).hexdigest()[:12]
        self.genesis_hash: str = genesis_hash
        self.head_hash: str = genesis_hash
        self.active_branch: str = "main"
        self.branches: Dict[str, str] = {"main": genesis_hash}
        self.next_node_index: int = 1

        operator_label = os.environ.get(
            "ZOTH_COT_OPERATOR",
            "Operator callsign: 1nc0gn30 (@1nc0gn30) • Sovereign AI Workstation.",
        )

        self.pinned_facts: List[Dict[str, Any]] = [
            {
                "id": "fact-operator",
                "category": "IDENTITY",
                "fact": operator_label,
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
                "branch": "main",
                "thought": "[GENESIS] Initialize Chain of Thoughts Working Memory DAG",
                "prompt": "[GENESIS] Initialize Chain of Thoughts Working Memory DAG",
                "phase": "GENESIS",
                "tags": ["genesis"],
                "confidence": 1.0,
                "steps": {
                    "recall": "Loaded core semantic engrams.",
                    "context_link": f"Initialized {self.max_turns}-turn rolling context window.",
                    "contextLink": f"Initialized {self.max_turns}-turn rolling context window.",
                    "deduction": "Armed multi-turn LLM router (Ollama + Cloud Providers).",
                    "synthesis": "Chain of Thoughts DAG online.",
                },
                "mood": "TACTICAL",
                "tokens": 64,
                "hash_version": 0,
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
            self.max_turns = int(data.get("maxTurns") or data.get("max_turns") or self.max_turns)
            self.active_branch = str(
                data.get("activeBranch") or data.get("active_branch") or "main"
            )

            raw_facts = data.get("pinnedFacts")
            if raw_facts is None:
                raw_facts = data.get("pinned_facts")
            if isinstance(raw_facts, list):
                self.pinned_facts = raw_facts

            raw_msgs = data.get("messages")
            if raw_msgs is None:
                raw_msgs = data.get("turns")
            if isinstance(raw_msgs, list):
                self.messages = raw_msgs

            raw_nodes = data.get("nodes")
            if isinstance(raw_nodes, list) and raw_nodes:
                normalized_nodes: List[Dict[str, Any]] = []
                max_idx = 0
                for n in raw_nodes:
                    node = dict(n)
                    if "parentHash" in node and "parent_hash" not in node:
                        node["parent_hash"] = node["parentHash"]
                    if "parent_hash" in node and "parentHash" not in node:
                        node["parentHash"] = node["parent_hash"]
                    if "prompt" in node and "thought" not in node:
                        node["thought"] = node["prompt"]
                    if "thought" in node and "prompt" not in node:
                        node["prompt"] = node["thought"]
                    if "phase" not in node:
                        node["phase"] = node.get("mood", "REASONING")
                    if "branch" not in node:
                        node["branch"] = "main"
                    if "tags" not in node or not isinstance(node["tags"], list):
                        node["tags"] = []
                    idx = _parse_node_index(node.get("id", ""))
                    if idx >= max_idx:
                        max_idx = idx
                    normalized_nodes.append(node)
                self.nodes = normalized_nodes
                self.next_node_index = max(
                    int(data.get("nextNodeIndex") or data.get("next_node_index") or 0),
                    max_idx + 1,
                    len(self.nodes),
                )

            raw_branches = data.get("branches")
            if isinstance(raw_branches, dict) and raw_branches:
                self.branches = {str(k): str(v) for k, v in raw_branches.items()}
            else:
                rebuilt: Dict[str, str] = {}
                for n in self.nodes:
                    rebuilt[str(n.get("branch") or "main")] = str(n.get("hash") or self.head_hash)
                self.branches = rebuilt or {"main": self.head_hash}

            if self.active_branch not in self.branches:
                self.branches[self.active_branch] = self.head_hash

            raw_entities = data.get("entities")
            if isinstance(raw_entities, dict):
                # Support both {ips: [...]} and UI dictionary {"ipv4:1.2.3.4": {type, value}}
                for k, v in raw_entities.items():
                    if k in self.entities and isinstance(v, list):
                        self.entities[k] = set(str(x) for x in v)
                    elif isinstance(v, dict) and "type" in v and "value" in v:
                        t = str(v["type"]).lower()
                        val = str(v["value"])
                        type_map = {
                            "ipv4": "ips",
                            "ip": "ips",
                            "port": "ports",
                            "domain": "domains",
                            "path": "paths",
                            "cve": "cves",
                            "tools": "tools",
                            "tool": "tools",
                        }
                        bucket = type_map.get(t)
                        if bucket:
                            self.entities[bucket].add(val)

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
                "activeBranch": self.active_branch,
                "active_branch": self.active_branch,
                "branches": self.branches,
                "nextNodeIndex": self.next_node_index,
                "next_node_index": self.next_node_index,
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
        Extract structured technical entities from text:
        - IPs: Valid IPv4 addresses
        - Ports: Port numbers (1-65535) associated with network traffic or explicit mentions
        - Domains: FQDN hostnames
        - Paths: Absolute or relative POSIX file paths (excluding URL paths)
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
        # Strip URL schemes (http://..., https://..., ws://...) before scanning local paths
        text_no_urls = re.sub(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s\"'<>]+", " ", p)
        path_pattern = re.compile(
            r"(?:(?<![a-zA-Z0-9_./])/(?:[a-zA-Z0-9_\-.]+/)+[a-zA-Z0-9_\-.]+|(?:\./|\.\./)[a-zA-Z0-9_\-./]+)"
        )
        for match in path_pattern.finditer(text_no_urls):
            candidate = match.group(0).rstrip(".,:;!?)\"'>")
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
    # Fact Auto-Extraction & Management
    # -------------------------------------------------------------------------

    def auto_extract_facts(self, prompt_text: str) -> List[Dict[str, Any]]:
        """
        Auto-extract permanent facts from prompt text:
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
                "stopword_filter": True,
            },
            {
                "re": re.compile(
                    r"\b(?:remember(?: that)?|don't forget(?: that)?|note that|keep in mind(?: that)?)\s+(.{4,140})",
                    re.IGNORECASE,
                ),
                "cat": "MEMORY",
                "prefix": "Explicit operator memory: ",
                "stopword_filter": False,
            },
            {
                "re": re.compile(
                    r"\b(?:target(?: ip| host| domain)? is|auditing|scanning|working on|project is|topic is)\s+([A-Za-z0-9_.:/-]{3,80})",
                    re.IGNORECASE,
                ),
                "cat": "MISSION",
                "prefix": "Active focus / target: ",
                "stopword_filter": False,
            },
            {
                "re": re.compile(
                    r"\b(?:secret word is|passphrase is|key is|pin is)\s+([A-Za-z0-9_!@#$%^&*-]{2,50})",
                    re.IGNORECASE,
                ),
                "cat": "SECRET",
                "prefix": "Pinned session token: ",
                "stopword_filter": False,
            },
        ]

        for pat in patterns:
            m = pat["re"].search(p)
            if m and m.group(1):
                clean_val = re.sub(r"[.!?]+$", "", m.group(1)).strip()
                if not clean_val:
                    continue
                if pat["stopword_filter"] and clean_val.lower() in IDENTITY_STOPWORDS:
                    continue
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

    def unpin_fact(self, fact_id: str, delete: bool = False) -> Dict[str, Any]:
        """Deactivate (or permanently delete) a pinned fact by ID."""
        target_id = str(fact_id or "").strip()
        if not target_id:
            raise ValueError("fact_id cannot be empty")

        for idx, fact in enumerate(self.pinned_facts):
            if fact.get("id") == target_id:
                if delete:
                    removed = self.pinned_facts.pop(idx)
                    self.save_state()
                    return {"ok": True, "action": "deleted", "fact": removed}
                fact["active"] = False
                self.save_state()
                return {"ok": True, "action": "deactivated", "fact": fact}

        raise ValueError(f"Pinned fact '{target_id}' not found")

    # -------------------------------------------------------------------------
    # DAG Operations: Steps, Branching, Revision & Verification
    # -------------------------------------------------------------------------

    def _find_node(self, ref: str) -> Optional[Dict[str, Any]]:
        """Find a node by exact ID (e.g., 'N01'), exact hash, or hash prefix."""
        needle = str(ref or "").strip()
        if not needle:
            return None
        needle_lower = needle.lower()
        for n in self.nodes:
            if str(n.get("id", "")).lower() == needle_lower:
                return n
            if str(n.get("hash", "")).lower() == needle_lower:
                return n
        # Fallback to unique hash prefix match
        matches = [n for n in self.nodes if str(n.get("hash", "")).lower().startswith(needle_lower)]
        if len(matches) == 1:
            return matches[0]
        return None

    def add_step(
        self,
        thought: str,
        phase: str = "REASONING",
        metadata: Optional[Dict[str, Any]] = None,
        parent_hash: Optional[str] = None,
        branch: Optional[str] = None,
        tags: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        revises: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Append a reasoning node to the Chain of Thoughts Cryptographic Merkle DAG.
        Supports branching from any ancestor node (`parent_hash` or node ID),
        named branches, normalized tags, confidence scores (0.0-1.0), and thought revision.
        """
        thought_str = str(thought or "").strip()
        phase_str = str(phase or "REASONING").strip().upper()
        if not thought_str:
            raise ValueError("Thought description cannot be empty")

        if confidence is not None:
            conf_val = float(confidence)
            if conf_val < 0.0 or conf_val > 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")
        else:
            conf_val = None

        target_branch = str(branch or self.active_branch or "main").strip() or "main"

        # Resolve parent hash
        if parent_hash:
            parent_node = self._find_node(parent_hash)
            if parent_node is None:
                raise ValueError(f"Parent node '{parent_hash}' not found in DAG")
            prev_hash = str(parent_node["hash"])
        elif target_branch in self.branches:
            prev_hash = self.branches[target_branch]
        else:
            prev_hash = self.head_hash or "000000000000"

        # Resolve thought revision target if supplied
        revised_target: Optional[Dict[str, Any]] = None
        if revises:
            revised_target = self._find_node(revises)
            if revised_target is None:
                raise ValueError(f"Revised node '{revises}' not found in DAG")

        node_idx = self.next_node_index
        self.next_node_index += 1
        node_id = f"N{node_idx:02d}"
        now_ts = _iso_now()

        node_hash = _compute_node_hash(
            prev_hash=prev_hash,
            thought=thought_str,
            phase=phase_str,
            timestamp=now_ts,
            branch=target_branch,
            version=2,
        )
        self.head_hash = node_hash
        self.active_branch = target_branch
        self.branches[target_branch] = node_hash

        meta = metadata or {}
        cleaned_tags = _normalize_tags(tags or meta.get("tags"))

        new_node: Dict[str, Any] = {
            "id": node_id,
            "hash": node_hash,
            "parent_hash": prev_hash,
            "parentHash": prev_hash,
            "branch": target_branch,
            "thought": thought_str,
            "prompt": thought_str,
            "phase": phase_str,
            "mood": meta.get("mood", "TACTICAL"),
            "tags": cleaned_tags,
            "confidence": conf_val,
            "revises": revised_target["id"] if revised_target else None,
            "steps": meta.get(
                "steps",
                {
                    "recall": f"Linked to prior head {prev_hash} on branch '{target_branch}'.",
                    "context_link": f"Phase {phase_str} step.",
                    "contextLink": f"Phase {phase_str} step.",
                    "deduction": thought_str[:60],
                    "synthesis": thought_str,
                },
            ),
            "tokens": max(32, round(len(thought_str) / 3.8)),
            "hash_version": 2,
            "timestamp": now_ts,
        }

        if revised_target is not None:
            revised_target["superseded_by"] = node_id

        self.nodes.append(new_node)
        if len(self.nodes) > self.max_nodes:
            # Always preserve genesis node at index 0 alongside most recent nodes
            self.nodes = [self.nodes[0]] + self.nodes[-(self.max_nodes - 1) :]

        self.save_state()
        return new_node

    def list_branches(self) -> Dict[str, Any]:
        """List all DAG branches, their head hashes, node counts, and active branch."""
        counts: Dict[str, int] = {}
        for n in self.nodes:
            b = str(n.get("branch") or "main")
            counts[b] = counts.get(b, 0) + 1

        branch_entries = []
        for name, head in sorted(self.branches.items()):
            head_node = self._find_node(head)
            branch_entries.append({
                "name": name,
                "head_hash": head,
                "head_id": head_node.get("id") if head_node else None,
                "node_count": counts.get(name, 0),
                "active": name == self.active_branch,
            })

        return {
            "active_branch": self.active_branch,
            "head_hash": self.head_hash,
            "branches": branch_entries,
        }

    def checkout_branch(self, branch: str, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Switch active branch to an existing branch, or create a new branch
        pointing at `target` (node ID or hash; defaults to current head).
        """
        name = str(branch or "").strip()
        if not name:
            raise ValueError("Branch name cannot be empty")

        if name in self.branches and not target:
            self.active_branch = name
            self.head_hash = self.branches[name]
            self.save_state()
            return {
                "ok": True,
                "created": False,
                "active_branch": self.active_branch,
                "head_hash": self.head_hash,
            }

        if target:
            anchor = self._find_node(target)
            if anchor is None:
                raise ValueError(f"Target node '{target}' not found in DAG")
            anchor_hash = str(anchor["hash"])
        else:
            anchor_hash = self.head_hash

        created = name not in self.branches
        self.branches[name] = anchor_hash
        self.active_branch = name
        self.head_hash = anchor_hash
        self.save_state()
        return {
            "ok": True,
            "created": created,
            "active_branch": self.active_branch,
            "head_hash": self.head_hash,
        }

    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify cryptographic hash integrity and parent-pointer linkage across the Merkle DAG.
        Checks:
        - Genesis node exists and links to '000000000000'
        - Every non-genesis node's parent_hash references an existing node in the DAG
        - Nodes with hash_version >= 2 match recomputed SHA-256 hash
        - Active head_hash and branch pointers reference known nodes
        """
        issues: List[str] = []
        hash_index: Dict[str, Dict[str, Any]] = {}

        for n in self.nodes:
            h = str(n.get("hash") or "")
            if not h:
                issues.append(f"Node {n.get('id')} is missing a hash")
                continue
            if h in hash_index:
                issues.append(f"Duplicate node hash detected: {h}")
            hash_index[h] = n

        if not self.nodes:
            issues.append("DAG contains zero nodes")
        else:
            genesis = self.nodes[0]
            genesis_parent = genesis.get("parent_hash") or genesis.get("parentHash")
            if genesis_parent != "000000000000":
                issues.append(
                    f"Genesis node {genesis.get('id')} has unexpected parent {genesis_parent}"
                )

            for n in self.nodes[1:]:
                nid = n.get("id", "N??")
                parent = n.get("parent_hash") or n.get("parentHash")
                if not parent or parent not in hash_index:
                    issues.append(
                        f"Broken parent link on {nid} ({n.get('hash')}): parent {parent} not found"
                    )

                hv = n.get("hash_version")
                if hv == 2:
                    expected = _compute_node_hash(
                        prev_hash=str(parent or ""),
                        thought=str(n.get("thought") or n.get("prompt") or ""),
                        phase=str(n.get("phase") or "REASONING"),
                        timestamp=str(n.get("timestamp") or ""),
                        branch=str(n.get("branch") or "main"),
                        version=2,
                    )
                    if expected != n.get("hash"):
                        issues.append(
                            f"Hash tampering detected on {nid}: expected {expected}, got {n.get('hash')}"
                        )

        if self.head_hash not in hash_index:
            issues.append(f"Active head_hash '{self.head_hash}' does not exist in DAG")

        for bname, bhash in self.branches.items():
            if bhash not in hash_index:
                issues.append(f"Branch '{bname}' head '{bhash}' does not exist in DAG")

        return {
            "valid": len(issues) == 0,
            "checked_nodes": len(self.nodes),
            "branch_count": len(self.branches),
            "head_hash": self.head_hash,
            "issues": issues,
        }

    # -------------------------------------------------------------------------
    # Turns & Rolling Checkpoints
    # -------------------------------------------------------------------------

    def add_turn(self, role: str, content: str) -> Dict[str, Any]:
        """
        Record a conversation turn with automatic entity & fact extraction
        and rolling checkpoint synthesis.
        """
        r = str(role or "user").strip().lower()
        c = str(content or "").strip()
        if r not in VALID_ROLES:
            raise ValueError(f"Invalid role '{r}'. Must be one of: {', '.join(sorted(VALID_ROLES))}")
        if not c:
            raise ValueError("Turn content cannot be empty")

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
            "branch": self.active_branch,
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
            "branch": self.active_branch,
        }

    def clear_turns(self) -> Dict[str, Any]:
        """Clear rolling conversation messages while preserving pinned facts and DAG nodes."""
        cleared_count = len(self.messages)
        self.messages = []
        self.save_state()
        return {
            "ok": True,
            "cleared_messages": cleared_count,
            "preserved_facts": len(self.pinned_facts),
            "preserved_nodes": len(self.nodes),
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
    # Prompt Compilation & Export
    # -------------------------------------------------------------------------

    def compile_system_prompt(
        self, base_prompt: str = "", branch: Optional[str] = None
    ) -> str:
        """
        Compile the structured <CHAIN_OF_THOUGHTS_MEMORY> prompt block ready for LLM injection.
        Includes head hash, active branch, pinned facts, extracted entities, checkpoint summary,
        and recent reasoning DAG nodes.
        """
        target_branch = branch or self.active_branch
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

        if branch:
            scoped_nodes = [n for n in self.nodes if n.get("branch", "main") == branch]
            recent_nodes = (scoped_nodes or self.nodes)[-5:]
        else:
            recent_nodes = self.nodes[-5:]

        node_lines = []
        for n in recent_nodes:
            conf = n.get("confidence")
            conf_str = f" conf={conf:.2f}" if isinstance(conf, (int, float)) else ""
            node_branch = n.get("branch", "main")
            node_lines.append(
                f"- [{n.get('id', 'N??')} // {n.get('hash', '000000')}] "
                f"({n.get('phase', 'REASONING')}@{node_branch}{conf_str}): {n.get('thought', '')[:70]}"
            )
        dag_block = "\n".join(node_lines)

        branch_head = self.branches.get(target_branch, self.head_hash)
        memory_block = (
            f"<CHAIN_OF_THOUGHTS_MEMORY>\n"
            f"HEAD_HASH: {branch_head} | BRANCH: {target_branch}\n"
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

    def export_trace(self, fmt: str = "markdown") -> str:
        """Export the complete working memory DAG trace as Markdown or JSON."""
        norm_fmt = str(fmt or "markdown").strip().lower()
        if norm_fmt == "json":
            payload = {
                "head_hash": self.head_hash,
                "active_branch": self.active_branch,
                "branches": self.branches,
                "verification": self.verify_chain(),
                "stats": self.get_stats(),
                "pinned_facts": self.pinned_facts,
                "entities": {k: sorted(list(v)) for k, v in self.entities.items()},
                "nodes": self.nodes,
                "checkpoints": self.checkpoints,
                "messages": self.messages,
                "exported_at": _iso_now(),
            }
            return json.dumps(payload, indent=2, ensure_ascii=False)

        if norm_fmt not in ("markdown", "md"):
            raise ValueError(f"Unsupported export format '{fmt}'. Use 'markdown' or 'json'.")

        verify = self.verify_chain()
        lines: List[str] = [
            f"# Chain of Thoughts Trace (`{self.head_hash}`)",
            "",
            f"- **Active Branch**: `{self.active_branch}`",
            f"- **Nodes**: {len(self.nodes)} | **Branches**: {len(self.branches)} | **Turns**: {len(self.messages) // 2}",
            f"- **Merkle Integrity**: {'VALID' if verify['valid'] else 'INVALID (' + str(len(verify['issues'])) + ' issues)'}",
            "",
            "## Pinned Facts",
        ]
        if self.pinned_facts:
            for f in self.pinned_facts:
                state_marker = "active" if f.get("active", True) else "inactive"
                lines.append(
                    f"- `[{f.get('category', 'PINNED')}]` ({state_marker}, `{f.get('id')}`): {f.get('fact')}"
                )
        else:
            lines.append("- None")

        lines.extend(["", "## Extracted Entities"])
        any_ent = False
        for cat in ["ips", "ports", "domains", "paths", "cves", "tools"]:
            vals = sorted(list(self.entities.get(cat, set())))
            if vals:
                any_ent = True
                lines.append(f"- **{cat.upper()}**: {', '.join(f'`{v}`' for v in vals)}")
        if not any_ent:
            lines.append("- None")

        lines.extend(["", "## Reasoning DAG"])
        for n in self.nodes:
            parent = n.get("parent_hash") or n.get("parentHash") or "000000000000"
            branch = n.get("branch", "main")
            phase = n.get("phase", "REASONING")
            tags = n.get("tags") or []
            conf = n.get("confidence")
            revises = n.get("revises")
            superseded = n.get("superseded_by")

            meta_bits = [f"branch=`{branch}`", f"phase=`{phase}`", f"parent=`{parent}`"]
            if isinstance(conf, (int, float)):
                meta_bits.append(f"confidence={conf:.2f}")
            if tags:
                meta_bits.append("tags=" + ",".join(f"`{t}`" for t in tags))
            if revises:
                meta_bits.append(f"revises=`{revises}`")
            if superseded:
                meta_bits.append(f"superseded_by=`{superseded}`")

            lines.append(
                f"- **{n.get('id')}** (`{n.get('hash')}`) [{', '.join(meta_bits)}]: {n.get('thought') or n.get('prompt', '')}"
            )

        if self.checkpoints:
            lines.extend(["", "## Rolling Checkpoints"])
            for c in self.checkpoints:
                lines.append(f"- `{c.get('id')}` (turn {c.get('turn_index')}): {c.get('summary')}")

        if self.messages:
            lines.extend(["", "## Conversation Turns"])
            for m in self.messages:
                lines.append(
                    f"- **{m.get('role', 'user').upper()}** (`{m.get('id')}`): {m.get('content', '')}"
                )

        return "\n".join(lines) + "\n"

    # -------------------------------------------------------------------------
    # Search, Stats & Status
    # -------------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        limit: int = 10,
        phase: Optional[str] = None,
        branch: Optional[str] = None,
        tag: Optional[str] = None,
        min_confidence: Optional[float] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search and filter across pinned facts, conversation turns, DAG thoughts, and entities.
        Supports keyword queries as well as structured filters (phase, branch, tag,
        min_confidence, category).
        """
        q = str(query or "").strip().lower()
        phase_f = str(phase).strip().upper() if phase else None
        branch_f = str(branch).strip() if branch else None
        tag_f = str(tag).strip().lower() if tag else None
        cat_f = str(category).strip().upper() if category else None
        min_conf = float(min_confidence) if min_confidence is not None else None
        lim = max(1, int(limit))

        has_filters = any(x is not None for x in (phase_f, branch_f, tag_f, min_conf, cat_f))
        if not q and not has_filters:
            return {
                "query": "",
                "filters": {},
                "matched_facts": [],
                "matched_turns": [],
                "matched_thoughts": [],
                "matched_entities": [],
                "total_matches": 0,
            }

        terms = [t for t in q.split() if len(t) >= 2]

        def text_matches(text: str) -> bool:
            if not q:
                return True
            lower_text = text.lower()
            return q in lower_text or any(t in lower_text for t in terms)

        # Facts
        matched_facts: List[Dict[str, Any]] = []
        if not any(x is not None for x in (phase_f, branch_f, tag_f, min_conf)):
            for f in self.pinned_facts:
                if cat_f and str(f.get("category", "")).upper() != cat_f:
                    continue
                if text_matches(f.get("fact", "") + " " + f.get("category", "")):
                    matched_facts.append(f)
                    if len(matched_facts) >= lim:
                        break

        # Turns
        matched_turns: List[Dict[str, Any]] = []
        if not any(x is not None for x in (phase_f, tag_f, min_conf, cat_f)):
            for m in self.messages:
                if branch_f and str(m.get("branch", "main")) != branch_f:
                    continue
                if text_matches(m.get("content", "") + " " + m.get("role", "")):
                    matched_turns.append(m)
                    if len(matched_turns) >= lim:
                        break

        # Thoughts (DAG nodes)
        matched_thoughts: List[Dict[str, Any]] = []
        if not cat_f:
            for n in self.nodes:
                if phase_f and str(n.get("phase", "")).upper() != phase_f:
                    continue
                if branch_f and str(n.get("branch", "main")) != branch_f:
                    continue
                node_tags = [str(t).lower() for t in (n.get("tags") or [])]
                if tag_f and tag_f not in node_tags:
                    continue
                if min_conf is not None:
                    cval = n.get("confidence")
                    if not isinstance(cval, (int, float)) or cval < min_conf:
                        continue
                haystack = " ".join([
                    str(n.get("thought") or n.get("prompt") or ""),
                    str(n.get("phase", "")),
                    str(n.get("branch", "")),
                    " ".join(node_tags),
                ])
                if text_matches(haystack):
                    matched_thoughts.append(n)
                    if len(matched_thoughts) >= lim:
                        break

        # Entities
        matched_entities: List[Dict[str, str]] = []
        if q and not any(x is not None for x in (phase_f, branch_f, tag_f, min_conf, cat_f)):
            for etype, vals in self.entities.items():
                for val in sorted(list(vals)):
                    if text_matches(f"{etype} {val}"):
                        matched_entities.append({"type": etype, "value": val})
                        if len(matched_entities) >= lim:
                            break
                if len(matched_entities) >= lim:
                    break

        total = (
            len(matched_facts)
            + len(matched_turns)
            + len(matched_thoughts)
            + len(matched_entities)
        )
        filters = {
            k: v
            for k, v in {
                "phase": phase_f,
                "branch": branch_f,
                "tag": tag_f,
                "min_confidence": min_conf,
                "category": cat_f,
            }.items()
            if v is not None
        }
        return {
            "query": query,
            "filters": filters,
            "matched_facts": matched_facts,
            "matched_turns": matched_turns,
            "matched_thoughts": matched_thoughts,
            "matched_entities": matched_entities,
            "total_matches": total,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate reasoning metrics across phases, branches, tags, confidence, and entities."""
        phases: Dict[str, int] = {}
        branches: Dict[str, int] = {}
        tags: Dict[str, int] = {}
        confidences: List[float] = []
        revised_count = 0

        for n in self.nodes:
            ph = str(n.get("phase") or "REASONING").upper()
            phases[ph] = phases.get(ph, 0) + 1

            br = str(n.get("branch") or "main")
            branches[br] = branches.get(br, 0) + 1

            for t in n.get("tags") or []:
                tags[t] = tags.get(t, 0) + 1

            c = n.get("confidence")
            if isinstance(c, (int, float)):
                confidences.append(float(c))

            if n.get("revises"):
                revised_count += 1

        active_facts = [f for f in self.pinned_facts if f.get("active", True)]
        total_chars = (
            sum(len(f.get("fact", "")) for f in active_facts)
            + sum(len(m.get("content", "")) for m in self.messages)
            + sum(len(n.get("thought") or n.get("prompt") or "") for n in self.nodes)
        )
        verify = self.verify_chain()

        return {
            "head_hash": self.head_hash,
            "active_branch": self.active_branch,
            "node_count": len(self.nodes),
            "branch_count": len(self.branches),
            "revised_node_count": revised_count,
            "message_count": len(self.messages),
            "turn_count": len(self.messages) // 2,
            "checkpoint_count": len(self.checkpoints),
            "facts": {
                "total": len(self.pinned_facts),
                "active": len(active_facts),
                "inactive": len(self.pinned_facts) - len(active_facts),
            },
            "entities": {k: len(v) for k, v in self.entities.items()},
            "entities_total": sum(len(v) for v in self.entities.values()),
            "phases": phases,
            "branches": branches,
            "tags": tags,
            "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
            "est_tokens": max(48, round(total_chars / 3.8)),
            "merkle_valid": verify["valid"],
        }

    def get_status(self) -> Dict[str, Any]:
        """Return session status, pinned facts, branches, entities, and recent turns."""
        active_facts = [f for f in self.pinned_facts if f.get("active", True)]
        total_chars = sum(len(f.get("fact", "")) for f in active_facts) + sum(
            len(m.get("content", "")) for m in self.messages
        )
        est_tokens = max(48, round(total_chars / 3.8))

        return {
            "ok": True,
            "head_hash": self.head_hash,
            "active_branch": self.active_branch,
            "branches": self.branches,
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
    Exposes ChainOfThoughts tools to Claude Desktop, Claude Code, Cursor,
    Antigravity / Gemini CLI, Hermes, and Windsurf.
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
            description="Returns session status, active branch, head hash, pinned facts, entities, and recent turns.",
            input_schema={"type": "object", "properties": {}},
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
                        "description": "Category for the pinned fact (e.g., IDENTITY, MISSION, MEMORY, SECRET, SECURITY).",
                        "default": "PINNED",
                    },
                },
                "required": ["fact"],
            },
            handler=self._tool_cot_pin_fact,
        )

        # 4. cot_unpin_fact
        self._register_tool(
            name="cot_unpin_fact",
            description="Deactivates or permanently deletes a pinned fact by ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "fact_id": {
                        "type": "string",
                        "description": "ID of the pinned fact to deactivate or remove.",
                    },
                    "delete": {
                        "type": "boolean",
                        "description": "If true, permanently delete the fact instead of marking it inactive.",
                        "default": False,
                    },
                },
                "required": ["fact_id"],
            },
            handler=self._tool_cot_unpin_fact,
        )

        # 5. cot_add_step
        self._register_tool(
            name="cot_add_step",
            description="Appends a reasoning node to the Merkle DAG. Supports branching (parent_hash, branch), tags, confidence (0.0-1.0), and thought revision (revises).",
            input_schema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Reasoning step or thought description.",
                    },
                    "phase": {
                        "type": "string",
                        "description": "Reasoning phase (e.g., RECALL, CONTEXT_LINK, DEDUCTION, SYNTHESIS, VERIFICATION, EXECUTION).",
                        "default": "REASONING",
                    },
                    "parent_hash": {
                        "type": "string",
                        "description": "Optional ancestor node ID (e.g. 'N01') or hash to branch from.",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Optional branch name (defaults to current active branch).",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of tags for filtering thoughts.",
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Optional confidence score between 0.0 and 1.0.",
                    },
                    "revises": {
                        "type": "string",
                        "description": "Optional prior node ID or hash that this reasoning step revises/supersedes.",
                    },
                },
                "required": ["thought"],
            },
            handler=self._tool_cot_add_step,
        )

        # 6. cot_branches
        self._register_tool(
            name="cot_branches",
            description="Lists all DAG branches or switches/creates a branch via checkout.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "checkout"],
                        "default": "list",
                        "description": "Use 'list' to view branches or 'checkout' to switch/create a branch.",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (required when action='checkout').",
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional ancestor node ID or hash when creating a new branch.",
                    },
                },
            },
            handler=self._tool_cot_branches,
        )

        # 7. cot_compile_prompt
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
                    "branch": {
                        "type": "string",
                        "description": "Optional branch name to scope the recent reasoning chain.",
                    },
                },
            },
            handler=self._tool_cot_compile_prompt,
        )

        # 8. cot_search
        self._register_tool(
            name="cot_search",
            description="Search and filter across turns, pinned facts, thoughts, and entities by keyword, phase, branch, tag, confidence, or category.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or query string (optional when filters are provided).",
                        "default": "",
                    },
                    "phase": {
                        "type": "string",
                        "description": "Filter thoughts by reasoning phase (e.g., DEDUCTION).",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Filter thoughts and turns by branch name.",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Filter thoughts by tag.",
                    },
                    "min_confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Filter thoughts with confidence >= min_confidence.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter pinned facts by category.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return per category.",
                        "default": 10,
                    },
                },
            },
            handler=self._tool_cot_search,
        )

        # 9. cot_verify
        self._register_tool(
            name="cot_verify",
            description="Verifies SHA-256 cryptographic hashes and parent-pointer linkage across the Merkle DAG.",
            input_schema={"type": "object", "properties": {}},
            handler=self._tool_cot_verify,
        )

        # 10. cot_stats
        self._register_tool(
            name="cot_stats",
            description="Returns summary statistics: node counts per phase/branch, tag counts, average confidence, entity totals, token estimate, and integrity status.",
            input_schema={"type": "object", "properties": {}},
            handler=self._tool_cot_stats,
        )

        # 11. cot_export
        self._register_tool(
            name="cot_export",
            description="Exports the full reasoning trace, pinned facts, entities, checkpoints, and turns to Markdown or JSON.",
            input_schema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "Export format: 'markdown' or 'json'.",
                    },
                },
            },
            handler=self._tool_cot_export,
        )

        # 12. cot_clear_turns
        self._register_tool(
            name="cot_clear_turns",
            description="Clears the rolling conversation turn buffer while preserving pinned facts and Merkle DAG nodes.",
            input_schema={"type": "object", "properties": {}},
            handler=self._tool_cot_clear_turns,
        )

    # -------------------------------------------------------------------------
    # Tool Handlers
    # -------------------------------------------------------------------------

    def _tool_cot_status(self, args: Dict[str, Any]) -> str:
        return json.dumps(self.cot.get_status(), indent=2, ensure_ascii=False)

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

    def _tool_cot_unpin_fact(self, args: Dict[str, Any]) -> str:
        fact_id = args.get("fact_id", "")
        delete = bool(args.get("delete", False))
        res = self.cot.unpin_fact(fact_id=fact_id, delete=delete)
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_add_step(self, args: Dict[str, Any]) -> str:
        res = self.cot.add_step(
            thought=args.get("thought", ""),
            phase=args.get("phase", "REASONING"),
            parent_hash=args.get("parent_hash"),
            branch=args.get("branch"),
            tags=args.get("tags"),
            confidence=args.get("confidence"),
            revises=args.get("revises"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_branches(self, args: Dict[str, Any]) -> str:
        action = str(args.get("action") or "list").strip().lower()
        if action == "checkout":
            res = self.cot.checkout_branch(
                branch=args.get("branch", ""),
                target=args.get("target"),
            )
            return json.dumps(res, indent=2, ensure_ascii=False)
        if action == "list":
            return json.dumps(self.cot.list_branches(), indent=2, ensure_ascii=False)
        raise ValueError(f"Unsupported branch action '{action}'. Use 'list' or 'checkout'.")

    def _tool_cot_compile_prompt(self, args: Dict[str, Any]) -> str:
        base_prompt = args.get("base_prompt", "")
        branch = args.get("branch")
        return self.cot.compile_system_prompt(base_prompt=base_prompt, branch=branch)

    def _tool_cot_search(self, args: Dict[str, Any]) -> str:
        res = self.cot.search(
            query=args.get("query", ""),
            limit=int(args.get("limit", 10)),
            phase=args.get("phase"),
            branch=args.get("branch"),
            tag=args.get("tag"),
            min_confidence=args.get("min_confidence"),
            category=args.get("category"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)

    def _tool_cot_verify(self, args: Dict[str, Any]) -> str:
        return json.dumps(self.cot.verify_chain(), indent=2, ensure_ascii=False)

    def _tool_cot_stats(self, args: Dict[str, Any]) -> str:
        return json.dumps(self.cot.get_stats(), indent=2, ensure_ascii=False)

    def _tool_cot_export(self, args: Dict[str, Any]) -> str:
        fmt = args.get("format", "markdown")
        return self.cot.export_trace(fmt=fmt)

    def _tool_cot_clear_turns(self, args: Dict[str, Any]) -> str:
        return json.dumps(self.cot.clear_turns(), indent=2, ensure_ascii=False)

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

        has_id = "id" in request
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params")

        if params is None:
            params = {}
        elif not isinstance(params, dict):
            if not has_id:
                return None
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: expected JSON object"},
            }

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

        # 2. Notifications (no response per JSON-RPC 2.0)
        if method in ("notifications/initialized", "initialized", "notifications/cancelled") or (
            isinstance(method, str) and method.startswith("notifications/") and not has_id
        ):
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
            if not isinstance(tool_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": "Error: tool arguments must be a JSON object."}],
                        "isError": True,
                    },
                }

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
        if has_id and req_id is not None:
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
    # Standard I/O Loop (Supports both NDJSON and UTF-8 byte-accurate Content-Length)
    # -------------------------------------------------------------------------

    def _read_message(self, stdin_buf: Any) -> Tuple[Optional[Any], bool]:
        """
        Read one JSON-RPC message from binary stdin buffer.
        Returns (parsed_payload, used_content_length). Returns (None, False) on EOF.
        """
        while True:
            raw_line = stdin_buf.readline()
            if not raw_line:
                return None, False

            stripped = raw_line.strip()
            if not stripped:
                continue

            lower = stripped.lower()
            if lower.startswith(b"content-length:"):
                length = int(stripped.split(b":", 1)[1].strip())
                # Consume remaining headers until empty line
                while True:
                    hdr = stdin_buf.readline()
                    if not hdr or hdr.strip() == b"":
                        break
                body_bytes = stdin_buf.read(length)
                if not body_bytes:
                    return None, True
                return json.loads(body_bytes.decode("utf-8")), True

            return json.loads(stripped.decode("utf-8")), False

    def _write_message(self, stdout_buf: Any, payload: Dict[str, Any], use_content_length: bool) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if use_content_length:
            header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
            stdout_buf.write(header + encoded)
        else:
            stdout_buf.write(encoded + b"\n")
        stdout_buf.flush()

    def run_stdio(self) -> None:
        """Run the MCP server over standard input and standard output."""
        _log(f"Starting {SERVER_NAME} v{SERVER_VERSION} MCP stdio transport...")
        stdin_buf = sys.stdin.buffer
        stdout_buf = sys.stdout.buffer

        while True:
            used_cl = False
            try:
                req_data, used_cl = self._read_message(stdin_buf)
                if req_data is None:
                    break

                response = self.handle_request(req_data)
                if response is not None:
                    self._write_message(stdout_buf, response, used_cl)

            except json.JSONDecodeError as jde:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(jde)}"},
                }
                self._write_message(stdout_buf, err_resp, used_cl)
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
                self._write_message(stdout_buf, err_resp, used_cl)

        _log("MCP stdio server terminated.")


def main() -> None:
    """Entrypoint for the MCP Server binary / command."""
    default_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    default_storage = os.environ.get("ZOTH_COT_DATA_FILE", os.path.join(default_data_dir, "cot_memory.json"))
    server = MCPServer(storage_path=default_storage)
    server.run_stdio()


if __name__ == "__main__":
    main()

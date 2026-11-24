#!/usr/bin/env python3
"""
test_zoth_cot.py — Comprehensive Unit & Integration Test Suite for Chain of Thoughts (zoth-cot)
Engineered by 1nc0gn30 (@1nc0gn30) • NullAI Platform

Covers:
- Entity extraction (IPs, ports, domains, paths, URL exclusion, CVEs, tools)
- Fact auto-extraction (IDENTITY + stopword guard, MEMORY, MISSION, SECRET, dedup, unpin/delete)
- DAG branching, checkout, thought revision (revises / superseded_by), confidence, tags, node ID monotonicity
- Cryptographic Merkle DAG verification (valid linear, valid branched, tamper detection, broken parent)
- Filtered search, aggregate stats, Markdown & JSON trace export, clear turns
- Rolling checkpoint compression & prompt compilation
- MCP JSON-RPC 2.0 unit tests (all 12 tools + error handling + notifications)
- Real subprocess stdio MCP round-trips (both NDJSON and UTF-8 Content-Length framing)
- Real Node CLI integration tests (`bin/zoth-cot` across all flags & subcommands)
- Real HTTP REST API integration tests (`server.js` on ephemeral port)
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

# Add project root to sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from zoth_cot_mcp import (
    ChainOfThoughts,
    MCPServer,
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class TestEntityExtraction(unittest.TestCase):
    """Verify entity extraction across IPs, ports, domains, paths, CVEs, and tools."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None)

    def test_ip_extraction(self) -> None:
        text = "Scanning targets 192.168.1.1, 10.0.2.15, and 127.0.0.1 for open services."
        entities = self.cot.extract_entities(text)
        self.assertIn("192.168.1.1", entities["ips"])
        self.assertIn("10.0.2.15", entities["ips"])
        self.assertIn("127.0.0.1", entities["ips"])
        self.assertIn("10.0.2.15", self.cot.entities["ips"])

    def test_invalid_ips_filtered(self) -> None:
        text = "Ignoring invalid IP 999.123.456.789 and partial 1.2.3."
        entities = self.cot.extract_entities(text)
        self.assertEqual(entities["ips"], [])

    def test_port_extraction(self) -> None:
        text = "Service listening on :8080 and port 22, also checking tcp/443 and udp/53."
        entities = self.cot.extract_entities(text)
        self.assertIn("22", entities["ports"])
        self.assertIn("53", entities["ports"])
        self.assertIn("443", entities["ports"])
        self.assertIn("8080", entities["ports"])

    def test_port_boundary_filtering(self) -> None:
        text = "Checking :70000 and port 0 which are invalid ports."
        entities = self.cot.extract_entities(text)
        self.assertNotIn("70000", entities["ports"])
        self.assertNotIn("0", entities["ports"])

    def test_domain_extraction(self) -> None:
        text = "Connecting to api.anthropic.com, nullai.tech, and zoth.nullai.tech over TLS."
        entities = self.cot.extract_entities(text)
        self.assertIn("api.anthropic.com", entities["domains"])
        self.assertIn("nullai.tech", entities["domains"])
        self.assertIn("zoth.nullai.tech", entities["domains"])

    def test_path_extraction(self) -> None:
        text = "Inspecting /etc/passwd and /var/log/auth.log alongside ./bin/zoth-cot-mcp."
        entities = self.cot.extract_entities(text)
        self.assertIn("/etc/passwd", entities["paths"])
        self.assertIn("/var/log/auth.log", entities["paths"])
        self.assertIn("./bin/zoth-cot-mcp", entities["paths"])

    def test_url_paths_not_misclassified_as_local_paths(self) -> None:
        text = "Fetch https://cot.nullai.tech/api/state and inspect /etc/hosts."
        entities = self.cot.extract_entities(text)
        self.assertIn("cot.nullai.tech", entities["domains"])
        self.assertIn("/etc/hosts", entities["paths"])
        self.assertFalse(any("cot.nullai.tech" in p for p in entities["paths"]))

    def test_cve_extraction(self) -> None:
        text = "Found vulnerability CVE-2024-3094 and prior report cve-2021-44228 in the audit."
        entities = self.cot.extract_entities(text)
        self.assertIn("CVE-2024-3094", entities["cves"])
        self.assertIn("CVE-2021-44228", entities["cves"])

    def test_tool_extraction(self) -> None:
        text = "Armed nmap, wireshark, gitleaks, ollama, and zoth-cot for reconnaissance."
        entities = self.cot.extract_entities(text)
        self.assertIn("nmap", entities["tools"])
        self.assertIn("wireshark", entities["tools"])
        self.assertIn("gitleaks", entities["tools"])
        self.assertIn("ollama", entities["tools"])
        self.assertIn("zoth-cot", entities["tools"])

    def test_combined_entity_payload(self) -> None:
        text = (
            "Engaging target 10.0.2.15 on port 8080 at nullai.tech with nmap. "
            "Testing for CVE-2024-3094 and checking /etc/shadow."
        )
        entities = self.cot.extract_entities(text)
        self.assertIn("10.0.2.15", entities["ips"])
        self.assertIn("8080", entities["ports"])
        self.assertIn("nullai.tech", entities["domains"])
        self.assertIn("nmap", entities["tools"])
        self.assertIn("CVE-2024-3094", entities["cves"])
        self.assertIn("/etc/shadow", entities["paths"])


class TestFactAutoExtraction(unittest.TestCase):
    """Verify natural language fact auto-extraction, pinning, and unpinning logic."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None)

    def test_identity_extraction(self) -> None:
        extracted = self.cot.auto_extract_facts("Hello AZOTH, my name is Neal.")
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["category"], "IDENTITY")
        self.assertIn("Neal", extracted[0]["fact"])

        extracted2 = self.cot.auto_extract_facts("From now on call me Falcon-9.")
        self.assertEqual(len(extracted2), 1)
        self.assertEqual(extracted2[0]["category"], "IDENTITY")
        self.assertIn("Falcon-9", extracted2[0]["fact"])

    def test_identity_stopword_guard(self) -> None:
        extracted = self.cot.auto_extract_facts("I am scanning the cluster right now.")
        identities = [f for f in extracted if f["category"] == "IDENTITY"]
        self.assertEqual(identities, [])

    def test_memory_extraction(self) -> None:
        extracted = self.cot.auto_extract_facts(
            "Please remember that all network communication must go over Tor."
        )
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["category"], "MEMORY")
        self.assertIn("Tor", extracted[0]["fact"])

        extracted2 = self.cot.auto_extract_facts(
            "Don't forget that SQLite WAL mode is mandatory for concurrency."
        )
        self.assertEqual(len(extracted2), 1)
        self.assertEqual(extracted2[0]["category"], "MEMORY")
        self.assertIn("SQLite WAL mode", extracted2[0]["fact"])

    def test_mission_extraction(self) -> None:
        extracted = self.cot.auto_extract_facts("Target is 10.0.2.15:8145.")
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["category"], "MISSION")
        self.assertIn("10.0.2.15:8145", extracted[0]["fact"])

        extracted2 = self.cot.auto_extract_facts("Currently auditing nullai.tech.")
        self.assertEqual(len(extracted2), 1)
        self.assertEqual(extracted2[0]["category"], "MISSION")
        self.assertIn("nullai.tech", extracted2[0]["fact"])

    def test_secret_extraction(self) -> None:
        extracted = self.cot.auto_extract_facts("The secret word is AzothCipher7.")
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["category"], "SECRET")
        self.assertIn("AzothCipher7", extracted[0]["fact"])

    def test_duplicate_facts_not_readded(self) -> None:
        first = self.cot.auto_extract_facts("My name is Neal.")
        self.assertEqual(len(first), 1)
        fact_count_before = len(self.cot.pinned_facts)

        second = self.cot.auto_extract_facts("My name is Neal.")
        self.assertEqual(len(second), 0)
        self.assertEqual(len(self.cot.pinned_facts), fact_count_before)

    def test_manual_pin_and_unpin_fact(self) -> None:
        item = self.cot.pin_fact(
            "Strict memory boundaries enforced by seccomp-bpf.",
            category="SECURITY",
        )
        self.assertEqual(item["category"], "SECURITY")
        self.assertTrue(item["active"])

        # Deactivate
        res = self.cot.unpin_fact(item["id"], delete=False)
        self.assertEqual(res["action"], "deactivated")
        self.assertFalse(item["active"])
        self.assertNotIn("seccomp-bpf", self.cot.compile_system_prompt())

        # Permanent delete
        res_del = self.cot.unpin_fact(item["id"], delete=True)
        self.assertEqual(res_del["action"], "deleted")
        self.assertNotIn(item, self.cot.pinned_facts)

        with self.assertRaises(ValueError):
            self.cot.unpin_fact("fact-does-not-exist")


class TestDAGBranchingRevisionAndVerification(unittest.TestCase):
    """Verify DAG branching, thought revision, confidence, tags, node IDs, verification, stats, and export."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None)

    def test_branching_and_checkout(self) -> None:
        n1 = self.cot.add_step("Initial hypothesis: TCP timeout", phase="DEDUCTION", tags=["net", "Latency"], confidence=0.65)
        self.assertEqual(n1["id"], "N01")
        self.assertEqual(n1["branch"], "main")
        self.assertEqual(n1["tags"], ["net", "latency"])
        self.assertEqual(n1["confidence"], 0.65)

        # Fork from N00 on a new branch
        n2 = self.cot.add_step(
            "Alternative hypothesis: DNS resolver cache miss",
            phase="DEDUCTION",
            parent_hash="N00",
            branch="dns-theory",
            tags=["dns"],
            confidence=0.9,
        )
        self.assertEqual(n2["parent_hash"], self.cot.nodes[0]["hash"])
        self.assertEqual(n2["branch"], "dns-theory")
        self.assertEqual(self.cot.active_branch, "dns-theory")

        branches = self.cot.list_branches()
        self.assertEqual(branches["active_branch"], "dns-theory")
        branch_names = [b["name"] for b in branches["branches"]]
        self.assertIn("main", branch_names)
        self.assertIn("dns-theory", branch_names)

        # Checkout back to main
        chk = self.cot.checkout_branch("main")
        self.assertFalse(chk["created"])
        self.assertEqual(self.cot.head_hash, n1["hash"])

        # Verification must pass on branched DAG
        verify = self.cot.verify_chain()
        self.assertTrue(verify["valid"])
        self.assertEqual(verify["issues"], [])

    def test_thought_revision_and_confidence_validation(self) -> None:
        n1 = self.cot.add_step("Assume port 8080 is HTTP", phase="DEDUCTION", confidence=0.5)
        n2 = self.cot.add_step(
            "Confirmed port 8080 serves TLS/HTTPS",
            phase="VERIFICATION",
            confidence=0.98,
            revises=n1["id"],
            tags=["tls", "verified"],
        )
        self.assertEqual(n2["revises"], n1["id"])
        self.assertEqual(n1["superseded_by"], n2["id"])

        with self.assertRaises(ValueError):
            self.cot.add_step("Out of bounds confidence", confidence=1.5)
        with self.assertRaises(ValueError):
            self.cot.add_step("Unknown parent", parent_hash="deadbeef0000")

    def test_merkle_tamper_and_broken_link_detection(self) -> None:
        n1 = self.cot.add_step("Legitimate deduction", phase="DEDUCTION")
        self.assertTrue(self.cot.verify_chain()["valid"])

        # Tamper with thought text without updating hash
        n1["thought"] = "TAMPERED CONTENT"
        v_tampered = self.cot.verify_chain()
        self.assertFalse(v_tampered["valid"])
        self.assertTrue(any("tampering" in i.lower() for i in v_tampered["issues"]))

        # Fix text, break parent pointer
        n1["thought"] = "Legitimate deduction"
        n1["parent_hash"] = "ffffffffffff"
        n1["parentHash"] = "ffffffffffff"
        v_broken = self.cot.verify_chain()
        self.assertFalse(v_broken["valid"])
        self.assertTrue(any("broken parent" in i.lower() for i in v_broken["issues"]))

    def test_node_id_monotonicity_past_capacity(self) -> None:
        cot = ChainOfThoughts(storage_path=None, max_nodes=12)
        ids = [cot.add_step(f"Step {i}")["id"] for i in range(1, 20)]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids[-1], "N19")
        self.assertEqual(cot.nodes[0]["id"], "N00")

    def test_filtered_search_stats_and_export(self) -> None:
        self.cot.add_step("Inspecting TLS certs", phase="AUDIT", branch="sec", tags=["tls", "cert"], confidence=0.92)
        self.cot.add_step("Low confidence hunch", phase="DEDUCTION", branch="main", tags=["misc"], confidence=0.25)
        self.cot.add_turn("user", "Audit nullai.tech on port 443 with nmap")

        # Filter-only search (no keyword)
        res_high = self.cot.search(min_confidence=0.85, tag="tls", branch="sec")
        self.assertEqual(len(res_high["matched_thoughts"]), 1)
        self.assertEqual(res_high["matched_thoughts"][0]["phase"], "AUDIT")

        # Entity search
        res_ent = self.cot.search("nullai.tech")
        self.assertTrue(any(e["value"] == "nullai.tech" for e in res_ent["matched_entities"]))

        # Stats
        stats = self.cot.get_stats()
        self.assertEqual(stats["node_count"], 3)
        self.assertEqual(stats["branch_count"], 2)
        self.assertEqual(stats["phases"]["AUDIT"], 1)
        self.assertTrue(stats["merkle_valid"])
        self.assertIsNotNone(stats["avg_confidence"])

        # Export Markdown & JSON
        md = self.cot.export_trace("markdown")
        self.assertIn("# Chain of Thoughts Trace", md)
        self.assertIn("Inspecting TLS certs", md)
        self.assertIn("`tls`", md)

        raw_json = self.cot.export_trace("json")
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["head_hash"], self.cot.head_hash)
        self.assertTrue(parsed["verification"]["valid"])

        # Clear turns preserves facts & nodes
        cleared = self.cot.clear_turns()
        self.assertEqual(cleared["cleared_messages"], 1)
        self.assertEqual(len(self.cot.messages), 0)
        self.assertEqual(len(self.cot.nodes), 3)


class TestRollingCheckpoint(unittest.TestCase):
    """Verify rolling checkpoint synthesis at configured turn intervals."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None, max_turns=4, checkpoint_interval=2)

    def test_rolling_checkpoint_interval_trigger(self) -> None:
        t1 = self.cot.add_turn("user", "Target is 10.0.2.15 on port 8080.")
        self.assertFalse(t1["checkpoint_updated"])
        t2 = self.cot.add_turn("assistant", "Acknowledged. Initialized nmap reconnaissance.")
        self.assertFalse(t2["checkpoint_updated"])
        self.assertEqual(len(self.cot.checkpoints), 0)

        t3 = self.cot.add_turn("user", "Inspect /var/log/auth.log for CVE-2024-3094.")
        self.assertFalse(t3["checkpoint_updated"])
        t4 = self.cot.add_turn("assistant", "Analysis completed. Log file indicates zero compromise.")
        self.assertTrue(t4["checkpoint_updated"])

        self.assertEqual(len(self.cot.checkpoints), 1)
        chk = self.cot.last_checkpoint
        self.assertIsNotNone(chk)
        self.assertEqual(chk["turn_index"], 2)
        self.assertIn("Checkpoint at turn 2", chk["summary"])
        self.assertIn("10.0.2.15", chk["summary"])

    def test_turn_window_compression_bounds(self) -> None:
        for i in range(10):
            self.cot.add_turn("user", f"Operator turn #{i + 1}")
            self.cot.add_turn("assistant", f"Agent response #{i + 1}")

        self.assertLessEqual(len(self.cot.messages), 8)
        self.assertGreaterEqual(len(self.cot.checkpoints), 2)

    def test_turn_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.cot.add_turn("invalid_role", "hello")
        with self.assertRaises(ValueError):
            self.cot.add_turn("user", "   ")


class TestPromptCompilation(unittest.TestCase):
    """Verify structured prompt compilation for LLM injection."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None)
        self.cot.add_turn("user", "My name is Neal. Target domain is nullai.tech.")
        self.cot.add_turn("assistant", "Understood Neal. Tracking nullai.tech.")
        self.cot.add_step("Configured DNS resolver to 1.1.1.1", phase="DEDUCTION")

    def test_compile_system_prompt_structure(self) -> None:
        prompt = self.cot.compile_system_prompt()
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", prompt)
        self.assertIn("</CHAIN_OF_THOUGHTS_MEMORY>", prompt)
        self.assertIn(f"HEAD_HASH: {self.cot.head_hash}", prompt)
        self.assertIn("[PINNED FACTS]", prompt)
        self.assertIn("[EXTRACTED ENTITIES]", prompt)
        self.assertIn("[ROLLING CHECKPOINT]", prompt)
        self.assertIn("[RECENT REASONING CHAIN]", prompt)
        self.assertIn("[CONTINUITY DIRECTIVE]", prompt)
        self.assertIn("nullai.tech", prompt)
        self.assertIn("Neal", prompt)

    def test_compile_system_prompt_with_base(self) -> None:
        base = "You are AZOTH, an embodied sovereign agent."
        compiled = self.cot.compile_system_prompt(base_prompt=base)
        self.assertTrue(compiled.startswith(base))
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", compiled)

    def test_compile_messages(self) -> None:
        messages = self.cot.compile_messages(system_prompt="Base prompt", max_turns=5)
        self.assertGreaterEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("nullai.tech", messages[1]["content"])
        self.assertEqual(messages[2]["role"], "assistant")


class TestMCPServerJSONRPC(unittest.TestCase):
    """Verify JSON-RPC 2.0 MCP protocol handling across all 12 tools."""

    def setUp(self) -> None:
        self.cot = ChainOfThoughts(storage_path=None)
        self.server = MCPServer(cot=self.cot)

    def test_initialize_handshake(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "clientInfo": {"name": "test-suite", "version": "1.0.0"},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], 1)
        self.assertEqual(res["result"]["protocolVersion"], MCP_PROTOCOL_VERSION)
        self.assertEqual(res["result"]["serverInfo"]["name"], SERVER_NAME)
        self.assertEqual(res["result"]["serverInfo"]["version"], SERVER_VERSION)

    def test_initialized_notification(self) -> None:
        req = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        self.assertIsNone(self.server.handle_request(req))

    def test_ping(self) -> None:
        res = self.server.handle_request({"jsonrpc": "2.0", "id": 42, "method": "ping"})
        self.assertEqual(res["id"], 42)
        self.assertEqual(res["result"], {})

    def test_tools_list(self) -> None:
        res = self.server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tool_names = [t["name"] for t in res["result"]["tools"]]
        expected_tools = [
            "cot_status",
            "cot_add_turn",
            "cot_pin_fact",
            "cot_unpin_fact",
            "cot_add_step",
            "cot_branches",
            "cot_compile_prompt",
            "cot_search",
            "cot_verify",
            "cot_stats",
            "cot_export",
            "cot_clear_turns",
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names)

    def test_tool_call_cot_status(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 10, "method": "tools/call",
            "params": {"name": "cot_status", "arguments": {}},
        })
        self.assertFalse(res["result"]["isError"])
        content_json = json.loads(res["result"]["content"][0]["text"])
        self.assertTrue(content_json["ok"])
        self.assertEqual(content_json["active_branch"], "main")

    def test_tool_call_cot_pin_and_unpin_fact(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 11, "method": "tools/call",
            "params": {"name": "cot_pin_fact", "arguments": {"fact": "Air-gapped cold signer active.", "category": "HARDWARE"}},
        })
        self.assertFalse(res["result"]["isError"])
        fact_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(fact_data["category"], "HARDWARE")

        res_unpin = self.server.handle_request({
            "jsonrpc": "2.0", "id": 110, "method": "tools/call",
            "params": {"name": "cot_unpin_fact", "arguments": {"fact_id": fact_data["id"], "delete": True}},
        })
        self.assertFalse(res_unpin["result"]["isError"])
        unpin_data = json.loads(res_unpin["result"]["content"][0]["text"])
        self.assertEqual(unpin_data["action"], "deleted")

    def test_tool_call_cot_add_turn(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 12, "method": "tools/call",
            "params": {"name": "cot_add_turn", "arguments": {"role": "user", "content": "Target is 10.0.2.15 running nmap with CVE-2024-3094."}},
        })
        self.assertFalse(res["result"]["isError"])
        turn_data = json.loads(res["result"]["content"][0]["text"])
        self.assertIn("10.0.2.15", turn_data["extracted_entities"]["ips"])
        self.assertIn("nmap", turn_data["extracted_entities"]["tools"])
        self.assertIn("CVE-2024-3094", turn_data["extracted_entities"]["cves"])

    def test_tool_call_cot_add_step_and_branches_and_verify_stats_export(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 13, "method": "tools/call",
            "params": {
                "name": "cot_add_step",
                "arguments": {
                    "thought": "Verified SHA-256 Merkle root hash for working memory node.",
                    "phase": "VERIFICATION",
                    "branch": "audit",
                    "tags": ["merkle", "crypto"],
                    "confidence": 0.95,
                },
            },
        })
        self.assertFalse(res["result"]["isError"])
        node_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(node_data["phase"], "VERIFICATION")
        self.assertEqual(node_data["branch"], "audit")

        res_br = self.server.handle_request({
            "jsonrpc": "2.0", "id": 131, "method": "tools/call",
            "params": {"name": "cot_branches", "arguments": {"action": "list"}},
        })
        br_data = json.loads(res_br["result"]["content"][0]["text"])
        self.assertEqual(br_data["active_branch"], "audit")

        res_ver = self.server.handle_request({
            "jsonrpc": "2.0", "id": 132, "method": "tools/call",
            "params": {"name": "cot_verify", "arguments": {}},
        })
        self.assertTrue(json.loads(res_ver["result"]["content"][0]["text"])["valid"])

        res_stats = self.server.handle_request({
            "jsonrpc": "2.0", "id": 133, "method": "tools/call",
            "params": {"name": "cot_stats", "arguments": {}},
        })
        stats_data = json.loads(res_stats["result"]["content"][0]["text"])
        self.assertEqual(stats_data["phases"]["VERIFICATION"], 1)

        res_exp = self.server.handle_request({
            "jsonrpc": "2.0", "id": 134, "method": "tools/call",
            "params": {"name": "cot_export", "arguments": {"format": "markdown"}},
        })
        self.assertIn("# Chain of Thoughts Trace", res_exp["result"]["content"][0]["text"])

    def test_tool_call_cot_compile_prompt(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 14, "method": "tools/call",
            "params": {"name": "cot_compile_prompt", "arguments": {"base_prompt": "You are a cyber sentinel."}},
        })
        text = res["result"]["content"][0]["text"]
        self.assertIn("You are a cyber sentinel.", text)
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", text)

    def test_tool_call_cot_search_and_clear_turns(self) -> None:
        self.cot.add_turn("user", "Checking subnet 172.16.0.0/16.")
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 15, "method": "tools/call",
            "params": {"name": "cot_search", "arguments": {"query": "172.16.0.0"}},
        })
        search_data = json.loads(res["result"]["content"][0]["text"])
        self.assertGreater(search_data["total_matches"], 0)

        res_clear = self.server.handle_request({
            "jsonrpc": "2.0", "id": 16, "method": "tools/call",
            "params": {"name": "cot_clear_turns", "arguments": {}},
        })
        clear_data = json.loads(res_clear["result"]["content"][0]["text"])
        self.assertEqual(clear_data["cleared_messages"], 1)

    def test_unknown_tool_and_method_errors(self) -> None:
        res = self.server.handle_request({
            "jsonrpc": "2.0", "id": 99, "method": "tools/call",
            "params": {"name": "non_existent_tool", "arguments": {}},
        })
        self.assertTrue(res["result"]["isError"])

        res2 = self.server.handle_request({"jsonrpc": "2.0", "id": 100, "method": "unknown/method"})
        self.assertEqual(res2["error"]["code"], -32601)

    def test_persistence_roundtrip(self) -> None:
        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, "cot_memory.json")
        try:
            cot1 = ChainOfThoughts(storage_path=state_file)
            cot1.pin_fact("Cold storage private keys unmounted.", category="SECURITY")
            cot1.add_turn("user", "Target is 192.168.10.50 with port 22.")
            cot1.add_step("Analyzed target response packet.", phase="DEDUCTION", branch="net-audit", tags=["ssh"], confidence=0.88)

            cot2 = ChainOfThoughts(storage_path=state_file)
            self.assertEqual(cot1.head_hash, cot2.head_hash)
            self.assertEqual(cot2.active_branch, "net-audit")
            self.assertEqual(len(cot1.nodes), len(cot2.nodes))
            self.assertIn("192.168.10.50", cot2.entities["ips"])
            self.assertIn("22", cot2.entities["ports"])
            self.assertTrue(cot2.verify_chain()["valid"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestMCPStdioSubprocess(unittest.TestCase):
    """End-to-end stdio subprocess round-trip tests (NDJSON + UTF-8 Content-Length framing)."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "mcp_stdio.json")
        self.mcp_bin = os.path.join(REPO_ROOT, "bin", "zoth-cot-mcp")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ndjson_stdio_roundtrip(self) -> None:
        env = os.environ.copy()
        env["ZOTH_COT_DATA_FILE"] = self.state_file

        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": MCP_PROTOCOL_VERSION}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "cot_add_step", "arguments": {"thought": "Unicode check ◈ αβγ", "phase": "AUDIT", "confidence": 0.9}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "cot_verify", "arguments": {}}},
        ]
        stdin_payload = ("\n".join(json.dumps(r, ensure_ascii=False) for r in requests) + "\n").encode("utf-8")

        proc = subprocess.run(
            [sys.executable, self.mcp_bin],
            input=stdin_payload,
            capture_output=True,
            env=env,
            timeout=10,
            check=True,
        )
        lines = [ln for ln in proc.stdout.decode("utf-8").splitlines() if ln.strip()]
        # 4 responses (notification emits none)
        self.assertEqual(len(lines), 4)
        r_init, r_list, r_step, r_ver = [json.loads(ln) for ln in lines]
        self.assertEqual(r_init["result"]["serverInfo"]["name"], SERVER_NAME)
        self.assertGreaterEqual(len(r_list["result"]["tools"]), 12)
        self.assertIn("Unicode check ◈ αβγ", r_step["result"]["content"][0]["text"])
        self.assertTrue(json.loads(r_ver["result"]["content"][0]["text"])["valid"])

    def test_content_length_utf8_framing(self) -> None:
        env = os.environ.copy()
        env["ZOTH_COT_DATA_FILE"] = self.state_file
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "cot_pin_fact", "arguments": {"fact": "Multibyte UTF-8 test: ◈ ⣿ ☕"}},
        }
        body = json.dumps(req, ensure_ascii=False).encode("utf-8")
        framed = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body

        proc = subprocess.run(
            [sys.executable, self.mcp_bin],
            input=framed,
            capture_output=True,
            env=env,
            timeout=10,
            check=True,
        )
        raw_out = proc.stdout
        self.assertTrue(raw_out.startswith(b"Content-Length:"))
        header, payload_bytes = raw_out.split(b"\r\n\r\n", 1)
        declared_len = int(header.decode("ascii").split(":", 1)[1].strip())
        self.assertEqual(declared_len, len(payload_bytes))
        parsed = json.loads(payload_bytes.decode("utf-8"))
        self.assertEqual(parsed["id"], 7)
        self.assertFalse(parsed["result"]["isError"])


class TestNodeCLIIntegration(unittest.TestCase):
    """End-to-end integration tests for `bin/zoth-cot` Node.js CLI."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "cli_memory.json")
        self.cli_bin = os.path.join(REPO_ROOT, "bin", "zoth-cot")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["node", self.cli_bin, "--file", self.state_file, *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=check,
        )

    def test_cli_full_workflow_and_python_interop(self) -> None:
        # Help & version
        self.assertIn("Usage:", self._run_cli("--help").stdout)
        ver = json.loads(self._run_cli("--version", "--json").stdout)
        self.assertEqual(ver["name"], "zoth-cot")

        # Pin + unpin
        pinned = json.loads(self._run_cli("--pin", "Strict zero-trust egress", "--category", "SECURITY", "--json").stdout)
        self.assertEqual(pinned["category"], "SECURITY")

        # Add steps + branch + revision
        s1 = json.loads(self._run_cli("--step", "Check TCP handshake", "--phase", "DEDUCTION", "--tag", "net,tcp", "--confidence", "0.7", "--json").stdout)
        self.assertEqual(s1["id"], "N01")
        s2 = json.loads(self._run_cli("--step", "Test DNS fallback", "--branch", "dns-branch", "--parent", "N00", "--confidence", "0.95", "--revises", "N01", "--json").stdout)
        self.assertEqual(s2["branch"], "dns-branch")
        self.assertEqual(s2["revises"], "N01")

        # Branches & checkout
        br = json.loads(self._run_cli("--branches", "--json").stdout)
        self.assertEqual(len(br["branches"]), 2)
        self._run_cli("--checkout", "main", "--json")

        # Turn + search + stats + compile + verify + export
        t1 = json.loads(self._run_cli("--turn", "Scanning 10.0.2.15 port 443 with nmap", "--role", "user", "--json").stdout)
        self.assertIn("10.0.2.15", t1["extracted_entities"]["ips"])

        search = json.loads(self._run_cli("--search", "--branch", "dns-branch", "--min-confidence", "0.9", "--json").stdout)
        self.assertEqual(len(search["matched_thoughts"]), 1)

        stats = json.loads(self._run_cli("--stats", "--json").stdout)
        self.assertEqual(stats["node_count"], 3)
        self.assertTrue(stats["merkle_valid"])

        verify = json.loads(self._run_cli("--verify", "--json").stdout)
        self.assertTrue(verify["valid"])

        compiled = self._run_cli("--compile").stdout
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", compiled)

        md_out = os.path.join(self.temp_dir, "trace.md")
        self._run_cli("--export", "markdown", "--out", md_out)
        with open(md_out, "r", encoding="utf-8") as f:
            self.assertIn("# Chain of Thoughts Trace", f.read())

        # Cross-runtime interop: Python ChainOfThoughts loads and verifies Node CLI's state file!
        cot_py = ChainOfThoughts(storage_path=self.state_file)
        self.assertTrue(cot_py.verify_chain()["valid"])
        self.assertEqual(len(cot_py.nodes), 3)
        self.assertIn("10.0.2.15", cot_py.entities["ips"])

        # Unpin + clear
        unp = json.loads(self._run_cli("--unpin", pinned["id"], "--json").stdout)
        self.assertEqual(unp["action"], "deactivated")
        clr = json.loads(self._run_cli("--clear", "--json").stdout)
        self.assertEqual(clr["cleared_messages"], 1)


class TestHTTPServerIntegration(unittest.TestCase):
    """End-to-end integration tests for `server.js` REST API on an ephemeral port."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "http_memory.json")
        self.port = _find_free_port()
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        env["ZOTH_COT_DATA_FILE"] = self.state_file
        self.proc = subprocess.Popen(
            ["node", os.path.join(REPO_ROOT, "server.js")],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait for server to bind
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=0.5) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.05)

    def tearDown(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=3)
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stderr:
            self.proc.stderr.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _req(self, path_str: str, method: str = "GET", body: dict = None):
        url = f"http://127.0.0.1:{self.port}{path_str}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if "application/json" in ctype else raw)

    def test_http_api_roundtrip(self) -> None:
        code, health = self._req("/health")
        self.assertEqual(code, 200)
        self.assertTrue(health["ok"])

        code, pin_res = self._req("/api/pin", "POST", {"fact": "API test constraint", "category": "TEST"})
        self.assertEqual(code, 200)
        fact_id = pin_res["fact"]["id"]

        code, turn_res = self._req("/api/turn", "POST", {"role": "user", "content": "Probing 10.0.2.15:8145 with nmap"})
        self.assertEqual(code, 200)
        self.assertIn("10.0.2.15", turn_res["extracted_entities"]["ips"])

        code, step_res = self._req("/api/step", "POST", {"thought": "Validated API node", "phase": "VERIFICATION", "branch": "api-branch", "tags": ["http"], "confidence": 0.9})
        self.assertEqual(code, 200)
        self.assertEqual(step_res["node"]["branch"], "api-branch")

        code, search_res = self._req("/api/search?branch=api-branch&tag=http&min_confidence=0.8")
        self.assertEqual(code, 200)
        self.assertEqual(len(search_res["matched_thoughts"]), 1)

        code, ver_res = self._req("/api/verify")
        self.assertEqual(code, 200)
        self.assertTrue(ver_res["valid"])

        code, stats_res = self._req("/api/stats")
        self.assertEqual(code, 200)
        self.assertEqual(stats_res["node_count"], 2)

        code, md_res = self._req("/api/export?format=markdown")
        self.assertEqual(code, 200)
        self.assertIn("# Chain of Thoughts Trace", md_res)

        code, unpin_res = self._req("/api/unpin", "POST", {"fact_id": fact_id, "delete": True})
        self.assertEqual(code, 200)
        self.assertEqual(unpin_res["action"], "deleted")

        code, clear_res = self._req("/api/clear", "POST", {})
        self.assertEqual(code, 200)
        self.assertTrue(clear_res["success"])


if __name__ == "__main__":
    unittest.main()

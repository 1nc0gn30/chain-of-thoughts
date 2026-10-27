#!/usr/bin/env python3
"""
test_zoth_cot.py — Comprehensive Unit Test Suite for Chain of Thoughts (zoth-cot) & MCP Server
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform

Tests:
- Entity extraction (IPs, ports, domains, paths, CVEs, tools)
- Fact auto-extraction ("my name is...", "remember that...", "target is...")
- Rolling checkpoint compression at turn intervals
- Prompt compilation (compile_system_prompt and compile_messages)
- JSON-RPC MCP server initialize, tools/list, and tools/call responses
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

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
        # Cumulative entity check
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
    """Verify natural language fact auto-extraction and pinning logic."""

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
        # First extraction
        first = self.cot.auto_extract_facts("My name is Neal.")
        self.assertEqual(len(first), 1)
        fact_count_before = len(self.cot.pinned_facts)

        # Duplicate prompt
        second = self.cot.auto_extract_facts("My name is Neal.")
        self.assertEqual(len(second), 0)
        self.assertEqual(len(self.cot.pinned_facts), fact_count_before)

    def test_manual_pin_fact(self) -> None:
        item = self.cot.pin_fact(
            "Strict memory boundaries enforced by seccomp-bpf.",
            category="SECURITY",
        )
        self.assertEqual(item["category"], "SECURITY")
        self.assertTrue(item["active"])
        self.assertIn("Strict memory boundaries", item["fact"])
        self.assertIn(item, self.cot.pinned_facts)


class TestRollingCheckpoint(unittest.TestCase):
    """Verify rolling checkpoint synthesis at configured turn intervals."""

    def setUp(self) -> None:
        # Set checkpoint interval to every 2 turns for rapid determinism
        self.cot = ChainOfThoughts(storage_path=None, max_turns=4, checkpoint_interval=2)

    def test_rolling_checkpoint_interval_trigger(self) -> None:
        # Turn 1
        t1 = self.cot.add_turn("user", "Target is 10.0.2.15 on port 8080.")
        self.assertFalse(t1["checkpoint_updated"])
        t2 = self.cot.add_turn("assistant", "Acknowledged. Initialized nmap reconnaissance.")
        self.assertFalse(t2["checkpoint_updated"])
        self.assertEqual(len(self.cot.checkpoints), 0)

        # Turn 2 (interval = 2 turns reached on assistant response)
        t3 = self.cot.add_turn("user", "Inspect /var/log/auth.log for CVE-2024-3094.")
        self.assertFalse(t3["checkpoint_updated"])
        t4 = self.cot.add_turn("assistant", "Analysis completed. Log file indicates zero compromise.")
        self.assertTrue(t4["checkpoint_updated"])

        # Verify checkpoint synthesized
        self.assertEqual(len(self.cot.checkpoints), 1)
        self.assertIsNotNone(self.cot.last_checkpoint)
        chk = self.cot.last_checkpoint
        self.assertEqual(chk["turn_index"], 2)
        self.assertIn("Checkpoint at turn 2", chk["summary"])
        self.assertIn("10.0.2.15", chk["summary"])

    def test_turn_window_compression_bounds(self) -> None:
        # max_turns is 4, meaning max 8 messages kept in rolling buffer
        for i in range(10):
            self.cot.add_turn("user", f"Operator turn #{i + 1}")
            self.cot.add_turn("assistant", f"Agent response #{i + 1}")

        # Messages must not exceed 2 * max_turns (8)
        self.assertLessEqual(len(self.cot.messages), 8)
        # Multiple checkpoints should have occurred
        self.assertGreaterEqual(len(self.cot.checkpoints), 2)


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
    """Verify JSON-RPC 2.0 MCP protocol handling: initialize, tools/list, and tools/call."""

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
        self.assertIn("result", res)
        self.assertEqual(res["result"]["protocolVersion"], MCP_PROTOCOL_VERSION)
        self.assertEqual(res["result"]["serverInfo"]["name"], SERVER_NAME)
        self.assertEqual(res["result"]["serverInfo"]["version"], SERVER_VERSION)
        self.assertIn("tools", res["result"]["capabilities"])

    def test_initialized_notification(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        res = self.server.handle_request(req)
        self.assertIsNone(res)

    def test_ping(self) -> None:
        req = {"jsonrpc": "2.0", "id": 42, "method": "ping"}
        res = self.server.handle_request(req)
        self.assertEqual(res["id"], 42)
        self.assertEqual(res["result"], {})

    def test_tools_list(self) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        expected_tools = [
            "cot_status",
            "cot_add_turn",
            "cot_pin_fact",
            "cot_add_step",
            "cot_compile_prompt",
            "cot_search",
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names)

    def test_tool_call_cot_status(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "cot_status", "arguments": {}},
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        content_json = json.loads(res["result"]["content"][0]["text"])
        self.assertTrue(content_json["ok"])
        self.assertIn("head_hash", content_json)
        self.assertIn("pinned_facts", content_json)
        self.assertIn("entities", content_json)

    def test_tool_call_cot_pin_fact(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "cot_pin_fact",
                "arguments": {
                    "fact": "Air-gapped hardware cold signer active.",
                    "category": "HARDWARE",
                },
            },
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        fact_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(fact_data["category"], "HARDWARE")
        self.assertIn("Air-gapped", fact_data["fact"])

    def test_tool_call_cot_add_turn(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "cot_add_turn",
                "arguments": {
                    "role": "user",
                    "content": "Target is 10.0.2.15 running nmap with CVE-2024-3094.",
                },
            },
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        turn_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(turn_data["role"], "user")
        self.assertIn("10.0.2.15", turn_data["extracted_entities"]["ips"])
        self.assertIn("nmap", turn_data["extracted_entities"]["tools"])
        self.assertIn("CVE-2024-3094", turn_data["extracted_entities"]["cves"])

    def test_tool_call_cot_add_step(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "cot_add_step",
                "arguments": {
                    "thought": "Verified SHA-256 Merkle root hash for working memory node.",
                    "phase": "VERIFICATION",
                },
            },
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        node_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(node_data["phase"], "VERIFICATION")
        self.assertIn("hash", node_data)
        self.assertEqual(self.cot.head_hash, node_data["hash"])

    def test_tool_call_cot_compile_prompt(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "cot_compile_prompt",
                "arguments": {"base_prompt": "You are a cyber sentinel."},
            },
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        text = res["result"]["content"][0]["text"]
        self.assertIn("You are a cyber sentinel.", text)
        self.assertIn("<CHAIN_OF_THOUGHTS_MEMORY>", text)

    def test_tool_call_cot_search(self) -> None:
        self.cot.add_turn("user", "Checking subnet 172.16.0.0/16.")
        req = {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {"name": "cot_search", "arguments": {"query": "172.16.0.0"}},
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"]["isError"])
        search_data = json.loads(res["result"]["content"][0]["text"])
        self.assertGreater(search_data["total_matches"], 0)
        self.assertEqual(len(search_data["matched_turns"]), 1)

    def test_unknown_tool_error(self) -> None:
        req = {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/call",
            "params": {"name": "non_existent_tool", "arguments": {}},
        }
        res = self.server.handle_request(req)
        self.assertTrue(res["result"]["isError"])
        self.assertIn("not found", res["result"]["content"][0]["text"])

    def test_unknown_method_error(self) -> None:
        req = {"jsonrpc": "2.0", "id": 100, "method": "unknown/method"}
        res = self.server.handle_request(req)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)

    def test_persistence_roundtrip(self) -> None:
        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, "cot_memory.json")
        try:
            # 1. Create and populate state
            cot1 = ChainOfThoughts(storage_path=state_file)
            cot1.pin_fact("Cold storage private keys unmounted.", category="SECURITY")
            cot1.add_turn("user", "Target is 192.168.10.50 with port 22.")
            cot1.add_step("Analyzed target response packet.", phase="DEDUCTION")

            # 2. Reload state in second instance
            cot2 = ChainOfThoughts(storage_path=state_file)
            self.assertEqual(cot1.head_hash, cot2.head_hash)
            self.assertEqual(len(cot1.nodes), len(cot2.nodes))
            self.assertIn("192.168.10.50", cot2.entities["ips"])
            self.assertIn("22", cot2.entities["ports"])
            facts = [f["fact"] for f in cot2.pinned_facts]
            self.assertTrue(any("Cold storage" in f for f in facts))

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

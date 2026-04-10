#!/usr/bin/env python3
"""
Comprehensive integration test for Monk CLI Epics.
Verifies core functionality across LLM Registry, Router, Workflow Engine, MCP, and Memory.
"""

import asyncio
import os
import sys
import logging

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import core components
from core.orchestrator import Orchestrator
from core.mcp_client import MCPClient
from core.unified_tool_router import UnifiedToolRouter
from core.procedural_memory import ProceduralMemoryManager
from core.vector_db import ChromaMemoryDB
from core.unified_api import UnifiedModelAPI
from core.episodic_memory import EpisodicMemoryManager
from core.prompt_augmentation import PromptAugmenter

async def run_all_epic_tests():
    print("\n--- Starting Comprehensive Monk CLI Epic Tests ---")
    test_results = {}

    # --- Setup: Initialize Orchestrator ---
    print("\n[SETUP] Initializing Orchestrator...")
    config_path = "/Users/Subho/models.yaml"
    if not os.path.exists(config_path):
        print(f"[FATAL] Configuration file not found at {config_path}. Please ensure task 25.1 was completed.")
        return False
    
    try:
        orchestrator = Orchestrator(config_path)
        test_results["Orchestrator_Init"] = "PASS"
        print("[SETUP] Orchestrator initialized successfully.")
    except Exception as e:
        test_results["Orchestrator_Init"] = f"FAIL: {e}"
        print(f"[SETUP] Orchestrator initialization FAILED: {e}")
        return False

    # --- EPIC 25 Test: LLM Registry and Unified API ---
    print("\n[TEST] EPIC 25: LLM Registry and Unified API")

    try:
        test_prompt = "Hello, what is the capital of France?"
        print(f"  - Testing simple completion with prompt: '{test_prompt}'")
        response = await orchestrator.api.get_completion(messages=[{"role": "user", "content": test_prompt}])
        if response and "paris" in response.lower():
            test_results["EPIC25_UnifiedAPI_Completion"] = "PASS"
            print(f"  - Unified API completion test PASSED. Response: {response[:50]}...")
        else:
            test_results["EPIC25_UnifiedAPI_Completion"] = f"FAIL: Unexpected response: {response}"
            print(f"  - Unified API completion test FAILED. Response: {response}")
    except Exception as e:
        test_results["EPIC25_UnifiedAPI_Completion"] = f"FAIL: {e}"
        print(f"  - Unified API completion test FAILED: {e}")

    # --- EPIC 26 Test: Router and Workflow Engine ---
    print("\n[TEST] EPIC 26: Router and Workflow Engine")

    try:
        complex_prompt = "Explain the actor model in concurrent programming and write a simple Python example."
        print(f"  - Testing complex prompt to trigger workflow: '{complex_prompt}'")
        workflow_output = await orchestrator.handle_prompt(complex_prompt)
        if isinstance(workflow_output, dict) and "research" in workflow_output and "coding" in workflow_output:
            test_results["EPIC26_Workflow_Execution"] = "PASS"
            print(f"  - Workflow execution test PASSED. Research: {workflow_output['research'][:50]}..., Coding: {workflow_output['coding'][:50]}...")
        else:
            test_results["EPIC26_Workflow_Execution"] = f"FAIL: Unexpected workflow output: {workflow_output}"
            print(f"  - Workflow execution test FAILED. Output: {workflow_output}")
    except Exception as e:
        test_results["EPIC26_Workflow_Execution"] = f"FAIL: {e}"
        print(f"  - Workflow execution test FAILED: {e}")

    # --- EPIC 27 Test: MCP Tool Protocol and Smithery.ai Integration ---
    print("\n[TEST] EPIC 27: MCP Tool Protocol and Smithery.ai Integration")

    try:
        # Test internal tool (file_system_list_directory)
        print("  - Testing internal tool: file_system_list_directory")
        # Need to instantiate UnifiedToolRouter separately as Orchestrator doesn't expose it directly
        mcp_client = MCPClient()
        tool_router = UnifiedToolRouter(mcp_client)
        await tool_router.initialize_registry() # Ensure registry is populated

        internal_tool_result = await tool_router.invoke_tool("file_system_list_directory", {"path": os.getcwd()})
        if internal_tool_result and "items" in internal_tool_result and isinstance(internal_tool_result["items"], list):
            test_results["EPIC27_InternalTool"] = "PASS"
            print(f"  - Internal tool test PASSED. Items found: {len(internal_tool_result['items'])}")
        else:
            test_results["EPIC27_InternalTool"] = f"FAIL: Unexpected internal tool result: {internal_tool_result}"
            print(f"  - Internal tool test FAILED. Result: {internal_tool_result}")

        # Test external tool (exa_web_search)
        print("  - Testing external tool: exa_web_search (mocked)")
        external_tool_result = await tool_router.invoke_tool("exa_search", {"query": "latest AI trends", "num_results": 1})
        if external_tool_result and isinstance(external_tool_result, list) and len(external_tool_result) > 0:
            test_results["EPIC27_ExternalTool"] = "PASS"
            print(f"  - External tool test PASSED. Results found: {len(external_tool_result)}")
        else:
            test_results["EPIC27_ExternalTool"] = f"FAIL: Unexpected external tool result: {external_tool_result}"
            print(f"  - External tool test FAILED. Result: {external_tool_result}")

    except Exception as e:
        test_results["EPIC27_Overall"] = f"FAIL: {e}"
        print(f"[TEST] EPIC 27 Overall FAILED: {e}")

    # --- EPIC 28 Test: Persistent Memory Store and Memory-Augmented Prompting ---
    print("\n[TEST] EPIC 28: Persistent Memory Store and Memory-Augmented Prompting")
    try:
        # Initialize memory components
        db = ChromaMemoryDB()
        # Need a dummy API for managers that require it, as we don't have a real one for testing here
        # For this test, we'll pass the orchestrator's api instance
        procedural_manager = ProceduralMemoryManager(db)
        episodic_manager = EpisodicMemoryManager(db, orchestrator.api)
        prompt_augmenter = PromptAugmenter(db, orchestrator.api)

        # Test procedural memory
        test_memory_text = "My favorite programming language is Python."
        print(f"  - Adding procedural memory: '{test_memory_text}'")
        memory_id = await procedural_manager.remember(test_memory_text)
        all_procedural = await procedural_manager.get_all_procedural_memories()
        if any(test_memory_text in m['document'] for m in all_procedural):
            test_results["EPIC28_ProceduralMemory"] = "PASS"
            print("  - Procedural memory test PASSED.")
        else:
            test_results["EPIC28_ProceduralMemory"] = "FAIL: Memory not found."
            print("  - Procedural memory test FAILED: Memory not found.")

        # Test prompt augmentation (requires embedding model, which is a placeholder)
        print("  - Testing prompt augmentation (dummy embeddings used)")
        augmented_prompt = await prompt_augmenter.augment_prompt("Tell me about my preferences.")
        if test_memory_text in augmented_prompt:
            test_results["EPIC28_PromptAugmentation"] = "PASS"
            print(f"  - Prompt augmentation test PASSED. Augmented prompt contains memory: {augmented_prompt[:100]}...")
        else:
            test_results["EPIC28_PromptAugmentation"] = "FAIL: Memory not augmented."
            print(f"  - Prompt augmentation test FAILED. Augmented prompt: {augmented_prompt}")

    except Exception as e:
        test_results["EPIC28_Overall"] = f"FAIL: {e}"
        print(f"[TEST] EPIC 28 Overall FAILED: {e}")

    print("\n--- Comprehensive Test Summary ---")
    overall_status = "PASS"
    for test, status in test_results.items():
        print(f"- {test}: {status}")
        if "FAIL" in status:
            overall_status = "FAIL"
    print(f"\nOverall Test Status: {overall_status}")
    return overall_status == "PASS"

if __name__ == "__main__":
    asyncio.run(run_all_epic_tests())

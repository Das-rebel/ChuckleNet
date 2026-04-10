#!/usr/bin/env python3
"""
Execution and validation script for Task 26.5: Create and Validate Sample 'Research and Code' Workflow
This script initializes the Orchestrator and runs a complex prompt to validate the workflow.
"""

import asyncio
import os
import sys
import logging

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from core.orchestrator import Orchestrator

async def main():
    """
    Main validation function.
    """
    print("🤖 Initializing the full Orchestrator...")
    
    # The Orchestrator expects the path to the models.yaml file.
    # This file was created in task 25.1.
    config_path = "/Users/Subho/models.yaml"
    if not os.path.exists(config_path):
        print(f"FATAL: Configuration file not found at {config_path}")
        print("Please ensure task 25.1 was completed successfully.")
        return

    try:
        orchestrator = Orchestrator(config_path)
    except Exception as e:
        print(f"FATAL: Failed to initialize Orchestrator: {e}")
        return

    print("\n🧪 Starting validation for the 'Research and Code' workflow.")
    print("---")
    
    complex_prompt = "Explain the actor model in concurrent programming and write a simple Python example using the 'thespian' library."
    print(f"📥 Using complex prompt: \"{complex_prompt}\"")
    print("---")

    # This call will trigger the entire chain:
    # 1. Orchestrator receives prompt.
    # 2. Router classifies it as 'complex_workflow'.
    # 3. Orchestrator builds and executes the sample workflow.
    # 4. Node 1 (research) runs.
    # 5. Node 2 (coding) runs, using the output of Node 1.
    # 6. The final state of the workflow is returned.
    final_state = await orchestrator.handle_prompt(complex_prompt)

    print("\n---")
    print("✅ Workflow execution finished.")
    print("\n📝 Final Workflow State:")
    
    if final_state and isinstance(final_state, dict):
        for node_id, result in final_state.items():
            if node_id == '__initial_input__':
                continue
            print(f"\n--- Node '{node_id}' Result ---")
            print(result)
    else:
        print("Workflow did not return a valid state dictionary.")
        print(f"Received: {final_state}")

if __name__ == "__main__":
    # Note: This test requires an internet connection and for LiteLLM
    # to be configured with API keys for the models in models.yaml.
    # The result of the LLM calls will depend on the provider.
    print("NOTE: This test will make live LLM API calls.")
    asyncio.run(main())

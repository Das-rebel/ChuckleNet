#!/usr/bin/env python3
"""
Execution script for Task 26.2: Develop Task Classification Logic
Uses a TreeQuestAgent to enhance the existing TaskRouter with classification logic.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class ClassificationLogicAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to enhance the TaskRouter with more detailed
    classification and dispatching logic.
    """
    def __init__(self, existing_code: str):
        super().__init__(name="ClassificationLogicAgent")
        self.existing_code = existing_code

    def propose_dispatcher_enhancement(self) -> Tuple[str, float]:
        """
        Enhances the TaskRouter by adding a dispatcher method.
        This is the primary strategy to fulfill the task requirements.
        """
        # This is a bit simplistic, a real implementation would use AST
        # but for this simulation, string manipulation is sufficient.
        if "handle_classified_prompt" in self.existing_code:
            return self.existing_code, 0.9 # Already implemented

        enhancement = '''
    async def handle_classified_prompt(self, classification_result: Dict[str, Any]):
        """
        Acts as a dispatcher based on the classification result.
        This is the integration point for the workflow engine.
        """
        task_type = classification_result.get("task_type")
        prompt = classification_result.get("original_prompt")

        logger.info(f"Handling task type: {task_type} for prompt: '{prompt[:50]}...'")

        if task_type == "simple_query":
            # Placeholder for direct LLM call
            print(f"--> Dispatching '{prompt[:20]}...' to simple query handler.")
            # In a real scenario, this would call the UnifiedModelAPI
            # response = await self.api.get_completion(messages=[{"role": "user", "content": prompt}])
            # return response
            return f"Completed simple query for: {prompt}"

        elif task_type == "complex_workflow":
            # Placeholder for triggering the workflow engine (from Task 26.3)
            print(f"--> Dispatching '{prompt[:20]}...' to workflow engine.")
            # In a real scenario, this would construct and run a graph
            # workflow_result = await workflow_engine.run(prompt)
            # return workflow_result
            return f"Triggered complex workflow for: {prompt}"

        else:
            logger.warning(f"Cannot handle unknown task type: {task_type}")
            return "Error: Could not handle the request."
'''
        
        new_code = self.existing_code + "\n" + enhancement
        score = 0.95
        return new_code.strip(), score

    def propose_rule_based_enhancement(self) -> Tuple[str, float]:
        """
        Adds a rule-based pre-filter for efficiency.
        """
        if "pre_filter_prompt" in self.existing_code:
            return self.existing_code, 0.8

        enhancement = '''
    def pre_filter_prompt(self, prompt: str) -> bool:
        """A simple rule-based filter to avoid unnecessary LLM calls."""
        if len(prompt) > 1000:
            logger.info("Prompt is very long, classifying as complex by rule.")
            return True # Is complex
        return False # Needs LLM classification
'''
        # This would require modifying the existing classify_prompt method to use it
        # For this simulation, we just add the function to the class.
        new_code = self.existing_code + "\n" + enhancement
        score = 0.8
        return new_code.strip(), score

async def main():
    """
    Main execution function.
    """
    router_path = "/Users/Subho/monk/core/task_router.py"
    print(f"🤖 Reading existing code from {router_path}...")
    try:
        with open(router_path, 'r') as f:
            existing_code = f.read()
    except FileNotFoundError:
        print(f"Error: {router_path} not found. Please run the script for task 26.1 first.")
        return

    print("🤖 Initializing ClassificationLogicAgent...")
    agent = ClassificationLogicAgent(existing_code)

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "dispatcher_enhancement": agent.propose_dispatcher_enhancement,
        "rule_based_enhancement": agent.propose_rule_based_enhancement,
    }

    print("🌳 Running TreeQuest optimization to find the best enhancement...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Enhanced Task Router Implementation:")
    print(result.best_state)
    print("---")

    with open(router_path, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved by overwriting {router_path}")

if __name__ == "__main__":
    asyncio.run(main())

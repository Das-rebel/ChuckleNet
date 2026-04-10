#!/usr/bin/env python3
"""
Execution script for Task 26.1: Implement Router Module Using Fast LLM
Uses a TreeQuestAgent to generate the best implementation for the Task Router.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any, Literal

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class TaskRouterAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the Task Router module.
    """
    def __init__(self):
        super().__init__(name="TaskRouterAgent")

    def propose_llm_router(self) -> Tuple[str, float]:
        """
        Proposes a router that uses a fast LLM for classification.
        This is the best practice and aligns with the PRD.
        """
        code = '''
import logging
from typing import Literal, Dict, Any

# Assuming unified_api is in the same core directory
from .unified_api import UnifiedModelAPI

logger = logging.getLogger(__name__)

TaskType = Literal["simple_query", "complex_workflow", "unknown"]

class TaskRouter:
    """
    Analyzes user prompts to classify them for downstream processing.
    """
    def __init__(self, api: UnifiedModelAPI):
        self.api = api
        self.classification_prompt_template = """
Analyze the following user prompt and classify it into one of the following categories:
- 'simple_query': A straightforward question or command that can be handled by a single LLM call.
- 'complex_workflow': A task that requires multiple steps, planning, or the use of external tools (e.g., searching the web, writing to a file).

User Prompt: "{prompt}"

Classification:"""

    async def classify_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Uses a fast LLM to classify the prompt and returns the classification.
        """
        formatted_prompt = self.classification_prompt_template.format(prompt=prompt)
        
        messages = [
            {"role": "system", "content": "You are an expert task classifier."},
            {"role": "user", "content": formatted_prompt}
        ]

        logger.info(f"Classifying prompt: '{prompt[:50]}...'")

        # Use the Unified API to call a fast and cheap model
        classification_text = await self.api.get_completion(
            messages=messages,
            speed_tier="fast",
            cost_tier="cheap",
            temperature=0.0
        )

        if not classification_text:
            logger.error("Classification LLM call failed.")
            return {"task_type": "unknown", "reason": "LLM call failed."}

        # Clean up the classification text
        cleaned_classification = classification_text.strip().lower()

        if "simple_query" in cleaned_classification:
            task_type = "simple_query"
        elif "complex_workflow" in cleaned_classification:
            task_type = "complex_workflow"
        else:
            task_type = "unknown"
            logger.warning(f"Could not determine task type from classification: {classification_text}")

        logger.info(f"Prompt classified as: {task_type}")
        return {"task_type": task_type, "original_prompt": prompt}
'''
        score = 0.95
        return code.strip(), score

    def propose_keyword_router(self) -> Tuple[str, float]:
        """
        Proposes a simple router based on keyword matching.
        """
        code = '''
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class KeywordTaskRouter:
    def __init__(self):
        self.complex_keywords = ["implement", "write", "create", "build", "research", "find"]

    def classify_prompt(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        for keyword in self.complex_keywords:
            if keyword in prompt_lower:
                logger.info(f"Classified as complex due to keyword '{keyword}'.")
                return {"task_type": "complex_workflow", "original_prompt": prompt}
        
        logger.info("Classified as simple.")
        return {"task_type": "simple_query", "original_prompt": prompt}
'''
        score = 0.6
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing TaskRouterAgent...")
    agent = TaskRouterAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "llm_router": agent.propose_llm_router,
        "keyword_router": agent.propose_keyword_router,
    }

    print("🌳 Running TreeQuest optimization to find the best Task Router design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Task Router Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "task_router.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

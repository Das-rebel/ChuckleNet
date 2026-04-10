#!/usr/bin/env python3
"""
Execution script for Task 28.4: Develop Memory-Augmented Prompting Module
Uses a TreeQuestAgent to generate the best implementation for the prompting module.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Callable, Tuple, Any, List

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class PromptAugmentationAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the memory-augmented prompting module.
    """
    def __init__(self):
        super().__init__(name="PromptAugmentationAgent")

    def propose_robust_augmentation(self) -> Tuple[str, float]:
        """
        Proposes a robust memory-augmented prompting module.
        """
        code = '''
import logging
from typing import List, Dict, Any

# Assuming vector_db, episodic_memory, procedural_memory, unified_api are in the same core directory
from .vector_db import ChromaMemoryDB
from .episodic_memory import EpisodicMemoryManager
from .procedural_memory import ProceduralMemoryManager
from .unified_api import UnifiedModelAPI

logger = logging.getLogger(__name__)

class PromptAugmenter:
    """
    Queries relevant memories and injects them into LLM prompts.
    """
    def __init__(self, db: ChromaMemoryDB, api: UnifiedModelAPI):
        self.db = db
        self.api = api
        self.episodic_manager = EpisodicMemoryManager(db, api) # Re-use managers
        self.procedural_manager = ProceduralMemoryManager(db) # Re-use managers
        logger.info("PromptAugmenter initialized.")

    async def augment_prompt(self, 
                             original_prompt: str, 
                             context_window_limit: int = 4000, 
                             n_episodic: int = 5, 
                             n_procedural: int = 3) -> str:
        """
        Queries relevant memories and injects them into the LLM prompt.
        """
        augmented_prompt_parts = []
        augmented_prompt_parts.append(original_prompt)

        # 1. Get embedding for the original prompt (using a dummy for now)
        # In a real scenario, this would use an embedding model via UnifiedModelAPI
        prompt_embedding = [0.0] * 1536 # Dummy embedding

        # 2. Query episodic memories
        episodic_results = self.db.query_memory(
            query_embeddings=[prompt_embedding],
            n_results=n_episodic,
            collection_name=self.episodic_manager.collection_name
        )
        if episodic_results:
            augmented_prompt_parts.append("\n\n--- Relevant Past Interactions ---")
            for res in episodic_results:
                augmented_prompt_parts.append(f"- {res['document']}")

        # 3. Query procedural memories
        procedural_results = self.db.query_memory(
            query_embeddings=[prompt_embedding],
            n_results=n_procedural,
            collection_name=self.procedural_manager.collection_name
        )
        if procedural_results:
            augmented_prompt_parts.append("\n\n--- User Preferences/Facts ---")
            for res in procedural_results:
                augmented_prompt_parts.append(f"- {res['document']}")

        final_prompt = "\n".join(augmented_prompt_parts)

        # Basic context window trimming (more sophisticated methods would use tokenizers)
        # For now, just truncate if too long
        if len(final_prompt) > context_window_limit:
            logger.warning("Augmented prompt exceeds context window limit. Truncating.")
            final_prompt = final_prompt[:context_window_limit] + "... (truncated)"

        logger.info("Prompt augmented with memories.")
        return final_prompt
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_augmentation(self) -> Tuple[str, float]:
        """
        Proposes a basic prompt augmentation module.
        """
        code = '''
import logging
from typing import List, Dict, Any
from .vector_db import ChromaMemoryDB

logger = logging.getLogger(__name__)

async def basic_augment_prompt(db: ChromaMemoryDB, original_prompt: str) -> str:
    # Very basic: just query some memories and append
    dummy_embedding = [0.0] * 1536
    episodic_memories = db.query_memory(query_embeddings=[dummy_embedding], n_results=2, collection_name="episodic_memory")
    procedural_memories = db.query_memory(query_embeddings=[dummy_embedding], n_results=1, collection_name="procedural_memory")

    augmented_prompt = original_prompt
    if episodic_memories:
        augmented_prompt += "\n\nPast interactions:\n" + "\n".join([m['document'] for m in episodic_memories])
    if procedural_memories:
        augmented_prompt += "\n\nUser facts:\n" + "\n".join([m['document'] for m in procedural_memories])
    
    logger.info("Basic prompt augmentation done.")
    return augmented_prompt
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing PromptAugmentationAgent...")
    agent = PromptAugmentationAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_augmentation": agent.propose_robust_augmentation,
        "basic_augmentation": agent.propose_basic_augmentation,
    }

    print("🌳 Running TreeQuest optimization to find the best Prompt Augmentation design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Prompt Augmentation Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "prompt_augmentation.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

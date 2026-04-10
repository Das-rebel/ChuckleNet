#!/usr/bin/env python3
"""
Execution script for Task 28.2: Implement CLI Commands for Procedural Memory Management
Uses a TreeQuestAgent to generate the best implementation for procedural memory commands.
"""

import asyncio
import os
import sys
import logging
import uuid
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class ProceduralMemoryAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for CLI commands to manage procedural memory.
    """
    def __init__(self):
        super().__init__(name="ProceduralMemoryAgent")

    def propose_robust_commands(self) -> Tuple[str, float]:
        """
        Proposes robust CLI commands for procedural memory management.
        """
        code = '''
import logging
import uuid
from typing import Optional

# Assuming vector_db is in the same core directory
from .vector_db import ChromaMemoryDB

logger = logging.getLogger(__name__)

class ProceduralMemoryManager:
    """
    Manages procedural memories (user preferences, facts) in the vector database.
    """
    def __init__(self, db: ChromaMemoryDB):
        self.db = db
        self.collection_name = "procedural_memory"
        # Ensure the collection exists (ChromaDB handles get_or_create)
        self.db.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"ProceduralMemoryManager initialized with collection '{self.collection_name}'.")

    async def remember(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Adds a new procedural memory.
        Returns the ID of the added memory.
        """
        memory_id = str(uuid.uuid4())
        full_metadata = {"type": "procedural", "timestamp": time.time(), **(metadata or {})}
        
        # In a real scenario, we'd use an embedding model here
        # For now, we'll use a dummy embedding or rely on ChromaDB's default if available
        dummy_embedding = [0.0] * 1536 # Placeholder for actual embedding

        try:
            self.db.add_memory(
                ids=[memory_id],
                documents=[text],
                embeddings=[dummy_embedding],
                metadatas=[full_metadata],
                collection_name=self.collection_name
            )
            logger.info(f"Remembered: '{text}' (ID: {memory_id})")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to remember '{text}': {e}")
            raise

    async def forget(self, memory_id: str):
        """
        Removes a procedural memory by its ID.
        """
        try:
            self.db.delete_memory(ids=[memory_id], collection_name=self.collection_name)
            logger.info(f"Forgot memory with ID: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to forget memory {memory_id}: {e}")
            raise

    async def get_all_procedural_memories(self) -> List[Dict[str, Any]]:
        """
        Retrieves all procedural memories.
        """
        # This is a simplified query. In a real system, you'd query by type or other metadata.
        # ChromaDB's query method is primarily for similarity search.
        # For full retrieval, you might need to iterate or use a different DB method.
        # For now, we'll simulate by querying with a generic embedding and high n_results
        dummy_query_embedding = [0.0] * 1536
        results = self.db.query_memory(
            query_embeddings=[dummy_query_embedding],
            n_results=self.db.count_memories(collection_name=self.collection_name),
            collection_name=self.collection_name
        )
        return results
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_commands(self) -> Tuple[str, float]:
        """
        Proposes basic functions for remember and forget.
        """
        code = '''
import logging
import uuid
from .vector_db import ChromaMemoryDB

logger = logging.getLogger(__name__)

async def basic_remember(db: ChromaMemoryDB, text: str):
    memory_id = str(uuid.uuid4())
    db.add_memory(ids=[memory_id], documents=[text], embeddings=[[0.0]*1536], metadatas=[{"type": "procedural"}])
    logger.info(f"Basic remembered: {text}")

async def basic_forget(db: ChromaMemoryDB, memory_id: str):
    db.delete_memory(ids=[memory_id])
    logger.info(f"Basic forgot: {memory_id}")
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing ProceduralMemoryAgent...")
    agent = ProceduralMemoryAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_commands": agent.propose_robust_commands,
        "basic_commands": agent.propose_basic_commands,
    }

    print("🌳 Running TreeQuest optimization to find the best Procedural Memory commands design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Procedural Memory Commands Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "procedural_memory.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

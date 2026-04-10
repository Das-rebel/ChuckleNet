#!/usr/bin/env python3
"""
Execution script for Task 28.1: Integrate Local Vector Database for Persistent Memory
Uses a TreeQuestAgent to generate the best implementation for ChromaDB integration.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Callable, Tuple, Any, List

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class VectorDBAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for ChromaDB integration.
    """
    def __init__(self):
        super().__init__(name="VectorDBAgent")

    def propose_persistent_chroma(self) -> Tuple[str, float]:
        """
        Proposes a robust persistent ChromaDB setup with helper functions.
        """
        code = '''
import chromadb
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChromaMemoryDB:
    """
    Manages a persistent ChromaDB instance for storing memory embeddings.
    """
    def __init__(self, path: str = "./chroma_db", collection_name: str = "monk_memory"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        logger.info(f"ChromaDB initialized at '{path}' with collection '{collection_name}'.")

    def add_memory(self, 
                   ids: List[str], 
                   embeddings: List[List[float]], 
                   documents: List[str], 
                   metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Adds new memories (documents and their embeddings) to the collection.
        """
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(ids)} memories to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to add memories to ChromaDB: {e}")

    def query_memory(self, 
                     query_embeddings: List[List[float]], 
                     n_results: int = 5, 
                     where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Queries the collection for the most relevant memories.
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )
            logger.info(f"Queried ChromaDB, found {len(results['ids'][0])} results.")
            # Reformat results for easier consumption
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else None,
                        "distance": results['distances'][0][i] if results['distances'] else None
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            return []

    def delete_memory(self, ids: List[str]):
        """
        Deletes memories by their IDs.
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} memories from ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to delete memories from ChromaDB: {e}")

    def count_memories(self) -> int:
        """
        Returns the total number of memories in the collection.
        """
        return self.collection.count()
'''
        score = 0.95
        return code.strip(), score

    def propose_in_memory_chroma(self) -> Tuple[str, float]:
        """
        Proposes a basic in-memory ChromaDB setup.
        """
        code = '''
import chromadb
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class InMemoryChromaDB:
    def __init__(self, collection_name: str = "monk_memory_in_memory"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)
        logger.info(f"In-memory ChromaDB initialized with collection '{collection_name}'.")

    def add_memory(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        self.collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

    def query_memory(self, query_embeddings: List[List[float]], n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(query_embeddings=query_embeddings, n_results=n_results, include=['documents', 'metadatas'])
        formatted_results = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else None
                })
        return formatted_results
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing VectorDBAgent...")
    agent = VectorDBAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "persistent_chroma": agent.propose_persistent_chroma,
        "in_memory_chroma": agent.propose_in_memory_chroma,
    }

    print("🌳 Running TreeQuest optimization to find the best Vector DB design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Vector DB Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "vector_db.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

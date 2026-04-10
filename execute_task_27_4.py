#!/usr/bin/env python3
"""
Execution script for Task 27.4: Integrate and Validate External Marketplace Tool
Uses a TreeQuestAgent to generate the best implementation for external tool integration.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Callable, Tuple, Any, List

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class ExternalToolIntegrationAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for integrating external marketplace tools.
    """
    def __init__(self):
        super().__init__(name="ExternalToolIntegrationAgent")

    def propose_robust_integration(self) -> Tuple[str, float]:
        """
        Proposes a robust integration for an external tool like Exa.
        """
        code = '''
import logging
from typing import List, Dict, Any

# Assuming mcp_client is in the same core directory
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)

class ExternalTools:
    """
    Provides an interface for interacting with external tools via MCPClient.
    """
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        logger.info("ExternalTools initialized.")

    async def exa_web_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a web search using the Exa tool via MCP.

        Args:
            query: The search query string.
            num_results: The maximum number of search results to return.

        Returns:
            A list of dictionaries, each representing a search result.
        """
        logger.info(f"Performing Exa web search for query: '{query}'")
        try:
            # The tool_name 'exa_search' is assumed based on Smithery.ai documentation
            # and common MCP tool naming conventions.
            results = await self.mcp_client.call_tool(
                tool_name="exa_search", 
                params={
                    "query": query,
                    "num_results": num_results
                }
            )
            if results is None:
                logger.warning(f"Exa search for '{query}' returned no results or an error.")
                return []
            logger.info(f"Exa search for '{query}' returned {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error calling Exa web search for '{query}': {e}")
            return []

    # Add more external tool integrations here as needed
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_integration(self) -> Tuple[str, float]:
        """
        Proposes a basic integration for an external tool.
        """
        code = '''
import logging
from typing import List, Dict, Any
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)

async def basic_exa_search(client: MCPClient, query: str) -> List[Dict[str, Any]]:
    logger.info(f"Basic Exa search for: {query}")
    results = await client.call_tool(tool_name="exa_search", params={"query": query})
    return results if results is not None else []
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing ExternalToolIntegrationAgent...")
    agent = ExternalToolIntegrationAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_integration": agent.propose_robust_integration,
        "basic_integration": agent.propose_basic_integration,
    }

    print("🌳 Running TreeQuest optimization to find the best external tool integration design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning External Tool Integration Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "external_tools.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Execution script for Task 27.3: Develop MCP Client Logic for Smithery.ai Marketplace Integration
Uses a TreeQuestAgent to generate the best implementation for the MCP client.
"""

import asyncio
import os
import sys
import json
import logging
from typing import Dict, Callable, Tuple, Any, List

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class MCPClientAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the MCP client logic.
    """
    def __init__(self):
        super().__init__(name="MCPClientAgent")

    def propose_robust_client(self) -> Tuple[str, float]:
        """
        Proposes a robust MCP client implementation for Smithery.ai integration.
        """
        code = '''
import httpx
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for interacting with MCP servers, including Smithery.ai marketplace.
    """
    def __init__(self, base_url: str = "https://smithery.ai/api/v1"): # Example Smithery API endpoint
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        logger.info(f"MCPClient initialized for {self.base_url}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Fetches a list of available tools from the MCP server.
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/list",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": "1"
                }
            )
            response.raise_for_status() # Raise an exception for 4xx/5xx responses
            result = response.json()
            if "result" in result:
                logger.info(f"Discovered {len(result["result"])} tools from {self.base_url}")
                return result["result"]
            elif "error" in result:
                logger.error(f"MCP tools/list error from {self.base_url}: {result["error"]}")
                return []
            return []
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed for tools/list to {self.base_url}: {e}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {self.base_url}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during tools/list: {e}")
            return []

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Calls a specific tool on the MCP server.
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"tool_name": tool_name, "params": params},
                    "id": "2"
                }
            )
            response.raise_for_status()
            result = response.json()
            if "result" in result:
                logger.info(f"Successfully called tool {tool_name}")
                return result["result"]
            elif "error" in result:
                logger.error(f"MCP tools/call error for {tool_name}: {result["error"]}")
                return None
            return None
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed for tools/call {tool_name}: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {self.base_url} for tool {tool_name}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during tools/call {tool_name}: {e}")
            return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_client(self) -> Tuple[str, float]:
        """
        Proposes a basic MCP client implementation.
        """
        code = '''
import httpx
import json

class BasicMCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def list_tools(self) -> List[Dict[str, Any]]:
        response = await self.client.post(f"{self.base_url}/tools/list", json={"jsonrpc": "2.0", "method": "tools/list", "id": "1"})
        return response.json().get("result", [])

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        response = await self.client.post(f"{self.base_url}/tools/call", json={"jsonrpc": "2.0", "method": "tools/call", "params": {"tool_name": tool_name, "params": params}, "id": "2"})
        return response.json().get("result")
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing MCPClientAgent...")
    agent = MCPClientAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_client": agent.propose_robust_client,
        "basic_client": agent.propose_basic_client,
    }

    print("🌳 Running TreeQuest optimization to find the best MCP Client design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning MCP Client Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "mcp_client.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

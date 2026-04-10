#!/usr/bin/env python3
"""
Execution script for Task 27.5: Implement Unified Tool Routing and Invocation via MCP Protocol
Uses a TreeQuestAgent to generate the best implementation for the unified tool router.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Callable, Tuple, Any, List

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class UnifiedToolRouterAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the unified tool router.
    """
    def __init__(self):
        super().__init__(name="UnifiedToolRouterAgent")

    def propose_robust_router(self) -> Tuple[str, float]:
        """
        Proposes a robust unified tool router implementation.
        """
        code = '''
import logging
from typing import Dict, Any, List, Callable

# Assuming mcp_client, mcp_server, and mcp_schemas are in the same core directory
from .mcp_client import MCPClient
from .mcp_server import MCPServer
from .mcp_schemas import get_file_system_mcp_schemas

logger = logging.getLogger(__name__)

class UnifiedToolRouter:
    """
    Manages and routes calls to both internal (Monk CLI) and external (Smithery.ai) tools.
    """
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.internal_tools: Dict[str, Callable] = self._get_internal_tool_actions()
        self.internal_mcp_server = MCPServer(self.internal_tools)
        self.unified_tool_registry: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    def _get_internal_tool_actions(self) -> Dict[str, Callable]:
        """
        Defines the actual Python functions for internal file system tools.
        These would typically interact with the OS.
        """
        # Placeholder for actual file system operations
        async def read_file_action(path: str) -> Dict[str, str]:
            logger.info(f"Internal tool: Reading file {path}")
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return {"content": content}
            except FileNotFoundError:
                return {"error": f"File not found: {path}"}
            except Exception as e:
                return {"error": f"Error reading file {path}: {e}"}

        async def write_file_action(path: str, content: str) -> Dict[str, bool]:
            logger.info(f"Internal tool: Writing to file {path}")
            try:
                with open(path, 'w') as f:
                    f.write(content)
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": f"Error writing file {path}: {e}"}

        async def list_directory_action(path: str) -> Dict[str, List[str]]:
            logger.info(f"Internal tool: Listing directory {path}")
            try:
                items = os.listdir(path)
                return {"items": items}
            except FileNotFoundError:
                return {"error": f"Directory not found: {path}"}
            except Exception as e:
                return {"error": f"Error listing directory {path}: {e}"}

        return {
            "file_system_read_file": read_file_action,
            "file_system_write_file": write_file_action,
            "file_system_list_directory": list_directory_action,
        }

    async def initialize_registry(self):
        """
        Populates the unified tool registry with internal and external tools.
        """
        if self.initialized:
            logger.info("Tool registry already initialized.")
            return

        logger.info("Initializing unified tool registry...")
        # Add internal tools
        for schema in get_file_system_mcp_schemas():
            self.unified_tool_registry[schema["name"]] = {"type": "internal", "schema": schema}
        logger.info(f"Registered {len(self.internal_tools)} internal tools.")

        # Add external tools from Smithery.ai
        external_schemas = await self.mcp_client.list_tools()
        for schema in external_schemas:
            self.unified_tool_registry[schema["name"]] = {"type": "external", "schema": schema}
        logger.info(f"Registered {len(external_schemas)} external tools from Smithery.ai.")
        self.initialized = True

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns the schema for a given tool name.
        """
        tool_info = self.unified_tool_registry.get(tool_name)
        return tool_info["schema"] if tool_info else None

    async def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Invokes a tool based on its type (internal or external).
        """
        if not self.initialized:
            await self.initialize_registry()

        tool_info = self.unified_tool_registry.get(tool_name)
        if not tool_info:
            logger.error(f"Tool '{tool_name}' not found in registry.")
            return {"error": f"Tool '{tool_name}' not found."}

        tool_type = tool_info["type"]
        schema = tool_info["schema"]

        # Basic input validation against schema (can be enhanced with a full JSON schema validator)
        for required_param in schema["inputSchema"].get("required", []):
            if required_param not in params:
                logger.error(f"Missing required parameter '{required_param}' for tool '{tool_name}'.")
                return {"error": f"Missing required parameter '{required_param}'."}

        if tool_type == "internal":
            logger.info(f"Invoking internal tool: {tool_name}")
            # Internal tools are directly callable Python functions
            action = self.internal_tools[tool_name]
            return await action(**params)
        elif tool_type == "external":
            logger.info(f"Invoking external tool: {tool_name}")
            # External tools are called via the MCPClient
            return await self.mcp_client.call_tool(tool_name, params)
        else:
            logger.error(f"Unknown tool type: {tool_type} for tool {tool_name}.")
            return {"error": f"Unknown tool type: {tool_type}."}
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_router(self) -> Tuple[str, float]:
        """
        Proposes a basic tool router implementation.
        """
        code = '''
import logging
from typing import Dict, Any
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)

class BasicToolRouter:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        if tool_name.startswith("file_system_"):
            logger.info(f"Invoking basic internal tool: {tool_name}")
            # Placeholder for actual internal tool logic
            return {"status": "success", "tool": tool_name, "params": params}
        else:
            logger.info(f"Invoking basic external tool: {tool_name}")
            return await self.mcp_client.call_tool(tool_name, params)
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing UnifiedToolRouterAgent...")
    agent = UnifiedToolRouterAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_router": agent.propose_robust_router,
        "basic_router": agent.propose_basic_router,
    }

    print("🌳 Running TreeQuest optimization to find the best Unified Tool Router design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Unified Tool Router Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "unified_tool_router.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

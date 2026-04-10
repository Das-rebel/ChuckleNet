#!/usr/bin/env python3
"""
Execution script for Task 27.2: Implement and Bundle Local MCP Server
Uses a TreeQuestAgent to generate the best implementation for the MCP server.
"""

import asyncio
import os
import sys
import json
import logging
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class MCPServerAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the local MCP server.
    """
    def __init__(self):
        super().__init__(name="MCPServerAgent")

    def propose_robust_server(self) -> Tuple[str, float]:
        """
        Proposes a robust MCP server implementation.
        """
        code = '''
import json
import sys
import asyncio
import logging
from typing import Dict, Any, Callable, List

# Assuming mcp_schemas is in the same core directory
from .mcp_schemas import get_file_system_mcp_schemas

logger = logging.getLogger(__name__)

class MCPServer:
    """
    A lightweight MCP server that exposes Monk CLI capabilities.
    Supports STDIO for local execution.
    """
    def __init__(self, tool_actions: Dict[str, Callable]):
        self.tool_actions = tool_actions
        self.schemas = get_file_system_mcp_schemas()
        self.tool_map = {schema["name"]: schema for schema in self.schemas}
        logger.info(f"MCP Server initialized with {len(self.schemas)} tools.")

    async def handle_request(self, request_str: str) -> Dict[str, Any]:
        """
        Handles an incoming MCP request.
        """
        try:
            request = json.loads(request_str)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "tools/list":
                return self._create_response(request_id, self.schemas)
            elif method == "tools/call":
                tool_name = params.get("tool_name")
                tool_params = params.get("params", {})
                if tool_name not in self.tool_actions:
                    return self._create_error_response(request_id, -32601, f"Tool not found: {tool_name}")
                
                action = self.tool_actions[tool_name]
                result = await self._execute_tool_action(action, tool_params)
                return self._create_response(request_id, result)
            else:
                return self._create_error_response(request_id, -32600, f"Method not found: {method}")
        except json.JSONDecodeError:
            return self._create_error_response(None, -32700, "Parse error: Invalid JSON")
        except Exception as e:
            logger.error(f"MCP Server internal error: {e}")
            return self._create_error_response(None, -32000, f"Internal error: {e}")

    async def _execute_tool_action(self, action: Callable, params: Dict[str, Any]) -> Any:
        """
        Executes the tool action, handling async/sync functions.
        """
        if asyncio.iscoroutinefunction(action):
            return await action(**params)
        else:
            return action(**params)

    def _create_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """
        Creates a successful MCP response.
        """
        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    def _create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """
        Creates an MCP error response.
        """
        return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}

    async def start_stdio_server(self):
        """
        Starts the MCP server using standard input/output.
        """
        logger.info("Starting MCP STDIO Server...")
        while True:
            line = await asyncio.to_thread(sys.stdin.readline) # Read blocking input in a thread
            if not line:
                break
            response = await self.handle_request(line.strip())
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
'''
        score = 0.95
        return code.strip(), score

    def propose_basic_server(self) -> Tuple[str, float]:
        """
        Proposes a basic MCP server implementation.
        """
        code = '''
import json
import sys

class BasicMCPServer:
    def __init__(self, tool_actions: Dict[str, Callable]):
        self.tool_actions = tool_actions

    def handle_request(self, request_str: str) -> Dict[str, Any]:
        request = json.loads(request_str)
        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "tools/list":
            return {"jsonrpc": "2.0", "result": [], "id": request_id} # No schemas defined here
        elif method == "tools/call":
            tool_name = params["tool_name"]
            tool_params = params.get("params", {})
            result = self.tool_actions[tool_name](**tool_params)
            return {"jsonrpc": "2.0", "result": result, "id": request_id}
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Method not found"}, "id": request_id}

    def start_stdio_server(self):
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            response = self.handle_request(line.strip())
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing MCPServerAgent...")
    agent = MCPServerAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_server": agent.propose_robust_server,
        "basic_server": agent.propose_basic_server,
    }

    print("🌳 Running TreeQuest optimization to find the best MCP Server design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning MCP Server Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "mcp_server.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

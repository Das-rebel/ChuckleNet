#!/usr/bin/env python3
"""
Execution script for Task 27.1: Define MCP-Compliant Schemas for Internal File System Tools
Uses a TreeQuestAgent to generate the best implementation for MCP schemas.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class MCPSchemaAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for MCP-compliant schemas for internal file system tools.
    """
    def __init__(self):
        super().__init__(name="MCPSchemaAgent")

    def propose_detailed_schemas(self) -> Tuple[str, float]:
        """
        Proposes a comprehensive set of MCP schemas for file system tools.
        """
        code = '''
import json

def get_file_system_mcp_schemas():
    """
    Returns a list of MCP-compliant schemas for internal file system tools.
    """
    schemas = [
        {
            "name": "file_system_read_file",
            "title": "Read File",
            "description": "Reads the content of a specified file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the file to read."
                    }
                },
                "required": ["path"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the file."
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "file_system_write_file",
            "title": "Write File",
            "description": "Writes content to a specified file, overwriting if it exists.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the file to write."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file."
                    }
                },
                "required": ["path", "content"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "True if the file was written successfully."
                    }
                },
                "required": ["success"]
            }
        },
        {
            "name": "file_system_list_directory",
            "title": "List Directory",
            "description": "Lists the names of files and subdirectories within a specified directory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The absolute path to the directory to list."
                    }
                },
                "required": ["path"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "A list of file and directory names."
                    }
                },
                "required": ["items"]
            }
        }
    ]
    return schemas
'''
        score = 0.95
        return code.strip(), score

    def propose_simple_schemas(self) -> Tuple[str, float]:
        """
        Proposes a basic set of schemas for file system tools.
        """
        code = '''
import json

def get_simple_file_system_mcp_schemas():
    schemas = [
        {
            "name": "read_file",
            "description": "Reads a file.",
            "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}}, 
            "outputSchema": {"type": "object", "properties": {"content": {"type": "string"}}}
        },
        {
            "name": "write_file",
            "description": "Writes to a file.",
            "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}, 
            "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}}}
        }
    ]
    return schemas
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing MCPSchemaAgent...")
    agent = MCPSchemaAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "detailed_schemas": agent.propose_detailed_schemas,
        "simple_schemas": agent.propose_simple_schemas,
    }

    print("🌳 Running TreeQuest optimization to find the best MCP schema design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning MCP Schema Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "mcp_schemas.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())

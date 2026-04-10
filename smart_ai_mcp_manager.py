#!/usr/bin/env python3
"""
Smart AI MCP Configuration Manager
Handles discovery, configuration, and integration of MCP (Model Context Protocol) tools
"""

import json
import asyncio
import subprocess
import socket
import time
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass
import logging

@dataclass
class MCPServer:
    """Represents an MCP server configuration"""
    name: str
    type: str  # stdio, sse, websocket
    command: str
    args: List[str]
    env: Dict[str, str]
    port: Optional[int] = None
    status: str = "unknown"  # unknown, running, stopped, error
    tools: List[str] = None
    capabilities: Set[str] = None

@dataclass 
class MCPTool:
    """Represents an MCP tool/capability"""
    name: str
    description: str
    server: str
    category: str  # task_management, file_system, browser, development, etc.
    parameters: Dict[str, Any]
    offline_capable: bool = False

class MCPConfigurationManager:
    """Manages MCP server configurations and tool discovery"""
    
    def __init__(self):
        self.config_paths = [
            Path.home() / ".mcp.json",
            Path.home() / ".claude" / "settings.local.json",
            Path.home() / ".claude" / "config.json"
        ]
        self.servers: Dict[str, MCPServer] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.tool_categories: Dict[str, List[str]] = {}
        self.offline_tools: Set[str] = set()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize MCP manager by reading configurations and discovering tools"""
        self.logger.info("🔧 Initializing MCP Configuration Manager...")
        
        # Read all MCP configurations
        await self.read_mcp_configurations()
        
        # Discover available MCP servers and their tools
        await self.discover_mcp_servers()
        
        # Categorize tools by capability
        self._categorize_tools()
        
        # Identify offline-capable tools
        self._identify_offline_tools()
        
        self.logger.info(f"✅ MCP Manager initialized with {len(self.servers)} servers and {len(self.tools)} tools")
        
    async def read_mcp_configurations(self):
        """Read MCP configurations from all standard locations"""
        for config_path in self.config_paths:
            if config_path.exists():
                await self._read_config_file(config_path)
    
    async def _read_config_file(self, config_path: Path):
        """Read a specific MCP configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Handle different configuration formats
            if 'mcpServers' in config:
                # Standard MCP configuration format
                await self._parse_mcp_servers(config['mcpServers'])
            elif 'enabledMcpjsonServers' in config:
                # Claude settings format - these reference .mcp.json servers
                enabled_servers = config.get('enabledMcpjsonServers', [])
                self.logger.info(f"📋 Found enabled MCP servers: {enabled_servers}")
            
            self.logger.info(f"📖 Read configuration from {config_path}")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Could not read {config_path}: {e}")
    
    async def _parse_mcp_servers(self, servers_config: Dict[str, Any]):
        """Parse MCP server configurations"""
        for server_name, server_config in servers_config.items():
            try:
                server = MCPServer(
                    name=server_name,
                    type=server_config.get('type', 'stdio'),
                    command=server_config.get('command', ''),
                    args=server_config.get('args', []),
                    env=server_config.get('env', {}),
                    port=server_config.get('port'),
                    tools=[],
                    capabilities=set()
                )
                
                self.servers[server_name] = server
                self.logger.info(f"📊 Configured MCP server: {server_name}")
                
            except Exception as e:
                self.logger.error(f"❌ Error parsing server {server_name}: {e}")
    
    async def discover_mcp_servers(self):
        """Discover running MCP servers and their available tools"""
        for server_name, server in self.servers.items():
            try:
                # Check if server is running
                server.status = await self._check_server_status(server)
                
                # Discover tools for all configured servers (even if stopped)
                # Many MCP servers work via npx and don't need to be "running"
                tools = await self._discover_server_tools(server)
                server.tools = tools
                
                # Add tools to global registry
                await self._register_server_tools(server_name, tools)
                    
                self.logger.info(f"🔍 Server {server_name}: {server.status} ({len(server.tools)} tools)")
                
            except Exception as e:
                self.logger.error(f"❌ Error discovering server {server_name}: {e}")
                server.status = "error"
    
    async def _check_server_status(self, server: MCPServer) -> str:
        """Check if an MCP server is running"""
        try:
            if server.type == "stdio":
                # For stdio servers, try to run a quick test
                if server.name == "task-master-ai":
                    # Special handling for TaskMaster
                    return await self._check_taskmaster_status()
                else:
                    # Generic stdio server check
                    return await self._check_stdio_server(server)
            elif server.type in ["sse", "websocket"] and server.port:
                # Check network servers
                return await self._check_network_server(server.port)
            else:
                return "unknown"
                
        except Exception as e:
            self.logger.debug(f"Server check failed for {server.name}: {e}")
            return "stopped"
    
    async def _check_taskmaster_status(self) -> str:
        """Check TaskMaster MCP server status"""
        try:
            # Try to run a simple TaskMaster command
            process = await asyncio.create_subprocess_exec(
                "npx", "-y", "--package=task-master-ai", "task-master-ai", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                return "running"
            else:
                return "stopped"
                
        except Exception:
            return "stopped"
    
    async def _check_stdio_server(self, server: MCPServer) -> str:
        """Check generic stdio MCP server"""
        try:
            # Try to start the server briefly to check if it's available
            process = await asyncio.create_subprocess_exec(
                server.command, *server.args, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            return "running" if process.returncode == 0 else "stopped"
        except Exception:
            return "stopped"
    
    async def _check_network_server(self, port: int) -> str:
        """Check if network MCP server is running on specified port"""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', port), 
                timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return "running"
        except Exception:
            return "stopped"
    
    async def _discover_server_tools(self, server: MCPServer) -> List[str]:
        """Discover available tools for an MCP server"""
        if server.name == "task-master-ai":
            return await self._discover_taskmaster_tools()
        elif server.name == "opendia":
            return await self._discover_opendia_tools()
        elif server.name == "filesystem":
            return await self._discover_filesystem_tools()
        elif server.name == "sqlite":
            return await self._discover_sqlite_tools()
        elif server.name == "git":
            return await self._discover_git_tools()
        else:
            return await self._discover_generic_mcp_tools(server)
    
    async def _discover_taskmaster_tools(self) -> List[str]:
        """Discover TaskMaster MCP tools"""
        taskmaster_tools = [
            "initialize_project",
            "get_tasks", 
            "add_task",
            "update_task",
            "set_task_status",
            "next_task",
            "get_task",
            "remove_task",
            "expand_task",
            "generate",
            "analyze_project_complexity",
            "models",
            "rules",
            "parse_prd",
            "research"
        ]
        
        # Register TaskMaster tools with metadata
        for tool_name in taskmaster_tools:
            self.tools[f"taskmaster_{tool_name}"] = MCPTool(
                name=tool_name,
                description=f"TaskMaster {tool_name.replace('_', ' ').title()}",
                server="task-master-ai",
                category="task_management",
                parameters={},
                offline_capable=False  # TaskMaster requires API keys
            )
        
        return taskmaster_tools
    
    async def _discover_opendia_tools(self) -> List[str]:
        """Discover OpenDia MCP tools"""
        opendia_tools = [
            "page_analyze",
            "page_extract_content", 
            "element_click",
            "element_fill",
            "page_navigate",
            "tab_create",
            "tab_close",
            "tab_list",
            "tab_switch",
            "get_bookmarks",
            "add_bookmark",
            "post_to_social",
            "research_workflow"
        ]
        
        # Register OpenDia tools
        for tool_name in opendia_tools:
            self.tools[f"opendia_{tool_name}"] = MCPTool(
                name=tool_name,
                description=f"OpenDia {tool_name.replace('_', ' ').title()}",
                server="opendia",
                category="browser_automation",
                parameters={},
                offline_capable=False  # Browser automation typically needs internet
            )
        
        return opendia_tools
    
    async def _discover_filesystem_tools(self) -> List[str]:
        """Discover Filesystem MCP tools"""
        filesystem_tools = [
            "read_file",
            "write_file", 
            "create_directory",
            "list_directory",
            "move_file",
            "search_files",
            "get_file_info"
        ]
        
        # Register Filesystem tools
        for tool_name in filesystem_tools:
            self.tools[f"filesystem_{tool_name}"] = MCPTool(
                name=tool_name,
                description=f"Filesystem {tool_name.replace('_', ' ').title()}",
                server="filesystem",
                category="file_system",
                parameters={},
                offline_capable=True  # Filesystem operations work offline
            )
        
        return filesystem_tools
    
    async def _discover_sqlite_tools(self) -> List[str]:
        """Discover SQLite MCP tools"""
        sqlite_tools = [
            "execute_query",
            "list_tables",
            "describe_table",
            "create_table",
            "insert_data",
            "update_data",
            "delete_data"
        ]
        
        # Register SQLite tools
        for tool_name in sqlite_tools:
            self.tools[f"sqlite_{tool_name}"] = MCPTool(
                name=tool_name,
                description=f"SQLite {tool_name.replace('_', ' ').title()}",
                server="sqlite",
                category="database",
                parameters={},
                offline_capable=True  # SQLite works offline
            )
        
        return sqlite_tools
    
    async def _discover_git_tools(self) -> List[str]:
        """Discover Git MCP tools"""
        git_tools = [
            "git_status",
            "git_log",
            "git_diff",
            "git_add",
            "git_commit",
            "git_branch",
            "git_checkout",
            "git_pull",
            "git_push",
            "git_clone"
        ]
        
        # Register Git tools  
        for tool_name in git_tools:
            self.tools[f"git_{tool_name}"] = MCPTool(
                name=tool_name,
                description=f"Git {tool_name.replace('_', ' ').title()}",
                server="git", 
                category="development",
                parameters={},
                offline_capable=True  # Most Git operations work offline
            )
        
        return git_tools
    
    async def _discover_generic_mcp_tools(self, server: MCPServer) -> List[str]:
        """Discover tools for generic MCP servers"""
        # This would implement MCP protocol tool discovery
        # For now, return empty list for unknown servers
        return []
    
    async def _register_server_tools(self, server_name: str, tools: List[str]):
        """Register tools from a server into the global tool registry"""
        for tool_name in tools:
            tool_key = f"{server_name}_{tool_name}"
            if tool_key not in self.tools:
                # Create generic tool entry if not already registered
                self.tools[tool_key] = MCPTool(
                    name=tool_name,
                    description=f"{server_name} {tool_name}",
                    server=server_name,
                    category="general",
                    parameters={}
                )
    
    def _categorize_tools(self):
        """Categorize tools by their capabilities"""
        self.tool_categories = {
            "task_management": [],
            "browser_automation": [],
            "file_system": [],
            "database": [],
            "development": [],
            "system": [],
            "general": []
        }
        
        for tool_key, tool in self.tools.items():
            category = tool.category
            if category not in self.tool_categories:
                category = "general"
            self.tool_categories[category].append(tool_key)
    
    def _identify_offline_tools(self):
        """Identify which tools can work offline"""
        for tool_key, tool in self.tools.items():
            if tool.offline_capable:
                self.offline_tools.add(tool_key)
    
    def get_available_tools(self, category: Optional[str] = None, offline_only: bool = False) -> List[str]:
        """Get available tools, optionally filtered by category or offline capability"""
        tools = []
        
        if category:
            tools = self.tool_categories.get(category, [])
        else:
            tools = list(self.tools.keys())
        
        if offline_only:
            tools = [tool for tool in tools if tool in self.offline_tools]
        
        return tools
    
    def get_optimal_tool_for_task(self, prompt: str, offline_mode: bool = False) -> Optional[str]:
        """Get the optimal MCP tool for a given task prompt"""
        prompt_lower = prompt.lower()
        
        # Task management keywords -> TaskMaster tools (check first - highest priority)
        task_keywords = ['task', 'project', 'todo', 'track', 'manage', 'plan', 'status', 'create task', 'add task', 'list tasks']
        if any(keyword in prompt_lower for keyword in task_keywords):
            if not offline_mode:  # TaskMaster requires internet
                return "taskmaster_get_tasks"  # Default TaskMaster tool
        
        # File operations -> Filesystem tools
        file_keywords = ['file', 'read', 'write', 'create', 'directory', 'folder', 'search files']
        if any(keyword in prompt_lower for keyword in file_keywords):
            return "filesystem_read_file"  # Default filesystem tool
        
        # Database operations -> SQLite tools  
        db_keywords = ['database', 'query', 'table', 'sql', 'data', 'insert', 'select']
        if any(keyword in prompt_lower for keyword in db_keywords):
            return "sqlite_execute_query"  # Default SQLite tool
        
        # Git operations -> Git tools
        git_keywords = ['git', 'commit', 'branch', 'repository', 'repo', 'version control', 'diff']
        if any(keyword in prompt_lower for keyword in git_keywords):
            return "git_git_status"  # Default Git tool
        
        
        # Browser keywords -> OpenDia tools
        browser_keywords = ['browse', 'click', 'navigate', 'extract', 'bookmark', 'social']
        if any(keyword in prompt_lower for keyword in browser_keywords):
            if not offline_mode:  # Browser automation typically needs internet
                return "opendia_page_analyze"  # Default OpenDia tool
        
        return None
    
    def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """Get status information for a specific MCP server"""
        if server_name not in self.servers:
            return {"error": "Server not found"}
        
        server = self.servers[server_name]
        return {
            "name": server.name,
            "type": server.type,
            "status": server.status,
            "tools_count": len(server.tools),
            "tools": server.tools
        }
    
    def get_all_servers_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all configured MCP servers"""
        return {
            server_name: self.get_server_status(server_name)
            for server_name in self.servers.keys()
        }

# Global MCP manager instance
mcp_manager = None

async def get_mcp_manager() -> MCPConfigurationManager:
    """Get the global MCP manager instance, initializing if needed"""
    global mcp_manager
    if mcp_manager is None:
        mcp_manager = MCPConfigurationManager()
        await mcp_manager.initialize()
    return mcp_manager

# Example usage and testing
if __name__ == "__main__":
    async def test_mcp_manager():
        manager = MCPConfigurationManager()
        await manager.initialize()
        
        print("\n📊 MCP Servers Status:")
        for server_name, status in manager.get_all_servers_status().items():
            print(f"  {server_name}: {status['status']} ({status['tools_count']} tools)")
        
        print(f"\n🔧 Available Tool Categories:")
        for category, tools in manager.tool_categories.items():
            print(f"  {category}: {len(tools)} tools")
        
        print(f"\n🔍 Optimal tool for 'create a new task': {manager.get_optimal_tool_for_task('create a new task')}")
        print(f"🔍 Optimal tool for 'browse to google.com': {manager.get_optimal_tool_for_task('browse to google.com')}")
    
    # Run test
    asyncio.run(test_mcp_manager())
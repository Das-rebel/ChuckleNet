#!/usr/bin/env python3
"""
SmartAI Backend Processing Engine
Handles verbose AI provider responses in the background and provides clean CLI output
"""

import asyncio
import json
import time
import subprocess
from typing import Dict, Optional, Any, List
from pathlib import Path

# Import MCP Configuration Manager
from smart_ai_mcp_manager import get_mcp_manager, MCPConfigurationManager


class SmartAIBackend:
    """Backend processing engine for SmartAI CLI tool"""
    
    def __init__(self):
        self.session_data = {}
        self.token_usage = {}
        self.providers = ['claude_code', 'treequest', 'gemma', 'opendia', 'mcp']
        self.session_log = Path.home() / ".smart-ai-session.json"
        self.mcp_manager: Optional[MCPConfigurationManager] = None
        self.mcp_manager_initialized = False
        self.load_session_state()
    
    async def _initialize_mcp_manager(self):
        """Initialize MCP manager for tool discovery (lazy initialization)"""
        if self.mcp_manager_initialized:
            return
            
        try:
            self.mcp_manager = await get_mcp_manager()
            self.mcp_manager_initialized = True
            print(f"✅ MCP Manager initialized with {len(self.mcp_manager.tools)} tools")
        except Exception as e:
            print(f"⚠️  MCP Manager initialization failed: {e}")
            self.mcp_manager = None
            self.mcp_manager_initialized = True  # Don't retry on every call
    
    async def process_request_async(self, prompt: str, provider: str) -> Optional[str]:
        """
        Processes an AI request asynchronously, handling verbose responses in background
        """
        try:
            print(f"🔄 Processing with {provider}...")
            
            if provider == 'claude_code':
                return await self._execute_claude_code(prompt)
            elif provider == 'treequest':
                return await self._execute_treequest(prompt)
            elif provider == 'gemma':
                return await self._execute_gemma(prompt)
            elif provider == 'opendia':
                return await self._execute_opendia(prompt)
            elif provider == 'mcp':
                return await self._execute_mcp(prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
        except Exception as e:
            print(f"❌ Error processing request for provider {provider}: {e}")
            return None
    
    async def _execute_claude_code(self, prompt: str) -> str:
        """Execute Claude Code CLI"""
        try:
            cmd = ["/Users/Subho/.claude/local/claude", prompt]
            process = await asyncio.create_subprocess_exec(
                *cmd, 
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                raise Exception(f"Claude Code failed: {stderr.decode('utf-8')}")
                
        except Exception as e:
            raise Exception(f"Failed to execute Claude Code: {e}")
    
    async def _execute_treequest(self, prompt: str) -> str:
        """Execute TreeQuest"""
        try:
            # Import TreeQuest controller for execution
            import sys
            sys.path.append('/Users/Subho/CascadeProjects/enhanced-treequest')
            from enhanced_treequest_controller import EnhancedTreeQuestController, TaskRequest, TaskComplexity
            
            tq = EnhancedTreeQuestController()
            task_request = TaskRequest(prompt=prompt, complexity=TaskComplexity.MEDIUM)
            result = await tq.execute_with_fallback(task_request)
            
            return result.content if result and hasattr(result, 'content') else "No response"
            
        except Exception as e:
            raise Exception(f"Failed to execute TreeQuest: {e}")
    
    async def _execute_gemma(self, prompt: str) -> str:
        """Execute Gemma via Ollama with enhanced offline capabilities"""
        try:
            # Check if Ollama is running first
            if not await self._check_ollama_running():
                print("🔄 Starting Ollama service...")
                await self._start_ollama_service()
            
            # Enhanced Gemma execution with optimized parameters for better responses
            cmd = [
                "ollama", "run", "gemma2:2b",
                # Add system prompt for better context understanding
                f"You are a helpful AI assistant. Provide concise, accurate responses. User query: {prompt}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                # Enhanced response processing for better quality
                return self._enhance_gemma_response(response, prompt)
            else:
                error_msg = stderr.decode('utf-8')
                if "model not found" in error_msg.lower():
                    print("📥 Gemma model not found. Downloading...")
                    await self._download_gemma_model()
                    # Retry after download
                    return await self._execute_gemma(prompt)
                raise Exception(f"Gemma failed: {error_msg}")
                
        except Exception as e:
            raise Exception(f"Failed to execute Gemma: {e}")
    
    async def _check_ollama_running(self) -> bool:
        """Check if Ollama service is running"""
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _start_ollama_service(self):
        """Start Ollama service if not running"""
        try:
            # Start Ollama in background
            process = await asyncio.create_subprocess_exec(
                "ollama", "serve",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            # Give it time to start
            await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️  Could not start Ollama service: {e}")
    
    async def _download_gemma_model(self):
        """Download Gemma model if not available"""
        try:
            print("📥 Downloading Gemma 2B model (this may take a while)...")
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", "gemma2:2b",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            print("✅ Gemma model downloaded successfully")
        except Exception as e:
            print(f"❌ Failed to download Gemma model: {e}")
    
    def _enhance_gemma_response(self, response: str, prompt: str) -> str:
        """Enhance Gemma response quality and formatting"""
        if not response:
            return "No response from Gemma model."
        
        # Remove common Gemma artifacts and improve formatting
        enhanced = response.strip()
        
        # Remove repetitive patterns
        lines = enhanced.split('\n')
        unique_lines = []
        for line in lines:
            if line.strip() and line not in unique_lines:
                unique_lines.append(line)
        
        enhanced = '\n'.join(unique_lines)
        
        # Add context-aware improvements
        if any(word in prompt.lower() for word in ['what', 'how', 'why']):
            # For questions, ensure clear, direct answers
            if not enhanced.endswith(('.', '!', '?')):
                enhanced += '.'
        
        return enhanced
    
    async def _execute_opendia(self, prompt: str) -> str:
        """Execute OpenDia browser automation commands"""
        try:
            # Check if OpenDia server is running
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5555))
            sock.close()
            
            if result != 0:
                # Start OpenDia server if not running
                print("🌐 Starting OpenDia server...")
                process = await asyncio.create_subprocess_exec(
                    "npx", "opendia", 
                    cwd="/Users/Subho/opendia/opendia-mcp",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                # Give it time to start
                await asyncio.sleep(3)
            
            # Use OpenDia MCP tools for browser automation
            opendia_response = await self._call_opendia_mcp(prompt)
            return opendia_response
            
        except Exception as e:
            raise Exception(f"Failed to execute OpenDia: {e}")
    
    async def _call_opendia_mcp(self, prompt: str) -> str:
        """Call OpenDia MCP tools based on prompt analysis"""
        try:
            # Analyze prompt to determine appropriate OpenDia action
            prompt_lower = prompt.lower()
            
            if any(word in prompt_lower for word in ['post', 'tweet', 'linkedin', 'facebook', 'social']):
                return await self._handle_social_posting(prompt)
            elif any(word in prompt_lower for word in ['browse', 'navigate', 'visit', 'go to']):
                return await self._handle_navigation(prompt)
            elif any(word in prompt_lower for word in ['fill', 'form', 'submit', 'input']):
                return await self._handle_form_filling(prompt)
            elif any(word in prompt_lower for word in ['extract', 'read', 'analyze', 'content']):
                return await self._handle_content_extraction(prompt)
            elif any(word in prompt_lower for word in ['bookmark', 'save', 'organize']):
                return await self._handle_bookmarks(prompt)
            else:
                # Default to page analysis
                return await self._handle_page_analysis(prompt)
                
        except Exception as e:
            return f"OpenDia automation error: {e}"
    
    async def _handle_social_posting(self, prompt: str) -> str:
        """Handle social media posting via OpenDia"""
        # This would integrate with OpenDia's post_to_social tool
        return f"🌐 OpenDia: Social media posting feature ready for: {prompt[:100]}..."
    
    async def _handle_navigation(self, prompt: str) -> str:
        """Handle browser navigation via OpenDia"""
        # This would use OpenDia's page_navigate tool
        return f"🌐 OpenDia: Browser navigation ready for: {prompt[:100]}..."
    
    async def _handle_form_filling(self, prompt: str) -> str:
        """Handle form filling via OpenDia"""
        # This would use OpenDia's fill_form_assistant tool
        return f"🌐 OpenDia: Form filling assistant ready for: {prompt[:100]}..."
    
    async def _handle_content_extraction(self, prompt: str) -> str:
        """Handle content extraction via OpenDia"""
        # This would use OpenDia's page_extract_content tool
        return f"🌐 OpenDia: Content extraction ready for: {prompt[:100]}..."
    
    async def _handle_bookmarks(self, prompt: str) -> str:
        """Handle bookmark management via OpenDia"""
        # This would use OpenDia's bookmark tools
        return f"🌐 OpenDia: Bookmark management ready for: {prompt[:100]}..."
    
    async def _handle_page_analysis(self, prompt: str) -> str:
        """Handle page analysis via OpenDia"""
        # This would use OpenDia's page_analyze tool
        return f"🌐 OpenDia: Page analysis ready for: {prompt[:100]}..."
    
    async def _execute_mcp(self, prompt: str) -> str:
        """Execute MCP tool based on prompt analysis"""
        try:
            # Ensure MCP manager is initialized
            await self._initialize_mcp_manager()
            if not self.mcp_manager:
                return "❌ MCP tools not available"
            
            # Determine optimal MCP tool for the prompt
            optimal_tool = self.mcp_manager.get_optimal_tool_for_task(prompt)
            
            if not optimal_tool:
                return "🔧 No suitable MCP tool found for this request"
            
            # Execute the MCP tool
            return await self._execute_mcp_tool(optimal_tool, prompt)
            
        except Exception as e:
            return f"❌ MCP execution error: {e}"
    
    async def _execute_mcp_tool(self, tool_key: str, prompt: str) -> str:
        """Execute a specific MCP tool"""
        try:
            tool = self.mcp_manager.tools.get(tool_key)
            if not tool:
                return f"❌ Tool {tool_key} not found"
            
            # Handle different MCP tool categories
            if tool.category == "task_management":
                return await self._execute_taskmaster_tool(tool, prompt)
            elif tool.category == "browser_automation":
                return await self._execute_opendia_tool(tool, prompt)
            else:
                return f"🔧 {tool.name} tool ready - Category: {tool.category}"
                
        except Exception as e:
            return f"❌ Tool execution error: {e}"
    
    async def _execute_taskmaster_tool(self, tool, prompt: str) -> str:
        """Execute TaskMaster MCP tool"""
        try:
            # Map prompt to TaskMaster action
            prompt_lower = prompt.lower()
            
            if any(word in prompt_lower for word in ['list', 'show', 'get', 'tasks']):
                return await self._run_taskmaster_command(["get_tasks"])
            elif any(word in prompt_lower for word in ['create', 'add', 'new']):
                return await self._run_taskmaster_command(["add_task", "--prompt", prompt])
            elif any(word in prompt_lower for word in ['next', 'what']):
                return await self._run_taskmaster_command(["next_task"])
            elif any(word in prompt_lower for word in ['status', 'project']):
                return await self._run_taskmaster_command(["get_tasks", "--status", "in_progress"])
            else:
                return await self._run_taskmaster_command(["get_tasks"])
                
        except Exception as e:
            return f"❌ TaskMaster execution error: {e}"
    
    async def _run_taskmaster_command(self, args: List[str]) -> str:
        """Run TaskMaster command via MCP"""
        try:
            # Use the global TaskMaster MCP tools
            cmd = ["npx", "-y", "--package=task-master-ai", "task-master-ai"] + args
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/Users/Subho"  # Use home directory as project root
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result = stdout.decode('utf-8').strip()
                return f"✅ TaskMaster: {result}" if result else "✅ TaskMaster command executed"
            else:
                error = stderr.decode('utf-8').strip()
                return f"❌ TaskMaster error: {error}"
                
        except Exception as e:
            return f"❌ TaskMaster command failed: {e}"
    
    async def _execute_opendia_tool(self, tool, prompt: str) -> str:
        """Execute OpenDia MCP tool"""
        # For now, delegate to existing OpenDia handler
        return await self._execute_opendia(prompt)
    
    def get_clean_output(self, response: str) -> str:
        """
        Extracts and returns essential information from a verbose response
        """
        if not response:
            return "No response available."
        
        # Remove excessive whitespace and limit length for CLI display
        clean_response = ' '.join(response.split())
        
        # For very long responses, provide a summary
        if len(clean_response) > 500:
            lines = clean_response.split('\n')
            if len(lines) > 10:
                # Return first few lines and indicate more content
                summary = '\n'.join(lines[:8])
                return f"{summary}\n\n... (response continues, use --verbose for full output)"
            else:
                # Truncate at word boundary
                truncated = clean_response[:400]
                last_space = truncated.rfind(' ')
                if last_space > 300:
                    truncated = truncated[:last_space]
                return f"{truncated}... (use --verbose for full output)"
        
        return clean_response
    
    def manage_session_state(self):
        """
        Manages session tracking and token usage monitoring
        """
        current_time = time.time()
        
        # Update session data
        self.session_data.update({
            'last_access': current_time,
            'requests_count': self.session_data.get('requests_count', 0) + 1,
            'token_usage': self.token_usage,
            'session_duration': current_time - self.session_data.get('session_start', current_time)
        })
        
        # Save to file
        self.save_session_state()
        
        # Check for token limit warnings
        total_requests = self.session_data.get('requests_count', 0)
        if total_requests > 50:
            print("⚠️  High usage detected - consider using local Gemma model")
    
    def handle_provider_fallback(self, failed_provider: str = None, prompt: str = None) -> str:
        """
        Implements intelligent provider selection with fallback between providers
        """
        # Smart provider selection based on prompt content
        if prompt and not failed_provider:
            provider = self._select_optimal_provider(prompt)
            if provider and self._check_provider_availability(provider):
                print(f"✅ Using {provider} (optimal for task)")
                return provider
        
        # Default fallback order
        fallback_order = ['claude_code', 'treequest', 'mcp', 'opendia', 'gemma']
        
        if failed_provider:
            print(f"❌ {failed_provider} failed, falling back...")
            # Remove failed provider from current session
            fallback_order = [p for p in fallback_order if p != failed_provider]
        
        for provider in fallback_order:
            if self._check_provider_availability(provider):
                print(f"✅ Using {provider}")
                return provider
        
        print("❌ No providers available")
        return None
    
    def _select_optimal_provider(self, prompt: str) -> str:
        """Select the best provider based on prompt analysis and connectivity"""
        prompt_lower = prompt.lower()
        
        # Check internet connectivity first
        internet_available = self._check_internet_connectivity()
        
        if not internet_available:
            print("🔒 No internet connection detected - using offline-capable providers")
            # Force local providers when offline
            if any(keyword in prompt_lower for keyword in ['browse', 'navigate', 'website']):
                # Browser tasks need internet, fallback to local description
                return 'gemma'
            return 'gemma'  # Gemma works fully offline
        
        # File system operations -> MCP filesystem tools
        file_keywords = ['file', 'read', 'write', 'create', 'directory', 'folder', 'search files']
        if any(keyword in prompt_lower for keyword in file_keywords):
            return 'mcp'
        
        # Database operations -> MCP SQLite tools
        db_keywords = ['database', 'query', 'table', 'sql', 'data', 'insert', 'select']
        if any(keyword in prompt_lower for keyword in db_keywords):
            return 'mcp'
        
        # Git operations -> MCP Git tools
        git_keywords = ['git', 'commit', 'branch', 'repository', 'repo', 'version control', 'diff']
        if any(keyword in prompt_lower for keyword in git_keywords):
            return 'mcp'
        
        # Task management keywords -> MCP TaskMaster tools
        task_keywords = ['task', 'tasks', 'project', 'todo', 'track', 'manage', 'plan', 'status', 
                        'create task', 'add task', 'next task', 'show tasks', 'list tasks']
        if any(keyword in prompt_lower for keyword in task_keywords):
            return 'mcp'
        
        # Browser automation tasks -> OpenDia
        browser_keywords = ['browse', 'navigate', 'website', 'page', 'click', 'form', 'post', 'tweet', 
                          'social', 'bookmark', 'extract', 'content', 'scroll', 'tab', 'browser']
        if any(keyword in prompt_lower for keyword in browser_keywords):
            return 'opendia'
        
        # Complex coding/analysis tasks -> TreeQuest  
        complex_keywords = ['implement', 'analyze', 'debug', 'architecture', 'design', 'refactor', 'optimize']
        if any(keyword in prompt_lower for keyword in complex_keywords):
            return 'treequest'
        
        # Quick questions -> Gemma (local, fast)
        if len(prompt) < 50 or any(word in prompt_lower for word in ['what', 'how', 'why', 'quick']):
            return 'gemma'
        
        # Default to Claude Code for general tasks
        return 'claude_code'
    
    def _check_internet_connectivity(self) -> bool:
        """Check if internet connection is available"""
        try:
            import socket
            # Try to connect to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def _check_provider_availability(self, provider: str) -> bool:
        """Check if provider is available and properly configured"""
        try:
            if provider == 'claude_code':
                return Path("/Users/Subho/.claude/local/claude").exists()
            elif provider == 'treequest':
                return Path("/Users/Subho/CascadeProjects/enhanced-treequest").exists()
            elif provider == 'opendia':
                # Check if OpenDia MCP server directory exists
                return Path("/Users/Subho/opendia/opendia-mcp").exists()
            elif provider == 'mcp':
                # MCP tools are always potentially available (they'll initialize when needed)
                # Check if task-master-ai is configured
                return Path("/Users/Subho/.mcp.json").exists()
            elif provider == 'gemma':
                # Check if Ollama is running and Gemma model is available
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                return result.returncode == 0 and "gemma2:2b" in result.stdout
            return False
        except Exception:
            return False
    
    def load_session_state(self):
        """Load session state from disk"""
        try:
            if self.session_log.exists():
                with open(self.session_log, 'r') as f:
                    data = json.load(f)
                    self.session_data = data.get('session_data', {})
                    self.token_usage = data.get('token_usage', {})
        except Exception as e:
            print(f"Warning: Could not load session state: {e}")
            self.session_data = {'session_start': time.time()}
            self.token_usage = {}
    
    def save_session_state(self):
        """Save session state to disk"""
        try:
            with open(self.session_log, 'w') as f:
                json.dump({
                    'session_data': self.session_data,
                    'token_usage': self.token_usage
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session state: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def test_backend():
        backend = SmartAIBackend()
        backend.manage_session_state()
        
        # Test provider fallback
        provider = backend.handle_provider_fallback()
        if provider:
            print(f"Selected provider: {provider}")
            
            # Test async processing
            response = await backend.process_request_async(
                "What is the capital of France?", 
                provider
            )
            
            if response:
                clean_output = backend.get_clean_output(response)
                print(f"Clean Output: {clean_output}")
            else:
                print("No response received")
        else:
            print("No providers available for testing")
    
    # Run test
    asyncio.run(test_backend())
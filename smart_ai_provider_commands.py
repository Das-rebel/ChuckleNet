#!/usr/bin/env python3
"""
Smart AI Provider Control Commands Implementation
Comprehensive provider switching, management, and status monitoring for smart-ai CLI
"""

import asyncio
import json
import time
import socket
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import smart-ai components
from smart_ai_slash_commands import (
    BaseCommandHandler, CommandDefinition, CommandParameter, CommandCategory,
    ParsedCommand, CommandExecutionContext, command_error_handler
)
from smart_ai_notifications import NotificationManager, NotificationType
from smart_ai_backend import SmartAIBackend
from smart_ai_mcp_manager import get_mcp_manager, MCPConfigurationManager


@dataclass
class ProviderHealthMetrics:
    """Health metrics for a provider"""
    name: str
    available: bool
    response_time: float
    last_success: Optional[datetime]
    success_rate: float
    error_count: int
    capabilities: List[str]
    configuration_status: str
    offline_capable: bool
    estimated_cost_per_request: float


@dataclass 
class ProviderRecommendation:
    """Provider recommendation based on query analysis"""
    provider: str
    confidence: float
    reasoning: List[str]
    fallback_options: List[str]


class ProviderManager:
    """Advanced provider management with health monitoring and smart recommendations"""
    
    def __init__(self):
        self.providers = ['claude_code', 'gemma', 'treequest', 'mcp', 'opendia']
        self.health_cache = {}
        self.performance_history = {}
        self.recommendation_cache = {}
        self.cache_expiry = 60  # seconds
        
    async def get_provider_health(self, provider_name: str, backend: Optional[SmartAIBackend] = None) -> ProviderHealthMetrics:
        """Get comprehensive health metrics for a provider"""
        current_time = time.time()
        
        # Check cache
        if (provider_name in self.health_cache and 
            current_time - self.health_cache[provider_name].get('timestamp', 0) < self.cache_expiry):
            return self.health_cache[provider_name]['metrics']
        
        # Collect fresh metrics
        metrics = await self._collect_provider_metrics(provider_name, backend)
        
        # Cache the results
        self.health_cache[provider_name] = {
            'timestamp': current_time,
            'metrics': metrics
        }
        
        return metrics
    
    async def _collect_provider_metrics(self, provider_name: str, backend: Optional[SmartAIBackend]) -> ProviderHealthMetrics:
        """Collect real-time metrics for a provider"""
        start_time = time.time()
        
        # Default metrics
        metrics = ProviderHealthMetrics(
            name=provider_name,
            available=False,
            response_time=0.0,
            last_success=None,
            success_rate=0.0,
            error_count=0,
            capabilities=[],
            configuration_status="unknown",
            offline_capable=False,
            estimated_cost_per_request=0.0
        )
        
        try:
            # Check basic availability
            if backend:
                metrics.available = backend._check_provider_availability(provider_name)
                metrics.response_time = time.time() - start_time
            
            # Provider-specific health checks and capabilities
            if provider_name == 'claude_code':
                await self._check_claude_health(metrics)
            elif provider_name == 'gemma':
                await self._check_gemma_health(metrics)
            elif provider_name == 'treequest':
                await self._check_treequest_health(metrics)
            elif provider_name == 'mcp':
                await self._check_mcp_health(metrics)
            elif provider_name == 'opendia':
                await self._check_opendia_health(metrics)
            
            # Load historical performance data
            self._load_performance_history(metrics)
            
        except Exception as e:
            metrics.configuration_status = f"error: {str(e)}"
        
        return metrics
    
    async def _check_claude_health(self, metrics: ProviderHealthMetrics):
        """Check Claude Code specific health"""
        claude_path = Path("/Users/Subho/.claude/local/claude")
        
        if claude_path.exists():
            metrics.configuration_status = "configured"
            metrics.capabilities = [
                "General AI assistance",
                "Code analysis", 
                "File operations",
                "Project management",
                "Advanced reasoning"
            ]
            metrics.offline_capable = False
            metrics.estimated_cost_per_request = 0.01  # Estimate
            
            # Test responsiveness
            try:
                process = await asyncio.create_subprocess_exec(
                    str(claude_path), "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.communicate(), timeout=5)
                
                if process.returncode == 0:
                    metrics.available = True
                    metrics.configuration_status = "ready"
                    metrics.last_success = datetime.now()
                
            except (asyncio.TimeoutError, FileNotFoundError):
                metrics.configuration_status = "timeout_or_missing"
        else:
            metrics.configuration_status = "not_installed"
    
    async def _check_gemma_health(self, metrics: ProviderHealthMetrics):
        """Check Gemma/Ollama specific health"""
        try:
            # Check if Ollama is running and responsive
            process = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                output = stdout.decode('utf-8')
                if "gemma2:2b" in output:
                    metrics.available = True
                    metrics.configuration_status = "ready"
                    metrics.last_success = datetime.now()
                else:
                    metrics.configuration_status = "model_missing"
                
                metrics.capabilities = [
                    "Local AI assistance",
                    "Offline capability", 
                    "Fast responses",
                    "Privacy focused",
                    "No API costs"
                ]
                metrics.offline_capable = True
                metrics.estimated_cost_per_request = 0.0
            else:
                metrics.configuration_status = "ollama_error"
                
        except (asyncio.TimeoutError, FileNotFoundError):
            metrics.configuration_status = "ollama_not_running"
    
    async def _check_treequest_health(self, metrics: ProviderHealthMetrics):
        """Check TreeQuest specific health"""
        treequest_path = Path("/Users/Subho/CascadeProjects/enhanced-treequest")
        
        if treequest_path.exists():
            metrics.configuration_status = "configured"
            metrics.capabilities = [
                "Multi-provider fallback",
                "Complex task handling",
                "Enhanced reasoning",
                "Provider orchestration",
                "Error recovery"
            ]
            metrics.offline_capable = False
            metrics.estimated_cost_per_request = 0.005
            
            # Check if dependencies are available
            controller_file = treequest_path / "enhanced_treequest_controller.py"
            if controller_file.exists():
                metrics.available = True
                metrics.configuration_status = "ready"
                metrics.last_success = datetime.now()
            else:
                metrics.configuration_status = "controller_missing"
        else:
            metrics.configuration_status = "not_installed"
    
    async def _check_mcp_health(self, metrics: ProviderHealthMetrics):
        """Check MCP tools health"""
        try:
            mcp_config = Path.home() / ".mcp.json"
            
            if mcp_config.exists():
                # Initialize MCP manager to check tools
                mcp_manager = await get_mcp_manager()
                
                if mcp_manager and mcp_manager.tools:
                    metrics.available = True
                    metrics.configuration_status = "ready"
                    metrics.last_success = datetime.now()
                    
                    # Categorize capabilities
                    capabilities = set()
                    for tool in mcp_manager.tools.values():
                        if tool.category == "task_management":
                            capabilities.add("Task management")
                        elif tool.category == "file_system":
                            capabilities.add("File operations")
                        elif tool.category == "database":
                            capabilities.add("Database access")
                        elif tool.category == "development":
                            capabilities.add("Git integration")
                        elif tool.category == "browser_automation":
                            capabilities.add("Browser automation")
                    
                    metrics.capabilities = list(capabilities)
                    metrics.offline_capable = any(tool.offline_capable for tool in mcp_manager.tools.values())
                    metrics.estimated_cost_per_request = 0.002
                else:
                    metrics.configuration_status = "no_tools_available"
            else:
                metrics.configuration_status = "not_configured"
                
        except Exception as e:
            metrics.configuration_status = f"initialization_error: {str(e)}"
    
    async def _check_opendia_health(self, metrics: ProviderHealthMetrics):
        """Check OpenDia browser automation health"""
        opendia_path = Path("/Users/Subho/opendia/opendia-mcp")
        
        if opendia_path.exists():
            metrics.configuration_status = "configured"
            metrics.capabilities = [
                "Browser automation",
                "Web scraping",
                "Form filling",
                "Social media posting",
                "Content extraction",
                "Bookmark management"
            ]
            metrics.offline_capable = False
            metrics.estimated_cost_per_request = 0.0
            
            # Check if server can start
            try:
                # Test if port 5555 is available (OpenDia default)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5555))
                sock.close()
                
                if result == 0:
                    metrics.available = True
                    metrics.configuration_status = "server_running"
                    metrics.last_success = datetime.now()
                else:
                    metrics.configuration_status = "server_stopped"
                    
            except Exception:
                metrics.configuration_status = "connection_error"
        else:
            metrics.configuration_status = "not_installed"
    
    def _load_performance_history(self, metrics: ProviderHealthMetrics):
        """Load historical performance data"""
        history = self.performance_history.get(metrics.name, {})
        
        metrics.success_rate = history.get('success_rate', 0.0)
        metrics.error_count = history.get('error_count', 0)
        
        last_success_str = history.get('last_success')
        if last_success_str:
            try:
                metrics.last_success = datetime.fromisoformat(last_success_str)
            except ValueError:
                pass
    
    def update_performance_history(self, provider_name: str, success: bool, response_time: float):
        """Update performance history for a provider"""
        if provider_name not in self.performance_history:
            self.performance_history[provider_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'error_count': 0,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'last_success': None
            }
        
        history = self.performance_history[provider_name]
        history['total_requests'] += 1
        
        if success:
            history['successful_requests'] += 1
            history['last_success'] = datetime.now().isoformat()
        else:
            history['error_count'] += 1
        
        history['success_rate'] = history['successful_requests'] / history['total_requests']
        
        # Update average response time (simple moving average)
        if 'avg_response_time' not in history:
            history['avg_response_time'] = response_time
        else:
            history['avg_response_time'] = (history['avg_response_time'] * 0.8) + (response_time * 0.2)
    
    async def recommend_provider(self, query: str, context: CommandExecutionContext) -> ProviderRecommendation:
        """Analyze query and recommend optimal provider"""
        query_lower = query.lower()
        
        # Check for cached recommendation
        cache_key = f"{hash(query_lower)}_{context.current_provider}"
        if cache_key in self.recommendation_cache:
            cached = self.recommendation_cache[cache_key]
            if time.time() - cached['timestamp'] < 300:  # 5 minute cache
                return cached['recommendation']
        
        # Analyze query for provider selection
        recommendation = await self._analyze_query_for_provider(query_lower, context)
        
        # Cache the recommendation
        self.recommendation_cache[cache_key] = {
            'timestamp': time.time(),
            'recommendation': recommendation
        }
        
        return recommendation
    
    async def _analyze_query_for_provider(self, query_lower: str, context: CommandExecutionContext) -> ProviderRecommendation:
        """Analyze query content to recommend optimal provider"""
        providers = []
        
        # Check network connectivity
        network_available = self._check_network_connectivity()
        
        # Task management keywords -> MCP TaskMaster
        task_keywords = ['task', 'project', 'todo', 'track', 'manage', 'plan', 'status', 'create task', 'list tasks']
        if any(keyword in query_lower for keyword in task_keywords):
            if network_available:
                providers.append(('mcp', 0.9, ['Task management capabilities', 'Project tracking features']))
            
        # File operations -> MCP or Claude
        file_keywords = ['file', 'read', 'write', 'create', 'directory', 'folder', 'search files']
        if any(keyword in query_lower for keyword in file_keywords):
            if network_available:
                providers.append(('mcp', 0.85, ['Direct file system access', 'MCP filesystem tools']))
                providers.append(('claude_code', 0.75, ['File analysis capabilities', 'Code understanding']))
        
        # Browser automation -> OpenDia
        browser_keywords = ['browse', 'navigate', 'website', 'page', 'click', 'form', 'post', 'tweet', 'social', 'bookmark']
        if any(keyword in query_lower for keyword in browser_keywords):
            if network_available:
                providers.append(('opendia', 0.95, ['Browser automation specialist', 'Web interaction tools']))
        
        # Complex analysis -> TreeQuest or Claude
        complex_keywords = ['implement', 'analyze', 'debug', 'architecture', 'design', 'refactor', 'optimize']
        if any(keyword in query_lower for keyword in complex_keywords):
            if network_available:
                providers.append(('treequest', 0.85, ['Multi-provider orchestration', 'Complex reasoning']))
                providers.append(('claude_code', 0.80, ['Advanced AI capabilities', 'Code analysis']))
        
        # Quick questions -> Gemma (local, fast)
        quick_keywords = ['what', 'how', 'why', 'quick', 'simple']
        if any(keyword in query_lower for keyword in quick_keywords) or len(query_lower) < 50:
            providers.append(('gemma', 0.8, ['Fast local responses', 'No API costs', 'Privacy focused']))
        
        # Default recommendations based on connectivity
        if not providers:
            if network_available:
                providers.append(('claude_code', 0.7, ['General AI capabilities', 'Reliable performance']))
                providers.append(('treequest', 0.6, ['Fallback orchestration', 'Multi-provider support']))
            else:
                providers.append(('gemma', 0.9, ['Offline capability', 'No internet required']))
        
        # Add offline fallback if no network
        if not network_available:
            providers = [p for p in providers if p[0] == 'gemma']
            if not providers:
                providers.append(('gemma', 0.8, ['Only offline-capable provider']))
        
        # Get the best recommendation
        if providers:
            providers.sort(key=lambda x: x[1], reverse=True)
            best_provider, confidence, reasoning = providers[0]
            fallback_options = [p[0] for p in providers[1:]]
        else:
            best_provider = 'claude_code'
            confidence = 0.5
            reasoning = ['Default provider']
            fallback_options = ['treequest', 'gemma']
        
        return ProviderRecommendation(
            provider=best_provider,
            confidence=confidence,
            reasoning=reasoning,
            fallback_options=fallback_options
        )
    
    def _check_network_connectivity(self) -> bool:
        """Check if network connection is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False


class ClaudeProviderCommandHandler(BaseCommandHandler):
    """Switch to Claude Code provider with status and execution"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        prompt = ' '.join(parsed_cmd.args) if parsed_cmd.args else None
        status_only = parsed_cmd.kwargs.get('status', False)
        force = parsed_cmd.kwargs.get('force', False)
        
        # Get provider health
        health = await self.provider_manager.get_provider_health('claude_code', context.backend)
        
        if status_only:
            return self._format_provider_status(health)
        
        # Check availability
        if not health.available and not force:
            return (f"❌ Claude Code not available: {health.configuration_status}\n"
                   f"💡 Install Claude CLI or use '/claude --force' to attempt anyway")
        
        # Switch provider
        context.smart_ai.current_provider = 'claude_code'
        
        result_lines = [
            "🤖 Switched to Claude Code",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s"
        ]
        
        if health.capabilities:
            result_lines.append(f"🔧 Capabilities: {', '.join(health.capabilities[:3])}")
        
        # Execute prompt if provided
        if prompt:
            result_lines.append("\n🔄 Executing with Claude Code...")
            
            try:
                if context.backend:
                    response = await context.backend.process_request_async(prompt, 'claude_code')
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Response:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history('claude_code', True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response received")
                        self.provider_manager.update_performance_history('claude_code', False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Execution error: {e}")
                self.provider_manager.update_performance_history('claude_code', False, health.response_time)
        
        return '\n'.join(result_lines)
    
    def _format_provider_status(self, health: ProviderHealthMetrics) -> str:
        """Format provider health status for display"""
        status_lines = [
            f"🤖 Claude Code Provider Status",
            "=" * 35,
            f"Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"Configuration: {health.configuration_status}",
            f"Response Time: {health.response_time:.2f}s",
            f"Success Rate: {health.success_rate:.1%}",
            f"Cost/Request: ${health.estimated_cost_per_request:.4f}",
            f"Offline Capable: {'Yes' if health.offline_capable else 'No'}"
        ]
        
        if health.capabilities:
            status_lines.append(f"\n🔧 Capabilities:")
            for capability in health.capabilities:
                status_lines.append(f"  • {capability}")
        
        if health.last_success:
            status_lines.append(f"\n⏰ Last Success: {health.last_success.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(status_lines)


class GemmaProviderCommandHandler(BaseCommandHandler):
    """Switch to Gemma (Ollama) provider with model management"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        prompt = ' '.join(parsed_cmd.args) if parsed_cmd.args else None
        status_only = parsed_cmd.kwargs.get('status', False)
        install = parsed_cmd.kwargs.get('install', False)
        models = parsed_cmd.kwargs.get('models', False)
        force = parsed_cmd.kwargs.get('force', False)
        
        # Get provider health
        health = await self.provider_manager.get_provider_health('gemma', context.backend)
        
        if status_only:
            return self._format_gemma_status(health)
        
        if models:
            return await self._list_ollama_models()
        
        if install:
            return await self._install_gemma_model()
        
        # Check availability
        if not health.available and not force:
            suggestion = ""
            if "ollama_not_running" in health.configuration_status:
                suggestion = "\n💡 Try: 'ollama serve' to start Ollama service"
            elif "model_missing" in health.configuration_status:
                suggestion = "\n💡 Try: '/gemma --install' to download Gemma model"
            
            return (f"❌ Gemma not available: {health.configuration_status}{suggestion}\n"
                   f"Use '/gemma --force' to attempt anyway")
        
        # Switch provider
        context.smart_ai.current_provider = 'gemma'
        
        result_lines = [
            "🧠 Switched to Gemma (Local AI)",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s",
            f"💰 Cost: Free (Local)",
            f"🔒 Privacy: Fully offline"
        ]
        
        # Execute prompt if provided
        if prompt:
            result_lines.append("\n🔄 Processing with Gemma...")
            
            try:
                if context.backend:
                    response = await context.backend.process_request_async(prompt, 'gemma')
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Response:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history('gemma', True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response received")
                        self.provider_manager.update_performance_history('gemma', False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Execution error: {e}")
                self.provider_manager.update_performance_history('gemma', False, health.response_time)
        
        return '\n'.join(result_lines)
    
    async def _list_ollama_models(self) -> str:
        """List available Ollama models"""
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8')
                return f"🧠 Available Ollama Models:\n\n{output}"
            else:
                return f"❌ Error listing models: {stderr.decode('utf-8')}"
        except FileNotFoundError:
            return "❌ Ollama not installed. Please install Ollama first."
        except Exception as e:
            return f"❌ Error: {e}"
    
    async def _install_gemma_model(self) -> str:
        """Install Gemma model via Ollama"""
        try:
            result_lines = ["🧠 Installing Gemma 2B model...", "This may take several minutes..."]
            
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", "gemma2:2b",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result_lines.append("✅ Gemma model installed successfully!")
                result_lines.append("💡 You can now use '/gemma <prompt>' for local AI")
            else:
                result_lines.append(f"❌ Installation failed: {stderr.decode('utf-8')}")
            
            return '\n'.join(result_lines)
        except FileNotFoundError:
            return "❌ Ollama not installed. Please install Ollama first."
        except Exception as e:
            return f"❌ Installation error: {e}"
    
    def _format_gemma_status(self, health: ProviderHealthMetrics) -> str:
        """Format Gemma provider status"""
        status_lines = [
            f"🧠 Gemma (Ollama) Provider Status",
            "=" * 35,
            f"Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"Configuration: {health.configuration_status}",
            f"Response Time: {health.response_time:.2f}s",
            f"Success Rate: {health.success_rate:.1%}",
            f"Cost/Request: Free (Local)",
            f"Offline Capable: {'Yes' if health.offline_capable else 'No'}"
        ]
        
        if health.capabilities:
            status_lines.append(f"\n🔧 Capabilities:")
            for capability in health.capabilities:
                status_lines.append(f"  • {capability}")
        
        return '\n'.join(status_lines)


class TreeQuestProviderCommandHandler(BaseCommandHandler):
    """Switch to TreeQuest provider with capability info"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        prompt = ' '.join(parsed_cmd.args) if parsed_cmd.args else None
        status_only = parsed_cmd.kwargs.get('status', False)
        complexity = parsed_cmd.kwargs.get('complexity', 'medium')
        force = parsed_cmd.kwargs.get('force', False)
        
        # Get provider health
        health = await self.provider_manager.get_provider_health('treequest', context.backend)
        
        if status_only:
            return self._format_treequest_status(health)
        
        # Check availability
        if not health.available and not force:
            return (f"❌ TreeQuest not available: {health.configuration_status}\n"
                   f"💡 Check installation in /Users/Subho/CascadeProjects/enhanced-treequest\n"
                   f"Use '/treequest --force' to attempt anyway")
        
        # Switch provider
        context.smart_ai.current_provider = 'treequest'
        
        result_lines = [
            "🌳 Switched to Enhanced TreeQuest",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s",
            f"🔄 Complexity: {complexity.title()}",
            f"🛡️ Fallback: Multi-provider orchestration"
        ]
        
        if health.capabilities:
            result_lines.append(f"🔧 Capabilities: {', '.join(health.capabilities[:3])}")
        
        # Execute prompt if provided
        if prompt:
            result_lines.append("\n🔄 Processing with TreeQuest...")
            
            try:
                if context.backend:
                    response = await context.backend.process_request_async(prompt, 'treequest')
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Response:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history('treequest', True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response received")
                        self.provider_manager.update_performance_history('treequest', False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Execution error: {e}")
                self.provider_manager.update_performance_history('treequest', False, health.response_time)
        
        return '\n'.join(result_lines)
    
    def _format_treequest_status(self, health: ProviderHealthMetrics) -> str:
        """Format TreeQuest provider status"""
        status_lines = [
            f"🌳 TreeQuest Provider Status",
            "=" * 35,
            f"Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"Configuration: {health.configuration_status}",
            f"Response Time: {health.response_time:.2f}s",
            f"Success Rate: {health.success_rate:.1%}",
            f"Cost/Request: ${health.estimated_cost_per_request:.4f}",
            f"Offline Capable: {'Yes' if health.offline_capable else 'No'}"
        ]
        
        if health.capabilities:
            status_lines.append(f"\n🔧 Capabilities:")
            for capability in health.capabilities:
                status_lines.append(f"  • {capability}")
        
        return '\n'.join(status_lines)


class MCPProviderCommandHandler(BaseCommandHandler):
    """Switch to MCP provider with tool discovery"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        tool_name = parsed_cmd.args[0] if parsed_cmd.args else None
        list_tools = parsed_cmd.kwargs.get('list', False)
        category = parsed_cmd.kwargs.get('category')
        status_only = parsed_cmd.kwargs.get('status', False)
        discover = parsed_cmd.kwargs.get('discover', False)
        
        # Get provider health
        health = await self.provider_manager.get_provider_health('mcp', context.backend)
        
        if status_only:
            return self._format_mcp_status(health)
        
        if discover:
            return await self._discover_mcp_tools()
        
        if list_tools:
            return await self._list_mcp_tools(category)
        
        # Switch to MCP provider
        context.smart_ai.current_provider = 'mcp'
        
        result_lines = [
            "🔧 Switched to MCP Tools",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s"
        ]
        
        if health.available:
            try:
                mcp_manager = await get_mcp_manager()
                if mcp_manager:
                    total_tools = len(mcp_manager.tools)
                    categories = len(mcp_manager.tool_categories)
                    result_lines.append(f"🔧 Tools Available: {total_tools} across {categories} categories")
                    
                    # Show popular tools
                    popular_tools = ['taskmaster_get_tasks', 'filesystem_read_file', 'git_git_status', 'opendia_page_analyze']
                    available_popular = [tool for tool in popular_tools if tool in mcp_manager.tools]
                    if available_popular:
                        result_lines.append(f"⭐ Popular: {', '.join(available_popular[:3])}")
                        
            except Exception as e:
                result_lines.append(f"⚠️ Tool discovery error: {e}")
        
        # Execute specific tool if provided
        if tool_name and health.available:
            result_lines.append(f"\n🔄 Executing MCP tool: {tool_name}")
            
            try:
                if context.backend:
                    prompt = f"Use MCP tool {tool_name}"
                    response = await context.backend.process_request_async(prompt, 'mcp')
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Result:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history('mcp', True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response from MCP tool")
                        self.provider_manager.update_performance_history('mcp', False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Tool execution error: {e}")
                self.provider_manager.update_performance_history('mcp', False, health.response_time)
        
        return '\n'.join(result_lines)
    
    async def _discover_mcp_tools(self) -> str:
        """Discover and refresh MCP tools"""
        try:
            result_lines = ["🔍 Discovering MCP tools...", ""]
            
            # Re-initialize MCP manager for fresh discovery
            mcp_manager = await get_mcp_manager()
            await mcp_manager.initialize()
            
            if mcp_manager.tools:
                result_lines.append(f"✅ Discovered {len(mcp_manager.tools)} MCP tools")
                result_lines.append("\n📊 By Category:")
                
                for category, tools in mcp_manager.tool_categories.items():
                    if tools:
                        result_lines.append(f"  {category.title()}: {len(tools)} tools")
                
                result_lines.append("\n🏥 Server Health:")
                server_status = mcp_manager.get_all_servers_status()
                for server_name, status in server_status.items():
                    status_emoji = "✅" if status.get('status') == 'running' else "❌"
                    result_lines.append(f"  {server_name}: {status_emoji} {status.get('status', 'unknown')}")
            else:
                result_lines.append("❌ No MCP tools discovered")
                result_lines.append("💡 Check ~/.mcp.json configuration")
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            return f"❌ Discovery error: {e}"
    
    async def _list_mcp_tools(self, category: Optional[str] = None) -> str:
        """List available MCP tools by category"""
        try:
            mcp_manager = await get_mcp_manager()
            if not mcp_manager or not mcp_manager.tools:
                return "❌ No MCP tools available\n💡 Run '/mcp --discover' to initialize"
            
            result_lines = ["🔧 Available MCP Tools", "=" * 25, ""]
            
            if category:
                tools = mcp_manager.get_available_tools(category)
                if tools:
                    result_lines.append(f"📋 {category.title()} Tools:")
                    for tool_key in tools:
                        tool = mcp_manager.tools[tool_key]
                        offline_indicator = "🔒" if tool.offline_capable else "🌐"
                        result_lines.append(f"  {offline_indicator} {tool.name} - {tool.description}")
                else:
                    result_lines.append(f"❌ No tools found in category: {category}")
            else:
                # List all categories
                for cat_name, tools in mcp_manager.tool_categories.items():
                    if tools:
                        result_lines.append(f"📋 {cat_name.title()} ({len(tools)} tools):")
                        for tool_key in tools[:5]:  # Show first 5 tools per category
                            tool = mcp_manager.tools[tool_key]
                            offline_indicator = "🔒" if tool.offline_capable else "🌐"
                            result_lines.append(f"  {offline_indicator} {tool.name}")
                        if len(tools) > 5:
                            result_lines.append(f"    ... and {len(tools) - 5} more")
                        result_lines.append("")
            
            result_lines.extend([
                "💡 Usage Tips:",
                "  /mcp <tool_name>           # Execute tool",
                "  /mcp --list --category=<cat>  # List by category", 
                "  /mcp__<server>__<tool>     # Direct tool access",
                "",
                "🔒 = Offline capable  🌐 = Requires internet"
            ])
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            return f"❌ Error listing tools: {e}"
    
    def _format_mcp_status(self, health: ProviderHealthMetrics) -> str:
        """Format MCP provider status"""
        status_lines = [
            f"🔧 MCP Tools Provider Status",
            "=" * 35,
            f"Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"Configuration: {health.configuration_status}",
            f"Response Time: {health.response_time:.2f}s",
            f"Success Rate: {health.success_rate:.1%}",
            f"Cost/Request: ${health.estimated_cost_per_request:.4f}",
            f"Offline Capable: {'Yes' if health.offline_capable else 'No'}"
        ]
        
        if health.capabilities:
            status_lines.append(f"\n🔧 Capabilities:")
            for capability in health.capabilities:
                status_lines.append(f"  • {capability}")
        
        return '\n'.join(status_lines)


class OpenDiaProviderCommandHandler(BaseCommandHandler):
    """Switch to OpenDia browser automation provider"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else None
        url = parsed_cmd.kwargs.get('url')
        status_only = parsed_cmd.kwargs.get('status', False)
        start_server = parsed_cmd.kwargs.get('start', False)
        force = parsed_cmd.kwargs.get('force', False)
        
        # Get provider health
        health = await self.provider_manager.get_provider_health('opendia', context.backend)
        
        if status_only:
            return self._format_opendia_status(health)
        
        if start_server:
            return await self._start_opendia_server()
        
        # Check availability
        if not health.available and not force:
            suggestion = ""
            if "server_stopped" in health.configuration_status:
                suggestion = "\n💡 Try: '/opendia --start' to start OpenDia server"
            elif "not_installed" in health.configuration_status:
                suggestion = "\n💡 Install OpenDia MCP server in /Users/Subho/opendia/opendia-mcp"
            
            return (f"❌ OpenDia not available: {health.configuration_status}{suggestion}\n"
                   f"Use '/opendia --force' to attempt anyway")
        
        # Switch provider
        context.smart_ai.current_provider = 'opendia'
        
        result_lines = [
            "🌐 Switched to OpenDia Browser Automation",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s",
            f"🔧 Server: Port 5555"
        ]
        
        if health.capabilities:
            result_lines.append(f"🛠️ Capabilities: {', '.join(health.capabilities[:3])}")
        
        # Execute browser action if provided
        if action and health.available:
            result_lines.append(f"\n🔄 Executing browser action: {action}")
            
            try:
                if context.backend:
                    prompt = f"Browser action: {action}"
                    if url:
                        prompt += f" on {url}"
                    
                    response = await context.backend.process_request_async(prompt, 'opendia')
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Result:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history('opendia', True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response from OpenDia")
                        self.provider_manager.update_performance_history('opendia', False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Browser action error: {e}")
                self.provider_manager.update_performance_history('opendia', False, health.response_time)
        
        return '\n'.join(result_lines)
    
    async def _start_opendia_server(self) -> str:
        """Start OpenDia MCP server"""
        try:
            opendia_dir = Path("/Users/Subho/opendia/opendia-mcp")
            
            if not opendia_dir.exists():
                return "❌ OpenDia not found. Please install OpenDia MCP server first."
            
            result_lines = ["🌐 Starting OpenDia server...", ""]
            
            # Start the server process
            process = await asyncio.create_subprocess_exec(
                "npx", "opendia",
                cwd=str(opendia_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Give it time to start
            await asyncio.sleep(3)
            
            # Check if server is responding
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5555))
                sock.close()
                
                if result == 0:
                    result_lines.append("✅ OpenDia server started successfully!")
                    result_lines.append("🌐 Server running on localhost:5555")
                    result_lines.append("💡 You can now use browser automation commands")
                else:
                    result_lines.append("⚠️ Server may still be starting...")
                    result_lines.append("💡 Check again in a few seconds")
                
            except Exception:
                result_lines.append("⚠️ Could not verify server status")
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            return f"❌ Error starting OpenDia server: {e}"
    
    def _format_opendia_status(self, health: ProviderHealthMetrics) -> str:
        """Format OpenDia provider status"""
        status_lines = [
            f"🌐 OpenDia Browser Provider Status",
            "=" * 35,
            f"Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"Configuration: {health.configuration_status}",
            f"Response Time: {health.response_time:.2f}s",
            f"Success Rate: {health.success_rate:.1%}",
            f"Cost/Request: Free (Local automation)",
            f"Offline Capable: {'Yes' if health.offline_capable else 'No'}"
        ]
        
        if health.capabilities:
            status_lines.append(f"\n🔧 Capabilities:")
            for capability in health.capabilities:
                status_lines.append(f"  • {capability}")
        
        return '\n'.join(status_lines)


class GenericProviderCommandHandler(BaseCommandHandler):
    """Generic provider switching command"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        provider_name = parsed_cmd.args[0] if parsed_cmd.args else None
        prompt = ' '.join(parsed_cmd.args[1:]) if len(parsed_cmd.args) > 1 else None
        force = parsed_cmd.kwargs.get('force', False)
        recommend = parsed_cmd.kwargs.get('recommend', False)
        
        if not provider_name:
            return ("❌ Provider name required\n"
                   "💡 Usage: /provider <name> [prompt]\n"
                   "Available: claude_code, gemma, treequest, mcp, opendia")
        
        if recommend and prompt:
            recommendation = await self.provider_manager.recommend_provider(prompt, context)
            return self._format_recommendation(recommendation)
        
        # Validate provider name
        if provider_name not in self.provider_manager.providers:
            return (f"❌ Unknown provider: {provider_name}\n"
                   f"Available: {', '.join(self.provider_manager.providers)}")
        
        # Get provider health
        health = await self.provider_manager.get_provider_health(provider_name, context.backend)
        
        # Check availability
        if not health.available and not force:
            return (f"❌ Provider {provider_name} not available: {health.configuration_status}\n"
                   f"Use '/provider {provider_name} --force' to attempt anyway")
        
        # Switch provider
        old_provider = context.smart_ai.current_provider
        context.smart_ai.current_provider = provider_name
        
        result_lines = [
            f"🔄 Switched from {old_provider} to {provider_name}",
            f"📊 Status: {health.configuration_status}",
            f"⚡ Response Time: {health.response_time:.2f}s"
        ]
        
        # Execute prompt if provided
        if prompt:
            result_lines.append(f"\n🔄 Executing with {provider_name}...")
            
            try:
                if context.backend:
                    response = await context.backend.process_request_async(prompt, provider_name)
                    if response:
                        clean_response = context.backend.get_clean_output(response)
                        result_lines.append(f"\n📝 Response:\n{clean_response}")
                        
                        # Update performance tracking
                        self.provider_manager.update_performance_history(provider_name, True, health.response_time)
                    else:
                        result_lines.append("\n❌ No response received")
                        self.provider_manager.update_performance_history(provider_name, False, health.response_time)
                else:
                    result_lines.append("\n❌ Backend not available")
            except Exception as e:
                result_lines.append(f"\n❌ Execution error: {e}")
                self.provider_manager.update_performance_history(provider_name, False, health.response_time)
        
        return '\n'.join(result_lines)
    
    def _format_recommendation(self, recommendation: ProviderRecommendation) -> str:
        """Format provider recommendation"""
        lines = [
            "🎯 Provider Recommendation",
            "=" * 30,
            f"Recommended: {recommendation.provider}",
            f"Confidence: {recommendation.confidence:.1%}",
            "",
            "🧠 Reasoning:"
        ]
        
        for reason in recommendation.reasoning:
            lines.append(f"  • {reason}")
        
        if recommendation.fallback_options:
            lines.append(f"\n🔄 Fallback Options: {', '.join(recommendation.fallback_options)}")
        
        return '\n'.join(lines)


class ProvidersListCommandHandler(BaseCommandHandler):
    """List all available providers with status"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        detailed = parsed_cmd.kwargs.get('detailed', False)
        status_only = parsed_cmd.kwargs.get('status', False)
        performance = parsed_cmd.kwargs.get('performance', False)
        
        result_lines = [
            "🤖 Smart AI Provider Status Overview",
            "=" * 45,
            ""
        ]
        
        current_provider = context.current_provider
        total_available = 0
        
        # Check each provider
        for provider_name in self.provider_manager.providers:
            health = await self.provider_manager.get_provider_health(provider_name, context.backend)
            
            if health.available:
                total_available += 1
            
            # Format provider entry
            status_emoji = "✅" if health.available else "❌"
            current_indicator = "👉" if provider_name == current_provider else "  "
            cost_indicator = "💰" if health.estimated_cost_per_request > 0 else "🆓"
            offline_indicator = "🔒" if health.offline_capable else "🌐"
            
            basic_info = f"{current_indicator} {status_emoji} {provider_name.title()}"
            
            if detailed:
                result_lines.extend([
                    f"{basic_info}",
                    f"    Status: {health.configuration_status}",
                    f"    Response: {health.response_time:.2f}s",
                    f"    Success Rate: {health.success_rate:.1%}",
                    f"    Cost: {cost_indicator} ${health.estimated_cost_per_request:.4f}/request",
                    f"    Mode: {offline_indicator} {'Offline' if health.offline_capable else 'Online'}",
                    ""
                ])
                
                if health.capabilities:
                    result_lines.append(f"    🔧 {', '.join(health.capabilities[:2])}")
                    result_lines.append("")
                    
            else:
                # Compact format
                status_text = health.configuration_status if len(health.configuration_status) < 15 else "configured"
                result_lines.append(f"{basic_info} - {status_text} {cost_indicator}{offline_indicator}")
        
        # Summary
        result_lines.extend([
            "",
            f"📊 Summary: {total_available}/{len(self.provider_manager.providers)} providers available",
            f"👉 Current: {current_provider}",
        ])
        
        # Performance metrics
        if performance:
            result_lines.append("\n⚡ Performance Summary:")
            for provider_name in self.provider_manager.providers:
                history = self.provider_manager.performance_history.get(provider_name, {})
                if history.get('total_requests', 0) > 0:
                    avg_time = history.get('avg_response_time', 0)
                    success_rate = history.get('success_rate', 0)
                    result_lines.append(f"  {provider_name}: {avg_time:.2f}s avg, {success_rate:.1%} success")
        
        # Usage tips
        result_lines.extend([
            "",
            "💡 Quick Commands:",
            "  /claude <prompt>     # Switch to Claude",
            "  /gemma <prompt>      # Switch to Gemma (local)",
            "  /mcp --list          # List MCP tools",
            "  /provider <name>     # Switch provider",
            "",
            "🔒 = Offline  🌐 = Online  💰 = Paid  🆓 = Free"
        ])
        
        return '\n'.join(result_lines)


class SystemStatusCommandHandler(BaseCommandHandler):
    """Show current provider and system status"""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        verbose = parsed_cmd.kwargs.get('verbose', False)
        network = parsed_cmd.kwargs.get('network', False)
        recommendations = parsed_cmd.kwargs.get('recommendations', False)
        
        current_provider = context.current_provider
        network_available = self.provider_manager._check_network_connectivity()
        
        result_lines = [
            "📊 Smart AI System Status",
            "=" * 30,
            f"🤖 Active Provider: {current_provider}",
            f"🌐 Network: {'Connected' if network_available else 'Offline'}",
            f"📁 Project: {context.project_root.name}",
            f"⏰ Session: {(time.time() - context.session_data.get('session_start', time.time())) / 60:.1f}m",
            ""
        ]
        
        # Current provider health
        health = await self.provider_manager.get_provider_health(current_provider, context.backend)
        result_lines.extend([
            f"📋 Current Provider Status:",
            f"  Status: {'✅ Available' if health.available else '❌ Unavailable'}",
            f"  Configuration: {health.configuration_status}",
            f"  Response Time: {health.response_time:.2f}s",
            f"  Success Rate: {health.success_rate:.1%}",
        ])
        
        # Network-specific information
        if network:
            result_lines.append("\n🌐 Network Analysis:")
            if network_available:
                result_lines.extend([
                    "  ✅ Internet connectivity detected",
                    "  🤖 Cloud providers available",
                    "  🔄 Real-time MCP tool access",
                ])
            else:
                result_lines.extend([
                    "  🔒 Operating in offline mode",
                    "  🧠 Local providers recommended",
                    "  ⚠️ Limited cloud functionality",
                ])
        
        # Smart recommendations
        if recommendations:
            result_lines.append("\n🎯 Smart Recommendations:")
            
            # Recommend based on current situation
            if not network_available:
                result_lines.append("  • Switch to Gemma for offline AI assistance")
            elif health.success_rate < 0.8:
                result_lines.append(f"  • Consider switching from {current_provider} (low success rate)")
            elif health.response_time > 5.0:
                result_lines.append("  • Try Gemma for faster local responses")
            
            # Cost optimization
            total_requests = context.session_data.get('requests_count', 0)
            if total_requests > 20:
                result_lines.append("  • High usage detected - consider local Gemma for simple queries")
        
        # System health overview
        if verbose:
            result_lines.append("\n🔧 System Health:")
            
            # Memory usage
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                result_lines.append(f"  Memory: {memory_mb:.1f} MB")
            except:
                result_lines.append("  Memory: Unknown")
            
            # Configuration status
            claude_dir = context.get_claude_config_dir()
            user_dir = context.get_user_config_dir()
            result_lines.extend([
                f"  Project Config: {'✅' if claude_dir.exists() else '❌'}",
                f"  User Config: {'✅' if user_dir.exists() else '❌'}",
            ])
            
            # MCP status
            try:
                mcp_manager = await get_mcp_manager()
                if mcp_manager:
                    result_lines.append(f"  MCP Tools: {len(mcp_manager.tools)} available")
                else:
                    result_lines.append("  MCP Tools: Not initialized")
            except:
                result_lines.append("  MCP Tools: Error")
        
        return '\n'.join(result_lines)


def register_provider_commands(registry, notification_manager: Optional[NotificationManager] = None):
    """Register all provider control commands with the command registry"""
    
    provider_manager = ProviderManager()
    
    # Claude Provider Command
    registry.register(CommandDefinition(
        name="claude",
        handler=ClaudeProviderCommandHandler(provider_manager),
        description="Switch to Claude Code provider and optionally execute prompt",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("prompt", str, False, None, "Prompt to execute with Claude"),
            CommandParameter("status", bool, False, False, "Show Claude provider status only"),
            CommandParameter("force", bool, False, False, "Force switch even if unavailable")
        ],
        aliases=["c", "claude-code"],
        examples=[
            "/claude How do I optimize this code?",
            "/claude --status",
            "/claude --force Fix this bug"
        ],
        requires_internet=True,
        usage="/claude [prompt] [--status] [--force]"
    ))
    
    # Gemma Provider Command
    registry.register(CommandDefinition(
        name="gemma",
        handler=GemmaProviderCommandHandler(provider_manager),
        description="Switch to Gemma (Ollama) local AI provider with model management",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("prompt", str, False, None, "Prompt to execute with Gemma"),
            CommandParameter("status", bool, False, False, "Show Gemma provider status only"),
            CommandParameter("install", bool, False, False, "Install Gemma model via Ollama"),
            CommandParameter("models", bool, False, False, "List available Ollama models"),
            CommandParameter("force", bool, False, False, "Force switch even if unavailable")
        ],
        aliases=["g", "local", "ollama"],
        examples=[
            "/gemma What is machine learning?",
            "/gemma --status",
            "/gemma --install",
            "/gemma --models"
        ],
        requires_internet=False,
        usage="/gemma [prompt] [--status] [--install] [--models] [--force]"
    ))
    
    # TreeQuest Provider Command
    registry.register(CommandDefinition(
        name="treequest",
        handler=TreeQuestProviderCommandHandler(provider_manager),
        description="Switch to TreeQuest multi-provider orchestration system",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("prompt", str, False, None, "Prompt to execute with TreeQuest"),
            CommandParameter("status", bool, False, False, "Show TreeQuest provider status only"),
            CommandParameter("complexity", str, False, "medium", "Task complexity level",
                           choices=["low", "medium", "high"]),
            CommandParameter("force", bool, False, False, "Force switch even if unavailable")
        ],
        aliases=["tq", "tree", "orchestrator"],
        examples=[
            "/treequest Implement a complex algorithm",
            "/treequest --status",
            "/treequest --complexity=high Debug this architecture"
        ],
        requires_internet=True,
        usage="/treequest [prompt] [--status] [--complexity=level] [--force]"
    ))
    
    # MCP Provider Command
    registry.register(CommandDefinition(
        name="mcp",
        handler=MCPProviderCommandHandler(provider_manager),
        description="Switch to MCP tools provider with tool discovery and execution",
        category=CommandCategory.MCP,
        parameters=[
            CommandParameter("tool", str, False, None, "MCP tool to execute"),
            CommandParameter("list", bool, False, False, "List available MCP tools"),
            CommandParameter("category", str, False, None, "Filter tools by category"),
            CommandParameter("status", bool, False, False, "Show MCP provider status only"),
            CommandParameter("discover", bool, False, False, "Discover and refresh MCP tools")
        ],
        aliases=["tools", "mcp-tools"],
        examples=[
            "/mcp get_tasks",
            "/mcp --list",
            "/mcp --list --category=task_management",
            "/mcp --discover"
        ],
        requires_internet=False,
        usage="/mcp [tool] [--list] [--category=cat] [--status] [--discover]"
    ))
    
    # OpenDia Provider Command
    registry.register(CommandDefinition(
        name="opendia",
        handler=OpenDiaProviderCommandHandler(provider_manager),
        description="Switch to OpenDia browser automation provider",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("action", str, False, None, "Browser action to perform"),
            CommandParameter("url", str, False, None, "Target URL for browser action"),
            CommandParameter("status", bool, False, False, "Show OpenDia provider status only"),
            CommandParameter("start", bool, False, False, "Start OpenDia MCP server"),
            CommandParameter("force", bool, False, False, "Force switch even if unavailable")
        ],
        aliases=["browser", "web", "automation"],
        examples=[
            "/opendia navigate --url=https://google.com",
            "/opendia --status",
            "/opendia --start",
            "/opendia post_tweet"
        ],
        requires_internet=True,
        usage="/opendia [action] [--url=url] [--status] [--start] [--force]"
    ))
    
    # Generic Provider Command
    registry.register(CommandDefinition(
        name="provider",
        handler=GenericProviderCommandHandler(provider_manager),
        description="Generic provider switching with smart recommendations",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("name", str, True, None, "Provider name to switch to"),
            CommandParameter("prompt", str, False, None, "Prompt to execute after switching"),
            CommandParameter("force", bool, False, False, "Force switch even if unavailable"),
            CommandParameter("recommend", bool, False, False, "Get provider recommendation for prompt")
        ],
        examples=[
            "/provider claude_code",
            "/provider gemma Hello world",
            "/provider mcp --recommend What are my tasks?"
        ],
        usage="/provider <name> [prompt] [--force] [--recommend]"
    ))
    
    # Providers List Command
    registry.register(CommandDefinition(
        name="providers",
        handler=ProvidersListCommandHandler(provider_manager),
        description="List all available providers with comprehensive status information",
        category=CommandCategory.PROVIDER,
        parameters=[
            CommandParameter("detailed", bool, False, False, "Show detailed provider information"),
            CommandParameter("status", bool, False, False, "Show status overview only"),
            CommandParameter("performance", bool, False, False, "Include performance metrics")
        ],
        aliases=["list-providers", "provider-list"],
        examples=[
            "/providers",
            "/providers --detailed",
            "/providers --performance"
        ],
        usage="/providers [--detailed] [--status] [--performance]"
    ))
    
    # Enhanced Status Command
    registry.register(CommandDefinition(
        name="status",
        handler=SystemStatusCommandHandler(provider_manager),
        description="Show current provider and comprehensive system status",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("verbose", bool, False, False, "Show detailed system information"),
            CommandParameter("network", bool, False, False, "Include network connectivity analysis"),
            CommandParameter("recommendations", bool, False, False, "Show smart provider recommendations")
        ],
        aliases=["stat", "info"],
        examples=[
            "/status",
            "/status --verbose",
            "/status --network --recommendations"
        ],
        usage="/status [--verbose] [--network] [--recommendations]"
    ))


# Integration function for easy setup
def integrate_provider_commands(smart_ai_instance, notification_manager: Optional[NotificationManager] = None):
    """
    Integrate provider control commands into an existing smart-ai instance
    """
    if hasattr(smart_ai_instance, 'command_registry'):
        register_provider_commands(smart_ai_instance.command_registry, notification_manager)
        return True
    else:
        raise ValueError("Smart AI instance must have a command_registry attribute")


if __name__ == "__main__":
    print("Smart AI Provider Commands Implementation")
    print("=" * 50)
    print("This module provides comprehensive provider control commands:")
    print("• /claude - Claude Code provider with status display")
    print("• /gemma - Gemma (Ollama) provider with model management")
    print("• /treequest - TreeQuest provider with capability info")
    print("• /mcp - MCP provider with tool discovery")
    print("• /opendia - OpenDia browser automation provider")
    print("• /provider - Generic provider switching command")
    print("• /providers - List all available providers with status")
    print("• /status - Show current provider and system status")
    print("\nFeatures:")
    print("• Provider availability checking and validation")
    print("• Smart provider recommendation based on query type")
    print("• Provider health monitoring and diagnostics")
    print("• Performance metrics and usage tracking")
    print("• Integration with notification system")
    print("• Offline detection and fallback provider selection")
    print("\nUse integrate_provider_commands() to add these to your smart-ai instance.")
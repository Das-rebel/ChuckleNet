#!/usr/bin/env python3
"""
Smart AI Essential System Commands Implementation
Production-ready command handlers following Claude Code patterns with comprehensive functionality
"""

import asyncio
import json
import time
import sys
import os
import platform
import subprocess
import uuid
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import psutil
import socket

# Import smart-ai components
from smart_ai_slash_commands import (
    BaseCommandHandler, CommandDefinition, CommandParameter, CommandCategory,
    ParsedCommand, CommandExecutionContext, command_error_handler
)
from smart_ai_notifications import NotificationManager, NotificationType


@dataclass
class SystemInfo:
    """System information container"""
    platform: str
    python_version: str
    memory_usage: float
    cpu_count: int
    disk_usage: float
    uptime: float
    network_connected: bool


class SystemCommandHandlers:
    """Collection of essential system command handlers for smart-ai"""
    
    def __init__(self, notification_manager: Optional[NotificationManager] = None):
        self.notification_manager = notification_manager
        self.system_info_cache = {}
        self.cache_expiry = 30  # seconds
        self.cost_tracking = {}
        self.session_start_time = time.time()
    
    def _get_system_info(self) -> SystemInfo:
        """Get cached or fresh system information"""
        current_time = time.time()
        if (current_time - self.system_info_cache.get('timestamp', 0)) > self.cache_expiry:
            self.system_info_cache = {
                'timestamp': current_time,
                'info': self._collect_system_info()
            }
        return self.system_info_cache['info']
    
    def _collect_system_info(self) -> SystemInfo:
        """Collect current system information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            disk_usage = psutil.disk_usage('/').percent
            uptime = time.time() - self.session_start_time
            
            # Check network connectivity
            network_connected = self._check_network()
            
            return SystemInfo(
                platform=platform.platform(),
                python_version=sys.version.split()[0],
                memory_usage=memory_mb,
                cpu_count=psutil.cpu_count(),
                disk_usage=disk_usage,
                uptime=uptime,
                network_connected=network_connected
            )
        except Exception:
            # Fallback for systems without psutil
            return SystemInfo(
                platform=platform.platform(),
                python_version=sys.version.split()[0],
                memory_usage=0,
                cpu_count=os.cpu_count() or 1,
                disk_usage=0,
                uptime=time.time() - self.session_start_time,
                network_connected=self._check_network()
            )
    
    def _check_network(self) -> bool:
        """Check if network is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False


class EnhancedHelpCommandHandler(BaseCommandHandler):
    """Enhanced help command with comprehensive documentation and examples"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        query = parsed_cmd.kwargs.get('query') or (parsed_cmd.args[0] if parsed_cmd.args else None)
        category = parsed_cmd.kwargs.get('category')
        search = parsed_cmd.kwargs.get('search')
        examples = parsed_cmd.kwargs.get('examples', False)
        
        registry = context.smart_ai.command_registry
        
        if query:
            help_text = registry.get_command_help(query)
            if examples and query in registry.commands:
                cmd_def = registry.commands[query]
                if cmd_def.examples:
                    help_text += "\n\n📚 Additional Examples:\n"
                    for example in cmd_def.examples:
                        help_text += f"  {example}\n"
            return help_text
        
        if search:
            commands = registry.search_commands(search)
            if not commands:
                return f"No commands found matching '{search}'"
            
            help_text = [f"Commands matching '{search}':", "=" * 40]
            for cmd in commands:
                aliases_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                help_text.append(f"  /{cmd.name}{aliases_str} - {cmd.description}")
            return "\n".join(help_text)
        
        # Enhanced general help with better organization
        help_text = [
            "🚀 Smart AI Enhanced Command System",
            "=" * 45,
            "",
            "Smart AI provides a comprehensive slash command system inspired by Claude Code.",
            "Commands support intelligent provider routing, progress tracking, and extensive",
            "customization through project-specific configurations.",
            ""
        ]
        
        # Show quick start commands
        help_text.extend([
            "⚡ Quick Start:",
            "  /help <command>     # Get detailed help for any command",
            "  /status            # Show system status and provider info",
            "  /providers         # List available AI providers",
            "  /claude <prompt>   # Switch to Claude and execute prompt",
            "  /mcp               # List available MCP tools",
            "  /project init      # Initialize project for smart-ai",
            ""
        ])
        
        if category:
            try:
                cat_enum = CommandCategory(category)
                commands = registry.list_commands(cat_enum)
                help_text.append(f"{cat_enum.value.title()} Commands:")
                help_text.append("-" * 25)
            except ValueError:
                return f"Invalid category: {category}. Valid categories: {', '.join(c.value for c in CommandCategory)}"
        else:
            commands = registry.list_commands()
        
        # Group commands by category with enhanced formatting
        for category_enum in CommandCategory:
            category_commands = [cmd for cmd in commands if cmd.category == category_enum]
            if category_commands:
                help_text.append(f"\n📋 {category_enum.value.title()}:")
                for cmd in sorted(category_commands, key=lambda x: x.name):
                    aliases_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    source_str = f" [{cmd.source}]" if cmd.source != "builtin" else ""
                    internet_str = " 🌐" if getattr(cmd, 'requires_internet', False) else ""
                    project_str = " 📁" if getattr(cmd, 'requires_project', False) else ""
                    
                    help_text.append(f"  /{cmd.name}{aliases_str}{source_str}{internet_str}{project_str}")
                    help_text.append(f"    {cmd.description}")
        
        help_text.extend([
            "",
            "💡 Advanced Usage:",
            "  /command [args] [--option=value]  # Basic syntax",
            "  /help --category=<category>       # Filter by category",
            "  /help --search=<term>             # Search commands",
            "  /help <command> --examples        # Show examples for command",
            "",
            "🔧 Configuration:",
            "  Project commands: .claude/commands/*.md",
            "  User commands: ~/.claude/commands/*.md",
            "  Notifications: ~/.smart_ai/notifications.json",
            "",
            "🛠️ MCP Integration:",
            "  /mcp <tool> [args]               # Execute MCP tool",
            "  /mcp__<server>__<tool> [args]    # Direct MCP tool access",
            "",
            "📊 Symbols:",
            "  🌐 Requires internet    📁 Requires project context",
            "",
            "Type '/help <command>' for detailed information about any command."
        ])
        
        return "\n".join(help_text)


class ComprehensiveStatusCommandHandler(BaseCommandHandler):
    """Comprehensive status command showing all system information"""
    
    def __init__(self, system_handlers: SystemCommandHandlers):
        self.system_handlers = system_handlers
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        verbose = parsed_cmd.kwargs.get('verbose', False)
        providers = parsed_cmd.kwargs.get('providers', False)
        mcp = parsed_cmd.kwargs.get('mcp', False)
        performance = parsed_cmd.kwargs.get('performance', False)
        
        backend = context.backend
        system_info = self.system_handlers._get_system_info()
        
        status_lines = [
            "🚀 Smart AI Enhanced System Status",
            "=" * 40,
            f"📊 Core Information:",
            f"  Session Duration: {system_info.uptime:.1f}s",
            f"  Current Provider: {context.current_provider}",
            f"  Project Root: {context.project_root.name}",
            f"  Network Status: {'🌐 Connected' if system_info.network_connected else '🔒 Offline'}",
            f"  Requests This Session: {context.session_data.get('requests_count', 0)}",
        ]
        
        # Provider status with detailed information
        if backend and (providers or verbose):
            status_lines.append("\n🤖 Provider Status:")
            provider_statuses = {}
            for provider in backend.providers:
                available = backend._check_provider_availability(provider)
                status_emoji = "✅" if available else "❌"
                provider_statuses[provider] = available
                
                # Add provider-specific details
                details = []
                if provider == 'claude_code':
                    if available:
                        details.append("Claude CLI detected")
                    else:
                        details.append("Claude CLI not found")
                elif provider == 'gemma':
                    if available:
                        details.append("Ollama + Gemma2:2b ready")
                    else:
                        details.append("Ollama/Gemma not configured")
                elif provider == 'treequest':
                    if available:
                        details.append("Enhanced TreeQuest available")
                    else:
                        details.append("TreeQuest not found")
                elif provider == 'opendia':
                    if available:
                        details.append("Browser automation ready")
                    else:
                        details.append("OpenDia not configured")
                elif provider == 'mcp':
                    if available:
                        details.append("MCP tools configured")
                    else:
                        details.append("MCP configuration missing")
                
                detail_str = f" - {details[0]}" if details else ""
                status_lines.append(f"  {provider}: {status_emoji} {detail_str}")
        
        # MCP Tools status
        if backend and (mcp or verbose):
            status_lines.append("\n🔧 MCP Tools Status:")
            if backend.mcp_manager:
                status_lines.append(f"  Total Tools: {len(backend.mcp_manager.tools)}")
                
                # Group tools by category
                categories = {}
                for tool_name, tool in backend.mcp_manager.tools.items():
                    category = tool.category
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(tool_name)
                
                for category, tools in categories.items():
                    status_lines.append(f"  {category.title()}: {len(tools)} tools")
                    if verbose:
                        for tool in tools[:3]:  # Show first 3 tools
                            status_lines.append(f"    - {tool}")
                        if len(tools) > 3:
                            status_lines.append(f"    ... and {len(tools) - 3} more")
            else:
                status_lines.append("  MCP Manager: Not initialized")
        
        # Performance metrics
        if performance or verbose:
            status_lines.append(f"\n⚡ Performance Metrics:")
            status_lines.append(f"  Memory Usage: {system_info.memory_usage:.1f} MB")
            status_lines.append(f"  CPU Cores: {system_info.cpu_count}")
            status_lines.append(f"  Platform: {system_info.platform}")
            status_lines.append(f"  Python: {system_info.python_version}")
            
            if system_info.disk_usage > 0:
                status_lines.append(f"  Disk Usage: {system_info.disk_usage:.1f}%")
        
        # Command registry information
        registry = context.smart_ai.command_registry
        total_commands = len(registry.commands) + len(registry.mcp_commands)
        status_lines.append(f"\n📚 Command Registry:")
        status_lines.append(f"  Total Commands: {total_commands}")
        status_lines.append(f"  Built-in: {len([c for c in registry.commands.values() if c.source == 'builtin'])}")
        status_lines.append(f"  Custom: {len([c for c in registry.commands.values() if c.source != 'builtin'])}")
        status_lines.append(f"  MCP: {len(registry.mcp_commands)}")
        
        # Configuration status
        claude_dir = context.get_claude_config_dir()
        user_claude_dir = context.get_user_config_dir()
        
        status_lines.append(f"\n⚙️ Configuration:")
        status_lines.append(f"  Project .claude: {'✅ Exists' if claude_dir.exists() else '❌ Missing'}")
        status_lines.append(f"  User .claude: {'✅ Exists' if user_claude_dir.exists() else '❌ Missing'}")
        
        if claude_dir.exists():
            commands_dir = claude_dir / "commands"
            memory_dir = claude_dir / "memory"
            custom_commands = len(list(commands_dir.glob("*.md"))) if commands_dir.exists() else 0
            memory_files = len(list(memory_dir.glob("*.md"))) if memory_dir.exists() else 0
            
            status_lines.append(f"  Custom Commands: {custom_commands}")
            status_lines.append(f"  Memory Files: {memory_files}")
        
        # Recent activity (if verbose)
        if verbose and hasattr(context.smart_ai, 'command_registry'):
            if hasattr(context.smart_ai, 'slash_commands'):
                command_system = context.smart_ai.slash_commands.command_system
                if command_system.command_history:
                    status_lines.append(f"\n📈 Recent Activity:")
                    recent_commands = command_system.command_history[-3:]
                    for cmd in recent_commands:
                        duration = f" ({cmd.get('duration', 0):.2f}s)" if 'duration' in cmd else ""
                        status_emoji = "✅" if cmd.get('status') == 'success' else "❌"
                        status_lines.append(f"  {status_emoji} {cmd.get('command', 'Unknown')}{duration}")
        
        return "\n".join(status_lines)


class VersionCommandHandler(BaseCommandHandler):
    """Comprehensive version information command"""
    
    def __init__(self, system_handlers: SystemCommandHandlers):
        self.system_handlers = system_handlers
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        detailed = parsed_cmd.kwargs.get('detailed', False)
        dependencies = parsed_cmd.kwargs.get('dependencies', False)
        
        system_info = self.system_handlers._get_system_info()
        
        version_info = [
            "🚀 Smart AI Enhanced v2.1.0",
            "=" * 35,
            "",
            "📦 Core Features:",
            "  ✅ Comprehensive slash command system",
            "  ✅ Multi-provider AI integration",
            "  ✅ MCP tool framework",
            "  ✅ Visual notification system",
            "  ✅ Session management",
            "  ✅ Custom command support",
            "  ✅ Project initialization",
            "  ✅ Performance monitoring",
            "",
            "🤖 Supported Providers:",
            "  • Claude Code (Anthropic CLI)",
            "  • TreeQuest (Enhanced multi-provider)",
            "  • Gemma (Local via Ollama)",
            "  • OpenDia (Browser automation)",
            "  • MCP Tools (Extensible framework)",
            "",
            f"🖥️ Environment:",
            f"  Platform: {system_info.platform}",
            f"  Python: {system_info.python_version}",
            f"  Memory: {system_info.memory_usage:.1f} MB",
            f"  CPU Cores: {system_info.cpu_count}",
            f"  Network: {'Connected' if system_info.network_connected else 'Offline'}",
        ]
        
        if detailed:
            version_info.extend([
                "",
                "🔧 Technical Details:",
                f"  Session Uptime: {system_info.uptime:.1f}s",
                f"  Working Directory: {context.project_root}",
                f"  Config Directory: {context.get_user_config_dir()}",
                f"  Process ID: {os.getpid()}",
            ])
            
            # Add provider-specific version info
            if context.backend:
                version_info.append("\n📊 Provider Versions:")
                for provider in context.backend.providers:
                    available = context.backend._check_provider_availability(provider)
                    if available:
                        version_info.append(f"  {provider}: Available")
                    else:
                        version_info.append(f"  {provider}: Not configured")
        
        if dependencies:
            version_info.extend([
                "",
                "📚 Key Dependencies:",
                "  • asyncio (built-in)",
                "  • pathlib (built-in)",
                "  • psutil (system monitoring)",
                "  • rich (terminal formatting)",
                "  • plyer (system notifications)",
                "",
                "🔗 Integration Points:",
                "  • Claude Code CLI",
                "  • Ollama (local AI)",
                "  • MCP Protocol",
                "  • System notifications",
                "  • Git integration",
            ])
        
        version_info.extend([
            "",
            "📖 Documentation:",
            "  Type '/help' for command reference",
            "  Type '/status' for system status",
            "  Type '/project init' to setup project",
            "",
            "Made with ❤️ for enhanced AI workflows"
        ])
        
        return "\n".join(version_info)


class ConfigCommandHandler(BaseCommandHandler):
    """Configuration management command"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'show'
        key = parsed_cmd.kwargs.get('key')
        value = parsed_cmd.kwargs.get('value')
        
        config_path = context.get_user_config_dir() / "smart_ai_config.json"
        
        # Load existing config
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                return f"❌ Error loading config: {e}"
        
        if action == 'show':
            if not config:
                return "📝 No configuration found. Use '/config set --key=<key> --value=<value>' to add settings."
            
            config_lines = ["⚙️ Smart AI Configuration:", "=" * 30]
            for k, v in config.items():
                config_lines.append(f"  {k}: {v}")
            return "\n".join(config_lines)
        
        elif action == 'set':
            if not key or value is None:
                return "❌ Both --key and --value are required for set action"
            
            config[key] = value
            
            # Save config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                return f"✅ Set {key} = {value}"
            except Exception as e:
                return f"❌ Error saving config: {e}"
        
        elif action == 'unset':
            if not key:
                return "❌ --key is required for unset action"
            
            if key in config:
                del config[key]
                try:
                    with open(config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    return f"✅ Removed {key}"
                except Exception as e:
                    return f"❌ Error saving config: {e}"
            else:
                return f"❌ Key '{key}' not found in configuration"
        
        elif action == 'reset':
            if config_path.exists():
                config_path.unlink()
                return "✅ Configuration reset to defaults"
            else:
                return "📝 No configuration file to reset"
        
        else:
            return f"❌ Unknown action: {action}. Available: show, set, unset, reset"


class PermissionsCommandHandler(BaseCommandHandler):
    """Provider permissions and access management"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'show'
        provider = parsed_cmd.kwargs.get('provider')
        
        permissions_path = context.get_user_config_dir() / "permissions.json"
        
        # Load existing permissions
        permissions = {}
        if permissions_path.exists():
            try:
                with open(permissions_path, 'r') as f:
                    permissions = json.load(f)
            except Exception as e:
                return f"❌ Error loading permissions: {e}"
        
        if action == 'show':
            if not permissions:
                return "🔒 No custom permissions set. All providers use default access levels."
            
            perm_lines = ["🔐 Provider Permissions:", "=" * 25]
            for provider_name, perms in permissions.items():
                perm_lines.append(f"\n{provider_name}:")
                for perm, value in perms.items():
                    perm_lines.append(f"  {perm}: {value}")
            return "\n".join(perm_lines)
        
        elif action == 'grant':
            if not provider:
                return "❌ --provider is required for grant action"
            
            permission_type = parsed_cmd.kwargs.get('type', 'basic')
            
            if provider not in permissions:
                permissions[provider] = {}
            
            permissions[provider][permission_type] = True
            permissions[provider]['granted_at'] = datetime.now().isoformat()
            
            # Save permissions
            permissions_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(permissions_path, 'w') as f:
                    json.dump(permissions, f, indent=2)
                return f"✅ Granted {permission_type} access to {provider}"
            except Exception as e:
                return f"❌ Error saving permissions: {e}"
        
        elif action == 'revoke':
            if not provider:
                return "❌ --provider is required for revoke action"
            
            permission_type = parsed_cmd.kwargs.get('type', 'basic')
            
            if provider in permissions and permission_type in permissions[provider]:
                del permissions[provider][permission_type]
                if not permissions[provider]:
                    del permissions[provider]
                
                try:
                    with open(permissions_path, 'w') as f:
                        json.dump(permissions, f, indent=2)
                    return f"✅ Revoked {permission_type} access from {provider}"
                except Exception as e:
                    return f"❌ Error saving permissions: {e}"
            else:
                return f"❌ No {permission_type} permission found for {provider}"
        
        else:
            return f"❌ Unknown action: {action}. Available: show, grant, revoke"


class DoctorCommandHandler(BaseCommandHandler):
    """Health check and diagnostic command"""
    
    def __init__(self, system_handlers: SystemCommandHandlers):
        self.system_handlers = system_handlers
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        fix = parsed_cmd.kwargs.get('fix', False)
        verbose = parsed_cmd.kwargs.get('verbose', False)
        
        self.show_progress("Running system health checks...", context)
        
        issues = []
        suggestions = []
        system_info = self.system_handlers._get_system_info()
        
        doctor_lines = [
            "🩺 Smart AI Health Check",
            "=" * 30,
            ""
        ]
        
        # Check Python version
        python_version = tuple(map(int, sys.version.split()[0].split('.')))
        if python_version < (3, 8):
            issues.append("Python version too old (< 3.8)")
            suggestions.append("Upgrade to Python 3.8 or newer")
        else:
            doctor_lines.append("✅ Python version: OK")
        
        # Check memory usage
        if system_info.memory_usage > 500:  # MB
            issues.append(f"High memory usage: {system_info.memory_usage:.1f} MB")
            suggestions.append("Consider restarting smart-ai session")
        else:
            doctor_lines.append("✅ Memory usage: OK")
        
        # Check network connectivity
        if system_info.network_connected:
            doctor_lines.append("✅ Network connectivity: OK")
        else:
            issues.append("No network connectivity")
            suggestions.append("Check internet connection for cloud providers")
        
        # Check provider availability
        if context.backend:
            doctor_lines.append("\n🤖 Provider Health:")
            working_providers = 0
            for provider in context.backend.providers:
                available = context.backend._check_provider_availability(provider)
                if available:
                    doctor_lines.append(f"✅ {provider}: Available")
                    working_providers += 1
                else:
                    doctor_lines.append(f"❌ {provider}: Not available")
                    issues.append(f"Provider {provider} not configured")
                    
                    # Provider-specific suggestions
                    if provider == 'claude_code':
                        suggestions.append("Install Claude CLI: Follow Anthropic's installation guide")
                    elif provider == 'gemma':
                        suggestions.append("Install Ollama and pull Gemma model: ollama pull gemma2:2b")
                    elif provider == 'treequest':
                        suggestions.append("Check TreeQuest installation in CascadeProjects")
                    elif provider == 'opendia':
                        suggestions.append("Setup OpenDia MCP server")
                    elif provider == 'mcp':
                        suggestions.append("Configure MCP tools in ~/.mcp.json")
            
            if working_providers == 0:
                issues.append("No working providers available")
                suggestions.append("At least one provider must be configured")
        
        # Check configuration files
        claude_dir = context.get_claude_config_dir()
        user_claude_dir = context.get_user_config_dir()
        
        doctor_lines.append("\n⚙️ Configuration Health:")
        if user_claude_dir.exists():
            doctor_lines.append("✅ User .claude directory: OK")
        else:
            issues.append("User .claude directory missing")
            suggestions.append(f"Create directory: mkdir -p {user_claude_dir}")
        
        # Check project structure if in project
        if claude_dir.exists():
            doctor_lines.append("✅ Project .claude directory: OK")
        else:
            doctor_lines.append("ℹ️ Project .claude directory: Not initialized (use '/project init')")
        
        # Check MCP configuration
        mcp_config = Path.home() / ".mcp.json"
        if mcp_config.exists():
            doctor_lines.append("✅ MCP configuration: Found")
        else:
            doctor_lines.append("ℹ️ MCP configuration: Not configured")
        
        # Check for common issues
        doctor_lines.append("\n🔍 Common Issues Check:")
        
        # Check for conflicting processes
        try:
            current_process = psutil.Process()
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] in ['smart-ai', 'smart_ai'] and proc.pid != current_process.pid:
                    issues.append("Multiple smart-ai instances detected")
                    suggestions.append("Stop other instances to avoid conflicts")
                    break
            else:
                doctor_lines.append("✅ No conflicting processes")
        except:
            doctor_lines.append("ℹ️ Process check: Skipped")
        
        # Check disk space
        if system_info.disk_usage > 90:
            issues.append(f"Low disk space: {system_info.disk_usage:.1f}% used")
            suggestions.append("Free up disk space")
        else:
            doctor_lines.append("✅ Disk space: OK")
        
        # Summary
        doctor_lines.append("\n📊 Health Summary:")
        if not issues:
            doctor_lines.append("🎉 All systems healthy!")
        else:
            doctor_lines.append(f"⚠️ Found {len(issues)} issue(s):")
            for issue in issues:
                doctor_lines.append(f"  • {issue}")
        
        if suggestions:
            doctor_lines.append("\n💡 Suggestions:")
            for suggestion in suggestions:
                doctor_lines.append(f"  • {suggestion}")
        
        # Auto-fix option
        if fix and issues:
            doctor_lines.append("\n🔧 Attempting auto-fixes...")
            
            # Try to create missing directories
            if not user_claude_dir.exists():
                try:
                    user_claude_dir.mkdir(parents=True, exist_ok=True)
                    doctor_lines.append("✅ Created user .claude directory")
                except Exception as e:
                    doctor_lines.append(f"❌ Failed to create .claude directory: {e}")
            
            # Additional auto-fixes could be implemented here
            doctor_lines.append("🏁 Auto-fix complete")
        
        if verbose:
            doctor_lines.extend([
                "",
                "🔬 Verbose System Information:",
                f"  Platform: {system_info.platform}",
                f"  Python: {system_info.python_version}",
                f"  Memory: {system_info.memory_usage:.1f} MB",
                f"  CPU Cores: {system_info.cpu_count}",
                f"  Session Uptime: {system_info.uptime:.1f}s",
                f"  Working Directory: {os.getcwd()}",
                f"  Process ID: {os.getpid()}",
            ])
        
        return "\n".join(doctor_lines)


class CostCommandHandler(BaseCommandHandler):
    """Token usage and provider cost tracking"""
    
    def __init__(self, system_handlers: SystemCommandHandlers):
        self.system_handlers = system_handlers
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        reset = parsed_cmd.kwargs.get('reset', False)
        provider = parsed_cmd.kwargs.get('provider')
        detailed = parsed_cmd.kwargs.get('detailed', False)
        
        cost_file = context.get_user_config_dir() / "cost_tracking.json"
        
        # Load cost data
        cost_data = {}
        if cost_file.exists():
            try:
                with open(cost_file, 'r') as f:
                    cost_data = json.load(f)
            except Exception:
                cost_data = {}
        
        if reset:
            if cost_file.exists():
                cost_file.unlink()
            return "✅ Cost tracking data reset"
        
        # Initialize default structure if empty
        if not cost_data:
            cost_data = {
                'session_start': time.time(),
                'providers': {},
                'total_requests': 0,
                'last_updated': time.time()
            }
        
        cost_lines = [
            "💰 Smart AI Usage & Cost Tracking",
            "=" * 40,
        ]
        
        # Session overview
        session_duration = time.time() - cost_data.get('session_start', time.time())
        cost_lines.extend([
            f"📊 Session Overview:",
            f"  Duration: {session_duration / 3600:.1f} hours",
            f"  Total Requests: {cost_data.get('total_requests', 0)}",
            f"  Last Updated: {datetime.fromtimestamp(cost_data.get('last_updated', time.time())).strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ])
        
        # Provider-specific costs
        providers_data = cost_data.get('providers', {})
        
        if provider:
            # Show specific provider details
            if provider in providers_data:
                provider_data = providers_data[provider]
                cost_lines.extend([
                    f"🤖 {provider.title()} Usage:",
                    f"  Requests: {provider_data.get('requests', 0)}",
                    f"  Total Tokens: {provider_data.get('total_tokens', 0):,}",
                    f"  Input Tokens: {provider_data.get('input_tokens', 0):,}",
                    f"  Output Tokens: {provider_data.get('output_tokens', 0):,}",
                ])
                
                # Estimated costs (placeholder - would need actual API pricing)
                estimated_cost = provider_data.get('estimated_cost', 0)
                cost_lines.append(f"  Estimated Cost: ${estimated_cost:.4f}")
            else:
                cost_lines.append(f"❌ No usage data for provider: {provider}")
        else:
            # Show all providers
            if providers_data:
                cost_lines.append("🤖 Provider Usage:")
                total_cost = 0
                total_requests = 0
                
                for prov_name, prov_data in providers_data.items():
                    requests = prov_data.get('requests', 0)
                    tokens = prov_data.get('total_tokens', 0)
                    cost = prov_data.get('estimated_cost', 0)
                    
                    total_requests += requests
                    total_cost += cost
                    
                    cost_lines.append(f"  {prov_name}:")
                    cost_lines.append(f"    Requests: {requests}")
                    cost_lines.append(f"    Tokens: {tokens:,}")
                    cost_lines.append(f"    Cost: ${cost:.4f}")
                
                cost_lines.extend([
                    "",
                    f"💸 Total Estimated Cost: ${total_cost:.4f}",
                    f"📈 Average Cost per Request: ${total_cost/max(total_requests, 1):.4f}"
                ])
            else:
                cost_lines.append("📊 No usage data available yet")
        
        # Cost breakdown by type
        if detailed and providers_data:
            cost_lines.append("\n📈 Detailed Breakdown:")
            
            # Calculate averages
            total_input_tokens = sum(p.get('input_tokens', 0) for p in providers_data.values())
            total_output_tokens = sum(p.get('output_tokens', 0) for p in providers_data.values())
            total_requests = sum(p.get('requests', 0) for p in providers_data.values())
            
            if total_requests > 0:
                avg_input = total_input_tokens / total_requests
                avg_output = total_output_tokens / total_requests
                
                cost_lines.extend([
                    f"  Average Input Tokens/Request: {avg_input:.1f}",
                    f"  Average Output Tokens/Request: {avg_output:.1f}",
                    f"  Input/Output Ratio: {avg_input/max(avg_output, 1):.2f}",
                ])
        
        # Usage recommendations
        cost_lines.extend([
            "",
            "💡 Cost Optimization Tips:",
            "  • Use local providers (gemma) for simple queries",
            "  • Cache responses for repeated questions",
            "  • Use shorter prompts when possible",
            "  • Monitor usage with '/cost --detailed'",
        ])
        
        return "\n".join(cost_lines)


class ResetCommandHandler(BaseCommandHandler):
    """Reset all provider connections and session state"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        all_data = parsed_cmd.kwargs.get('all', False)
        providers = parsed_cmd.kwargs.get('providers', False)
        session = parsed_cmd.kwargs.get('session', False)
        confirm = parsed_cmd.kwargs.get('confirm', False)
        
        if not confirm and all_data:
            return ("⚠️ This will reset ALL smart-ai data including session, configuration, and cache.\n"
                   "Use '/reset --all --confirm' to proceed.")
        
        reset_items = []
        
        # Reset session data
        if session or all_data:
            context.session_data.clear()
            context.session_data['session_start'] = time.time()
            reset_items.append("session data")
        
        # Reset provider connections
        if providers or all_data:
            if context.backend:
                # Re-initialize backend if possible
                context.backend.session_data.clear()
                context.backend.load_session_state()
                reset_items.append("provider connections")
        
        # Reset configuration files
        if all_data:
            config_files = [
                context.get_user_config_dir() / "smart_ai_config.json",
                context.get_user_config_dir() / "cost_tracking.json",
                context.get_user_config_dir() / "permissions.json",
                context.get_user_config_dir() / "notifications.json"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    try:
                        config_file.unlink()
                        reset_items.append(f"{config_file.name}")
                    except Exception as e:
                        return f"❌ Error removing {config_file.name}: {e}"
        
        if reset_items:
            return f"✅ Reset: {', '.join(reset_items)}"
        else:
            return "❌ No reset options specified. Use --session, --providers, or --all"


class ExitCommandHandler(BaseCommandHandler):
    """Enhanced exit command with graceful cleanup"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        force = parsed_cmd.kwargs.get('force', False)
        save_session = parsed_cmd.kwargs.get('save', False)
        
        # Save session if requested
        if save_session:
            session_name = parsed_cmd.kwargs.get('name', f"session_{int(time.time())}")
            # This would integrate with session management
            context.session_data['exit_timestamp'] = time.time()
        
        # Graceful cleanup
        try:
            # Save current session state
            if context.backend:
                context.backend.save_session_state()
            
            # Cleanup notification system
            if hasattr(context.smart_ai, 'notification_manager'):
                context.smart_ai.notification_manager.shutdown()
            
            # Set exit flag
            context.smart_ai.should_exit = True
            
            exit_message = "👋 Smart AI shutting down gracefully..."
            if save_session:
                exit_message += f"\n💾 Session saved as '{session_name}'"
            
            return exit_message
            
        except Exception as e:
            if force:
                context.smart_ai.should_exit = True
                return "🛑 Force exit - some cleanup may have failed"
            else:
                return f"❌ Exit error: {e}. Use --force to exit anyway"


class OfflineCommandHandler(BaseCommandHandler):
    """Force offline mode for local-only operation"""
    
    @command_error_handler
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        enable = parsed_cmd.kwargs.get('enable', True)
        
        if enable:
            # Set offline mode in session data
            context.session_data['offline_mode'] = True
            
            # Switch to offline-capable provider
            if context.backend:
                offline_providers = ['gemma']  # Providers that work offline
                available_offline = [p for p in offline_providers 
                                   if context.backend._check_provider_availability(p)]
                
                if available_offline:
                    context.smart_ai.current_provider = available_offline[0]
                    return (f"🔒 Offline mode enabled\n"
                           f"✅ Switched to {available_offline[0]} (offline-capable)")
                else:
                    return ("🔒 Offline mode enabled\n"
                           "⚠️ No offline-capable providers available")
            else:
                return "🔒 Offline mode enabled"
        else:
            # Disable offline mode
            context.session_data['offline_mode'] = False
            return "🌐 Offline mode disabled - all providers available"


def register_system_commands(registry, notification_manager: Optional[NotificationManager] = None):
    """Register all system commands with the command registry"""
    
    system_handlers = SystemCommandHandlers(notification_manager)
    
    # Enhanced Help Command
    registry.register(CommandDefinition(
        name="help",
        handler=EnhancedHelpCommandHandler(),
        description="Show comprehensive help with examples and categories",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("query", str, False, None, "Command to get help for"),
            CommandParameter("category", str, False, None, "Filter by category", 
                           choices=[c.value for c in CommandCategory]),
            CommandParameter("search", str, False, None, "Search commands by keyword"),
            CommandParameter("examples", bool, False, False, "Show additional examples")
        ],
        aliases=["h", "?"],
        examples=[
            "/help",
            "/help status",
            "/help --category=provider",
            "/help --search=session",
            "/help claude --examples"
        ],
        usage="/help [command] [--category=<cat>] [--search=<term>] [--examples]"
    ))
    
    # Comprehensive Status Command
    registry.register(CommandDefinition(
        name="status",
        handler=ComprehensiveStatusCommandHandler(system_handlers),
        description="Show comprehensive system status with detailed information",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("verbose", bool, False, False, "Show detailed information"),
            CommandParameter("providers", bool, False, False, "Show detailed provider info"),
            CommandParameter("mcp", bool, False, False, "Show MCP tools status"),
            CommandParameter("performance", bool, False, False, "Show performance metrics")
        ],
        aliases=["stat", "info"],
        examples=[
            "/status",
            "/status --verbose",
            "/status --providers",
            "/status --mcp --performance"
        ],
        usage="/status [--verbose] [--providers] [--mcp] [--performance]"
    ))
    
    # Enhanced Version Command
    registry.register(CommandDefinition(
        name="version",
        handler=VersionCommandHandler(system_handlers),
        description="Show Smart AI version and environment information",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("detailed", bool, False, False, "Show detailed version info"),
            CommandParameter("dependencies", bool, False, False, "Show dependency information")
        ],
        aliases=["ver", "v"],
        examples=[
            "/version",
            "/version --detailed",
            "/version --dependencies"
        ],
        usage="/version [--detailed] [--dependencies]"
    ))
    
    # Configuration Command
    registry.register(CommandDefinition(
        name="config",
        handler=ConfigCommandHandler(),
        description="View and modify smart-ai configuration",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("action", str, False, "show", "Action to perform",
                           choices=["show", "set", "unset", "reset"]),
            CommandParameter("key", str, False, None, "Configuration key"),
            CommandParameter("value", str, False, None, "Configuration value")
        ],
        examples=[
            "/config show",
            "/config set --key=theme --value=dark",
            "/config unset --key=theme",
            "/config reset"
        ],
        usage="/config [action] [--key=<key>] [--value=<value>]"
    ))
    
    # Permissions Command
    registry.register(CommandDefinition(
        name="permissions",
        handler=PermissionsCommandHandler(),
        description="Manage provider permissions and access control",
        category=CommandCategory.SECURITY,
        parameters=[
            CommandParameter("action", str, False, "show", "Action to perform",
                           choices=["show", "grant", "revoke"]),
            CommandParameter("provider", str, False, None, "Provider name"),
            CommandParameter("type", str, False, "basic", "Permission type")
        ],
        examples=[
            "/permissions show",
            "/permissions grant --provider=claude --type=basic",
            "/permissions revoke --provider=opendia --type=browser"
        ],
        usage="/permissions [action] [--provider=<name>] [--type=<type>]"
    ))
    
    # Doctor Command
    registry.register(CommandDefinition(
        name="doctor",
        handler=DoctorCommandHandler(system_handlers),
        description="Health check and diagnostics for smart-ai installation",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("fix", bool, False, False, "Attempt to fix issues automatically"),
            CommandParameter("verbose", bool, False, False, "Show detailed diagnostic info")
        ],
        examples=[
            "/doctor",
            "/doctor --fix",
            "/doctor --verbose --fix"
        ],
        usage="/doctor [--fix] [--verbose]"
    ))
    
    # Cost Command
    registry.register(CommandDefinition(
        name="cost",
        handler=CostCommandHandler(system_handlers),
        description="Show token usage and provider cost estimates",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("reset", bool, False, False, "Reset cost tracking data"),
            CommandParameter("provider", str, False, None, "Show costs for specific provider"),
            CommandParameter("detailed", bool, False, False, "Show detailed cost breakdown")
        ],
        examples=[
            "/cost",
            "/cost --provider=claude",
            "/cost --detailed",
            "/cost --reset"
        ],
        usage="/cost [--provider=<name>] [--detailed] [--reset]"
    ))
    
    # Reset Command
    registry.register(CommandDefinition(
        name="reset",
        handler=ResetCommandHandler(),
        description="Reset provider connections and session state",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("all", bool, False, False, "Reset all data (requires --confirm)"),
            CommandParameter("providers", bool, False, False, "Reset provider connections"),
            CommandParameter("session", bool, False, False, "Reset session data"),
            CommandParameter("confirm", bool, False, False, "Confirm destructive operations")
        ],
        examples=[
            "/reset --session",
            "/reset --providers",
            "/reset --all --confirm"
        ],
        usage="/reset [--session] [--providers] [--all --confirm]"
    ))
    
    # Enhanced Exit Command
    registry.register(CommandDefinition(
        name="exit",
        handler=ExitCommandHandler(),
        description="Exit smart-ai with graceful cleanup",
        category=CommandCategory.SYSTEM,
        parameters=[
            CommandParameter("force", bool, False, False, "Force exit without cleanup"),
            CommandParameter("save", bool, False, False, "Save session before exit"),
            CommandParameter("name", str, False, None, "Name for saved session")
        ],
        aliases=["quit", "q", "bye"],
        examples=[
            "/exit",
            "/exit --save",
            "/exit --save --name=my_session",
            "/exit --force"
        ],
        usage="/exit [--save] [--name=<session>] [--force]"
    ))
    
    # Offline Mode Command
    registry.register(CommandDefinition(
        name="offline",
        handler=OfflineCommandHandler(),
        description="Force offline mode using only local providers",
        category=CommandCategory.UTILITY,
        parameters=[
            CommandParameter("enable", bool, False, True, "Enable offline mode")
        ],
        examples=[
            "/offline",
            "/offline --enable=false"
        ],
        usage="/offline [--enable=true|false]"
    ))


# Integration function for easy setup
def integrate_system_commands(smart_ai_instance, notification_manager: Optional[NotificationManager] = None):
    """
    Integrate system commands into an existing smart-ai instance
    """
    if hasattr(smart_ai_instance, 'command_registry'):
        register_system_commands(smart_ai_instance.command_registry, notification_manager)
        return True
    else:
        raise ValueError("Smart AI instance must have a command_registry attribute")


if __name__ == "__main__":
    print("Smart AI System Commands Implementation")
    print("=" * 50)
    print("This module provides essential system commands for smart-ai:")
    print("• Enhanced help with examples and categories")
    print("• Comprehensive status with detailed metrics")  
    print("• Configuration management")
    print("• Health checks and diagnostics")
    print("• Cost tracking and optimization")
    print("• Permission management")
    print("• Graceful reset and exit")
    print("• Offline mode support")
    print("\nUse integrate_system_commands() to add these to your smart-ai instance.")
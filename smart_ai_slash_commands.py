#!/usr/bin/env python3
"""
Smart AI Slash Commands System - Enhanced Production Version
A comprehensive slash command parser and registry for smart-ai CLI
Based on Claude Code research with enhanced provider integration and MCP support
"""

import re
import json
import asyncio
import shlex
import time
import subprocess
import yaml
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum
import argparse
import traceback
from functools import wraps


class CommandCategory(Enum):
    """Command categories for organization and help display"""
    SYSTEM = "system"
    SESSION = "session"
    PROVIDER = "provider"
    MCP = "mcp"
    DEVELOPMENT = "development"
    PROJECT = "project"
    TESTING = "testing"
    SECURITY = "security"
    UTILITY = "utility"
    CUSTOM = "custom"


@dataclass
class CommandParameter:
    """Represents a command parameter with validation"""
    name: str
    param_type: type = str
    required: bool = False
    default: Any = None
    description: str = ""
    choices: List[str] = field(default_factory=list)
    validator: Optional[Callable[[Any], bool]] = None
    help_text: str = ""


@dataclass
class CommandDefinition:
    """Defines a slash command with metadata"""
    name: str
    handler: Callable
    description: str
    category: CommandCategory
    parameters: List[CommandParameter] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    requires_internet: bool = False
    requires_project: bool = False
    usage: str = ""
    long_description: str = ""
    source: str = "builtin"  # builtin, project, user, mcp


@dataclass
class ParsedCommand:
    """Result of parsing a slash command"""
    command: str
    args: List[str]
    kwargs: Dict[str, Any]
    raw_input: str
    is_valid: bool = True
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class CommandExecutionContext:
    """Context passed to command handlers"""
    def __init__(self, smart_ai_instance, session_data: Dict[str, Any]):
        self.smart_ai = smart_ai_instance
        self.session_data = session_data
        self.execution_start = time.time()
        self.notifications_enabled = True
        self.debug_mode = False
        self.verbose = False
        
    @property
    def backend(self):
        """Access to SmartAI backend"""
        return getattr(self.smart_ai, 'backend', None)
    
    @property
    def current_provider(self):
        """Get current active provider"""
        return getattr(self.smart_ai, 'current_provider', 'claude_code')
    
    @property
    def project_root(self):
        """Get current project root directory"""
        return Path.cwd()
    
    def get_claude_config_dir(self):
        """Get .claude directory for project-specific configs"""
        return self.project_root / ".claude"
    
    def get_user_config_dir(self):
        """Get user's .claude directory"""
        return Path.home() / ".claude"


class SlashCommandParser:
    """Enhanced parser for slash commands with robust parameter validation"""
    
    COMMAND_PATTERN = re.compile(r'^/([a-zA-Z][a-zA-Z0-9_\-:]*)\s*(.*)')
    QUOTED_ARG_PATTERN = re.compile(r'''("[^"]*"|'[^']*'|\S+)''')
    MCP_COMMAND_PATTERN = re.compile(r'^/mcp__([^_]+)__(.+)')
    
    def __init__(self):
        self.namespace_separator = ":"
        self.mcp_prefix = "mcp__"
    
    def is_slash_command(self, input_text: str) -> bool:
        """Check if input is a slash command"""
        return input_text.strip().startswith('/')
    
    def is_mcp_command(self, input_text: str) -> bool:
        """Check if input is an MCP command"""
        return self.MCP_COMMAND_PATTERN.match(input_text.strip()) is not None
    
    def parse(self, input_text: str) -> ParsedCommand:
        """Parse slash command input into structured format"""
        input_text = input_text.strip()
        
        if not self.is_slash_command(input_text):
            return ParsedCommand(
                command="", args=[], kwargs={}, raw_input=input_text,
                is_valid=False, error_message="Not a slash command"
            )
        
        # Check for MCP command format
        mcp_match = self.MCP_COMMAND_PATTERN.match(input_text)
        if mcp_match:
            return self._parse_mcp_command(mcp_match, input_text)
        
        # Parse regular command
        match = self.COMMAND_PATTERN.match(input_text)
        if not match:
            return ParsedCommand(
                command="", args=[], kwargs={}, raw_input=input_text,
                is_valid=False, error_message="Invalid command format"
            )
        
        command_name = match.group(1)
        args_text = match.group(2).strip()
        
        return self._parse_arguments(command_name, args_text, input_text)
    
    def _parse_mcp_command(self, match, input_text: str) -> ParsedCommand:
        """Parse MCP command format: /mcp__server__tool [args]"""
        server_name = match.group(1)
        tool_and_args = match.group(2)
        
        # Split tool name and arguments
        parts = tool_and_args.split(' ', 1)
        tool_name = parts[0]
        args_text = parts[1] if len(parts) > 1 else ""
        
        command_name = f"{self.mcp_prefix}{server_name}__{tool_name}"
        return self._parse_arguments(command_name, args_text, input_text)
    
    def _parse_arguments(self, command_name: str, args_text: str, raw_input: str) -> ParsedCommand:
        """Parse command arguments using shlex for proper quoted string handling"""
        try:
            args = shlex.split(args_text) if args_text else []
        except ValueError as e:
            return ParsedCommand(
                command=command_name, args=[], kwargs={}, raw_input=raw_input,
                is_valid=False, error_message=f"Argument parsing error: {e}"
            )
        
        # Separate positional args from keyword args
        positional_args = []
        keyword_args = {}
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                # Long option format: --key=value or --key value
                if '=' in arg:
                    key, value = arg[2:].split('=', 1)
                    keyword_args[key] = self._convert_value(value)
                else:
                    key = arg[2:]
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        keyword_args[key] = self._convert_value(args[i + 1])
                        i += 1
                    else:
                        keyword_args[key] = True
            elif arg.startswith('-') and len(arg) > 1:
                # Short option format: -k value or -k
                key = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    keyword_args[key] = self._convert_value(args[i + 1])
                    i += 1
                else:
                    keyword_args[key] = True
            else:
                positional_args.append(arg)
            i += 1
        
        return ParsedCommand(
            command=command_name,
            args=positional_args,
            kwargs=keyword_args,
            raw_input=raw_input,
            is_valid=True
        )
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def validate_parameters(self, parsed_cmd: ParsedCommand, 
                          command_def: CommandDefinition) -> ParsedCommand:
        """Validate parsed command against command definition"""
        if not parsed_cmd.is_valid:
            return parsed_cmd
        
        errors = []
        warnings = []
        validated_kwargs = {}
        
        # Check required parameters
        for param in command_def.parameters:
            value = None
            
            # Get value from positional args if available
            param_index = next(
                (i for i, p in enumerate(command_def.parameters) if p.name == param.name),
                None
            )
            if param_index is not None and param_index < len(parsed_cmd.args):
                value = parsed_cmd.args[param_index]
            
            # Override with keyword arg if present
            if param.name in parsed_cmd.kwargs:
                value = parsed_cmd.kwargs[param.name]
            
            # Use default if no value provided
            if value is None:
                if param.required:
                    errors.append(f"Required parameter '{param.name}' missing")
                    continue
                value = param.default
            
            # Type conversion and validation
            if value is not None:
                try:
                    # Type conversion
                    if param.param_type == bool and not isinstance(value, bool):
                        value = str(value).lower() in ('true', '1', 'yes', 'on')
                    elif param.param_type == int and not isinstance(value, int):
                        value = int(value)
                    elif param.param_type == float and not isinstance(value, float):
                        value = float(value)
                    elif param.param_type == str and not isinstance(value, str):
                        value = str(value)
                    
                    # Choice validation
                    if param.choices and value not in param.choices:
                        errors.append(
                            f"Parameter '{param.name}' must be one of: {', '.join(map(str, param.choices))}"
                        )
                        continue
                    
                    # Custom validator
                    if param.validator and not param.validator(value):
                        errors.append(f"Parameter '{param.name}' failed validation")
                        continue
                    
                    validated_kwargs[param.name] = value
                    
                except (ValueError, TypeError) as e:
                    errors.append(f"Parameter '{param.name}' type error: {e}")
        
        # Check for unknown parameters
        known_params = {p.name for p in command_def.parameters}
        for key in parsed_cmd.kwargs:
            if key not in known_params:
                warnings.append(f"Unknown parameter '{key}' ignored")
        
        if errors:
            parsed_cmd.is_valid = False
            parsed_cmd.error_message = "; ".join(errors)
        else:
            parsed_cmd.kwargs = validated_kwargs
            parsed_cmd.warnings = warnings
        
        return parsed_cmd


class CommandRegistry:
    """Enhanced registry for managing slash commands with categories and discovery"""
    
    def __init__(self):
        self.commands: Dict[str, CommandDefinition] = {}
        self.aliases: Dict[str, str] = {}
        self.categories: Dict[CommandCategory, List[str]] = {}
        self.mcp_commands: Dict[str, CommandDefinition] = {}
        self.custom_commands_cache: Dict[str, Dict] = {}
        
        # Initialize categories
        for category in CommandCategory:
            self.categories[category] = []
    
    def register(self, command_def: CommandDefinition):
        """Register a new command"""
        # Register main command
        self.commands[command_def.name] = command_def
        self.categories[command_def.category].append(command_def.name)
        
        # Register aliases
        for alias in command_def.aliases:
            self.aliases[alias] = command_def.name
    
    def register_mcp_command(self, server_name: str, tool_name: str, command_def: CommandDefinition):
        """Register an MCP command"""
        mcp_key = f"mcp__{server_name}__{tool_name}"
        command_def.name = mcp_key
        self.mcp_commands[mcp_key] = command_def
    
    def load_custom_commands(self, commands_dir: Path):
        """Load custom commands from markdown files"""
        if not commands_dir.exists():
            return
        
        for cmd_file in commands_dir.glob("*.md"):
            try:
                self._load_command_file(cmd_file)
            except Exception as e:
                print(f"Warning: Failed to load command {cmd_file}: {e}")
    
    def _load_command_file(self, cmd_file: Path):
        """Load a single command file"""
        content = cmd_file.read_text()
        
        # Parse frontmatter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                command_content = parts[2].strip()
            else:
                frontmatter = {}
                command_content = content
        else:
            frontmatter = {}
            command_content = content
        
        # Create command definition
        cmd_name = frontmatter.get('name', cmd_file.stem)
        description = frontmatter.get('description', f"Custom command: {cmd_name}")
        category = CommandCategory(frontmatter.get('category', 'custom'))
        
        # Create handler for custom command
        handler = CustomCommandHandler(command_content, frontmatter)
        
        command_def = CommandDefinition(
            name=cmd_name,
            handler=handler,
            description=description,
            category=category,
            source="project" if ".claude/commands" in str(cmd_file) else "user",
            long_description=command_content
        )
        
        self.register(command_def)
    
    def get_command(self, name: str) -> Optional[CommandDefinition]:
        """Get command definition by name or alias"""
        # Check aliases first
        if name in self.aliases:
            name = self.aliases[name]
        
        # Check regular commands
        if name in self.commands:
            return self.commands[name]
        
        # Check MCP commands
        if name in self.mcp_commands:
            return self.mcp_commands[name]
        
        return None
    
    def list_commands(self, category: Optional[CommandCategory] = None, 
                     include_mcp: bool = True) -> List[CommandDefinition]:
        """List all commands, optionally filtered by category"""
        commands = []
        
        if category:
            command_names = self.categories.get(category, [])
            commands.extend([self.commands[name] for name in command_names])
        else:
            commands.extend(list(self.commands.values()))
        
        if include_mcp:
            commands.extend(list(self.mcp_commands.values()))
        
        return commands
    
    def search_commands(self, query: str) -> List[CommandDefinition]:
        """Search commands by name or description"""
        query = query.lower()
        results = []
        
        all_commands = {**self.commands, **self.mcp_commands}
        for cmd in all_commands.values():
            if (query in cmd.name.lower() or 
                query in cmd.description.lower() or
                any(query in alias.lower() for alias in cmd.aliases)):
                results.append(cmd)
        
        return results
    
    def get_command_help(self, command_name: str) -> str:
        """Generate detailed help text for a specific command"""
        cmd = self.get_command(command_name)
        if not cmd:
            return f"Command '{command_name}' not found."
        
        help_text = [
            f"Command: /{cmd.name}",
            f"Category: {cmd.category.value}",
            f"Source: {cmd.source}",
            f"Description: {cmd.description}",
        ]
        
        if cmd.long_description:
            help_text.append(f"\nDetails:\n{cmd.long_description}")
        
        if cmd.aliases:
            help_text.append(f"\nAliases: {', '.join('/' + alias for alias in cmd.aliases)}")
        
        if cmd.usage:
            help_text.append(f"\nUsage: {cmd.usage}")
        
        if cmd.parameters:
            help_text.append("\nParameters:")
            for param in cmd.parameters:
                param_info = f"  {param.name}"
                if param.param_type != str:
                    param_info += f" ({param.param_type.__name__})"
                if param.required:
                    param_info += " [required]"
                if param.default is not None:
                    param_info += f" [default: {param.default}]"
                if param.choices:
                    param_info += f" [choices: {', '.join(map(str, param.choices))}]"
                if param.description:
                    param_info += f" - {param.description}"
                help_text.append(param_info)
        
        if cmd.examples:
            help_text.append("\nExamples:")
            for example in cmd.examples:
                help_text.append(f"  {example}")
        
        return "\n".join(help_text)


class BaseCommandHandler(ABC):
    """Base class for command handlers with enhanced logging and error handling"""
    
    @abstractmethod
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        """Execute the command and return result"""
        pass
    
    def show_progress(self, message: str, context: CommandExecutionContext):
        """Show progress message if notifications enabled"""
        if context.notifications_enabled:
            print(f"🔄 {message}")
    
    def show_success(self, message: str, context: CommandExecutionContext):
        """Show success message"""
        if context.notifications_enabled:
            print(f"✅ {message}")
    
    def show_error(self, message: str, context: CommandExecutionContext):
        """Show error message"""
        if context.notifications_enabled:
            print(f"❌ {message}")
    
    def show_warning(self, message: str, context: CommandExecutionContext):
        """Show warning message"""
        if context.notifications_enabled:
            print(f"⚠️ {message}")
    
    def show_info(self, message: str, context: CommandExecutionContext):
        """Show info message"""
        if context.notifications_enabled:
            print(f"ℹ️ {message}")


# Enhanced Command Handlers

class HelpCommandHandler(BaseCommandHandler):
    """Enhanced handler for /help command with better formatting"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        query = parsed_cmd.kwargs.get('query') or (parsed_cmd.args[0] if parsed_cmd.args else None)
        category = parsed_cmd.kwargs.get('category')
        search = parsed_cmd.kwargs.get('search')
        
        registry = context.smart_ai.command_registry
        
        if query:
            return registry.get_command_help(query)
        
        if search:
            commands = registry.search_commands(search)
            if not commands:
                return f"No commands found matching '{search}'"
            
            help_text = [f"Commands matching '{search}':", "=" * 30]
            for cmd in commands:
                help_text.append(f"  /{cmd.name} - {cmd.description}")
            return "\n".join(help_text)
        
        # Show general help
        help_text = [
            "Smart AI Slash Commands",
            "=" * 30,
            "",
            "Smart AI provides a comprehensive slash command system inspired by Claude Code.",
            "Commands are organized by category and support both built-in and custom commands.",
            ""
        ]
        
        if category:
            try:
                cat_enum = CommandCategory(category)
                commands = registry.list_commands(cat_enum)
                help_text.append(f"{cat_enum.value.title()} Commands:")
                help_text.append("-" * 20)
            except ValueError:
                return f"Invalid category: {category}. Valid categories: {', '.join(c.value for c in CommandCategory)}"
        else:
            commands = registry.list_commands()
            
        # Group by category
        for category_enum in CommandCategory:
            category_commands = [cmd for cmd in commands if cmd.category == category_enum]
            if category_commands:
                help_text.append(f"\n{category_enum.value.title()}:")
                for cmd in sorted(category_commands, key=lambda x: x.name):
                    aliases_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    source_str = f" [{cmd.source}]" if cmd.source != "builtin" else ""
                    help_text.append(f"  /{cmd.name}{aliases_str}{source_str} - {cmd.description}")
        
        help_text.extend([
            "",
            "Usage:",
            "  /command [arguments] [--option=value]",
            "  /help <command>                    # Detailed help for specific command",
            "  /help --category=<category>        # Filter by category", 
            "  /help --search=<term>              # Search commands",
            "",
            "Custom Commands:",
            "  Project commands: .claude/commands/*.md",
            "  User commands: ~/.claude/commands/*.md",
            "",
            "MCP Commands:",
            "  Format: /mcp__<server>__<tool> [args]",
            "  Use /mcp to list available MCP tools"
        ])
        
        return "\n".join(help_text)


class StatusCommandHandler(BaseCommandHandler):
    """Enhanced handler for /status command with detailed system information"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        backend = context.backend
        verbose = parsed_cmd.kwargs.get('verbose', False)
        
        status_lines = [
            "Smart AI System Status",
            "=" * 25,
            f"Current Provider: {context.current_provider}",
            f"Session Duration: {time.time() - context.session_data.get('session_start', time.time()):.1f}s",
            f"Requests Count: {context.session_data.get('requests_count', 0)}",
            f"Project Root: {context.project_root}",
        ]
        
        if backend:
            # Provider availability
            status_lines.append("\nProvider Status:")
            for provider in backend.providers:
                available = backend._check_provider_availability(provider)
                status_lines.append(f"  {provider}: {'✅ Available' if available else '❌ Unavailable'}")
            
            # MCP Status
            if backend.mcp_manager:
                status_lines.append(f"\nMCP Status:")
                status_lines.append(f"  Tools Available: {len(backend.mcp_manager.tools)}")
                if verbose:
                    for tool_name in sorted(backend.mcp_manager.tools.keys()):
                        status_lines.append(f"    - {tool_name}")
            
            # Internet connectivity
            internet = backend._check_internet_connectivity()
            status_lines.append(f"\nConnectivity:")
            status_lines.append(f"  Internet: {'✅ Connected' if internet else '🔒 Offline'}")
        
        # Command registry status
        registry = context.smart_ai.command_registry
        total_commands = len(registry.commands) + len(registry.mcp_commands)
        status_lines.append(f"\nCommand Registry:")
        status_lines.append(f"  Total Commands: {total_commands}")
        status_lines.append(f"  Built-in: {len([c for c in registry.commands.values() if c.source == 'builtin'])}")
        status_lines.append(f"  Custom: {len([c for c in registry.commands.values() if c.source != 'builtin'])}")
        status_lines.append(f"  MCP: {len(registry.mcp_commands)}")
        
        # Project status
        claude_dir = context.get_claude_config_dir()
        user_claude_dir = context.get_user_config_dir()
        
        status_lines.append(f"\nConfiguration:")
        status_lines.append(f"  Project .claude dir: {'✅ Exists' if claude_dir.exists() else '❌ Missing'}")
        status_lines.append(f"  User .claude dir: {'✅ Exists' if user_claude_dir.exists() else '❌ Missing'}")
        
        if verbose:
            # Memory usage
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            status_lines.append(f"\nSystem Resources:")
            status_lines.append(f"  Memory Usage: {memory_mb:.1f} MB")
        
        return "\n".join(status_lines)


class ProviderCommandHandler(BaseCommandHandler):
    """Enhanced handler for provider switching commands"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        provider = parsed_cmd.command
        prompt = " ".join(parsed_cmd.args) if parsed_cmd.args else None
        backend = context.backend
        
        if not backend:
            return "Backend not available"
        
        # Map command names to providers
        provider_map = {
            'claude': 'claude_code',
            'gemma': 'gemma',
            'treequest': 'treequest',
            'opendia': 'opendia',
            'mcp': 'mcp'
        }
        
        target_provider = provider_map.get(provider, provider)
        
        if target_provider not in backend.providers:
            return f"Unknown provider: {target_provider}"
        
        if not backend._check_provider_availability(target_provider):
            return f"Provider {target_provider} is not available"
        
        # Switch provider
        context.smart_ai.current_provider = target_provider
        self.show_success(f"Switched to {target_provider}", context)
        
        # If prompt provided, execute it with the new provider
        if prompt:
            self.show_progress(f"Executing with {target_provider}: {prompt[:50]}...", context)
            try:
                response = await backend.process_request_async(prompt, target_provider)
                if response:
                    clean_output = backend.get_clean_output(response)
                    return f"Provider: {target_provider}\n\n{clean_output}"
                else:
                    return f"No response from {target_provider}"
            except Exception as e:
                return f"Error executing with {target_provider}: {e}"
        
        return f"Now using provider: {target_provider}"


class ProjectCommandHandler(BaseCommandHandler):
    """Handler for project management commands"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.args[0] if parsed_cmd.args else 'status'
        
        if action == 'init':
            return await self._init_project(context)
        elif action == 'status':
            return await self._project_status(context)
        elif action == 'config':
            return await self._project_config(parsed_cmd, context)
        elif action == 'memory':
            return await self._manage_memory(parsed_cmd, context)
        else:
            return f"Unknown project action: {action}. Available: init, status, config, memory"
    
    async def _init_project(self, context: CommandExecutionContext) -> str:
        """Initialize project with .claude directory and CLAUDE.md"""
        claude_dir = context.get_claude_config_dir()
        
        if claude_dir.exists():
            return f"Project already initialized at {claude_dir}"
        
        # Create .claude directory structure
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "commands").mkdir(exist_ok=True)
        (claude_dir / "memory").mkdir(exist_ok=True)
        
        # Create CLAUDE.md template
        claude_md = context.project_root / "CLAUDE.md"
        if not claude_md.exists():
            template = """# Claude Code Instructions

## Project Context
Brief description of your project and its goals.

## Development Guidelines
- Coding standards and conventions
- Testing requirements
- Documentation expectations

## AI Collaboration Preferences
- Preferred communication style
- How to handle ambiguous requirements
- Review and approval processes

## Essential Commands
List your most frequently used slash commands and workflows.
"""
            claude_md.write_text(template)
        
        return f"✅ Project initialized at {claude_dir}\n📄 Created CLAUDE.md template"
    
    async def _project_status(self, context: CommandExecutionContext) -> str:
        """Show project status"""
        claude_dir = context.get_claude_config_dir()
        claude_md = context.project_root / "CLAUDE.md"
        
        status = [
            f"Project Root: {context.project_root}",
            f".claude Directory: {'✅ Exists' if claude_dir.exists() else '❌ Missing'}",
            f"CLAUDE.md: {'✅ Exists' if claude_md.exists() else '❌ Missing'}",
        ]
        
        if claude_dir.exists():
            commands_dir = claude_dir / "commands"
            memory_dir = claude_dir / "memory"
            
            custom_commands = len(list(commands_dir.glob("*.md"))) if commands_dir.exists() else 0
            memory_files = len(list(memory_dir.glob("*.md"))) if memory_dir.exists() else 0
            
            status.extend([
                f"Custom Commands: {custom_commands}",
                f"Memory Files: {memory_files}"
            ])
        
        return "\n".join(status)
    
    async def _project_config(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        """Manage project configuration"""
        # TODO: Implement project config management
        return "Project config management coming soon"
    
    async def _manage_memory(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        """Manage project memory files"""
        # TODO: Implement memory management
        return "Memory management coming soon"


class MCPCommandHandler(BaseCommandHandler):
    """Enhanced handler for MCP tool commands"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        backend = context.backend
        if not backend:
            return "Backend not available"
        
        # Initialize MCP manager if needed
        await backend._initialize_mcp_manager()
        
        if not backend.mcp_manager:
            return "MCP tools not available"
        
        if not parsed_cmd.args:
            return await self._list_mcp_tools(backend)
        
        # Execute specific MCP tool
        tool_name = parsed_cmd.args[0]
        prompt = " ".join(parsed_cmd.args[1:]) if len(parsed_cmd.args) > 1 else ""
        
        if not prompt and not parsed_cmd.kwargs:
            # Show tool details
            return await self._show_tool_details(tool_name, backend)
        
        self.show_progress(f"Executing MCP tool: {tool_name}", context)
        
        try:
            result = await backend._execute_mcp_tool(tool_name, prompt)
            return result
        except Exception as e:
            self.show_error(f"MCP tool execution failed: {e}", context)
            return f"❌ MCP tool execution error: {e}"
    
    async def _list_mcp_tools(self, backend) -> str:
        """List available MCP tools"""
        tools = list(backend.mcp_manager.tools.keys())
        if not tools:
            return "No MCP tools available"
        
        lines = ["Available MCP Tools:", "=" * 20]
        for tool_name in sorted(tools):
            tool = backend.mcp_manager.tools[tool_name]
            category = getattr(tool, 'category', 'unknown')
            description = getattr(tool, 'description', 'No description')
            lines.append(f"  {tool_name} [{category}] - {description}")
        
        lines.extend([
            "",
            "Usage:",
            "  /mcp <tool-name> <prompt>     # Execute tool with prompt",
            "  /mcp <tool-name>              # Show tool details",
            "  /mcp                          # List all tools"
        ])
        
        return "\n".join(lines)
    
    async def _show_tool_details(self, tool_name: str, backend) -> str:
        """Show details for a specific MCP tool"""
        tool = backend.mcp_manager.tools.get(tool_name)
        if not tool:
            return f"MCP tool '{tool_name}' not found"
        
        details = [
            f"MCP Tool: {tool_name}",
            "=" * (len(tool_name) + 10),
            f"Category: {getattr(tool, 'category', 'unknown')}",
            f"Description: {getattr(tool, 'description', 'No description')}",
        ]
        
        # Add tool-specific information if available
        if hasattr(tool, 'parameters'):
            details.append("\nParameters:")
            for param in tool.parameters:
                details.append(f"  {param}")
        
        return "\n".join(details)


class CustomCommandHandler(BaseCommandHandler):
    """Handler for custom commands loaded from markdown files"""
    
    def __init__(self, content: str, frontmatter: dict):
        self.content = content
        self.frontmatter = frontmatter
        self.pre_execution_commands = []
        
        # Parse pre-execution commands (lines starting with !)
        lines = content.split('\n')
        self.command_content = []
        for line in lines:
            if line.strip().startswith('!'):
                self.pre_execution_commands.append(line[1:].strip())
            else:
                self.command_content.append(line)
        
        self.command_content = '\n'.join(self.command_content).strip()
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        # Execute pre-execution commands
        for cmd in self.pre_execution_commands:
            try:
                self.show_progress(f"Executing: {cmd}", context)
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.show_warning(f"Pre-command failed: {result.stderr.strip()}", context)
            except Exception as e:
                self.show_warning(f"Pre-command error: {e}", context)
        
        # Replace placeholders in content
        final_content = self.command_content
        
        # Replace $ARGUMENTS with provided arguments
        if parsed_cmd.args:
            final_content = final_content.replace('$ARGUMENTS', ' '.join(parsed_cmd.args))
        
        # Replace @filename references with file contents
        import re
        file_refs = re.findall(r'@([^\s]+)', final_content)
        for file_ref in file_refs:
            try:
                file_path = Path(file_ref)
                if file_path.exists():
                    file_content = file_path.read_text()
                    final_content = final_content.replace(f'@{file_ref}', file_content)
                else:
                    final_content = final_content.replace(f'@{file_ref}', f'[File not found: {file_ref}]')
            except Exception as e:
                final_content = final_content.replace(f'@{file_ref}', f'[Error reading {file_ref}: {e}]')
        
        # Execute the content as a prompt with the current provider
        if context.backend:
            provider = context.backend.handle_provider_fallback(prompt=final_content)
            if provider:
                try:
                    response = await context.backend.process_request_async(final_content, provider)
                    if response:
                        return context.backend.get_clean_output(response)
                    else:
                        return "No response from provider"
                except Exception as e:
                    return f"Error executing custom command: {e}"
            else:
                return "No providers available for custom command"
        else:
            return f"Custom command content:\n{final_content}"


def command_error_handler(func):
    """Decorator for handling command execution errors"""
    @wraps(func)
    async def wrapper(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        try:
            return await func(self, parsed_cmd, context)
        except Exception as e:
            if context.debug_mode:
                traceback.print_exc()
            return f"❌ Command error: {e}"
    return wrapper


class SlashCommandSystem:
    """Enhanced main slash command system coordinator"""
    
    def __init__(self, smart_ai_instance):
        self.smart_ai = smart_ai_instance
        self.parser = SlashCommandParser()
        self.registry = CommandRegistry()
        self.session_data = getattr(smart_ai_instance, 'session_data', {'session_start': time.time()})
        
        # Load custom commands
        self._load_custom_commands()
        
        # Register built-in commands
        self._register_builtin_commands()
        
        # Store registry in smart_ai instance for access by handlers
        self.smart_ai.command_registry = self.registry
    
    def _load_custom_commands(self):
        """Load custom commands from project and user directories"""
        # Load project commands
        project_commands_dir = Path.cwd() / ".claude" / "commands"
        if project_commands_dir.exists():
            self.registry.load_custom_commands(project_commands_dir)
        
        # Load user commands
        user_commands_dir = Path.home() / ".claude" / "commands"
        if user_commands_dir.exists():
            self.registry.load_custom_commands(user_commands_dir)
    
    def _register_builtin_commands(self):
        """Register all built-in slash commands"""
        
        # Help command with enhanced features
        self.registry.register(CommandDefinition(
            name="help",
            handler=HelpCommandHandler(),
            description="Show help for commands",
            category=CommandCategory.SYSTEM,
            parameters=[
                CommandParameter("query", str, False, None, "Command to get help for"),
                CommandParameter("category", str, False, None, "Filter by category", 
                               choices=[c.value for c in CommandCategory]),
                CommandParameter("search", str, False, None, "Search commands by keyword")
            ],
            aliases=["h", "?"],
            examples=["/help", "/help status", "/help --category=provider", "/help --search=session"],
            usage="/help [command] [--category=<cat>] [--search=<term>]"
        ))
        
        # Enhanced status command
        self.registry.register(CommandDefinition(
            name="status",
            handler=StatusCommandHandler(),
            description="Show comprehensive system status and provider information",
            category=CommandCategory.SYSTEM,
            parameters=[
                CommandParameter("verbose", bool, False, False, "Show detailed information")
            ],
            aliases=["stat", "info"],
            examples=["/status", "/status --verbose"],
            usage="/status [--verbose]"
        ))
        
        # Provider switching commands
        for provider_name in ["claude", "gemma", "treequest", "opendia", "mcp"]:
            self.registry.register(CommandDefinition(
                name=provider_name,
                handler=ProviderCommandHandler(),
                description=f"Switch to {provider_name} provider and optionally execute prompt",
                category=CommandCategory.PROVIDER,
                parameters=[
                    CommandParameter("prompt", str, False, None, "Optional prompt to execute")
                ],
                examples=[f"/{provider_name}", f"/{provider_name} What is Python?"],
                usage=f"/{provider_name} [prompt]"
            ))
        
        # Clear command
        self.registry.register(CommandDefinition(
            name="clear",
            handler=ClearCommandHandler(),
            description="Clear terminal and optionally session data",
            category=CommandCategory.UTILITY,
            parameters=[
                CommandParameter("session", bool, False, False, "Also clear session data")
            ],
            aliases=["cls"],
            examples=["/clear", "/clear --session"],
            usage="/clear [--session]"
        ))
        
        # Session management
        self.registry.register(CommandDefinition(
            name="session",
            handler=SessionCommandHandler(),
            description="Manage sessions (save/load/list/delete)",
            category=CommandCategory.SESSION,
            parameters=[
                CommandParameter("action", str, True, None, "Action to perform", 
                               ["save", "load", "list", "delete", "info"]),
                CommandParameter("name", str, False, None, "Session name for save/load/delete")
            ],
            examples=["/session save my_session", "/session load my_session", "/session list"],
            usage="/session <action> [name]"
        ))
        
        # Project management
        self.registry.register(CommandDefinition(
            name="project",
            handler=ProjectCommandHandler(),
            description="Manage project configuration and initialization",
            category=CommandCategory.PROJECT,
            parameters=[
                CommandParameter("action", str, False, "status", "Action to perform",
                               ["init", "status", "config", "memory"])
            ],
            aliases=["proj"],
            examples=["/project init", "/project status", "/project config"],
            usage="/project [action]",
            requires_project=False
        ))
        
        # Enhanced MCP tools
        self.registry.register(CommandDefinition(
            name="mcp",
            handler=MCPCommandHandler(),
            description="Execute MCP tools or list available tools",
            category=CommandCategory.MCP,
            parameters=[
                CommandParameter("tool", str, False, None, "MCP tool name"),
                CommandParameter("prompt", str, False, None, "Prompt for the tool")
            ],
            examples=["/mcp", "/mcp task-master list", "/mcp filesystem read /path/to/file"],
            usage="/mcp [tool] [prompt]",
            requires_internet=True
        ))
        
        # Version command
        self.registry.register(CommandDefinition(
            name="version",
            handler=VersionCommandHandler(),
            description="Show Smart AI version information",
            category=CommandCategory.SYSTEM,
            aliases=["ver", "v"],
            examples=["/version"],
            usage="/version"
        ))
        
        # Exit command
        self.registry.register(CommandDefinition(
            name="exit",
            handler=ExitCommandHandler(),
            description="Exit Smart AI interactive mode",
            category=CommandCategory.SYSTEM,
            aliases=["quit", "q"],
            examples=["/exit"],
            usage="/exit"
        ))
    
    async def process_command(self, input_text: str) -> Tuple[bool, str]:
        """
        Enhanced command processing with better error handling and logging
        Returns (was_command, result)
        """
        if not self.parser.is_slash_command(input_text):
            return False, ""
        
        try:
            # Parse command
            parsed_cmd = self.parser.parse(input_text)
            if not parsed_cmd.is_valid:
                return True, f"❌ Command parsing error: {parsed_cmd.error_message}"
            
            # Get command definition
            command_def = self.registry.get_command(parsed_cmd.command)
            if not command_def:
                suggestions = self.get_command_suggestions(parsed_cmd.command)
                error_msg = f"❌ Unknown command: /{parsed_cmd.command}"
                if suggestions:
                    error_msg += f"\nDid you mean: {', '.join(suggestions)}"
                error_msg += "\nType '/help' for available commands"
                return True, error_msg
            
            # Validate parameters
            parsed_cmd = self.parser.validate_parameters(parsed_cmd, command_def)
            if not parsed_cmd.is_valid:
                return True, f"❌ Parameter error: {parsed_cmd.error_message}\nType '/help {parsed_cmd.command}' for usage"
            
            # Show warnings if any
            if parsed_cmd.warnings:
                for warning in parsed_cmd.warnings:
                    print(f"⚠️ {warning}")
            
            # Create execution context
            context = CommandExecutionContext(self.smart_ai, self.session_data)
            
            # Check requirements
            if command_def.requires_internet and not self._check_internet():
                return True, f"❌ Command /{parsed_cmd.command} requires internet connection"
            
            if command_def.requires_project and not self._check_project():
                return True, f"❌ Command /{parsed_cmd.command} requires a project context"
            
            # Execute command
            result = await command_def.handler.execute(parsed_cmd, context)
            
            # Log execution time if verbose
            execution_time = time.time() - context.execution_start
            if context.verbose:
                result += f"\n\n⏱️ Execution time: {execution_time:.2f}s"
            
            return True, result
            
        except Exception as e:
            error_msg = f"❌ Command execution error: {e}"
            if getattr(self.session_data, 'debug_mode', False):
                import traceback
                error_msg += f"\n\nDebug trace:\n{traceback.format_exc()}"
            return True, error_msg
    
    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions for typos or partial matches"""
        suggestions = []
        
        # Exact prefix matches
        for cmd_name in self.registry.commands.keys():
            if cmd_name.startswith(partial_command):
                suggestions.append(f"/{cmd_name}")
        
        # Fuzzy matching for typos
        import difflib
        all_commands = list(self.registry.commands.keys()) + list(self.registry.aliases.keys())
        close_matches = difflib.get_close_matches(partial_command, all_commands, n=3, cutoff=0.6)
        for match in close_matches:
            if f"/{match}" not in suggestions:
                suggestions.append(f"/{match}")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _check_internet(self) -> bool:
        """Check if internet is available"""
        backend = getattr(self.smart_ai, 'backend', None)
        if backend:
            return backend._check_internet_connectivity()
        return True  # Assume available if can't check
    
    def _check_project(self) -> bool:
        """Check if we're in a project context"""
        # Check for common project indicators
        project_files = ['.git', 'package.json', 'requirements.txt', 'Cargo.toml', 'setup.py', 'Makefile']
        return any(Path(f).exists() for f in project_files)
    
    def get_command_suggestions_for_autocomplete(self, partial_input: str) -> List[str]:
        """Get command suggestions for autocomplete"""
        if not partial_input.startswith('/'):
            return []
        
        partial_command = partial_input[1:].lower()
        suggestions = []
        
        # Regular commands
        for cmd_name in self.registry.commands.keys():
            if cmd_name.lower().startswith(partial_command):
                suggestions.append(f"/{cmd_name}")
        
        # Aliases
        for alias, cmd_name in self.registry.aliases.items():
            if alias.lower().startswith(partial_command):
                suggestions.append(f"/{alias}")
        
        # MCP commands
        for mcp_cmd in self.registry.mcp_commands.keys():
            if mcp_cmd.lower().startswith(partial_command):
                suggestions.append(f"/{mcp_cmd}")
        
        return sorted(suggestions)[:10]  # Limit to 10 suggestions


class ExitCommandHandler(BaseCommandHandler):
    """Handler for /exit command"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        # Set exit flag on smart_ai instance
        context.smart_ai.should_exit = True
        return "👋 Goodbye!"


class ClearCommandHandler(BaseCommandHandler):
    """Enhanced handler for /clear command"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        # Clear terminal
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Reset session if requested
        if parsed_cmd.kwargs.get('session'):
            context.session_data.clear()
            context.session_data['session_start'] = time.time()
            self.show_info("Session data cleared", context)
        
        return "Terminal cleared"


class SessionCommandHandler(BaseCommandHandler):
    """Enhanced handler for session management commands"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        action = parsed_cmd.kwargs.get('action', parsed_cmd.args[0] if parsed_cmd.args else 'info')
        name = parsed_cmd.kwargs.get('name') or (parsed_cmd.args[1] if len(parsed_cmd.args) > 1 else None)
        
        if action == 'save':
            if not name:
                name = f"session_{int(time.time())}"
            return await self._save_session(name, context)
        elif action == 'load':
            if not name:
                return "Session name required for load"
            return await self._load_session(name, context)
        elif action == 'list':
            return await self._list_sessions(context)
        elif action == 'delete':
            if not name:
                return "Session name required for delete"
            return await self._delete_session(name, context)
        else:
            return self._session_info(context)
    
    async def _save_session(self, name: str, context: CommandExecutionContext) -> str:
        sessions_dir = Path.home() / ".smart-ai" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        session_file = sessions_dir / f"{name}.json"
        session_data = {
            'timestamp': time.time(),
            'session_data': context.session_data,
            'current_provider': context.current_provider,
            'project_root': str(context.project_root),
            'version': '1.0'
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return f"✅ Session saved as '{name}'"
    
    async def _load_session(self, name: str, context: CommandExecutionContext) -> str:
        sessions_dir = Path.home() / ".smart-ai" / "sessions"
        session_file = sessions_dir / f"{name}.json"
        
        if not session_file.exists():
            return f"❌ Session '{name}' not found"
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            context.session_data.update(session_data.get('session_data', {}))
            context.smart_ai.current_provider = session_data.get('current_provider', 'claude_code')
            
            return f"✅ Session '{name}' loaded"
        except Exception as e:
            return f"❌ Error loading session: {e}"
    
    async def _list_sessions(self, context: CommandExecutionContext) -> str:
        sessions_dir = Path.home() / ".smart-ai" / "sessions"
        if not sessions_dir.exists():
            return "No saved sessions"
        
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                timestamp = data.get('timestamp', 0)
                project = data.get('project_root', 'Unknown')
                provider = data.get('current_provider', 'Unknown')
                sessions.append((session_file.stem, timestamp, project, provider))
            except:
                continue
        
        if not sessions:
            return "No saved sessions"
        
        sessions.sort(key=lambda x: x[1], reverse=True)
        lines = ["Saved Sessions:", "=" * 15]
        for name, timestamp, project, provider in sessions:
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
            lines.append(f"  {name}")
            lines.append(f"    Time: {time_str}")
            lines.append(f"    Provider: {provider}")
            lines.append(f"    Project: {Path(project).name}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def _delete_session(self, name: str, context: CommandExecutionContext) -> str:
        sessions_dir = Path.home() / ".smart-ai" / "sessions"
        session_file = sessions_dir / f"{name}.json"
        
        if not session_file.exists():
            return f"❌ Session '{name}' not found"
        
        session_file.unlink()
        return f"✅ Session '{name}' deleted"
    
    def _session_info(self, context: CommandExecutionContext) -> str:
        duration = time.time() - context.session_data.get('session_start', time.time())
        return f"Current session: {context.session_data.get('requests_count', 0)} requests, {duration:.1f}s duration"


class VersionCommandHandler(BaseCommandHandler):
    """Enhanced handler for /version command"""
    
    async def execute(self, parsed_cmd: ParsedCommand, context: CommandExecutionContext) -> str:
        version_info = [
            "Smart AI Enhanced v2.0.0",
            "=" * 25,
            "Features:",
            "  ✅ Comprehensive slash command system",
            "  ✅ Multiple AI provider support", 
            "  ✅ MCP tool integration",
            "  ✅ Custom command support",
            "  ✅ Session management",
            "  ✅ Project initialization",
            "",
            "Supported Providers:",
            "  - Claude Code (Anthropic)",
            "  - TreeQuest (Multi-provider)",
            "  - Gemma (Local via Ollama)",
            "  - OpenDia (Browser automation)",
            "  - MCP Tools (Extensible)",
            "",
            f"Python: {context.smart_ai.__class__.__module__}",
            f"Project: {context.project_root.name}"
        ]
        
        return "\n".join(version_info)


# Integration helper functions

def integrate_slash_commands_with_smart_ai(smart_ai_instance):
    """
    Integrate enhanced slash command system with existing SmartAI instance
    """
    # Create slash command system
    slash_system = SlashCommandSystem(smart_ai_instance)
    smart_ai_instance.slash_commands = slash_system
    smart_ai_instance.should_exit = False
    
    # Store original process method if it exists
    original_process = getattr(smart_ai_instance, '_process_interactive_with_backend', None)
    
    async def enhanced_process_interactive(user_input):
        """Enhanced interactive processing with slash command support"""
        # Check if it's a slash command
        is_command, result = await slash_system.process_command(user_input)
        
        if is_command:
            print(result)
            return
        
        # Fall back to original processing
        if original_process:
            await original_process(user_input)
        else:
            # Default behavior
            backend = getattr(smart_ai_instance, 'backend', None)
            if backend:
                provider = backend.handle_provider_fallback(prompt=user_input)
                if provider:
                    backend.manage_session_state()
                    response = await backend.process_request_async(user_input, provider)
                    if response:
                        clean_output = backend.get_clean_output(response)
                        print(clean_output)
                    else:
                        print("❌ No response received")
                else:
                    print("❌ No providers available")
            else:
                print("❌ Backend not available")
    
    # Replace the interactive processing method
    smart_ai_instance._process_interactive_with_backend = enhanced_process_interactive
    
    # Enhanced interactive mode
    original_interactive = getattr(smart_ai_instance, 'interactive_mode', None)
    
    def enhanced_interactive_mode():
        """Enhanced interactive mode with slash command support"""
        print("🚀 Smart AI Enhanced Interactive Mode")
        print("=" * 50)
        print("Type '/help' for available commands")
        print("Type '/exit' to quit")
        print("=" * 50)
        
        while not getattr(smart_ai_instance, 'should_exit', False):
            try:
                user_input = input("\n💭 Smart AI> ").strip()
                
                if not user_input:
                    continue
                
                # Process with enhanced handler
                asyncio.run(enhanced_process_interactive(user_input))
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
    
    # Replace interactive mode
    smart_ai_instance.interactive_mode = enhanced_interactive_mode
    
    return slash_system


# Example usage and testing
if __name__ == "__main__":
    import sys
    sys.path.append('/Users/Subho')
    from smart_ai_backend import SmartAIBackend
    
    class MockSmartAI:
        def __init__(self):
            self.backend = SmartAIBackend()
            self.current_provider = 'claude_code'
            self.session_data = {'session_start': time.time(), 'requests_count': 0}
            self.should_exit = False
    
    async def test_enhanced_slash_commands():
        mock_ai = MockSmartAI()
        slash_system = SlashCommandSystem(mock_ai)
        
        test_commands = [
            "/help",
            "/help --category=system",
            "/help --search=provider",
            "/status --verbose",
            "/claude What is Python?",
            "/project init",
            "/session save test_session",
            "/mcp",
            "/version",
            "/invalid_command",
            "not a command"
        ]
        
        print("Testing Enhanced Smart AI Slash Commands")
        print("=" * 50)
        
        for cmd in test_commands:
            print(f"\n🧪 Testing: {cmd}")
            is_command, result = await slash_system.process_command(cmd)
            print(f"Is command: {is_command}")
            print(f"Result:\n{result}")
            print("-" * 50)
    
    # Run tests
    asyncio.run(test_enhanced_slash_commands())
#!/usr/bin/env python3
"""
Smart AI Unified CLI
Combines legacy positional interface with modern subcommand structure
Integrates SmartAIBackend with enhanced features for comprehensive AI tool management
"""

import os
import sys
import subprocess
import argparse
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any, List

# Add TreeQuest paths
sys.path.append('/Users/Subho/CascadeProjects/enhanced-treequest')
sys.path.append('/Users/Subho/CascadeProjects/multi-ai-treequest')

# Import the SmartAIBackend
try:
    from smart_ai_backend import SmartAIBackend
except ImportError:
    print("⚠️  SmartAIBackend not available - some features may be limited")
    SmartAIBackend = None

class SmartAIUnified:
    """Unified Smart AI CLI with hybrid interface support"""
    
    def __init__(self):
        self.claude_code_path = "/Users/Subho/.claude/local/claude"
        self.treequest_path = "/Users/Subho/CascadeProjects/enhanced-treequest"
        self.gemma_model = "gemma2:2b"
        self.session_log = Path.home() / ".smart-ai-session.json"
        self.token_usage_threshold = 0.9
        
        # Initialize SmartAIBackend if available
        self.backend = SmartAIBackend() if SmartAIBackend else None
        
        # Output format options
        self.output_formats = ['plain', 'json', 'markdown']
        self.current_format = 'plain'
        self.quiet_mode = False
        self.verbose_mode = False
    
    def detect_interface_mode(self, args: List[str]) -> str:
        """
        Detect whether user is using legacy or modern interface
        Returns: 'legacy', 'modern', or 'help'
        """
        if not args:
            return 'legacy'  # Interactive mode
        
        # Check for help flags first
        if args[0] in ['-h', '--help', 'help']:
            return 'help'
        
        # Look for modern subcommands anywhere in args (after global flags)
        modern_commands = ['ask', 'chat', 'providers', 'config', 'status']
        global_flags = ['--verbose', '-v', '--quiet', '-q', '--format']
        
        # Skip global flags and their values to find the actual command
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in modern_commands:
                return 'modern'
            
            # Skip global flags and their values
            if arg in global_flags:
                if arg == '--format' and i + 1 < len(args):
                    i += 2  # Skip flag and its value
                else:
                    i += 1  # Skip just the flag
            elif arg.startswith('--format='):
                i += 1  # Skip flag with embedded value
            elif arg in ['--verbose', '-v', '--quiet', '-q']:
                i += 1  # Skip boolean flags
            else:
                # This is not a global flag, check what it is
                if arg in modern_commands:
                    return 'modern'
                
                # Check for legacy flags
                legacy_flags = ['--claude', '--gemma', '--treequest', '--opendia', '--mcp', '--interactive', '-i']
                if arg in legacy_flags:
                    return 'legacy'
                
                # If it doesn't start with '-' and isn't a command, it's likely a prompt
                if not arg.startswith('-'):
                    return 'legacy'
                
                i += 1
        
        # Default to legacy for unknown patterns
        return 'legacy'
    
    def create_modern_parser(self):
        """Create argument parser for modern subcommand interface"""
        parser = argparse.ArgumentParser(
            prog='smart-ai',
            description="Smart AI Unified CLI - Intelligent AI provider switching and management",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Modern Interface Examples:
  smart-ai ask "What is Python?"                 # Ask a question
  smart-ai ask "Analyze this code" --provider claude  # Force provider
  smart-ai ask "Quick question" --format json    # JSON output
  smart-ai chat                                  # Interactive chat
  smart-ai providers list                       # List providers
  smart-ai providers status                     # Check provider status
  smart-ai config get model                     # Get config value
  smart-ai status                               # Show system status

Legacy Interface Examples (backward compatible):
  smart-ai "What is Python?"                    # Direct prompt
  smart-ai --claude "Use Claude Code"           # Force provider
  smart-ai --interactive                        # Interactive mode
  smart-ai                                      # Interactive mode

Output Format Options:
  --format plain      # Clean text output (default)
  --format json       # JSON structured output  
  --format markdown   # Markdown formatted output

Verbosity Options:
  --quiet, -q         # Minimal output
  --verbose, -v       # Detailed output with provider info
            """
        )
        
        # Global options
        parser.add_argument('--verbose', '-v', action='store_true', 
                          help='Verbose output with provider details')
        parser.add_argument('--quiet', '-q', action='store_true',
                          help='Minimal output mode')
        parser.add_argument('--format', choices=self.output_formats, default='plain',
                          help='Output format (plain, json, markdown)')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Ask command - for single questions
        ask_parser = subparsers.add_parser('ask', help='Ask a question')
        ask_parser.add_argument('question', nargs='+', help='Question to ask')
        ask_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                               help='Force specific provider')
        ask_parser.add_argument('--timeout', type=int, default=60,
                               help='Timeout in seconds (default: 60)')
        
        # Chat command - for interactive conversations
        chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
        chat_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                                help='Preferred provider for chat session')
        
        # Providers command - manage AI providers
        providers_parser = subparsers.add_parser('providers', help='Manage AI providers')
        providers_subparsers = providers_parser.add_subparsers(dest='providers_action')
        
        providers_subparsers.add_parser('list', help='List all available providers')
        providers_subparsers.add_parser('status', help='Check provider availability and status')
        providers_subparsers.add_parser('test', help='Test provider connectivity')
        
        test_parser = providers_subparsers.add_parser('test-provider', help='Test specific provider')
        test_parser.add_argument('provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                                help='Provider to test')
        
        # Config command - manage configuration  
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        get_parser = config_subparsers.add_parser('get', help='Get configuration value')
        get_parser.add_argument('key', help='Configuration key')
        
        set_parser = config_subparsers.add_parser('set', help='Set configuration value')
        set_parser.add_argument('key', help='Configuration key')
        set_parser.add_argument('value', help='Configuration value')
        
        config_subparsers.add_parser('list', help='List all configuration')
        config_subparsers.add_parser('reset', help='Reset configuration to defaults')
        
        # Status command - show system status
        status_parser = subparsers.add_parser('status', help='Show system and provider status')
        status_parser.add_argument('--detailed', action='store_true',
                                  help='Show detailed status information')
        
        return parser
    
    def create_legacy_parser(self):
        """Create argument parser for legacy interface"""
        parser = argparse.ArgumentParser(
            prog='smart-ai',
            description="Smart AI CLI - Intelligent switching between Claude Code, Gemma, and TreeQuest",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,  # We'll handle help manually
            epilog="""
Legacy Interface Examples:
  smart-ai                          # Interactive mode with smart switching
  smart-ai "What is Python?"        # Single query with smart routing
  smart-ai --claude                 # Force Claude Code mode
  smart-ai --gemma "Quick question"  # Force Gemma for quick questions
  smart-ai --treequest "Complex task" # Force TreeQuest for complex tasks
  
Interactive mode commands:
  /claude     - Switch to Claude Code
  /gemma      - Use Gemma for current query  
  /treequest  - Use TreeQuest for current query
  /status     - Show system status
  /help       - Show help
  /quit       - Exit interactive mode
        """
        )
        
        parser.add_argument("prompt", nargs="*", help="Prompt to process")
        parser.add_argument("--claude", action="store_true", help="Force use Claude Code")
        parser.add_argument("--gemma", action="store_true", help="Force use Gemma")
        parser.add_argument("--treequest", action="store_true", help="Force use TreeQuest")
        parser.add_argument("--opendia", action="store_true", help="Force use OpenDia")
        parser.add_argument("--mcp", action="store_true", help="Force use MCP tools")
        parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
        parser.add_argument("--format", choices=self.output_formats, default='plain',
                          help="Output format")
        parser.add_argument("--help", "-h", action="store_true", help="Show help")
        
        return parser
    
    def show_unified_help(self):
        """Show comprehensive help for both interfaces"""
        print("""
Smart AI Unified CLI - Hybrid Interface Documentation

🎯 MODERN INTERFACE (Recommended for new users):
   smart-ai ask "What is Python?"              # Ask a question
   smart-ai chat                               # Interactive chat mode
   smart-ai providers list                     # List all providers
   smart-ai status                             # Show system status
   smart-ai config get model                   # Configuration management

🔄 LEGACY INTERFACE (Backward compatible):
   smart-ai "What is Python?"                  # Direct prompt
   smart-ai --claude "Use Claude specifically" # Force provider
   smart-ai --interactive                      # Interactive mode
   smart-ai                                    # Interactive mode

📊 UNIVERSAL OPTIONS (work with both interfaces):
   --format plain|json|markdown               # Output formatting
   --verbose, -v                              # Detailed output
   --quiet, -q                                # Minimal output

🔧 AVAILABLE PROVIDERS:
   claude_code    # Claude Code CLI (requires authentication)
   treequest      # Multi-provider TreeQuest system
   gemma          # Local Gemma 2B via Ollama
   opendia        # Browser automation tools
   mcp            # Model Context Protocol tools

🚀 SMART ROUTING:
   The system automatically selects the best provider based on:
   - Internet connectivity
   - Prompt analysis (file operations → MCP, browser tasks → OpenDia)
   - Provider availability
   - Performance characteristics

📋 INTERACTIVE MODE COMMANDS:
   /claude, /gemma, /treequest     # Force specific providers
   /status                         # Show system status
   /providers                      # List available providers
   /help                          # Show help
   /quit, /exit                   # Exit

For detailed help on any command:
   smart-ai <command> --help      # Modern interface
   smart-ai --help                # Legacy interface
        """)
    
    async def handle_modern_interface(self, args: List[str]) -> int:
        """Handle modern subcommand-based interface"""
        parser = self.create_modern_parser()
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1
        
        # Set global options
        self.current_format = parsed_args.format
        self.verbose_mode = parsed_args.verbose
        self.quiet_mode = parsed_args.quiet
        
        if not parsed_args.command:
            parser.print_help()
            return 0
        
        try:
            if parsed_args.command == 'ask':
                return await self.handle_ask_command(parsed_args)
            elif parsed_args.command == 'chat':
                return await self.handle_chat_command(parsed_args)
            elif parsed_args.command == 'providers':
                return await self.handle_providers_command(parsed_args)
            elif parsed_args.command == 'config':
                return await self.handle_config_command(parsed_args)
            elif parsed_args.command == 'status':
                return await self.handle_status_command(parsed_args)
            else:
                self.output_error(f"Unknown command: {parsed_args.command}")
                return 1
        
        except Exception as e:
            if self.verbose_mode:
                import traceback
                traceback.print_exc()
            else:
                self.output_error(f"Error: {e}")
            return 1
    
    async def handle_legacy_interface(self, args: List[str]) -> int:
        """Handle legacy positional argument interface"""
        parser = self.create_legacy_parser()
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1
        
        # Set global options
        self.current_format = parsed_args.format
        self.verbose_mode = parsed_args.verbose
        self.quiet_mode = parsed_args.quiet
        
        if parsed_args.help:
            self.show_unified_help()
            return 0
        
        # Handle forced provider selection
        if parsed_args.claude:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else ""
            return await self.run_claude_code_with_prompt(prompt)
        elif parsed_args.gemma:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_gemma_ollama(prompt)
        elif parsed_args.treequest:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_treequest(prompt)
        elif parsed_args.opendia:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_opendia(prompt)
        elif parsed_args.mcp:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_mcp(prompt)
        
        # Interactive mode or single command
        if not parsed_args.prompt or parsed_args.interactive:
            return await self.interactive_mode()
        else:
            return await self.run_single_command(parsed_args.prompt)
    
    async def handle_ask_command(self, args) -> int:
        """Handle the ask subcommand"""
        question = ' '.join(args.question)
        
        if not self.backend:
            self.output_error("Backend not available. Using fallback...")
            self.output_message(f"Question: {question}")
            self.output_message("Response: Smart AI CLI is working! Backend integration needed.")
            return 0
        
        provider = args.provider or self.backend.handle_provider_fallback(prompt=question)
        
        if self.verbose_mode:
            self.output_info(f"Using provider: {provider}")
            self.output_info(f"Question: {question}")
        
        response = await self.backend.process_request_async(question, provider)
        
        if response:
            self.format_and_output_response(question, response, provider)
            return 0
        else:
            self.output_error("No response received")
            return 1
    
    async def handle_chat_command(self, args) -> int:
        """Handle the chat subcommand"""
        return await self.interactive_mode(preferred_provider=getattr(args, 'provider', None))
    
    async def handle_providers_command(self, args) -> int:
        """Handle the providers subcommand"""
        if not args.providers_action:
            print("Available provider commands: list, status, test")
            return 0
        
        if args.providers_action == 'list':
            await self.list_providers()
        elif args.providers_action == 'status':
            await self.check_providers_status()
        elif args.providers_action == 'test':
            await self.test_all_providers()
        elif args.providers_action == 'test-provider':
            await self.test_specific_provider(args.provider)
        
        return 0
    
    async def handle_config_command(self, args) -> int:
        """Handle the config subcommand"""
        config_file = Path.home() / ".smart-ai-config.json"
        
        if args.config_action == 'get':
            config = self.load_config(config_file)
            value = config.get(args.key, "Not set")
            self.output_message(f"{args.key}: {value}")
        
        elif args.config_action == 'set':
            config = self.load_config(config_file)
            config[args.key] = args.value
            self.save_config(config, config_file)
            self.output_success(f"Set {args.key} = {args.value}")
        
        elif args.config_action == 'list':
            config = self.load_config(config_file)
            for key, value in config.items():
                self.output_message(f"{key}: {value}")
        
        elif args.config_action == 'reset':
            config_file.unlink(missing_ok=True)
            self.output_success("Configuration reset to defaults")
        
        return 0
    
    async def handle_status_command(self, args) -> int:
        """Handle the status subcommand"""
        self.output_info("Smart AI System Status")
        self.output_message("=" * 50)
        
        # Check backend status
        if self.backend:
            self.output_success("SmartAI Backend: Available")
        else:
            self.output_warning("SmartAI Backend: Not available")
        
        # Check provider status
        await self.check_providers_status()
        
        # Check session info
        if args.detailed:
            self.show_session_info()
        
        return 0
    
    async def interactive_mode(self, preferred_provider: str = None) -> int:
        """Enhanced interactive mode with smart switching"""
        if not self.quiet_mode:
            self.output_info("Smart AI Interactive Mode")
            print("=" * 50)
            self.print_interactive_help()
        
        while True:
            try:
                user_input = input("\n💭 Smart AI> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("/quit", "/exit"):
                    if not self.quiet_mode:
                        self.output_success("Goodbye!")
                    break
                elif user_input == "/help":
                    self.print_interactive_help()
                    continue
                elif user_input == "/status":
                    await self.handle_status_command(type('Args', (), {'detailed': False})())
                    continue
                elif user_input == "/providers":
                    await self.list_providers()
                    continue
                elif user_input.startswith("/claude"):
                    prompt = user_input[7:].strip() or "Hello"
                    await self.run_claude_code_with_prompt(prompt)
                    continue
                elif user_input.startswith("/gemma"):
                    prompt = user_input[6:].strip() or "Hello"
                    await self.run_gemma_ollama(prompt)
                    continue
                elif user_input.startswith("/treequest"):
                    prompt = user_input[10:].strip() or "Hello"
                    await self.run_treequest(prompt)
                    continue
                elif user_input.startswith("/opendia"):
                    prompt = user_input[8:].strip() or "Hello"
                    await self.run_opendia(prompt)
                    continue
                elif user_input.startswith("/mcp"):
                    prompt = user_input[4:].strip() or "Hello"
                    await self.run_mcp(prompt)
                    continue
                
                # Smart routing with backend processing
                await self.process_interactive_with_backend(user_input, preferred_provider)
                    
            except KeyboardInterrupt:
                if not self.quiet_mode:
                    self.output_success("\nGoodbye!")
                break
            except EOFError:
                if not self.quiet_mode:
                    self.output_success("\nGoodbye!")
                break
        
        return 0
    
    def print_interactive_help(self):
        """Print help for interactive mode"""
        print("Available commands:")
        print("  /claude [prompt]   - Force use Claude Code")
        print("  /gemma [prompt]    - Force use Gemma")
        print("  /treequest [prompt] - Force use TreeQuest")
        print("  /opendia [prompt]  - Force use OpenDia")
        print("  /mcp [prompt]      - Force use MCP tools")
        print("  /status            - Show current status")
        print("  /providers         - List available providers")
        print("  /help              - Show this help message")
        print("  /quit, /exit       - Exit")
        print("=" * 50)
    
    async def run_single_command(self, args: List[str]) -> int:
        """Run a single command intelligently with backend processing"""
        prompt = " ".join(args)
        return await self.process_with_backend(prompt)
    
    async def process_with_backend(self, prompt: str, preferred_provider: str = None) -> int:
        """Process command using SmartAIBackend for clean output"""
        if not self.backend:
            self.output_error("Backend not available")
            return 1
        
        try:
            # Let backend handle provider selection with fallback
            provider = preferred_provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if not provider:
                self.output_error("No providers available")
                return 1
            
            # Update session state
            self.backend.manage_session_state()
            
            if self.verbose_mode:
                self.output_info(f"Using provider: {provider}")
            
            # Process async with backend
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(prompt, response, provider)
                return 0
            else:
                self.output_error("No response received")
                return 1
                
        except Exception as e:
            self.output_error(f"Error: {e}")
            return 1
    
    async def process_interactive_with_backend(self, user_input: str, preferred_provider: str = None):
        """Process interactive input using SmartAIBackend"""
        if not self.backend:
            self.output_error("Backend not available")
            return
        
        try:
            # Let backend determine best provider
            provider = preferred_provider or self.backend.handle_provider_fallback(prompt=user_input)
            
            if not provider:
                self.output_error("No providers available")
                return
            
            if self.verbose_mode:
                self.output_info(f"Routing to provider: {provider}")
            
            # Update session state
            self.backend.manage_session_state()
            
            # Process async with backend
            response = await self.backend.process_request_async(user_input, provider)
            
            if response:
                self.format_and_output_response(user_input, response, provider)
            else:
                self.output_error("No response received")
                
        except Exception as e:
            self.output_error(f"Error: {e}")
    
    # Provider-specific execution methods
    async def run_claude_code_with_prompt(self, prompt: str) -> int:
        """Run Claude Code with a specific prompt"""
        if not self.quiet_mode:
            self.output_info("Using Claude Code...")
        
        try:
            if prompt:
                cmd = [self.claude_code_path, prompt]
            else:
                cmd = [self.claude_code_path]
            
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            self.output_error(f"Claude Code error: {e}")
            return 1
    
    async def run_gemma_ollama(self, prompt: str) -> int:
        """Run Gemma via Ollama"""
        if not self.quiet_mode:
            self.output_info("Using Gemma 2B via Ollama...")
        
        if self.backend:
            try:
                response = await self.backend._execute_gemma(prompt)
                self.format_and_output_response(prompt, response, "gemma")
                return 0
            except Exception as e:
                self.output_error(f"Gemma error: {e}")
                return 1
        else:
            # Fallback to direct Ollama execution
            try:
                cmd = ["ollama", "run", self.gemma_model, prompt]
                result = subprocess.run(cmd, text=True)
                return result.returncode
            except Exception as e:
                self.output_error(f"Gemma error: {e}")
                return 1
    
    async def run_treequest(self, prompt: str) -> int:
        """Run TreeQuest for complex tasks"""
        if not self.quiet_mode:
            self.output_info("Using TreeQuest with multiple providers...")
        
        if self.backend:
            try:
                response = await self.backend._execute_treequest(prompt)
                self.format_and_output_response(prompt, response, "treequest")
                return 0
            except Exception as e:
                self.output_error(f"TreeQuest error: {e}")
                return 1
        else:
            self.output_error("TreeQuest requires SmartAI Backend")
            return 1
    
    async def run_opendia(self, prompt: str) -> int:
        """Run OpenDia for browser automation"""
        if not self.quiet_mode:
            self.output_info("Using OpenDia for browser automation...")
        
        if self.backend:
            try:
                response = await self.backend._execute_opendia(prompt)
                self.format_and_output_response(prompt, response, "opendia")
                return 0
            except Exception as e:
                self.output_error(f"OpenDia error: {e}")
                return 1
        else:
            self.output_error("OpenDia requires SmartAI Backend")
            return 1
    
    async def run_mcp(self, prompt: str) -> int:
        """Run MCP tools"""
        if not self.quiet_mode:
            self.output_info("Using MCP tools...")
        
        if self.backend:
            try:
                response = await self.backend._execute_mcp(prompt)
                self.format_and_output_response(prompt, response, "mcp")
                return 0
            except Exception as e:
                self.output_error(f"MCP error: {e}")
                return 1
        else:
            self.output_error("MCP requires SmartAI Backend")
            return 1
    
    # Provider management methods
    async def list_providers(self):
        """List all available providers"""
        providers_info = [
            ("claude_code", "Claude Code CLI", self.check_claude_code_available()),
            ("treequest", "Multi-provider TreeQuest", self.check_treequest_available()),
            ("gemma", "Local Gemma 2B via Ollama", await self.check_gemma_available()),
            ("opendia", "Browser automation tools", self.check_opendia_available()),
            ("mcp", "Model Context Protocol tools", self.check_mcp_available())
        ]
        
        if self.current_format == 'json':
            providers_list = []
            for provider, description, available in providers_info:
                providers_list.append({
                    "name": provider,
                    "description": description,
                    "available": available,
                    "status": "available" if available else "unavailable"
                })
            print(json.dumps({"providers": providers_list}, indent=2))
        
        elif self.current_format == 'markdown':
            print("# Available Providers\n")
            for provider, description, available in providers_info:
                status = "✅ Available" if available else "❌ Unavailable"
                print(f"## {provider}")
                print(f"- **Description:** {description}")
                print(f"- **Status:** {status}\n")
        
        else:  # plain format
            self.output_info("Available providers:")
            for provider, description, available in providers_info:
                status = "✅" if available else "❌"
                self.output_message(f"  {status} {provider}: {description}")
    
    async def check_providers_status(self):
        """Check and display provider status"""
        if self.backend:
            self.output_info("Provider status (via backend):")
            for provider in self.backend.providers:
                available = self.backend._check_provider_availability(provider)
                status = "Available" if available else "Unavailable"
                icon = "✅" if available else "❌"
                self.output_message(f"  {icon} {provider}: {status}")
        else:
            await self.list_providers()
    
    async def test_all_providers(self):
        """Test all providers with a simple query"""
        test_prompt = "Hello, this is a test."
        self.output_info("Testing all providers...")
        
        providers = ["claude_code", "gemma", "treequest", "opendia", "mcp"]
        
        for provider in providers:
            if self.backend and self.backend._check_provider_availability(provider):
                try:
                    self.output_info(f"Testing {provider}...")
                    response = await self.backend.process_request_async(test_prompt, provider)
                    if response:
                        self.output_success(f"{provider}: ✅ Working")
                    else:
                        self.output_warning(f"{provider}: ⚠️ No response")
                except Exception as e:
                    self.output_error(f"{provider}: ❌ Error - {e}")
            else:
                self.output_warning(f"{provider}: ❌ Not available")
    
    async def test_specific_provider(self, provider: str):
        """Test a specific provider"""
        test_prompt = "Hello, this is a test."
        
        if self.backend and self.backend._check_provider_availability(provider):
            try:
                self.output_info(f"Testing {provider}...")
                response = await self.backend.process_request_async(test_prompt, provider)
                if response:
                    self.output_success(f"{provider}: ✅ Working")
                    if self.verbose_mode:
                        self.output_message(f"Response: {response[:100]}...")
                else:
                    self.output_warning(f"{provider}: ⚠️ No response")
            except Exception as e:
                self.output_error(f"{provider}: ❌ Error - {e}")
        else:
            self.output_error(f"{provider}: ❌ Not available")
    
    # Provider availability checks
    def check_claude_code_available(self) -> bool:
        """Check if Claude Code is available and responsive"""
        try:
            result = subprocess.run([self.claude_code_path, "--version"], 
                                 capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_treequest_available(self) -> bool:
        """Check if TreeQuest is available"""
        return Path(self.treequest_path).exists()
    
    async def check_gemma_available(self) -> bool:
        """Check if Gemma is available via Ollama"""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and "gemma2:2b" in result.stdout
        except:
            return False
    
    def check_opendia_available(self) -> bool:
        """Check if OpenDia is available"""
        return Path("/Users/Subho/opendia/opendia-mcp").exists()
    
    def check_mcp_available(self) -> bool:
        """Check if MCP tools are available"""
        return Path("/Users/Subho/.mcp.json").exists()
    
    # Configuration management
    def load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_config(self, config: Dict[str, Any], config_file: Path):
        """Save configuration to file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.output_error(f"Could not save config: {e}")
    
    def show_session_info(self):
        """Show session information"""
        if self.session_log.exists():
            try:
                with open(self.session_log, 'r') as f:
                    data = json.load(f)
                
                session_data = data.get('session_data', {})
                self.output_message("\nSession Information:")
                self.output_message(f"  Requests: {session_data.get('requests_count', 0)}")
                self.output_message(f"  Duration: {session_data.get('session_duration', 0):.1f}s")
                
                if session_data.get('last_access'):
                    import datetime
                    last_access = datetime.datetime.fromtimestamp(session_data['last_access'])
                    self.output_message(f"  Last access: {last_access.strftime('%Y-%m-%d %H:%M:%S')}")
                    
            except Exception as e:
                self.output_warning(f"Could not load session info: {e}")
    
    # Output formatting methods
    def format_and_output_response(self, prompt: str, response: str, provider: str):
        """Format and output response based on current format setting"""
        if self.current_format == 'json':
            output = {
                "prompt": prompt,
                "response": response,
                "provider": provider,
                "timestamp": time.time()
            }
            print(json.dumps(output, indent=2))
        
        elif self.current_format == 'markdown':
            print(f"## Query\n{prompt}\n")
            print(f"## Response\n{response}\n")
            if self.verbose_mode:
                print(f"*Provider: {provider}*\n")
        
        else:  # plain format
            if self.verbose_mode and not self.quiet_mode:
                self.output_info(f"Response from {provider}:")
            print(response)
    
    def output_message(self, message: str):
        """Output a regular message"""
        if not self.quiet_mode:
            print(message)
    
    def output_info(self, message: str):
        """Output an info message"""
        if not self.quiet_mode:
            print(f"ℹ️  {message}")
    
    def output_success(self, message: str):
        """Output a success message"""
        if not self.quiet_mode:
            print(f"✅ {message}")
    
    def output_warning(self, message: str):
        """Output a warning message"""
        if not self.quiet_mode:
            print(f"⚠️  {message}")
    
    def output_error(self, message: str):
        """Output an error message"""
        print(f"❌ {message}")

async def main():
    """Main entry point with interface detection"""
    args = sys.argv[1:]
    smart_ai = SmartAIUnified()
    
    # Detect interface mode
    interface_mode = smart_ai.detect_interface_mode(args)
    
    if interface_mode == 'help':
        smart_ai.show_unified_help()
        return 0
    elif interface_mode == 'modern':
        return await smart_ai.handle_modern_interface(args)
    else:  # legacy
        return await smart_ai.handle_legacy_interface(args)

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(130)
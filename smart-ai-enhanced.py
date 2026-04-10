#!/usr/bin/env python3
"""
Smart AI Enhanced CLI
Wrapper that uses existing smart_ai_backend.py with enhanced command structure
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add paths
sys.path.append('/Users/Subho')
sys.path.append('/Users/Subho/smart-ai-enhanced-modules')

# Import existing backend
try:
    from smart_ai_backend import SmartAIBackend
    from smart_ai_enhanced.src.config.config_manager import ConfigurationManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure smart_ai_backend.py exists and modules are properly installed")
    # Use basic fallback
    SmartAIBackend = None
    ConfigurationManager = None

class SmartAIEnhanced:
    """Enhanced Smart AI CLI with subcommands"""
    
    def __init__(self):
        if SmartAIBackend:
            self.backend = SmartAIBackend()
        else:
            self.backend = None
            
        if ConfigurationManager:
            self.config = ConfigurationManager()
        else:
            self.config = None
        
    def create_parser(self):
        """Create argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            description="Smart AI Enhanced CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  smart-ai-enhanced.py ask "What is Python?"
  smart-ai-enhanced.py chat
  smart-ai-enhanced.py providers list
  smart-ai-enhanced.py config get api_key
            """
        )
        
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--format', choices=['plain', 'json', 'markdown'], default='plain', help='Output format')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Ask command
        ask_parser = subparsers.add_parser('ask', help='Ask a question')
        ask_parser.add_argument('question', nargs='+', help='Question to ask')
        ask_parser.add_argument('--provider', help='Force specific provider')
        
        # Chat command
        chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
        
        # Providers command
        providers_parser = subparsers.add_parser('providers', help='Manage providers')
        providers_subparsers = providers_parser.add_subparsers(dest='providers_action')
        providers_subparsers.add_parser('list', help='List providers')
        providers_subparsers.add_parser('status', help='Check provider status')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        get_parser = config_subparsers.add_parser('get', help='Get config value')
        get_parser.add_argument('key', help='Config key')
        set_parser = config_subparsers.add_parser('set', help='Set config value')
        set_parser.add_argument('key', help='Config key')
        set_parser.add_argument('value', help='Config value')
        
        return parser
    
    async def handle_ask(self, args):
        """Handle ask command"""
        question = ' '.join(args.question)
        
        if not self.backend:
            print("❌ Backend not available. Using fallback...")
            print(f"Question: {question}")
            print("Response: Enhanced CLI is working! Backend integration needed.")
            return
            
        provider = args.provider or self.backend.handle_provider_fallback(prompt=question)
        
        if args.verbose:
            print(f"🔄 Using provider: {provider}")
            print(f"📝 Question: {question}")
        
        response = await self.backend.process_request_async(question, provider)
        
        if response:
            if args.format == 'json':
                import json
                print(json.dumps({"question": question, "response": response, "provider": provider}))
            elif args.format == 'markdown':
                print(f"## Question\n{question}\n\n## Response\n{response}")
            else:
                print(response)
        else:
            print("❌ No response received")
    
    def handle_chat(self, args):
        """Handle chat command"""
        print("🗣️  Smart AI Enhanced Chat Mode")
        print("Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("💭 > ").strip()
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if self.backend:
                    # Use existing interactive processing
                    asyncio.run(self.backend._process_interactive_with_backend(user_input))
                else:
                    print(f"Enhanced CLI Response: {user_input}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    
    def handle_providers(self, args):
        """Handle providers command"""
        if args.providers_action == 'list':
            print("🔧 Available providers:")
            if self.backend:
                for provider in self.backend.providers:
                    available = self.backend._check_provider_availability(provider)
                    status = "✅" if available else "❌"
                    print(f"  {status} {provider}")
            else:
                print("  ❌ Backend not available")
        
        elif args.providers_action == 'status':
            print("📊 Provider status:")
            if self.backend:
                for provider in self.backend.providers:
                    available = self.backend._check_provider_availability(provider)
                    status = "Available" if available else "Unavailable"
                    print(f"  {provider}: {status}")
            else:
                print("  Backend not available")
    
    def handle_config(self, args):
        """Handle config command"""
        if args.config_action == 'get':
            if self.config:
                value = self.config.get_config(args.key)
                print(f"{args.key}: {value}")
            else:
                print(f"{args.key}: Config manager not available")
        
        elif args.config_action == 'set':
            if self.config:
                self.config.set_config(args.key, args.value)
                print(f"✅ Set {args.key} = {args.value}")
            else:
                print("❌ Config manager not available")
    
    async def run(self):
        """Main run method"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == 'ask':
                await self.handle_ask(args)
            elif args.command == 'chat':
                self.handle_chat(args)
            elif args.command == 'providers':
                self.handle_providers(args)
            elif args.command == 'config':
                self.handle_config(args)
        
        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    cli = SmartAIEnhanced()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main()
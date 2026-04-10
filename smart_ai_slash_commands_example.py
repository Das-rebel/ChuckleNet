#!/usr/bin/env python3
"""
Smart AI Slash Commands - Usage Examples and Integration Demo
Demonstrates how to integrate and use the enhanced slash command system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add to path for imports
sys.path.append('/Users/Subho')

from smart_ai_slash_commands import (
    integrate_slash_commands_with_smart_ai,
    SlashCommandSystem,
    CommandDefinition,
    CommandParameter,
    CommandCategory,
    BaseCommandHandler
)
from smart_ai_backend import SmartAIBackend


class ExampleCustomCommandHandler(BaseCommandHandler):
    """Example custom command handler"""
    
    async def execute(self, parsed_cmd, context):
        name = parsed_cmd.kwargs.get('name', 'World')
        times = parsed_cmd.kwargs.get('times', 1)
        
        result = []
        for i in range(times):
            result.append(f"Hello, {name}! (#{i+1})")
        
        return "\n".join(result)


class SmartAIDemo:
    """Demo class showing Smart AI with slash commands"""
    
    def __init__(self):
        self.backend = SmartAIBackend()
        self.current_provider = 'claude_code'
        self.session_data = {'session_start': asyncio.get_event_loop().time(), 'requests_count': 0}
        self.should_exit = False
        
        # Integrate slash commands
        self.slash_system = integrate_slash_commands_with_smart_ai(self)
        
        # Add custom commands
        self._register_custom_commands()
    
    def _register_custom_commands(self):
        """Register additional custom commands for demo"""
        
        # Custom hello command
        self.slash_system.registry.register(CommandDefinition(
            name="hello",
            handler=ExampleCustomCommandHandler(),
            description="Say hello with customizable name and repetition",
            category=CommandCategory.UTILITY,
            parameters=[
                CommandParameter("name", str, False, "World", "Name to greet"),
                CommandParameter("times", int, False, 1, "Number of times to repeat", validator=lambda x: x > 0)
            ],
            examples=["/hello", "/hello --name=Alice", "/hello --name=Bob --times=3"],
            usage="/hello [--name=<name>] [--times=<count>]"
        ))
    
    async def demo_interactive_mode(self):
        """Demo interactive mode with slash commands"""
        print("🎯 Smart AI Slash Commands Demo")
        print("=" * 40)
        print("Available demo commands:")
        print("  /help                     - Show all commands")
        print("  /status                   - System status") 
        print("  /hello --name=Alice       - Custom hello command")
        print("  /project init             - Initialize project")
        print("  /session save demo        - Save session")
        print("  /claude What is Python?   - Switch provider and query")
        print("  /exit                     - Exit demo")
        print("=" * 40)
        
        while not self.should_exit:
            try:
                user_input = input("\n💭 Demo> ").strip()
                
                if not user_input:
                    continue
                
                # Process with slash command system
                await self._process_interactive_with_backend(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 Demo ended!")
                break
            except EOFError:
                print("\n👋 Demo ended!")
                break


async def demo_command_parsing():
    """Demonstrate command parsing capabilities"""
    print("\n🔧 Command Parsing Demo")
    print("=" * 30)
    
    demo_ai = SmartAIDemo()
    parser = demo_ai.slash_system.parser
    
    test_commands = [
        "/help",
        "/status --verbose",
        "/hello --name='Alice Smith' --times=3",
        "/session save 'my session'",
        "/claude 'What is the meaning of life?'",
        "/mcp task-master --list",
        "/invalid command",
        "regular text input"
    ]
    
    for cmd in test_commands:
        print(f"\nInput: {cmd}")
        parsed = parser.parse(cmd)
        print(f"  Command: {parsed.command}")
        print(f"  Args: {parsed.args}")
        print(f"  Kwargs: {parsed.kwargs}")
        print(f"  Valid: {parsed.is_valid}")
        if not parsed.is_valid:
            print(f"  Error: {parsed.error_message}")


async def demo_custom_commands():
    """Demonstrate custom command creation"""
    print("\n📂 Custom Commands Demo")
    print("=" * 30)
    
    # Create example custom command files
    demo_commands_dir = Path.cwd() / ".claude" / "commands"
    demo_commands_dir.mkdir(parents=True, exist_ok=True)
    
    # Example custom command with frontmatter
    custom_cmd_content = """---
name: analyze-code
description: Analyze code for potential improvements
category: development
---

Analyze the following code for:
- Performance optimizations
- Security vulnerabilities  
- Code quality improvements
- Best practices adherence

Code to analyze: $ARGUMENTS

Please provide specific recommendations with examples.
"""
    
    custom_cmd_file = demo_commands_dir / "analyze-code.md"
    custom_cmd_file.write_text(custom_cmd_content)
    
    # Another example with file references
    review_cmd_content = """---
name: review-pr
description: Review a pull request comprehensively
category: development
---

!git diff HEAD~1 HEAD

Please review the above git diff and provide:

1. Code quality assessment
2. Security considerations  
3. Performance implications
4. Testing recommendations
5. Documentation needs

Focus on: $ARGUMENTS
"""
    
    review_cmd_file = demo_commands_dir / "review-pr.md"
    review_cmd_file.write_text(review_cmd_content)
    
    print(f"✅ Created custom commands in {demo_commands_dir}")
    print("  - analyze-code.md")
    print("  - review-pr.md")
    
    # Load and demonstrate
    demo_ai = SmartAIDemo()
    demo_ai.slash_system._load_custom_commands()
    
    registry = demo_ai.slash_system.registry
    custom_commands = [cmd for cmd in registry.commands.values() if cmd.source != "builtin"]
    
    print(f"\nLoaded {len(custom_commands)} custom commands:")
    for cmd in custom_commands:
        print(f"  /{cmd.name} - {cmd.description}")


async def demo_mcp_integration():
    """Demonstrate MCP integration capabilities"""
    print("\n🔌 MCP Integration Demo")
    print("=" * 30)
    
    demo_ai = SmartAIDemo()
    
    # Check MCP availability
    if demo_ai.backend:
        await demo_ai.backend._initialize_mcp_manager()
        
        if demo_ai.backend.mcp_manager:
            tools = list(demo_ai.backend.mcp_manager.tools.keys())
            print(f"✅ MCP Manager initialized with {len(tools)} tools")
            
            if tools:
                print("Available MCP tools:")
                for tool in tools[:5]:  # Show first 5
                    print(f"  - {tool}")
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more")
            else:
                print("No MCP tools currently available")
        else:
            print("❌ MCP Manager not available")
    else:
        print("❌ Backend not available")


async def demo_session_management():
    """Demonstrate session management"""
    print("\n💾 Session Management Demo")
    print("=" * 30)
    
    demo_ai = SmartAIDemo()
    
    # Simulate some session activity
    demo_ai.session_data.update({
        'requests_count': 5,
        'last_command': '/help',
        'demo_data': 'This is demo session data'
    })
    
    # Test session commands
    test_commands = [
        "/session save demo_session",
        "/session list",
        "/session info"
    ]
    
    for cmd in test_commands:
        print(f"\nExecuting: {cmd}")
        is_command, result = await demo_ai.slash_system.process_command(cmd)
        print(result)


async def demo_error_handling():
    """Demonstrate error handling and validation"""
    print("\n⚠️ Error Handling Demo")
    print("=" * 30)
    
    demo_ai = SmartAIDemo()
    
    # Test various error scenarios
    error_commands = [
        "/nonexistent",
        "/hello --times=invalid",
        "/session",  # Missing required parameter
        "/status --unknown-param=value",
        "/hello --name",  # Missing value
    ]
    
    for cmd in error_commands:
        print(f"\nTesting: {cmd}")
        is_command, result = await demo_ai.slash_system.process_command(cmd)
        print(f"Result: {result}")


async def main():
    """Run all demos"""
    print("🚀 Smart AI Slash Commands - Complete Demo")
    print("=" * 50)
    
    await demo_command_parsing()
    await demo_custom_commands()
    await demo_mcp_integration()
    await demo_session_management()
    await demo_error_handling()
    
    print("\n🎯 Interactive Demo")
    print("=" * 20)
    
    # Ask user if they want interactive demo
    response = input("Run interactive demo? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        demo_ai = SmartAIDemo()
        await demo_ai.demo_interactive_mode()
    
    print("\n✅ Demo completed!")
    print("To integrate with your Smart AI:")
    print("  from smart_ai_slash_commands import integrate_slash_commands_with_smart_ai")
    print("  slash_system = integrate_slash_commands_with_smart_ai(your_smart_ai_instance)")


if __name__ == "__main__":
    asyncio.run(main())
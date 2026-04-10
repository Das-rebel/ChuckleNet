#!/usr/bin/env python3
"""
Test Smart AI integration with slash commands
"""

import asyncio
import sys
sys.path.append('/Users/Subho')

from smart_ai_slash_commands import integrate_slash_commands_with_smart_ai
from smart_ai_backend import SmartAIBackend

class TestSmartAI:
    """Test Smart AI class for integration testing"""
    
    def __init__(self):
        self.backend = SmartAIBackend()
        self.current_provider = 'claude_code'
        self.session_data = {'session_start': asyncio.get_event_loop().time(), 'requests_count': 0}
        self.should_exit = False

async def test_integration():
    """Test slash command integration"""
    print("🧪 Testing Smart AI Slash Commands Integration")
    print("=" * 50)
    
    # Create test instance
    smart_ai = TestSmartAI()
    
    # Integrate slash commands
    slash_system = integrate_slash_commands_with_smart_ai(smart_ai)
    
    # Test commands
    test_commands = [
        ("/help", "Should show help"),
        ("/status", "Should show status"),
        ("/version", "Should show version"),
        ("/claude", "Should switch to Claude"),
        ("/session info", "Should show session info"),
        ("/invalid", "Should show error with suggestions"),
        ("regular input", "Should not be processed as command")
    ]
    
    for cmd, description in test_commands:
        print(f"\n🔍 Testing: {cmd}")
        print(f"   Expected: {description}")
        
        try:
            is_command, result = await slash_system.process_command(cmd)
            print(f"   Is Command: {is_command}")
            print(f"   Result: {result[:100]}{'...' if len(result) > 100 else ''}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Integration test completed!")
    print(f"📊 Command Registry Stats:")
    print(f"   Total Commands: {len(slash_system.registry.commands)}")
    print(f"   Built-in Commands: {len([c for c in slash_system.registry.commands.values() if c.source == 'builtin'])}")
    print(f"   Custom Commands: {len([c for c in slash_system.registry.commands.values() if c.source != 'builtin'])}")
    print(f"   Categories: {len(slash_system.registry.categories)}")

if __name__ == "__main__":
    asyncio.run(test_integration())
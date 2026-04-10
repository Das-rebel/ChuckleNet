#!/usr/bin/env python3
"""
Smart AI Integration Module
Integrates session management, slash commands, and notifications with the main smart-ai system.
Provides a unified interface for command processing and session handling.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# Import core components
from smart_ai_backend import SmartAIBackend
from smart_ai_session_commands import (
    register_session_commands, SessionStorage, SessionData, SessionMetadata, 
    ConversationEntry, SessionStatus
)
from smart_ai_slash_commands import (
    SlashCommandParser, CommandExecutionContext,
    CommandDefinition, CommandCategory, CommandParameter, BaseCommandHandler,
    command_error_handler
)
from smart_ai_notifications import NotificationManager, NotificationType, NotificationConfig


# Create a simplified command registry since we don't have the full one
class SimpleCommandRegistry:
    """Simplified command registry for session commands"""
    
    def __init__(self):
        self.commands: Dict[str, CommandDefinition] = {}
    
    def register(self, command_def: CommandDefinition):
        """Register a command"""
        self.commands[command_def.name] = command_def
        for alias in command_def.aliases:
            self.commands[alias] = command_def
    
    async def execute(self, parsed_cmd, context: CommandExecutionContext) -> str:
        """Execute a command"""
        if parsed_cmd.command not in self.commands:
            return f"❌ Unknown command: {parsed_cmd.command}"
        
        command_def = self.commands[parsed_cmd.command]
        return await command_def.handler.execute(parsed_cmd, context)
    
    def generate_help(self, category_filter: str = None, verbose: bool = False) -> str:
        """Generate help text"""
        lines = ["Available Commands:", "=" * 20]
        
        for name, cmd_def in self.commands.items():
            if name != cmd_def.name:  # Skip aliases in main listing
                continue
            
            if category_filter and cmd_def.category.value != category_filter:
                continue
            
            lines.append(f"/{cmd_def.name} - {cmd_def.description}")
            if verbose and cmd_def.usage:
                lines.append(f"  Usage: {cmd_def.usage}")
                if cmd_def.examples:
                    lines.append(f"  Examples: {', '.join(cmd_def.examples[:2])}")
            lines.append("")
        
        return "\n".join(lines)


@dataclass
class SmartAIConfig:
    """Configuration for Smart AI system"""
    enable_session_management: bool = True
    enable_notifications: bool = True
    enable_autosave: bool = True
    autosave_interval: int = 300  # 5 minutes
    session_directory: Optional[Path] = None
    notification_config: NotificationConfig = field(default_factory=NotificationConfig)
    max_conversation_history: int = 1000
    enable_encryption: bool = True
    debug_mode: bool = False
    
    def __post_init__(self):
        if self.session_directory is None:
            self.session_directory = Path.home() / ".smart-ai" / "sessions"


class SmartAICore:
    """
    Enhanced Smart AI Core with full session management, command processing, and notifications.
    Provides a complete framework for the smart-ai CLI system.
    """
    
    def __init__(self, config: Optional[SmartAIConfig] = None):
        self.config = config or SmartAIConfig()
        
        # Core components
        self.backend = SmartAIBackend()
        self.conversation_history: List[ConversationEntry] = []
        self.session_data: Dict[str, Any] = {}
        self.current_provider = 'claude_code'
        
        # Session management
        if self.config.enable_session_management:
            self.session_storage = SessionStorage(self.config.session_directory)
        else:
            self.session_storage = None
        
        # Notification system
        if self.config.enable_notifications:
            # Create notifications config directory
            notifications_dir = self.config.session_directory.parent / "notifications"
            notifications_dir.mkdir(parents=True, exist_ok=True)
            self.notification_manager = NotificationManager(str(notifications_dir / "config.json"))
        else:
            self.notification_manager = None
        
        # Command system
        self.command_parser = SlashCommandParser()
        self.command_registry = SimpleCommandRegistry()
        
        # State tracking
        self.session_start_time = time.time()
        self.last_autosave = time.time()
        self.provider_states: Dict[str, Any] = {}
        self.mcp_config: Dict[str, Any] = {}
        
        # Initialize components
        self._initialize_session_data()
        self._register_builtin_commands()
        
        if self.config.enable_session_management:
            self._register_session_commands()
    
    def _initialize_session_data(self):
        """Initialize session data with defaults"""
        self.session_data.update({
            'session_start': self.session_start_time,
            'conversation_count': 0,
            'total_tokens': 0,
            'provider_usage': {},
            'autosave_enabled': self.config.enable_autosave,
            'autosave_interval': self.config.autosave_interval
        })
    
    def _register_builtin_commands(self):
        """Register built-in system commands"""
        
        class StatusCommandHandler(BaseCommandHandler):
            def __init__(self, core_instance):
                self.core = core_instance
            
            @command_error_handler
            async def execute(self, parsed_cmd, context):
                lines = [
                    "Smart AI Status:",
                    "=" * 20,
                    f"Active Provider: {self.core.current_provider}",
                    f"Conversation History: {len(self.core.conversation_history)} entries",
                    f"Session Duration: {int(time.time() - self.core.session_start_time)}s",
                ]
                
                if self.core.session_storage:
                    sessions = self.core.session_storage.list_sessions()
                    lines.append(f"Saved Sessions: {len(sessions)}")
                
                if self.core.config.enable_autosave:
                    lines.append(f"Autosave: ✅ ({self.core.config.autosave_interval}s)")
                else:
                    lines.append("Autosave: ❌")
                
                return "\n".join(lines)
        
        class HelpCommandHandler(BaseCommandHandler):
            def __init__(self, core_instance):
                self.core = core_instance
            
            @command_error_handler
            async def execute(self, parsed_cmd, context):
                category_filter = parsed_cmd.args[0] if parsed_cmd.args else None
                verbose = parsed_cmd.kwargs.get('verbose', False)
                
                return self.core.command_registry.generate_help(category_filter, verbose)
        
        # Register built-in commands
        self.command_registry.register(CommandDefinition(
            name="status",
            handler=StatusCommandHandler(self),
            description="Show current system status",
            category=CommandCategory.SYSTEM,
            examples=["/status"],
            usage="/status"
        ))
        
        self.command_registry.register(CommandDefinition(
            name="help",
            handler=HelpCommandHandler(self),
            description="Show available commands and usage information",
            category=CommandCategory.SYSTEM,
            parameters=[
                CommandParameter("category", str, False, None, "Filter by category"),
                CommandParameter("verbose", bool, False, False, "Show detailed information")
            ],
            examples=[
                "/help",
                "/help session",
                "/help --verbose"
            ],
            usage="/help [category] [--verbose]"
        ))
    
    def _register_session_commands(self):
        """Register session management commands"""
        if self.session_storage:
            register_session_commands(self.command_registry, self)
    
    async def process_command(self, input_text: str) -> str:
        """Process a slash command or regular input"""
        input_text = input_text.strip()
        
        # Check if it's a slash command
        if self.command_parser.is_slash_command(input_text):
            return await self._process_slash_command(input_text)
        else:
            return await self._process_regular_input(input_text)
    
    async def _process_slash_command(self, input_text: str) -> str:
        """Process a slash command"""
        try:
            # Parse command
            parsed_cmd = self.command_parser.parse(input_text)
            
            if not parsed_cmd.is_valid:
                return f"❌ {parsed_cmd.error_message}"
            
            # Execute command
            context = CommandExecutionContext(self, self.session_data)
            result = await self.command_registry.execute(parsed_cmd, context)
            
            # Handle autosave
            await self._check_autosave()
            
            return result
            
        except Exception as e:
            if self.config.debug_mode:
                import traceback
                return f"❌ Command execution failed: {e}\n{traceback.format_exc()}"
            else:
                return f"❌ Command execution failed: {e}"
    
    async def _process_regular_input(self, input_text: str) -> str:
        """Process regular AI input using the backend"""
        try:
            # Add to conversation history
            user_entry = ConversationEntry(
                id=f"user_{int(time.time() * 1000)}",
                timestamp=datetime.now(),
                role="user",
                content=input_text,
                provider=self.current_provider
            )
            self.conversation_history.append(user_entry)
            
            # Process with backend
            provider = self.backend.handle_provider_fallback(prompt=input_text)
            if not provider:
                return "❌ No providers available"
            
            self.current_provider = provider
            response = await self.backend.process_request_async(input_text, provider)
            
            if response:
                # Add assistant response to history
                assistant_entry = ConversationEntry(
                    id=f"assistant_{int(time.time() * 1000)}",
                    timestamp=datetime.now(),
                    role="assistant",
                    content=response,
                    provider=provider
                )
                self.conversation_history.append(assistant_entry)
                
                # Update session data
                self.session_data['conversation_count'] = len(self.conversation_history)
                self.session_data['provider_usage'][provider] = self.session_data['provider_usage'].get(provider, 0) + 1
                
                # Handle autosave
                await self._check_autosave()
                
                return self.backend.get_clean_output(response)
            else:
                return "❌ No response received"
                
        except Exception as e:
            if self.config.debug_mode:
                import traceback
                return f"❌ Processing failed: {e}\n{traceback.format_exc()}"
            else:
                return f"❌ Processing failed: {e}"
    
    async def _check_autosave(self):
        """Check if autosave should be performed"""
        if not self.config.enable_autosave or not self.session_storage:
            return
        
        current_time = time.time()
        if current_time - self.last_autosave >= self.config.autosave_interval:
            try:
                await self.autosave_session()
                self.last_autosave = current_time
            except Exception as e:
                if self.config.debug_mode:
                    print(f"Autosave failed: {e}")
    
    async def autosave_session(self, session_name: str = None):
        """Automatically save current session"""
        if not self.session_storage:
            return
        
        session_name = session_name or f"autosave_{int(time.time())}"
        
        metadata = SessionMetadata(
            name=session_name,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            description="Auto-saved session",
            project_root=str(Path.cwd()),
            provider_states=self.provider_states,
            mcp_config=self.mcp_config,
            status=SessionStatus.ACTIVE
        )
        
        session_data = SessionData(
            metadata=metadata,
            conversation_history=self.conversation_history[-100:],  # Keep last 100 conversations
            context_data=self.session_data.copy()
        )
        
        self.session_storage.save_session(session_data)
        
        if self.notification_manager:
            self.notification_manager.notify(
                "Session Auto-saved",
                f"Session saved as '{session_name}'",
                NotificationType.INFO
            )
    
    def save_session(self, session_name: str, password: str = None) -> Path:
        """Manually save current session"""
        if not self.session_storage:
            raise ValueError("Session management not enabled")
        
        metadata = SessionMetadata(
            name=session_name,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            description="Manually saved session",
            project_root=str(Path.cwd()),
            provider_states=self.provider_states,
            mcp_config=self.mcp_config,
            status=SessionStatus.SAVED,
            encrypted=bool(password)
        )
        
        session_data = SessionData(
            metadata=metadata,
            conversation_history=self.conversation_history,
            context_data=self.session_data.copy()
        )
        
        return self.session_storage.save_session(session_data, password)
    
    def load_session(self, session_name: str, password: str = None, merge: bool = False):
        """Load a saved session"""
        if not self.session_storage:
            raise ValueError("Session management not enabled")
        
        session_data = self.session_storage.load_session(session_name, password)
        
        if merge:
            # Merge with current session
            self.conversation_history.extend(session_data.conversation_history)
            self.session_data.update(session_data.context_data)
        else:
            # Replace current session
            self.conversation_history = session_data.conversation_history
            self.session_data = session_data.context_data.copy()
            self.provider_states = session_data.metadata.provider_states
            self.mcp_config = session_data.metadata.mcp_config
        
        # Update session stats
        self.session_data['conversation_count'] = len(self.conversation_history)
    
    def clear_session(self, create_backup: bool = True) -> Optional[str]:
        """Clear current session"""
        backup_name = None
        
        if create_backup and self.conversation_history and self.session_storage:
            backup_name = f"clear_backup_{int(time.time())}"
            try:
                self.save_session(backup_name)
            except Exception:
                backup_name = None
        
        # Clear data
        self.conversation_history.clear()
        self.session_data.clear()
        self._initialize_session_data()
        
        return backup_name
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            'conversation_count': len(self.conversation_history),
            'session_duration': int(time.time() - self.session_start_time),
            'current_provider': self.current_provider,
            'session_data_keys': list(self.session_data.keys()),
            'provider_usage': self.session_data.get('provider_usage', {}),
            'autosave_enabled': self.config.enable_autosave,
            'last_autosave': self.last_autosave if hasattr(self, 'last_autosave') else None
        }
    
    async def interactive_mode(self):
        """Start enhanced interactive mode with full command support"""
        print("🚀 Smart AI Enhanced Interactive Mode")
        print("=" * 50)
        print("Type /help for available commands")
        print("Type /status for current system status")
        print("Type /quit or /exit to exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💭 Smart AI> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("/quit", "/exit"):
                    # Auto-save before exit if enabled
                    if self.config.enable_autosave and self.conversation_history:
                        try:
                            await self.autosave_session("exit_autosave")
                            print("💾 Session auto-saved before exit")
                        except Exception:
                            pass
                    print("👋 Goodbye!")
                    break
                
                # Process command or input
                result = await self.process_command(user_input)
                print(result)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                if self.config.debug_mode:
                    import traceback
                    print(f"❌ Error: {e}\n{traceback.format_exc()}")
                else:
                    print(f"❌ Error: {e}")


# Factory function for easy initialization
def create_smart_ai(config: Optional[SmartAIConfig] = None) -> SmartAICore:
    """Create and initialize a Smart AI Core instance"""
    return SmartAICore(config)


# Example usage and testing
if __name__ == "__main__":
    import tempfile
    
    print("Smart AI Integration Test")
    print("=" * 30)
    
    # Create test configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        config = SmartAIConfig(
            session_directory=Path(temp_dir) / "sessions",
            debug_mode=True
        )
        
        # Create Smart AI instance
        smart_ai = create_smart_ai(config)
        
        # Test basic functionality
        print("✅ Smart AI Core initialized")
        print(f"✅ Session storage: {smart_ai.session_storage is not None}")
        print(f"✅ Notification manager: {smart_ai.notification_manager is not None}")
        print(f"✅ Command registry: {len(smart_ai.command_registry.commands)} commands registered")
        
        # Test command processing
        async def test_commands():
            print("\n🧪 Testing commands...")
            
            # Test help command
            help_result = await smart_ai.process_command("/help")
            print(f"Help command length: {len(help_result)} characters")
            
            # Test status command
            status_result = await smart_ai.process_command("/status")
            print(f"Status: {status_result}")
            
            print("✅ Command tests completed")
        
        # Run async tests
        asyncio.run(test_commands())
        
        print("\n✅ All tests passed!")
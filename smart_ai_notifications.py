#!/usr/bin/env python3
"""
Smart AI Notification System
Comprehensive notification framework for smart-ai slash commands with visual feedback,
system notifications, and configurable preferences.
"""

import asyncio
import json
import logging
import platform
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime
import threading
from queue import Queue, Empty
import os
import sys

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not available. Install with: pip install rich")

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("Warning: plyer library not available. Install with: pip install plyer")


class NotificationLevel(Enum):
    """Notification verbosity levels"""
    MINIMAL = "minimal"
    NORMAL = "normal"
    VERBOSE = "verbose"


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"
    COMMAND_START = "command_start"
    COMMAND_END = "command_end"


class CommandStatus(Enum):
    """Command execution statuses"""
    STARTING = "starting"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class NotificationConfig:
    """Configuration for notification preferences"""
    level: NotificationLevel = NotificationLevel.NORMAL
    enable_system_notifications: bool = True
    enable_terminal_notifications: bool = True
    enable_sound: bool = False
    enable_progress_bars: bool = True
    show_performance_metrics: bool = True
    auto_clear_success: bool = True
    auto_clear_delay: float = 3.0
    max_notification_history: int = 100
    notification_timeout: int = 5000  # milliseconds
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NotificationConfig':
        """Create from dictionary"""
        # Handle enum conversion
        if 'level' in data and isinstance(data['level'], str):
            try:
                data['level'] = NotificationLevel(data['level'])
            except ValueError:
                # Default to NORMAL if invalid level
                data['level'] = NotificationLevel.NORMAL
        return cls(**data)


@dataclass
class NotificationMessage:
    """Represents a single notification message"""
    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Optional[Dict] = None
    command: Optional[str] = None
    provider: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NotificationIcons:
    """Icon mappings for different notification types"""
    
    # Unicode icons for terminal display
    TERMINAL_ICONS = {
        NotificationType.INFO: "ℹ️",
        NotificationType.SUCCESS: "✅",
        NotificationType.WARNING: "⚠️",
        NotificationType.ERROR: "❌",
        NotificationType.PROGRESS: "🔄",
        NotificationType.COMMAND_START: "🚀",
        NotificationType.COMMAND_END: "🏁"
    }
    
    # Rich console styles
    RICH_STYLES = {
        NotificationType.INFO: "blue",
        NotificationType.SUCCESS: "green",
        NotificationType.WARNING: "yellow",
        NotificationType.ERROR: "red",
        NotificationType.PROGRESS: "cyan",
        NotificationType.COMMAND_START: "magenta",
        NotificationType.COMMAND_END: "green"
    }
    
    @classmethod
    def get_terminal_icon(cls, notification_type: NotificationType) -> str:
        return cls.TERMINAL_ICONS.get(notification_type, "📋")
    
    @classmethod
    def get_rich_style(cls, notification_type: NotificationType) -> str:
        return cls.RICH_STYLES.get(notification_type, "white")


class CommandNotificationSystem:
    """Visual command execution feedback system with rich terminal formatting"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.console = Console() if RICH_AVAILABLE else None
        self.active_commands: Dict[str, Dict] = {}
        self.command_history: List[Dict] = []
        self._progress_tasks: Dict[str, Any] = {}
        self._live_displays: Dict[str, Any] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def start_command(self, command_id: str, command: str, provider: Optional[str] = None) -> None:
        """Start tracking a command execution"""
        start_time = time.time()
        
        command_info = {
            'id': command_id,
            'command': command,
            'provider': provider,
            'status': CommandStatus.STARTING,
            'start_time': start_time,
            'end_time': None,
            'duration': None
        }
        
        self.active_commands[command_id] = command_info
        
        if self.config.enable_terminal_notifications:
            self._show_command_start(command_info)
    
    def update_command_progress(self, command_id: str, message: str, progress: Optional[float] = None) -> None:
        """Update command progress"""
        if command_id not in self.active_commands:
            return
            
        self.active_commands[command_id]['status'] = CommandStatus.RUNNING
        
        if self.config.enable_progress_bars and self.console:
            self._update_progress_display(command_id, message, progress)
    
    def complete_command(self, command_id: str, success: bool = True, message: Optional[str] = None, 
                        result_data: Optional[Dict] = None) -> None:
        """Complete a command execution"""
        if command_id not in self.active_commands:
            return
            
        command_info = self.active_commands[command_id]
        end_time = time.time()
        duration = end_time - command_info['start_time']
        
        command_info.update({
            'status': CommandStatus.SUCCESS if success else CommandStatus.ERROR,
            'end_time': end_time,
            'duration': duration,
            'result_message': message,
            'result_data': result_data
        })
        
        if self.config.enable_terminal_notifications:
            self._show_command_completion(command_info)
        
        # Move to history
        self.command_history.append(command_info.copy())
        if len(self.command_history) > self.config.max_notification_history:
            self.command_history.pop(0)
        
        # Cleanup
        self._cleanup_command_display(command_id)
        del self.active_commands[command_id]
    
    def cancel_command(self, command_id: str, reason: Optional[str] = None) -> None:
        """Cancel a command execution"""
        if command_id not in self.active_commands:
            return
            
        command_info = self.active_commands[command_id]
        command_info['status'] = CommandStatus.CANCELLED
        command_info['cancel_reason'] = reason
        
        if self.config.enable_terminal_notifications:
            self._show_command_cancellation(command_info)
        
        self._cleanup_command_display(command_id)
        del self.active_commands[command_id]
    
    def _show_command_start(self, command_info: Dict) -> None:
        """Display command start notification"""
        if not self.console:
            print(f"🚀 Starting: {command_info['command']}")
            return
            
        icon = NotificationIcons.get_terminal_icon(NotificationType.COMMAND_START)
        style = NotificationIcons.get_rich_style(NotificationType.COMMAND_START)
        
        provider_text = f" [{command_info['provider']}]" if command_info['provider'] else ""
        
        self.console.print(
            f"{icon} [bold {style}]Starting command:[/bold {style}] {command_info['command']}{provider_text}"
        )
    
    def _show_command_completion(self, command_info: Dict) -> None:
        """Display command completion notification"""
        if not self.console:
            status = "✅" if command_info['status'] == CommandStatus.SUCCESS else "❌"
            duration = f" ({command_info['duration']:.2f}s)" if self.config.show_performance_metrics else ""
            print(f"{status} {command_info['command']}{duration}")
            return
            
        is_success = command_info['status'] == CommandStatus.SUCCESS
        icon = NotificationIcons.get_terminal_icon(NotificationType.SUCCESS if is_success else NotificationType.ERROR)
        style = NotificationIcons.get_rich_style(NotificationType.SUCCESS if is_success else NotificationType.ERROR)
        
        status_text = "Completed" if is_success else "Failed"
        duration_text = f" ({command_info['duration']:.2f}s)" if self.config.show_performance_metrics else ""
        
        message_parts = [
            f"{icon} [bold {style}]{status_text}:[/bold {style}] {command_info['command']}{duration_text}"
        ]
        
        if command_info.get('result_message'):
            message_parts.append(f"   Result: {command_info['result_message']}")
        
        for part in message_parts:
            self.console.print(part)
    
    def _show_command_cancellation(self, command_info: Dict) -> None:
        """Display command cancellation notification"""
        if not self.console:
            print(f"🛑 Cancelled: {command_info['command']}")
            return
            
        reason_text = f" - {command_info.get('cancel_reason', 'User cancelled')}"
        self.console.print(f"🛑 [bold yellow]Cancelled:[/bold yellow] {command_info['command']}{reason_text}")
    
    def _update_progress_display(self, command_id: str, message: str, progress: Optional[float]) -> None:
        """Update progress display for command"""
        if not self.console:
            return
            
        # Simple progress indication for now
        if progress is not None:
            progress_bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
            self.console.print(f"   {progress_bar} {progress:.1%} - {message}")
        else:
            self.console.print(f"   🔄 {message}")
    
    def _cleanup_command_display(self, command_id: str) -> None:
        """Cleanup any ongoing displays for command"""
        if command_id in self._progress_tasks:
            del self._progress_tasks[command_id]
        if command_id in self._live_displays:
            del self._live_displays[command_id]
    
    def get_command_status(self, command_id: str) -> Optional[Dict]:
        """Get current status of a command"""
        return self.active_commands.get(command_id)
    
    def get_active_commands(self) -> List[Dict]:
        """Get all currently active commands"""
        return list(self.active_commands.values())
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get command execution history"""
        history = self.command_history
        if limit:
            history = history[-limit:]
        return history
    
    def show_status_table(self) -> None:
        """Display a table of active commands"""
        if not self.console or not self.active_commands:
            return
            
        table = Table(title="Active Commands")
        table.add_column("ID", style="cyan")
        table.add_column("Command", style="magenta")
        table.add_column("Provider", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Duration", style="blue")
        
        for cmd in self.active_commands.values():
            duration = time.time() - cmd['start_time']
            table.add_row(
                cmd['id'][:8],
                cmd['command'][:50],
                cmd.get('provider', 'N/A'),
                cmd['status'].value,
                f"{duration:.1f}s"
            )
        
        self.console.print(table)


class SystemNotificationManager:
    """Cross-platform system notifications with native integration"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.platform = platform.system().lower()
        self.notification_queue = Queue()
        self.worker_thread = None
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform-specific settings
        self._setup_platform_notifications()
        
    def _setup_platform_notifications(self) -> None:
        """Setup platform-specific notification settings"""
        if self.platform == "darwin":  # macOS
            self.app_name = "Smart AI"
            self.app_icon = None  # Could point to an icon file
        elif self.platform == "linux":
            self.app_name = "smart-ai"
            self.app_icon = None
        elif self.platform == "windows":
            self.app_name = "Smart AI"
            self.app_icon = None
        else:
            self.logger.warning(f"Unsupported platform for notifications: {self.platform}")
    
    def start(self) -> None:
        """Start the notification worker thread"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._notification_worker, daemon=True)
        self.worker_thread.start()
    
    def stop(self) -> None:
        """Stop the notification worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
    
    def send_notification(self, title: str, message: str, notification_type: NotificationType = NotificationType.INFO,
                         timeout: Optional[int] = None, actions: Optional[List[str]] = None) -> None:
        """Send a system notification"""
        if not self.config.enable_system_notifications:
            return
            
        notification_data = {
            'title': title,
            'message': message,
            'type': notification_type,
            'timeout': timeout or self.config.notification_timeout,
            'actions': actions or [],
            'timestamp': datetime.now()
        }
        
        self.notification_queue.put(notification_data)
        
        if not self.running:
            self.start()
    
    def _notification_worker(self) -> None:
        """Worker thread for processing notifications"""
        while self.running:
            try:
                notification_data = self.notification_queue.get(timeout=1.0)
                self._send_platform_notification(notification_data)
                self.notification_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error sending notification: {e}")
    
    def _send_platform_notification(self, notification_data: Dict) -> None:
        """Send notification using platform-specific method"""
        if not PLYER_AVAILABLE:
            self._fallback_notification(notification_data)
            return
            
        try:
            plyer_notification.notify(
                title=notification_data['title'],
                message=notification_data['message'],
                app_name=self.app_name,
                app_icon=self.app_icon,
                timeout=notification_data['timeout'] / 1000.0  # Convert to seconds
            )
        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}")
            self._fallback_notification(notification_data)
    
    def _fallback_notification(self, notification_data: Dict) -> None:
        """Fallback notification method when system notifications fail"""
        # Try platform-specific fallbacks
        if self.platform == "darwin":
            self._macos_fallback_notification(notification_data)
        elif self.platform == "linux":
            self._linux_fallback_notification(notification_data)
        else:
            # Last resort: print to console
            print(f"NOTIFICATION: {notification_data['title']} - {notification_data['message']}")
    
    def _macos_fallback_notification(self, notification_data: Dict) -> None:
        """macOS fallback using osascript"""
        try:
            import subprocess
            script = f'''
            display notification "{notification_data['message']}" with title "{notification_data['title']}"
            '''
            subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
        except Exception as e:
            self.logger.error(f"macOS fallback notification failed: {e}")
    
    def _linux_fallback_notification(self, notification_data: Dict) -> None:
        """Linux fallback using notify-send"""
        try:
            import subprocess
            subprocess.run([
                'notify-send',
                notification_data['title'],
                notification_data['message']
            ], check=True, capture_output=True)
        except Exception as e:
            self.logger.error(f"Linux fallback notification failed: {e}")


class NotificationManager:
    """Main notification manager coordinating all notification systems"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path.home() / '.smart_ai' / 'notifications.json'
        self.config = self._load_config()
        
        # Initialize subsystems
        self.command_system = CommandNotificationSystem(self.config)
        self.system_manager = SystemNotificationManager(self.config)
        
        # Notification history
        self.notification_history: List[NotificationMessage] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Start systems
        self.system_manager.start()
    
    def _load_config(self) -> NotificationConfig:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                return NotificationConfig.from_dict(data)
            except Exception as e:
                print(f"Warning: Failed to load notification config: {e}")
        
        # Create default config and save it
        config = NotificationConfig()
        self.save_config(config)
        return config
    
    def save_config(self, config: Optional[NotificationConfig] = None) -> None:
        """Save configuration to file"""
        config = config or self.config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save notification config: {e}")
    
    def update_config(self, **kwargs) -> None:
        """Update configuration settings"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Update subsystem configs
        self.command_system.config = self.config
        self.system_manager.config = self.config
        
        self.save_config()
    
    def notify(self, title: str, message: str, notification_type: NotificationType = NotificationType.INFO,
              command: Optional[str] = None, provider: Optional[str] = None, 
              show_system: Optional[bool] = None, duration: Optional[float] = None,
              metadata: Optional[Dict] = None) -> str:
        """Send a notification through all enabled channels"""
        
        # Generate unique ID
        notification_id = f"notif_{int(time.time() * 1000)}"
        
        # Create notification message
        notification_msg = NotificationMessage(
            id=notification_id,
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            duration=duration,
            metadata=metadata,
            command=command,
            provider=provider
        )
        
        # Add to history
        self.notification_history.append(notification_msg)
        if len(self.notification_history) > self.config.max_notification_history:
            self.notification_history.pop(0)
        
        # Send terminal notification
        if self.config.enable_terminal_notifications:
            self._send_terminal_notification(notification_msg)
        
        # Send system notification
        should_send_system = show_system if show_system is not None else self.config.enable_system_notifications
        if should_send_system and self._should_send_system_notification(notification_type):
            self.system_manager.send_notification(title, message, notification_type)
        
        return notification_id
    
    def _should_send_system_notification(self, notification_type: NotificationType) -> bool:
        """Determine if system notification should be sent based on config and type"""
        if self.config.level == NotificationLevel.MINIMAL:
            return notification_type in [NotificationType.ERROR, NotificationType.SUCCESS]
        elif self.config.level == NotificationLevel.NORMAL:
            return notification_type != NotificationType.PROGRESS
        else:  # VERBOSE
            return True
    
    def _send_terminal_notification(self, notification: NotificationMessage) -> None:
        """Send terminal notification"""
        if self.command_system.console:
            icon = NotificationIcons.get_terminal_icon(notification.type)
            style = NotificationIcons.get_rich_style(notification.type)
            
            # Format message with metadata
            message_parts = [f"{icon} [bold {style}]{notification.title}[/bold {style}]"]
            if notification.message:
                message_parts.append(f"   {notification.message}")
            
            if notification.provider and self.config.show_performance_metrics:
                message_parts.append(f"   Provider: {notification.provider}")
            
            if notification.duration and self.config.show_performance_metrics:
                message_parts.append(f"   Duration: {notification.duration:.2f}s")
            
            for part in message_parts:
                self.command_system.console.print(part)
        else:
            # Fallback for no rich
            icon = NotificationIcons.get_terminal_icon(notification.type)
            print(f"{icon} {notification.title}: {notification.message}")
    
    # Command execution methods
    def start_command(self, command_id: str, command: str, provider: Optional[str] = None) -> None:
        """Start tracking a command execution"""
        self.command_system.start_command(command_id, command, provider)
        
        # Send notification if enabled
        if self.config.level == NotificationLevel.VERBOSE:
            self.notify(
                title="Command Started",
                message=f"Executing: {command}",
                notification_type=NotificationType.COMMAND_START,
                command=command,
                provider=provider,
                show_system=False  # Don't spam system notifications for command starts
            )
    
    def update_command_progress(self, command_id: str, message: str, progress: Optional[float] = None) -> None:
        """Update command progress"""
        self.command_system.update_command_progress(command_id, message, progress)
    
    def complete_command(self, command_id: str, success: bool = True, message: Optional[str] = None,
                        result_data: Optional[Dict] = None, duration: Optional[float] = None) -> None:
        """Complete a command execution"""
        self.command_system.complete_command(command_id, success, message, result_data)
        
        # Send completion notification
        command_info = self.command_system.get_command_status(command_id)
        if command_info:
            notification_type = NotificationType.SUCCESS if success else NotificationType.ERROR
            title = "Command Completed" if success else "Command Failed"
            
            self.notify(
                title=title,
                message=message or f"Command: {command_info['command']}",
                notification_type=notification_type,
                command=command_info['command'],
                provider=command_info.get('provider'),
                duration=duration,
                show_system=not success or self.config.level == NotificationLevel.VERBOSE  # System notify on errors or verbose
            )
    
    def cancel_command(self, command_id: str, reason: Optional[str] = None) -> None:
        """Cancel a command execution"""
        self.command_system.cancel_command(command_id, reason)
    
    # Utility methods
    def get_notification_history(self, limit: Optional[int] = None, 
                               notification_type: Optional[NotificationType] = None) -> List[NotificationMessage]:
        """Get notification history with optional filtering"""
        history = self.notification_history
        
        if notification_type:
            history = [n for n in history if n.type == notification_type]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self) -> None:
        """Clear notification history"""
        self.notification_history.clear()
    
    def show_status(self) -> None:
        """Display current notification system status"""
        if self.command_system.console:
            self.command_system.show_status_table()
        else:
            print("Active commands:", len(self.command_system.active_commands))
            for cmd in self.command_system.active_commands.values():
                print(f"  {cmd['id']}: {cmd['command']} ({cmd['status'].value})")
    
    def shutdown(self) -> None:
        """Gracefully shutdown notification systems"""
        self.system_manager.stop()


# Integration hooks and utilities
class NotificationHooks:
    """Integration hooks for smart-ai command execution"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.manager = notification_manager
    
    def before_command_execution(self, command: str, provider: str, command_id: str) -> None:
        """Hook called before command execution"""
        self.manager.start_command(command_id, command, provider)
    
    def after_command_execution(self, command_id: str, success: bool, result: Any = None, 
                               error: Optional[Exception] = None, duration: Optional[float] = None) -> None:
        """Hook called after command execution"""
        if error:
            message = f"Error: {str(error)}"
        elif result:
            message = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
        else:
            message = "Command completed successfully"
        
        self.manager.complete_command(command_id, success, message, duration=duration)
    
    def on_command_progress(self, command_id: str, message: str, progress: Optional[float] = None) -> None:
        """Hook called during command execution for progress updates"""
        self.manager.update_command_progress(command_id, message, progress)
    
    def on_mcp_tool_execution(self, tool_name: str, parameters: Dict, result: Any) -> None:
        """Hook for MCP tool execution feedback"""
        self.manager.notify(
            title="MCP Tool Executed",
            message=f"Tool: {tool_name}",
            notification_type=NotificationType.INFO,
            metadata={'tool': tool_name, 'parameters': parameters},
            show_system=False
        )


# Provider-specific notification styles
class ProviderNotificationStyles:
    """Provider-specific notification customizations"""
    
    STYLES = {
        'claude': {
            'color': 'blue',
            'icon': '🤖',
            'name': 'Claude'
        },
        'openai': {
            'color': 'green',
            'icon': '🌟',
            'name': 'OpenAI'
        },
        'gemini': {
            'color': 'cyan',
            'icon': '💎',
            'name': 'Gemini'
        },
        'anthropic': {
            'color': 'blue',
            'icon': '🔷',
            'name': 'Anthropic'
        },
        'local': {
            'color': 'magenta',
            'icon': '🏠',
            'name': 'Local'
        }
    }
    
    @classmethod
    def get_style(cls, provider: str) -> Dict:
        """Get style for provider"""
        return cls.STYLES.get(provider.lower(), {
            'color': 'white',
            'icon': '🤖',
            'name': provider.title()
        })


# Testing utilities
def create_test_notifications(manager: NotificationManager) -> None:
    """Create test notifications for development/testing"""
    test_cases = [
        ("Test Info", "This is an info notification", NotificationType.INFO),
        ("Test Success", "Command completed successfully", NotificationType.SUCCESS),
        ("Test Warning", "This is a warning message", NotificationType.WARNING),
        ("Test Error", "An error occurred", NotificationType.ERROR),
    ]
    
    for title, message, ntype in test_cases:
        manager.notify(title, message, ntype)
        time.sleep(0.5)


def demo_command_execution(manager: NotificationManager) -> None:
    """Demonstrate command execution notifications"""
    import uuid
    
    command_id = str(uuid.uuid4())
    
    # Start command
    manager.start_command(command_id, "/ask What is the weather?", "claude")
    
    # Simulate progress
    time.sleep(1)
    manager.update_command_progress(command_id, "Processing request...", 0.3)
    
    time.sleep(1)
    manager.update_command_progress(command_id, "Generating response...", 0.7)
    
    time.sleep(1)
    manager.complete_command(command_id, True, "Weather information retrieved successfully")


if __name__ == "__main__":
    # Example usage and testing
    print("Smart AI Notification System")
    print("=" * 50)
    
    # Create notification manager
    manager = NotificationManager()
    
    try:
        # Demo basic notifications
        print("\n1. Testing basic notifications...")
        create_test_notifications(manager)
        
        time.sleep(2)
        
        # Demo command execution
        print("\n2. Testing command execution...")
        demo_command_execution(manager)
        
        time.sleep(2)
        
        # Show status
        print("\n3. Current status:")
        manager.show_status()
        
        # Show history
        print("\n4. Recent notifications:")
        history = manager.get_notification_history(limit=5)
        for notif in history:
            print(f"  {notif.timestamp.strftime('%H:%M:%S')} - {notif.title}: {notif.message}")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        manager.shutdown()
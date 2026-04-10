#!/usr/bin/env python3
"""
Smart AI Notification System - Testing Utilities
Comprehensive testing framework for notification system validation.
"""

import unittest
import asyncio
import tempfile
import json
import time
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from smart_ai_notifications import (
    NotificationManager, NotificationConfig, NotificationLevel, NotificationType,
    CommandNotificationSystem, SystemNotificationManager, NotificationHooks,
    NotificationMessage, ProviderNotificationStyles
)


class TestNotificationConfig(unittest.TestCase):
    """Test notification configuration functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = NotificationConfig()
        self.assertEqual(config.level, NotificationLevel.NORMAL)
        self.assertTrue(config.enable_system_notifications)
        self.assertTrue(config.enable_terminal_notifications)
        self.assertFalse(config.enable_sound)
        self.assertTrue(config.enable_progress_bars)
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization"""
        config = NotificationConfig(
            level=NotificationLevel.VERBOSE,
            enable_system_notifications=False,
            notification_timeout=10000
        )
        
        # Test to_dict
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['level'], NotificationLevel.VERBOSE)
        self.assertFalse(config_dict['enable_system_notifications'])
        self.assertEqual(config_dict['notification_timeout'], 10000)
        
        # Test from_dict
        restored_config = NotificationConfig.from_dict(config_dict)
        self.assertEqual(restored_config.level, NotificationLevel.VERBOSE)
        self.assertFalse(restored_config.enable_system_notifications)
        self.assertEqual(restored_config.notification_timeout, 10000)
    
    def test_config_enum_handling(self):
        """Test proper enum handling in configuration"""
        config_dict = {
            'level': 'verbose',
            'enable_system_notifications': True
        }
        
        config = NotificationConfig.from_dict(config_dict)
        self.assertEqual(config.level, NotificationLevel.VERBOSE)


class TestNotificationMessage(unittest.TestCase):
    """Test notification message structure"""
    
    def test_notification_message_creation(self):
        """Test notification message creation"""
        msg = NotificationMessage(
            id="test_123",
            type=NotificationType.SUCCESS,
            title="Test Title",
            message="Test message",
            timestamp=time.time()
        )
        
        self.assertEqual(msg.id, "test_123")
        self.assertEqual(msg.type, NotificationType.SUCCESS)
        self.assertEqual(msg.title, "Test Title")
        self.assertEqual(msg.message, "Test message")
        self.assertIsInstance(msg.metadata, dict)
    
    def test_notification_message_with_metadata(self):
        """Test notification message with metadata"""
        metadata = {"command": "/ask", "provider": "claude"}
        msg = NotificationMessage(
            id="test_123",
            type=NotificationType.INFO,
            title="Test",
            message="Test",
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.assertEqual(msg.metadata, metadata)


class TestCommandNotificationSystem(unittest.TestCase):
    """Test command notification system"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = NotificationConfig()
        self.system = CommandNotificationSystem(self.config)
    
    def test_command_lifecycle(self):
        """Test complete command lifecycle"""
        command_id = "test_cmd_123"
        command = "/ask Test question"
        provider = "claude"
        
        # Start command
        self.system.start_command(command_id, command, provider)
        self.assertIn(command_id, self.system.active_commands)
        
        cmd_info = self.system.get_command_status(command_id)
        self.assertIsNotNone(cmd_info)
        self.assertEqual(cmd_info['command'], command)
        self.assertEqual(cmd_info['provider'], provider)
        
        # Update progress
        self.system.update_command_progress(command_id, "Processing...", 0.5)
        cmd_info = self.system.get_command_status(command_id)
        self.assertEqual(cmd_info['status'].value, "running")
        
        # Complete command
        self.system.complete_command(command_id, True, "Success!")
        self.assertNotIn(command_id, self.system.active_commands)
        
        # Check history
        history = self.system.get_command_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['command'], command)
    
    def test_command_cancellation(self):
        """Test command cancellation"""
        command_id = "test_cancel_123"
        
        self.system.start_command(command_id, "/test Cancel test", "test")
        self.assertIn(command_id, self.system.active_commands)
        
        self.system.cancel_command(command_id, "User cancelled")
        self.assertNotIn(command_id, self.system.active_commands)
    
    def test_command_error_handling(self):
        """Test command error scenarios"""
        command_id = "test_error_123"
        
        self.system.start_command(command_id, "/test Error test", "test")
        self.system.complete_command(command_id, False, "Error occurred")
        
        history = self.system.get_command_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['status'].value, "error")
    
    def test_multiple_active_commands(self):
        """Test handling multiple active commands"""
        command_ids = ["cmd1", "cmd2", "cmd3"]
        
        for cmd_id in command_ids:
            self.system.start_command(cmd_id, f"/test {cmd_id}", "test")
        
        active_commands = self.system.get_active_commands()
        self.assertEqual(len(active_commands), 3)
        
        # Complete one command
        self.system.complete_command("cmd2", True)
        active_commands = self.system.get_active_commands()
        self.assertEqual(len(active_commands), 2)


class TestSystemNotificationManager(unittest.TestCase):
    """Test system notification manager"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = NotificationConfig()
        self.manager = SystemNotificationManager(self.config)
    
    def test_notification_queue(self):
        """Test notification queueing"""
        self.manager.send_notification(
            "Test Title",
            "Test message",
            NotificationType.INFO
        )
        
        # Check that notification was queued
        self.assertFalse(self.manager.notification_queue.empty())
    
    def test_manager_lifecycle(self):
        """Test manager start/stop lifecycle"""
        self.assertFalse(self.manager.running)
        
        self.manager.start()
        self.assertTrue(self.manager.running)
        self.assertIsNotNone(self.manager.worker_thread)
        
        self.manager.stop()
        self.assertFalse(self.manager.running)
    
    def test_platform_detection(self):
        """Test platform-specific configuration"""
        # This will vary by platform, so just check it's set
        self.assertIsNotNone(self.manager.platform)
        self.assertIsNotNone(self.manager.app_name)


class TestNotificationManager(unittest.TestCase):
    """Test main notification manager"""
    
    def setUp(self):
        """Set up test environment"""
        # Use temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_notifications.json"
        self.manager = NotificationManager(config_path=str(self.config_path))
    
    def tearDown(self):
        """Clean up test environment"""
        self.manager.shutdown()
    
    def test_config_persistence(self):
        """Test configuration file persistence"""
        # Update config
        self.manager.update_config(
            level=NotificationLevel.VERBOSE,
            enable_sound=True
        )
        
        # Check file was created
        self.assertTrue(self.config_path.exists())
        
        # Load config from file
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['level'], 'verbose')
        self.assertTrue(saved_config['enable_sound'])
    
    def test_notification_sending(self):
        """Test sending notifications"""
        notification_id = self.manager.notify(
            "Test Title",
            "Test message",
            NotificationType.SUCCESS
        )
        
        self.assertIsNotNone(notification_id)
        
        # Check history
        history = self.manager.get_notification_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].title, "Test Title")
    
    def test_notification_filtering(self):
        """Test notification history filtering"""
        # Send different types of notifications
        self.manager.notify("Info", "Info message", NotificationType.INFO)
        self.manager.notify("Error", "Error message", NotificationType.ERROR)
        self.manager.notify("Success", "Success message", NotificationType.SUCCESS)
        
        # Filter by type
        error_notifications = self.manager.get_notification_history(
            notification_type=NotificationType.ERROR
        )
        self.assertEqual(len(error_notifications), 1)
        self.assertEqual(error_notifications[0].title, "Error")
        
        # Limit results
        limited_notifications = self.manager.get_notification_history(limit=2)
        self.assertEqual(len(limited_notifications), 2)
    
    def test_command_integration(self):
        """Test command execution integration"""
        command_id = str(uuid.uuid4())
        
        self.manager.start_command(command_id, "/test Integration test", "test")
        self.manager.update_command_progress(command_id, "Testing...", 0.5)
        self.manager.complete_command(command_id, True, "Test completed")
        
        # Check notifications were generated
        history = self.manager.get_notification_history()
        self.assertGreater(len(history), 0)
    
    def test_notification_levels(self):
        """Test different notification levels"""
        levels = [NotificationLevel.MINIMAL, NotificationLevel.NORMAL, NotificationLevel.VERBOSE]
        
        for level in levels:
            self.manager.update_config(level=level)
            
            # Send various notifications
            self.manager.notify("Test", "Test", NotificationType.INFO)
            self.manager.notify("Test", "Test", NotificationType.PROGRESS)
            self.manager.notify("Test", "Test", NotificationType.ERROR)
            
            # Clear history for next test
            self.manager.clear_history()


class TestNotificationHooks(unittest.TestCase):
    """Test notification hooks"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = NotificationManager()
        self.hooks = NotificationHooks(self.manager)
    
    def tearDown(self):
        """Clean up test environment"""
        self.manager.shutdown()
    
    def test_command_execution_hooks(self):
        """Test command execution hooks"""
        command_id = str(uuid.uuid4())
        command = "/test Hook test"
        provider = "test"
        
        # Before execution
        self.hooks.before_command_execution(command, provider, command_id)
        
        # Progress update
        self.hooks.on_command_progress(command_id, "Processing...", 0.5)
        
        # After execution
        self.hooks.after_command_execution(command_id, True, "Success")
        
        # Check notifications were generated
        history = self.manager.get_notification_history()
        self.assertGreater(len(history), 0)
    
    def test_mcp_tool_hook(self):
        """Test MCP tool execution hook"""
        self.hooks.on_mcp_tool_execution(
            "test_tool",
            {"param1": "value1"},
            "Tool result"
        )
        
        history = self.manager.get_notification_history()
        self.assertEqual(len(history), 1)
        self.assertIn("MCP Tool", history[0].title)


class TestProviderNotificationStyles(unittest.TestCase):
    """Test provider-specific notification styles"""
    
    def test_known_providers(self):
        """Test styles for known providers"""
        providers = ["claude", "openai", "gemini", "anthropic", "local"]
        
        for provider in providers:
            style = ProviderNotificationStyles.get_style(provider)
            self.assertIn('color', style)
            self.assertIn('icon', style)
            self.assertIn('name', style)
    
    def test_unknown_provider(self):
        """Test fallback for unknown providers"""
        style = ProviderNotificationStyles.get_style("unknown_provider")
        self.assertEqual(style['color'], 'white')
        self.assertEqual(style['icon'], '🤖')
        self.assertEqual(style['name'], 'Unknown_Provider')


class TestAsyncNotifications(unittest.TestCase):
    """Test async notification functionality"""
    
    def setUp(self):
        """Set up async test environment"""
        self.manager = NotificationManager()
    
    def tearDown(self):
        """Clean up async test environment"""
        self.manager.shutdown()
    
    async def test_concurrent_commands(self):
        """Test concurrent command notifications"""
        command_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        # Start multiple commands
        for i, cmd_id in enumerate(command_ids):
            self.manager.start_command(cmd_id, f"/test Async test {i}", "test")
        
        # Simulate concurrent processing
        await asyncio.sleep(0.1)
        
        # Complete all commands
        for cmd_id in command_ids:
            self.manager.complete_command(cmd_id, True, "Async test completed")
        
        # Check history
        history = self.manager.get_notification_history()
        self.assertGreaterEqual(len(history), 3)
    
    def test_async_command_execution(self):
        """Test async command execution"""
        asyncio.run(self.test_concurrent_commands())


class NotificationTestSuite:
    """Comprehensive test suite for notification system"""
    
    @staticmethod
    def run_all_tests():
        """Run all notification system tests"""
        test_classes = [
            TestNotificationConfig,
            TestNotificationMessage,
            TestCommandNotificationSystem,
            TestSystemNotificationManager,
            TestNotificationManager,
            TestNotificationHooks,
            TestProviderNotificationStyles,
            TestAsyncNotifications
        ]
        
        suite = unittest.TestSuite()
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    @staticmethod
    def run_performance_tests():
        """Run performance tests for notification system"""
        print("Running performance tests...")
        
        manager = NotificationManager()
        
        # Test notification throughput
        start_time = time.time()
        num_notifications = 1000
        
        for i in range(num_notifications):
            manager.notify(
                f"Perf Test {i}",
                f"Performance test notification {i}",
                NotificationType.INFO
            )
        
        elapsed = time.time() - start_time
        throughput = num_notifications / elapsed
        
        print(f"Notification throughput: {throughput:.2f} notifications/second")
        
        # Test command execution performance
        start_time = time.time()
        num_commands = 100
        
        for i in range(num_commands):
            command_id = f"perf_cmd_{i}"
            manager.start_command(command_id, f"/test Perf test {i}", "test")
            manager.complete_command(command_id, True, f"Completed {i}")
        
        elapsed = time.time() - start_time
        command_throughput = num_commands / elapsed
        
        print(f"Command notification throughput: {command_throughput:.2f} commands/second")
        
        manager.shutdown()
        
        return throughput, command_throughput
    
    @staticmethod
    def run_stress_tests():
        """Run stress tests for notification system"""
        print("Running stress tests...")
        
        manager = NotificationManager()
        
        # Test memory usage with large notification history
        for i in range(10000):
            manager.notify(
                f"Stress Test {i}",
                f"Stress test notification with longer message content {i} " * 10,
                NotificationType.INFO
            )
        
        history_size = len(manager.get_notification_history())
        print(f"Notification history size: {history_size}")
        
        # Test concurrent command execution
        import threading
        
        def worker(worker_id, num_commands):
            for i in range(num_commands):
                command_id = f"stress_worker_{worker_id}_cmd_{i}"
                manager.start_command(command_id, f"/test Stress {worker_id}-{i}", "test")
                time.sleep(0.001)  # Small delay to simulate real usage
                manager.complete_command(command_id, True, f"Completed {worker_id}-{i}")
        
        threads = []
        num_workers = 10
        commands_per_worker = 100
        
        start_time = time.time()
        
        for worker_id in range(num_workers):
            thread = threading.Thread(target=worker, args=(worker_id, commands_per_worker))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        total_commands = num_workers * commands_per_worker
        
        print(f"Concurrent stress test: {total_commands} commands in {elapsed:.2f}s")
        print(f"Concurrent throughput: {total_commands / elapsed:.2f} commands/second")
        
        manager.shutdown()


def main():
    """Main testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart AI Notification System Tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--stress", action="store_true", help="Run stress tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.all or args.unit:
        print("Running unit tests...")
        success = NotificationTestSuite.run_all_tests()
        print(f"Unit tests {'PASSED' if success else 'FAILED'}")
    
    if args.all or args.performance:
        print("\nRunning performance tests...")
        NotificationTestSuite.run_performance_tests()
    
    if args.all or args.stress:
        print("\nRunning stress tests...")
        NotificationTestSuite.run_stress_tests()
    
    if not any([args.unit, args.performance, args.stress, args.all]):
        print("Smart AI Notification System - Testing Utilities")
        print("Usage: python notification_testing.py [--unit] [--performance] [--stress] [--all]")
        print("\nTest categories:")
        print("  --unit       Run unit tests")
        print("  --performance Run performance tests")
        print("  --stress     Run stress tests")
        print("  --all        Run all tests")


if __name__ == "__main__":
    main()
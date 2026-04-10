#!/usr/bin/env python3
"""
Smart AI Notification System - Usage Examples
Demonstrates various notification patterns and integration scenarios.
"""

import time
import uuid
import asyncio
from smart_ai_notifications import (
    NotificationManager, NotificationHooks, NotificationType, 
    NotificationLevel, create_test_notifications, demo_command_execution
)


class SmartAICommandSimulator:
    """Simulates smart-ai command execution with notifications"""
    
    def __init__(self):
        self.notification_manager = NotificationManager()
        self.hooks = NotificationHooks(self.notification_manager)
        
    async def execute_command(self, command: str, provider: str = "claude") -> str:
        """Simulate executing a smart-ai command with full notification lifecycle"""
        command_id = str(uuid.uuid4())
        
        try:
            # Before execution hook
            self.hooks.before_command_execution(command, provider, command_id)
            
            # Simulate command processing
            await self._simulate_command_processing(command_id, command)
            
            # Simulate successful completion
            result = f"Successfully executed: {command}"
            self.hooks.after_command_execution(command_id, True, result, duration=2.5)
            
            return result
            
        except Exception as e:
            # Handle errors
            self.hooks.after_command_execution(command_id, False, error=e)
            raise
    
    async def _simulate_command_processing(self, command_id: str, command: str):
        """Simulate the various stages of command processing"""
        stages = [
            ("Parsing command...", 0.1),
            ("Connecting to provider...", 0.3),
            ("Sending request...", 0.5),
            ("Processing response...", 0.8),
            ("Formatting output...", 0.9),
            ("Finalizing...", 1.0)
        ]
        
        for message, progress in stages:
            self.hooks.on_command_progress(command_id, message, progress)
            await asyncio.sleep(0.5)  # Simulate processing time


def example_basic_notifications():
    """Example 1: Basic notification usage"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Notifications")
    print("="*60)
    
    manager = NotificationManager()
    
    # Different types of notifications
    notifications = [
        ("Welcome", "Smart AI notification system initialized", NotificationType.SUCCESS),
        ("Processing", "Analyzing your request...", NotificationType.INFO),
        ("Warning", "Rate limit approaching", NotificationType.WARNING),
        ("Error", "Failed to connect to provider", NotificationType.ERROR),
    ]
    
    for title, message, ntype in notifications:
        print(f"Sending: {title}")
        manager.notify(title, message, ntype)
        time.sleep(1)
    
    manager.shutdown()


def example_command_lifecycle():
    """Example 2: Complete command execution lifecycle"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Command Execution Lifecycle")
    print("="*60)
    
    manager = NotificationManager()
    command_id = str(uuid.uuid4())
    
    # Start command
    print("Starting command execution...")
    manager.start_command(command_id, "/ask Explain quantum computing", "claude")
    
    # Progress updates
    progress_updates = [
        ("Initializing request...", 0.1),
        ("Connecting to Claude API...", 0.3),
        ("Sending query...", 0.5),
        ("Receiving response...", 0.7),
        ("Processing content...", 0.9),
        ("Finalizing output...", 1.0)
    ]
    
    for message, progress in progress_updates:
        print(f"Progress: {message} ({progress:.0%})")
        manager.update_command_progress(command_id, message, progress)
        time.sleep(0.8)
    
    # Complete successfully
    print("Command completed successfully!")
    manager.complete_command(
        command_id, 
        success=True, 
        message="Generated comprehensive explanation of quantum computing",
        duration=4.8
    )
    
    time.sleep(1)
    manager.shutdown()


def example_error_handling():
    """Example 3: Error handling and notifications"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Error Handling")
    print("="*60)
    
    manager = NotificationManager()
    command_id = str(uuid.uuid4())
    
    # Start command
    manager.start_command(command_id, "/search Invalid query syntax", "openai")
    
    # Simulate some progress before error
    manager.update_command_progress(command_id, "Validating query...", 0.2)
    time.sleep(1)
    
    manager.update_command_progress(command_id, "Parsing syntax...", 0.4)
    time.sleep(1)
    
    # Simulate error
    print("Error occurred during execution!")
    manager.complete_command(
        command_id, 
        success=False, 
        message="Syntax error: Invalid query format",
        duration=2.1
    )
    
    # Additional error notification
    manager.notify(
        "Syntax Error",
        "Please check your query syntax and try again",
        NotificationType.ERROR,
        command="/search Invalid query syntax",
        provider="openai"
    )
    
    time.sleep(1)
    manager.shutdown()


def example_configuration_levels():
    """Example 4: Different notification levels"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Notification Levels")
    print("="*60)
    
    levels = [
        NotificationLevel.MINIMAL,
        NotificationLevel.NORMAL,
        NotificationLevel.VERBOSE
    ]
    
    for level in levels:
        print(f"\nTesting {level.value.upper()} notification level:")
        
        # Create manager with specific level
        manager = NotificationManager()
        manager.update_config(level=level)
        
        # Test various notification types
        test_notifications = [
            ("Info", "This is an info message", NotificationType.INFO),
            ("Progress", "Processing data...", NotificationType.PROGRESS),
            ("Success", "Operation completed", NotificationType.SUCCESS),
            ("Error", "Something went wrong", NotificationType.ERROR)
        ]
        
        for title, message, ntype in test_notifications:
            manager.notify(title, message, ntype)
            time.sleep(0.3)
        
        time.sleep(1)
        manager.shutdown()


def example_provider_specific():
    """Example 5: Provider-specific notifications"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Provider-Specific Notifications")
    print("="*60)
    
    manager = NotificationManager()
    
    providers = ["claude", "openai", "gemini", "local"]
    
    for provider in providers:
        print(f"Testing {provider} provider notifications...")
        
        command_id = str(uuid.uuid4())
        manager.start_command(command_id, f"/ask Hello from {provider}", provider)
        
        time.sleep(0.5)
        manager.update_command_progress(command_id, f"Processing with {provider}...", 0.5)
        
        time.sleep(0.5)
        manager.complete_command(command_id, True, f"Response received from {provider}")
        
        time.sleep(0.5)
    
    manager.shutdown()


async def example_async_simulation():
    """Example 6: Async command simulation"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Async Command Simulation")
    print("="*60)
    
    simulator = SmartAICommandSimulator()
    
    commands = [
        "/ask What's the weather today?",
        "/search Python asyncio tutorial",
        "/generate Write a haiku about coding",
        "/analyze Review this code snippet"
    ]
    
    # Execute commands concurrently
    tasks = []
    for command in commands:
        task = asyncio.create_task(simulator.execute_command(command))
        tasks.append(task)
        await asyncio.sleep(0.5)  # Stagger command starts
    
    # Wait for all commands to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\nAll commands completed!")
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Command {i+1} failed: {result}")
        else:
            print(f"Command {i+1}: {result}")
    
    simulator.notification_manager.shutdown()


def example_notification_history():
    """Example 7: Notification history and analytics"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Notification History")
    print("="*60)
    
    manager = NotificationManager()
    
    # Generate some notifications
    for i in range(10):
        manager.notify(
            f"Task {i+1}",
            f"Completed task number {i+1}",
            NotificationType.SUCCESS if i % 3 != 0 else NotificationType.ERROR,
            command=f"/task{i+1}",
            provider="claude" if i % 2 == 0 else "openai"
        )
        time.sleep(0.2)
    
    # Show history
    print("\nNotification History:")
    history = manager.get_notification_history(limit=5)
    for notif in history:
        timestamp = notif.timestamp.strftime("%H:%M:%S")
        print(f"  {timestamp} | {notif.type.value:8} | {notif.title} | {notif.message}")
    
    # Show error notifications only
    print("\nError Notifications Only:")
    error_history = manager.get_notification_history(notification_type=NotificationType.ERROR)
    for notif in error_history:
        timestamp = notif.timestamp.strftime("%H:%M:%S")
        print(f"  {timestamp} | ERROR | {notif.title} | {notif.message}")
    
    # Show current status
    print("\nCurrent System Status:")
    manager.show_status()
    
    manager.shutdown()


def example_custom_configuration():
    """Example 8: Custom configuration"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Custom Configuration")
    print("="*60)
    
    # Create manager with custom config path
    manager = NotificationManager(config_path="/tmp/custom_notifications.json")
    
    # Update configuration
    print("Updating configuration...")
    manager.update_config(
        level=NotificationLevel.VERBOSE,
        enable_system_notifications=True,
        show_performance_metrics=True,
        auto_clear_delay=1.0,
        notification_timeout=3000
    )
    
    print("Configuration updated. Testing with new settings...")
    
    # Test with new configuration
    command_id = str(uuid.uuid4())
    start_time = time.time()
    
    manager.start_command(command_id, "/test Custom config test", "claude")
    manager.update_command_progress(command_id, "Testing custom settings...", 0.5)
    
    time.sleep(1)
    
    duration = time.time() - start_time
    manager.complete_command(command_id, True, "Custom configuration test completed", duration=duration)
    
    print(f"Test completed in {duration:.2f} seconds")
    
    manager.shutdown()


def run_all_examples():
    """Run all examples in sequence"""
    print("Smart AI Notification System - Examples")
    print("="*60)
    print("Running comprehensive notification examples...")
    
    examples = [
        ("Basic Notifications", example_basic_notifications),
        ("Command Lifecycle", example_command_lifecycle),
        ("Error Handling", example_error_handling),
        ("Configuration Levels", example_configuration_levels),
        ("Provider Specific", example_provider_specific),
        ("Notification History", example_notification_history),
        ("Custom Configuration", example_custom_configuration)
    ]
    
    for name, example_func in examples:
        print(f"\n🔹 Running: {name}")
        try:
            example_func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
        
        time.sleep(1)  # Brief pause between examples
    
    # Run async example separately
    print(f"\n🔹 Running: Async Command Simulation")
    try:
        asyncio.run(example_async_simulation())
        print(f"✅ Async Command Simulation completed successfully")
    except Exception as e:
        print(f"❌ Async Command Simulation failed: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart AI Notification Examples")
    parser.add_argument("--example", type=int, choices=range(1, 9), 
                       help="Run specific example (1-8)")
    parser.add_argument("--all", action="store_true", 
                       help="Run all examples")
    
    args = parser.parse_args()
    
    if args.all:
        run_all_examples()
    elif args.example:
        examples = [
            example_basic_notifications,
            example_command_lifecycle,
            example_error_handling,
            example_configuration_levels,
            example_provider_specific,
            example_async_simulation,
            example_notification_history,
            example_custom_configuration
        ]
        
        if args.example <= len(examples):
            if args.example == 6:  # Async example
                asyncio.run(examples[args.example - 1]())
            else:
                examples[args.example - 1]()
        else:
            print(f"Example {args.example} not found")
    else:
        print("Smart AI Notification System Examples")
        print("Usage: python notification_examples.py --all")
        print("   or: python notification_examples.py --example <1-8>")
        print("\nAvailable examples:")
        print("  1. Basic Notifications")
        print("  2. Command Lifecycle")
        print("  3. Error Handling")
        print("  4. Configuration Levels")
        print("  5. Provider Specific")
        print("  6. Async Command Simulation")
        print("  7. Notification History")
        print("  8. Custom Configuration")
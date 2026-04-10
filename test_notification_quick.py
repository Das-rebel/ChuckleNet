#!/usr/bin/env python3
"""Quick test of the notification system"""

import time
from smart_ai_notifications import NotificationManager, NotificationType
from smart_ai_integration import init_notifications, notify_info, notify_success

def main():
    print("🧪 Quick Notification System Test")
    print("=" * 50)
    
    # Initialize the system
    integration = init_notifications(level="verbose")
    
    # Test basic notifications
    print("\n1. Testing basic notifications...")
    notify_info("System Test", "Notification system is working correctly")
    notify_success("Test Complete", "All systems operational")
    
    # Test command tracking
    print("\n2. Testing command tracking...")
    manager = integration.notification_manager
    
    command_id = "test_123"
    manager.start_command(command_id, "/test Quick test command", "test_provider")
    
    time.sleep(0.5)
    manager.update_command_progress(command_id, "Processing test data...", 0.3)
    
    time.sleep(0.5)
    manager.update_command_progress(command_id, "Finalizing results...", 0.8)
    
    time.sleep(0.5)
    manager.complete_command(command_id, True, "Test completed successfully", duration=1.5)
    
    # Show status
    print("\n3. System status:")
    status = integration.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Active commands: {status['active_commands']}")
    print(f"   History size: {status['notification_history']}")
    
    # Show recent notifications
    print("\n4. Recent notifications:")
    history = manager.get_notification_history(limit=3)
    for notif in history:
        timestamp = notif.timestamp.strftime("%H:%M:%S")
        print(f"   {timestamp} | {notif.type.value:8} | {notif.title}")
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup
    integration.shutdown()

if __name__ == "__main__":
    main()
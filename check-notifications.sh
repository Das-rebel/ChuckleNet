#!/bin/bash

# Check if terminal-notifier is working
echo "Testing terminal-notifier..."
terminal-notifier -title "Test Notification" -message "This is a test notification from terminal-notifier" -sound default

# Check if AppleScript notifications work
echo "Testing AppleScript notification..."
osascript -e 'display notification "This is a test notification from AppleScript" with title "Test" sound name "default"'

# Check notification settings
echo -e "\nPlease check these settings manually:"
echo "1. Open System Settings > Notifications"
echo "2. Find your terminal app (Terminal, iTerm, etc.)"
echo "3. Make sure 'Allow Notifications' is ON"
echo "4. Set 'Notification Style' to 'Alerts'"
echo "5. Make sure 'Show notifications on lock screen' is enabled"
echo "6. Check that 'Do Not Disturb' is off in Control Center"

# Open notification settings
open "x-apple.systempreferences:com.apple.preference.notifications"

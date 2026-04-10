#!/bin/bash
# Launch Android TV Remote GUI Application (FIXED VERSION)

echo "🎬 Launching Android TV Remote (Enhanced)..."

# Check if GUI is already running
if pgrep -f "tv_remote_gui" > /dev/null; then
    echo "✅ TV Remote GUI is already running"
    echo "📱 Check for the window titled '🎬 Android TV Remote - dasi TV (FIXED)'"
else
    echo "🚀 Starting Enhanced TV Remote GUI..."
    python3 /Users/Subho/tv_remote_gui_fixed.py &
    echo "✅ Enhanced GUI launched! Look for the remote control window."
    echo "💡 This version has improved Bluetooth connection methods!"
fi

echo "💡 Alternative options:"
echo "   python3 /Users/Subho/tv_hid_controller.py  # Test connection"
echo "   python3 /Users/Subho/improved_tv_connector.py  # Diagnose issues"
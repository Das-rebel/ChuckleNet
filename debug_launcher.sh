#!/bin/bash
set -x  # Enable debug output

DIR="/Users/Subho/second-brain-android/resumetailor-app/ResumeTailor.app/Contents/MacOS"
RESOURCES_DIR="$DIR/../Resources"

echo "DEBUG: DIR = $DIR"
echo "DEBUG: RESOURCES_DIR = $RESOURCES_DIR"

# Check if electron binary exists
if [ -f "$DIR/electron" ]; then
    echo "DEBUG: Electron binary found"
    file "$DIR/electron"
else
    echo "ERROR: Electron binary not found at $DIR/electron"
    exit 1
fi

# Check if renderer directory exists
if [ -d "$RESOURCES_DIR/renderer" ]; then
    echo "DEBUG: Renderer directory found"
    ls -la "$RESOURCES_DIR/renderer"
else
    echo "ERROR: Renderer directory not found"
    exit 1
fi

# Try to run electron with debug output
echo "DEBUG: Attempting to run Electron..."
cd "$RESOURCES_DIR"
"$DIR/electron" "renderer" 2>&1 &
ELECTRON_PID=$!

echo "DEBUG: Electron PID = $ELECTRON_PID"

# Wait a bit and check if process is still running
sleep 2
if kill -0 $ELECTRON_PID 2>/dev/null; then
    echo "DEBUG: Electron is running"
    wait $ELECTRON_PID
else
    echo "ERROR: Electron process died immediately"
    exit 1
fi
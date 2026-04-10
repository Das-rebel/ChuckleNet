#!/bin/bash

echo "📱 Building Android TV Controller Mac App..."

# Create app bundle structure
APP_NAME="AndroidTVController"
APP_DIR="$HOME/Desktop/$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "📁 Creating app bundle..."
rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Compile the Swift app
echo "⚙️  Compiling Swift code..."
cd /Users/Subho
swiftc -o "$MACOS_DIR/$APP_NAME" AndroidTVController.swift \
  -framework Cocoa \
  -framework CoreBluetooth \
  -framework IOBluetooth

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
else
    echo "❌ Compilation failed!"
    exit 1
fi

# Create Info.plist
echo "📋 Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.$USER.androidtvcontroller</string>
    <key>CFBundleName</key>
    <string>Android TV Controller</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSBluetoothAlwaysUsageDescription</key>
    <string>This app needs Bluetooth access to connect to and control your Android TV device.</string>
    <key>NSBluetoothPeripheralUsageDescription</key>
    <string>This app uses Bluetooth to send remote control commands to your Android TV.</string>
</dict>
</plist>
EOF

# Make the executable file executable
chmod +x "$MACOS_DIR/$APP_NAME"

# Create app icon (simple placeholder)
echo "🎨 Creating app icon..."
cat > "$RESOURCES_DIR/AppIcon.icns" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIconFamily</key>
    <dict>
        <key>ICN#</key>
        <data>
        <!-- Placeholder icon data -->
        R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
        </data>
    </dict>
</dict>
</plist>
EOF

echo "🚀 App created successfully at: $APP_DIR"
echo ""
echo "📖 Usage Instructions:"
echo "1. Double-click the app on your Desktop to launch it"
echo "2. Grant Bluetooth permissions when prompted"
echo "3. Click 'Connect' to find and connect to your Android TV"
echo "4. Use the remote controls to navigate and enable WiFi"
echo ""
echo "🔧 Controls:"
echo "• Power button: Turn TV on/off"
echo "• Home button: Go to home screen"
echo "• Back button: Navigate back"
echo "• D-Pad: Navigate menus"
echo "• Select button: Confirm selections"
echo "• Volume buttons: Control volume"
echo "• Enable WiFi: Toggle WiFi connection"
echo ""
echo "⚠️  Note: Make sure your Android TV is discoverable via Bluetooth"

# Try to open the app immediately
read -p "Open the app now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "$APP_DIR"
fi
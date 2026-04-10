#!/bin/bash

# Claude GLM (Happy) Configuration and Authentication Fix
echo "🚀 Claude GLM (Happy) Configuration & Authentication Fix"
echo "======================================================="

# Function to handle non-interactive authentication
setup_happy_auth() {
    echo "📱 Setting up Happy GLM authentication..."
    
    # Create Happy config directory if it doesn't exist
    mkdir -p ~/.happy
    
    # Check if already authenticated
    if [ -f ~/.happy/credentials.json ]; then
        echo "✓ Existing credentials found"
        return 0
    fi
    
    echo "⚠️  Authentication required for Happy GLM"
    echo "Please authenticate using one of these methods:"
    echo "  1. Mobile App - Install Happy mobile app and scan QR code"
    echo "  2. Web Browser - Use browser authentication"
    echo ""
    echo "Run manually: happy auth login"
    echo "Then re-run this script to continue setup"
    
    return 1
}

# Function to configure Happy settings
configure_happy_settings() {
    echo "⚙️  Configuring Happy settings..."
    
    # Create optimized settings.json
    cat > ~/.happy/settings.json << 'EOF'
{
  "onboardingCompleted": true,
  "daemonAutoStartWhenRunningHappy": true,
  "theme": "dark",
  "verbose": false,
  "dangerouslySkipPermissions": false,
  "defaultModel": "claude-3-5-sonnet-20241022",
  "fallbackModel": "claude-3-haiku-20240307",
  "mobileEnabled": true,
  "autoStartDaemon": true,
  "logLevel": "info"
}
EOF
    
    echo "✓ Happy settings configured"
}

# Function to setup environment variables
setup_environment() {
    echo "🌍 Setting up environment variables..."
    
    # Add to shell profile if not already present
    SHELL_RC=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        # Add Happy environment variables
        if ! grep -q "HAPPY_HOME_DIR" "$SHELL_RC"; then
            echo "" >> "$SHELL_RC"
            echo "# Happy GLM (Claude GLM) Configuration" >> "$SHELL_RC"
            echo "export HAPPY_HOME_DIR=\"$HOME/.happy\"" >> "$SHELL_RC"
            echo "export PATH=\"$HOME/.npm-global/bin:\$PATH\"" >> "$SHELL_RC"
            echo "✓ Environment variables added to $SHELL_RC"
        else
            echo "✓ Environment variables already configured"
        fi
    fi
}

# Function to test Happy functionality
test_happy_functionality() {
    echo "🧪 Testing Happy GLM functionality..."
    
    # Test basic command
    if happy --help > /dev/null 2>&1; then
        echo "✓ Happy CLI responsive"
    else
        echo "❌ Happy CLI not working properly"
        return 1
    fi
    
    # Test doctor command
    echo "Running Happy doctor..."
    happy doctor
    
    return 0
}

# Function to setup Claude integration
setup_claude_integration() {
    echo "🔗 Setting up Claude integration..."
    
    # Ensure Claude is configured
    if command -v claude > /dev/null 2>&1; then
        echo "✓ Claude CLI found"
        
        # Set up MCP configuration for Happy integration
        if [ ! -f ~/.claude/.mcp.json ]; then
            mkdir -p ~/.claude
            cat > ~/.claude/.mcp.json << 'EOF'
{
  "mcpServers": {
    "happy-integration": {
      "command": "node",
      "args": ["~/.npm-global/lib/node_modules/happy-coder/dist/mcp-server.js"],
      "env": {
        "HAPPY_HOME_DIR": "~/.happy"
      }
    }
  }
}
EOF
            echo "✓ Claude-Happy MCP integration configured"
        else
            echo "✓ Claude MCP config already exists"
        fi
    else
        echo "⚠️  Claude CLI not found - install it for full integration"
    fi
}

# Function to create helper scripts
create_helper_scripts() {
    echo "📝 Creating helper scripts..."
    
    # Create Happy launcher script
    cat > ~/.happy/launch_happy.sh << 'EOF'
#!/bin/bash
# Happy GLM Launcher with proper environment

export HAPPY_HOME_DIR="$HOME/.happy"
export NODE_ENV="production"

# Start Happy with proper terminal handling
exec ~/.npm-global/bin/happy "$@"
EOF
    
    chmod +x ~/.happy/launch_happy.sh
    
    # Create alias setup
    cat > ~/.happy/aliases.sh << 'EOF'
# Happy GLM Aliases
alias happy-mobile="happy --yolo"
alias happy-debug="DEBUG=* happy"
alias happy-reset="happy auth login --force"
alias happy-status="happy doctor"
EOF
    
    echo "✓ Helper scripts created"
    echo "  - ~/.happy/launch_happy.sh - Proper launcher"
    echo "  - ~/.happy/aliases.sh - Useful aliases"
}

# Main execution
main() {
    echo "Starting Happy GLM deployment..."
    echo ""
    
    # Step 1: Configure settings
    configure_happy_settings
    
    # Step 2: Setup environment
    setup_environment
    
    # Step 3: Create helper scripts
    create_helper_scripts
    
    # Step 4: Setup Claude integration
    setup_claude_integration
    
    # Step 5: Test functionality
    test_happy_functionality
    
    # Step 6: Handle authentication
    echo ""
    echo "🔐 Authentication Status Check..."
    if [ -f ~/.happy/credentials.json ]; then
        echo "✅ Happy GLM is authenticated and ready!"
        echo ""
        echo "🎉 Deployment Complete!"
        echo "You can now use Happy GLM with:"
        echo "  happy              # Start interactive session"
        echo "  happy --yolo       # Skip permissions"
        echo "  happy doctor       # Check status"
        echo "  happy auth login   # Re-authenticate if needed"
    else
        echo "⚠️  Authentication Required!"
        echo ""
        echo "To complete setup, run:"
        echo "  happy auth login"
        echo ""
        echo "Choose option 2 (Web Browser) for easiest setup"
        echo "Then Happy GLM will be fully functional"
    fi
    
    echo ""
    echo "📚 Next Steps:"
    echo "1. Restart your terminal or run: source ~/.zshrc"
    echo "2. Authenticate with: happy auth login"  
    echo "3. Test with: happy doctor"
    echo "4. Start using: happy"
}

# Run main function
main
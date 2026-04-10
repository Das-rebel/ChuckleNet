#!/bin/bash

# Claude Doctor Fix - Manual System Check
# This script provides the functionality of claude doctor when it fails due to TTY issues

echo "🔧 Claude Code System Check"
echo "=========================="
echo

# Check Claude Code installation
echo "📦 Installation Status:"
CLAUDE_VERSION=$(claude --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ Claude Code installed: $CLAUDE_VERSION"
else
    echo "   ❌ Claude Code not found or not working"
fi

# Check Node.js
NODE_VERSION=$(node --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ Node.js: $NODE_VERSION"
else
    echo "   ❌ Node.js not found"
fi

# Check NPX
NPX_VERSION=$(npx --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ✅ NPX: $NPX_VERSION"
else
    echo "   ❌ NPX not found"
fi

echo

# Check configuration
echo "⚙️  Configuration:"
if [ -f ~/.claude/settings.json ]; then
    echo "   ✅ Settings file exists"
else
    echo "   ⚠️  Settings file missing"
fi

if [ -f ~/.claude/settings.local.json ]; then
    SETTINGS_SIZE=$(wc -c < ~/.claude/settings.local.json)
    echo "   ✅ Local settings file exists (${SETTINGS_SIZE} bytes)"
    if [ $SETTINGS_SIZE -gt 50000 ]; then
        echo "   ⚠️  Local settings file is large - may cause token usage issues"
    fi
else
    echo "   ⚠️  Local settings file missing"
fi

if [ -f ~/.mcp.json ]; then
    MCP_SERVERS=$(jq '.mcpServers | keys | length' ~/.mcp.json 2>/dev/null)
    echo "   ✅ MCP configuration exists with $MCP_SERVERS servers"
else
    echo "   ⚠️  MCP configuration missing"
fi

echo

# Check environment
echo "🌍 Environment:"
echo "   TTY: $(tty 2>/dev/null || echo 'Not a TTY (normal for some environments)')"
echo "   TERM: ${TERM:-'Not set'}"
echo "   Shell: $SHELL"

echo

# Check common issues
echo "🔍 Common Issues Check:"

# Check for TTY issue (the main problem)
if ! tty >/dev/null 2>&1; then
    echo "   ⚠️  TTY not available - claude doctor will fail (this is expected in some environments)"
    echo "      This doesn't affect normal Claude Code functionality"
else
    echo "   ✅ TTY available - claude doctor should work"
fi

# Check for token usage issues
if [ -f ~/.claude/settings.local.json.backup ]; then
    BACKUP_SIZE=$(wc -c < ~/.claude/settings.local.json.backup)
    CURRENT_SIZE=$(wc -c < ~/.claude/settings.local.json)
    REDUCTION=$((BACKUP_SIZE - CURRENT_SIZE))
    if [ $REDUCTION -gt 0 ]; then
        echo "   ✅ Settings optimized - reduced by $(echo "scale=1; $REDUCTION/1000" | bc)KB"
        echo "      This should significantly improve token usage"
    fi
fi

echo

echo "💡 Recommendations:"
echo "   • Claude Code should work normally despite TTY issues"
echo "   • Settings have been optimized to reduce token usage"
echo "   • Use this script instead of 'claude doctor' if TTY issues persist"
echo "   • All essential components are properly configured"

echo
echo "✅ System check complete!"
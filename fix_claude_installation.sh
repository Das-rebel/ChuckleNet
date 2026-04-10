#!/bin/bash

# Fix Multiple Claude Code Installation Issue
# This script cleans up duplicate installations and PATH entries

set -e

echo "🔧 Claude Code Installation Fix Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check current state
echo "📊 Current Installation Analysis:"
echo "----------------------------------------"
echo "Active version:"
claude --version 2>/dev/null || echo "  Error: claude command not working"
echo ""

echo "All Claude installations:"
which -a claude || echo "  None found"
echo ""

echo "All npm-global Claude versions:"
if [ -d ~/.npm-global/lib/node_modules/@anthropic-ai/claude-code ]; then
    echo "  ~/.npm-global/lib/node_modules/@anthropic-ai/claude-code/"
    cat ~/.npm-global/lib/node_modules/@anthropic-ai/claude-code/package.json 2>/dev/null | grep '"version"' || echo "    version: unknown"
else
    echo "  None in ~/.npm-global"
fi
echo ""

if [ -d /usr/local/lib/node_modules/@anthropic-ai/claude-code ]; then
    echo "  /usr/local/lib/node_modules/@anthropic-ai/claude-code/"
    cat /usr/local/lib/node_modules/@anthropic-ai/claude-code/package.json 2>/dev/null | grep '"version"' || echo "    version: unknown"
fi
echo ""

echo "========================================"
echo ""

# Ask for confirmation before making changes
echo "🔄 Proposed Fixes:"
echo "----------------------------------------"
echo "1. Remove duplicate symlink: ~/.local/bin/claude"
echo "2. Clean up duplicate PATH entries in ~/.zshrc"
echo "3. Verify ~/.npm-global/bin/claude is the primary installation"
echo ""

read -p "Do you want to proceed with these fixes? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Aborted by user${NC}"
    exit 0
fi

echo ""
echo "========================================"
echo "🛠️  Applying Fixes..."
echo "========================================"
echo ""

# Step 1: Remove duplicate symlink
echo "Step 1: Removing duplicate symlink..."
if [ -L ~/.local/bin/claude ]; then
    echo "  Removing: ~/.local/bin/claude"
    rm ~/.local/bin/claude
    echo -e "${GREEN}✓ Done${NC}"
elif [ -f ~/.local/bin/claude ]; then
    echo "  Warning: ~/.local/bin/claude exists but is not a symlink"
    echo "  Skipping removal for safety"
else
    echo "  ~/.local/bin/claude does not exist (already clean)"
fi
echo ""

# Step 2: Clean up PATH duplicates in .zshrc
echo "Step 2: Cleaning up PATH in ~/.zshrc..."
echo "  Creating backup: ~/.zshrc.backup_claude_fix"
cp ~/.zshrc ~/.zshrc.backup_claude_fix

# Remove duplicate PATH entries while keeping the first occurrence
echo "  Removing duplicate PATH entries..."

# Create a temporary file to process
tmp_file=$(mktemp)
awk '
{
    if (/^export PATH/) {
        seen = 0
        # Extract paths from this line
        n = split($0, paths, ":")
        unique_paths = ""
        for (i = 2; i <= n; i++) {
            # Check if this path is already in the line
            if (index($0, paths[i]":") == 0 && index($0, paths[i]"$") == 0) {
                if (unique_paths == "") {
                    unique_paths = paths[i]
                } else {
                    unique_paths = unique_paths ":" paths[i]
                }
            }
        }
        # Reconstruct line with unique paths only
        if (unique_paths != "") {
            print "export PATH=\"" unique_paths ":$PATH\""
        } else {
            print
        }
    } else {
        print
    }
}
' ~/.zshrc > "$tmp_file"

# Simpler approach: just remove obvious duplicates
# Use grep to remove consecutive duplicate PATH exports
python3 << 'PYTHON_EOF'
import re

with open('$HOME/.zshrc', 'r') as f:
    content = f.read()

# Remove specific duplicate PATH lines
# Remove duplicate "export PATH=$HOME/.npm-global/bin:$PATH"
lines = content.split('\n')
seen_exports = set()
filtered_lines = []

for line in lines:
    # Check for PATH export lines
    if 'export PATH' in line and '.npm-global' in line:
        # Simple dedup - only keep first occurrence of each pattern
        pattern = re.sub(r'\$PATH.*', '', line).strip()
        if pattern not in seen_exports:
            seen_exports.add(pattern)
            filtered_lines.append(line)
        else:
            # This is a duplicate, skip it
            filtered_lines.append('# REMOVED DUPLICATE: ' + line)
    elif 'export PATH=$HOME:.local/bin:$PATH' in line:
        # Remove redundant .local/bin exports
        filtered_lines.append('# REMOVED DUPLICATE: ' + line)
    else:
        filtered_lines.append(line)

# Write back
with open('$HOME/.zshrc', 'w') as f:
    f.write('\n'.join(filtered_lines))

print("PATH duplicates removed")
PYTHON_EOF

echo -e "${GREEN}✓ PATH cleaned up${NC}"
echo ""

# Step 3: Verify primary installation
echo "Step 3: Verifying primary installation..."
if [ -L ~/.npm-global/bin/claude ]; then
    echo "  ✓ ~/.npm-global/bin/claude exists (symlink)"
    echo "    → $(readlink ~/.npm-global/bin/claude)"
else
    echo -e "${RED}✗ ~/.npm-global/bin/claude not found${NC}"
fi
echo ""

# Show warning about system-wide installation
if [ -f /usr/local/bin/claude ]; then
    echo -e "${YELLOW}⚠️  System-wide installation detected:${NC}"
    echo "  /usr/local/bin/claude → $(readlink /usr/local/bin/claude)"
    echo ""
    echo "  This is an OLD version (v1.0.48) that may conflict with your"
    echo "  newer v2.1.63 installation. To remove it (requires sudo):"
    echo "    sudo rm /usr/local/bin/claude"
    echo "    sudo rm -rf /usr/local/lib/node_modules/@anthropic-ai/claude-code"
    echo ""
    read -p "Do you want to remove the system-wide installation now? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Removing system-wide installation..."
        sudo rm /usr/local/bin/claude
        sudo rm -rf /usr/local/lib/node_modules/@anthropic-ai/claude-code
        echo -e "${GREEN}✓ System-wide installation removed${NC}"
    else
        echo "  Skipped (you can remove it later with the commands above)"
    fi
fi
echo ""

echo "========================================"
echo -e "${GREEN}✅ Fix Complete!${NC}"
echo "========================================"
echo ""
echo "📝 Next Steps:"
echo "----------------------------------------"
echo "1. Reload your shell:"
echo "   source ~/.zshrc"
echo ""
echo "2. Verify the fix:"
echo "   which claude      # Should show: ~/.npm-global/bin/claude"
echo "   claude --version  # Should show: 2.1.63 (Claude Code)"
echo ""
echo "3. If issues persist, restart your terminal"
echo ""

#!/bin/bash
# Quick development script - assumes everything is already built
# Just opens the extension and launches dev window

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
VSCODE_DIR="$PROJECT_DIR/stencila/vscode"

# Determine IDE command
if command -v cursor &> /dev/null; then
    IDE_CMD="cursor"
elif command -v code &> /dev/null; then
    IDE_CMD="code"
else
    echo "❌ Neither Cursor nor VS Code found in PATH"
    exit 1
fi

echo "🚀 Opening Stencila extension in $IDE_CMD..."
echo "   Press F5 to launch the development window"
echo ""

# Open the extension workspace
$IDE_CMD "$VSCODE_DIR"


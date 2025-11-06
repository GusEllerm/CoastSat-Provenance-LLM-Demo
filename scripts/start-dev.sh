#!/bin/bash
# One-command startup: Build everything and open development window

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
STENCILA_DIR="$PROJECT_DIR/stencila"
VSCODE_DIR="$STENCILA_DIR/vscode"

echo "🚀 Starting Stencila development environment..."
echo ""

# Run the setup script
"$SCRIPT_DIR/dev.sh"

# Determine IDE command
if command -v cursor &> /dev/null; then
    IDE_CMD="cursor"
elif command -v code &> /dev/null; then
    IDE_CMD="code"
else
    echo "❌ Neither Cursor nor VS Code found in PATH"
    exit 1
fi

echo ""
echo "🎯 Opening extension workspace in $IDE_CMD..."
echo "   After it opens, press F5 to launch the development window"
echo ""

# Open the extension workspace
$IDE_CMD "$VSCODE_DIR"

echo ""
echo "✅ Setup complete! Next steps:"
echo "  1. Wait for Cursor/VS Code to open"
echo "  2. Press F5 to launch development window"
echo "  3. In development window, open: $PROJECT_DIR/test-files"
echo ""


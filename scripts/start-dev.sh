#!/bin/bash
# One-command startup: Build everything and open development window

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
STENCILA_DIR="$PROJECT_DIR/stencila"
VSCODE_DIR="$STENCILA_DIR/vscode"

echo "🚀 Starting Stencila development environment..."
echo ""

# Run the setup script (it handles errors internally)
"$SCRIPT_DIR/dev.sh"
EXIT_CODE=$?

# If CLI build failed, exit
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Setup failed. Please fix the errors above."
    exit $EXIT_CODE
fi

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
if [ -f /tmp/stencila-compile.log ] && grep -q "Error\|failed" /tmp/stencila-compile.log 2>/dev/null; then
    echo "ℹ️  Note: Extension build had issues (see docs/troubleshooting/README.md)"
    echo "   This won't affect CLI development or extension functionality!"
    echo ""
fi


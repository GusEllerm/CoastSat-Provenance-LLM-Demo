#!/bin/bash
# Development environment startup script
# This script sets up everything needed to start developing Stencila

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
STENCILA_DIR="$PROJECT_DIR/stencila"
VSCODE_DIR="$STENCILA_DIR/vscode"

echo "🚀 Setting up Stencila development environment..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js."
    exit 1
fi

if ! command -v cursor &> /dev/null && ! command -v code &> /dev/null; then
    echo "⚠️  Cursor/VS Code not found in PATH. You may need to launch it manually."
    IDE_CMD=""
elif command -v cursor &> /dev/null; then
    IDE_CMD="cursor"
else
    IDE_CMD="code"
fi

echo "✅ Prerequisites check passed"
echo ""

# Build CLI
echo "🔨 Building Stencila CLI..."
cd "$STENCILA_DIR"
cargo build --bin stencila
echo "✅ CLI built"
echo ""

# Install and build extension
echo "📦 Setting up VS Code extension..."
cd "$VSCODE_DIR"

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install
else
    echo "  Dependencies already installed"
fi

# Install and build workspace dependencies
echo "  Installing workspace dependencies..."

# Install root workspace dependencies (this installs all workspace packages)
cd "$STENCILA_DIR"
if [ ! -d "node_modules" ]; then
    echo "  Installing root workspace dependencies..."
    npm install
else
    echo "  Root workspace dependencies already installed"
fi

# Build TypeScript types (required by web)
TS_DIR="$STENCILA_DIR/ts"
if [ ! -d "$TS_DIR/dist" ]; then
    echo "  Building TypeScript types..."
    cd "$TS_DIR"
    npm run build
fi

# Now compile extension
cd "$VSCODE_DIR"
echo "  Compiling extension..."
npm run compile
echo "✅ Extension compiled"
echo ""

# Check if launch.json exists
if [ ! -f "$VSCODE_DIR/.vscode/launch.json" ]; then
    echo "📝 Creating launch configuration..."
    mkdir -p "$VSCODE_DIR/.vscode"
    cat > "$VSCODE_DIR/.vscode/launch.json" << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension (Development)",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}"
      ],
      "outFiles": [
        "${workspaceFolder}/out/**/*.js"
      ],
      "preLaunchTask": {
        "type": "npm",
        "script": "compile"
      }
    }
  ]
}
EOF
    echo "✅ Launch configuration created"
    echo ""
fi

echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Open the extension in your IDE:"
if [ -n "$IDE_CMD" ]; then
    echo "     $IDE_CMD \"$VSCODE_DIR\""
else
    echo "     Open: $VSCODE_DIR"
fi
echo ""
echo "  2. Press F5 (or Cmd+F5) to launch the development window"
echo ""
echo "  3. In the development window, open your test files:"
echo "     $PROJECT_DIR/test-files"
echo ""
echo "  4. Your changes to the CLI will be automatically used!"
echo "     (Just rebuild: cargo build --bin stencila, then restart LSP server)"
echo ""

# Ask if user wants to open the extension workspace
if [ -n "$IDE_CMD" ]; then
    read -p "Open extension workspace in $IDE_CMD now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Opening $VSCODE_DIR..."
        $IDE_CMD "$VSCODE_DIR"
    fi
fi


#!/bin/bash
# Watch mode script - automatically rebuilds CLI and extension on changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
STENCILA_DIR="$PROJECT_DIR/stencila"
VSCODE_DIR="$STENCILA_DIR/vscode"

echo "👀 Starting watch mode..."
echo "This will automatically rebuild:"
echo "  - CLI when Rust files change"
echo "  - Extension when TypeScript files change"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Check if cargo-watch is installed
if ! command -v cargo-watch &> /dev/null; then
    echo "⚠️  cargo-watch not found. Installing..."
    cargo install cargo-watch
fi

# Function to rebuild CLI
rebuild_cli() {
    echo ""
    echo "🔨 Rebuilding CLI..."
    cd "$STENCILA_DIR"
    cargo build --bin stencila
    echo "✅ CLI rebuilt"
    echo "💡 Tip: Restart the LSP server in the development window to use the new build"
}

# Function to rebuild extension
rebuild_extension() {
    echo ""
    echo "📦 Rebuilding extension..."
    cd "$VSCODE_DIR"
    npm run compile
    echo "✅ Extension rebuilt"
    echo "💡 Tip: Reload the development window to use the new build"
}

# Watch CLI
(
    cd "$STENCILA_DIR/rust"
    cargo watch -x 'build --bin stencila' --postpone
) &
CLI_PID=$!

# Watch extension TypeScript
(
    cd "$VSCODE_DIR"
    npm run watch 2>/dev/null || npx tsc -watch -p . 2>/dev/null || echo "Extension watch mode not available, rebuild manually"
) &
EXT_PID=$!

# Trap Ctrl+C to kill background processes
trap "kill $CLI_PID $EXT_PID 2>/dev/null; exit" INT TERM

echo "✅ Watch mode started (PIDs: $CLI_PID, $EXT_PID)"
echo ""

# Wait for processes
wait

#!/bin/bash
# Initial setup script for Stencila development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🚀 Setting up Stencila development environment..."
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v rustc &> /dev/null; then
    echo "❌ Rust not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 from https://www.python.org/"
    exit 1
fi

if ! command -v make &> /dev/null; then
    echo "❌ Make not found. Please install make (usually comes with development tools)"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Setup Rust tools
echo "🔧 Setting up Rust development tools..."
cd "$STENCILA_DIR"
make -C rust setup

echo ""
echo "📦 Installing all project dependencies..."
make install

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/build.sh' to build the project"
echo "  2. Run './scripts/test.sh' to run all tests"
echo "  3. Start editing code in stencila/"



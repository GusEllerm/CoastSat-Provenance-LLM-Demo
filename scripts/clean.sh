#!/bin/bash
# Clean build artifacts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🧹 Cleaning build artifacts..."
cd "$STENCILA_DIR"
make clean

echo "✅ Clean complete!"



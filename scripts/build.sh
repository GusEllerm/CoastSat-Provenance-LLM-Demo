#!/bin/bash
# Build script for Stencila development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🔨 Building Stencila..."
cd "$STENCILA_DIR"
make build

echo "✅ Build complete!"



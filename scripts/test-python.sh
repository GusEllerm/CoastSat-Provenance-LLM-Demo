#!/bin/bash
# Run Python tests only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🐍 Running Python tests..."
cd "$STENCILA_DIR"
make -C python/stencila test

echo "✅ Python tests passed!"



#!/bin/bash
# Run Node.js tests only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "📦 Running Node.js tests..."
cd "$STENCILA_DIR"
make -C node test

echo "✅ Node.js tests passed!"



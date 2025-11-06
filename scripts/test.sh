#!/bin/bash
# Test script for Stencila development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🧪 Running Stencila tests..."
cd "$STENCILA_DIR"
make test

echo "✅ All tests passed!"



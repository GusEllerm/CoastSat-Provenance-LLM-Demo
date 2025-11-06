#!/bin/bash
# Run Rust tests only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

echo "🦀 Running Rust tests..."
cd "$STENCILA_DIR"
make -C rust test

echo "✅ Rust tests passed!"



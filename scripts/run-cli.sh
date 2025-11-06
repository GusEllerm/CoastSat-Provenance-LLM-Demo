#!/bin/bash
# Run the Stencila CLI with cargo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STENCILA_DIR="$SCRIPT_DIR/../stencila"

cd "$STENCILA_DIR"

# Run with cargo, passing all arguments
cargo run --bin stencila -- "$@"



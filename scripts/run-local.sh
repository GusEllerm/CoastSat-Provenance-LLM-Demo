#!/bin/bash
# Run the locally built Stencila CLI
# This is an alias for the run-cli.sh script but with a clearer name

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/run-cli.sh" "$@"



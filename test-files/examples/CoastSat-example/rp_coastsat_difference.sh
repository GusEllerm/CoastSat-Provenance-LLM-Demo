#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

STENCILA_DEV="/Users/eller/Projects/stencila_dev/stencila/target/debug/stencila"
CLI="$STENCILA_DEV"
if [ ! -x "$CLI" ]; then
  CLI="$(command -v stencila || true)"
fi
if [ -z "$CLI" ]; then
  echo "Unable to locate stencila CLI (expected $STENCILA_DEV or stencila on PATH)" >&2
  exit 1
fi

PROMPTS_DIR="/Users/eller/Projects/stencila_dev/stencila/prompts"
export STENCILA_PROMPTS_DIR="$PROMPTS_DIR"

"$CLI" render coastsat_difference_llm.smd coastsat_difference.html --debug

if command -v open >/dev/null 2>&1; then
  open test.html
else
  echo "Rendered HTML at $SCRIPT_DIR/test.html"
fi

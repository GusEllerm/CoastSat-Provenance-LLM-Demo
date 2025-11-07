#!/bin/zsh

# Compile simple-article.smd using stencila pipeline
# 1. Convert template to DNF.json
# 2. Render DNF.json to DNF_eval.json
# 3. Convert DNF_eval.json to render.html

set -e  # Exit on error

# Use local stencila build
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../" && pwd)"
STENCILA_BIN="${PROJECT_ROOT}/stencila/target/debug/stencila"

# Create outputs directory if it doesn't exist
mkdir -p outputs

# Unset conflicting color environment variables
unset NO_COLOR FORCE_COLOR

# Step 1: Convert template to DNF.json
"${STENCILA_BIN}" convert examples/simple-article.smd outputs/DNF.json --debug

# Step 2: Render DNF.json to DNF_eval.json
"${STENCILA_BIN}" render outputs/DNF.json outputs/DNF_eval.json --debug

# Step 3: Convert DNF_eval.json to render.html
"${STENCILA_BIN}" convert outputs/DNF_eval.json outputs/render.html --debug

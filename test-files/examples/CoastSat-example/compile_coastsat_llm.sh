#!/bin/zsh

# Compile coastsat_llm.smd using stencila pipeline
# 1. Convert template to DNF.json
# 2. Render DNF.json to DNF_eval.json
# 3. Convert DNF_eval.json to render.html

set -e  # Exit on error

# Use local stencila build
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../" && pwd)"
STENCILA_BIN="${PROJECT_ROOT}/stencila/target/debug/stencila"

# Create outputs directory if it doesn't exist
OUTPUTS_DIR="${SCRIPT_DIR}/outputs"
mkdir -p "${OUTPUTS_DIR}"

# Unset conflicting color environment variables
unset NO_COLOR FORCE_COLOR

# Step 1: Convert template to DNF.json
"${STENCILA_BIN}" convert "${SCRIPT_DIR}/coastsat_llm.smd" "${OUTPUTS_DIR}/DNF.json" --debug

# Step 2: Render DNF.json to DNF_eval.json
"${STENCILA_BIN}" render "${OUTPUTS_DIR}/DNF.json" "${OUTPUTS_DIR}/DNF_eval.json" --debug

# Step 3: Convert DNF_eval.json to render.html
"${STENCILA_BIN}" convert "${OUTPUTS_DIR}/DNF_eval.json" "${OUTPUTS_DIR}/render.html" --debug



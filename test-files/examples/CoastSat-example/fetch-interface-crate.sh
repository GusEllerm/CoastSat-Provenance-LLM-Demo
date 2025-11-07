#!/bin/bash

# Script to fetch the latest interface.crate from CoastSat-interface.crate repository
# This script will replace any existing interface.crate file or directory
#
# Usage:
#   ./fetch-interface-crate.sh
#
# The script attempts to fetch interface.crate in the following order:
#   1. Download from latest GitHub release assets (if available)
#   2. Extract from latest GitHub release source code archive
#   3. Clone repository and copy from main branch
#
# Requirements:
#   - curl (for downloading)
#   - git (for cloning repository, fallback method)
#   - tar (for extracting archives)
#   - python3 or jq (optional, for better JSON parsing)

# Exit on error for critical commands
set -eo pipefail

REPO_OWNER="GusEllerm"
REPO_NAME="CoastSat-interface.crate"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
API_BASE="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}"
TEMP_DIR="${SCRIPT_DIR}/.temp_fetch"
INTERFACE_CRATE_FILE="${TARGET_DIR}/interface.crate"

echo "Fetching latest interface.crate from ${REPO_OWNER}/${REPO_NAME}..."

# Clean up temp directory if it exists
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# Function to cleanup on exit
cleanup() {
    rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

# Try to get the latest release
echo "Checking for latest release..."
HTTP_CODE=$(curl -s -o "${TEMP_DIR}/release.json" -w "%{http_code}" "${API_BASE}/releases/latest" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ] && [ -f "${TEMP_DIR}/release.json" ]; then
    # Try to use Python/jq for JSON parsing if available, otherwise use grep
    if command -v python3 &> /dev/null; then
        TAG_NAME=$(python3 -c "import json, sys; data = json.load(open('${TEMP_DIR}/release.json')); print(data.get('tag_name', ''))" 2>/dev/null || echo "")
        # Check for assets with interface.crate in the name
        ASSET_URL=$(python3 -c "
import json, sys
data = json.load(open('${TEMP_DIR}/release.json'))
assets = data.get('assets', [])
for asset in assets:
    name = asset.get('name', '')
    if 'interface.crate' in name:
        print(asset.get('browser_download_url', ''))
        break
" 2>/dev/null || echo "")
    elif command -v jq &> /dev/null; then
        TAG_NAME=$(jq -r '.tag_name // ""' "${TEMP_DIR}/release.json" 2>/dev/null || echo "")
        ASSET_URL=$(jq -r '.assets[] | select(.name | contains("interface.crate")) | .browser_download_url' "${TEMP_DIR}/release.json" 2>/dev/null | head -1 || echo "")
    else
        # Fallback to grep (allow failure)
        TAG_NAME=$(grep -o '"tag_name":"[^"]*' "${TEMP_DIR}/release.json" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
        ASSET_URL=$(grep -o '"browser_download_url":"[^"]*interface\.crate[^"]*' "${TEMP_DIR}/release.json" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
    fi
    
    if [ -n "$TAG_NAME" ] && [ "$TAG_NAME" != "null" ]; then
        echo "Found latest release: ${TAG_NAME}"
        
        # Check if interface.crate is available as a release asset
        if [ -n "$ASSET_URL" ] && [ "$ASSET_URL" != "null" ]; then
            echo "Downloading interface.crate from release assets..."
            # Remove existing interface.crate (file or directory)
            rm -rf "${INTERFACE_CRATE_FILE}"
            if curl -L -f -s "${ASSET_URL}" -o "${INTERFACE_CRATE_FILE}" 2>/dev/null; then
                if [ -f "${INTERFACE_CRATE_FILE}" ]; then
                    echo "Successfully downloaded interface.crate from release ${TAG_NAME}"
                    exit 0
                fi
            fi
        fi
        
        # If not an asset, try to download the source code from the release tag
        echo "Downloading source code from release ${TAG_NAME}..."
        ARCHIVE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/tags/${TAG_NAME}.tar.gz"
        
        if curl -L -s -f "${ARCHIVE_URL}" -o "${TEMP_DIR}/release.tar.gz" 2>/dev/null; then
            cd "${TEMP_DIR}"
            tar -xzf release.tar.gz 2>/dev/null || true
            
            # Find the extracted directory (usually repo-tag_name format)
            EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "${REPO_NAME}-*" | head -1)
            if [ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR" ]; then
                cd "$EXTRACTED_DIR"
                
                # Look for interface.crate in the extracted files
                if [ -f "interface.crate" ]; then
                    rm -rf "${INTERFACE_CRATE_FILE}"
                    cp "interface.crate" "${INTERFACE_CRATE_FILE}"
                    echo "Successfully extracted interface.crate from release ${TAG_NAME}"
                    exit 0
                elif [ -d "interface.crate" ]; then
                    rm -rf "${INTERFACE_CRATE_FILE}"
                    cp -r "interface.crate" "${INTERFACE_CRATE_FILE}"
                    echo "Successfully extracted interface.crate directory from release ${TAG_NAME}"
                    exit 0
                fi
            fi
        fi
    fi
fi

# Fallback: Clone the repository shallowly and get interface.crate from main/master
echo "Cloning repository to fetch interface.crate from main branch..."
cd "${TEMP_DIR}"
if ! git clone --depth 1 "${REPO_URL}" repo 2>/dev/null; then
    echo "Error: Failed to clone repository"
    exit 1
fi

cd repo

# Remove existing interface.crate before copying
rm -rf "${INTERFACE_CRATE_FILE}"

# Look for interface.crate in the repository
if [ -f "interface.crate" ]; then
    cp "interface.crate" "${INTERFACE_CRATE_FILE}"
    echo "Successfully fetched interface.crate from main branch"
    exit 0
fi

# Also check if it's in a subdirectory (like the LP_Crate output)
if [ -d "interface.crate" ]; then
    # It's an RO-Crate directory, copy it
    echo "Found interface.crate directory, copying..."
    cp -r "interface.crate" "${INTERFACE_CRATE_FILE}"
    echo "Successfully copied interface.crate directory from repository"
    exit 0
fi

# Check LP_Crate directory or other common locations
for dir in "LP_Crate" "."; do
    if [ -f "${dir}/interface.crate" ]; then
        cp "${dir}/interface.crate" "${INTERFACE_CRATE_FILE}"
        echo "Successfully found interface.crate in ${dir}/"
        exit 0
    elif [ -d "${dir}/interface.crate" ]; then
        cp -r "${dir}/interface.crate" "${INTERFACE_CRATE_FILE}"
        echo "Successfully copied interface.crate directory from ${dir}/"
        exit 0
    fi
done

echo "Error: Could not find interface.crate in the repository"
echo "Please check the repository structure manually"
exit 1


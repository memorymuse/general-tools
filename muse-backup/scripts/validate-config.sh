#!/bin/bash
# validate-config.sh
# Validates all JSON config files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$BASE_DIR/configs"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

validate_json_array() {
    local file=$1

    # Check file exists
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Config file not found: $file${NC}"
        return 1
    fi

    # Check valid JSON
    if ! jq empty < "$file" 2>/dev/null; then
        echo -e "${RED}✗ Invalid JSON syntax: $file${NC}"
        return 1
    fi

    # Check is array
    if ! jq -e 'type == "array"' < "$file" >/dev/null; then
        echo -e "${RED}✗ Config must be JSON array: $file${NC}"
        return 1
    fi

    # Check all strings
    if ! jq -e 'all(type == "string")' < "$file" >/dev/null; then
        echo -e "${RED}✗ Array must contain only strings: $file${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ Valid JSON array: $file${NC}"
    return 0
}

validate_daily_config() {
    local file=$1
    validate_json_array "$file" || return 1

    # Check all paths are absolute
    if ! jq -e 'all(startswith("/"))' < "$file" >/dev/null; then
        echo -e "${RED}✗ Daily config must contain absolute paths: $file${NC}"
        return 1
    fi

    # Count items
    local count=$(jq 'length' < "$file")
    echo -e "${GREEN}✓ Daily config valid: $file ($count items)${NC}"
    return 0
}

validate_monthly_config() {
    local file=$1
    validate_json_array "$file" || return 1

    # Count items
    local count=$(jq 'length' < "$file")
    echo -e "${GREEN}✓ Monthly config valid: $file ($count patterns)${NC}"
    return 0
}

echo "========== Config Validation =========="
echo ""

# Check jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo -e "${RED}ERROR: jq is not installed${NC}"
    echo "Install with: sudo apt install jq"
    exit 1
fi

# Validate all configs
all_valid=true

echo "Validating daily configs..."
validate_daily_config "$CONFIG_DIR/muse-v0-daily.json" || all_valid=false
validate_daily_config "$CONFIG_DIR/muse-v1-daily.json" || all_valid=false
echo ""

echo "Validating monthly configs..."
validate_monthly_config "$CONFIG_DIR/muse-v0-monthly.json" || all_valid=false
validate_monthly_config "$CONFIG_DIR/muse-v1-monthly.json" || all_valid=false
echo ""

if [ "$all_valid" = true ]; then
    echo -e "${GREEN}========== All Configs Valid ==========${NC}"
    exit 0
else
    echo -e "${RED}========== Some Configs Invalid ==========${NC}"
    exit 1
fi

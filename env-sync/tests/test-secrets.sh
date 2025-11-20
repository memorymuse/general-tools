#!/usr/bin/env bash
#
# cc-isolate Secret Scanning Test Suite
# Tests secret detection, template generation, and whitelisting
#

set -euo pipefail

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_SYNC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load libraries
source "$ENV_SYNC_ROOT/lib/platform.sh"
source "$ENV_SYNC_ROOT/lib/secrets.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test fixture directory
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
TEST_PREFIX=".cc-test-"

#------------------------------------------------------------------------------
# Test Framework
#------------------------------------------------------------------------------

test_start() {
    local name="$1"
    echo -e "${BLUE}▶ Testing:${RESET} $name"
    ((TESTS_RUN++))
}

test_pass() {
    echo -e "  ${GREEN}✓ PASS${RESET}"
    ((TESTS_PASSED++))
    echo
}

test_fail() {
    local message="$1"
    echo -e "  ${RED}✗ FAIL${RESET}: $message"
    ((TESTS_FAILED++))
    echo
}

cleanup_test_files() {
    # Remove all test artifacts
    find "$FIXTURES_DIR" -name "${TEST_PREFIX}*" -delete 2>/dev/null || true
    rm -f "$ENV_SYNC_ROOT/.cc-secrets-whitelist" 2>/dev/null || true
}

#------------------------------------------------------------------------------
# Test Cases
#------------------------------------------------------------------------------

test_aws_key_detection() {
    test_start "AWS Access Key Detection"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}aws.txt"
    cat > "$test_file" << 'EOF'
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EOF

    if ! scan_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to detect AWS keys"
    fi

    rm -f "$test_file"
}

test_github_token_detection() {
    test_start "GitHub Token Detection"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}github.txt"
    cat > "$test_file" << 'EOF'
# GitHub Configuration
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
EOF

    if ! scan_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to detect GitHub token"
    fi

    rm -f "$test_file"
}

test_private_key_detection() {
    test_start "Private Key Detection"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}privatekey.pem"
    cat > "$test_file" << 'EOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijk
-----END RSA PRIVATE KEY-----
EOF

    if ! scan_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to detect private key"
    fi

    rm -f "$test_file"
}

test_database_url_detection() {
    test_start "Database URL Detection"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}database.env"
    cat > "$test_file" << 'EOF'
DATABASE_URL=postgres://user:SuperSecret123@localhost:5432/mydb
MONGO_URL=mongodb://admin:password123@mongo.example.com/db
EOF

    if ! scan_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to detect database URLs"
    fi

    rm -f "$test_file"
}

test_safe_file_detection() {
    test_start "Safe File (No Secrets)"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}safe.txt"
    cat > "$test_file" << 'EOF'
# Safe configuration file
EDITOR=vim
PATH=/usr/local/bin:/usr/bin:/bin
USER=$(whoami)
HOME=$HOME
EOF

    if scan_file "$test_file"; then
        test_pass
    else
        test_fail "False positive on safe file"
    fi

    rm -f "$test_file"
}

test_template_placeholder_detection() {
    test_start "Template Placeholder (Should Pass)"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}template.txt"
    cat > "$test_file" << 'EOF'
# Template file
API_KEY=YOUR_API_KEY_HERE
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID_HERE
DATABASE_URL=postgres://YOUR_DATABASE_USER_HERE:YOUR_DATABASE_PASSWORD_HERE@localhost/db
EOF

    if scan_file "$test_file"; then
        test_pass
    else
        test_fail "Template placeholders should not be detected as secrets"
    fi

    rm -f "$test_file"
}

test_blocked_file_extension() {
    test_start "Blocked File Extension (.pem)"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}cert.pem"
    touch "$test_file"

    if is_blocked_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to block .pem file"
    fi

    rm -f "$test_file"
}

test_blocked_filename() {
    test_start "Blocked Filename (id_rsa)"

    local test_file="${FIXTURES_DIR}/id_rsa"
    touch "$test_file"

    if is_blocked_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to block id_rsa file"
    fi

    rm -f "$test_file"
}

test_template_generation() {
    test_start "Template Generation"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}withsecrets.conf"
    cat > "$test_file" << 'EOF'
# Configuration file
API_KEY=sk-abcd1234567890efghijklmnopqrstuvwxyz
DATABASE_PASSWORD=SuperSecret123!
SAFE_VALUE=This is fine
EOF

    create_template_file "$test_file" >/dev/null 2>&1

    if [[ -f "${test_file}.template" ]]; then
        # Check if template contains placeholders instead of secrets
        if grep -q "YOUR_.*_HERE" "${test_file}.template"; then
            # Check if safe value is preserved
            if grep -q "SAFE_VALUE=This is fine" "${test_file}.template"; then
                test_pass
            else
                test_fail "Template should preserve non-secret values"
            fi
        else
            test_fail "Template should contain YOUR_*_HERE placeholders"
        fi
    else
        test_fail "Template file was not created"
    fi

    rm -f "$test_file" "${test_file}.template"
}

test_whitelist_functionality() {
    test_start "Whitelist Functionality"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}whitelisted.txt"
    cat > "$test_file" << 'EOF'
API_KEY=fake_key_12345
EOF

    # Add to whitelist
    whitelist_file "$test_file" >/dev/null 2>&1

    # Should now pass scan
    if is_whitelisted "$test_file"; then
        test_pass
    else
        test_fail "File should be whitelisted"
    fi

    rm -f "$test_file"
}

test_shell_export_detection() {
    test_start "Shell Export Secret Detection"

    local test_file="${FIXTURES_DIR}/${TEST_PREFIX}bashrc"
    cat > "$test_file" << 'EOF'
#!/bin/bash
export API_TOKEN="1234567890abcdefghijklmnop"
export SECRET_KEY='zyxwvutsrqponmlkjihgfedcba9876543210'
export NORMAL_VAR="short"
EOF

    if ! scan_file "$test_file"; then
        test_pass
    else
        test_fail "Failed to detect secrets in shell exports"
    fi

    rm -f "$test_file"
}

#------------------------------------------------------------------------------
# Main Test Execution
#------------------------------------------------------------------------------

main() {
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║${RESET}  cc-isolate Secret Scanning Test Suite               ${BOLD}║${RESET}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════════╝${RESET}"
    echo

    # Check if gitleaks is available
    if ! check_gitleaks; then
        echo -e "${YELLOW}⚠ GitLeaks not found${RESET}"
        echo "Some tests require gitleaks. Install with:"
        echo "  brew install gitleaks"
        echo "  OR"
        echo "  go install github.com/gitleaks/gitleaks/v8@latest"
        echo
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Create fixtures directory
    mkdir -p "$FIXTURES_DIR"

    # Run tests
    echo -e "${BOLD}Running Tests...${RESET}"
    echo

    test_blocked_file_extension
    test_blocked_filename
    test_aws_key_detection
    test_github_token_detection
    test_private_key_detection
    test_database_url_detection
    test_shell_export_detection
    test_safe_file_detection
    test_template_placeholder_detection
    test_template_generation
    test_whitelist_functionality

    # Clean up
    cleanup_test_files

    # Print summary
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}Test Summary:${RESET}"
    echo -e "  Total:    $TESTS_RUN"
    echo -e "  ${GREEN}Passed:   $TESTS_PASSED${RESET}"
    echo -e "  ${RED}Failed:   $TESTS_FAILED${RESET}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passed!${RESET}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${RESET}"
        exit 1
    fi
}

main "$@"

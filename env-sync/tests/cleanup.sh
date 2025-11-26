#!/usr/bin/env bash
#
# Cleanup Test Artifacts
# Removes all test files created by the test suite
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_SYNC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Cleaning up test artifacts..."

# Remove test fixtures
find "$SCRIPT_DIR/fixtures" -name ".cc-test-*" -delete 2>/dev/null || true

# Remove test whitelist
rm -f "$ENV_SYNC_ROOT/.cc-secrets-whitelist" 2>/dev/null || true

# Remove any leftover template files from tests
find "$SCRIPT_DIR" -name "*.template" -delete 2>/dev/null || true

echo "✓ Cleanup complete"

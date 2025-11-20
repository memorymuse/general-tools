#!/usr/bin/env bash
#
# Secret Scanning Library for cc-isolate
# Uses GitLeaks for local, offline secret detection
#

set -euo pipefail

# Template placeholder pattern
TEMPLATE_PREFIX="YOUR_"
TEMPLATE_SUFFIX="_HERE"

# Colors for output
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' BOLD='' RESET=''
fi

log_info() {
    echo -e "${BLUE}ℹ${RESET} $*"
}

log_success() {
    echo -e "${GREEN}✓${RESET} $*"
}

log_warn() {
    echo -e "${YELLOW}⚠${RESET} $*"
}

log_error() {
    echo -e "${RED}✗${RESET} $*" >&2
}

#------------------------------------------------------------------------------
# GitLeaks Integration
#------------------------------------------------------------------------------

# Check if gitleaks is installed
check_gitleaks() {
    if ! command -v gitleaks >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Install gitleaks (if possible)
install_gitleaks() {
    log_info "GitLeaks not found. Attempting to install..."

    if command -v brew >/dev/null 2>&1; then
        log_info "Installing via Homebrew..."
        brew install gitleaks
        return $?
    elif command -v go >/dev/null 2>&1; then
        log_info "Installing via Go..."
        go install github.com/gitleaks/gitleaks/v8@latest
        return $?
    else
        log_error "Cannot install gitleaks automatically"
        log_error "Please install manually:"
        echo "  Homebrew: brew install gitleaks"
        echo "  Go:       go install github.com/gitleaks/gitleaks/v8@latest"
        echo "  Binary:   https://github.com/gitleaks/gitleaks/releases"
        return 1
    fi
}

# Ensure gitleaks is available
ensure_gitleaks() {
    if ! check_gitleaks; then
        if [[ "${SECRET_SCAN_AUTO_INSTALL:-true}" == "true" ]]; then
            if ! install_gitleaks; then
                return 1
            fi
        else
            log_error "GitLeaks is not installed and auto-install is disabled"
            return 1
        fi
    fi
    return 0
}

#------------------------------------------------------------------------------
# File Type Detection
#------------------------------------------------------------------------------

# Check if file should be blocked by extension/name
is_blocked_file() {
    local file="$1"
    local basename=$(basename "$file")

    # Blocked extensions
    local blocked_extensions=(
        ".pem" ".key" ".p12" ".pfx"
        ".keystore" ".jks" ".pkcs12"
        ".asc" ".gpg" ".pgp"
        ".env" ".env.local" ".env.production" ".env.development"
        ".credentials" ".secrets"
    )

    # Blocked filenames
    local blocked_filenames=(
        "id_rsa" "id_dsa" "id_ecdsa" "id_ed25519"
        "credentials" "credentials.json"
        ".netrc" ".dockercfg"
        "secrets.yml" "vault.yml"
    )

    # Check extensions
    for ext in "${blocked_extensions[@]}"; do
        if [[ "$basename" == *"$ext" ]]; then
            return 0
        fi
    done

    # Check filenames
    for name in "${blocked_filenames[@]}"; do
        if [[ "$basename" == "$name" ]]; then
            return 0
        fi
    done

    return 1
}

# Check if file is whitelisted
is_whitelisted() {
    local file="$1"
    local whitelist_file="${ENV_SYNC_ROOT}/.cc-secrets-whitelist"

    if [[ ! -f "$whitelist_file" ]]; then
        return 1
    fi

    # Check if file is in whitelist
    if grep -qF "$file" "$whitelist_file" 2>/dev/null; then
        return 0
    fi

    return 1
}

#------------------------------------------------------------------------------
# Secret Scanning
#------------------------------------------------------------------------------

# Scan a single file for secrets
scan_file() {
    local file="$1"
    local report_file="${2:-}"

    # Check if file is whitelisted
    if is_whitelisted "$file"; then
        log_info "Skipped (whitelisted): $file"
        return 0
    fi

    # Check if file is blocked by type
    if is_blocked_file "$file"; then
        log_error "Blocked file type: $file"
        log_error "This file type should never be committed to git"
        return 1
    fi

    # Skip if file doesn't exist
    if [[ ! -f "$file" ]]; then
        return 0
    fi

    # Ensure gitleaks is available
    if ! ensure_gitleaks; then
        log_warn "Skipping secret scan (gitleaks not available)"
        return 0
    fi

    # Run gitleaks on file
    local config_file="${ENV_SYNC_ROOT}/.gitleaks.toml"
    local temp_report=$(mktemp)

    local gitleaks_cmd="gitleaks detect --no-git --source=\"$file\""

    if [[ -f "$config_file" ]]; then
        gitleaks_cmd="$gitleaks_cmd --config=\"$config_file\""
    fi

    if [[ -n "$report_file" ]]; then
        gitleaks_cmd="$gitleaks_cmd --report-format=json --report-path=\"$temp_report\""
    fi

    # Run scan (gitleaks exits with 1 if secrets found)
    if eval "$gitleaks_cmd" >/dev/null 2>&1; then
        # No secrets found
        rm -f "$temp_report"
        return 0
    else
        # Secrets found
        if [[ -n "$report_file" ]] && [[ -f "$temp_report" ]]; then
            cat "$temp_report" >> "$report_file"
        fi
        rm -f "$temp_report"
        return 1
    fi
}

# Scan directory for secrets
scan_directory() {
    local dir="$1"
    local found_secrets=0
    local total_files=0
    local blocked_files=0

    log_info "Scanning directory: $dir"
    echo

    # Find all files (excluding .git, node_modules, etc.)
    while IFS= read -r -d '' file; do
        ((total_files++))

        # Show progress
        echo -ne "\rScanning: $total_files files checked..."

        if ! scan_file "$file"; then
            ((found_secrets++))
            if is_blocked_file "$file"; then
                ((blocked_files++))
            fi
        fi
    done < <(find "$dir" -type f \
        -not -path "*/.git/*" \
        -not -path "*/node_modules/*" \
        -not -path "*/.cc-test-*" \
        -print0)

    echo -e "\r\033[K"  # Clear progress line

    if [[ $found_secrets -gt 0 ]]; then
        log_error "Found secrets in $found_secrets file(s)"
        if [[ $blocked_files -gt 0 ]]; then
            log_error "  - $blocked_files blocked file type(s)"
        fi
        return 1
    else
        log_success "No secrets found ($total_files files scanned)"
        return 0
    fi
}

# Scan files staged for commit
scan_staged_files() {
    local repo_root="$1"
    local found_secrets=0

    log_info "Scanning staged files..."
    echo

    # Get list of staged files
    cd "$repo_root"
    local staged_files=$(git diff --cached --name-only --diff-filter=ACM)

    if [[ -z "$staged_files" ]]; then
        log_info "No files staged for commit"
        return 0
    fi

    # Scan each file
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            echo -n "  "
            if scan_file "$file"; then
                echo -e "${GREEN}✓${RESET} $file"
            else
                echo -e "${RED}✗${RESET} $file ${YELLOW}(secrets detected)${RESET}"
                ((found_secrets++))
            fi
        fi
    done <<< "$staged_files"

    echo

    if [[ $found_secrets -gt 0 ]]; then
        return 1
    fi

    return 0
}

#------------------------------------------------------------------------------
# Template Generation
#------------------------------------------------------------------------------

# Generate template variable name from secret description
generate_template_var() {
    local description="$1"

    # Convert to uppercase and replace spaces/special chars with underscores
    local var_name=$(echo "$description" | tr '[:lower:]' '[:upper:]' | sed 's/[^A-Z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')

    # Add prefix and suffix
    echo "${TEMPLATE_PREFIX}${var_name}${TEMPLATE_SUFFIX}"
}

# Create template file from original with secrets replaced
create_template_file() {
    local source_file="$1"
    local template_file="${source_file}.template"

    log_info "Creating template: $template_file"

    # Ensure gitleaks is available
    if ! ensure_gitleaks; then
        log_error "Cannot create template without gitleaks"
        return 1
    fi

    # Run gitleaks and get JSON report
    local report_file=$(mktemp)
    local config_file="${ENV_SYNC_ROOT}/.gitleaks.toml"

    local gitleaks_cmd="gitleaks detect --no-git --source=\"$source_file\" --report-format=json --report-path=\"$report_file\""

    if [[ -f "$config_file" ]]; then
        gitleaks_cmd="$gitleaks_cmd --config=\"$config_file\""
    fi

    # Run scan
    eval "$gitleaks_cmd" >/dev/null 2>&1 || true

    # Check if secrets were found
    if [[ ! -s "$report_file" ]]; then
        log_info "No secrets found, copying file as-is"
        cp "$source_file" "$template_file"
        rm -f "$report_file"
        return 0
    fi

    # Parse JSON and replace secrets
    cp "$source_file" "$template_file"

    # Extract secrets from JSON report (using simple grep/sed since we can't rely on jq)
    local secrets_found=0

    # Read JSON and extract Secret and Description fields
    while IFS= read -r line; do
        if echo "$line" | grep -q '"Secret":'; then
            local secret=$(echo "$line" | sed 's/.*"Secret": *"\([^"]*\)".*/\1/')
            # Get next description line
            local description=$(grep -A 5 "\"Secret\": \"$secret\"" "$report_file" | grep '"Description":' | head -1 | sed 's/.*"Description": *"\([^"]*\)".*/\1/')

            if [[ -z "$description" ]]; then
                description="SECRET"
            fi

            local template_var=$(generate_template_var "$description")

            # Replace in template file (escape special regex chars)
            local escaped_secret=$(echo "$secret" | sed 's/[]\/$*.^[]/\\&/g')
            sed -i.bak "s/$escaped_secret/$template_var/g" "$template_file"
            rm -f "${template_file}.bak"

            ((secrets_found++))
            log_success "Replaced secret: $description -> $template_var"
        fi
    done < "$report_file"

    rm -f "$report_file"

    log_success "Template created with $secrets_found secret(s) replaced"

    return 0
}

# Scan for unconverted template values in live files
scan_for_template_placeholders() {
    local dir="$1"
    local found=0

    log_info "Scanning for unconverted template placeholders..."

    # Search for YOUR_*_HERE pattern
    while IFS= read -r -d '' file; do
        if grep -q "${TEMPLATE_PREFIX}.*${TEMPLATE_SUFFIX}" "$file" 2>/dev/null; then
            log_warn "Found placeholder in: $file"
            grep --color=always -n "${TEMPLATE_PREFIX}.*${TEMPLATE_SUFFIX}" "$file" | sed 's/^/  /'
            ((found++))
        fi
    done < <(find "$dir" -type f \
        -not -path "*/.git/*" \
        -not -path "*/node_modules/*" \
        -not -path "*/.template" \
        -not -path "*/.example" \
        -print0)

    if [[ $found -gt 0 ]]; then
        echo
        log_warn "Found $found file(s) with template placeholders"
        log_info "These should be replaced with actual values"
        return 1
    else
        log_success "No template placeholders found"
        return 0
    fi
}

#------------------------------------------------------------------------------
# Whitelist Management
#------------------------------------------------------------------------------

# Add file to whitelist
whitelist_file() {
    local file="$1"
    local whitelist_file="${ENV_SYNC_ROOT}/.cc-secrets-whitelist"

    # Create whitelist if doesn't exist
    if [[ ! -f "$whitelist_file" ]]; then
        cat > "$whitelist_file" << 'EOF'
# cc-isolate Secret Scan Whitelist
# Add files to skip during secret scanning (one per line)
# Use relative paths from env-sync root
#
# Example:
#   dotfiles/.gitconfig
#   profiles/global/bashrc
#
EOF
    fi

    # Check if already whitelisted
    if grep -qF "$file" "$whitelist_file" 2>/dev/null; then
        log_info "Already whitelisted: $file"
        return 0
    fi

    # Add to whitelist
    echo "$file" >> "$whitelist_file"
    log_success "Added to whitelist: $file"
}

# Export functions
export -f check_gitleaks
export -f install_gitleaks
export -f ensure_gitleaks
export -f is_blocked_file
export -f is_whitelisted
export -f scan_file
export -f scan_directory
export -f scan_staged_files
export -f create_template_file
export -f generate_template_var
export -f scan_for_template_placeholders
export -f whitelist_file

#!/usr/bin/env bash
#
# Secrets Sync Library for cc-isolate
# Password-based encryption using age for cross-machine secret synchronization
#

set -euo pipefail

# File locations
SECRETS_YAML="${ENV_SYNC_ROOT}/secrets.yaml"
SECRETS_ENCRYPTED="${ENV_SYNC_ROOT}/secrets.yaml.age"
GLOBAL_ENV_FILE="${HOME}/.env.secrets"

# Colors (inherit from parent or define)
if [[ -t 1 ]] && [[ -z "${RED:-}" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
fi

#------------------------------------------------------------------------------
# Age Installation
#------------------------------------------------------------------------------

check_age() {
    command -v age >/dev/null 2>&1
}

install_age() {
    echo -e "${BLUE}i${RESET} age not found. Attempting to install..."

    if command -v brew >/dev/null 2>&1; then
        echo -e "${BLUE}i${RESET} Installing via Homebrew..."
        brew install age
        return $?
    elif command -v apt-get >/dev/null 2>&1; then
        echo -e "${BLUE}i${RESET} Installing via apt..."
        sudo apt-get update && sudo apt-get install -y age
        return $?
    elif command -v pacman >/dev/null 2>&1; then
        echo -e "${BLUE}i${RESET} Installing via pacman..."
        sudo pacman -S age
        return $?
    else
        echo -e "${RED}x${RESET} Cannot install age automatically" >&2
        echo "Please install manually:" >&2
        echo "  macOS:  brew install age" >&2
        echo "  Ubuntu: sudo apt install age" >&2
        echo "  Arch:   sudo pacman -S age" >&2
        echo "  Other:  https://github.com/FiloSottile/age#installation" >&2
        return 1
    fi
}

ensure_age() {
    if ! check_age; then
        if ! install_age; then
            return 1
        fi
    fi
    return 0
}

#------------------------------------------------------------------------------
# Env File Detection
#------------------------------------------------------------------------------

# Find all env-like files in a directory
find_env_files() {
    local search_dir="${1:-.}"

    find "$search_dir" -type f \( \
        -name ".env" -o \
        -name ".env.*" -o \
        -name "*.env" -o \
        -name "*-env" -o \
        -name "*_env" -o \
        -name ".envrc" \
    \) ! -name "*.example" \
       ! -name "*.template" \
       ! -name "*.sample" \
       ! -path "*/.git/*" \
       ! -path "*/node_modules/*" \
       ! -path "*/.venv/*" \
       ! -path "*/venv/*" \
       2>/dev/null | sort
}

# Check if a file matches env patterns
is_env_file() {
    local file="$1"
    local basename=$(basename "$file")

    # Match patterns
    [[ "$basename" == ".env" ]] && return 0
    [[ "$basename" == .env.* ]] && [[ "$basename" != *.example ]] && [[ "$basename" != *.template ]] && [[ "$basename" != *.sample ]] && return 0
    [[ "$basename" == *.env ]] && [[ "$basename" != *.example ]] && [[ "$basename" != *.template ]] && [[ "$basename" != *.sample ]] && return 0
    [[ "$basename" == *-env ]] && return 0
    [[ "$basename" == *_env ]] && return 0
    [[ "$basename" == ".envrc" ]] && return 0

    return 1
}

#------------------------------------------------------------------------------
# YAML Helpers (minimal, no external deps)
#------------------------------------------------------------------------------

# Simple YAML writer - we keep it basic to avoid jq/yq dependency
# Format:
# global:
#   VAR_NAME: "value"
# projects:
#   "/path/to/project":
#     VAR_NAME: "value"

yaml_escape() {
    local value="$1"
    # Escape double quotes and backslashes
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    # Wrap in quotes
    echo "\"$value\""
}

# Parse a simple .env file and output VAR=VALUE lines
parse_env_file() {
    local file="$1"

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        # Skip lines without =
        [[ "$line" != *"="* ]] && continue

        # Extract variable name and value
        local var_name="${line%%=*}"
        local var_value="${line#*=}"

        # Trim whitespace from var_name
        var_name="${var_name#"${var_name%%[![:space:]]*}"}"
        var_name="${var_name%"${var_name##*[![:space:]]}"}"

        # Skip if var_name is empty or contains spaces
        [[ -z "$var_name" ]] && continue
        [[ "$var_name" == *" "* ]] && continue

        # Remove surrounding quotes from value if present
        if [[ "$var_value" =~ ^\"(.*)\"$ ]] || [[ "$var_value" =~ ^\'(.*)\'$ ]]; then
            var_value="${BASH_REMATCH[1]}"
        fi

        echo "${var_name}=${var_value}"
    done < "$file"
}

#------------------------------------------------------------------------------
# Core Operations
#------------------------------------------------------------------------------

# Export env files to secrets.yaml
secrets_export() {
    local search_dirs=("$@")
    [[ ${#search_dirs[@]} -eq 0 ]] && search_dirs=("$HOME")

    echo -e "${BLUE}i${RESET} Exporting secrets from env files..."
    echo

    local temp_dir=$(mktemp -d)
    local temp_global="$temp_dir/global"
    local temp_projects_list="$temp_dir/projects_list"
    local found_files=0

    touch "$temp_global"
    touch "$temp_projects_list"

    for search_dir in "${search_dirs[@]}"; do
        echo -e "${CYAN}Searching:${RESET} $search_dir"

        while IFS= read -r env_file; do
            [[ -z "$env_file" ]] && continue
            found_files=$((found_files + 1))

            local dir=$(dirname "$env_file")
            local rel_dir="${dir/#$HOME/~}"

            echo -e "  ${GREEN}+${RESET} $env_file"

            # Determine if global or project-specific
            if [[ "$dir" == "$HOME" ]] || [[ "$env_file" == "$HOME/.env" ]] || [[ "$env_file" == "$HOME/.envrc" ]]; then
                # Global
                parse_env_file "$env_file" >> "$temp_global"
            else
                # Project-specific - use sanitized filename
                local safe_name=$(echo "$rel_dir" | sed 's/[^a-zA-Z0-9]/_/g')
                local temp_file="$temp_dir/project_${safe_name}"

                # Track the mapping: safe_name -> rel_dir
                echo "${safe_name}|${rel_dir}" >> "$temp_projects_list"

                parse_env_file "$env_file" >> "$temp_file"
            fi
        done < <(find_env_files "$search_dir")
    done

    echo

    if [[ $found_files -eq 0 ]]; then
        echo -e "${YELLOW}!${RESET} No env files found"
        rm -rf "$temp_dir"
        return 1
    fi

    # Generate YAML
    echo -e "${BLUE}i${RESET} Generating secrets.yaml..."

    {
        echo "# Secrets Vault - Generated $(date -Iseconds)"
        echo "# Edit this file, then run: cc-isolate vault encrypt"
        echo "#"
        echo "# WARNING: This file contains secrets in plaintext!"
        echo "# It should be encrypted before committing."
        echo ""
        echo "global:"

        if [[ -s "$temp_global" ]]; then
            # Deduplicate and sort
            sort -u "$temp_global" | while IFS='=' read -r var_name var_value; do
                [[ -z "$var_name" ]] && continue
                echo "  ${var_name}: $(yaml_escape "$var_value")"
            done
        else
            echo "  # No global secrets found"
            echo "  # Example:"
            echo "  # GITHUB_TOKEN: \"ghp_xxxxxxxxxxxx\""
        fi

        echo ""
        echo "projects:"

        # Get unique project paths
        local has_projects=false
        if [[ -s "$temp_projects_list" ]]; then
            # Deduplicate project list and iterate
            sort -u "$temp_projects_list" | while IFS='|' read -r safe_name rel_dir; do
                local temp_file="$temp_dir/project_${safe_name}"
                if [[ -s "$temp_file" ]]; then
                    has_projects=true
                    echo "  \"${rel_dir}\":"
                    sort -u "$temp_file" | while IFS='=' read -r var_name var_value; do
                        [[ -z "$var_name" ]] && continue
                        echo "    ${var_name}: $(yaml_escape "$var_value")"
                    done
                fi
            done
        fi

        if [[ "$has_projects" != "true" ]] && [[ ! -s "$temp_projects_list" ]]; then
            echo "  # No project-specific secrets found"
            echo "  # Example:"
            echo "  # \"~/projects/my-app\":"
            echo "  #   DATABASE_URL: \"postgres://...\""
        fi

    } > "$SECRETS_YAML"

    # Cleanup temp files
    rm -rf "$temp_dir"

    echo -e "${GREEN}✓${RESET} Exported to: $SECRETS_YAML"
    echo
    echo -e "${YELLOW}!${RESET} Next steps:"
    echo "  1. Review and edit: ${CYAN}$SECRETS_YAML${RESET}"
    echo "  2. Encrypt: ${CYAN}cc-isolate vault encrypt${RESET}"
    echo

    return 0
}

# Encrypt secrets.yaml -> secrets.yaml.age
# Args: [--auto] - skip confirmation, auto-delete plaintext
secrets_encrypt() {
    local auto_mode=false
    [[ "$1" == "--auto" ]] && auto_mode=true

    if ! ensure_age; then
        return 1
    fi

    if [[ ! -f "$SECRETS_YAML" ]]; then
        echo -e "${RED}x${RESET} No secrets.yaml found" >&2
        echo "Run 'devenv vault export' first, or create secrets.yaml manually" >&2
        return 1
    fi

    echo -e "${BLUE}i${RESET} Encrypting secrets.yaml..."

    # Prompt for password
    if ! age -p -o "$SECRETS_ENCRYPTED" "$SECRETS_YAML"; then
        echo -e "${RED}x${RESET} Encryption failed" >&2
        return 1
    fi

    echo -e "${GREEN}✓${RESET} Encrypted"

    # Auto-delete plaintext in auto mode, otherwise ask
    if $auto_mode; then
        rm -f "$SECRETS_YAML"
    else
        echo -e "${YELLOW}?${RESET} Remove plaintext secrets.yaml? [Y/n] "
        read -r response
        if [[ ! "$response" =~ ^[Nn] ]]; then
            rm -f "$SECRETS_YAML"
            echo -e "${GREEN}✓${RESET} Removed plaintext file"
        else
            echo -e "${YELLOW}!${RESET} Plaintext file kept - DO NOT commit it!"
        fi
    fi

    return 0
}

# Decrypt secrets.yaml.age -> secrets.yaml
secrets_decrypt() {
    if ! ensure_age; then
        return 1
    fi

    if [[ ! -f "$SECRETS_ENCRYPTED" ]]; then
        echo -e "${RED}x${RESET} No encrypted secrets found: $SECRETS_ENCRYPTED" >&2
        return 1
    fi

    echo -e "${BLUE}i${RESET} Decrypting secrets..."
    echo

    # Prompt for password
    echo -e "${CYAN}Enter decryption password:${RESET}"
    if ! age -d -o "$SECRETS_YAML" "$SECRETS_ENCRYPTED"; then
        echo -e "${RED}x${RESET} Decryption failed (wrong password?)" >&2
        return 1
    fi

    echo
    echo -e "${GREEN}✓${RESET} Decrypted to: $SECRETS_YAML"

    return 0
}

# Deploy secrets to ~/.env.secrets and project .env files
# Args: [--auto] - skip confirmations
secrets_deploy() {
    local auto_mode=false
    [[ "$1" == "--auto" ]] && auto_mode=true

    if [[ ! -f "$SECRETS_YAML" ]]; then
        # Try to decrypt first
        if [[ -f "$SECRETS_ENCRYPTED" ]]; then
            echo -e "${BLUE}i${RESET} Decrypting secrets..."
            if ! secrets_decrypt; then
                return 1
            fi
        else
            echo -e "${RED}x${RESET} No secrets found (neither .yaml nor .age)" >&2
            return 1
        fi
    fi

    echo -e "${BLUE}i${RESET} Deploying secrets..."
    echo

    local temp_dir=$(mktemp -d)
    local temp_global="$temp_dir/global"
    local temp_projects_list="$temp_dir/projects_list"

    local in_global=false
    local in_projects=false
    local current_project=""
    local current_project_file=""

    touch "$temp_global"
    touch "$temp_projects_list"

    # Parse YAML (simple line-by-line parser)
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        # Detect sections
        if [[ "$line" == "global:" ]]; then
            in_global=true
            in_projects=false
            current_project=""
            continue
        elif [[ "$line" == "projects:" ]]; then
            in_global=false
            in_projects=true
            current_project=""
            continue
        fi

        # Detect project path (line ending with :)
        if $in_projects && [[ "$line" =~ ^[[:space:]]+\"([^\"]+)\":$ ]]; then
            current_project="${BASH_REMATCH[1]}"
            # Expand ~ to $HOME
            current_project="${current_project/#\~/$HOME}"
            # Create temp file for this project
            local safe_name=$(echo "$current_project" | sed 's/[^a-zA-Z0-9]/_/g')
            current_project_file="$temp_dir/project_${safe_name}"
            echo "${safe_name}|${current_project}" >> "$temp_projects_list"
            continue
        fi

        # Parse key: "value" pairs
        if [[ "$line" =~ ^[[:space:]]+([A-Za-z_][A-Za-z0-9_]*):\ *\"(.*)\"$ ]]; then
            local var_name="${BASH_REMATCH[1]}"
            local var_value="${BASH_REMATCH[2]}"

            # Unescape
            var_value="${var_value//\\\"/\"}"
            var_value="${var_value//\\\\/\\}"

            if $in_global; then
                echo "${var_name}=${var_value}" >> "$temp_global"
            elif [[ -n "$current_project" ]] && [[ -n "$current_project_file" ]]; then
                echo "${var_name}=${var_value}" >> "$current_project_file"
            fi
        fi
    done < "$SECRETS_YAML"

    # Deploy global secrets
    if [[ -s "$temp_global" ]]; then
        echo -e "${CYAN}Global secrets -> ${RESET}$GLOBAL_ENV_FILE"

        {
            echo "# Global secrets - deployed by cc-isolate"
            echo "# Generated: $(date -Iseconds)"
            echo "# DO NOT EDIT - changes will be overwritten"
            echo ""
            cat "$temp_global"
        } > "$GLOBAL_ENV_FILE"

        chmod 600 "$GLOBAL_ENV_FILE"
        local global_count=$(wc -l < "$temp_global" | tr -d ' ')
        echo -e "  ${GREEN}✓${RESET} ${global_count} variables deployed"
    fi

    # Deploy project secrets
    if [[ -s "$temp_projects_list" ]]; then
        sort -u "$temp_projects_list" | while IFS='|' read -r safe_name project_path; do
            local temp_file="$temp_dir/project_${safe_name}"
            local env_file="${project_path}/.env"

            if [[ ! -d "$project_path" ]]; then
                echo -e "${YELLOW}!${RESET} Skipping (dir not found): $project_path"
                continue
            fi

            if [[ ! -s "$temp_file" ]]; then
                continue
            fi

            echo -e "${CYAN}Project secrets -> ${RESET}$env_file"

            {
                echo "# Project secrets - deployed by cc-isolate"
                echo "# Generated: $(date -Iseconds)"
                echo "# DO NOT EDIT - changes will be overwritten"
                echo ""
                cat "$temp_file"
            } > "$env_file"

            chmod 600 "$env_file"
            local count=$(wc -l < "$temp_file" | tr -d ' ')
            echo -e "  ${GREEN}✓${RESET} $count variables deployed"
        done
    fi

    # Cleanup
    rm -rf "$temp_dir"

    echo
    echo -e "${GREEN}✓${RESET} Secrets deployed"
    echo

    # Suggest sourcing (only in non-auto mode)
    if ! $auto_mode; then
        echo -e "${BLUE}i${RESET} To use global secrets, add to your shell profile:"
        echo -e "  ${CYAN}[ -f ~/.env.secrets ] && source ~/.env.secrets${RESET}"
        echo
    fi

    # Clean up plaintext - auto in auto_mode, ask otherwise
    if $auto_mode; then
        rm -f "$SECRETS_YAML"
    else
        echo -e "${YELLOW}?${RESET} Remove plaintext secrets.yaml? [Y/n] "
        read -r response
        if [[ ! "$response" =~ ^[Nn] ]]; then
            rm -f "$SECRETS_YAML"
            echo -e "${GREEN}✓${RESET} Removed plaintext file"
        fi
    fi

    return 0
}

# Edit secrets (decrypt -> $EDITOR -> re-encrypt)
secrets_edit() {
    local editor="${EDITOR:-vim}"

    # Decrypt if needed
    if [[ ! -f "$SECRETS_YAML" ]]; then
        if [[ -f "$SECRETS_ENCRYPTED" ]]; then
            if ! secrets_decrypt; then
                return 1
            fi
        else
            echo -e "${YELLOW}!${RESET} No secrets file found. Creating template..."
            secrets_init
        fi
    fi

    echo -e "${BLUE}i${RESET} Opening secrets in $editor..."
    echo -e "${YELLOW}!${RESET} Save and close editor to re-encrypt"
    echo

    # Get modification time before edit
    local mtime_before=$(stat -f %m "$SECRETS_YAML" 2>/dev/null || stat -c %Y "$SECRETS_YAML" 2>/dev/null)

    # Open editor
    "$editor" "$SECRETS_YAML"

    # Check if file was modified
    local mtime_after=$(stat -f %m "$SECRETS_YAML" 2>/dev/null || stat -c %Y "$SECRETS_YAML" 2>/dev/null)

    if [[ "$mtime_before" != "$mtime_after" ]]; then
        echo
        echo -e "${BLUE}i${RESET} File modified. Re-encrypting..."
        secrets_encrypt
    else
        echo
        echo -e "${BLUE}i${RESET} No changes made"
        rm -f "$SECRETS_YAML"
    fi

    return 0
}

# Create initial secrets.yaml template
secrets_init() {
    if [[ -f "$SECRETS_YAML" ]] || [[ -f "$SECRETS_ENCRYPTED" ]]; then
        echo -e "${YELLOW}!${RESET} Secrets file already exists"
        return 1
    fi

    cat > "$SECRETS_YAML" << 'EOF'
# Secrets Vault
# Edit this file, then run: cc-isolate vault encrypt
#
# WARNING: This file contains secrets in plaintext!
# It should be encrypted before committing.

global:
  # Global secrets available everywhere
  # Example:
  # GITHUB_TOKEN: "ghp_xxxxxxxxxxxx"
  # VERCEL_TOKEN: "xxxxx"

projects:
  # Project-specific secrets
  # Use ~ for home directory
  # Example:
  # "~/projects/my-app":
  #   DATABASE_URL: "postgres://user:pass@host:5432/db"
  #   API_KEY: "sk-xxxxx"
EOF

    echo -e "${GREEN}✓${RESET} Created: $SECRETS_YAML"
    echo
    echo -e "${BLUE}i${RESET} Next steps:"
    echo "  1. Edit: ${CYAN}$SECRETS_YAML${RESET}"
    echo "  2. Encrypt: ${CYAN}cc-isolate vault encrypt${RESET}"
    echo

    return 0
}

# Show diff between current deployed and vault
secrets_diff() {
    if [[ ! -f "$SECRETS_YAML" ]]; then
        if [[ -f "$SECRETS_ENCRYPTED" ]]; then
            if ! secrets_decrypt; then
                return 1
            fi
        else
            echo -e "${RED}x${RESET} No secrets file found" >&2
            return 1
        fi
    fi

    echo -e "${BLUE}i${RESET} Comparing vault with deployed secrets..."
    echo

    # Compare global
    if [[ -f "$GLOBAL_ENV_FILE" ]]; then
        echo -e "${CYAN}Global secrets ($GLOBAL_ENV_FILE):${RESET}"
        # Extract global vars from YAML and compare
        # This is a simplified diff - just shows what's in each
        echo "  (comparison not yet implemented - showing current)"
        grep -v '^#' "$GLOBAL_ENV_FILE" 2>/dev/null | sed 's/^/  /' || echo "  (empty)"
    else
        echo -e "${YELLOW}!${RESET} No global secrets deployed yet"
    fi

    echo
    echo -e "${BLUE}i${RESET} Run 'cc-isolate vault deploy' to apply changes"

    # Clean up
    rm -f "$SECRETS_YAML"

    return 0
}

# Export functions
export -f check_age
export -f install_age
export -f ensure_age
export -f find_env_files
export -f is_env_file
export -f secrets_export
export -f secrets_encrypt
export -f secrets_decrypt
export -f secrets_deploy
export -f secrets_edit
export -f secrets_init
export -f secrets_diff

#!/usr/bin/env bash
#
# cc-isolate Installation Script
# Sets up the Claude Code isolation system
#

set -euo pipefail

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

print_header() {
    echo -e "${BLUE}${BOLD}╔═══════════════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}${BOLD}║${RESET}  ${CYAN}cc-isolate${RESET} Installation                     ${BLUE}${BOLD}║${RESET}"
    echo -e "${BLUE}${BOLD}╚═══════════════════════════════════════════════════╝${RESET}"
    echo
}

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

die() {
    log_error "$*"
    exit 1
}

print_header

log_info "Installing cc-isolate from: $SCRIPT_DIR"
echo

# Source platform detection
source "$SCRIPT_DIR/lib/platform.sh"

log_info "Detected platform: $(get_platform_name)"
echo

# Step 1: Make cc-isolate executable
log_info "Making cc-isolate executable..."
chmod +x "$SCRIPT_DIR/bin/cc-isolate"
log_success "cc-isolate is now executable"

# Step 2: Create symlink in /usr/local/bin if possible
if [[ -d "/usr/local/bin" ]] && [[ -w "/usr/local/bin" ]]; then
    log_info "Creating symlink in /usr/local/bin..."
    ln -sf "$SCRIPT_DIR/bin/cc-isolate" /usr/local/bin/cc-isolate
    log_success "Symlink created: /usr/local/bin/cc-isolate"
    INSTALL_METHOD="symlink"
elif [[ -d "/usr/local/bin" ]]; then
    log_warn "/usr/local/bin exists but is not writable"
    log_info "Trying with sudo..."
    if sudo ln -sf "$SCRIPT_DIR/bin/cc-isolate" /usr/local/bin/cc-isolate; then
        log_success "Symlink created: /usr/local/bin/cc-isolate (with sudo)"
        INSTALL_METHOD="symlink"
    else
        log_warn "Failed to create symlink in /usr/local/bin"
        INSTALL_METHOD="path"
    fi
else
    log_warn "/usr/local/bin does not exist"
    INSTALL_METHOD="path"
fi

# Step 3: Create config file if it doesn't exist
if [[ ! -f "$SCRIPT_DIR/config.sh" ]]; then
    log_info "Creating default configuration..."
    cat > "$SCRIPT_DIR/config.sh" << 'EOF'
#!/usr/bin/env bash
#
# cc-isolate Configuration
# Edit this file to customize your isolation settings
#

# System bashrc location (auto-detected by default)
# SYSTEM_BASHRC="$HOME/.bashrc"

# Protect system bashrc with immutable flag when mounted
PROTECT_SYSTEM_BASHRC=true

# Dotfile sync mode: "all", "list", or "none"
DOTFILE_SYNC_MODE="list"

# List of dotfiles to sync (only used when DOTFILE_SYNC_MODE="list")
# WARNING: Only sync safe dotfiles! Never sync files containing secrets
DOTFILES_TO_SYNC=".bash_aliases .inputrc .editorconfig"

# ============================================================================
# Secret Scanning Configuration
# ============================================================================

# Enable secret scanning before push (RECOMMENDED: true)
SECRET_SCAN_ENABLED=true

# Automatically install gitleaks if not found (requires brew or go)
SECRET_SCAN_AUTO_INSTALL=true

# Block push when secrets are detected (RECOMMENDED: true)
SECRET_BLOCK_PUSH=true

# Automatically create template files when secrets are detected
# Templates replace secrets with YOUR_*_HERE placeholders
SECRET_CREATE_TEMPLATES=true

# Template placeholder pattern (for easy scanning)
# Secrets are replaced with: YOUR_<SECRET_NAME>_HERE
# Example: YOUR_API_KEY_HERE, YOUR_AWS_ACCESS_KEY_ID_HERE
# To find unconverted placeholders: cc-isolate secrets check

# ============================================================================
# 1Password CLI Integration
# ============================================================================

# Enable 1Password CLI integration (requires 'op' command and desktop app)
# When enabled, the shell plugin provides seamless secret injection
# Documentation: https://developer.1password.com/docs/cli/shell-plugins
CC_ISOLATE_1PASSWORD_ENABLED=true

# Auto-signin when session expires (requires biometric authentication)
# RECOMMENDED: false (let 1Password desktop app handle authentication)
CC_ISOLATE_1PASSWORD_AUTO_SIGNIN=false

# Default 1Password account (optional)
# Leave empty to use default account, or set to your account subdomain
# Example: "my-team.1password.com"
CC_ISOLATE_1PASSWORD_ACCOUNT=""

# ============================================================================
# UI Configuration
# ============================================================================

# Enable custom bash prompt with git branch display
CC_ISOLATE_PROMPT_ENABLED=true

# Show welcome message when shell starts
CC_ISOLATE_SHOW_WELCOME=false

# Additional configuration can be added here
EOF
    log_success "Configuration file created: $SCRIPT_DIR/config.sh"
else
    log_info "Configuration file already exists: $SCRIPT_DIR/config.sh"
fi

# Step 4: Create global profile with default bashrc
if [[ ! -f "$SCRIPT_DIR/profiles/global/bashrc" ]]; then
    log_info "Creating global profile..."
    cat > "$SCRIPT_DIR/profiles/global/bashrc" << 'EOF'
#!/usr/bin/env bash
#
# CC-Isolate Global Profile
# This file is sourced AFTER the system bashrc for all Claude Code sessions
# Settings here override system settings
#

# ============================================================================
# Claude Code Isolated Environment
# ============================================================================

# Visual indicator that we're in CC isolated mode
if [[ -n "$PS1" ]]; then
    # Add [CC] prefix to prompt
    PS1='\[\033[01;35m\][CC]\[\033[00m\] '"$PS1"
fi

# ============================================================================
# Safe Defaults - Restrict Dangerous Operations
# ============================================================================

# Prevent accidental overwrites
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'

# Safer rm with trash if available
if command -v trash >/dev/null 2>&1; then
    alias rm='trash'
fi

# ============================================================================
# Environment Variables
# ============================================================================

# Set default editor
export EDITOR="${EDITOR:-vim}"
export VISUAL="${VISUAL:-vim}"

# Increase history size
export HISTSIZE=10000
export HISTFILESIZE=20000

# Avoid duplicate entries in history
export HISTCONTROL=ignoredups:erasedups

# ============================================================================
# PATH Management
# ============================================================================

# Add local bin directories to PATH if they exist
[[ -d "$HOME/bin" ]] && export PATH="$HOME/bin:$PATH"
[[ -d "$HOME/.local/bin" ]] && export PATH="$HOME/.local/bin:$PATH"

# ============================================================================
# Useful Aliases
# ============================================================================

# List aliases
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'

# Git aliases
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate'
alias gp='git pull'

# Safe defaults for common commands
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# ============================================================================
# Functions
# ============================================================================

# Quick directory navigation
..() {
    local count="${1:-1}"
    local path=""
    for ((i=0; i<count; i++)); do
        path="../$path"
    done
    cd "$path" || return
}

# Make directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# ============================================================================
# Claude Code Specific Settings
# ============================================================================

# Limit operations to current working directory for safety
# (This is a reminder - actual enforcement is done by CC sandbox mode)

# Set a marker that CC isolation is active
export CC_ISOLATED=true

# ============================================================================
# Custom Settings
# ============================================================================

# Add your custom settings below this line
EOF
    log_success "Global profile created: $SCRIPT_DIR/profiles/global/bashrc"
else
    log_info "Global profile already exists"
fi

# Step 5: Create README for global profile
if [[ ! -f "$SCRIPT_DIR/profiles/global/README.md" ]]; then
    cat > "$SCRIPT_DIR/profiles/global/README.md" << 'EOF'
# Global Profile

This is the default profile used for all Claude Code sessions unless a specific profile is selected.

## Files

- `bashrc` - Main bash configuration file sourced after system bashrc
- `README.md` - This file

## Customization

Edit `bashrc` to customize your Claude Code environment. Settings here will override system bashrc settings.

Common customizations:
- Environment variables
- Aliases
- Functions
- PATH modifications
- Prompt customization

## Safety

This profile includes several safety features:
- Interactive confirmation for `cp`, `mv`, `rm`
- Visual indicator `[CC]` in prompt
- `CC_ISOLATED` environment variable set
EOF
fi

# Step 6: Create example project profile
if [[ ! -d "$SCRIPT_DIR/profiles/projects/example" ]]; then
    log_info "Creating example project profile..."
    mkdir -p "$SCRIPT_DIR/profiles/projects/example"

    cat > "$SCRIPT_DIR/profiles/projects/example/bashrc" << 'EOF'
#!/usr/bin/env bash
#
# Example Project Profile
# Copy this to create project-specific profiles
#

# Project-specific environment variables
export PROJECT_NAME="example"
export PROJECT_ENV="development"

# Project-specific aliases
alias build='echo "Running build for $PROJECT_NAME..."'
alias test='echo "Running tests for $PROJECT_NAME..."'

# Add project tools to PATH
# export PATH="$HOME/projects/example/tools:$PATH"

# Add your project-specific customizations below:
EOF

    log_success "Example project profile created"
fi

# Step 7: Create .gitignore
if [[ ! -f "$SCRIPT_DIR/.gitignore" ]]; then
    log_info "Creating .gitignore..."
    cat > "$SCRIPT_DIR/.gitignore" << 'EOF'
# CC-Isolate Generated Files
.state
.cc-env
system-backup/

# OS Files
.DS_Store
Thumbs.db

# Editor Files
.vscode/
.idea/
*.swp
*.swo
*~

# Don't ignore example dotfiles
!dotfiles/.gitconfig.example
EOF
    log_success ".gitignore created"
fi

# Step 8: Create example dotfiles
if [[ ! -f "$SCRIPT_DIR/dotfiles/.gitconfig.example" ]]; then
    log_info "Creating example dotfiles..."
    cat > "$SCRIPT_DIR/dotfiles/.gitconfig.example" << 'EOF'
[user]
    name = Your Name
    email = your.email@example.com

[core]
    editor = vim
    autocrlf = input

[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD

[color]
    ui = auto

[push]
    default = simple

[pull]
    rebase = false
EOF
    log_success "Example dotfiles created"
fi

echo
echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║${RESET}  Installation Complete!                       ${GREEN}${BOLD}║${RESET}"
echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════╝${RESET}"
echo

# Print next steps
echo -e "${BOLD}Next Steps:${RESET}"
echo

if [[ "$INSTALL_METHOD" == "symlink" ]]; then
    echo -e "1. Run ${CYAN}cc-isolate --help${RESET} to see available commands"
else
    echo -e "1. Add to PATH: ${CYAN}export PATH=\"$SCRIPT_DIR/bin:\$PATH\"${RESET}"
    echo -e "   Add the above line to your shell profile (~/.bashrc or ~/.bash_profile)"
    echo
    echo -e "2. Run ${CYAN}cc-isolate --help${RESET} to see available commands"
fi

echo
echo -e "3. Mount isolation: ${CYAN}cc-isolate mount${RESET}"
echo
echo -e "4. Configure for Claude Code:"
echo -e "   ${CYAN}export BASH_ENV=$SCRIPT_DIR/.cc-env${RESET}"
echo -e "   ${YELLOW}(Add to your shell profile for persistence)${RESET}"
echo
echo -e "5. Customize your environment:"
echo -e "   ${CYAN}${EDITOR:-vim} $SCRIPT_DIR/profiles/global/bashrc${RESET}"
echo
echo -e "6. Sync dotfiles: ${CYAN}cc-isolate dotfiles sync${RESET}"
echo

echo -e "${BOLD}Documentation:${RESET}"
echo -e "  ${CYAN}$SCRIPT_DIR/README.md${RESET}"
echo

log_success "Happy coding with Claude Code! 🚀"
echo

#!/usr/bin/env bash
#
# cc-isolate Uninstallation Script
# Removes the Claude Code isolation system
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
    echo -e "${RED}${BOLD}╔═══════════════════════════════════════════════════╗${RESET}"
    echo -e "${RED}${BOLD}║${RESET}  ${CYAN}cc-isolate${RESET} Uninstallation                   ${RED}${BOLD}║${RESET}"
    echo -e "${RED}${BOLD}╚═══════════════════════════════════════════════════╝${RESET}"
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

print_header

log_warn "This will remove cc-isolate from your system."
echo
read -p "Are you sure you want to continue? [y/N] " -n 1 -r
echo
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

# Source platform detection
if [[ -f "$SCRIPT_DIR/lib/platform.sh" ]]; then
    source "$SCRIPT_DIR/lib/platform.sh"
fi

# Step 1: Unmount if currently mounted
if [[ -f "$SCRIPT_DIR/bin/cc-isolate" ]]; then
    log_info "Checking if isolation is mounted..."
    if "$SCRIPT_DIR/bin/cc-isolate" status 2>/dev/null | grep -q "Mounted:.*Yes"; then
        log_info "Unmounting isolation..."
        "$SCRIPT_DIR/bin/cc-isolate" unmount
        log_success "Unmounted"
    fi
fi

# Step 2: Remove symlink from /usr/local/bin
if [[ -L "/usr/local/bin/cc-isolate" ]]; then
    log_info "Removing symlink from /usr/local/bin..."
    if rm "/usr/local/bin/cc-isolate" 2>/dev/null; then
        log_success "Symlink removed"
    else
        log_info "Trying with sudo..."
        if sudo rm "/usr/local/bin/cc-isolate" 2>/dev/null; then
            log_success "Symlink removed (with sudo)"
        else
            log_warn "Failed to remove symlink. You may need to remove it manually."
        fi
    fi
fi

# Step 3: Remove generated files
log_info "Removing generated files..."

files_to_remove=(
    "$SCRIPT_DIR/.cc-env"
    "$SCRIPT_DIR/.state"
)

for file in "${files_to_remove[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        log_success "Removed: $(basename "$file")"
    fi
done

# Step 4: Restore system bashrc if backed up
if [[ -f "$SCRIPT_DIR/system-backup/bashrc.backup" ]]; then
    log_warn "System bashrc backup found: $SCRIPT_DIR/system-backup/bashrc.backup"
    log_info "This has NOT been automatically restored."
    log_info "If you need to restore it, you can find it at the location above."
fi

# Step 5: Clean up dotfile symlinks
log_info "Checking for dotfile symlinks..."
symlink_count=0

if [[ -d "$SCRIPT_DIR/dotfiles" ]]; then
    for dotfile_path in "$SCRIPT_DIR/dotfiles"/.*; do
        dotfile=$(basename "$dotfile_path")
        [[ "$dotfile" == "." || "$dotfile" == ".." ]] && continue

        home_file="$HOME/$dotfile"

        if [[ -L "$home_file" ]] && [[ "$(readlink "$home_file")" == "$dotfile_path" ]]; then
            log_warn "Found symlink: $home_file -> $dotfile_path"
            read -p "Remove this symlink? [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm "$home_file"
                log_success "Removed symlink: $dotfile"
                ((symlink_count++))
            fi
        fi
    done
fi

if [[ $symlink_count -eq 0 ]]; then
    log_info "No dotfile symlinks found"
fi

# Step 6: Check BASH_ENV
if [[ -n "${BASH_ENV:-}" ]] && [[ "$BASH_ENV" == "$SCRIPT_DIR/.cc-env" ]]; then
    log_warn "BASH_ENV is currently set to: $BASH_ENV"
    log_info "You should unset it by running: unset BASH_ENV"
    log_info "Also remove it from your shell profile (~/.bashrc or ~/.bash_profile)"
fi

echo
echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║${RESET}  Uninstallation Complete                      ${GREEN}${BOLD}║${RESET}"
echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════╝${RESET}"
echo

log_info "The following items were NOT removed:"
echo -e "  ${CYAN}•${RESET} Configuration files (config.sh)"
echo -e "  ${CYAN}•${RESET} Profiles (profiles/)"
echo -e "  ${CYAN}•${RESET} Dotfiles (dotfiles/)"
echo -e "  ${CYAN}•${RESET} System bashrc backup (system-backup/)"
echo

log_info "To completely remove cc-isolate, delete this directory:"
echo -e "  ${CYAN}rm -rf $SCRIPT_DIR${RESET}"
echo

log_info "Don't forget to:"
echo -e "  ${CYAN}1.${RESET} Unset BASH_ENV if you set it"
echo -e "  ${CYAN}2.${RESET} Remove BASH_ENV export from your shell profile"
echo -e "  ${CYAN}3.${RESET} Remove PATH addition if you added $SCRIPT_DIR/bin to PATH"
echo

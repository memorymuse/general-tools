#!/bin/bash
# Setup script for dotfiles on new machine

set -e

echo "=== Dotfiles Setup ==="

# Backup existing files
backup_if_exists() {
    if [ -f "$1" ]; then
        echo "Backing up existing $1 to $1.backup"
        cp "$1" "$1.backup.$(date +%Y%m%d-%H%M%S)"
    fi
}

# Setup .claude directory
echo "Setting up ~/.claude..."
mkdir -p ~/.claude/output-styles
backup_if_exists ~/.claude/CLAUDE.md
backup_if_exists ~/.claude/settings.json

cp claude/CLAUDE.md ~/.claude/
cp claude/settings.json ~/.claude/
cp claude/output-styles/dense.md ~/.claude/output-styles/

echo "✓ ~/.claude/ configured"

# Add bashrc aliases
echo ""
echo "Setting up bash aliases..."
backup_if_exists ~/.bashrc

# Extract custom aliases from dotfiles/bashrc
echo "" >> ~/.bashrc
echo "# Custom aliases from dotfiles ($(date +%Y-%m-%d))" >> ~/.bashrc
grep -E "^alias (filedet|backup-health|db-query|mdhist)" bashrc >> ~/.bashrc || true

echo "✓ Bash aliases added"

# Install direnv if not present
echo ""
if ! command -v direnv &> /dev/null; then
    echo "direnv not found. Install it:"
    echo "  Ubuntu/Debian: sudo apt install direnv"
    echo "  macOS: brew install direnv"
    echo ""
    echo "Then add to ~/.bashrc or ~/.zshrc:"
    echo '  eval "$(direnv hook bash)"  # or zsh'
else
    echo "✓ direnv already installed"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Add API keys to ~/.claude/settings.json (see env-templates/README.md)"
echo "2. Clone muse-v1: git clone https://github.com/memorymuse/muse-v1.git ~/projects/muse-v1"
echo "3. Setup direnv hook in ~/.bashrc if not already done"
echo "4. Reload shell: source ~/.bashrc"

# cc-isolate 🛡️

**Claude Code Isolation System** - Portable, cross-platform environment isolation for Claude Code with intelligent bashrc layering, dotfile synchronization, and integrated secret scanning.

---

## 🚀 Quick Reference

### Installation
```bash
cd env-sync
./install.sh
```

### Essential Commands
```bash
# Mount isolation (activate CC environment)
cc-isolate mount              # Use global profile
cc-isolate mount my-project   # Use specific profile

# Unmount isolation (deactivate)
cc-isolate unmount

# Check status
cc-isolate status

# Sync dotfiles locally (create symlinks)
cc-isolate dotfiles sync

# Git sync - Push/Pull to GitHub (with secret scanning!)
cc-isolate dotfiles push      # Push dotfiles to GitHub
cc-isolate sync pull          # Pull everything from GitHub
cc-isolate sync status        # Check what needs to be pushed

# Secret scanning
cc-isolate secrets scan       # Scan for secrets
cc-isolate secrets template   # Create template from file with secrets
```

### Activate in Current Shell
```bash
# One-time activation
source /path/to/env-sync/.cc-env

# Persistent activation (add to ~/.bashrc or ~/.bash_profile)
export BASH_ENV=/path/to/env-sync/.cc-env
```

### Common Workflows

**First-time setup:**
```bash
cd env-sync && ./install.sh
cc-isolate mount
export BASH_ENV=$PWD/.cc-env
```

**Sync environment to new machine:**
```bash
git clone <repo-url>
cd general-tools/env-sync
./install.sh
cc-isolate sync pull         # Pull and sync everything
cc-isolate mount
```

**Push changes to GitHub:**
```bash
# Edit your dotfiles
vim ~/.gitconfig

# Push just dotfiles
cc-isolate dotfiles push "Update gitconfig"

# Or push everything (dotfiles + profiles + config)
cc-isolate sync push "Update environment"
```

**Create project-specific profile:**
```bash
cc-isolate profile create web-dev
vim env-sync/profiles/web-dev/bashrc
cc-isolate mount web-dev
```

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
  - [Mounting & Unmounting](#mounting--unmounting)
  - [Profiles](#profiles)
  - [Dotfile Management](#dotfile-management)
  - [Git Synchronization](#git-synchronization)
  - [Configuration](#configuration)
- [Cross-Platform Support](#cross-platform-support)
- [Secret Scanning & Protection](#secret-scanning--protection)
- [Security & Isolation](#security--isolation)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

`cc-isolate` is a comprehensive environment isolation system designed specifically for Claude Code usage, with a focus on:

1. **Safety**: Protects your system bashrc from accidental modifications
2. **Portability**: Syncs seamlessly between macOS, Linux, and WSL via GitHub
3. **Flexibility**: Supports global and project-specific environments
4. **Layering**: Intelligently combines system bashrc with custom settings
5. **Security**: Leverages OS-level file protection mechanisms

### Why cc-isolate?

When running Claude Code with `dangerously-skip-permissions` mode (especially on macOS where it has broader system access), you need:

- **Isolation boundaries** between CC's environment and your system
- **Consistent dev environments** across multiple machines (desktop + laptop)
- **Protection** for your system configuration files
- **Easy synchronization** via GitHub
- **Flexible customization** for different projects

cc-isolate solves all of these problems elegantly.

---

## Features

### 🔒 Bashrc Isolation & Layering

- **Dual-layer architecture**: System bashrc sources first, then custom CC bashrc
- **Override priority**: Custom settings override system settings on conflicts
- **Read-only protection**: Optional immutable flag on system bashrc (via `chattr` on Linux, `chflags` on macOS)
- **No system file modification**: Your system bashrc stays pristine

### 👥 Profile System

- **Global profile**: Default environment for all CC sessions
- **Project profiles**: Custom environments for specific projects/workflows
- **Easy switching**: `cc-isolate mount <profile-name>`
- **Isolated configurations**: Each profile has its own bashrc, aliases, environment variables

### 📦 Dotfile Synchronization

- **Configurable sync modes**:
  - `list`: Sync specific dotfiles (e.g., `.gitconfig`, `.vimrc`)
  - `all`: Sync all dotfiles in the repository
  - `none`: Disable dotfile sync
- **Symlink management**: Automatic symlinking between repo and home directory
- **Conflict detection**: Warns about conflicts between repo and local files
- **GitHub-based sync**: Commit and push changes to sync across machines

### 🔐 Secret Scanning & Protection

- **Automatic scanning**: Pre-push secret detection using GitLeaks (160+ patterns)
- **100% local**: No API calls, no cloud services, all scanning happens on your machine
- **Template generation**: Auto-creates template files with `YOUR_*_HERE` placeholders
- **Blocked file types**: Prevents accidental commit of `.pem`, `.key`, `.env`, SSH keys, etc.
- **Whitelist support**: Manage false positives easily
- **Configurable**: Enable/disable, auto-install GitLeaks, auto-generate templates

### 🌍 Cross-Platform Support

- **Linux**: Full support (native and WSL)
- **macOS**: Full support
- **WSL Ubuntu**: Full support with Windows integration
- **Platform detection**: Automatic detection and adaptation
- **Portable scripts**: Same commands work everywhere

### 🔧 Advanced Features

- **Mount/unmount**: Easy activation/deactivation of isolation
- **Status monitoring**: Check current state, active profile, configuration
- **BASH_ENV integration**: Automatic sourcing for CC sessions
- **Safe defaults**: Interactive confirmations, command aliases
- **Visual indicators**: `[CC]` prefix in prompt when isolated

---

## Architecture

### Directory Structure

```
env-sync/
├── bin/
│   └── cc-isolate              # Main command-line tool
├── lib/
│   └── platform.sh             # Cross-platform compatibility layer
├── profiles/
│   ├── global/
│   │   ├── bashrc              # Global CC bashrc (overrides system)
│   │   └── README.md
│   └── projects/
│       └── example/
│           └── bashrc          # Example project-specific bashrc
├── dotfiles/
│   ├── .gitconfig.example      # Example dotfiles for reference
│   └── ...                     # Your synced dotfiles go here
├── bashrc.d/
│   └── *.sh                    # Additional bash snippets (optional)
├── system-backup/
│   └── bashrc.backup           # Backup of system bashrc
├── .cc-env                     # Generated environment file (when mounted)
├── .state                      # Current state tracking
├── config.sh                   # Configuration file
├── install.sh                  # Installation script
├── uninstall.sh                # Uninstallation script
└── README.md                   # This file
```

### How It Works

1. **Mounting**: When you run `cc-isolate mount`:
   - Backs up your system bashrc (if not already backed up)
   - Optionally protects system bashrc with immutable flag
   - Creates `.cc-env` file that sources:
     - System bashrc (read-only)
     - Profile-specific bashrc (your customizations)
     - Additional snippets from `bashrc.d/`

2. **Layering**: The `.cc-env` file sources files in this order:
   ```bash
   1. System bashrc (/home/user/.bashrc)
   2. Profile bashrc (profiles/<profile>/bashrc)
   3. Snippets (bashrc.d/*.sh)
   ```
   Later settings override earlier ones.

3. **Activation**: Set `BASH_ENV` to point to `.cc-env`:
   ```bash
   export BASH_ENV=/path/to/env-sync/.cc-env
   ```
   Now all bash sessions (including CC) will source this environment.

4. **Protection**: System bashrc is protected with:
   - **Linux/WSL**: `chattr +i` (immutable flag)
   - **macOS**: `chflags uchg` (user immutable flag)
   - Result: File cannot be modified/deleted without removing the flag

---

## Installation

### Prerequisites

- Bash 4.0 or later
- Git
- sudo access (for file protection features)

### Install

```bash
# Clone the repository (or pull latest changes)
git clone <your-repo-url>
cd general-tools/env-sync

# Run installation
./install.sh
```

The installer will:
- Make `cc-isolate` executable
- Create symlink in `/usr/local/bin` (if possible)
- Create default configuration file
- Set up global profile with safe defaults
- Create example files and documentation

### Verify Installation

```bash
cc-isolate --version
cc-isolate status
```

---

## Usage

### Mounting & Unmounting

#### Mount Isolation

Activate the CC isolated environment:

```bash
# Use global profile
cc-isolate mount

# Use specific profile
cc-isolate mount my-project
```

This creates `.cc-env` and optionally protects your system bashrc.

#### Activate in Current Shell

To use the isolated environment in your current shell:

```bash
source /path/to/env-sync/.cc-env
```

#### Activate for Claude Code

To make Claude Code automatically use the isolated environment:

```bash
# Set BASH_ENV to point to .cc-env
export BASH_ENV=/path/to/env-sync/.cc-env

# Add to your shell profile for persistence
echo 'export BASH_ENV=/path/to/env-sync/.cc-env' >> ~/.bashrc
```

Now all bash sessions (including those started by Claude Code) will use the isolated environment.

#### Unmount Isolation

Deactivate the isolation:

```bash
cc-isolate unmount
```

This removes `.cc-env` and unprotects the system bashrc.

Don't forget to unset `BASH_ENV`:

```bash
unset BASH_ENV
# Remove from ~/.bashrc if you added it there
```

### Profiles

Profiles allow you to maintain different environments for different use cases.

#### List Profiles

```bash
cc-isolate profile list
```

Output:
```
Available Profiles:

● global (active)
  web-dev
  data-science
  projects/my-app
```

#### Create a New Profile

```bash
cc-isolate profile create web-dev
```

This creates `profiles/web-dev/bashrc` with a template. Edit it:

```bash
vim profiles/web-dev/bashrc
```

Example customizations:

```bash
# Web development profile

# Node.js environment
export NODE_ENV=development
export PATH="$HOME/.nvm/versions/node/v18.0.0/bin:$PATH"

# Aliases
alias dev='npm run dev'
alias build='npm run build'
alias test='npm test'

# Custom prompt
PS1='\[\033[01;32m\][WEB]\[\033[00m\] \[\033[01;34m\]\w\[\033[00m\]\$ '
```

#### Switch Profiles

```bash
cc-isolate mount web-dev
```

#### Delete a Profile

```bash
cc-isolate profile delete web-dev
```

### Dotfile Management

Manage your dotfiles across machines.

#### Configure Sync Mode

Edit `config.sh`:

```bash
# Sync specific files
DOTFILE_SYNC_MODE="list"
DOTFILES_TO_SYNC=".gitconfig .vimrc .tmux.conf .zshrc"

# Or sync everything in dotfiles/
DOTFILE_SYNC_MODE="all"

# Or disable sync
DOTFILE_SYNC_MODE="none"
```

#### Sync Dotfiles

```bash
cc-isolate dotfiles sync
```

This will:
- Import dotfiles from `~` to `dotfiles/` if they don't exist in repo
- Create symlinks from `~` to `dotfiles/` for dotfiles in repo
- Detect conflicts and warn you

#### List Managed Dotfiles

```bash
cc-isolate dotfiles list
```

Output:
```
Managed Dotfiles:

  ● .gitconfig (linked)
  ● .vimrc (linked)
  ○ .tmux.conf (not linked)
  ○ .bashrc (conflict)
```

#### Workflow for Syncing Across Machines

**On Machine 1 (initial setup):**
```bash
# Configure which dotfiles to sync
vim config.sh

# Sync dotfiles locally (creates symlinks)
cc-isolate dotfiles sync

# Push to GitHub
cc-isolate dotfiles push "Initial dotfiles"
```

**On Machine 2 (new machine):**
```bash
# Pull from GitHub
cc-isolate dotfiles pull

# Or pull everything (dotfiles + profiles + config)
cc-isolate sync pull
```

Your dotfiles are now synced! Changes on either machine can be pushed/pulled with cc-isolate commands.

### Git Synchronization

cc-isolate includes integrated Git commands for seamless synchronization across machines. All sync commands operate on the **same exact files** (dotfiles/, profiles/, bashrc.d/, config.sh) to ensure consistency.

#### Push Dotfiles Only

```bash
# Edit a dotfile (changes auto-save to repo via symlinks)
vim ~/.gitconfig

# Push just dotfiles to GitHub
cc-isolate dotfiles push
cc-isolate dotfiles push "Update gitconfig"
```

This commits and pushes only files in `dotfiles/`.

#### Pull Dotfiles Only

```bash
# Pull and re-sync dotfiles from GitHub
cc-isolate dotfiles pull
```

This pulls changes and automatically re-creates symlinks.

#### Push Everything

```bash
# Edit profile or config
vim profiles/global/bashrc
vim config.sh

# Push all changes (dotfiles + profiles + config)
cc-isolate sync push
cc-isolate sync push "Update environment settings"
```

This commits and pushes changes in:
- `dotfiles/`
- `profiles/`
- `bashrc.d/`
- `config.sh`

#### Pull Everything

```bash
# Pull all changes from GitHub
cc-isolate sync pull
```

This pulls and automatically:
- Re-syncs dotfiles (creates symlinks)
- Reloads configuration
- Suggests remounting if currently mounted

#### Check Sync Status

```bash
# See what needs to be pushed
cc-isolate sync status
```

Output:
```
Git Repository Status:

  Branch:         main
  Remote:         https://github.com/user/repo.git
  Last commit:    abc1234 - Update gitconfig (2 hours ago)

Pending Changes:

  M  dotfiles/.gitconfig
  M  profiles/global/bashrc
  ?  dotfiles/.vimrc

ℹ To push changes: cc-isolate sync push
```

#### Conflict Handling

If you have uncommitted changes when pulling, cc-isolate will:
1. Warn you about uncommitted changes
2. Offer to stash them automatically
3. Pull the changes
4. You can restore stashed changes with `git stash pop`

```bash
$ cc-isolate sync pull
⚠ You have uncommitted changes
Stash changes and pull? [y/N] y
ℹ Stashing changes...
✓ Changes stashed
ℹ Pulling from remote...
✓ Pulled from remote
```

#### Complete Workflow Between Machines

**Machine 1 (edit and push):**
```bash
# Make changes
vim ~/.gitconfig
vim profiles/global/bashrc

# Check status
cc-isolate sync status

# Push to GitHub
cc-isolate sync push "Update config and profile"
```

**Machine 2 (pull and apply):**
```bash
# Pull changes
cc-isolate sync pull

# If mounted, remount to apply changes
cc-isolate unmount
cc-isolate mount
```

### Configuration

#### View Current Configuration

```bash
cc-isolate config
```

#### Edit Configuration

```bash
vim config.sh
```

#### Configuration Options

```bash
# System bashrc location (auto-detected by default)
SYSTEM_BASHRC="$HOME/.bashrc"

# Protect system bashrc with immutable flag when mounted
PROTECT_SYSTEM_BASHRC=true

# Dotfile sync mode: "all", "list", or "none"
DOTFILE_SYNC_MODE="list"

# List of dotfiles to sync (only used when DOTFILE_SYNC_MODE="list")
DOTFILES_TO_SYNC=".gitconfig .vimrc .tmux.conf"
```

---

## Cross-Platform Support

### Platform-Specific Behavior

| Feature | Linux | macOS | WSL |
|---------|-------|-------|-----|
| File protection | `chattr +i` | `chflags uchg` | `chattr +i` |
| System bashrc | `~/.bashrc` | `~/.bash_profile` or `~/.bashrc` | `~/.bashrc` |
| Symlinks | Full support | Full support | Full support |
| Auto-detection | ✓ | ✓ | ✓ (detects WSL) |

### Platform Detection

The system automatically detects your platform and adapts:

```bash
# Check detected platform
cc-isolate status
```

Output includes:
```
Platform: WSL (Windows Subsystem for Linux)
```

### WSL-Specific Features

- Detects WSL environment automatically
- Works with WSL Ubuntu, Debian, etc.
- Isolates CC from Windows system (better security boundary)

### macOS-Specific Considerations

- On macOS, the system "bashrc" may be `~/.bash_profile`
- `chflags uchg` provides file protection
- Works with both Intel and Apple Silicon Macs

---

## Secret Scanning & Protection

cc-isolate includes **integrated secret scanning** to prevent accidental leakage of sensitive information to GitHub. This is critical when syncing dotfiles that may contain API keys, tokens, or credentials.

### How It Works

**Automatic Scanning**: Every push command (`dotfiles push` and `sync push`) automatically scans files for secrets **before** committing.

**GitLeaks Integration**: Uses [GitLeaks](https://github.com/gitleaks/gitleaks), the industry-standard open-source secret scanner with 160+ built-in secret patterns.

**Template Generation**: When secrets are detected, cc-isolate can automatically create template files with secrets replaced by placeholders.

**Local-Only**: All scanning happens **100% locally** - no API calls, no cloud services, no data leaves your machine.

### Installation

Install GitLeaks for secret scanning to work:

```bash
# macOS
brew install gitleaks

# Go
go install github.com/gitleaks/gitleaks/v8@latest

# Or download binary from:
# https://github.com/gitleaks/gitleaks/releases
```

cc-isolate can auto-install via Homebrew or Go if `SECRET_SCAN_AUTO_INSTALL=true`.

### Template Placeholders

Secrets are replaced with the pattern: `YOUR_<SECRET_NAME>_HERE`

**Examples:**
- `YOUR_API_KEY_HERE`
- `YOUR_AWS_ACCESS_KEY_ID_HERE`
- `YOUR_DATABASE_PASSWORD_HERE`
- `YOUR_GITHUB_TOKEN_HERE`

This pattern makes it easy to:
1. Identify template files that need values filled in
2. Scan for unconverted placeholders: `cc-isolate secrets check`
3. Search across systems: `grep -r "YOUR_.*_HERE"`

### Usage Examples

#### Scan Before Push

```bash
# Scan specific directory
cc-isolate secrets scan dotfiles

# Scan specific file
cc-isolate secrets scan dotfiles/.gitconfig
```

#### Auto-Scan During Push

```bash
# This automatically scans before pushing
cc-isolate dotfiles push "Update config"

# If secrets found:
# ✗ dotfiles/.gitconfig (secrets detected)
#
# Options:
#   1. Remove secrets from files
#   2. Use template files (*.template)
#   3. Whitelist false positives
#   4. Skip scan (DANGEROUS)
#
# ✗ Push blocked due to detected secrets
```

#### Template Generation

When secrets are detected, templates are auto-created:

```bash
# Original file: dotfiles/.gitconfig
[github]
    token = ghp_abc123xyz789...

# Auto-generated: dotfiles/.gitconfig.template
[github]
    token = YOUR_GITHUB_TOKEN_HERE
```

**Workflow:**
1. Add original to `.gitignore`
2. Commit template instead
3. On new machine, copy template and fill in values

Manual template creation:

```bash
cc-isolate secrets template dotfiles/.npmrc
# Creates dotfiles/.npmrc.template
```

#### Whitelist False Positives

Sometimes legitimate values trigger detection:

```bash
# Whitelist a file
cc-isolate secrets whitelist dotfiles/.gitconfig

# View whitelist
cc-isolate secrets whitelist
```

#### Check for Unconverted Placeholders

Ensure you've replaced all `YOUR_*_HERE` values:

```bash
cc-isolate secrets check dotfiles

# Or check everything
cc-isolate secrets check .
```

### What Gets Detected

**Built-in patterns (160+):**
- AWS keys and secrets
- GitHub tokens (classic, PAT, OAuth)
- Private keys (RSA, SSH, PGP)
- Database connection strings
- API keys (Slack, Stripe, etc.)
- JWT tokens
- Docker registry auth
- NPM tokens
- Shell exports with secrets

**Blocked file types:**
- `.pem`, `.key`, `.p12`, `.pfx` (certificates)
- `.env*` files (environment variables)
- `id_rsa`, `id_dsa`, `id_ecdsa` (SSH keys)
- `credentials`, `credentials.json` (cloud credentials)

See `.gitleaks.toml` for full configuration.

### Configuration

In `config.sh`:

```bash
# Enable secret scanning (RECOMMENDED)
SECRET_SCAN_ENABLED=true

# Block push when secrets detected (RECOMMENDED)
SECRET_BLOCK_PUSH=true

# Auto-create templates
SECRET_CREATE_TEMPLATES=true

# Auto-install gitleaks if missing
SECRET_SCAN_AUTO_INSTALL=true
```

### Bypass Scanning (Use Carefully!)

```bash
# Skip scan for this push (DANGEROUS)
cc-isolate dotfiles push --no-scan "message"
cc-isolate sync push --no-scan "message"
```

⚠️ **Warning**: Only use `--no-scan` if you're absolutely certain the files are safe.

### Best Practices

1. **Whitelist-Only Dotfiles**: Only sync files that never contain secrets:
   ```bash
   DOTFILES_TO_SYNC=".bash_aliases .inputrc .editorconfig"
   ```

2. **Use Templates**: For configs that need secrets, use template files:
   ```bash
   # Commit: .gitconfig.template (with placeholders)
   # Keep local: .gitconfig (with real values)
   # .gitignore: .gitconfig
   ```

3. **Environment Variables**: Store secrets in `.env.local` (gitignored):
   ```bash
   # profiles/global/bashrc
   if [[ -f "$HOME/.env.local" ]]; then
       source "$HOME/.env.local"
   fi
   ```

4. **Cloud Secret Managers**: For sensitive production use:
   - [1Password CLI](https://developer.1password.com/docs/cli/)
   - [Bitwarden CLI](https://bitwarden.com/help/cli/)
   - [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
   - [HashiCorp Vault](https://www.vaultproject.io/)

5. **Regular Scans**: Periodically scan everything:
   ```bash
   cc-isolate secrets scan .
   ```

### Troubleshooting

**"GitLeaks not found"**
```bash
# Install via Homebrew
brew install gitleaks

# Or disable scanning
SECRET_SCAN_ENABLED=false  # in config.sh
```

**False positives**
```bash
# Whitelist the file
cc-isolate secrets whitelist path/to/file
```

**Push blocked unexpectedly**
```bash
# See what was detected
cc-isolate secrets scan dotfiles

# If false positive, whitelist
# If real secret, remove or use template
```

---

## Security & Isolation

### Isolation Layers

1. **Filesystem Isolation**:
   - Claude Code Sandbox mode restricts filesystem access
   - cc-isolate adds logical separation of system vs CC environment

2. **Bashrc Protection**:
   - System bashrc made immutable during mount
   - Prevents accidental modifications by CC or user
   - Unmount to regain write access

3. **Environment Separation**:
   - CC sessions use `.cc-env` instead of system bashrc
   - Clear visual indicator (`[CC]` in prompt)
   - `CC_ISOLATE_ACTIVE` environment variable set

### Security Best Practices

1. **Always use CC Sandbox mode** when possible
2. **Run WSL for maximum isolation** on Windows (dedicated Linux environment)
3. **Enable system bashrc protection** (`PROTECT_SYSTEM_BASHRC=true`)
4. **Review profile bashrc** before mounting
5. **Use project-specific profiles** for different security contexts
6. **Regularly audit** your isolation setup:
   ```bash
   cc-isolate status
   ```

### Threat Model

cc-isolate protects against:

- ✅ Accidental modification of system bashrc by CC
- ✅ Configuration drift between machines
- ✅ Confusion between system and CC environments
- ✅ Mistakes when running `dangerously-skip-permissions`

cc-isolate does NOT protect against:

- ❌ Malicious code execution (use CC Sandbox mode for this)
- ❌ Network-based attacks (use CC network isolation)
- ❌ Root-level compromises

**Important**: cc-isolate is a convenience and safety layer, not a security boundary. Always use Claude Code's built-in Sandbox mode for security isolation.

---

## Advanced Usage

### Custom Bashrc Snippets

Add reusable bash snippets to `bashrc.d/`:

```bash
# Create a snippet for Docker aliases
cat > bashrc.d/docker.sh << 'EOF'
#!/usr/bin/env bash
# Docker aliases

alias dps='docker ps'
alias dimg='docker images'
alias dexec='docker exec -it'
alias dlog='docker logs -f'
EOF
```

These are automatically sourced when isolation is mounted.

### Project-Specific Profiles

Create profiles under `profiles/projects/`:

```bash
mkdir -p profiles/projects/my-web-app
cat > profiles/projects/my-web-app/bashrc << 'EOF'
#!/usr/bin/env bash
# My Web App Profile

export PROJECT_ROOT="$HOME/projects/my-web-app"
export NODE_ENV=development

alias serve='cd $PROJECT_ROOT && npm start'
alias deploy='cd $PROJECT_ROOT && ./deploy.sh'

# Auto-cd to project
cd "$PROJECT_ROOT" 2>/dev/null || true
EOF

cc-isolate mount projects/my-web-app
```

### Conditional Configuration

Use platform detection in your bashrc:

```bash
# In profiles/global/bashrc

# Source platform library
source /path/to/env-sync/lib/platform.sh

if is_macos; then
    # macOS-specific settings
    export HOMEBREW_PREFIX="/opt/homebrew"
    export PATH="$HOMEBREW_PREFIX/bin:$PATH"
elif is_wsl; then
    # WSL-specific settings
    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
elif is_linux; then
    # Native Linux settings
    export PATH="/snap/bin:$PATH"
fi
```

### Multiple Machine Profiles

Create machine-specific profiles:

```bash
# Desktop profile (powerful machine)
cc-isolate profile create desktop
cat > profiles/desktop/bashrc << 'EOF'
export PARALLEL_JOBS=16
export DOCKER_MEMORY=8G
EOF

# Laptop profile (resource-constrained)
cc-isolate profile create laptop
cat > profiles/laptop/bashrc << 'EOF'
export PARALLEL_JOBS=4
export DOCKER_MEMORY=2G
EOF
```

On each machine, mount the appropriate profile:

```bash
# On desktop
cc-isolate mount desktop

# On laptop
cc-isolate mount laptop
```

### Integration with Claude Code Hooks

Create a Claude Code session-start hook to auto-mount:

```bash
# In your Claude Code hooks configuration
session-start:
  - /path/to/env-sync/bin/cc-isolate mount global
```

---

## Troubleshooting

### Common Issues

#### "Permission denied" when protecting system bashrc

**Cause**: Need sudo for `chattr`/`chflags`

**Solution**:
```bash
# You'll be prompted for sudo password
cc-isolate mount
```

Or disable protection:
```bash
# In config.sh
PROTECT_SYSTEM_BASHRC=false
```

#### Changes to bashrc not taking effect

**Cause**: Shell not sourcing `.cc-env`

**Solution**:
```bash
# Manually source
source /path/to/env-sync/.cc-env

# Or set BASH_ENV
export BASH_ENV=/path/to/env-sync/.cc-env
```

#### "Already mounted" error

**Cause**: Isolation already active

**Solution**:
```bash
# Unmount first
cc-isolate unmount

# Then mount again
cc-isolate mount
```

#### Dotfile conflicts

**Cause**: File exists in both `~` and `dotfiles/`, not linked

**Solution**:
```bash
# Manually resolve
# Option 1: Keep home version
mv ~/dotfiles/.gitconfig ~/.gitconfig.backup
cc-isolate dotfiles sync

# Option 2: Use repo version
rm ~/.gitconfig
cc-isolate dotfiles sync
```

#### Can't modify system bashrc after mounting

**Cause**: Immutable flag is set (this is intentional!)

**Solution**:
```bash
# Unmount to regain write access
cc-isolate unmount

# Now you can edit
vim ~/.bashrc

# Remount when done
cc-isolate mount
```

### Debug Mode

Run with `set -x` for verbose output:

```bash
bash -x $(which cc-isolate) status
```

### Check State

```bash
# View internal state
cat /path/to/env-sync/.state

# Check if BASH_ENV is set
echo $BASH_ENV

# Check if CC isolation is active
echo $CC_ISOLATE_ACTIVE
```

---

## Uninstalling

```bash
cd env-sync

# Unmount if currently mounted
cc-isolate unmount

# Run uninstaller
./uninstall.sh

# Remove the repository
cd ..
rm -rf general-tools/env-sync
```

---

## FAQ

### Q: Do I need to commit `.cc-env` to Git?

**A**: No, it's generated locally. It's in `.gitignore`.

### Q: Can I use this without Claude Code?

**A**: Yes! It's a general-purpose bash environment manager. Just source `.cc-env` in your shell.

### Q: What if I use Zsh instead of Bash?

**A**: This is designed for Bash. For Zsh, you'd need to adapt the scripts and use `.zshrc` instead of `.bashrc`.

### Q: How do I sync environment variables between machines?

**A**: Add them to your profile bashrc, commit, and push:
```bash
# In profiles/global/bashrc
export MY_VAR=value

# Commit and push
git add profiles/global/bashrc
git commit -m "Add MY_VAR"
git push
```

### Q: Can I have different profiles on different machines?

**A**: Yes! The profile you mount is a local choice. Just mount different profiles on each machine.

### Q: What happens if I delete `.cc-env`?

**A**: Just remount: `cc-isolate mount`. It will be regenerated.

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on Linux, macOS, and WSL if possible
5. Submit a pull request

---

## License

MIT License - see LICENSE file for details

---

## Credits

Created to solve the problem of portable, safe Claude Code environments across multiple machines.

**Platforms tested:**
- ✅ Ubuntu 22.04 (WSL)
- ✅ Ubuntu 20.04 (native)
- ✅ macOS 13 Ventura
- ✅ macOS 14 Sonoma

---

## Changelog

### v1.0.0 (2025-11-14)

- Initial release
- Cross-platform support (Linux, macOS, WSL)
- Profile system (global + project-specific)
- Dotfile synchronization
- Bashrc layering with system override
- File protection via `chattr`/`chflags`
- Mount/unmount functionality
- Comprehensive documentation

---

**Happy isolating! 🛡️**

For issues or questions, please open an issue on GitHub.

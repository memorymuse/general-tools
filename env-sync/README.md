# devenv

**Cross-Machine Environment Synchronization** - Seamlessly sync your development environment between machines (macOS, WSL/Linux) with encrypted secrets, shell configurations, and tool management.

---

## Project Status & Vision

**Current State**: This README documents the existing implementation - a working system for syncing secrets, shell configs, Claude Code settings, and tools between machines.

**Expanded Vision**: The `docs/` directory contains planning for the next evolution of this tool:

- [`docs/VISION.md`](docs/VISION.md) - User-perspective narrative of the full problem and desired experience
- [`docs/PROBLEM-MODEL.md`](docs/PROBLEM-MODEL.md) - Comprehensive problem model for the expanded system

**Key gaps between current and vision**:
- **Auto-discovery**: Current system requires manual vault export; vision calls for automatic discovery of gitignored essentials across all projects
- **Validation**: Vision includes user validation workflow for discovered files
- **Conflict resolution**: Current system overwrites; vision includes smart conflict detection and resolution
- **Completeness verification**: Vision requires verified capture of ALL Claude Code config, not just a static list

The problem model is intended as the foundation for designing and implementing these expanded capabilities.

---

## What This Does

`devenv` solves the "new machine problem" - when you switch between your MacBook and Desktop (or any machines), you want:

- Same environment variables and secrets (API keys, tokens)
- Same shell aliases and functions
- Same CLI tools installed
- Same dotfiles (.gitconfig, .vimrc, etc.)

One command syncs everything: `devenv push` / `devenv pull`

---

## Quick Start

### First Machine (Setup)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd general-tools/env-sync

# 2. Install
./install.sh

# 3. Export your existing secrets
devenv vault export ~ ~/projects

# 4. Review and encrypt
vim secrets.yaml          # Review/edit
devenv vault encrypt      # Encrypts with password

# 5. Push to git
devenv push "Initial setup"
```

### Second Machine (Sync)

```bash
# 1. Clone and install
git clone <your-repo-url>
cd general-tools/env-sync
./install.sh

# 2. Pull everything
devenv pull               # Enter password, secrets deployed automatically

# 3. Install missing tools
devenv tools install
```

---

## Core Commands

### Unified Sync

| Command | Description |
|---------|-------------|
| `devenv push [message]` | Encrypt secrets + stage all changes + commit + push |
| `devenv pull` | Pull from git + decrypt secrets + deploy to local files |

These are the primary commands. One password prompt, then everything is automatic.

### Secrets Vault

| Command | Description |
|---------|-------------|
| `devenv vault init` | Create empty secrets.yaml template |
| `devenv vault export [dirs...]` | Scan directories for .env files, merge into secrets.yaml |
| `devenv vault encrypt` | Encrypt secrets.yaml → secrets.yaml.age (password-protected) |
| `devenv vault decrypt` | Decrypt secrets.yaml.age → secrets.yaml |
| `devenv vault deploy` | Deploy secrets to ~/.env.secrets and project .env files |
| `devenv vault edit` | Decrypt → open in $EDITOR → re-encrypt on save |

### Tools Management

| Command | Description |
|---------|-------------|
| `devenv tools check` | Show installed/missing tools for current platform |
| `devenv tools install` | Install all missing tools |
| `devenv tools list` | List all tools in manifest with platform support |

### Other Commands

| Command | Description |
|---------|-------------|
| `devenv status` | Show current state, platform, configuration |
| `devenv help` | Full command reference |

---

## How Secrets Work

### The Flow

```
Your .env files  →  secrets.yaml  →  secrets.yaml.age  →  Git
                    (plaintext)       (encrypted)

On pull:
Git  →  secrets.yaml.age  →  secrets.yaml  →  ~/.env.secrets + project .env files
        (encrypted)           (decrypted)     (deployed)
```

### Encryption

Uses [age](https://github.com/FiloSottile/age) with password-based encryption:
- Strong encryption (ChaCha20-Poly1305)
- No key management - just remember your password
- Standard `age -p` prompts for password on encrypt/decrypt

### Secrets YAML Format

```yaml
global:
  # Available everywhere via ~/.env.secrets
  GITHUB_TOKEN: "ghp_xxxxxxxxxxxx"
  VERCEL_TOKEN: "xxxxx"

projects:
  # Deployed to specific project directories
  "~/projects/my-app":
    DATABASE_URL: "postgres://user:pass@host:5432/db"
    API_KEY: "sk-xxxxx"

  "~/projects/another-app":
    STRIPE_KEY: "sk_test_xxxxx"
```

### Deployment Locations

| Type | Deployed To | How To Use |
|------|-------------|------------|
| Global | `~/.env.secrets` | `source ~/.env.secrets` in shell profile |
| Project | `<project>/.env` | Loaded by most frameworks automatically |

The global bashrc already sources `~/.env.secrets` if it exists.

---

## Claude Code Config Sync

devenv automatically syncs your global Claude Code configuration between machines.

### What Gets Synced

| Item | Source | Destination |
|------|--------|-------------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | `dotfiles/claude/CLAUDE.md` |
| `commands/` | `~/.claude/commands/` | `dotfiles/claude/commands/` |
| `skills/` | `~/.claude/skills/` | `dotfiles/claude/skills/` |
| `settings.json` | `~/.claude/settings.json` | `dotfiles/claude/settings.json` |
| `output-styles/` | `~/.claude/output-styles/` | `dotfiles/claude/output-styles/` |

### What Does NOT Sync (machine-specific)

- `history.jsonl` - Conversation history
- `todos/`, `plans/`, `debug/` - Transient working data
- `projects/` - Machine-specific project data
- `file-history/`, `shell-snapshots/` - Local state
- `statsig/`, `telemetry/` - Analytics

### Push/Pull Flow

**On push (`devenv push`):**
1. Copies syncable items from `~/.claude/` → `dotfiles/claude/`
2. Encrypts secrets
3. Commits and pushes everything

**On pull (`devenv pull`):**
1. Pulls from git
2. Deploys secrets
3. Copies `dotfiles/claude/` → `~/.claude/`
4. Syncs other dotfiles

### Project-Level Claude Configs

Project-level `.claude/` directories (inside each project) are NOT handled by devenv - they sync via each project's own git repository. devenv only handles the global `~/.claude/` directory.

---

## Tools Manifest

The `tools.yaml` file defines required CLI tools with platform-specific install methods:

```yaml
tools:
  claude:
    description: "Claude Code CLI"
    macos: true
    wsl: true
    check: "claude --version"
    install:
      npm: "@anthropic-ai/claude-code"

  surreal:
    description: "SurrealDB CLI"
    macos: true
    wsl: true
    check: "surreal version"
    install:
      brew: "surrealdb/tap/surreal"
      script: "curl -sSf https://install.surrealdb.com | sh"
```

Run `devenv tools check` to see what's missing, `devenv tools install` to install them.

---

## Shell Configuration

### Global Bashrc

Located at `profiles/global/bashrc`, this file is sourced for all shells and includes:

- Platform detection (macOS, Linux, WSL)
- PATH configuration (Homebrew, cargo, go, etc.)
- History settings
- Common aliases (ls, grep, git shortcuts)
- Useful functions (mkcd, extract, etc.)
- Sources `~/.env.secrets` if present

### Zsh Compatibility

The bashrc is compatible with both bash and zsh. Add to your `~/.zshrc`:

```bash
source ~/path/to/env-sync/profiles/global/bashrc
```

### Project Profiles

Create project-specific profiles for different workflows:

```bash
devenv profile create web-dev
vim profiles/web-dev/bashrc
devenv mount web-dev
```

---

## Directory Structure

devenv uses two directories that work together:

```
general-tools/
├── dotfiles/                   # Storage - all syncable configs
│   ├── claude/                 # Claude Code configs (synced to ~/.claude/)
│   │   ├── CLAUDE.md           # Global agent instructions
│   │   ├── commands/           # Custom slash commands
│   │   ├── skills/             # User-level skills
│   │   ├── settings.json       # Claude Code preferences
│   │   └── output-styles/      # Custom output styles
│   ├── bashrc                  # Shell configuration
│   ├── env-templates/          # Environment variable templates
│   └── setup.sh                # One-time setup script
│
└── env-sync/                   # Mechanism - sync tooling
    ├── bin/
    │   ├── cc-isolate          # Main CLI
    │   └── devenv -> cc-isolate
    ├── lib/
    │   ├── platform.sh         # Platform detection
    │   ├── secrets.sh          # GitLeaks secret scanning
    │   └── secrets-sync.sh     # Age encryption library
    ├── profiles/
    │   └── global/
    │       └── bashrc          # Global shell config
    ├── tools.yaml              # Tools manifest
    ├── secrets.yaml.age        # Encrypted secrets
    └── config.sh               # Configuration
```

### What Gets Synced via Git

| Path | Description |
|------|-------------|
| `dotfiles/claude/` | Claude Code configs (CLAUDE.md, commands/, skills/, settings.json) |
| `dotfiles/bashrc` | Shell configuration |
| `env-sync/profiles/` | Shell profiles |
| `env-sync/tools.yaml` | Tools manifest |
| `env-sync/secrets.yaml.age` | Encrypted secrets |
| `env-sync/config.sh` | Configuration |

### What Stays Local (gitignored)

| Path | Description |
|------|-------------|
| `secrets.yaml` | Plaintext secrets (deleted after encrypt) |
| `.state` | Mount state |
| `.cc-env` | Generated environment file |
| `~/.claude/history.jsonl` | Conversation history |
| `~/.claude/todos/`, `plans/`, `debug/` | Transient data |

---

## Cross-Platform Support

### Platform Detection

The system auto-detects:
- **macOS** - Apple Silicon and Intel
- **Linux** - Native Linux
- **WSL** - Windows Subsystem for Linux

### Platform-Specific Behavior

| Feature | macOS | Linux/WSL |
|---------|-------|-----------|
| Package manager | Homebrew | apt-get + Homebrew |
| File protection | `chflags uchg` | `chattr +i` |
| Default shell | zsh | bash |

### Tools Installation

Tools manifest specifies install methods per platform:
- `brew:` - Homebrew (macOS primary, Linux fallback)
- `apt:` - apt-get (Linux/WSL)
- `npm:` - npm global install
- `script:` - Custom install script

---

## Workflow Examples

### Daily Workflow

```bash
# On MacBook - end of day
devenv push "Updated API keys"

# On Desktop - start of day
devenv pull
```

### Adding New Secrets

```bash
# Edit secrets
devenv vault edit

# Add your new secrets, save and close
# Automatically re-encrypts

# Push to sync
devenv push "Added Stripe keys"
```

### New Tool Needed

```bash
# Add to tools.yaml
vim tools.yaml

# Install it
devenv tools install

# Push for other machines
devenv push "Added new-tool"
```

### Setting Up a New Machine

```bash
# Clone repo
git clone <repo> && cd general-tools/env-sync

# Install devenv
./install.sh

# Pull everything
devenv pull

# Install tools
devenv tools install

# Verify
devenv status
devenv tools check
```

---

## Configuration

Edit `config.sh` for customization:

```bash
# Protect system bashrc with immutable flag when mounted
PROTECT_SYSTEM_BASHRC=true

# Dotfile sync mode: "all", "list", or "none"
DOTFILE_SYNC_MODE="list"
DOTFILES_TO_SYNC=".gitconfig .vimrc"

# Secret scanning (uses GitLeaks)
SECRET_SCAN_ENABLED=true
SECRET_BLOCK_PUSH=true
```

---

## Security

### Secrets

- **Encryption**: age (ChaCha20-Poly1305) with password
- **Plaintext secrets.yaml**: Deleted after encryption
- **Deployed files**: `chmod 600` (owner read/write only)
- **Git tracking**: Only encrypted `.age` file is tracked

### Secret Scanning

Pre-push scanning uses GitLeaks to detect:
- API keys (AWS, GitHub, Stripe, etc.)
- Private keys (RSA, SSH, PGP)
- Database connection strings
- JWT tokens
- 160+ secret patterns

If secrets are detected in non-vault files, push is blocked.

### Best Practices

1. **Never commit secrets.yaml** - Only the encrypted .age file
2. **Use strong passwords** - The password protects all your secrets
3. **Same password on all machines** - Or you can't decrypt
4. **Review before push** - Check `devenv sync status`

---

## Troubleshooting

### "age: command not found"

```bash
# macOS
brew install age

# Linux/WSL
sudo apt install age
```

### "Decryption failed"

Wrong password. The password must match what was used to encrypt.

### "No secrets file found"

Run `devenv vault export ~` to scan for .env files, or `devenv vault init` for empty template.

### Git push fails

Check `devenv sync status` for uncommitted changes. Ensure you have push access to the remote.

### Tools install fails

Some tools require manual installation. Check the `install:` section in tools.yaml for alternatives.

---

## Command Reference

```
devenv <command> [options]

SYNC:
  push [msg]              Push EVERYTHING (configs + secrets) to git
  pull                    Pull EVERYTHING from git and deploy

VAULT:
  vault init              Create empty secrets.yaml template
  vault export [dirs...]  Export env files to secrets.yaml
  vault encrypt           Encrypt secrets.yaml -> secrets.yaml.age
  vault decrypt           Decrypt secrets.yaml.age -> secrets.yaml
  vault deploy            Deploy secrets to ~/.env.secrets and project .env
  vault edit              Edit secrets (decrypt -> editor -> re-encrypt)

TOOLS:
  tools check             Check which tools are installed/missing
  tools install           Install missing tools for current platform
  tools list              List all tools in manifest

PROFILES:
  mount [profile]         Mount isolation (default: global)
  unmount                 Unmount isolation
  profile list            List available profiles
  profile create <name>   Create a new profile
  profile delete <name>   Delete a profile

DOTFILES:
  dotfiles sync           Sync dotfiles locally (create symlinks)
  dotfiles list           List managed dotfiles
  dotfiles push [msg]     Commit and push dotfiles to GitHub
  dotfiles pull           Pull dotfiles from GitHub and re-sync

OTHER:
  status                  Show isolation status
  config                  Show current configuration
  help                    Show this help message
  version                 Show version
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `secrets.yaml` | Plaintext secrets (temporary, deleted after encrypt) |
| `secrets.yaml.age` | Encrypted secrets (git-tracked) |
| `~/.env.secrets` | Deployed global secrets |
| `<project>/.env` | Deployed project secrets |
| `tools.yaml` | Tools manifest |
| `profiles/global/bashrc` | Global shell configuration |
| `config.sh` | devenv configuration |

---

## Secret Scanning (GitLeaks)

Pre-push scanning detects secrets before they reach git. This uses [GitLeaks](https://github.com/gitleaks/gitleaks), an open-source secret scanner with 160+ patterns.

### How It Works

Every `devenv push` and `devenv dotfiles push` automatically scans files before committing:

```bash
$ devenv dotfiles push "Update config"
ℹ Scanning for secrets...
  ✓ dotfiles/.gitconfig
  ✓ dotfiles/.vimrc
  ✗ dotfiles/.npmrc (secrets detected)

✗ Push blocked due to detected secrets
```

### What Gets Detected

**Built-in patterns (160+):**
- AWS keys and secrets
- GitHub tokens (classic, PAT, OAuth)
- Private keys (RSA, SSH, PGP)
- Database connection strings
- API keys (Slack, Stripe, Twilio, etc.)
- JWT tokens
- NPM tokens
- Docker registry auth

**Blocked file types:**
- `.pem`, `.key`, `.p12`, `.pfx` (certificates)
- `.env*` files (use vault instead)
- `id_rsa`, `id_dsa`, `id_ecdsa` (SSH keys)
- `credentials`, `credentials.json`

### Manual Scanning

```bash
# Scan specific directory
devenv secrets scan dotfiles

# Scan specific file
devenv secrets scan dotfiles/.gitconfig

# Check for template placeholders that need values
devenv secrets check dotfiles
```

### Template Generation

When secrets are detected, templates can be auto-created:

```bash
# Original: dotfiles/.gitconfig
[github]
    token = ghp_abc123xyz789...

# Generated: dotfiles/.gitconfig.template
[github]
    token = YOUR_GITHUB_TOKEN_HERE
```

Create templates manually:

```bash
devenv secrets template dotfiles/.npmrc
```

### Whitelist False Positives

```bash
# Whitelist a file
devenv secrets whitelist dotfiles/.gitconfig

# View whitelist
devenv secrets whitelist
```

### Configuration

In `config.sh`:

```bash
# Enable secret scanning (default: true)
SECRET_SCAN_ENABLED=true

# Block push when secrets detected (default: true)
SECRET_BLOCK_PUSH=true

# Auto-create templates when secrets found
SECRET_CREATE_TEMPLATES=true

# Auto-install gitleaks if missing
SECRET_SCAN_AUTO_INSTALL=true
```

### Bypass Scanning

```bash
# Skip scan for this push (DANGEROUS)
devenv dotfiles push --no-scan "message"
devenv sync push --no-scan "message"
```

### Installing GitLeaks

```bash
# macOS
brew install gitleaks

# Go
go install github.com/gitleaks/gitleaks/v8@latest

# Or download binary from:
# https://github.com/gitleaks/gitleaks/releases
```

---

## 1Password Integration

The global bashrc includes optional 1Password CLI integration for seamless secret injection into CLI tools.

### Why 1Password?

**Templates for Structure, 1Password for Secrets:**
- Templates (with `YOUR_*_HERE` placeholders) define configuration structure → synced via git
- 1Password stores actual secret values → never touch git
- Shell plugin provides secrets at runtime → transparent to tools

**Benefits:**
- Secrets never stored in files or environment variables
- Works seamlessly with existing tools (git, aws, gh, etc.)
- Biometric authentication (Touch ID, Windows Hello)
- Zero changes to existing workflows

### Installation

#### 1. Install 1Password Desktop App

Download from [1password.com/downloads](https://1password.com/downloads)

#### 2. Install 1Password CLI

**macOS:**
```bash
brew install --cask 1password-cli
```

**Linux/WSL:**
```bash
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
  sudo tee /etc/apt/sources.list.d/1password.list

sudo apt update && sudo apt install 1password-cli
```

#### 3. Enable CLI Integration

1. Open 1Password desktop app
2. Go to **Settings → Developer**
3. Enable **"Integrate with 1Password CLI"**
4. Enable **"Connect with 1Password CLI"** (for biometric unlock)

### How It Works

The global bashrc (`profiles/global/bashrc`) automatically initializes 1Password when available:

```bash
if command -v op >/dev/null 2>&1; then
    if [[ "${CC_ISOLATE_1PASSWORD_ENABLED:-true}" == "true" ]]; then
        eval "$(op plugin run -- --init bash)"
    fi
fi
```

**Shell plugin auto-injects secrets for 60+ tools:**
- Git (GitHub, GitLab, Bitbucket tokens)
- AWS CLI (access keys)
- GitHub CLI (gh)
- Docker (registry auth)
- SSH (key passphrases)
- Terraform, kubectl, and more

### Usage

**Automatic (via shell plugin):**
```bash
# Tools authenticate automatically
git push                  # 1Password provides GitHub token
aws s3 ls                # 1Password provides AWS credentials
gh api user              # 1Password provides GitHub token
```

**Manual secret injection:**
```bash
# Read secrets directly
export API_KEY="$(op read 'op://Private/MyApp/api_key')"

# Inject into command
op run --env-file=.env -- npm start
```

**Template syntax in .env:**
```bash
# .env (gitignored)
API_KEY="op://Private/MyApp/api_key"
DB_URL="op://Private/Database/connection_string"
```

### Configuration

In `config.sh` or your shell profile:

```bash
# Enable/disable 1Password integration
CC_ISOLATE_1PASSWORD_ENABLED=true

# Auto-signin when session expires
CC_ISOLATE_1PASSWORD_AUTO_SIGNIN=false

# Default account
CC_ISOLATE_1PASSWORD_ACCOUNT=""
```

### Troubleshooting

**"op: command not found"** - Install 1Password CLI (see above)

**"not signed in"** - Enable desktop app integration or run `eval "$(op signin)"`

**"Shell plugin not working"** - Re-initialize: `eval "$(op plugin run -- --init bash)"`

### Resources

- [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- [Shell Plugins Guide](https://developer.1password.com/docs/cli/shell-plugins/)
- [Supported Tools List](https://developer.1password.com/docs/cli/shell-plugins/supported-tools/)

---

## Isolation System (Mount/Unmount)

The mount system provides isolated bash environments for Claude Code sessions with protection against accidental system file modifications.

### Why Isolation?

When running Claude Code with `dangerously-skip-permissions`, you want:
- **Protection** for system bashrc from accidental modifications
- **Consistent environments** across machines
- **Visual indicators** when in isolated mode
- **Easy switching** between project contexts

### How It Works

1. **Mounting** creates a layered environment:
   ```
   System bashrc (read-only)
      ↓
   Profile bashrc (your customizations)
      ↓
   Snippets from bashrc.d/
   ```

2. **Protection** (optional) makes system bashrc immutable:
   - Linux: `chattr +i`
   - macOS: `chflags uchg`

3. **BASH_ENV** points Claude Code to use the isolated environment

### Commands

```bash
# Mount with global profile
devenv mount

# Mount with specific profile
devenv mount web-dev

# Check status
devenv status

# Unmount (removes protection)
devenv unmount
```

### Activating for Claude Code

```bash
# Set BASH_ENV for all Claude Code sessions
export BASH_ENV=$HOME/cc-projects/general-tools/env-sync/.cc-env

# Add to ~/.bashrc or ~/.zshrc for persistence
```

### Profile Management

```bash
# List profiles
devenv profile list

# Create new profile
devenv profile create web-dev

# Delete profile
devenv profile delete web-dev
```

### Configuration

```bash
# In config.sh
PROTECT_SYSTEM_BASHRC=true   # Enable immutable flag
CC_ISOLATE_PROMPT_ENABLED=true  # Show [CC] in prompt
CC_ISOLATE_SHOW_WELCOME=false   # Show welcome message
```

---

## Advanced Usage

### Custom Bashrc Snippets

Add reusable snippets to `bashrc.d/`:

```bash
# bashrc.d/docker.sh
alias dps='docker ps'
alias dimg='docker images'
alias dexec='docker exec -it'
```

These are automatically sourced when isolation is mounted.

### Conditional Platform Configuration

```bash
# In profiles/global/bashrc
if [[ "$CC_ISOLATE_PLATFORM" == "macos" ]]; then
    export HOMEBREW_PREFIX="/opt/homebrew"
    export PATH="$HOMEBREW_PREFIX/bin:$PATH"
elif [[ "$CC_ISOLATE_PLATFORM" == "wsl" ]]; then
    export BROWSER="/mnt/c/Windows/explorer.exe"
fi
```

### Machine-Specific Profiles

```bash
# Desktop profile (powerful machine)
devenv profile create desktop
cat > profiles/desktop/bashrc << 'EOF'
export PARALLEL_JOBS=16
export DOCKER_MEMORY=8G
EOF

# Laptop profile (resource-constrained)
devenv profile create laptop
cat > profiles/laptop/bashrc << 'EOF'
export PARALLEL_JOBS=4
export DOCKER_MEMORY=2G
EOF

# Mount appropriate profile per machine
devenv mount desktop  # On desktop
devenv mount laptop   # On laptop
```

### Claude Code Hooks Integration

Auto-mount on session start:

```yaml
# In Claude Code hooks configuration
session-start:
  - /path/to/env-sync/bin/devenv mount global
```

---

## Security & Isolation

### Security Layers

1. **Age Encryption**: Secrets encrypted with ChaCha20-Poly1305
2. **GitLeaks Scanning**: Pre-push secret detection
3. **File Protection**: Immutable flags on system files
4. **Permission Control**: Deployed secrets are `chmod 600`

### Threat Model

**devenv protects against:**
- ✅ Accidental secret commits to git
- ✅ Accidental modification of system bashrc
- ✅ Configuration drift between machines
- ✅ Plaintext secrets in dotfiles

**devenv does NOT protect against:**
- ❌ Malicious code execution (use Claude Code Sandbox)
- ❌ Stolen encryption password
- ❌ Root-level compromises
- ❌ Memory-based attacks

**Important**: devenv is a convenience and safety layer, not a security boundary. Use Claude Code's built-in Sandbox mode for security isolation.

---

## FAQ

### Do I need to commit `.cc-env`?

No, it's generated locally and gitignored.

### Can I use this without Claude Code?

Yes. It's a general-purpose environment sync tool. Just source the bashrc in your shell.

### What if I use Zsh instead of Bash?

The bashrc is zsh-compatible. Add to `~/.zshrc`:
```bash
source ~/path/to/env-sync/profiles/global/bashrc
```

### How do I sync environment variables?

Add them to `profiles/global/bashrc`, then `devenv push`.

### Can I have different secrets on different machines?

The vault is shared, but you can use project-specific secrets that only deploy if the project directory exists on that machine.

### What happens if I forget my encryption password?

You cannot decrypt your secrets. Keep your password in a password manager.

### Is the encryption secure?

Yes. Age uses ChaCha20-Poly1305, a modern authenticated encryption scheme. Password-based encryption uses scrypt for key derivation.

---

## Dependencies

Required:
- **bash** 3.2+ (macOS default works)
- **git**
- **age** (auto-installed if missing)

Optional:
- **GitLeaks** - For secret scanning (auto-installed via brew/go)
- **Homebrew** - For tool installation on macOS
- **1Password CLI** - For shell plugin integration

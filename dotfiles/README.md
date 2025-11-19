# Dotfiles Backup

Environment configuration backup for easy setup on new machines.

## Contents

- `bashrc` - Full bashrc with custom aliases
- `claude/` - Global Claude Code settings
  - `CLAUDE.md` - Global agent instructions
  - `settings.json` - Claude Code configuration (API keys redacted)
  - `output-styles/dense.md` - Custom dense output style
- `env-templates/` - Environment variable templates and instructions
- `setup.sh` - Automated setup script

## Quick Setup

On a new machine:

```bash
cd ~/projects/general_tools/dotfiles
chmod +x setup.sh
./setup.sh
```

Then follow the post-setup instructions.

## Manual Setup

If you prefer manual setup:

1. **Claude settings:**
   ```bash
   mkdir -p ~/.claude/output-styles
   cp claude/* ~/.claude/
   cp claude/output-styles/* ~/.claude/output-styles/
   ```

2. **Bash aliases:**
   - Copy relevant aliases from `bashrc` to your `~/.bashrc`
   - Or source entire file: `echo 'source ~/projects/general_tools/dotfiles/bashrc' >> ~/.bashrc`

3. **Environment variables:**
   - See `env-templates/README.md` for API key setup
   - Clone muse-v1 repo - `.envrc` files are tracked there

4. **Tools:**
   - Install direnv: `brew install direnv` (macOS) or `apt install direnv` (Linux)
   - Add to shell: `eval "$(direnv hook bash)"` in `~/.bashrc`

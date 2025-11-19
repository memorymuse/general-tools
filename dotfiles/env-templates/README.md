# Environment Setup

## API Keys

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "OPENAI_API_KEY": "sk-proj-...",
    "ANTHROPIC_API_KEY": "sk-ant-api03-...",
    "GEMINI_API_KEY": "AIza..."
  }
}
```

## Muse Environment

The main `.envrc` files are tracked in the muse-v1 repo. After cloning muse-v1:

```bash
cd ~/projects/muse-v1
direnv allow
```

This will load all project-specific environment variables automatically.

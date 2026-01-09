# Git Workflows - Extended Reference

Advanced git patterns for branch management, PRs, and collaboration.

## Branch Strategies

### Feature Branch Workflow

```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/descriptive-name

# Work on feature (commit regularly)
git add specific_file.py
git commit -m "feat: Add initial implementation"

# Push feature branch
git push -u origin feature/descriptive-name

# When ready, create PR (see PR section below)
```

### Naming Conventions

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New functionality | `feature/user-auth` |
| `fix/` | Bug fixes | `fix/session-timeout` |
| `refactor/` | Code improvements | `refactor/storage-layer` |
| `test/` | Test additions | `test/integration-coverage` |
| `docs/` | Documentation | `docs/api-reference` |

## Commit Discipline

### Atomic Commits

Each commit should be:
- **Single purpose**: One logical change
- **Complete**: Tests pass, code works
- **Reversible**: Can be reverted independently

```bash
# ❌ BAD - multiple unrelated changes
git add .
git commit -m "feat: Add auth and fix bug and update docs"

# ✅ GOOD - atomic commits
git add auth.py tests/test_auth.py
git commit -m "feat: Add authentication module"

git add bug_fix.py
git commit -m "fix: Resolve session timeout issue"

git add README.md
git commit -m "docs: Update authentication section"
```

### Commit Message Format

```
type(scope): subject

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or correcting tests
- `docs`: Documentation only changes
- `chore`: Changes to build process or auxiliary tools
- `perf`: Performance improvement
- `style`: Formatting, missing semicolons, etc.

**Examples**:

```bash
# Simple
git commit -m "feat: Add user registration endpoint"

# With scope
git commit -m "fix(auth): Resolve token expiration bug"

# With body (use heredoc for multi-line)
git commit -m "$(cat <<'EOF'
refactor(storage): Simplify query builder

- Extract common query patterns
- Add type hints throughout
- Remove deprecated methods

Closes #123
EOF
)"
```

## Staging Discipline

### Explicit File Staging

```bash
# ❌ NEVER - stages everything including unintended files
git add .
git add -A

# ✅ ALWAYS - stage explicitly
git add src/feature.py
git add tests/test_feature.py

# Stage specific hunks interactively (when needed)
git add -p src/feature.py
```

### Review Before Commit

```bash
# See what's staged
git diff --staged

# See what's not staged
git diff

# See status
git status
```

## Pull Request Workflow

### Creating a PR

```bash
# Ensure branch is up to date
git fetch origin main
git rebase origin/main  # Or merge, depending on team preference

# Push and create PR
git push origin feature/my-feature

# Create PR via gh CLI
gh pr create --title "feat: Add feature X" --body "$(cat <<'EOF'
## Summary
- Added feature X
- Updated tests

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual verification

## Notes
Any additional context for reviewers.
EOF
)"
```

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Changes
- List of specific changes
- Another change

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #123
```

## Recovery Patterns

### Undo Last Commit (Keep Changes)

```bash
git reset --soft HEAD~1
```

### Undo Last Commit (Discard Changes)

```bash
git reset --hard HEAD~1
```

### Fix Last Commit Message

```bash
git commit --amend -m "corrected message"
```

### Add Forgotten File to Last Commit

```bash
git add forgotten_file.py
git commit --amend --no-edit
```

### Stash Work in Progress

```bash
# Save WIP
git stash push -m "WIP: feature description"

# List stashes
git stash list

# Apply latest stash
git stash pop

# Apply specific stash
git stash apply stash@{2}
```

## Safety Checks

### Pre-Push Verification

```bash
# Verify local and remote are in sync
git fetch origin
git status

# Should show "Your branch is up to date" or "ahead by X commits"
```

### Verify Push Succeeded

```bash
# Check remote has your commits
git log --oneline -n 5 origin/branch-name
```

### Check for Secrets

```bash
# Before committing, check for sensitive patterns
git diff --staged | grep -E "(password|secret|api_key|token)" || echo "No secrets found"
```

## What to NEVER Do

| Action | Risk | Alternative |
|--------|------|-------------|
| `git add .` | Commits unintended files | Stage explicitly |
| `git push --force` | Destroys remote history | Use `--force-with-lease` if necessary |
| Commit `.env` files | Exposes secrets | Add to `.gitignore` |
| Commit to main directly | Bypasses review | Use feature branches |
| Amend pushed commits | Breaks collaborators | Create new commit |

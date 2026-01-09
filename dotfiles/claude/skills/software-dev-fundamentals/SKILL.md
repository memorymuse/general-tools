---
name: software-dev-fundamentals
description: You MUST PROACTIVELY USE this skill when developing software. Provides TDD workflow (RED-GREEN-REFACTOR), error handling patterns (fail-loud, educational errors), and git discipline (commits, branches, PRs). NEVER skip tests or suppress errors.
---

# Software Development Fundamentals

Core practices for quality software development. These are non-negotiable standards.

## TDD: Test-Driven Development

**NO EXCEPTIONS**. Every change follows this cycle:

### The RED-GREEN-REFACTOR Cycle

1. **RED**: Write failing test first
   - Think about interface before implementation
   - Define expected behavior clearly
   - Run test, confirm it fails for the right reason

2. **GREEN**: Write minimal code to pass
   - No gold plating
   - Simplest solution that works
   - Run test, confirm it passes

3. **REFACTOR**: Improve code while tests stay green
   - Extract duplication
   - Improve naming
   - Simplify logic
   - Tests must stay green throughout

```python
# ALWAYS start with test file
test_feature.py  # Write this FIRST
feature.py       # Write this SECOND
```

### Test Structure Pattern

```python
# Unit test structure (Arrange → Act → Assert)
async def test_feature_description():
    # Arrange
    expected = "value"

    # Act
    result = await function_under_test()

    # Assert
    assert result == expected
```

### Coverage Requirements

- New code: 100% coverage target (90%+ acceptable with rationale for gaps)
- Modified code: Maintain or improve coverage
- Integration points: Must have integration tests
- Edge cases: Explicitly test error conditions
- Overall codebase: Strive for 90%+ coverage

**ALWAYS translate implementation plans** into TDD outlines before writing any other code.

---

## Error Handling: Fail-Loud Philosophy

Errors must surface visibly. Silent failures allow agents to operate on false assumptions, compounding problems.

### Core Principle

**Never suppress errors**:

```python
# ❌ Silent failure - NEVER DO THIS
try:
    result = risky_operation()
except:
    pass

# ✅ Fail loudly - Let it fail visibly
result = risky_operation()

# ✅ If handling required, log and re-raise with context
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise OperationalError(f"Failed to process {item}: {e}") from e
```

Visible failures force correction. Silent failures create cascading errors.

### Educational Error Messages

Errors are learning opportunities. Every error message must teach how to fix the problem.

**Pattern**:

```python
# ❌ Minimal error - unhelpful
raise ValueError("Missing user id attribute")

# ✅ Educational error - teaches how to fix
raise ValueError(
    "Missing required parameter 'user_id'. "
    "Example: get_user(user_id=123). "
    f"Received: get_user(user_id={user_id})"
)
```

**Required elements**:
1. What went wrong
2. Why it matters
3. How to fix it (with example)
4. What was actually received (if applicable)

### Contextual Re-raising

Add context when re-raising exceptions:

```python
try:
    result = await operation()
except SpecificError as e:
    raise OperationalError(
        f"Failed to process {item_id}: {str(e)}. "
        f"Recovery hint: Check stream configuration. "
        f"Expected: valid stream_id, Received: {item_id}",
        recovery_hint="Check stream configuration"
    ) from e
```

---

## Git Discipline

### Commit & Push Discipline

**Context**: Local work can vanish. Commit early, commit often, push regularly.

**When to commit**:
- After test creation
- After tests pass
- After refactoring
- Before risky operations

**When to push**:
- After each test/implementation cycle
- At session end
- Minimum: After any significant work

### Commit Message Format

```
type: description

Types: test, feat, fix, refactor, docs, chore, perf, style

Examples:
test: Add session state validation tests
feat: Implement environment variable handshake
fix: Resolve session state synchronization issue
docs: Update session handoff template
```

### Git Workflow

**Branch strategy**: Feature branches off main

```bash
git checkout -b feature/descriptive-name
```

**Commit discipline**:

```bash
# After test creation
git add tests/test_feature.py
git commit -m "test: Add failing tests for feature X"

# After implementation
git add feature.py
git commit -m "feat: Implement feature X to pass tests"

# After refactoring
git add feature.py
git commit -m "refactor: Improve feature X implementation"
```

**Push discipline**:

```bash
# Push regularly
git push origin branch-name

# Verify push succeeded
git log --oneline -n 5 origin/branch-name
```

### Pre-Commit Checklist

- [ ] Tests passing
- [ ] Files staged explicitly (no `git add .`)
- [ ] Commit message follows format
- [ ] No secrets in staged files

### Pre-Push Checklist

- [ ] All tests passing
- [ ] No uncommitted changes
- [ ] Push verified: `git fetch && git status`

### Critical Warnings

- **NEVER** use `git add .` or `git add -A` (stage files explicitly)
- **NEVER** commit `.env*` files or secrets
- **NEVER** force push to main/master without explicit user request
- **NEVER** modify `.gitignore` under your own initiative

---

## Quick Reference

### TDD Cycle Summary

| Phase | Action | Verification |
|-------|--------|--------------|
| RED | Write failing test | Test fails for right reason |
| GREEN | Write minimal code | Test passes |
| REFACTOR | Improve code | Tests stay green |

### Error Message Checklist

- [ ] What went wrong?
- [ ] Why it matters?
- [ ] How to fix? (with example)
- [ ] What was received?

### Git Checklist

- [ ] Tests pass?
- [ ] Files staged explicitly?
- [ ] Message formatted correctly?
- [ ] No secrets?

---

## References

These references extend this skill's core content. Load them proactively when your task requires deeper context in these areas—don't wait until you're stuck.

| Reference | Load When | Example Conditions |
|-----------|-----------|-------------------|
| [tdd-patterns.md](tdd-patterns.md) | Writing async tests, organizing test suites, mocking dependencies, handling test edge cases | "Need async fixtures with cleanup", "How do I mock this service?", "Tests are flaky", "Organizing tests for large module" |
| [error-examples.md](error-examples.md) | Implementing error handling beyond basic fail-loud, creating custom exceptions, building error hierarchies | "Need educational error for this case", "Building exception hierarchy", "Re-raising with proper context" |
| [git-workflows.md](git-workflows.md) | Creating PRs, managing branches, recovering from git mistakes, advanced staging | "Creating a PR", "Need to undo last commit", "What branch naming convention?", "Stashing work in progress" |

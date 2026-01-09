# Handoff Templates - Extended Reference

Templates and examples for effective session handoffs.

## Standard Handoff Template

```markdown
# Handoff Memo - [YYYY-MM-DD]

## Session Summary
**Agent**: [Agent identifier]
**Duration**: [Approximate time]
**Focus**: [Primary work area]

---

## Current State

### Overall Status
[One paragraph summary of where things stand]

### Project/Feature Status
- [ ] [Component 1]: [Status - Complete/In Progress/Blocked]
- [ ] [Component 2]: [Status]
- [ ] [Component 3]: [Status]

---

## Work Completed This Session

### 1. [First Major Accomplishment]
- What: [Description]
- Why: [Rationale/Goal]
- Files: [List of files modified]
- Tests: [Test coverage added]

### 2. [Second Major Accomplishment]
- What: [Description]
- Why: [Rationale/Goal]
- Files: [List of files modified]
- Tests: [Test coverage added]

---

## Key Decisions Made

| # | Decision | Options Considered | Rationale |
|---|----------|-------------------|-----------|
| 1 | [Decision] | [A, B, C] | [Why we chose A] |
| 2 | [Decision] | [X, Y] | [Why we chose X] |

---

## Critical Context / Nuance

**IMPORTANT**: [Things that aren't obvious but are critical]

- [Insight 1]: [Explanation]
- [Insight 2]: [Explanation]
- [Gotcha]: [Something that could trip up the next agent]

---

## Blockers / Unresolved Issues

### Blocker 1: [Name]
- **Issue**: [Description]
- **Attempted**: [What was tried]
- **Needed**: [What would unblock this]

---

## Next Steps (Priority Order)

1. **[HIGH]** [Task]: [Brief description]
   - Start point: [Where to begin]
   - Expected outcome: [What success looks like]

2. **[MEDIUM]** [Task]: [Brief description]
   - Start point: [Where to begin]

3. **[LOW]** [Task]: [Brief description]

---

## Modified Files Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `path/to/file.py` | Modified | [What changed] |
| `path/to/new.py` | Created | [Purpose] |
| `tests/test_x.py` | Created | [Coverage added] |

---

## Test Status

```
Tests: X passed, Y failed, Z skipped
Coverage: XX% → YY%
```

**Failing tests** (if any):
- `test_name`: [Reason/Status]

---

## Commands for Next Agent

```bash
# To pick up where I left off:
cd [directory]
git status  # Should show: [expected state]

# To run relevant tests:
pytest tests/path/to/test.py -v

# To verify current state:
[Any verification commands]
```
```

## Quick Handoff Template (Short Sessions)

For shorter sessions or simpler work:

```markdown
# Quick Handoff - [DATE]

**Completed**: [1-2 sentence summary]

**Key Decision**: [Most important decision made, if any]

**Next Step**: [Single most important next action]

**Files Changed**: [List]

**Note**: [One critical thing to know]
```

## Feature Development Handoff

```markdown
# Feature Handoff: [Feature Name]

## Feature Status: [X]% Complete

### Completed Components
- [x] [Component 1]
- [x] [Component 2]
- [ ] [Component 3] - In Progress

### Current Implementation State
[Describe what's built and working]

### What Remains
1. [Remaining task 1]
2. [Remaining task 2]

### Design Decisions Locked In
- [Decision 1]: [Brief rationale]
- [Decision 2]: [Brief rationale]

### Open Design Questions
- [ ] [Question 1]: [Options being considered]

### Test Coverage
- Unit: [X]% of new code
- Integration: [Y/N]

### Handoff Point
The next agent should start by: [specific instruction]
```

## Bug Investigation Handoff

```markdown
# Bug Investigation Handoff

## Bug: [Description]

## Investigation Status: [Phase]
- [ ] Symptom documented
- [ ] Reproduced reliably
- [x] Trace started
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Tests added

## Current Understanding

### What We Know
- [Fact 1]
- [Fact 2]

### What We Suspect
- [Hypothesis 1]
- [Hypothesis 2]

### What We've Ruled Out
- [Not the cause 1]
- [Not the cause 2]

## Investigation Trace So Far

```
Step 1: [Where error occurs]
  → Found: [Finding]

Step 2: [Traced value origin]
  → Found: [Finding]

Step 3: [Next step needed]
  → TODO: [What to investigate next]
```

## Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Expected vs Actual]

## Next Investigation Steps
1. [What to check next]
2. [What to verify]
```

## Handoff Quality Checklist

Before finalizing any handoff, verify:

- [ ] **State is clear**: Another agent can understand exactly where things stand
- [ ] **Decisions are explained**: WHY, not just WHAT
- [ ] **Nuance is captured**: Non-obvious insights documented
- [ ] **Next steps are actionable**: Specific enough to start immediately
- [ ] **Files are listed**: What was touched and why
- [ ] **Blockers are explicit**: What couldn't be resolved and why
- [ ] **Commands are provided**: How to verify/continue

## Common Handoff Mistakes

### Too Vague
```
❌ "Made good progress on the feature"
✅ "Implemented user authentication endpoint (POST /auth/login),
    added JWT token generation, wrote 5 unit tests (all passing)"
```

### Missing Context
```
❌ "Fixed the bug"
✅ "Fixed race condition in session initialization by ensuring
    environment variables are cleared in test fixtures. Root cause
    was env var leak between tests."
```

### No Next Steps
```
❌ "Continue from here"
✅ "Next: Implement token refresh endpoint. Start by reading
    auth/tokens.py:45 where refresh logic should go. Follow
    pattern established in login endpoint."
```

### Missing Nuance
```
❌ "Tests are passing"
✅ "Tests are passing. NOTE: test_concurrent_sessions is flaky
    (~5% failure rate) due to timing sensitivity. Added retry
    decorator as workaround but root cause needs investigation."
```

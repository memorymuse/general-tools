# Planning Deep Dive - Extended Reference

Detailed methodology for planning complex work as an agent.

## Hypothesis Formation

### Good vs Bad Hypotheses

| Bad (Vague)            | Good (Testable)                                    |
| ---------------------- | -------------------------------------------------- |
| "Something is wrong"   | "The validation is failing because input is None"  |
| "It needs refactoring" | "Extract the duplicate code into a shared utility" |
| "Performance is slow"  | "The N+1 query in user_list() causes slowdown"     |

### Hypothesis Template

```
Hypothesis: [Specific, testable claim]
Evidence needed: [What would prove/disprove this]
Test approach: [How to gather evidence efficiently]
Risk if wrong: [What happens if we proceed on false assumption]
```

### Example

```
Hypothesis: The test timeout is caused by unclosed database connections
Evidence needed: Check if connections are closed in fixtures, monitor open handles
Test approach: Add connection tracking, run single test with profiler
Risk if wrong: We'd refactor fixtures when the real issue is elsewhere
```

## Plan Structure Patterns

### Feature Implementation Plan

```markdown
# Feature: [Name]

## 1. Goals
- Primary: [What must be achieved]
- Secondary: [Nice-to-haves if time permits]
- Non-goals: [Explicitly out of scope]

## 2. Approach
- Strategy: [High-level approach]
- Alternatives considered: [What else was evaluated]
- Why this approach: [Decision rationale]

## 3. Requirements
- [ ] Functional: [What it must do]
- [ ] Performance: [Speed/resource constraints]
- [ ] Security: [Access control, data protection]
- [ ] Testing: [Coverage expectations]

## 4. Implementation Steps
1. [Step 1] → produces [output 1]
2. [Step 2] (uses output 1) → produces [output 2]
3. [Step 3] (uses output 2) → produces [final result]

## 5. Success Metrics
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] No regressions in existing tests
- [ ] Code review approved

## 6. Definition of Done
- [ ] Feature complete per requirements
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Handoff memo created
```

### Bug Fix Plan

```markdown
# Bug: [Description]

## 1. Symptom
[What's observed - exact error, unexpected behavior]

## 2. Investigation Hypothesis
[What we think is wrong, based on initial evidence]

## 3. Investigation Steps
1. [Trace step 1]
2. [Trace step 2]
3. [Validation of hypothesis]

## 4. Root Cause (after investigation)
[What's actually wrong]

## 5. Fix Approach
[How to address root cause]

## 6. Verification
- [ ] Bug no longer reproducible
- [ ] No regressions introduced
- [ ] Test added to prevent recurrence
```

### Refactoring Plan

```markdown
# Refactor: [What's being improved]

## 1. Current State
[What exists now and why it's problematic]

## 2. Desired State
[What it should look like after refactoring]

## 3. Constraints
- Must maintain backward compatibility: [yes/no]
- Must preserve existing tests: [yes/no]
- Time budget: [constraint]

## 4. Strategy
- [ ] Incremental (small changes, frequent commits)
- [ ] Big bang (single large change)
Rationale: [Why this strategy]

## 5. Steps
1. [First transformation]
2. [Second transformation]
...

## 6. Verification
- [ ] All existing tests pass
- [ ] New tests for changed behavior
- [ ] Performance not degraded
```

## Sequential Planning

### Why Sequential Matters

Each step should produce output that feeds the next step:

```
Step 1: Analyze existing code
  → Output: List of current patterns and pain points

Step 2: Design new interface (uses Step 1 output)
  → Output: Interface specification

Step 3: Write tests for new interface (uses Step 2 output)
  → Output: Failing tests

Step 4: Implement interface (uses Step 2 + Step 3 output)
  → Output: Passing tests, working code
```

### Anti-Pattern: Parallel Steps with Dependencies

```
❌ Wrong:
1. Write implementation
2. Write tests
3. Design interface

These have dependencies but aren't sequenced correctly.

✅ Right:
1. Design interface → produces spec
2. Write tests (using spec) → produces test suite
3. Write implementation (to pass tests) → produces code
```

## Risk Assessment

### Before Starting Major Work

Ask:

1. What could go wrong?
2. What's the blast radius if it fails?
3. Do I have a rollback plan?
4. Should I escalate before proceeding?

### Risk Levels

| Risk Level | Characteristics                                | Action                      |
| ---------- | ---------------------------------------------- | --------------------------- |
| Low        | Reversible, limited scope, well-understood     | Proceed autonomously        |
| Medium     | Significant scope, some uncertainty            | Document rationale, proceed |
| High       | Data loss possible, breaking changes, security | Escalate to user            |

## Work Review Patterns

### Self-Review Checklist

After completing work:

- [ ] Re-read all changes with fresh eyes
- [ ] Check each file: Does this do what I intended? Does it meet the objective?
- [ ] Run all tests (not just new ones)
- [ ] Look for edge cases I might have missed
- [ ] Check for security implications
- [ ] Verify no debug code left in

### Quality Questions

- Is this the simplest solution that works?
- Would another agent understand this without context?
- Did I follow established patterns in the codebase?
- Are error messages educational?
- Is test coverage adequate?

### Iteration Triggers

Iterate more if:

- Confidence is below "high"
- You're unsure about any aspect
- The approach feels hacky
- Tests are incomplete

Stop iterating when:

- All requirements are met
- Code is clean and readable
- Tests are comprehensive
- You can explain every decision

---
name: debugging-protocol
description: You MUST PROACTIVELY USE this skill when debugging unexpected behavior or investigating failures. Provides systematic trace-before-fix methodology and root cause analysis patterns. NEVER fix without tracing first.
---

# Debugging Protocol: Trace Before You Fix

When encountering unexpected behavior, **trace every expectation back to its source** before writing any fix.

**Core Principle**: The fix should address the root cause, not accommodate the symptom.

---

## The Investigation Pattern

Follow these 5 steps BEFORE writing any fix:

### Step 1: Error/Expectation → Where is this checked?

Identify the exact location where the error is raised or where the expectation is validated.

```
Error: "Session number mismatch: expected 2, got 1"
Question: Where is this check performed?
Answer: domain/sessions/manager.py:157
```

### Step 2: Check Location → What values are being compared?

Examine the comparison logic. What specific values are involved?

```
Code at manager.py:157:
  if current_session != expected_session:
      raise SessionError(f"mismatch: expected {expected_session}, got {current_session}")

Values being compared:
  - expected_session = 2
  - current_session = 1
```

### Step 3: Values → Where do these values originate?

Trace each value back to its source. Don't assume - verify.

```
expected_session comes from: os.environ.get('EXPECTED_NEXT_SESSION_NUM')
current_session comes from: self.session_counter (instance variable)

Question: Why would environment say 2 but counter say 1?
```

### Step 4: Origin → What system maintains this state?

Understand the system responsible for each piece of state.

```
Environment variable: Set during session initialization
Session counter: Incremented in start_session() method

Discovery: Environment variables persist across test runs
The env var from a previous test is leaking into this test
```

### Step 5: System → Why was it designed this way?

Understand the design intent before proposing changes.

```
Design: Environment variables used for cross-process communication
Intent: Allow external systems to know expected session number
Problem: Test isolation doesn't clear environment state
```

### Step 6: Craft Your Hypotheses

Only after completing the trace, formulate:

**Root Cause Hypothesis**: What is actually wrong?
```
Environment variable leak between test runs. The env var
EXPECTED_NEXT_SESSION_NUM persists from previous test, causing
mismatch with fresh session counter.
```

**Fix Hypothesis**: What change will address the root cause?
```
Clear environment state in test fixtures before each test.
Add os.environ.pop('EXPECTED_NEXT_SESSION_NUM', None) to fixture teardown.
```

---

## Complete Example

```
Error: "Session number mismatch: expected 2, got 1"

Trace:
1. Checked at: domain/sessions/manager.py:157
2. Comparing: expected_session (2) vs current_session (1)
3. expected_session from: os.environ.get('EXPECTED_NEXT_SESSION_NUM')
   current_session from: self.session_counter
4. Discovery: Environment variables persist across test runs
5. Design: Env vars used for cross-process state sharing

Root Cause Hypothesis: Environment variable leak between tests
Fix Hypothesis: Clear environment state in test fixtures

Validation:
- Reproduced env var leak in isolated test
- Confirmed clearing fixture env state prevents leak
- All tests pass with fix applied
```

---

## Anti-Patterns to Avoid

### Fixing Symptoms

```python
# ❌ WRONG - Accommodates the symptom
if current_session != expected_session:
    current_session = expected_session  # Just make them match!

# ✅ RIGHT - Addresses root cause
# In test fixture:
@pytest.fixture(autouse=True)
def clean_environment():
    yield
    os.environ.pop('EXPECTED_NEXT_SESSION_NUM', None)
```

### Skipping Steps

```
❌ "I think it's X" → [writes fix without tracing]
✅ "I think it's X" → [traces to verify] → [finds it's actually Y] → [fixes Y]
```

### Stopping at First Clue

```
❌ "Found where error is raised, that must be the problem"
✅ "Found where error is raised, now trace the values back to their origin"
```

---

## When to Use This Protocol

**Always use when**:
- Error messages are unclear about root cause
- Same bug keeps reappearing
- Fix attempts haven't worked
- Behavior differs between environments
- "It works on my machine" situations

**Quick fixes OK when**:
- Cause is obvious (typo, missing import)
- You've seen this exact issue before with same root cause
- Fix is trivial AND you can verify correctness immediately

---

## Debugging Checklist

Before writing any fix, confirm:

- [ ] Identified exact location of error/unexpected behavior
- [ ] Traced all values back to their origins
- [ ] Understand what system maintains each piece of state
- [ ] Understand the design intent
- [ ] Formulated root cause hypothesis
- [ ] Formulated fix hypothesis that addresses root cause (not symptom)
- [ ] Can explain why this fix is correct

---

## References

These references extend this skill's core methodology. Load proactively when your debugging scenario requires additional context—don't wait until you're stuck.

| Reference | Load When | Example Conditions |
|-----------|-----------|-------------------|
| [investigation-examples.md](investigation-examples.md) | Debugging async/timing issues, environment-specific failures, memory problems, or need debugging tools reference | "Tests hang after passing", "Works locally fails in CI", "Flaky test", "Memory growing over time", "Need to add debug logging" |

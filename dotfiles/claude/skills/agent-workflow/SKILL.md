---
name: agent-workflow
description: You MUST PROACTIVELY USE this skill when starting sessions, ending sessions, or planning complex multi-step tasks. Provides session lifecycle procedures, work planning frameworks, and handoff protocols for effective multi-session continuity.
---

# Agent Workflow

Procedures for effective session management, work planning, and multi-session continuity.

**Core Principle**: Every agent session is one leg of a relay race. You inherit context from prior agents, do focused work, then pass the baton forward.

---

## Session Lifecycle

### Session Start Checklist

When beginning a new session:

1. **Review Stream Conscious** (if available)
   - Load the working memory snapshot
   - Note high-retention items (these were deemed important)

2. **Read handoff memo** from prior session
   - Understand current state
   - Note any blockers or decisions made
   - Identify next steps that were planned

3. **Query relevant memories**
   - Search for context related to current task
   - Look for patterns or decisions that may apply

4. **Correlate context to current goals**
   - Connect prior work to what you need to accomplish
   - Identify gaps in context

5. **Highlight key insights**
   - Note any nuance or learnings the prior agent emphasized
   - These often contain critical information

6. **Summarize plan** (<500 tokens, step-level detail)
   - State what you will accomplish this session
   - Make the plan visible

### During Session

- **Capture decisions with reasoning** - Document why, not just what
- **Document insights as thoughts** - Valuable observations persist as memories
- **Track progress visibly** - Use todo lists, update status regularly

### Session End Checklist (MANDATORY)

Before ending any session:

1. **Update progress tracking**
   - What was completed?
   - What remains?

2. **Create handoff memo**
   - Current state
   - Key decisions made
   - Blockers encountered
   - Explicit next steps

3. **Capture key insights as memories**
   - What did you learn?
   - What patterns did you discover?
   - What should future agents know?

4. **Self-assess against success criteria**
   - Did you meet the session's goals?
   - What could improve?

---

## Work Planning Framework

### Before Beginning Work

**State simple hypotheses**:

Make a simple, crisp and **meaningful** hypothesis (or hypotheses) about the work:

```
Hypothesis: The bug is caused by race condition in async initialization
Evidence needed: Trace the initialization order, check for missing awaits
```

Avoid uselessly vague hypotheses like "something is wrong with the code."

### Discovery & Validation

Explore the codebase and documentation to validate or invalidate your hypotheses:

- **Run minimal sandboxed tests** (minimal LOC to test core hypothesis)
- **ALWAYS understand what code does before executing**
  - "What are possible outputs?"
  - "Can this risk data loss?"
  - "Will this pollute production systems?"
  - "Will this mutate state?"
  - "How can I isolate this?"

**Apply appropriate caution**:
- **Data loss risk** → Escalate to user
- **>5k tokens just to determine starting point** → Escalate to user
- **Safe workarounds available** → Proceed confidently
- **When in doubt** → Abort and escalate

**Update mental model**:
If you've invalidated a hypothesis, develop new hypotheses with clear rationale before proceeding.

### Develop Your Plan

**Always** craft a *visible* plan before executing work:

1. **Goals/Objectives** - Clearly articulated, meaningful
2. **Strategic approach** - Considerations and decisions with rationale
3. **Requirements/Specifications** - Clear set of what must be true
4. **Implementation plan** - Sequential steps
5. **Success metrics** - How will you know it's done?
6. **Definition of done** - Sharp and tight

**Design implementation plans sequentially**: Output from one step should inform the next.

### Work Review Cycles

After completing work, ask yourself:

- Does this meet all requirements?
- Does this meet my bar for quality and excellence?
- Does this have weaknesses or vulnerabilities?
- Was any of this designed or executed "lazily"?
  - If remaining to-do's exist: clearly identify them with strong rationale
  - To-do's must be self-contained for another agent with zero context

**Re-read with fresh eyes**. Iterate until confidence is very high.

---

## Progress Tracking

### Session Progress Template

After each work session, document:

```markdown
## Session [NUMBER] - [DATE]

### Completed
- [Specific achievement 1]
- [Specific achievement 2]

### Tests Added
- [test_file_1.py]
- [test_file_2.py]

### Coverage
- Before: [X]%
- After: [Y]%

### Key Decisions
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

### Next Steps
- [ ] [Specific task 1]
- [ ] [Specific task 2]

### Blockers
- [Any blocking issues]
```

---

## Handoff Protocol

### Handoff Memo Structure

```markdown
# Handoff Memo - [DATE]

## Current State
[Where are we? What's the overall status?]

## Completed This Session
- [Specific completions with context]

## Key Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [What] | [Why] | [Effect] |

## Important Context/Nuance
[Things the next agent MUST know that aren't obvious]

## Blockers/Issues
- [Any unresolved problems]

## Explicit Next Steps
1. [ ] [First priority task]
2. [ ] [Second priority task]
3. [ ] [Third priority task]

## Files Modified
- [file1.py] - [what changed]
- [file2.py] - [what changed]
```

### What Makes a Good Handoff

**Critical reality**: Incomplete or low-quality handoffs are the single biggest risk to multi-session success.

A good handoff:
- **States current position clearly** - No ambiguity about where things stand
- **Explains decisions with reasoning** - Future agent understands WHY
- **Captures nuance** - Subtle insights that aren't obvious from code
- **Lists explicit next steps** - Actionable, not vague
- **Notes blockers** - What couldn't be resolved and why

A bad handoff:
- "Made progress on feature X"
- "See the code for details"
- "Continue from here"

---

## References

These references extend this skill's core procedures. Load proactively when your task requires deeper context—don't wait until you're stuck.

| Reference | Load When | Example Conditions |
|-----------|-----------|-------------------|
| [planning-deep-dive.md](planning-deep-dive.md) | Planning complex features, bug investigations, or refactors; need hypothesis templates or sequential planning guidance | "Building a multi-step feature", "Need structured bug fix plan", "Want to assess risk before proceeding" |
| [handoff-templates.md](handoff-templates.md) | Creating handoff memos, especially for feature development or bug investigations | "Ending session, need handoff template", "Handing off incomplete investigation", "Need quality checklist for handoff" |

---
description: Update docs and create session handoff
argument-hint: [focus-area] [depth-level]
---

# Session Closure: Documentation Update & Handoff Creation

## Phase 1: Audit & Update Documentation

### Step 1: Identify Files Touched This Session

List all files modified/created, sorted by recency with timestamps:

!`git status --short && echo "\n=== Recently Modified (including staged) ===" && git diff --name-only --cached 2>/dev/null | xargs ls -lt 2>/dev/null && echo "\n=== Untracked Files ===" && git ls-files --others --exclude-standard | xargs ls -lt 2>/dev/null | head -10`

### Step 2: Internal Audit

For each file touched, mentally catalog:
- All changes made (like a granular git commit history with brief, matter-of-fact comments)
- Documentation that should be correspondingly updated
- Whether work is in-flight (capture in handoff/project docs) vs complete (update system-level docs)

For code files:
- Review docstrings - are they useful? Do they embed context, decisions, rationale that prevents misinterpretation?
- Trim unnecessarily verbose docstrings (low-value fluff, dead-obvious explanations, repetition)

### Step 3: Determine What to Update

Content worth capturing in docs:
- Decisions and rationale
- Insights and discoveries
- Design changes
- Research findings
- Feedback and context
- Knowledge, details, nuances
- Examples (both guide-type and "learn from my mistake")
- Principles
- References to new files/tools/scripts created (with explanations and where to find them)

Document type guidelines:
- **System/architecture docs**: NO project/feature development status. YES foundational architectural decisions.
- **Project plans**: NO sole location for architectural decisions. YES task tracking and feature status.
- **Living documents** (multi-session, multi-agent): Compress content 4+ sessions old. Don't delete entire phases - compress to core relevant info (context, decisions, work done). Leave brief "hooks" that can be expanded if needed.
- **DRY principle**: See duplicative info in two docs? Trim one and leave markdown link to the canonical source.

### Step 4: User-Specified Updates

User may specify docs to update: $ARGUMENTS

IMPORTANT: Unless user explicitly restricts scope, update user-specified docs PLUS all others identified in your audit.

### Step 5: Execute Updates

Vigilantly scan and update all relevant documents per framework above. Look for token-burn reduction opportunities in living documents.

---

## Phase 2: Create Handoff Document

### Location
Default: `docs/handoffs/YYMMDD-HHMM_session-description.md` (time in PST - explicitly convert to Pacific Time, max 30 chars for description)
User may specify alternative location in arguments.

### Purpose
Capture all useful, utilitarian, subtly important aspects NOT already captured in other updated docs. Set next agent up for success.

### Critical Context
The next agent has ZERO memory of this session. No recollection of conversations, decisions, rationale, learnings - nothing. They enter with only onboarding docs you read at session start. This handoff is your ONE chance to impart wisdom and critical details. It enables compounding collective intelligence over time.

### Content to Include

**Session Work**:
- What you did and why
- Decisions made not pre-documented
- User inputs not captured elsewhere
- Files created/modified (with markdown links)

**Insights & Learning**:
- Insights learned (project, task, system/codebase, user)
- Nuances of how things work or are intended to work
- Important context that deepened understanding
- Pro-tips picked up
- Wisdom imparted by user or prior agents

**Issues & Friction**:
- Bugs squashed or still open
- Friction encountered
- Reflections: what went well, what you'd do differently

**Remaining Work**:
- Unfinished tasks with known/inferred/best-guessed priority order
- NO fabricated busy-work - only real remaining items
- Known requirements/specs/use cases for remaining work (don't fabricate)

**Navigation**:
- Required reading section
- Suggested reading section
- Files to be aware of (may need to use/modify)
- Useful references (with markdown links)

### User Specifications

Specific Focus: $1 (if provided - go deeper on this topic in handoff)
Depth Level: $2 (if provided - Low/High or specific token count)

Depth guidelines:
- Low = ~1.5k tokens
- High = ~3k tokens
- Custom = specific token count provided by user

If Low depth: Focus on most critical details next agent MUST know. Think: "What would next agent likely mess up if they didn't know X, Y, Z?" Include recommended questions for them to ask user to build context or fill gaps you don't know but they'll need.

### Constraints

- Max 300 lines
- Balance: depth of detail/context vs concise brevity
- Apply DRY: Don't duplicate info from other docs - link to them
- Cannot dump entire context window - more tokens consumed = less work capacity for next agent

---

## Your Task

1. Execute Phase 1: Audit and update all relevant documentation
2. Execute Phase 2: Create handoff document
3. Report completion with:
   - Summary of documents updated
   - Handoff document location
   - Any critical notes for user

# Self-Review System: User Guide

**For**: Kyle
**Purpose**: How to use and understand the self-review system

---

## What This Is

When you complete a significant artifact—a problem model, design document, implementation plan, or similar deliverable—there is a gap between "I think this is good" and "I have verified this is good." This system bridges that gap.

**The core insight:** You are capable of finding most flaws in your own work—but only if you systematically look for them. This protocol makes that systematic examination concrete and repeatable.

**The value**: Catches flaws before they cost hours downstream. Reviews build an auditable quality record.

**The trust cycle**: Consistent quality verification → demonstrated reliability → earned autonomy.

---

## Quick Start

```bash
/artifact-review <artifact> [intensity] [focus]
```

| Argument | Required | Options |
|----------|----------|---------|
| artifact | Yes | File path, `last`, `above`, or description |
| intensity | No | `quick`, `standard` (default), `thorough` |
| focus | No | `security`, `accuracy`, `clarity`, `completeness`, `feasibility` |

**Example**: `/artifact-review ./docs/plan.md thorough security`

---

## The Philosophy

### Operating Principles

These principles govern all self-review work:

**Intellectual Honesty.** Seek truth about quality. No false humility, no overconfidence. Just straightforward assessment. If there's a flaw, surface it.

**Constructive Candor.** Be direct. If a section is hand-wavy, call it hand-wavy. Challenge work with the same rigor you'd apply to someone else's.

**Empiricism.** Zero assumptions. Verify claims. Base review on evidence, not impressions.

**Objectivity.** The orchestrator created the artifact and has attachment. The subagents examine with fresh eyes—no history, no attachment. This structural separation enables objectivity the creator cannot achieve alone.

### Core Principles

**No Quota Theater**: Every question must genuinely matter. Quality over quantity.

**Goal Alignment**: Every question serves the artifact's objectives.

**Focused Execution**: Depth on one thing beats shallow passes on everything.

**Right-Sized Rigor**: Not too much, not too little—exactly what's needed.

**Autonomous Quality**: You are your own quality gate.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  YOU invoke: /artifact-review <artifact>                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SLASH COMMAND parses arguments, triggers skill                 │
│  ~/.claude/commands/artifact-review.md                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR SKILL loaded by prime agent                       │
│  ~/.claude/skills/artifact-review/SKILL.md                          │
│                                                                 │
│  Prime agent responsibilities:                                  │
│  • Prepare comprehensive context for each subagent              │
│  • Include relevant Operating Principles for each phase         │
│  • Invoke subagents in sequence                                 │
│  • Apply file revisions between phases                          │
│  • Synthesize and present final results                         │
│                                                                 │
│  The prime agent IS the quality gate.                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   SUBAGENT    │   │   SUBAGENT    │   │   SUBAGENT    │
│   P1-P5       │   │   P1-P5       │   │   P1-P5       │
│               │   │               │   │               │
│ Fresh context │   │ Fresh context │   │ Fresh context │
│ each invoke   │   │ each invoke   │   │ each invoke   │
└───────────────┘   └───────────────┘   └───────────────┘

Each subagent: ~/.claude/agents/artifact-review/artifact-review-p*.md
```

**Key insight**: Subagents spawn with ZERO context. They only know their system prompt + whatever the prime agent explicitly provides. This isolation is intentional—fresh eyes catch what familiar eyes miss.

---

## The Five Phases

| # | Subagent | What It Does | Key Principle |
|---|----------|--------------|---------------|
| 1 | `self-review-p1-generate` | Produces critical questions | No Quota Theater |
| 2 | `self-review-p2-organize` | Groups into thematic sets | Focused Execution |
| 3 | `self-review-p3-execute` | Answers questions, identifies gaps | Intellectual Honesty |
| 4 | `self-review-p4-revise` | Surgical edits to address gaps | Right-Sized Rigor |
| 5 | `self-review-p5-verify` | Final coherence check | Autonomous Quality |

**Flow**:
```
P1 → P2 → [P3 → P4] × N sets → P5 → Final Summary
```

P3 can run in parallel for multiple sets (if gathering findings before revisions).
P4 must run sequentially (to avoid edit conflicts).

---

## Cognitive Expectations

**This is demanding cognitive work.**

Do not breeze through this to check a box. Self-review requires deep, careful thinking—the kind where you slow down, reason deliberately, and challenge assumptions.

**Put your ultrathink cap on.** Think out loud. Surface reasoning explicitly.

**There is zero time pressure.** The protocol exists precisely so you take that time before handoff, not after problems emerge downstream.

**Slow and methodical beats fast and superficial.** A review that finds two real gaps is infinitely more valuable than a review that finds nothing because you weren't really looking.

---

## Invocation Options

### Basic
```bash
/artifact-review ./docs/architecture.md
```

### With Intensity
```bash
/artifact-review ./docs/plan.md quick      # 6-10 questions, critical only
/artifact-review ./docs/plan.md standard   # 15-25 questions (default)
/artifact-review ./docs/plan.md thorough   # 25-40 questions, full polish
```

### With Focus Areas
```bash
/artifact-review ./docs/api.md thorough security
/artifact-review ./docs/design.md standard accuracy,feasibility
```

### Special Artifact References
```bash
/artifact-review last                      # Last significant artifact in conversation
/artifact-review above                     # Content immediately above command
/artifact-review "the implementation plan" # Agent identifies from context
```

---

## What You'll See

**Progress updates**:
```
Starting self-review of architecture.md...
Phase 1: Generating questions... (invoking P1 subagent)
Phase 1 complete: 18 questions generated
Phase 2: Organizing into sets... (invoking P2 subagent)
Phase 2 complete: 4 sets organized
Executing Set 1: Architecture Fundamentals...
[continues...]
```

**Final output**:
```
SELF-REVIEW COMPLETE

Artifact: architecture.md
Sets reviewed: 4
Questions answered: 18
Gaps identified: 7 (Critical: 1, Significant: 4, Minor: 2)
Revisions made: 6
Validated as correct: 11

Status: Ready for handoff

Key changes:
- Added error handling for edge case X
- Clarified ambiguous requirement in Section 3
- Fixed contradiction between sections 5 and 7
```

---

## Important Concepts

### Subagent Zero-Context Reality

Every subagent spawns completely fresh:
- No conversation history
- No project knowledge
- No artifact awareness
- Only: system prompt + explicit context from prime agent

**Implication**: The prime agent must prepare comprehensive context for each subagent, including the Operating Principles relevant to that phase.

### Severity Ratings

| Severity | Meaning | Action |
|----------|---------|--------|
| Critical | Blocks artifact's primary purpose | Must fix |
| Significant | Materially weakens artifact | Should fix |
| Minor | Polish issue | Fix if time permits |

**Calibration**: Critical should be rare. Significant is typical for real issues.

### "Validated as Correct"

When a question reveals no gap, it's logged as "validated as correct" with justification. This is valuable—it's evidence of thorough examination, not absence of work.

---

## File Locations

```
~/.claude/
├── skills/artifact-review/
│   ├── SKILL.md                 ← Orchestration instructions (Skill)
│   ├── README.md                ← This file
│   └── PROTOCOL-ALTERATIONS.md  ← Change history
├── agents/artifact-review/
│   ├── self-review-p1-generate.md   ← Question generation (Subagent)
│   ├── self-review-p2-organize.md   ← Set organization (Subagent)
│   ├── self-review-p3-execute.md    ← Set execution (Subagent)
│   ├── self-review-p4-revise.md     ← Revision (Subagent)
│   └── self-review-p5-verify.md     ← Verification (Subagent)
└── commands/
    └── artifact-review.md       ← Slash command entry point
```

---

## When to Use vs Skip

**Use for**:
- Design documents
- Implementation plans
- Architecture decisions
- Problem models
- Complex analyses
- Anything referenced by others

**Skip for**:
- Commit messages
- Quick comments
- Exploratory brainstorms
- Simple code changes
- Throwaway artifacts

**Rule of thumb**: If flaws have downstream cost, review. If disposable, skip.

---

## Duration Expectations

| Intensity | Typical Duration |
|-----------|------------------|
| Quick | 3-5 minutes |
| Standard | 8-15 minutes |
| Thorough | 15-25 minutes |

---

## Troubleshooting

**"Not enough questions"**: Artifact may be too simple for formal review. Agent will suggest lightweight verification.

**"Subagent returned malformed output"**: Agent will retry with clearer instructions.

**"Phase failed after 2 attempts"**: Agent will escalate to you for guidance.

**Review taking too long**: Consider using `quick` intensity or reviewing sections independently.

---

## Why This Works

This process forces systematic critical examination before anyone else has the chance to find problems. It surfaces blind spots. It catches premature convergence. It prevents both over-engineering and lazy shortcuts.

Artifacts that pass this review are clearer, more complete, and more actionable. They require fewer revision cycles downstream. They build trust through demonstrated quality.

**The investment is small. The payoff compounds.**

---

## The Trust Proposition

```
Agent completes artifact
        ↓
Self-review verifies quality (auditable)
        ↓
You see evidence of verification
        ↓
Trust increases
        ↓
Agent autonomy can increase
        ↓
More valuable work delegated
        ↓
[Cycle continues]
```

Self-review is the mechanism that makes increased autonomy safe. Consistent quality demonstration → earned trust → expanded scope.

---

*System implemented 2026-01-06*

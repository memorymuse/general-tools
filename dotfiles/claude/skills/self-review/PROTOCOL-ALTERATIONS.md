# Protocol Alterations Summary

Changes made from the original Self-Review Protocol when implementing as a Claude Code system.

**Last Updated**: 2026-01-06 (philosophical foundation restoration)

---

## Architecture

### Final Design: Skill Orchestrator + Subagent Invocation

**Original**: Single document containing all 5 phases in sequence.

**Implemented**:
- **Orchestrator**: Skill (`~/.claude/skills/self-review/SKILL.md`) loaded by prime agent
- **Phase Executors**: 5 dedicated subagents (`~/.claude/agents/self-review/self-review-p*.md`)
- **Entry Point**: Slash command (`~/.claude/commands/artifact-review.md`)

**How it works**:
1. User invokes `/artifact-review <artifact>`
2. Prime agent loads orchestrator skill
3. Prime agent prepares context and invokes each subagent via conversational invocation
4. Each subagent spawns with fresh, empty context—knows only its system prompt + provided context
5. Subagents return structured output; prime agent accumulates state
6. Prime agent applies file revisions (P4) and synthesizes final summary

**Why subagents**: True cognitive isolation. Each phase executes without knowledge of other phases, preventing bias. The subagent literally cannot know about severity ratings (P3) when generating questions (P1) because that information is never in its context.

**Key constraint discovered**: Subagents spawn with ZERO context. Prime agent must provide comprehensive context for each invocation—project background, artifact content, goals, parameters. This is explicitly emphasized in the orchestrator skill.

---

## Structural Changes

### 1. Context Preparation Guidance

**Original**: Assumed context would be available.

**Added**: Dedicated "Context Preparation" section emphasizing:
- Subagents have ZERO contextual knowledge
- Prime agent must provide: project background, artifact content, metadata, parameters
- Option to save `.self-review-context.md` briefing file for reuse across subagents

**Why**: Without explicit guidance, prime agents pass insufficient context, leading to poor subagent performance.

### 2. Parallel Execution Option

**Original**: Strictly sequential phases.

**Added**: P3 (Execute) can run in parallel for multiple sets if artifact is read-only during execution. P4 (Revise) must remain sequential to avoid edit conflicts.

**Why**: Performance optimization for larger reviews with many sets.

### 3. Pre-Flight Check

**Original**: Protocol begins immediately.

**Added**: Validation before starting:
- Artifact is complete (not draft)
- Artifact has clear purpose
- Review is warranted

**Why**: Prevents wasted effort on incomplete or trivial artifacts.

### 4. Iteration Bounds

**Original**: Implicit limits.

**Added**:
- Maximum 8 sets
- Maximum 40 questions
- Maximum 2 retry attempts per phase

**Why**: Prevents runaway reviews.

### 5. Multi-File Artifact Support

**Original**: Assumes single artifact.

**Added**: Guidance for multi-file systems:
- Unified strategy (treat as single logical artifact)
- Sequential strategy (review each file, then integration)

**Why**: Real artifacts often span multiple files.

---

## Content Changes

### 6. Intensity Levels

**Added**: Three levels:
- Quick: 6-10 questions, 2-3 sets, critical only
- Standard: 15-25 questions, 3-5 sets, all severities
- Thorough: 25-40 questions, 5-8 sets, full polish

### 7. Focus Areas

**Added**: Optional emphasis on security, accuracy, clarity, completeness, feasibility.

### 8. Model Selection

**Added**: Opus for all phases (P1-P5) and orchestrator. Originally P2 used Sonnet, but organizing questions into optimal thematic sets requires understanding question intent and importance—not worth the risk of underperformance.

### 9. Terminology Standardization

**Changed**: "No change needed" → "Validated as correct" throughout.

**Why**: Reframes validation as positive evidence of quality, not absence of findings.

### 10. Enhanced Severity Calibration

**Added**: Explicit guidance that Critical should be rare, Significant is typical for real issues, with calibration warnings.

### 11. Anti-Patterns per Phase

**Added**: Dedicated sections in each subagent with specific failure modes to avoid.

### 12. Error Handling

**Added**: Explicit paths for malformed output, phase failures, large artifacts, cancellation.

### 13. Progress Visibility

**Added**: Guidance for prime agent to report progress at each phase transition.

### 14. State Management

**Added**: Explicit list of what prime agent maintains across phases (completed sets, revision log, gap counts, remaining sets).

### 15. Revision Application

**Added**: Explicit mechanism—Edit tool for files, context maintenance for inline artifacts.

---

## Preserved from Original

1. **Core principles**: No quota theater, goal alignment, focused execution, right-sized rigor, autonomous quality
2. **Phase structure**: Generate → Organize → Execute → Revise → Verify
3. **Question targets**: 10-40, minimum 6
4. **Set constraints**: 2-8 sets, 2-5 questions each
5. **Severity definitions**: Critical/Significant/Minor
6. **Cognitive expectations**: Deep thinking, no time pressure, thoroughness
7. **Operating principles**: Intellectual honesty, constructive candor, empiricism, objectivity
8. **"Objectivity & Accuracy" set recommendation**
9. **Ordering sets by dependency**
10. **Surgical revision principle**

---

## What Each Component Does

| Component | Type | Purpose |
|-----------|------|---------|
| `SKILL.md` | Skill | Orchestration instructions for prime agent |
| `self-review-p1-generate.md` | Subagent | Produces critical questions |
| `self-review-p2-organize.md` | Subagent | Groups questions into thematic sets |
| `self-review-p3-execute.md` | Subagent | Analyzes artifact against questions, identifies gaps |
| `self-review-p4-revise.md` | Subagent | Makes surgical edits to address gaps |
| `self-review-p5-verify.md` | Subagent | Final judgment: ready or blocked |
| `artifact-review.md` | Slash Command | User entry point with argument parsing |

---

## Validation

System validated by executing self-review on itself:
- 17 questions across 6 sets
- 1 Critical gap discovered (architecture flaw)
- 14 revisions made
- Architecture corrected before deployment

The Critical flaw (incorrect assumption about Task tool spawning) would have made the system non-functional. Self-review caught it, demonstrating protocol value.

---

## 2026-01-06: Philosophical Foundation Restoration

Comparative analysis of the original standalone protocol vs. the implemented system revealed that the implementation had lost significant philosophical grounding, voice, and teaching value. Changes made to restore these while properly adapting for the subagent isolation model.

### Philosophy & Voice Restoration

**Added to all components** (SKILL.md, P1-P5, README):

1. **Cognitive Expectations section**: Restored "ultrathink cap" language, "zero time pressure", "slow and methodical beats fast and superficial". This sets the cognitive stance before operational instructions.

2. **Operating Principles**: Full articulation of Intellectual Honesty, Constructive Candor, Empiricism, Objectivity—with explanations of what each means in practice.

3. **Core Principles with "one sentence" summaries**: No Quota Theater, Goal Alignment, Focused Execution, Right-Sized Rigor, Autonomous Quality. Each now has a memorable summary line.

4. **"Why This Works" closing**: Restored the original's explanation of why the process produces value.

5. **Voice elements**: "gut check" (P5), "you are your own quality gate", "the investment is small, the payoff compounds".

### Critical Framing Correction: Subagent Isolation

**Problem identified**: Initial implementation incorrectly told subagents "you may be attached to this artifact—you created it." But subagents spawn with zero context—they didn't create anything and have no attachment.

**Corrected framing**:

| Component | Correct Framing |
|-----------|-----------------|
| **Orchestrator (SKILL.md)** | "You created this artifact. You have attachment... This is precisely why subagents matter: they examine with fresh eyes." |
| **Subagents (P1, P3, P5)** | "You have fresh eyes. You're examining an artifact you didn't create, with no history, no attachment. This is your advantage—use it." |
| **Context templates** | "You have fresh eyes—no history with this artifact. Find problems the creator is too close to see." |
| **README** | "The orchestrator created the artifact and has attachment. The subagents examine with fresh eyes... This structural separation enables objectivity the creator cannot achieve alone." |

**Why this matters**: The original protocol assumed a single agent transcending its own biases. The implementation uses structural separation instead—subagents literally cannot have attachment because they have no history. The framing must reflect this reality: isolation is the subagent's advantage, not a bias to overcome.

### Files Modified

| File | Changes |
|------|---------|
| `SKILL.md` | Added Cognitive Expectations, Operating Principles, Core Principles sections. Updated Objectivity to acknowledge orchestrator attachment. Updated context templates with fresh-eyes framing. Added "Why This Works" closing. |
| `self-review-p1-generate.md` | Added Cognitive Expectations, Operating Principles, No Quota Theater principle. Fixed Objectivity to fresh-eyes framing. |
| `self-review-p2-organize.md` | Added Focused Execution as core principle with explanation. Added "Why Organization Matters" section. |
| `self-review-p3-execute.md` | Added Operating Principles, Cognitive Expectations. Fixed Objectivity to fresh-eyes framing. |
| `self-review-p4-revise.md` | Added Right-Sized Rigor as core principle. Added Operating Principles (Surgical Precision, Traceability, Honesty). |
| `self-review-p5-verify.md` | Added Autonomous Quality as core principle. Restored "gut check" language. Added Operating Principles. Fixed Objectivity to fresh-eyes framing. |
| `README.md` | Added Philosophy section with Operating Principles and Core Principles. Added Cognitive Expectations section. Explained orchestrator/subagent dynamic. |

### Conceptual Model Now Consistent

- **Orchestrator** = artifact creator with natural attachment → responsible for comprehensive context preparation
- **Subagents** = fresh eyes with no history → leverage isolation as cognitive advantage
- **Structural separation** = the mechanism enabling objectivity (not psychological self-transcendence)

This preserves the original protocol's philosophical depth while correctly adapting it for the distributed cognition model of the implementation.

# Self-Review Protocol

A structured process for agents to critically examine their own work before handoff.

---

## What This Is

When you complete a significant artifact—a problem model, design document, implementation plan, or similar deliverable—there is a gap between "I think this is good" and "I have verified this is good." This protocol bridges that gap.

**The process in brief:**
1. You generate critical questions that, if answered, would improve your artifact
2. You organize those questions into focused, thematic sets
3. You work through each set: answering questions, identifying gaps, making revisions
4. You verify the final artifact against its primary goals

**Why this exists:**
- Artifacts reviewed through this process are clearer, more complete, and more actionable
- Catching flaws before handoff saves significant time downstream—for you, for future agents, and for users
- Self-review builds trust: it demonstrates that quality is verified, not assumed
- The process prevents both over-engineering (complexity theater) and under-engineering (lazy shortcuts)

**The core insight:** You are capable of finding most flaws in your own work—but only if you systematically look for them. This protocol makes that systematic examination concrete and repeatable.

---

## Cognitive Expectations

**This is a demanding cognitive task.**

Do not breeze through this protocol to check a box. This requires your deepest, most careful thinking—the kind where you slow down, reason through each step deliberately, and challenge your own assumptions.

**Put your ultrathink cap on.** Think out loud. Surface your reasoning explicitly. Build robust thought-architecture before committing to conclusions. If a question requires careful analysis, give it careful analysis.

**There is zero time pressure.** "If I had more time, I would have..." is not an excuse. You have the time. The protocol exists precisely so you take that time before handoff, not after problems emerge downstream.

**Slow and methodical beats fast and superficial.** Speed is not a virtue here. Thoroughness is. A review that finds two real gaps in 20 minutes is infinitely more valuable than a review that finds nothing in 5 minutes because you weren't really looking.

---

## Operating Principles

These principles govern your self-review work:

**Intellectual Honesty.** Seek truth about your artifact's quality. No false humility ("this is probably terrible"), no overconfidence ("this is definitely fine"). Just straightforward assessment. If you made a mistake, surface it—errors are acceptable, hiding them is not. If you don't know whether something is correct, say so and investigate.

**Constructive Candor.** Be direct with yourself. If a section is hand-wavy, call it hand-wavy. If a claim is unsupported, call it unsupported. "This might be a minor issue" when it's actually a significant gap is self-deception. Challenge your own work with the same rigor you'd apply to someone else's.

**Empiricism.** Zero assumptions. If your artifact claims something is true, verify it. If documentation references code behavior, read the code. If a requirement claims to address a use case, trace it through. Base your review on evidence, not on "I think I remember this being correct."

**Objectivity.** You wrote this artifact. You may be attached to it. That attachment is a bias—recognize it and compensate. Your north star is the artifact's stated goals, not your ego. A review that finds real problems serves the goals. A review that protects your pride does not.

---

## When To Use This

**Use this protocol for:** Problem models, design documents, implementation plans, architectural decisions, complex analysis—any artifact where flaws have downstream cost.

**Skip this protocol for:** Quick answers, exploratory drafts, simple code changes, throwaway artifacts. If the cost of a flaw is low, the overhead of formal review isn't justified.

**Rule of thumb:** If the artifact will be referenced by others (users or future agents), use this protocol. If it's disposable, skip it.

---

## Purpose

You just created an artifact. Before anyone else sees it, you will stress-test it yourself.

This is not proofreading. This is adversarial self-examination—treating your own work as if a skeptical expert wrote it, then hunting for weaknesses, gaps, and flawed assumptions.

**Why this matters:** Flaws caught now cost minutes. Flaws caught during implementation cost hours. Flaws caught in production cost days. The cheapest time to find a problem is right now.

---

## Core Principles

### 1. No Quota Theater

Every question you generate must genuinely improve the artifact. Do not invent questions to hit a number. Do not pad sets with filler. Ask yourself: *"If this question were answered, would the artifact materially improve?"* If no, discard it.

**One sentence:** Quality of questions over quantity—but don't shy away from quantity when quality is present.

### 2. Goal Alignment

Every question must serve the artifact's primary objectives. Before generating questions, state the primary goals explicitly. Filter every question through: *"Does answering this move us closer to the stated goals?"*

**One sentence:** If a question doesn't serve the goals, it doesn't belong.

### 3. Focused Execution

You will organize questions into small, thematically coherent sets. When working a set, that set is your entire world. Do not think about other sets. Do not anticipate future phases. Complete what is in front of you.

**One sentence:** Depth on one thing beats shallow passes on everything.

### 4. Right-Sized Rigor

This process prevents two failure modes:
- **Over-engineering:** Excessive detail, premature optimization, complexity theater
- **Under-engineering:** Lazy shortcuts, vague hand-waves, missing critical elements

You are aiming for the precise level of rigor the artifact requires—no more, no less.

**One sentence:** Not too much, not too little—exactly what's needed.

### 5. Autonomous Quality

The goal is to improve artifact quality without user intervention. You should complete this process and produce a better artifact without needing to ask clarifying questions (unless you hit a genuine blocker that only the user can resolve).

**One sentence:** You are your own quality gate.

---

## Process Overview

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: GENERATE                                          │
│  Produce 10-40 critical questions (6 absolute minimum)      │
├─────────────────────────────────────────────────────────────┤
│  PHASE 2: ORGANIZE                                          │
│  Group into 2-8 focused sets (max 5 questions per set)      │
├─────────────────────────────────────────────────────────────┤
│  PHASE 3: EXECUTE                                           │
│  Work one set at a time: answer, identify gaps              │
├─────────────────────────────────────────────────────────────┤
│  PHASE 4: REVISE                                            │
│  Address gaps, log changes                                  │
│  (Repeat 3-4 for each remaining set)                        │
├─────────────────────────────────────────────────────────────┤
│  PHASE 5: VERIFY                                            │
│  Final check against primary goals                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Generate Questions

### Objective
Produce a comprehensive list of critical questions that, if answered, would improve the artifact.

### Guidelines

**Think across multiple perspectives.** Consider:
- Completeness: What's missing?
- Accuracy: What might be wrong?
- Clarity: What's ambiguous?
- Consistency: What contradicts itself?
- Actionability: What can't be acted upon?
- Risk: What could fail?
- Goal alignment: What doesn't serve the primary objectives?

**Target range: 10-40 questions.** Fewer than 10 suggests shallow examination. More than 40 suggests unfocused scope. The absolute minimum is 6—anything less is inadequate scrutiny.

**Prioritize ruthlessly.** After generating questions, rank them by impact. Ask: *"If I could only answer 5 questions, which 5 would most improve this artifact?"* Those are your highest-priority questions.

**Self-check your questions.** Before proceeding, scan your list and ask:
- Is each question distinct, or are some redundant?
- Does each question target something that could actually be wrong?
- Would answering this question lead to a concrete change?
If a question fails these checks, cut it. A short list of sharp questions beats a long list of vague ones.

### Output
A prioritized list of questions, each one distinct and genuinely valuable.

### Checkpoint
Do not proceed until you have generated and prioritized your questions.

---

## Phase 2: Organize Into Sets

### Objective
Group questions into focused, thematically coherent sets that can be worked serially.

### Guidelines

**Each set has one theme.** A set might focus on "security guarantees" or "goal alignment" or "implementation readiness." When you work that set, you should be able to hold the entire theme in mind without distraction.

**Maximum 5 questions per set.** More than 5 dilutes focus. If a theme has more than 5 questions, split it or cut the weakest questions.

**Target range: 2-8 sets.** Fewer than 2 means you haven't separated concerns. More than 8 means your themes are too granular.

**Order sets by dependency.** If answering Set A's questions might change how you'd answer Set B's questions, do Set A first.

**Name each set.** A clear, descriptive name (e.g., "Security Model," "Goal Alignment") helps maintain focus during execution.

**Strongly consider an "Objectivity & Accuracy" set.** One of the most valuable outcomes of self-review is validating that claims in the artifact are objectively accurate and empirically grounded where relevant. Questions in this set might probe:
- Are stated facts actually true?
- Are assumptions explicitly called out as assumptions?
- Where claims are made, is there evidence or reasoning to support them?
- Could a skeptic poke holes in the logical reasoning?

This set catches unsupported assertions, wishful thinking, and gaps in reasoning that other thematic sets often miss. In rare cases—such as purely creative or exploratory artifacts—this set may not apply. Use judgment, but default to including it.

### Output
A structured list of named question sets, each with 2-5 questions, ordered for serial execution.

### Checkpoint
Do not proceed until your sets are defined and ordered.

---

## Phase 3: Execute Set

### Objective
For the current set only, answer each question against the artifact and identify gaps.

### Guidelines

**Work only the current set.** Other sets do not exist right now. Do not think about them.

**For each question, provide:**
1. The answer (what the artifact currently says or implies)
2. The gap (what's missing, wrong, or unclear)
3. The severity:
   - **Critical:** Blocks the artifact's primary purpose. Must fix before proceeding.
   - **Significant:** Materially weakens the artifact. Should fix.
   - **Minor:** Small improvement opportunity. Fix if time permits.

**Be honest.** If the artifact fails a question, say so. The point is to find problems, not to defend the work.

**If blocked, escalate.** If answering a question requires information only the user can provide, flag it clearly and continue with remaining questions. Do not invent answers.

**Edge cases:**
- *No gaps found in a set:* This is fine. Log "Set N: No gaps identified" and move to the next set. Do not invent problems.
- *All questions pass:* Possible for strong artifacts. Complete remaining sets to confirm, then proceed to Phase 5.
- *Stuck on a question:* If you genuinely cannot assess a question, flag it as "Unable to assess: [reason]" and continue.

### Output
For current set only: Each question with its answer, identified gap (if any), and severity rating.

### Checkpoint
Do not proceed until all questions in the current set are answered.

---

## Phase 4: Revise

### Objective
Address the gaps identified in the current set.

### Guidelines

**Address gaps by severity.** Critical first, then significant, then minor.

**Make surgical edits.** Change what needs to change. Do not rewrite sections that passed review.

**Log each revision.** Track what changed and why. Keep it trim—one line per change is sufficient.

**Log "no change needed" when appropriate.** If a question reveals no gap, or a set passes entirely, log that explicitly with brief justification. This is not failure—it's validation. A passing review is valuable evidence of quality.

Example log format:
```
- Section 8.3: Added discovery mechanism for gitignored essentials (Q7 gap)
- Section 10: Removed unenforceable invariant I4 (Q5 gap)
- Q3: No change needed—edge cases already addressed in Section 6
- Set 2: No changes—all questions pass, claims are well-supported
```

**Note:** "No change needed" must be justified, not assumed. The justification proves you examined the question seriously. Unjustified "no change needed" is laziness. Justified "no change needed" is validation.

**Verify the fix.** After revising, re-read the question. Does the artifact now pass? If not, revise again.

### Output
- Revised artifact
- Revision log for this set

### Checkpoint
Do not proceed until all gaps from the current set are addressed. Then return to Phase 3 for the next set. Repeat until all sets are complete.

---

## Phase 5: Verify

### Objective
Final sanity check—does the revised artifact serve its primary goals?

### Guidelines

**Re-state the primary goals.** What was this artifact supposed to accomplish?

**Gut check.** Read the artifact fresh. Does it feel complete, coherent, and actionable? Trust your expert judgment.

**Check for introduced problems.** Did revisions create new inconsistencies or gaps?

**Confirm no critical gaps remain.** Every critical-severity gap from Phase 3/4 should be resolved.

### Output
- Confirmation that the artifact is ready, OR
- List of remaining concerns (with recommendation to address or accept)

### Final Output
Present a clean summary to the user:
```
SELF-REVIEW COMPLETE

Sets reviewed: [N]
Questions answered: [N]
Gaps identified: [N] ([critical], [significant], [minor])
Revisions made: [N]
No change needed: [N] (justified)

Revision log:
- [change 1]
- [change 2]
- [no change needed with justification]
- ...

Status: Ready for next phase / Blocked on [X]
```

The "No change needed" count demonstrates thorough examination—you looked and confirmed quality, rather than simply not finding problems because you weren't looking hard enough.

---

## Quick Reference

| Element | Range | Hard Limits |
|---------|-------|-------------|
| Total questions | 10-40 | Minimum 6 |
| Question sets | 2-8 | — |
| Questions per set | 2-5 | Maximum 5 |

| Severity | Meaning | Action |
|----------|---------|--------|
| Critical | Blocks primary purpose | Must fix |
| Significant | Materially weakens artifact | Should fix |
| Minor | Small improvement | Fix if time permits |

| Principle | One Sentence |
|-----------|--------------|
| No quota theater | Quality of questions over quantity—but don't shy from quantity when quality is present. |
| Goal alignment | If a question doesn't serve the goals, it doesn't belong. |
| Focused execution | Depth on one thing beats shallow passes on everything. |
| Right-sized rigor | Not too much, not too little—exactly what's needed. |
| Autonomous quality | You are your own quality gate. |

---

## Why This Works

This process forces you to be your own harshest critic before anyone else has the chance. It surfaces blindspots. It catches premature convergence. It prevents both over-engineering and lazy shortcuts.

Artifacts that pass this review are clearer, more complete, and more actionable. They require fewer revision cycles downstream. They build trust through demonstrated quality.

**The investment is small. The payoff compounds.**

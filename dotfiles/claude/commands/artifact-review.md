---
description: Conduct systematic self-review of an artifact before handoff
allowed-tools: Read, Edit, Glob, Grep, Task
argument-hint: <artifact> [intensity] [focus]
---

# Self-Review Invocation

Invoke the self-review protocol to systematically examine an artifact before handoff.

## Arguments

**$1 - Artifact** (required):
- **File path**: `/path/to/artifact.md` — Review that specific file
- **"last"**: Review the most recent significant artifact YOU produced in this conversation (you must identify what that was)
- **"above"**: Review the content immediately preceding this command in the conversation
- **Description**: `"the implementation plan"` — Identify and review the described artifact from context

**$2 - Intensity** (optional, default: standard):
- **quick** / **q**: Lightweight review (6-10 questions, 2-3 sets, critical issues only)
- **standard** / **s**: Full review (15-25 questions, 3-5 sets, all severities)
- **thorough** / **t**: Deep examination (25-40 questions, 5-8 sets, full polish)

**$3 - Focus** (optional):
Comma-separated areas to emphasize:
- **security**: Authentication, authorization, vulnerabilities
- **accuracy**: Factual correctness, evidence for claims
- **clarity**: Readability, ambiguity, structure
- **completeness**: Gaps, missing elements, edge cases
- **feasibility**: Implementation risks, dependencies

## Your Arguments

```
Artifact:  $1
Intensity: $2
Focus:     $3
```

## What to Do

1. **Parse arguments**: Interpret according to the rules above

2. **Identify the artifact**:
   - If file path: Confirm file exists
   - If "last": Identify the most recent significant artifact you produced
   - If "above": Identify content immediately above this command
   - If description: Locate the matching artifact in conversation

3. **Load the self-review skill**: Read `~/.claude/skills/self-review/SKILL.md`

4. **Follow the orchestration protocol**:
   - Prepare context for each subagent (CRITICAL: they have ZERO context without it)
   - Invoke subagents in sequence: P1 → P2 → [P3 → P4 loop] → P5
   - Apply revisions for file-based artifacts
   - Synthesize final results

5. **Present summary to user** when complete

## Examples

```bash
/artifact-review ./docs/architecture.md
# Standard review of architecture.md

/artifact-review ./docs/architecture.md quick
# Quick review, critical issues only

/artifact-review ./docs/architecture.md thorough security
# Deep review with security focus

/artifact-review last
# Standard review of last significant artifact in this conversation

/artifact-review "the implementation plan" standard accuracy,feasibility
# Review the implementation plan with focus on accuracy and feasibility
```

## Quick Reference

| Intensity | Questions | Sets | Minor Gaps |
|-----------|-----------|------|------------|
| quick     | 6-10      | 2-3  | Skip       |
| standard  | 15-25     | 3-5  | Address    |
| thorough  | 25-40     | 5-8  | Full polish|

## Begin

Load the self-review skill and begin orchestration. Keep the user informed of progress at each phase transition.

# Session Handoff: Problem Model Complete

**Date**: 2025-01-05
**Focus**: Problem modeling for env-sync expanded vision

---

## What This Project Is

**devenv** is a cross-machine environment synchronization tool. The user works on a MacBook (macOS) and Desktop (Windows 11 + WSL/Ubuntu), switching between them daily/weekly.

**The core pain**: Every gitignored-but-essential file (`.env`, provider configs, Claude Code settings, auth tokens) must be manually reconstructed on each machine switch. This friction adds up.

**The north star**: "Instant redeploy" - clone the sync repo, run `devenv pull`, enter password, and every project is immediately functional. No "setup day."

---

## Current State vs Vision

There's an **existing implementation** (documented in README.md) and an **expanded vision** (VISION.md + PROBLEM-MODEL.md).

**Existing system provides**:
- Manual vault management (`devenv vault export/encrypt/decrypt`)
- Push/pull commands
- Claude Code config sync (static list of items)
- Tools manifest and installation
- Profile/mount system for bash isolation

**Vision expands to include**:
- Auto-discovery of gitignored essentials across all projects
- User validation workflow (discovery is permissive, validation is restrictive)
- Conflict detection and resolution (LLM-assisted via `/devenv-resolve`)
- Completeness verification for Claude Code (detect new config locations automatically)
- Project path mapping (same project, different paths per machine)
- Defense-in-depth security (multiple safeguards, not just encryption)

---

## What Was Done This Session

1. **Created VISION.md** - User-perspective narrative capturing the problem and desired experience

2. **Created PROBLEM-MODEL.md** - Comprehensive problem model (v1.9, ~950 lines) covering:
   - Problem statement and context
   - Hard/soft constraints
   - 8 functional requirements, 5 non-functional requirements
   - 8 use cases
   - Data model (conceptual)
   - State models (illustrative, not prescriptive)
   - Invariants with strictness levels
   - Success criteria
   - Risk analysis with complexity guardrails
   - Performance considerations

3. **Rigorous review** - Executed 5 question sets (18 total questions) covering:
   - Goal alignment
   - Security model
   - Capture model
   - Implementation readiness
   - Performance & discovery efficiency

4. **Updated README.md** - Added "Project Status & Vision" section clarifying the gap between current and vision

---

## How the Problem Model Is Designed & Intended to Be Used

The problem model is **solution-agnostic** - it describes *what* problem we're solving, not *how* to solve it.

**Key sections for the designer**:
- **Section 4 (Constraints)**: Non-negotiable requirements (HC1-HC7) and strong preferences (SC1-SC5)
- **Section 5 (Requirements)**: FR1-FR8 define what the system must do
- **Section 8.3-8.4 (Discovery & Validation)**: Critical insight - discovery must be permissive, validation restrictive
- **Section 10 (Invariants)**: Properties the system must enforce
- **NFR1 (Performance)**: Scale context (10→50+ projects), key concerns, discovery shortcuts

**What's explicitly NOT prescriptive**:
- Section 9 (State Models) - marked as illustrative suggestions only
- Section 8.1 (Data Model) - conceptual entities, not implementation schema
- Section 10 Strictness column - severity levels, not enforcement mechanisms

**Open Questions (Section 17)** require design-time decisions - they're scope boundaries to close, not features to add.

---

## Critical Decision for Next Agent

**You must make an upfront decision**: Design a fresh, new system or build on the existing implementation?

This requires **thorough evaluation of the current system**:
- Read the README.md to understand what exists
- Examine `bin/cc-isolate` for the actual implementation
- Assess: How much of the existing code serves the expanded vision?
- Consider: Is the current architecture extensible, or would it accumulate tech debt?

**Arguments for fresh start**:
- Current system is manual-centric; vision is auto-discovery-centric
- Adding auto-discovery may require architectural changes throughout
- Cleaner to design for the vision than retrofit existing code

**Arguments for building on existing**:
- Working push/pull, vault, encryption already exist
- User familiarity with current commands
- Less risk of breaking what works

This is a **significant architectural decision** - don't rush it.

---

## Key Nuances & Insights

### Discovery vs Validation
The system must find gitignored essentials automatically. Critical insight: **discovery should be permissive** (find everything plausible, err toward false positives), **validation should be restrictive** (user narrows down). An implementation that restricts at discovery time will under-capture.

### Performance at Scale
- Currently ~10 projects, will grow to 50+
- Discovery runs automatically on every push (must be fast)
- Key concern: accidentally descending into `node_modules/` would be catastrophic
- `~/.claude/projects/` is a potential discovery shortcut, but it only tracks invocation roots, not nested sub-projects

### Nested Sub-Projects
A repo like `general-tools/` contains multiple independent sub-projects (`env-sync/`, `filedet/`, etc.), each with their own dotfiles. The design must handle essentials at multiple depth levels within a single repo.

### Content Inspection
May be needed in rare cases (ambiguous file types, detecting secrets in non-obvious locations), but should be the exception. Path/name-based identification handles most cases.

### Technology Constraints (User-Specified)
- Git-based transport and storage
- Password-based encryption (age)
- Bash-based (not bash/zsh split)

These are decisions already made, not design options.

---

## Required Reading

1. **[`docs/PROBLEM-MODEL.md`](../PROBLEM-MODEL.md)** - The foundation for design work
2. **[`docs/VISION.md`](../VISION.md)** - User perspective and scenarios
3. **[`../README.md`](../../README.md)** - Current implementation (evaluate for reuse)

## Suggested Reading

- **[`docs/REVIEW-QUESTIONS.md`](../REVIEW-QUESTIONS.md)** - Questions used to review the problem model
- **`bin/cc-isolate`** - Current implementation code

---

## Files Modified This Session

| File | Change |
|------|--------|
| `docs/PROBLEM-MODEL.md` | Created and refined through v1.9 |
| `docs/VISION.md` | Created (prior to this session, reviewed) |
| `docs/REVIEW-QUESTIONS.md` | Created with 5 question sets |
| `README.md` | Added "Project Status & Vision" section |

---

## Remaining Work

1. **Design document** - Translate problem model into system design
2. **Implementation plan** - Sequenced implementation steps
3. **Implementation** - Build the expanded system

The design phase should produce architectural decisions, component breakdown, and interface definitions that satisfy the problem model requirements.

# Session Handoff: Design Phase Complete

**Date**: 2026-01-06
**Status**: Design complete, ready for implementation planning

---

## What This Project Is

**devenv** is a cross-machine environment synchronization tool. The user (Kyle) works on a MacBook (macOS) and Desktop (Windows 11 + WSL/Ubuntu), switching between them regularly.

**The core problem**: Every gitignored-but-essential file (`.env`, provider configs like `.vercel/`, Claude Code settings in `~/.claude/`, auth tokens) must be manually reconstructed when switching machines. This friction adds up to significant lost time.

**The goal**: One command (`devenv push` / `devenv pull`) + password = entire environment synced. "Instant redeploy" on a new machine.

---

## Current State: Two Systems

### 1. Existing Implementation (Working)
Location: `bin/cc-isolate` (~3,400 lines bash)

What it does today:
- Manual vault management (`devenv vault export/encrypt/decrypt`)
- Push/pull to git with encryption
- Claude Code config sync (static list of items)
- Tools manifest and installation
- Profile/mount system for bash isolation

**This is production code that Kyle uses today.**

### 2. Designed v2 System (Not Yet Built)
Location: `docs/design/`

What v2 adds:
- **Auto-discovery** of gitignored essentials (no manual vault export)
- **Manifest-driven** sync (YAML manifest tracks all state)
- **Conflict detection/resolution** with agent assistance
- **Python 3.10+** implementation (not bash)
- **Completeness verification** for Claude Code configs

**The design is complete. Implementation has not started.**

---

## Key Documents (Read in This Order)

| Priority | Document | Purpose | Lines |
|----------|----------|---------|-------|
| 1 | `docs/design/DECISIONS.md` | 16 architectural decisions with rationale | 795 |
| 2 | `docs/design/SYSTEM-DESIGN.md` | Component specs, interfaces, flows | 1,122 |
| 3 | `docs/PROBLEM-MODEL.md` | Requirements, constraints, use cases | 970 |
| 4 | `docs/design/SYSTEM-DESIGN-REVIEW.md` | Self-review log (what gaps were found/fixed) | 147 |
| 5 | `docs/VISION.md` | User perspective, scenarios | 150 |

**Do NOT read the existing `bin/cc-isolate` code as a reference for v2.** The bash implementation has different architecture. Use it only to understand what migration path is needed.

---

## Critical Context (Read Carefully)

### Decision D16: Python, Not Bash
The original constraint (HC7) was "bash-based." This was **superseded** by D16 after identifying fragility and maintainability concerns:
- Bash YAML parsing is error-prone
- Debugging is primitive (set -x only)
- Cross-platform edge cases are subtle

**v2 is Python 3.10+ with PyYAML.** Do not implement in bash.

### The Manifest Is Central
v2 is **manifest-driven**. The `devenv.yaml` file is the source of truth:
- What items are tracked
- Which machines exist
- Project path mappings
- Validation decisions
- Operation history

Every sync operation reads/updates the manifest. See Section 2.1 of SYSTEM-DESIGN.md for schema.

### Discovery Is Permissive, Validation Is Restrictive
The system auto-discovers gitignored essentials. Critical insight:
- **Discovery** should find everything plausible (err toward false positives)
- **Validation** lets the user narrow down (reject junk)

An implementation that restricts at discovery time will **silently miss essentials**. This is worse than showing junk that gets rejected.

### Agent-Assisted Conflict Resolution
When conflicts occur, the system writes to `staging/conflicts.yaml` and expects either:
1. An agent (via Claude Code skill) to read conflicts, write `staging/resolutions.yaml`
2. Manual fallback prompts if agent unavailable

See Section 3.3 of SYSTEM-DESIGN.md for the interface spec.

### Security: Defense in Depth
Four layers, not just encryption:
1. **Encryption**: age with password
2. **Pre-commit verification**: Check vault/ for plaintext before git add
3. **Audit scan**: gitleaks for historical exposure
4. **Recovery procedure**: Document what to rotate if exposed

See Section 6 of SYSTEM-DESIGN.md.

---

## What's Next: Implementation Planning

The design is complete. The next step is creating an **implementation plan** that:

1. Defines implementation phases/milestones
2. Sequences work (what depends on what)
3. Identifies the critical path
4. Specifies testing approach (TDD expected)

Suggested approach:
- Start with manifest manager and models (foundation)
- Add discovery engine (can test independently)
- Add crypto module (wrapper around age CLI)
- Build push flow (discovery → validation → encrypt → commit)
- Build pull flow (fetch → conflict detect → decrypt → deploy)
- Add CLI layer last

### Migration Consideration
Existing users (Kyle) have a working vault with `secrets.yaml.age`. The implementation needs a migration path from the current format to the new manifest structure. See Section 8.2 of SYSTEM-DESIGN.md.

---

## File Structure After Implementation

```
env-sync/
├── src/devenv/
│   ├── __init__.py
│   ├── cli.py              # Click or argparse CLI
│   ├── manifest.py         # Manifest operations
│   ├── discovery.py        # Discovery engine
│   ├── conflict.py         # Conflict detection/resolution
│   ├── validation.py       # Validation workflow
│   ├── crypto.py           # Encryption (calls age CLI)
│   ├── paths.py            # Path mapping
│   └── models.py           # Dataclasses
├── tests/
├── pyproject.toml
├── devenv.yaml             # Manifest (committed)
├── devenv.local.yaml       # Machine-specific (gitignored)
├── vault/                  # Encrypted content (committed)
└── staging/                # Temporary workspace (gitignored)
```

---

## Common Pitfalls to Avoid

1. **Don't conflate existing implementation with v2 design.** They have different architectures.

2. **Don't skip the manifest.** Every operation flows through it. If you're writing code that doesn't touch the manifest, question whether it's correct.

3. **Don't over-engineer discovery.** The algorithm in Section 3.2 is intentionally simple: `git ls-files --others --ignored --exclude-standard` + pattern matching + blocklist.

4. **Don't forget encryption verification.** Step 7 of push flow (Section 5.1) verifies no plaintext before commit. This is a hard requirement.

5. **Don't implement shell hooks.** There are none designed. This is a standalone CLI, not shell-integrated.

6. **Don't parse YAML manually.** Use PyYAML. This was a key reason for choosing Python.

---

## Questions? Context Missing?

If something is unclear or seems contradictory:
1. Check DECISIONS.md for rationale on specific choices
2. Check SYSTEM-DESIGN-REVIEW.md for gaps that were identified and how they were resolved
3. Ask Kyle to clarify before proceeding

**Proceeding on incorrect assumptions causes silent chaos.** When in doubt, verify.

---

## Files in This Commit

| File | Change |
|------|--------|
| `docs/design/SYSTEM-DESIGN.md` | Fixed section numbering (8.2.2, 8.2.3) |
| `docs/handoffs/250106-design-complete.md` | This handoff document |

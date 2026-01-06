# Design Decisions Log

This document captures architectural and design decisions for the env-sync/devenv system redesign. Each decision includes context, options considered, rationale, and consequences.

---

## D1: Build vs. Extend Architecture

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Hybrid approach - new core architecture with reused library primitives

### Context

The existing `cc-isolate` implementation (~3,400 lines) provides working functionality for vault management, git sync, and Claude Code config sync. However, the expanded vision (PROBLEM-MODEL.md) requires fundamentally different capabilities:

| Vision Requirement | Current Implementation |
|--------------------|----------------------|
| Auto-discovery of gitignored essentials | Manual configuration only |
| User validation workflow | None |
| Project path mapping | Assumes identical paths |
| Conflict detection/resolution | Silent overwrite |
| Machine registry | None |
| Completeness verification for Claude Code | Static hardcoded list |
| Manifest-driven sync | Command-driven sync |

### Options Considered

**Option A: Extend Existing**
- Add manifest system to existing push/pull commands
- Bolt on discovery to existing sync flow
- Retrofit conflict detection

*Pros*: Less initial work, preserves user familiarity
*Cons*: Architectural mismatch, accumulates complexity, harder to reason about

**Option B: Fresh Build**
- Rewrite everything from scratch
- New command structure, new data model

*Pros*: Clean architecture, native support for vision requirements
*Cons*: Duplicates working code (encryption, platform detection), higher risk

**Option C: Hybrid (Chosen)**
- New core architecture designed for the vision
- Reuse proven library primitives (`lib/platform.sh`, `lib/secrets.sh`, `lib/secrets-sync.sh`)
- New `bin/devenv` script with manifest-driven approach
- `cc-isolate` either deprecated or aliased to subset of commands

*Pros*: Clean architecture where it matters, reuses tested code, lower risk
*Cons*: Some refactoring of library code needed

### Decision

**Option C: Hybrid approach**

### Rationale

1. **Architecture matters more than code volume**: The vision requires a manifest-driven, discovery-based system. The current system is command-driven and explicit. These are fundamentally incompatible mental models.

2. **Libraries are sound**: The `lib/*.sh` files handle genuinely complex problems (cross-platform compatibility, age encryption, gitleaks integration) that don't need redesign.

3. **Main script is the problem**: `bin/cc-isolate` is where the architectural mismatch lives. The push/pull commands have no concept of manifests, discovery, or conflicts.

4. **Risk management**: Reusing working encryption and platform code eliminates a class of bugs and edge cases we'd otherwise reintroduce.

### Consequences

1. **Create new `bin/devenv`** - Main entry point with manifest-driven commands
2. **Refactor libraries** - May need to extract/rename some functions for clarity
3. **Deprecate `cc-isolate`** - Either remove entirely or keep as alias to profile commands
4. **New manifest format** - Design from scratch for the problem model
5. **Migration path** - Existing users (you) need way to migrate current vault

---

## D2: Manifest Storage Format

**Date**: 2026-01-05
**Status**: Decided
**Decision**: YAML format with separate machine-specific and shared sections

### Context

The system needs a manifest to track:
- Registered machines (name, platform, project roots)
- Known projects (name, paths per machine)
- Sync items (what files to sync, hashes, timestamps)
- User validation decisions (accepted/rejected patterns)

### Options Considered

**Option A: Single JSON file**
- All state in one `manifest.json`

*Pros*: Simple to parse (jq available), single source of truth
*Cons*: Merge conflicts likely when both machines modify

**Option B: Directory structure**
- `manifest/machines/`, `manifest/projects/`, etc.
- One file per entity

*Pros*: Git-friendly, reduces merge conflicts
*Cons*: More complex to parse, scattered state

**Option C: YAML with sections (Chosen)**
- Single `devenv.yaml` with clear sections
- Machine-specific config in separate `devenv.local.yaml` (gitignored)

*Pros*: Human-readable, YAML handles multi-line strings, git-friendly for shared state
*Cons*: Need YAML parser (but we already have one in secrets-sync.sh)

### Decision

**Option C: YAML with sections**

### Rationale

1. We already have YAML parsing code in `lib/secrets-sync.sh`
2. YAML is more readable than JSON for config files
3. Separating machine-specific (`.local.yaml`) from shared (main `.yaml`) prevents most merge conflicts
4. Single file is easier to reason about than directory structure

### Consequences

1. `devenv.yaml` - Shared manifest (committed to git)
2. `devenv.local.yaml` - Machine-specific config (gitignored)
3. Extend YAML parser from secrets-sync.sh or create shared `lib/yaml.sh`

---

## D3: Discovery Mechanism

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Multi-phase discovery with explicit shortcuts and traversal limits

### Context

FR7 requires auto-discovery of gitignored essentials across projects. NFR1 identifies performance concerns:
- Currently ~10 projects, expected 50+
- Discovery runs on every push (must not be sluggish)
- Accidentally traversing `node_modules/` would be catastrophic

### Options Considered

**Option A: Full filesystem traversal**
- Recursively scan all project roots every time

*Pros*: Comprehensive
*Cons*: Slow at scale, dangerous without safeguards

**Option B: Git-aware incremental**
- Use `git status` and `git ls-files --others --ignored` per project
- Only scan projects with changes since last sync

*Pros*: Fast, leverages git's tracking
*Cons*: Requires git invocation per project, may miss non-git content

**Option C: Hybrid discovery (Chosen)**
- Phase 1: Quick check using manifest (what's changed since last sync?)
- Phase 2: `~/.claude/projects/` as discovery shortcut for active projects
- Phase 3: Full scan only for newly discovered projects or on explicit `--full` flag
- Hard traversal limits: max depth, skip directories matching blocklist

*Pros*: Fast for normal case, comprehensive when needed, safe by default
*Cons*: More complex implementation

### Decision

**Option C: Hybrid discovery with explicit phases**

### Rationale

1. **Performance is critical**: Discovery runs on every push. Sluggish = won't use.
2. **Git-aware beats naive traversal**: Most essentials are gitignored, so `git ls-files --others --ignored --exclude-standard` is the right primitive.
3. **Shortcuts exist**: `~/.claude/projects/` already indexes active projects.
4. **Incremental is sufficient**: Only new/changed files need discovery; manifest tracks known items.

### Consequences

1. Manifest tracks `last_discovered_at` per project
2. Discovery phases implemented as separate functions
3. Hard blocklist: `node_modules/`, `dist/`, `build/`, `.cache/`, `target/`, `__pycache__/`
4. Max depth configurable (default: 3 levels below project root)
5. `devenv discover --full` for explicit comprehensive scan

---

## D4: Conflict Detection Strategy

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Hash-based detection with content preserved for resolution

### Context

FR6 requires conflict detection when same file modified on multiple machines since last sync. The system must prevent silent data loss.

### Options Considered

**Option A: Timestamp-based**
- Compare modification times

*Pros*: Simple
*Cons*: Unreliable across machines (clock drift, timezone issues)

**Option B: Hash-based (Chosen)**
- SHA256 hash of content stored in manifest
- Compare local hash vs manifest hash on pull

*Pros*: Reliable, content-addressable, no clock dependency
*Cons*: Requires hash computation, slightly more storage

**Option C: Git-native**
- Let git handle merge conflicts

*Pros*: Familiar, well-tested
*Cons*: Only works for decrypted content, breaks encryption flow

### Decision

**Option B: Hash-based detection**

### Rationale

1. Hashes are deterministic and platform-independent
2. SHA256 is fast enough for config files
3. Storing expected hash in manifest enables detection before overwrite
4. Git merge conflicts don't work well with encrypted content

### Consequences

1. Manifest stores `content_hash` per sync item
2. Push records hash of synced content
3. Pull compares local hash to manifest before deploy
4. Mismatch = conflict state, requires resolution
5. Hash computation uses `sha256sum` (Linux) or `shasum -a 256` (macOS)

---

## D5: Validation Workflow Design

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Accept/reject per item with persistent decisions

### Context

Section 8.4 of PROBLEM-MODEL.md requires user validation:
- Present discovered candidates
- Allow accept/reject per item
- Allow manual addition (false negative recovery)
- Persist decisions for future syncs

### Options Considered

**Option A: Interactive CLI prompts**
- Each discovered item shows prompt: [a]ccept / [r]eject / [s]kip

*Pros*: Simple, works in terminal
*Cons*: Tedious for many items, poor UX for bulk operations

**Option B: Validation file with manual edit**
- Generate `pending-validation.txt` listing discoveries
- User edits file, marks each as accept/reject
- Tool processes file

*Pros*: Batch operations, user can review at leisure
*Cons*: Extra step, format must be parsed

**Option C: Hybrid (Chosen)**
- Default: Interactive prompts for small batches (<10 items)
- Large batches: Generate validation file
- `devenv validate` command to process either mode
- Decisions persisted in manifest

*Pros*: Good UX for both cases, persistent state
*Cons*: More complex implementation

### Decision

**Option C: Hybrid validation workflow**

### Rationale

1. Interactive works well for typical case (few new discoveries)
2. File-based works well for initial setup (many items)
3. Persisting decisions in manifest ensures "once validated, stays validated"

### Consequences

1. `devenv discover` presents items for validation
2. Interactive mode for <=10 items, file mode for >10
3. Validation decisions stored in manifest: `accepted_patterns`, `rejected_patterns`
4. Patterns support glob matching (e.g., `**/.env*`, `.vercel/`)

---

## D6: Claude Code Completeness Verification

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Dynamic scanning with known exclusions list

### Context

FR8 requires syncing ALL Claude Code config, not a static list. New config locations must be detected automatically.

Current hardcoded list in cc-isolate:
```bash
CLAUDE_SYNC_ITEMS=(
    "CLAUDE.md"
    "commands"
    "skills"
    "settings.json"
    "output-styles"
)
```

Known exclusions:
- `~/.claude/plugins/cache/` - regenerates automatically

### Options Considered

**Option A: Maintain static list**
- Keep hardcoded list, update when new locations discovered

*Pros*: Simple
*Cons*: Violates completeness requirement, silent failures

**Option B: Sync entire ~/.claude/ minus exclusions (Chosen)**
- Scan `~/.claude/` for all files/directories
- Skip explicitly excluded items (`plugins/cache/`)
- Alert user to unknown items for validation

*Pros*: Completeness by default, future-proof
*Cons*: May initially capture junk, requires validation

### Decision

**Option B: Dynamic scanning with exclusion list**

### Rationale

1. Claude Code evolves - new config locations appear
2. "Unknown items trigger validation" matches the permissive-discovery principle
3. Exclusion list is shorter and more stable than inclusion list

### Consequences

1. Scan `~/.claude/` recursively, excluding known caches
2. Compare to manifest's known items
3. New items trigger validation prompt
4. Exclusions configurable in manifest: `claude_exclusions: [plugins/cache/]`

---

## D7: Project Path Mapping Implementation

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Git remote URL as project identity, explicit path mapping per machine

### Context

FR3 requires mapping same logical project to different physical paths:
- MacBook: `~/cc-projects/muse-v1`
- Desktop: `~/projects/muse/muse-v1`

### Options Considered

**Option A: Folder name matching**
- Match projects by folder name

*Pros*: Simple
*Cons*: Fails for nested paths (`muse-v1` vs `muse/muse-v1`), common names

**Option B: Git remote URL as identity (Chosen)**
- Use `git remote get-url origin` as canonical project ID
- Each machine registers its local path for that project ID

*Pros*: Globally unique, already exists, handles renames
*Cons*: Requires git remote configured, manual for new projects

**Option C: User-assigned project names**
- User assigns name like "muse-v1" and maps paths

*Pros*: Explicit control
*Cons*: Manual overhead, easy to get wrong

### Decision

**Option B: Git remote URL as identity**

### Rationale

1. Git remotes are globally unique
2. Already configured for any cloned project
3. Survives local renames and moves
4. Matches developer mental model ("this is the muse repo")

### Consequences

1. Project identity = normalized git remote URL (strip `.git`, lowercase)
2. Manifest stores: `projects: { "github.com/memorymuse/muse-v1": { macbook: "~/cc-projects/muse-v1", desktop: "~/projects/muse/muse-v1" } }`
3. New project discovery prompts for path on other machines
4. Projects without git remotes use folder name (degraded mode)

---

## D8: Deletion Propagation

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Yes, propagate deletions with high-confidence verification

### Context

When a file is deleted on one machine, should that deletion propagate to other machines on pull?

### Decision

**Yes, propagate deletions** - but the system must be absolutely certain the deletion actually occurred on the source machine (not just missing locally due to other reasons).

### Verification Requirements

1. Manifest must explicitly record `deleted_at` timestamp and `deleted_by` machine
2. Deletion only recorded during push if:
   - Item was previously in manifest with content hash
   - File no longer exists at expected path
   - User confirms deletion intent (or automated confirmation if within same push session where file was known to exist)
3. On pull, deletion only applied if manifest shows explicit deletion record

### Consequences

1. Manifest items gain `status: active | deleted` field
2. Deleted items retained in manifest (with deletion metadata) for audit trail
3. Orphaned local files (exist locally but deleted in manifest) prompt user for action
4. False positives (file missing due to local issue) won't propagate - requires explicit deletion on source

---

## D9: Pull Scope Filtering

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Automatic filtering to relevant projects, no partial pull command

### Context

Should users be able to pull only specific items? What about projects that don't exist on the pulling machine?

### Decision

**No explicit partial pull command**, but pull automatically filters to projects that exist on this machine.

### Behavior

1. Pull always pulls all global config (Claude Code, dotfiles)
2. For project-scoped items, only deploy if project path exists locally
3. Items for projects not on this machine are skipped silently (no error)
4. Manifest still receives full update (knows about all items)

### Rationale

If MacBook doesn't have `/muse-v0/`, there's no sensible place to deploy its secrets. Skip it. User can add the project later and secrets will deploy on next pull.

### Consequences

1. `devenv pull` is always "pull everything relevant to me"
2. No `--scope` or `--project` flags needed
3. Manifest contains full state; deployment filters by local presence
4. Status command shows "X items skipped (project not present)"

---

## D10: File Size Handling

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Hard limit at 5MB, warning at 1MB

### Context

Should there be file size limits for synced items?

### Discussion

Concerns with large files:
1. **Git bloat**: Large files in history are permanent
2. **Wrong tool signal**: Config files are small; large files suggest generated/binary content that shouldn't be synced

### Decision

- **Hard limit**: 5MB max per file. Files larger than this indicate something is wrong.
- **Warning**: Files >1MB trigger a broadcast warning to terminal during sync.

### Rationale

Config files are small. If files >5MB are getting synced, there's likely an issue (wrong file captured, generated artifact, etc.). The 1MB warning provides early visibility without blocking.

### Consequences

1. Size check during discovery/push
2. >1MB: Warning broadcast to terminal (non-blocking)
3. >5MB: Error, file rejected from sync
4. Clear error message explaining why and suggesting review

---

## D11: Pattern Registration Mechanism

**Date**: 2026-01-05
**Status**: Decided
**Decision**: CLI command for now, agent-driven in future

### Context

How do users add new essential patterns (e.g., when adopting a new service that creates `.newservice/` config)?

### Decision

**Phase 1 (now)**: `devenv config add-pattern "**/.newservice/"` CLI command

**Phase 2 (future)**: Agent-aware registration via hooks/skills. An agent discovering a new service integration could register patterns within their session.

### Rationale

User (Kyle) noted that agents do 100% of execution work. Ideally agents would self-register new patterns. However, this requires additional infrastructure (hooks, skills) that is out of scope for initial implementation.

### Consequences

1. `devenv config add-pattern <glob>` adds to `validation.accepted_patterns`
2. `devenv config remove-pattern <glob>` removes pattern
3. Future: Consider hook on "new gitignored file detected" for agent integration

---

## D12: Conflict Resolution Strategy

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Agent-assisted merge capability, not just pick-one

### Context

When conflicts occur, should the system support actual content merging, or just pick one version?

### Discussion

User (Kyle) clarified:
1. Initial sync will have many conflicts requiring compilation/unification
2. Terminals stay up indefinitely - can't rely on session boundaries
3. Simple pull-work-push is ideal but not guaranteed
4. Agent-assisted merge is feasible with clear instructions

### Decision

**Agent-assisted merge** as primary resolution path:
1. Detect conflict (hash mismatch)
2. Present both versions to agent (via Claude Code session or `/devenv-resolve` skill)
3. Agent merges with user consultation as needed
4. Merged result becomes new canonical version

**Fallback**: Manual pick-one (`--use-local` / `--use-remote`) when agent unavailable

### Rationale

Config files are structured. An agent with context ("this is a .env file, these are the keys") can intelligently merge. Better than losing changes or forcing manual diff/merge.

### Consequences

1. Conflict resolution invokes agent assistance by default
2. `/devenv-resolve` skill provides agent with conflict context
3. Agent can ask clarifying questions
4. Fallback flags for non-interactive resolution
5. Initial environment unification treated as batch conflict resolution

---

## D13: Operation History

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Per-action logging, ~50 entries, no aggressive trimming

### Context

How much operation history to retain in manifest?

### Entry Structure

An operation entry is a JSON blob per push/pull action:
```yaml
- type: push
  machine: macbook
  timestamp: "2026-01-05T17:30:00Z"
  items_affected: 12
  conflicts_resolved: 0
  # Optionally: list of item IDs affected
```

**Granularity**: Per-action (push/pull), not per-item. This is the right level - per-item would be noise.

### Decision

- **Retain ~50 entries** as a soft guideline
- **No aggressive trimming** - this file isn't regularly ingested by agents, so token bloat is not a concern
- **Value**: Provides explicit, easily readable/queryable history beyond git

### Rationale

Git history tells you what changed, but requires git commands to query. Manifest operation log is immediately readable and shows the sync-specific context (which machine, how many items, conflicts).

### Consequences

1. `operations` array in manifest
2. Soft cap at 50 entries (prune oldest when exceeded)
3. Each entry captures the action-level summary
4. Useful for debugging sync issues without diving into git

---

## D14: Manifest Versioning

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Version field + immutable schema files in dedicated folder

### Context

How to handle manifest schema changes over time?

### Decision

1. **Include `version: "1.0"`** in manifest from the start (low effort)
2. **Dedicated schema folder**: `docs/schemas/` containing versioned schema files
3. **Immutability governance**: Schema files are immutable once created

### Schema File Structure

```
docs/schemas/
├── manifest-v1.0.yaml    # Schema definition for v1.0
├── manifest-v1.1.yaml    # Schema definition for v1.1 (when needed)
└── README.md             # Explains versioning rules
```

### Immutability Rule

Each schema file must include a prominent comment:

```yaml
# ============================================================
# IMMUTABLE SCHEMA FILE - DO NOT MODIFY
#
# This schema is frozen. Any changes require:
# 1. Create a new schema file with incremented version
# 2. Update version references in code
# 3. Implement migration function if needed
# ============================================================
```

### Rationale

Low effort to include versioning from start. Immutable schema files provide clear reference for each version. Governance rule prevents accidental schema drift.

### Consequences

1. `version` field at top of devenv.yaml
2. Schema files in `docs/schemas/` are immutable reference
3. On load, check version compatibility
4. If version mismatch: run migration or error with instructions
5. Schema changes require new file + version increment

---

## D15: Manifest Corruption Recovery

**Date**: 2026-01-05
**Status**: Decided
**Decision**: Agent-guided recovery from git history with user approval for destructive ops

### Context

What if manifest becomes corrupt or inconsistent?

### Decision

**`devenv repair`** initiates agent-guided recovery:

1. Agent examines git history for last known-good manifest
2. Agent compares vault contents to manifest expectations
3. Agent proposes recovery plan
4. **All destructive operations require explicit user approval**
5. Recovery leverages git - can always reset to previous commit

### Safety Requirements

1. Agent must explain what it found and what it proposes
2. No automatic deletion or overwrite without confirmation
3. User can abort at any point
4. Git provides ultimate fallback: `git reset --hard <good-commit>`

### Rationale

User (Kyle) emphasized: agent must be extremely cautious, loop in user, request permission. Remote git provides safety net.

### Consequences

1. `devenv repair` command exists
2. Invokes agent with repair context
3. Agent proposes, user approves
4. Backup manifest before any repair attempt
5. Document manual git recovery as last resort

---

## D16: Implementation Language

**Date**: 2026-01-06
**Status**: Decided
**Decision**: Python 3.10+ instead of Bash

### Context

Original design specified bash (HC7: "Bash-based") to avoid shell implementation splits and minimize dependencies. Self-review identified significant fragility and maintainability concerns:

- **Fragility**: YAML parsing in bash is error-prone; state spread across 5 locations; multi-step flows have many failure points
- **Maintainability**: 9 bash files with primitive debugging (set -x only); cross-platform differences hide subtle bugs

### Impact Assessment

**Direct impacts evaluated**:
| Area | Bash | Python | Verdict |
|------|------|--------|---------|
| YAML handling | Hand-rolled, fragile | PyYAML, battle-tested | Major improvement |
| Error handling | exit codes, set -e | try/except, stack traces | Major improvement |
| Debugging | set -x, echo | pdb, IDE support, logging | Major improvement |
| Testing | Manual/ad-hoc | pytest, unittest, mock | Enables proper testing |
| Cross-platform | BSD/GNU workarounds | pathlib, os module | Simplifies significantly |
| Type safety | None | Type hints, dataclasses | Enables static analysis |

**Indirect impacts evaluated**:
- HC7 constraint invalidated — but underlying concern (cross-platform consistency) is *better* served by Python
- SC1 "minimal dependencies" — Python + PyYAML is 1 package, acceptable trade-off
- D1 "reuse bash libs" — existing ~1,200 lines become reference, not reusable code; logic transfers, syntax doesn't
- Age integration — unchanged, subprocess call to CLI
- Shell event hooks — none designed, no impact

**Risks evaluated**:
- Python not installed: Low risk (macOS/Ubuntu ship with it)
- Wrong Python version: Mitigated by pyproject.toml, fail-fast
- Rewrite introduces bugs: Mitigated by porting logic carefully, testing against bash outputs

### Decision

**Python 3.10+** with PyYAML. Call `age` CLI via subprocess (unchanged from bash approach).

### Rationale

1. Fragility and maintainability concerns (self-review items 6 & 7) are substantially addressed
2. Dependency cost is minimal: Python runtime (pre-installed) + 1 pip package
3. Design has no shell event hooks — it's a standalone CLI, language is implementation detail
4. Implementing agents will find Python more navigable than bash
5. Existing bash code's *logic* transfers even though *syntax* doesn't

### Consequences

1. **Supersedes HC7**: "Bash-based" constraint retired; Python addresses underlying cross-platform concern better
2. **Updates SC1**: "Minimal dependencies" becomes "minimal, justified dependencies" — Python + PyYAML qualifies
3. **Invalidates D1 partially**: "Reuse lib/*.sh" no longer applies; existing bash becomes reference implementation
4. **Directory structure changes**: `lib/*.sh` → `src/devenv/*.py`
5. **Component signatures change**: Bash functions → Python methods with type hints
6. **New dependency section**: Python 3.10+, PyYAML >= 6.0, age CLI

### What Does NOT Change

- File-based interfaces (YAML manifests, conflict files, validation files) — language agnostic
- Age encryption approach — subprocess call works identically
- Overall architecture — components, flows, data model unchanged
- Agent consumption — design doc structure and clarity unchanged

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-05 | Initial decisions (D1-D7) |
| 1.1 | 2026-01-05 | Added D8-D15 (formerly open questions) |
| 1.2 | 2026-01-05 | Revised D10 (5MB hard limit, 1MB warning), D13 (per-action, ~50 entries), D14 (immutable schema folder) |
| 1.3 | 2026-01-06 | Added D16 (Python implementation language) |

# env-sync Problem Model

This document models the problem space for environment synchronization across development machines. It is intentionally solution-agnostic - focusing on what problem we're solving, not how we'll solve it.

Any agent starting fresh on this project should read this document to understand the problem domain, constraints, and success criteria.

---

## 1. Problem Statement

### 1.1 The Core Problem

A developer works across multiple machines (e.g., MacBook and Windows Desktop with WSL). Each machine has its own filesystem with its own state. The developer's mental model is: "My development environment is a single logical entity." The reality is: each machine is an independent island.

**The gap:** There is no mechanism to bridge the mental model to reality. The developer must manually synchronize environment state across machines, which is tedious, error-prone, and often forgotten.

### 1.2 What Constitutes "Environment State"

Environment state includes everything necessary to make a machine productive for development that is NOT automatically tracked or synced by existing tools:

| Category | Examples | Why It's a Problem |
|----------|----------|-------------------|
| Secrets | `.env`, `.npmrc` with tokens, API keys | Gitignored (correctly), must be manually copied |
| Shell config | `.zshrc`, `.bashrc`, aliases, functions | Lives in home directory, not in any repo |
| Tool config | `.gitconfig`, `.vimrc`, IDE settings | Personal customizations, often gitignored |
| Claude Code | `~/.claude/` (CLAUDE.md, skills, commands, settings) | User-level config, no sync mechanism |
| Provider config | `.vercel/`, `.netlify/`, `.firebase/` | Per-project but gitignored |
| Cloud config | `.aws/`, `.gcloud/`, service accounts | Machine-local, gitignored |
| Auth state | OAuth tokens, session files | Machine-local |

### 1.3 Why Existing Solutions Don't Work

| Existing Approach | Why It's Insufficient |
|-------------------|----------------------|
| Git | Secrets can't be committed; user-level config isn't in any repo |
| Dotfiles repos | Only handles home directory files; no secret encryption; no project-level sync |
| Cloud sync (Dropbox, etc.) | Syncs everything including generated artifacts; no encryption; symlink issues |
| Secrets managers (1Password, etc.) | Designed for retrieval, not file reconstruction; doesn't handle config files |
| Configuration management (Ansible, etc.) | Overkill for single user; designed for provisioning, not bidirectional sync |

### 1.4 The Fundamental Tension

The problem has an inherent tension:

1. **Security**: Secrets must never appear in plaintext in any synced/shared location
2. **Convenience**: Sync must be effortless (one command) or it won't be used
3. **Flexibility**: Must handle both global config and per-project config
4. **Heterogeneity**: Machines have different paths, tools, and platform specifics

Any solution must navigate all four simultaneously.

---

## 2. Context

### 2.1 User Profile

- **Who**: Single developer (not a team)
- **Machines**: 2-3 personal development machines
- **Platforms**: macOS and Windows with WSL/Ubuntu
- **Technical Level**: Advanced (comfortable with CLI, git, shell scripting)
- **Workflow**: Works on one machine at a time, switches daily or weekly

### 2.2 Physical Environment

```
┌─────────────────┐         ┌─────────────────┐
│   MacBook       │         │   Desktop       │
│   (macOS)       │         │   (WSL/Ubuntu)  │
│                 │         │                 │
│  ~/cc-projects/ │         │  ~/projects/    │
│  ~/.claude/     │         │  ~/.claude/     │
│  ~/.zshrc       │         │  ~/.bashrc      │
│  ~/.gitconfig   │         │  ~/.gitconfig   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     │
              ┌──────┴──────┐
              │   Git Repo  │
              │  (remote)   │
              │             │
              │  Encrypted  │
              │   state     │
              └─────────────┘
```

### 2.3 Temporal Context

- **Frequency**: Push/pull happens when switching machines (daily to weekly)
- **Latency tolerance**: Should feel fast, not sluggish
- **Staleness tolerance**: Hours between syncs is acceptable; real-time not needed
- **Conflict frequency**: Low - typically only one machine is active at a time

### 2.4 What Success Looks Like

The developer sits down at any machine, runs a single command, enters a password, and within seconds has an environment identical to what they left on the other machine. No manual copying. No forgotten configs. No "works on my other machine" problems.

---

## 3. Stakeholders

### 3.1 Primary Stakeholder

**The Developer (User)**
- Needs: Seamless machine switching, no manual sync overhead
- Frustrations: Forgotten configs, repeated setup, context switching friction
- Constraints: Limited time for tooling maintenance

### 3.2 Secondary Stakeholders

**Future Agents**
- Needs: Clear problem understanding to build/extend solution
- Frustrations: Incomplete context, unclear requirements
- Constraints: Must work from documentation, no direct user access

**The Projects**
- Needs: Correct configuration to function
- Frustrations: Missing .env files, wrong provider config
- Constraints: Expect config to "just be there"

---

## 4. Constraints

### 4.1 Hard Constraints (Non-Negotiable)

| ID | Constraint | Rationale |
|----|------------|-----------|
| HC1 | Secrets must be encrypted before leaving local machine | Security requirement - secrets in git history is unacceptable |
| HC2 | Must work on macOS and WSL/Ubuntu | These are the actual machines in use |
| HC3 | Push and pull must each be a single command | Complexity beyond this won't be used consistently |
| HC4 | No manual steps beyond password entry for nominal operations | Friction kills adoption. Edge cases (new project mapping, conflict resolution) may require additional prompts, but daily push/pull must be password-only. |
| HC5 | Git-based transport and storage | Leverages existing infrastructure, provides history |
| HC6 | Password-based encryption | No external key management dependencies |
| ~~HC7~~ | ~~Bash-based (not bash/zsh split)~~ | **SUPERSEDED by D16**: Python 3.10+ addresses cross-platform consistency better than bash; original concern was platform compatibility, not bash specifically |

### 4.2 Soft Constraints (Strong Preferences)

| ID | Constraint | Rationale |
|----|------------|-----------|
| SC1 | Minimal, justified dependencies | Python 3.10+ (pre-installed on target platforms) + PyYAML + age CLI. Trade-off accepted per D16 for maintainability gains. |
| SC2 | Understandable by reading the code | Future maintenance by agents or user |
| SC3 | Fast execution for typical sync | Should feel responsive, not sluggish |
| SC4 | Graceful degradation on errors | Partial success better than total failure |
| SC5 | No over-engineering | Complexity is the enemy; YAGNI applies |

### 4.3 Platform Constraints

| Platform | Specific Constraints |
|----------|---------------------|
| macOS | Homebrew at `/opt/homebrew` (Apple Silicon) or `/usr/local` (Intel); zsh default shell; older bash version |
| WSL/Ubuntu | Homebrew at `/home/linuxbrew/.linuxbrew` if present; newer bash; Windows interop paths |
| Both | Different tool availability; different default paths; symlink behavior differences |

---

## 5. Requirements

### 5.1 Functional Requirements

#### FR1: Bidirectional State Synchronization
The system must support both:
- **Push**: Transfer local state to shared repository
- **Pull**: Transfer shared repository state to local machine

Either operation can be initiated at any time, in any order.

#### FR2: Multi-Scope State Handling
The system must handle state at multiple scopes:

| Scope | Examples | Behavior |
|-------|----------|----------|
| Global (user-level) | `~/.claude/`, `~/.zshrc` | Same across all machines |
| Project-level | `.env`, `.vercel/` in project dirs | Deployed to correct project path per machine |
| Machine-specific | PATH additions, tool paths | Stays local, never synced |

#### FR3: Project Path Mapping
The system must map the same logical project to different physical paths across machines:
- Project identity: folder name containing `.git`
- Path resolution: each machine maintains its own path for each project
- Graceful handling: if project folder named differently, allow explicit mapping

#### FR4: Gitignored Essential Capture
The system must identify and capture files that are:
- Gitignored in their project (not tracked by project's git)
- Essential for project function (secrets, provider config, tool config)
- NOT generated artifacts

**Generated artifact indicators** (exclude from discovery):
- Directories with many files (likely `node_modules/`, caches)
- Common generated directory names: `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.cache/`, `target/`
- Unusually large files (likely compiled output, not config)

These are indicators, not hard rules. When uncertain, include for user validation rather than exclude silently.

#### FR5: Secret Protection (Defense-in-Depth)
The system must implement multiple layers of protection against secret exposure:

**Layer 1 - Encryption**: Encrypt all sensitive data before git commit
**Layer 2 - Verification**: Verify no plaintext secrets in staged content before commit
**Layer 3 - Detection**: Ability to scan repository for accidental plaintext exposure
**Layer 4 - Recovery**: Clear procedure if exposure is detected (cannot un-expose, but can rotate/invalidate)

Additional requirements:
- Store only encrypted form in git history
- Decrypt only on pull, on local machine
- Use password-based encryption (user provides password)

No single safeguard is sufficient. Defense-in-depth assumes any layer can fail.

#### FR6: Conflict Detection and Resolution
The system must:
- Detect when same file was modified on multiple machines since last sync
- Prevent silent data loss from overwrites
- Provide a resolution mechanism (automated or assisted)

#### FR7: Project Auto-Discovery
The system must:
- Scan configured project root directories for git repositories
- Identify new projects automatically
- Capture their gitignored essentials

#### FR8: Claude Code Configuration Sync (Completeness Required)
The system must sync ALL user-configured Claude Code state. This is not a static list - it's a completeness requirement.

**Known locations** (as of document date):
- `~/.claude/` directory (CLAUDE.md, commands/, skills/, agents/, rules/, settings.json)
- `~/.claude.json` (encrypted - contains tokens and MCP config)

**Exclusions**:
- `~/.claude/plugins/cache/` - regenerates automatically

**Completeness verification**:
- The system must detect new files/directories in `~/.claude/` that aren't explicitly excluded
- Unknown items trigger user validation (accept for sync, or add to exclusions)
- This prevents silent omission when Claude Code adds new config locations

**The invariant**: If a user configures something in Claude Code and it persists to disk, it must be captured (unless explicitly excluded). "I configured this on my other machine" failures are unacceptable.

### 5.2 Non-Functional Requirements

#### NFR1: Performance
- Typical push/pull should feel fast (not sluggish)
- Avoid full filesystem scans; use incremental detection

**Scale context** (informs design tradeoffs):
- Current: ~10 projects
- Expected growth: 50+ projects over time
- Discovery runs automatically on every push (must not be sluggish)

**Performance-sensitive operations**:
- Directory traversal across project roots
- Gitignore evaluation (potentially per-file)
- Content inspection (when needed - see below)

**When content inspection may be needed**:
- Files with ambiguous names that could be config or generated (rare)
- Verifying a file contains expected structure (e.g., is this a valid .env format?)
- Detecting secrets in non-obvious locations (files not named `.env` but containing credentials)

Content inspection should be the exception, not the rule. Path/name-based identification handles most cases.

**Key concern**: Accidentally descending into large ignored directories (e.g., `node_modules/`) would be catastrophic. Discovery must be able to skip known-large directories *before* fully traversing them.

**Design guidance**: The solution should handle 50+ projects without noticeable slowdown on typical push. This likely requires incremental detection (only scan what changed) rather than full traversal every time.

**Potential discovery shortcuts**:
- `~/.claude/projects/` contains a list of directories where Claude Code has been invoked - a pre-built index of "projects the user actively works on"
- Limitation: This tracks invocation roots, not nested structure. A repo like `general-tools/` may contain multiple independent sub-projects (`env-sync/`, `filedet/`, etc.), each with their own dotfiles. Claude tracks the root, but essential files may be nested below it.
- Also doesn't cover projects without Claude Code usage
- Useful for bootstrapping, but not sufficient as sole discovery mechanism

**Edge case: Non-standard file locations**:
The model assumes essentials live within project directories. Real-world exceptions:

1. **Nested sub-projects**: A monorepo or multi-tool repo may have essentials at multiple levels (e.g., `general-tools/.env` AND `general-tools/env-sync/.env`). Discovery must handle depth, not just project root.

2. **External secrets**: Secrets stored outside project trees (e.g., `~/secrets/project-specific/api-keys.env`). This is currently **out of scope** - the system tracks project-scoped essentials, not arbitrary filesystem locations. If needed, user can configure additional paths as "project roots."

The design must decide: How deep to recurse within a project? One level? All subdirectories? Only directories containing certain markers?

#### NFR2: Reliability
- Never lose user data
- Never expose secrets unencrypted in git
- Atomic operations where possible (no partial states)

#### NFR3: Usability
- Single command for push, single command for pull
- Clear error messages with remediation guidance
- Progress indication for longer operations

#### NFR4: Maintainability
- Code understandable without extensive documentation
- Modular structure for extending file type support
- Reasonable test coverage for critical paths

#### NFR5: Recoverability
- Ability to recover from interrupted sync
- Ability to roll back to previous state
- Clear guidance when manual intervention needed

---

## 6. Use Case Decomposition

### UC1: Initial Setup (First Machine)

**Actor**: Developer on primary machine
**Preconditions**:
- No sync repository exists
- Machine has git and encryption tool available

**Flow**:
1. Developer initializes sync system
2. System prompts for machine name (e.g., "macbook")
3. System prompts for project root directories
4. System scans for existing projects
5. System captures current state (global configs, project essentials)
6. System encrypts sensitive data
7. System creates git repository and pushes

**Postconditions**:
- Git repository exists with encrypted state
- Machine is registered in manifest
- All current state captured

**Variations**:
- A1: Developer wants to add more project roots later

---

### UC2: Secondary Machine Setup

**Actor**: Developer on new/additional machine
**Preconditions**:
- Sync repository exists with data from other machine(s)
- Machine has git and encryption tool available

**Flow**:
1. Developer clones sync repository
2. Developer runs setup command
3. System prompts for machine name
4. System prompts for project root directories
5. Developer runs pull command
6. System prompts for encryption password
7. System decrypts state
8. System deploys global configs to home directory
9. System maps projects to local paths (prompting if unclear)
10. System deploys project essentials to mapped paths

**Postconditions**:
- Machine is registered in manifest
- Global configs deployed
- Project essentials deployed to correct paths

**Variations**:
- A1: Project path is ambiguous (prompt user)
- A2: Project doesn't exist locally yet (store config for later)

---

### UC3: Regular Push

**Actor**: Developer ending work session
**Preconditions**:
- Machine is set up and registered
- Local changes may or may not exist

**Flow**:
1. Developer runs push command
2. System scans for changes (using manifest for efficiency)
3. System discovers any new projects
4. System captures changed files and new project essentials
5. System prompts for encryption password
6. System encrypts sensitive data
7. System commits to git
8. System pushes to remote

**Postconditions**:
- All local changes synced to repository
- Manifest updated with new state

**Variations**:
- A1: No changes detected (no-op)
- A2: New project discovered (auto-capture essentials)
- A3: Git push fails (provide error guidance)

---

### UC4: Regular Pull

**Actor**: Developer starting work on different machine
**Preconditions**:
- Machine is set up and registered
- Repository may have changes from other machine(s)

**Flow**:
1. Developer runs pull command
2. System fetches from remote
3. System checks for local changes that would be overwritten
4. If no conflicts: System prompts for encryption password
5. System decrypts incoming state
6. System deploys updates to appropriate locations
7. System updates local manifest

**Postconditions**:
- Local state matches repository state
- All configs and essentials deployed

**Variations**:
- A1: No remote changes (no-op)
- A2: Conflict detected (invoke resolution flow)
- A3: New project from other machine (prompt for local path)

---

### UC5: Conflict Resolution

**Actor**: Developer pulling when conflicts exist
**Preconditions**:
- Same file modified on both local machine and repository
- System has detected the conflict

**Flow**:
1. System writes conflict details to pending file
2. System informs developer of conflict
3. Developer invokes resolution assistant (separate command/skill)
4. Assistant reads conflict details
5. Assistant presents each conflict with diff
6. Developer selects resolution for each (via interactive prompts)
7. Assistant writes resolution decisions
8. Developer runs apply command
9. System applies resolutions
10. System cleans up conflict state

**Postconditions**:
- All conflicts resolved
- State is consistent
- Resolution logged for history

**Variations**:
- A1: Developer chooses "use local" for all
- A2: Developer chooses "use remote" for all
- A3: Developer wants to manually merge (provide file paths)

---

### UC6: New Project Discovery

**Actor**: System during push
**Preconditions**:
- Developer has created new project in a project root
- Project has gitignored essentials

**Flow**:
1. System scans project roots
2. System finds new git repository
3. System adds project to manifest
4. System scans project for gitignored essentials
5. System captures matching files/directories
6. Files included in push

**Postconditions**:
- Project registered in manifest
- Project essentials captured in sync repo

**Variations**:
- A1: Project has no gitignored essentials (still register, nothing to capture)
- A2: Project has unusually large files (size limits?)

---

### UC7: New Machine Deployment

**Actor**: Developer with brand new machine
**Preconditions**:
- Sync repository exists
- Machine is clean (no existing config)

**Flow**:
1. Developer installs prerequisites (git, encryption tool)
2. Developer clones sync repository
3. Developer runs setup (machine name, project roots)
4. Developer runs pull
5. System deploys all global configs
6. System deploys all project essentials (prompting for paths if needed)
7. Developer clones project repositories
8. Projects are immediately functional

**Postconditions**:
- Machine fully configured
- All projects ready to use (after cloning their repos)

**Success Metric**: Bare machine to productive without a "setup day" - should feel quick

---

### UC8: Machine-Specific Configuration

**Actor**: Developer configuring platform-specific settings
**Preconditions**:
- Different machines need different values (e.g., PATH)

**Flow**:
1. System provides mechanism for machine-specific config
2. Developer creates/edits machine-specific file
3. File is stored in sync repo but only deployed to matching machine
4. Shared config sources machine-specific config if present

**Postconditions**:
- Machine-specific settings stay local
- Shared settings sync normally
- No conditionals scattered in main config

---

## 7. Boundaries

### 7.1 In Scope

| Category | Specifics |
|----------|-----------|
| Global configs | `~/.claude/`, `~/.claude.json`, `~/.zshrc`, `~/.bashrc`, `~/.bash_aliases`, `~/.gitconfig`, `~/.vimrc`, etc. |
| Project configs | `.env*`, `.vercel/`, `.netlify/`, `.firebase/`, `.aws/`, provider configs |
| Shell utilities | Custom functions, aliases, significant scripts |
| Encryption | Password-based encryption of all synced content |
| Project mapping | Same project → different paths across machines |
| Conflict handling | Detection and assisted resolution |
| Audit/History | Log of sync operations and conflict resolutions |

### 7.2 Out of Scope

| Category | Rationale |
|----------|-----------|
| Generated artifacts | `node_modules/`, `dist/`, `build/` - regenerate locally |
| System packages | Use system package managers, not this tool |
| Large binary files | Not designed for large assets; use git-lfs or cloud storage |
| Real-time sync | Manual push/pull model; not continuous sync |
| Multi-user sync | Single user across their own machines |
| Production secrets | Use proper secrets management for production |
| Full machine backup | This is environment sync, not backup |
| Automatic dependency install | Separate concern; this is config, not provisioning |

### 7.3 Boundary Decisions

| Decision | Included | Excluded | Rationale |
|----------|----------|----------|-----------|
| File size | < 10MB per file | ≥ 10MB | Large files suggest wrong tool |
| Project scope | Configured roots only | Arbitrary paths | Bounded search space |
| Platform support | macOS, Ubuntu/WSL | Windows native, other Linux | User's actual machines |
| Shell support | bash, zsh | fish, others | User's actual shells |

---

## 8. Data Model (Conceptual)

### 8.1 Entities

```
Machine
├── name: string (user-assigned identifier)
├── platform: enum (macos | wsl | linux)
├── project_roots: list<path>
└── registered_at: timestamp

Project
├── name: string (folder name)
├── paths: map<machine_name, local_path>
├── essentials: list<EssentialPattern>
└── discovered_at: timestamp

SyncItem
├── id: string (content-addressable or path-based)
├── scope: enum (global | project)
├── relative_path: string
├── content_hash: string
├── last_modified_by: machine_name
├── last_modified_at: timestamp
└── is_sensitive: boolean

Manifest
├── version: string
├── machines: list<Machine>
├── projects: list<Project>
├── items: list<SyncItem>
└── last_operations: list<Operation>

Conflict
├── item: SyncItem
├── local_state: {hash, content, modified_at}
├── remote_state: {hash, content, modified_at}
├── status: enum (pending | resolved)
└── resolution: enum (use_local | use_remote | merged) | null

Operation
├── type: enum (push | pull | resolve)
├── machine: machine_name
├── timestamp: timestamp
├── items_affected: count
└── conflicts_resolved: list<resolution_summary>
```

### 8.2 Relationships

```
Machine 1──* Project (via path mapping)
Project 1──* SyncItem (project-scoped items)
Machine 1──* SyncItem (global items belong to machine that last modified)
SyncItem 1──0..1 Conflict (item may have pending conflict)
Operation *──1 Machine (operation performed on a machine)
```

### 8.3 Essential Discovery (Abstract Requirement)

The system must identify and capture **gitignored essentials** - files that are:
1. Present in a project directory
2. Gitignored (not tracked by the project's git)
3. Necessary for project function (not generated artifacts)

**Categories of essentials** (non-exhaustive):
- Environment/secrets (`.env*`, credential files)
- Provider configs (deployment platform directories)
- Cloud configs (cloud provider directories)
- Tool configs (IDE, LSP, toolchain settings)
- Auth state (tokens, session files, auth caches)

**The problem**: Essentials vary by project, toolchain, and time. New services create new patterns. A static list cannot anticipate all variations.

**The requirement**: The solution must include a discovery mechanism that:
- Identifies candidates (gitignored, non-generated files)
- Allows user validation (prevent false positives and negatives)
- Evolves as new patterns emerge

This is a discovery problem, not an enumeration problem.

**Critical design principle**: Discovery is PERMISSIVE, validation is RESTRICTIVE.
- Discovery should find everything plausible (err toward false positives)
- Validation lets user narrow down (reject what doesn't belong)
- This is safer than restrictive discovery which silently misses essentials

An implementation that restricts at discovery time will under-capture. Trust the user to reject junk; don't trust the system to predict what's essential.

### 8.4 User Validation Requirements

Discovery without validation produces garbage. The validation mechanism must address:

**When validation occurs**:
- On first discovery of a new project
- When new gitignored files appear in a tracked project
- On-demand when user suspects missed essentials

**What validation provides**:
- Present discovered candidates to user
- Allow accept/reject per item
- Allow manual addition of items discovery missed (false negative recovery)
- Persist decisions so accepted items sync automatically going forward

**What validation prevents**:
- False positives: Junk files captured and synced (user rejects)
- False negatives: Essential files missed (user manually adds)
- Decision fatigue: Once validated, item stays validated until explicitly changed

**The invariant**: No file is synced without explicit user acceptance (initial validation or prior acceptance).

---

## 9. State Model

***Note: The state diagrams below are illustrative suggestions, not prescriptive. The system designer should construct the appropriate state model based on implementation choices. Simpler or different state representations may be preferable.***

### 9.1 Machine States

```
                    ┌─────────────┐
                    │ Uninitialized│
                    └──────┬──────┘
                           │ setup
                           ▼
                    ┌─────────────┐
         ┌─────────│  Configured │◄──────────┐
         │         └──────┬──────┘           │
         │                │ push/pull        │
         │                ▼                  │ resolve
         │         ┌─────────────┐           │
         │    ┌───▶│   Synced    │───┐       │
         │    │    └──────┬──────┘   │       │
         │    │           │          │       │
   local │    │ push      │ local    │ pull  │
   change│    │           │ change   │ with  │
         │    │           ▼          │conflict│
         │    │    ┌─────────────┐   │       │
         │    └────│    Dirty    │   │       │
         │         └─────────────┘   │       │
         │                           ▼       │
         │                    ┌─────────────┐│
         └────────────────────│  Conflict   │┘
                              └─────────────┘
```

### 9.2 Item States

```
         ┌─────────────┐
         │  Untracked  │
         └──────┬──────┘
                │ capture
                ▼
         ┌─────────────┐
    ┌───▶│   Tracked   │◄───┐
    │    └──────┬──────┘    │
    │           │           │
push│           │ local     │ pull
    │           │ change    │ (clean)
    │           ▼           │
    │    ┌─────────────┐    │
    └────│  Modified   │────┘
         └──────┬──────┘
                │ pull (diverged)
                ▼
         ┌─────────────┐
         │  Conflict   │
         └──────┬──────┘
                │ resolve
                ▼
         ┌─────────────┐
         │   Tracked   │
         └─────────────┘
```

---

## 10. Invariants

Properties the system must actively enforce:

| ID | Invariant | Verification | Strictness |
|----|-----------|--------------|------------|
| I1 | All synced content encrypted before commit | Automated pre-commit verification of staged files | Strictly forbidden to violate - operation must not proceed |
| I2 | Manifest accurately reflects repository content | Hash verification of all items after each operation | Must self-correct if violated |
| I3 | Local changes detected before overwrite | Pull compares local hash to manifest before writing | Strictly forbidden - no silent overwrites |
| I4 | Machine-specific items only deployed to matching machine | Filter check during deployment | Must not deploy; may log/warn |
| I5 | Every sync operation logged | Append-only operation log | Required for auditability |
| I6 | Password required for both encrypt and decrypt | Prompt on every operation | Strictly required - no caching, no bypass |

**Note on I1**: The system cannot guarantee secrets were *never* exposed (past bugs, user error). It guarantees that *going forward*, all commits are verified before acceptance. Historical exposure requires separate audit (Layer 3 of FR5).

---

## 11. Success Criteria

### 11.1 Primary Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Machine switch time | Fast | Sit down → productive without waiting |
| New machine setup | Quick | Bare machine → all projects working without a "setup day" |
| Push/pull duration | Responsive | Should not feel sluggish or require waiting |
| Data loss incidents | 0 | Count of unrecoverable lost configurations |
| Secret exposure incidents | 0 | Count of plaintext secrets in git history |

**Verification of "all projects working"**: The system must provide a verification report after pull that confirms:
- All global configs deployed (list with status)
- All project essentials deployed (per-project list with status)
- Any items that failed or were skipped (with reason)

The user can inspect this report to confirm completeness. "Working" means: all tracked essentials are in place. Whether the project actually runs depends on factors outside sync scope (dependencies installed, services running, etc.).

### 11.2 Qualitative Success Criteria

| Criterion | Description |
|-----------|-------------|
| Invisible when working | User doesn't think about sync during normal work |
| Trustworthy | User confident their data is safe and synced |
| Predictable | User knows what will happen when they push/pull |
| Recoverable | User can fix problems without starting over |
| Maintainable | Future agents can understand and modify |

---

## 12. Verification Strategy

### 12.1 Functional Verification

| Test | Description | Expected Result |
|------|-------------|-----------------|
| T1: Round-trip global config | Create file on A, push, pull on B | Identical file on B |
| T2: Round-trip project config | Create .env on A, push, pull on B | .env in correct project path on B |
| T3: Conflict detection | Modify same file on A and B, push A, pull B | Conflict detected, not overwritten |
| T4: Conflict resolution | Resolve conflict using assistant | Resolution applied correctly |
| T5: New project discovery | Create project on A, push | Project appears in manifest |
| T6: Machine-specific isolation | Create machine-specific config | Not deployed to other machines |
| T7: Encryption verification | Inspect git history | No plaintext secrets |
| T8: Password protection | Attempt decrypt with wrong password | Fails gracefully |

### 12.2 Non-Functional Verification

| Test | Description | Expected Result |
|------|-------------|-----------------|
| P1: Performance | Typical push/pull | Feels responsive, not sluggish |
| P2: Reliability - interrupted push | Kill process mid-push | Recoverable state |
| P3: Reliability - interrupted pull | Kill process mid-pull | Recoverable state |
| P4: Usability - error messages | Trigger common errors | Clear remediation guidance |

### 12.3 Edge Case Verification

| Test | Description | Expected Result |
|------|-------------|-----------------|
| E1: Empty project | Project with no gitignored essentials | Registered but no capture |
| E2: Large file | File > 10MB | Warning or rejection |
| E3: Binary file | Binary config file | Handled correctly |
| E4: Special characters | Paths/filenames with spaces, unicode | Handled correctly |
| E5: Missing project | Project in manifest but not on disk | Graceful handling |
| E6: New essential type | New provider creates new config pattern | Discoverable or configurable |

---

## 13. Risk Analysis

### 13.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Complexity creep | High | High | See Section 13.4: Complexity Guardrails |
| Path mapping failures | Medium | Medium | Clear project identity; explicit override mechanism |
| Encryption failures | Low | Critical | Use proven tool (age); extensive testing |
| Performance degradation | Medium | Medium | Manifest-based tracking; avoid full scans |
| Platform incompatibility | Low | High | Test on both platforms continuously |

### 13.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Forgotten password | Low | Critical | Clear documentation; consider recovery mechanism |
| Corrupted manifest | Low | High | Backup manifest; recovery procedures |
| Git conflicts in sync repo | Low | Medium | Clear resolution guidance |
| Accidental secret exposure | Low | Critical | Pre-commit validation; defensive design |

### 13.3 Adoption Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Too complex to use | Medium | High | Single command interface; minimal config |
| Doesn't fit workflow | Low | High | Designed around actual user workflow |
| Maintenance burden | Medium | Medium | Simple code; good documentation |

### 13.4 Complexity Guardrails

Indicators that complexity is creeping in (suggestions, not hard rules):

**Code smells**:
- Single file getting unwieldy (common threshold: ~500 lines)
- Deep conditional nesting
- External dependencies growing beyond core (git, age, bash)
- Configuration file becoming complex
- User must understand internal concepts to operate

**Feature smells**:
- Feature requires explaining "why you'd want this"
- Feature handles a scenario that hasn't actually occurred
- Feature adds a flag/option to existing command
- Feature requires documentation longer than its implementation

**Process smells**:
- "We'll need this eventually" justification
- "While we're at it" scope additions
- Implementing before user requests it

**Escalation path**: When any smell is detected, the default is to NOT add complexity. Burden of proof is on the addition: "What specific user pain does this eliminate, and is that pain real or hypothetical?"

---

## 14. Assumptions

| ID | Assumption | If Violated |
|----|------------|-------------|
| A1 | User has git configured and accessible on all machines | Setup will fail; document prerequisite |
| A2 | User remembers encryption password | Cannot recover data; document risk |
| A3 | Project folder names are reasonably consistent across machines | Path mapping becomes complex; allow override |
| A4 | User initiates sync manually (not automatic) | Design doesn't change; feature could be added |
| A5 | Conflicts are rare (one machine active at a time) | Resolution flow becomes more critical |
| A6 | Internet connectivity available for sync | Offline work with later sync is acceptable |
| A7 | Git remote is accessible from all machines | Same remote; no multi-remote complexity |

---

## 15. Dependencies

### 15.1 External Dependencies

| Dependency | Purpose | Version Requirement | Fallback |
|------------|---------|---------------------|----------|
| Git | Transport, storage, history | 2.0+ | None (required) |
| Age | Encryption | 1.0+ | Could substitute gpg |
| Bash | Scripting | Works on macOS default bash | None for core |
| Claude Code | Conflict resolution assistant | Any | Manual resolution |

### 15.2 Internal Dependencies

| Component | Depends On | Nature |
|-----------|------------|--------|
| Push | Manifest, Encryption, Git | Must have current manifest; encrypt before commit |
| Pull | Manifest, Decryption, Git, Conflict Detection | Must detect conflicts before overwrite |
| Conflict Resolution | Pending conflicts file, User interaction | Cannot resolve without conflict data |
| Project Discovery | Configured project roots, Git detection | Scans only configured paths |

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Essential** | A file or directory that is gitignored but necessary for project function |
| **Global config** | Configuration that applies across all projects (lives in home directory) |
| **Machine-specific** | Configuration that varies per machine (paths, tools, hardware settings) |
| **Manifest** | The index of all tracked items, machines, and projects |
| **Project root** | A directory that contains project repositories |
| **Sync item** | A single file or directory being tracked for synchronization |
| **Conflict** | State where same item modified on multiple machines since last sync |
| **Resolution** | The decision on how to handle a conflict (local, remote, or merged) |

---

## 17. Open Questions

Questions that require design-time decisions. These are scope boundaries to **close**, not features to add. Each should be resolved with a clear yes/no or specific constraint during design phase:

1. **Deletion propagation**: If a file is deleted on one machine, should that propagate to others?
2. **Partial pull**: Can user pull only specific items (e.g., just Claude config)?
3. **Size limits**: What's the maximum reasonable file size to sync?
4. **New essential patterns**: How does user add support for new gitignored patterns?
5. **Merge vs replace**: For conflicts, should we support actual content merging or just pick one?
6. **History depth**: How much operation history to retain?
7. **Manifest versioning**: How to handle manifest format changes?
8. **Recovery mode**: What happens if manifest becomes corrupt?

---

## 18. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-05 | Claude | Initial problem model |
| 1.1 | 2025-01-05 | Claude | Set 1 review: Abstracted essential discovery (8.3), added verification mechanism (11.1), clarified HC4 nominal vs edge cases |
| 1.2 | 2025-01-05 | Claude | Set 2 review: Defense-in-depth for FR5, reframed invariants with enforcement column, removed aspirational "never" language |
| 1.3 | 2025-01-05 | Claude | Set 3 review: Added user validation requirements (8.4), made FR8 a completeness requirement with verification |
| 1.4 | 2025-01-05 | Claude | Set 4 review: Added complexity guardrails (13.4), clarified permissive discovery principle, added generated artifact heuristics |
| 1.5 | 2025-01-05 | Claude | Holistic review: Scrubbed invented numbers, clarified HC7 (bash-based not version-specific), marked complexity thresholds as suggestions |
| 1.6 | 2025-01-05 | Claude | Added note to Section 9 clarifying state diagrams are illustrative, not prescriptive |
| 1.7 | 2025-01-05 | Claude | Section 10: Changed "Enforcement" to "Strictness" with general severity language instead of design prescriptions |
| 1.8 | 2025-01-05 | Claude | NFR1: Added scale context (10→50+ projects), performance-sensitive operations, and key concern about large directory traversal |
| 1.9 | 2025-01-05 | Claude | Set 5 review: Clarified content inspection use cases, added edge case section for nested sub-projects and external secrets |
| 1.10 | 2025-01-05 | Claude | Session close: Updated README with vision status, created handoff document |

---

## Summary for New Agents

**What this project is about**: Synchronizing development environment configuration across multiple machines (macOS + WSL), including secrets, shell config, Claude Code settings, and per-project gitignored essentials.

**The core challenge**: Security (secrets must be encrypted) + Convenience (must be effortless) + Flexibility (global + project-level) + Heterogeneity (different platforms, different paths).

**What we're NOT building**: A backup system, a team collaboration tool, a secrets manager for production, or a configuration management system.

**Success looks like**: Developer runs one command, enters password, and their entire environment is synchronized. Switching machines is quick. New machine is productive without a "setup day."

**Key constraints**: Single command interface, password-based encryption, git-based transport, bash-based (works on both platforms), no manual steps beyond password for daily operations (edge cases like new projects or conflicts may prompt).

Read the VISION.md for the user-perspective narrative. This document provides the technical problem model.

# devenv System Design

**Version**: 0.3
**Date**: 2026-01-05
**Status**: Design Complete (pending implementation planning)

---

## Document Purpose & Audience

**This document is written for AI agents** who will:
1. Digest this design to understand the system architecture
2. Build an implementation plan from these specifications
3. Execute implementation against this design

**Writing principles applied**:
- **Explicit over implicit**: Constraints, interfaces, and behaviors are stated directly. Do not infer intent from ambiguity.
- **Self-contained sections**: Each component specification should be understandable without extensive cross-referencing.
- **Clear contracts**: Inputs, outputs, and error conditions are specified for key interfaces.
- **Actionable specifications**: If you cannot determine what to build from a section, the section is incomplete.

**Prerequisites**: Read PROBLEM-MODEL.md and DECISIONS.md before this document. Those documents provide the "why"; this document provides the "what."

---

## 1. Architecture Overview

### 1.1 Design Philosophy

**Manifest-driven**: All sync operations reference a central manifest. The manifest is the source of truth for what should be synced, where it lives on each machine, and its current state.

**Discovery-driven capture**: New essentials are found through automated discovery, not manual registration. Discovery is permissive; validation is restrictive.

**Defense-in-depth**: Multiple security layers. Encryption is necessary but not sufficient.

**Incremental by default**: Operations compare current state to manifest state. Full scans are explicit opt-in.

### 1.2 High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         devenv CLI                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  push    │ │  pull    │ │ discover │ │ validate │  ...      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                  │
│       └────────────┴─────┬──────┴────────────┘                  │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────┐      │
│  │                   Core Engine                          │      │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │      │
│  │  │ Manifest   │ │ Discovery  │ │ Sync Operations    │ │      │
│  │  │ Manager    │ │ Engine     │ │ (push/pull/deploy) │ │      │
│  │  └────────────┘ └────────────┘ └────────────────────┘ │      │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │      │
│  │  │ Conflict   │ │ Validation │ │ Path Mapper        │ │      │
│  │  │ Detector   │ │ Workflow   │ │                    │ │      │
│  │  └────────────┘ └────────────┘ └────────────────────┘ │      │
│  └───────────────────────────────────────────────────────┘      │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────┐      │
│  │                  Library Layer                         │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │      │
│  │  │ platform │ │ crypto   │ │ git      │ │ yaml     │  │      │
│  │  │ .sh      │ │ .sh      │ │ .sh      │ │ .sh      │  │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ devenv.yaml  │  │ devenv.local   │  │ secrets.yaml.age   │   │
│  │ (manifest)   │  │ .yaml          │  │ (encrypted vault)  │   │
│  └──────────────┘  └────────────────┘  └────────────────────┘   │
│  ┌──────────────┐  ┌────────────────┐                           │
│  │ vault/       │  │ staging/       │                           │
│  │ (encrypted   │  │ (pre-encrypt   │                           │
│  │  content)    │  │  workspace)    │                           │
│  └──────────────┘  └────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Directory Structure

```
env-sync/
├── src/devenv/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point (click or argparse)
│   ├── manifest.py         # Manifest operations
│   ├── discovery.py        # Discovery engine
│   ├── conflict.py         # Conflict detection/resolution
│   ├── validation.py       # Validation workflow
│   ├── crypto.py           # Encryption/decryption (calls age CLI)
│   ├── paths.py            # Path mapping and resolution
│   └── models.py           # Dataclasses for Manifest, Item, Project, etc.
├── tests/
│   ├── test_manifest.py
│   ├── test_discovery.py
│   └── ...
├── pyproject.toml          # Package config, dependencies
├── devenv.yaml             # Shared manifest (committed)
├── devenv.local.yaml       # Machine-specific config (gitignored)
├── secrets.yaml.age        # Encrypted secrets vault
├── vault/                  # Encrypted sync content (committed)
│   ├── global/             # Global configs (encrypted)
│   └── projects/           # Project configs (encrypted)
├── staging/                # Temporary workspace (gitignored)
├── docs/
│   ├── PROBLEM-MODEL.md
│   ├── VISION.md
│   ├── design/
│   │   ├── SYSTEM-DESIGN.md    # This document
│   │   └── DECISIONS.md
│   └── schemas/                # Immutable versioned schema files
│       ├── manifest-v1.0.yaml
│       └── README.md
└── README.md
```

---

## 2. Data Model

### 2.1 Manifest Structure (devenv.yaml)

```yaml
# devenv.yaml - Shared manifest (committed to git)
version: "1.0"

# Registered machines
machines:
  macbook:
    platform: macos
    registered_at: "2026-01-05T10:00:00Z"
    project_roots:
      - ~/cc-projects
      - ~/projects
  desktop:
    platform: wsl
    registered_at: "2026-01-05T12:00:00Z"
    project_roots:
      - ~/projects

# Known projects (keyed by normalized git remote URL)
projects:
  "github.com/memorymuse/muse-v1":
    paths:
      macbook: ~/cc-projects/muse-v1
      desktop: ~/projects/muse/muse-v1
    discovered_at: "2026-01-05T10:15:00Z"
    last_scanned_at: "2026-01-05T18:00:00Z"

  "github.com/kysonk/general-tools":
    paths:
      macbook: ~/cc-projects/general-tools
      desktop: ~/projects/general-tools
    discovered_at: "2026-01-05T10:15:00Z"
    last_scanned_at: "2026-01-05T18:00:00Z"

# Sync items - what we're tracking
# Keyed by: scope/relative_path
items:
  # Global items
  "global:~/.claude/CLAUDE.md":
    type: file
    scope: global
    sensitive: false
    status: active           # active | deleted (per D8)
    content_hash: "sha256:abc123..."
    last_modified_by: macbook
    last_modified_at: "2026-01-05T17:30:00Z"
    # If deleted:
    # deleted_at: "2026-01-06T10:00:00Z"
    # deleted_by: macbook

  "global:~/.claude/settings.json":
    type: file
    scope: global
    sensitive: true  # Contains API keys
    content_hash: "sha256:def456..."
    last_modified_by: macbook
    last_modified_at: "2026-01-05T17:30:00Z"

  "global:~/.claude/skills":
    type: directory
    scope: global
    sensitive: false
    content_hash: "sha256:ghi789..."  # Hash of directory contents
    last_modified_by: macbook
    last_modified_at: "2026-01-05T17:30:00Z"

  # Project items (use project ID + relative path)
  "project:github.com/memorymuse/muse-v1:.env":
    type: file
    scope: project
    sensitive: true
    content_hash: "sha256:jkl012..."
    last_modified_by: desktop
    last_modified_at: "2026-01-05T16:00:00Z"

# Validation decisions - patterns user has accepted/rejected
validation:
  accepted_patterns:
    - "**/.env"
    - "**/.env.*"
    - "**/.vercel"
    - "**/.netlify"
    - "~/.claude/**"
  rejected_patterns:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/dist/**"
    - "**/build/**"

# Claude Code specific
claude:
  exclusions:
    - plugins/cache
    - statsig_metadata
  last_completeness_check: "2026-01-05T17:30:00Z"

# Operation log (last N operations)
operations:
  - type: push
    machine: macbook
    timestamp: "2026-01-05T17:30:00Z"
    items_affected: 12
    conflicts_resolved: 0

  - type: pull
    machine: desktop
    timestamp: "2026-01-05T16:00:00Z"
    items_affected: 12
    conflicts_resolved: 0
```

### 2.2 Machine-Local Config (devenv.local.yaml)

```yaml
# devenv.local.yaml - Machine-specific config (gitignored)
# This file is NOT committed - each machine has its own

machine_name: macbook
# or: machine_name: desktop

# Override project roots if different from manifest default
project_roots:
  - ~/cc-projects
  - ~/projects

# Machine-specific path overrides (rare)
path_overrides:
  # If a project is in a non-standard location on THIS machine
  "github.com/example/repo": ~/weird/path/repo

# Local preferences
preferences:
  # Skip validation prompts for these patterns
  auto_accept_patterns:
    - "**/.env.local"
```

### 2.3 Vault Storage Structure

```
vault/
├── global/
│   ├── claude/                    # ~/.claude/ contents
│   │   ├── CLAUDE.md.age         # Individual files encrypted
│   │   ├── settings.json.age
│   │   ├── skills.tar.age        # Directories as encrypted tarballs
│   │   └── commands.tar.age
│   ├── gitconfig.age             # ~/.gitconfig
│   └── env.secrets.age           # ~/.env.secrets
└── projects/
    ├── github.com_memorymuse_muse-v1/
    │   ├── .env.age
    │   └── .vercel.tar.age
    └── github.com_kysonk_general-tools/
        └── env-sync/
            └── .env.age
```

### 2.4 Conflict State (when detected)

```yaml
# In-memory or temporary file during resolution
conflicts:
  - item_id: "project:github.com/memorymuse/muse-v1:.env"
    local_state:
      content_hash: "sha256:aaa..."
      modified_at: "2026-01-05T17:00:00Z"
    remote_state:
      content_hash: "sha256:bbb..."
      modified_at: "2026-01-05T16:30:00Z"
      modified_by: desktop
    status: pending
    resolution: null  # Will be: use_local | use_remote | merged
```

---

## 3. Component Specifications

### 3.1 Manifest Manager (`manifest.py`)

**Responsibilities**:
- Load/save manifest YAML
- Query items by scope, project, pattern
- Update item state (hash, timestamp, modifier)
- Manage validation decisions
- Log operations

**Key Interface**:
```python
@dataclass
class Manifest:
    version: str
    machines: dict[str, Machine]
    projects: dict[str, Project]
    items: dict[str, SyncItem]
    validation: ValidationConfig
    operations: list[Operation]

class ManifestManager:
    def load(self, path: Path, local_path: Path) -> Manifest: ...
    def save(self, manifest: Manifest, path: Path) -> None: ...
    def get_item(self, item_id: str) -> SyncItem | None: ...
    def set_item(self, item_id: str, item: SyncItem) -> None: ...
    def get_items_by_scope(self, scope: Scope) -> list[SyncItem]: ...
    def get_items_by_project(self, project_id: str) -> list[SyncItem]: ...
    def is_pattern_accepted(self, pattern: str) -> bool: ...
    def add_accepted_pattern(self, pattern: str) -> None: ...
    def log_operation(self, op: Operation) -> None: ...
    def get_machine_name(self) -> str: ...  # From local config
    def get_project_path(self, project_id: str) -> Path | None: ...
```

### 3.2 Discovery Engine (`discovery.py`)

**Responsibilities**:
- Find gitignored essentials across projects
- Identify new items not in manifest
- Apply traversal limits and blocklists
- Support incremental and full scan modes

**Scan Mode Triggers**:
- **Incremental** (default on `devenv push`): Only scan projects where `last_scanned_at` < project directory mtime. Skip unchanged projects.
- **Full** (on `devenv discover --full` or first run): Scan all registered projects regardless of timestamps.
- **Claude completeness**: Runs on every push. Scans `~/.claude/`, compares to manifest, flags new items for validation.

**Key Interface**:
```python
@dataclass
class DiscoveredItem:
    path: Path
    item_type: Literal["file", "directory"]
    size: int

class DiscoveryEngine:
    BLOCKLIST: ClassVar[set[str]] = {"node_modules", "dist", "build", ...}
    ESSENTIAL_PATTERNS: ClassVar[list[str]] = [".env", ".env.*", ".vercel", ...]

    def scan_project(self, project_path: Path) -> list[DiscoveredItem]: ...
    def scan_all_projects(self, manifest: Manifest) -> list[DiscoveredItem]: ...
    def scan_claude_config(self) -> list[DiscoveredItem]: ...
    def get_pending_items(self, manifest: Manifest) -> list[DiscoveredItem]: ...
    def is_blocked_path(self, path: Path) -> bool: ...

    def _find_gitignored_essentials(self, project_path: Path) -> list[DiscoveredItem]:
        """Uses: git -C <path> ls-files --others --ignored --exclude-standard"""
        ...
```

**Blocklist** (hardcoded, not configurable):
```bash
DISCOVERY_BLOCKLIST=(
    "node_modules"
    "dist"
    "build"
    ".cache"
    "target"
    "__pycache__"
    ".venv"
    "venv"
    ".git"
)
```

**Essential Patterns** (default, extensible via manifest):
```bash
ESSENTIAL_PATTERNS=(
    ".env"
    ".env.*"
    ".envrc"
    ".vercel"
    ".netlify"
    ".firebase"
    ".amplify"
    ".aws"
    ".gcloud"
)
```

**Discovery Algorithm** (`_find_gitignored_essentials`):
```
Input: project_path (directory containing .git)
Output: list of {path, type, size} for candidate essentials

Algorithm:
1. Get gitignored files:
   cmd: git -C <project_path> ls-files --others --ignored --exclude-standard

2. Filter results:
   For each path:
     - Skip if any path component matches DISCOVERY_BLOCKLIST
     - Skip if file size > 5MB (per D10)
     - Include if basename matches any ESSENTIAL_PATTERNS
     - Include if path is directory matching pattern (e.g., .vercel/)

3. Return filtered list with metadata:
   { path: relative_path, type: file|directory, size: bytes }

Edge cases:
- No .git directory: skip project, log warning
- No .gitignore: returns empty (nothing is ignored)
- Nested gitignores: git ls-files handles this natively
```

### 3.3 Conflict Detector (`conflict.py`)

**Responsibilities**:
- Compare local file state to manifest
- Detect divergence (both local and remote changed)
- Track conflict state during resolution
- Apply resolution decisions

**Key Interface**:
```python
@dataclass
class Conflict:
    item_id: str
    item_path: Path
    local_hash: str
    local_content: str
    local_modified_at: datetime
    remote_hash: str
    remote_content: str
    remote_modified_at: datetime
    remote_modified_by: str

class ConflictDetector:
    def check_item(self, item_id: str, manifest: Manifest) -> Conflict | None: ...
    def check_all(self, manifest: Manifest) -> list[Conflict]: ...
    def get_pending(self) -> list[Conflict]: ...
    def resolve(self, item_id: str, resolution: Resolution) -> None: ...
    def write_conflict_context(self, conflicts: list[Conflict], path: Path) -> None: ...
    def read_resolutions(self, path: Path) -> list[Resolution]: ...
```

**Conflict Detection Logic**:
```
On pull:
  For each item in manifest:
    local_hash = compute_hash(local_path)
    manifest_hash = manifest.items[item_id].content_hash

    if local_hash == manifest_hash:
      # No local changes, safe to update
      continue

    if manifest.items[item_id].last_modified_by == this_machine:
      # We made the remote change, this is just stale local
      continue

    # Different hash, different modifier = CONFLICT
    record_conflict(item_id, local_hash, manifest_hash)
```

**Agent-Assisted Resolution Interface**:

When conflicts are detected, the system invokes agent assistance by default (per D12).

*Conflict context file* (written to `staging/conflicts.yaml`):
```yaml
conflicts:
  - item_id: "project:github.com/example/repo:.env"
    item_path: "~/.env"  # Resolved for this machine
    local:
      content: |
        # Local version content here
        API_KEY=local_value
      modified_at: "2026-01-05T10:00:00Z"
    remote:
      content: |
        # Remote version content here
        API_KEY=remote_value
      modified_at: "2026-01-05T09:00:00Z"
      modified_by: desktop
```

*Resolution file* (agent writes to `staging/resolutions.yaml`):
```yaml
resolutions:
  - item_id: "project:github.com/example/repo:.env"
    action: merge  # or: use_local, use_remote
    merged_content: |
      # Merged by agent
      API_KEY=remote_value
```

*Handoff*: CLI detects conflicts → writes context file → invokes `/devenv-resolve` skill or prompts user → reads resolution file → applies.

*Fallback*: If agent unavailable, CLI prompts: "[L]ocal / [R]emote / [S]kip?"

### 3.4 Validation Workflow (`validation.py`)

**Responsibilities**:
- Present discovered items for user review
- Collect accept/reject decisions
- Persist decisions to manifest
- Support both interactive and batch modes

**Key Interface**:
```python
class ValidationWorkflow:
    INTERACTIVE_THRESHOLD: ClassVar[int] = 10

    def start(self, items: list[DiscoveredItem]) -> None: ...
    def prompt_interactive(self, items: list[DiscoveredItem]) -> list[ValidationDecision]: ...
    def generate_file(self, items: list[DiscoveredItem], path: Path) -> None: ...
    def process_file(self, path: Path) -> list[ValidationDecision]: ...
    def commit_decisions(self, decisions: list[ValidationDecision], manifest: Manifest) -> None: ...
```

**Interactive Prompt Format** (≤10 items):
```
Discovered 3 new items:

  1. ~/cc-projects/new-project/.env
     Type: file, Size: 256 bytes
     [a]ccept / [r]eject / [s]kip / [v]iew

  2. ~/cc-projects/new-project/.vercel/
     Type: directory
     [a]ccept / [r]eject / [s]kip / [v]iew

Choice for #1: _
```

**File-Based Validation** (>10 items):

Generated file location: `staging/pending-validation.yaml`

```yaml
# Pending Validation - Edit this file and run: devenv validate
# Mark each item: accept, reject, or skip
# Save and close when done

items:
  - path: ~/cc-projects/new-project/.env
    type: file
    size: 256
    decision: pending  # Change to: accept, reject, or skip

  - path: ~/cc-projects/new-project/.vercel/
    type: directory
    decision: pending

  - path: ~/.claude/new-config.json
    type: file
    size: 128
    decision: pending
```

Processing rules:
- `accept`: Add to manifest, include in sync
- `reject`: Add to `validation.rejected_patterns` (won't be discovered again)
- `skip`: Ignore for now, will be discovered again next time
- `pending` or missing: Treated as skip

### 3.5 Path Mapper (`paths.py`)

**Responsibilities**:
- Resolve project paths for current machine
- Handle path normalization (~, relative)
- Map between project ID and local path

**Key Interface**:
```python
class PathMapper:
    def get_project_id(self, local_path: Path) -> str:
        """Extract git remote URL, normalize to project ID."""
        ...

    def get_local_path(self, project_id: str, manifest: Manifest) -> Path | None:
        """Look up this machine's path for project, with override support."""
        ...

    def normalize(self, path: str | Path) -> Path:
        """Expand ~, resolve .., return absolute Path."""
        ...

    def register_project(self, local_path: Path, manifest: Manifest) -> str:
        """Add project to manifest, return project ID."""
        ...
```

### 3.6 Crypto Module (`crypto.py`)

**Responsibilities**:
- Encrypt files/directories with age
- Decrypt on demand
- Hash computation for conflict detection

**Key Interface**:
```python
class CryptoModule:
    def __init__(self, password: str): ...

    def encrypt_file(self, source: Path, dest: Path) -> None:
        """Calls: age -p -o <dest> <source>"""
        ...

    def decrypt_file(self, source: Path, dest: Path) -> None:
        """Calls: age -d -o <dest> <source>"""
        ...

    def encrypt_directory(self, source: Path, dest: Path) -> None:
        """Tar directory, then encrypt."""
        ...

    def decrypt_directory(self, source: Path, dest: Path) -> None:
        """Decrypt, then untar."""
        ...

    def compute_hash(self, path: Path) -> str:
        """SHA256 of file or directory contents."""
        ...

    def verify_encryption(self, file: Path) -> bool:
        """Check .age extension and valid age header."""
        ...

@contextmanager
def get_password() -> Generator[str, None, None]:
    """Prompt once, yield password, clear from memory on exit."""
    password = getpass.getpass("Encryption password: ")
    try:
        yield password
    finally:
        # Clear password from memory (best effort)
        del password
```

**Password Handling**:
- Single prompt per session via `getpass.getpass()` (no echo)
- Passed to age via subprocess stdin (not environment variable)
- Never written to disk

---

## 4. Command Interface

### 4.1 Primary Commands

```bash
devenv push [message]
```
- Discover new items in all projects
- Validate new discoveries (if any)
- Encrypt changed items
- Commit and push to git

```bash
devenv pull
```
- Git pull
- Check for conflicts
- If conflicts: halt and report, else continue
- Decrypt and deploy items

```bash
devenv status
```
- Show manifest state
- Show pending changes
- Show any unresolved conflicts

### 4.2 Discovery Commands

```bash
devenv discover [--full]
```
- Run discovery scan
- Default: incremental (only projects changed since last scan)
- `--full`: comprehensive scan of all projects
- Present new items for validation

```bash
devenv validate
```
- Resume validation of pending items
- Interactive or file-based depending on count

### 4.3 Conflict Resolution

```bash
devenv conflicts
```
- List unresolved conflicts

```bash
devenv resolve [--all-local | --all-remote | --interactive]
```
- Resolve conflicts
- `--all-local`: keep all local versions
- `--all-remote`: accept all remote versions
- `--interactive`: decide each one (default)

### 4.4 Machine Management

```bash
devenv init [machine-name]
```
- First-time setup
- Register machine in manifest
- Configure project roots
- Create local config

```bash
devenv machines
```
- List registered machines

### 4.5 Project Management

```bash
devenv projects
```
- List tracked projects

```bash
devenv project add [path]
```
- Manually add project to tracking

### 4.6 Vault Commands (Legacy Compatibility)

```bash
devenv vault edit
```
- Edit secrets (decrypt -> $EDITOR -> re-encrypt)

```bash
devenv vault diff
```
- Compare vault to deployed

---

## 5. Sync Flow Specifications

### 5.1 Push Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        devenv push                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Load manifest                                             │
│    - Read devenv.yaml                                        │
│    - Read devenv.local.yaml (machine-specific)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Discovery phase                                           │
│    - Scan ~/.claude/ for completeness                        │
│    - Scan each project for gitignored essentials             │
│    - Compare to manifest, identify new items                 │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ New items found?              │
              └───────────────┬───────────────┘
                    Yes │           │ No
                        ▼           │
┌──────────────────────────────┐   │
│ 3. Validation phase          │   │
│    - Present new items       │   │
│    - Collect accept/reject   │   │
│    - Update manifest         │   │
└──────────────────────────────┘   │
                    │               │
                    └───────┬───────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Capture phase                                             │
│    For each accepted item:                                   │
│    - Compute content hash                                    │
│    - If changed since last push:                             │
│      - Copy to staging/                                      │
│      - Mark for encryption                                   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ Any changes to sync?          │
              └───────────────┬───────────────┘
                    Yes │           │ No
                        ▼           │
┌──────────────────────────────┐   │
│ 5. Encryption phase          │   │    ┌──────────────────┐
│    - Prompt for password     │   │    │ "Already in sync" │
│    - Encrypt staged items    │   ├───►│ Exit             │
│    - Move to vault/          │   │    └──────────────────┘
└──────────────────────────────┘   │
                    │               │
                    ▼               │
┌─────────────────────────────────────────────────────────────┐
│ 6. Update manifest                                           │
│    - Update content_hash for each item                       │
│    - Set last_modified_by = this machine                     │
│    - Set last_modified_at = now                              │
│    - Log operation                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Encryption verification (Invariant I1)                    │
│    - Scan vault/ for any non-.age files                      │
│    - Verify each .age file has valid age header              │
│    - ABORT if plaintext detected (do not proceed to commit)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Git commit and push                                       │
│    - Stage: devenv.yaml, vault/                              │
│    - Commit with message                                     │
│    - Push to remote                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         [Complete]
```

### 5.2 Pull Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        devenv pull                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Git pull                                                  │
│    - Fetch and merge from remote                             │
│    - Handle git merge conflicts if any (abort if present)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Load updated manifest                                     │
│    - Read devenv.yaml (now updated)                          │
│    - Read devenv.local.yaml                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Conflict detection                                        │
│    For each item in manifest:                                │
│    - Compute local content hash                              │
│    - Compare to manifest hash                                │
│    - If different AND not modified by this machine:          │
│      - Record as conflict                                    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ Conflicts detected?           │
              └───────────────┬───────────────┘
                    Yes │           │ No
                        ▼           │
┌──────────────────────────────┐   │
│ 4a. Conflict resolution      │   │
│    - Write staging/conflicts │   │
│      .yaml with both versions│   │
│    - Invoke agent resolution │   │
│      (or fallback to manual) │   │
│    - Read staging/resolutions│   │
│      .yaml, apply decisions  │   │
└──────────────────────────────┘   │
                    │               │
                    └───────┬───────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Decryption phase                                          │
│    - Prompt for password                                     │
│    - Decrypt changed vault/ items to staging/                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Deployment phase                                          │
│    For each decrypted item:                                  │
│    - Resolve target path for this machine                    │
│    - Deploy (copy/extract) to target                         │
│    - Set appropriate permissions (600 for sensitive)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Verification report                                       │
│    - List all deployed items with status                     │
│    - Report any failures or skips                            │
│    - Log operation to manifest                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Cleanup                                                   │
│    - Remove decrypted files from staging/                    │
│    - (Plaintext should never persist on disk)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         [Complete]
```

---

## 6. Security Specifications

### 6.1 Defense-in-Depth Layers (per FR5)

**Layer 1 - Encryption**:
- All sensitive content encrypted with age before git commit
- Password-based encryption (no key files)
- Content in `vault/` is always encrypted

**Layer 2 - Pre-commit Verification**:
- Before `git add`, verify all files in vault/ are encrypted
- Check for `.age` extension AND valid age header
- Abort push if plaintext detected

**Layer 3 - Audit Scan**:
- `devenv audit` command to scan git history for accidental plaintext
- Uses gitleaks for pattern detection
- Report any historical exposure

**Layer 4 - Recovery Procedure**:
- If exposure detected, document rotation procedure
- Cannot un-expose, but can invalidate exposed credentials
- `devenv audit --remediate` suggests which secrets need rotation

### 6.2 Password Handling

```python
import getpass
from contextlib import contextmanager

@contextmanager
def password_session():
    """Prompt once, provide password to operations, clear on exit."""
    password = getpass.getpass("Encryption password: ")
    try:
        yield password
    finally:
        del password  # Best-effort memory clearing

# Usage in CLI:
with password_session() as password:
    crypto = CryptoModule(password)
    # ... all encrypt/decrypt operations use this instance
```

**Key differences from bash approach**:
- Uses `getpass` (no echo, cross-platform)
- Password passed directly to CryptoModule, not stored in environment
- Context manager ensures cleanup

### 6.3 Interruption Recovery

If push or pull is interrupted, `staging/` may contain plaintext. Recovery:

1. **Detection**: On startup, check if `staging/` is non-empty
2. **Action**: If non-empty, prompt: "Previous operation incomplete. Delete staging/ and retry? [Y/n]"
3. **Cleanup**: `rm -rf staging/*` before proceeding

This ensures plaintext doesn't persist across sessions.

### 6.4 Consistency Checks

**Manifest/vault consistency** (checked on pull):
- For each item in manifest with `status: active`, verify corresponding file exists in `vault/`
- Missing vault file = error, report to user, skip item
- Extra vault files not in manifest = warning (orphaned, suggest cleanup)

**Manual recovery** (without agent assistance):
- View git history: `git log --oneline devenv.yaml`
- Reset to known-good state: `git checkout <commit> -- devenv.yaml vault/`
- Re-run pull to deploy

### 6.5 File Permissions

| File | Permissions | Rationale |
|------|-------------|-----------|
| `devenv.yaml` | 644 | Shared manifest, not sensitive |
| `devenv.local.yaml` | 600 | Machine-specific, may have paths |
| `vault/*.age` | 644 | Encrypted, safe to share |
| `staging/*` | 600 | Decrypted content, temporary |
| Deployed `.env` | 600 | Sensitive, restrict access |

---

## 7. Dependencies

### 7.1 Runtime Requirements

| Dependency | Version | Purpose | Installation |
|------------|---------|---------|--------------|
| Python | 3.10+ | Runtime | Pre-installed on macOS/Ubuntu |
| PyYAML | ≥6.0 | YAML parsing | `pip install pyyaml` |
| age | ≥1.0 | Encryption | `brew install age` / `apt install age` |
| git | ≥2.0 | Transport, storage | Pre-installed |

### 7.2 Optional Dependencies

| Dependency | Purpose |
|------------|---------|
| gitleaks | Audit scan for exposed secrets (Layer 3) |

### 7.3 Installation

```bash
# Clone the repo
git clone <env-sync-repo> && cd env-sync

# Install Python package
pip install -e .

# Or with pyproject.toml
pip install .
```

The `devenv` command will be available after installation.

---

## 8. Operational Context

### 8.1 User Experience Expectations

**Steady-state operation** (daily use after setup):
- `devenv push`: Single command + password prompt. No confirmation prompts on happy path.
- `devenv pull`: Single command + password prompt. No confirmation prompts if no conflicts.

**First-time setup** (new user or new machine):
- Multi-step guided process, not "instant"
- Sequence: `devenv init` → discovery → validation → first push
- If many essentials discovered (>10), validation is file-based requiring manual review
- This complexity is inherent to initial capture; steady-state is simple

**New machine deployment**:
- Requires `devenv init [machine-name]` before first pull
- Cannot simply clone and pull - local config must be established first
- After init: `devenv pull` deploys all relevant content

**Skip reporting**:
- Pull skips items for projects not present on this machine
- Reporting is concise: "Skipped N items (projects not present)"
- Detailed list available via `devenv status`, not dumped to terminal

### 8.2 Migration from cc-isolate

#### 8.2.1 Migration Path

For existing cc-isolate users:

1. **Export current vault**: `cc-isolate vault decrypt` to get plaintext
2. **Run `devenv init`**: Creates new manifest structure
3. **Import vault**: Tool migrates secrets.yaml format to new structure
4. **Discover and validate**: `devenv discover` finds existing essentials
5. **First push**: Establishes new manifest baseline

#### 7.2.2 Command Mapping

| cc-isolate | devenv | Notes |
|------------|--------|-------|
| `cc-isolate push` | `devenv push` | Enhanced with discovery |
| `cc-isolate pull` | `devenv pull` | Enhanced with conflicts |
| `cc-isolate vault edit` | `devenv vault edit` | Same |
| `cc-isolate vault encrypt` | (automatic on push) | No longer manual |
| `cc-isolate vault decrypt` | (automatic on pull) | No longer manual |
| `cc-isolate status` | `devenv status` | Enhanced |
| `cc-isolate mount` | Deprecated | Profile isolation removed |
| `cc-isolate profile *` | Deprecated | Profile isolation removed |

#### 7.2.3 Deprecation Notice

After migration:
- `cc-isolate` symlinks to `devenv` with deprecation warning
- Profile commands (`mount`, `unmount`, `profile *`) print migration guide
- Full removal in future version

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-05 | Initial draft - architecture, data model, components, flows |
| 0.2 | 2026-01-05 | Removed open questions (moved to DECISIONS.md), removed implementation phases |
| 0.3 | 2026-01-05 | Added paths.sh to directory structure; Added Section 7.1 UX Expectations (self-review Set 1) |
| 0.4 | 2026-01-05 | Self-review Sets 2-7: Discovery algorithm, agent resolution interface, validation file format, scan triggers, encryption verification step, interruption recovery, consistency checks |

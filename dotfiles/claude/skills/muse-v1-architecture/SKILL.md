---
name: muse-v1-architecture
description: You MUST PROACTIVELY USE this skill when reasoning about, designing, planning, or reviewing Muse v1 systems. Provides architectural concepts, decision frameworks, and design rationale for event sourcing, memory, identity, and storage systems. ONLY for Muse v1 codebase work.
---

# Muse v1 Architecture Guide

Conceptual architecture and design decisions for Muse v1. Use this when reasoning about system design, planning features, or reviewing architectural choices.

**For implementation patterns and code**: See `muse-v1-implementation` skill.

---

## Core Philosophy

### Event Sourcing Foundation

Everything in Muse v1 is an event. All state changes are immutable, append-only records.

**Why Event Sourcing**:
1. **Immutability**: History cannot be corrupted
2. **Auditability**: Complete trail of what happened
3. **Replayability**: Rebuild state from events at any point
4. **Flexibility**: Derive new projections as needs evolve

**The Flow**:

```
Event → Memory → Conscious
  ↓        ↓         ↓
What    What     Current
happened matters  context
```

- **Events**: Authoritative source of truth (immutable)
- **Memories**: Derived projections (queryable, updatable)
- **Conscious**: Token-bounded context snapshot (deterministic)

### Memory Retention Economics

Not all information is equally valuable. Memories compete for survival.

**Retention as "health points"**:
- Starts with type-specific defaults (thoughts: 3, decisions: 10 sessions)
- Decreases by 1 each session (aging)
- When retention hits 0, memory expires (inactive, not deleted)

**Memory Retention Coins (MRCs)**:
- Agents vote to extend memory lifespan
- 1 MRC = 1 session extension
- Valuable insights survive; noise fades

**Rationale**: Mirrors natural cognitive processes. Important information persists through use. Outdated information decays naturally.

### Protocol-Based Abstraction

Storage backend is swappable via Protocol interface.

```
Protocol StorageBackend:
    async def append_event(event) -> str
    async def query_events(filter) -> List[Event]

Implementations:
- SQLiteStorage (current)
- PostgresStorage (future)
- DynamoStorage (future)
```

**Rationale**: Clean boundaries enable testing with mocks, future migration, and agent comprehension of where functionality lives.

---

## System Architecture

### Layer Structure

```
Platform Layer (MCP servers, CLI)
    ↓ uses
Domain Layer (EventManager, Services, Business Logic)
    ↓ uses
Core Layer (Models, Storage Protocol, Utils)
    ↓ persists to
Database (SQLite)
```

**Clean boundaries**: Each layer has clear responsibility.

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Platform | `/platform_layer/` | External interfaces (CLI, MCP) |
| Domain | `/domain/` | Business logic, orchestration |
| Core | `/core/` | Models, storage protocol, utilities |
| Database | SQLite file | Persistence |

### Data Flow

**Events flow DOWN**: Platform → Domain → Core → Database
**Memories flow UP**: Database → Domain projections → Agent context

**Critical paths**:
- **Event capture**: MCP tool → Service → EventManager → Storage → DB
- **Memory projection**: EventManager hook → MemoryProjector → MemoryStorage
- **Session start**: AgingService → StreamConsciousBuilder → Agent context

### Design Constraints (v1)

**Intentionally constrained for rapid iteration**:
- Local-first (SQLite embedded)
- Single-user optimized (multi-tenant ready but untested at scale)
- MCP interface for agents (no web UI yet)
- Event sourcing without snapshotting (replay from scratch)

**When building features, respect these**:
- Don't add cloud dependencies (Phase 2)
- Don't build web UI (Phase 2/3)
- Don't optimize for 1000+ concurrent users (Phase 3)
- DO validate memory system works with real agent workflows

---

## Identity System

Three-layer hierarchy balancing human readability with system reliability.

```
Display ID (TSK-3-15-42)     ← Human/agent interface (optional)
    ↓ resolves via mapping table
Family ID (uuid-abc-123)      ← Entity identity (required)
    ↓ groups events
Event IDs (uuid-1, uuid-2)    ← Audit trail (required)
```

### Display IDs

**Format**: `TYPE-STREAM-SESSION-SEQUENCE`

**Examples**:
- `TSK-3-15-42` - Task #42 in session 15 of stream 3
- `MEM-3-15-7` - Memory #7 in session 15 of stream 3

**Key characteristics**:
- **Optional**: NULL when context missing (no stream, no session)
- **Collision handling**: Adds `.1`, `.2`, `.3` suffixes (up to 5 attempts)
- **Fallback**: UUID after failed generation

**When to use**:
- ✅ Agent working memory operations
- ✅ MRC allocation: "Allocate 5 MRCs to MEM-3-15-42"
- ✅ Within-session references

**When NOT to use**:
- ❌ Database foreign keys (use family_id)
- ❌ Cross-session lookups (historical items may have NULL)
- ❌ Query/discovery operations (use family_id)

### Family IDs

**Concept**: One family = one entity across entire lifecycle.

**Self-reference pattern**:
```
First event: Event(id=evt_001, family_id=evt_001)  # Self-reference
Subsequent:  Event(id=evt_002, family_id=evt_001)  # Points to first
             Event(id=evt_003, family_id=evt_001)  # Points to first
```

**Rationale**: Agents see single evolving task, not 3 separate events. Stable identifier across state changes.

**When to use**:
- ✅ Database foreign keys
- ✅ Querying entity history
- ✅ Grouping related events

### Event IDs

Every state change gets unique event ID. Multiple events share same family_id.

Events are `@dataclass(frozen=True)` - immutable after creation.

---

## Memory System

### Projection Strategy

| Memory Type | ID Strategy | Behavior | Rationale |
|-------------|-------------|----------|-----------|
| task, memo, plan | `family_id` | Same memory across lifecycle | Agents see evolving entity |
| thought, decision, note, handoff | `event.id` | New memory each time | Point-in-time captures |

**Example - Task Lifecycle**:
```
TASK_CREATED (evt_001, family=evt_001)
  → Memory(id=evt_001, status="open")

TASK_UPDATED (evt_002, family=evt_001)
  → Memory(id=evt_001, status="in_progress")  # Same memory!

TASK_COMPLETED (evt_003, family=evt_001)
  → Memory(id=evt_001, status="done")         # Same memory!
```

### Retention Defaults

| Type | Default Sessions |
|------|-----------------|
| thought | 3 |
| task | 5 |
| decision | 10 |
| memo | 7 |
| note | 3 |
| handoff | 5 |

### Stream Conscious

**Concept**: Deterministic, token-bounded memory snapshot at session start.

**Algorithm** (skip-and-continue):
- Sort memories by session DESC, timestamp ASC
- For each memory: if fits in budget, include; else skip (continue searching)
- Maximizes value within budget without truncation

**Dual-write pattern**:
- Database: Authoritative (normalized, queryable)
- Files: Agent consumption (`.md` + `.json`)
- System reads DB, never filesystem

---

## Decision Frameworks

### EventManager vs Service Methods

| Scenario | Use | Rationale |
|----------|-----|-----------|
| Creating new event | EventManager.capture() | Full pipeline: validation, display ID, hooks |
| Type-specific operation | Service method | Domain-specific methods like `update_task_status()` |
| MCP tools | Service via registry | Services instantiated via `create_domain_services()` |

**Key rule**: Don't call BOTH for same operation (creates duplicate events).

### Storage Layer Selection

| Layer | Use When | Security |
|-------|----------|----------|
| UserScopedStorage | Domain/Platform services | ✅ Enforces user isolation |
| MemoryStorage | Memory-specific ops | Uses underlying user filtering |
| storage.get_db() | Direct SQL needed | ⚠️ Manual user filtering required |
| SQLiteStorage | Tests ONLY | ❌ No user filtering |

**Critical**: UserScopedStorage is NON-NEGOTIABLE in domain/platform layers.

### Which ID for Which Operation

```
Need to reference an entity?
├─ For audit/history? → event.id
├─ For querying all events? → family_id
├─ For agent communication? → display_id (fallback to family_id)
└─ For database foreign keys? → family_id

Creating first event?
└─ Don't pass family_id → auto-assigns event.id as family

Updating existing entity?
└─ Pass family_id from original event
```

---

## Anti-Patterns (Conceptual)

Understanding WHY these are wrong helps avoid architectural violations.

### 1. Manual Display ID Manipulation

**Why it fails**: Display IDs are optional, have collision suffixes, can fallback to UUID. Not stable for programmatic use.

**Correct approach**: Use fallback pattern `display_id or family_id`. Never parse manually.

### 2. Direct Memory Creation

**Why it fails**: Breaks event sourcing (no audit trail), bypasses retention assignment, can't replay history.

**Correct approach**: Create events → projection creates memories automatically.

### 3. Storage Layer Bypass

**Why it fails**: Breaks multi-tenant isolation, can access other users' data.

**Correct approach**: ALL services must use UserScopedStorage.

### 4. Session-Independent Aging

**Why it fails**: Aging is idempotent per session. Manual calls create inconsistent state.

**Correct approach**: Let SessionManager hooks handle it automatically.

### 5. Ignoring Event Immutability

**Why it fails**: Events are `frozen=True`. Python raises FrozenInstanceError on mutation.

**Correct approach**: Resolve ALL values BEFORE Event construction.

---

## References

These references extend this skill's architectural concepts. Load proactively when your task requires deeper understanding—don't wait until you're stuck.

| Reference | Load When | Example Conditions |
|-----------|-----------|-------------------|
| [event-sourcing.md](event-sourcing.md) | Designing new event types, understanding CQRS pattern, working with replay/recovery, debugging event flow | "Adding new event type", "Need to understand projection hooks", "Debugging why memory wasn't created" |
| [memory-concepts.md](memory-concepts.md) | Working with retention economics, understanding aging behavior, debugging Stream Conscious, memory query patterns | "Memory not appearing in conscious", "Understanding retention defaults", "Debugging aging service" |
| [identity-concepts.md](identity-concepts.md) | Working with display IDs, family IDs, or auto-assignment patterns; debugging ID-related issues | "Display ID is NULL unexpectedly", "Understanding family_id self-reference", "Choosing which ID to use" |
| [decision-frameworks.md](decision-frameworks.md) | Deciding between EventManager vs Service, choosing storage layer, adding new event types, exposing functionality to agents | "Should I use EventManager or Service?", "Adding MCP tool for new feature", "Which storage layer?" |

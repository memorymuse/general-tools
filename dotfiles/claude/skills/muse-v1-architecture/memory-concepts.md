# Memory Concepts - Deep Dive

Detailed exploration of the memory system in Muse v1.

## Memory as Projection

### Core Concept

Memories are NOT primary data - they are derived projections from events.

```
Events (Source of Truth)     Memories (Derived State)
┌────────────────────┐       ┌────────────────────┐
│ TASK_CREATED       │──┐    │                    │
│ evt_001            │  │    │ Memory             │
├────────────────────┤  ├───>│ id: evt_001        │
│ TASK_UPDATED       │  │    │ type: task         │
│ evt_002            │──┤    │ content: latest    │
├────────────────────┤  │    │ retention: 5       │
│ TASK_COMPLETED     │──┘    │                    │
│ evt_003            │       └────────────────────┘
└────────────────────┘
```

### Why Projections?

**Events optimize for**:
- Append-only writes
- Complete history
- Audit trail

**Memories optimize for**:
- Fast reads
- Current state queries
- Agent consumption

## AtomicMemory Model

```python
@dataclass
class AtomicMemory:
    memory_id: str           # UUID or family_id
    memory_type: str         # "task", "thought", etc.
    content: str             # Main text
    display_id: Optional[str]
    retention: int           # Sessions remaining
    is_active: bool          # True if retention > 0
    session_created: int
    timestamp: float
    # ... metadata fields
```

## Retention Economics

### The Problem

Without retention management:
- Memory accumulates forever
- Context becomes diluted
- Signal-to-noise ratio degrades
- Token budgets overwhelmed

### Natural Selection Model

**Retention as "health points"**:

```
Session 1: Memory created (retention = 5)
Session 2: Aging runs (retention = 4)
Session 3: Aging runs (retention = 3)
Session 4: Agent votes +3 MRCs (retention = 6)
Session 5: Aging runs (retention = 5)
...
Session N: retention hits 0 → memory expires
```

### Type-Specific Defaults

| Memory Type | Default Retention | Rationale |
|-------------|------------------|-----------|
| thought | 3 sessions | Ephemeral, often noise |
| note | 3 sessions | Similar to thoughts |
| task | 5 sessions | May need follow-up |
| handoff | 5 sessions | Relevant for immediate context |
| memo | 7 sessions | More considered content |
| decision | 10 sessions | Long-term reference value |

### Memory Retention Coins (MRCs)

**Agent voting mechanism**:

```python
await memory_allocate_coins(
    memory_id="MEM-3-15-42",  # Display ID or UUID
    coins=5,                   # Sessions to add
    reason="Critical for architecture decisions"
)
```

**Properties**:
- 1 MRC = 1 session extension
- Coins can be negative (reduce retention)
- All changes audited in `retention_history` table
- Collective voting reveals what truly matters

### Aging Service

**When**: Runs at session start (before conscious building)

**Behavior**:
- Decrements retention by 1 for ALL active memories
- Idempotent per session (tracked in `memory_aging_log`)
- Never reduces below 0

**Critical**: NEVER call manually - SessionManager handles it.

## Stream Conscious

### Purpose

Token-bounded memory snapshot loaded at session start.

**Problem solved**: Agents can't load unlimited memories. Need deterministic selection within budget.

### Selection Algorithm

```python
def build_conscious(budget_tokens: int) -> List[Memory]:
    candidates = get_active_memories()  # retention > 0
    candidates.sort(by=[session DESC, timestamp ASC])

    selected = []
    tokens_used = 0

    for memory in candidates:
        memory_tokens = estimate_tokens(memory)

        # Skip if exceeds budget (but keep searching!)
        if tokens_used + memory_tokens > budget_tokens:
            continue  # NOT break

        selected.append(memory)
        tokens_used += memory_tokens

    return selected
```

### Why Skip-and-Continue?

**Scenario**: Budget = 1000 tokens

| Memory | Tokens | Cumulative | Decision |
|--------|--------|------------|----------|
| M1 | 200 | 200 | Include |
| M2 | 300 | 500 | Include |
| M3 | 600 | 1100 | Skip (over budget) |
| M4 | 100 | 600 | Include! |
| M5 | 400 | 1000 | Include! |

**Skip-and-continue finds M4 and M5**. Simple break would miss them.

### Determinism Guarantees

Same inputs → same output:
- Sorting is stable (session DESC, timestamp ASC)
- No randomness in selection
- Deduplication by content hash

### Dual-Write Pattern

```
              ┌─────────────┐
              │   Database  │ ← Authoritative
              │  (memories) │
              └──────┬──────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐   ┌─────────────────┐
│ stream_conscious│   │ stream_conscious│
│ .json           │   │ .md             │
└─────────────────┘   └─────────────────┘
   For parsing          For reading
```

**Rule**: System reads from DB, never filesystem. File failures logged but don't block.

## Memory Lifecycle

```
Event Created
     │
     ▼
MemoryProjector (hook)
     │
     ├─ Updateable type? (task/memo/plan)
     │   └─ Upsert by family_id
     │
     └─ Point-in-time? (thought/decision)
         └─ Insert with event.id
     │
     ▼
Memory Active (retention > 0)
     │
     ▼
Session Boundaries
     │
     ├─ Aging Service runs
     │   └─ retention -= 1
     │
     ├─ Agent votes MRCs?
     │   └─ retention += coins
     │
     └─ Conscious Builder runs
         └─ Selects within budget
     │
     ▼
retention == 0?
     │
     └─ Memory expires (is_active = false)
```

## Query Patterns

### Active Memories

```python
# Memories with retention > 0
await memory_storage.get_active_memories(
    stream_id=stream_id,
    user_id=user_id
)
```

### By Type

```python
# All active thoughts
await memory_storage.query(
    memory_type="thought",
    is_active=True
)
```

### Full-Text Search

```python
# Search across content
await memory_storage.search(
    query="authentication",
    user_id=user_id
)
```

### By Session

```python
# Memories from specific session
await memory_storage.query(
    session_created=session_number
)
```

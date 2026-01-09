# Identity Concepts - Deep Dive

Detailed exploration of the identity system in Muse v1.

## The Three-Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    DISPLAY ID (Optional)                     │
│                      TSK-3-15-42                             │
│                                                              │
│   Human-readable, session-contextual, may be NULL            │
└─────────────────────────┬───────────────────────────────────┘
                          │ resolves via display_id_mappings
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FAMILY ID (Required)                      │
│                    evt_abc123-...                            │
│                                                              │
│   Entity identity, stable across lifecycle, groups events    │
└─────────────────────────┬───────────────────────────────────┘
                          │ groups via foreign key
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    EVENT IDS (Required)                      │
│              evt_001, evt_002, evt_003, ...                  │
│                                                              │
│   Unique per state change, immutable audit trail             │
└─────────────────────────────────────────────────────────────┘
```

## Display IDs

### Format

`TYPE-STREAM_SERIAL-SESSION-SEQUENCE`

**Components**:
- `TYPE`: Abbreviation (TSK, MEM, THT, DEC, etc.)
- `STREAM_SERIAL`: Stream's serial ID (integer)
- `SESSION`: Session number within stream
- `SEQUENCE`: Sequential counter within session

### Examples

| Display ID | Meaning |
|------------|---------|
| `TSK-3-15-42` | Task #42 in session 15 of stream 3 |
| `MEM-3-15-7` | Memory #7 in session 15 of stream 3 |
| `THT-3-15-1` | Thought #1 in session 15 of stream 3 |
| `DEC-3-15-3` | Decision #3 in session 15 of stream 3 |
| `HND-3-15-1` | Handoff #1 in session 15 of stream 3 |

### Type Abbreviations

| Type | Abbreviation |
|------|--------------|
| task | TSK |
| thought | THT |
| decision | DEC |
| memo | MEM |
| note | NOT |
| handoff | HND |
| plan | PLN |

### Generation Process

```
1. Get stream serial_id (required)
2. Get current session number (required)
3. Get next sequence for type (atomic increment)
4. Format: f"{TYPE}-{stream_serial}-{session}-{sequence}"
5. Check for collision in display_id_mappings
6. If collision: add suffix (.1, .2, .3...)
7. If 5 collisions: fallback to UUID
```

### NULL Strategy

Display IDs become NULL when:
- No active stream context
- No active session
- Generation fails repeatedly

**Philosophy**: No bad ID better than forced ID.

```python
# Safe pattern
identifier = display_id or family_id or event.id
```

### Collision Handling

```
Attempt 1: TSK-3-15-42        → Exists? No → Use it
Attempt 1: TSK-3-15-42        → Exists? Yes → Try suffix
Attempt 2: TSK-3-15-42.1      → Exists? No → Use it
...
Attempt 6: Fallback to UUID
```

### Display ID Mapping Table

```sql
CREATE TABLE display_id_mappings (
    display_id TEXT PRIMARY KEY,
    family_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    created_at REAL NOT NULL
);
```

**Purpose**: Resolve display_id → family_id for queries.

## Family IDs

### Concept

One family = one logical entity across its entire lifecycle.

### Self-Reference Pattern

```
First Event (entity creation):
┌──────────────────────────────────┐
│ id: evt_001                      │
│ family_id: evt_001  ← SELF       │
│ type: TASK_CREATED               │
└──────────────────────────────────┘

Subsequent Events (same entity):
┌──────────────────────────────────┐
│ id: evt_002                      │
│ family_id: evt_001  ← FIRST      │
│ type: TASK_UPDATED               │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ id: evt_003                      │
│ family_id: evt_001  ← FIRST      │
│ type: TASK_COMPLETED             │
└──────────────────────────────────┘
```

### Auto-Assignment Rule

**When creating first event**: Do NOT pass family_id

```python
# ✅ Correct - let system auto-assign
await event_manager.capture(
    content="New task",
    event_type=EventType.TASK_CREATED,
    # family_id NOT provided
)
# System sets: family_id = event.id

# ❌ Wrong - manually setting family_id for new entity
await event_manager.capture(
    content="New task",
    event_type=EventType.TASK_CREATED,
    family_id="some-id"  # Don't do this!
)
```

**When updating existing entity**: MUST pass family_id

```python
# ✅ Correct - reference existing family
await event_manager.capture(
    content="Updated task",
    event_type=EventType.TASK_UPDATED,
    family_id=original_event.family_id  # Required!
)
```

### Why Self-Reference?

**Problem**: How to identify "first event" for new entities?

**Solution**: First event's family_id equals its own id.

```python
# Detection
is_first_event = (event.id == event.family_id)
```

### Use Cases

| Operation | Use family_id? |
|-----------|---------------|
| Create new entity | No - auto-assigned |
| Update existing | Yes - from original |
| Query entity history | Yes - groups all events |
| Database foreign keys | Yes - stable reference |

## Event IDs

### Properties

- **Unique**: Every event gets unique UUID
- **Immutable**: Cannot change after creation
- **Audit trail**: Complete history of changes

### When to Use

| Purpose | Use |
|---------|-----|
| Audit log reference | event.id |
| "Which exact event?" | event.id |
| Debugging specific change | event.id |
| Memory ID for point-in-time | event.id |

## Decision Guide

### Which ID When?

```
┌─────────────────────────────────────────────────────────────┐
│                    What do you need?                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Human/  │     │ Query   │     │ Audit   │
    │ Agent   │     │ Entity  │     │ Trail   │
    │ Comms   │     │ History │     │         │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         ▼               ▼               ▼
    display_id      family_id       event.id
    (+ fallback)
```

### Common Patterns

**Agent communication**:
```python
# Show to agent
msg = f"Task {task.display_id or task.family_id} updated"
```

**Database foreign key**:
```python
# Reference in other table
comment.task_family_id = task.family_id  # Stable reference
```

**Query entity**:
```python
# Get all events for entity
events = await storage.query(family_id=family_id)
```

**Audit lookup**:
```python
# Find specific state change
event = await storage.get_event(event_id=specific_event_id)
```

## Anti-Patterns

### Parsing Display IDs

```python
# ❌ WRONG
parts = display_id.split('-')
stream = parts[1]
session = parts[2]

# Problems:
# - display_id can be NULL
# - Can have suffix (.1, .2)
# - Can be UUID fallback
```

### Assuming Display ID Exists

```python
# ❌ WRONG
f"Task {task.display_id} created"  # May be None!

# ✅ CORRECT
f"Task {task.display_id or task.family_id} created"
```

### Using Display ID as Foreign Key

```python
# ❌ WRONG
comment.task_id = task.display_id  # Can be NULL!

# ✅ CORRECT
comment.task_family_id = task.family_id  # Always stable
```

### Manual Family ID on First Event

```python
# ❌ WRONG - breaks self-reference pattern
event = Event(
    id=generate_uuid(),
    family_id=generate_uuid(),  # Different UUID!
    ...
)

# ✅ CORRECT - let EventManager handle it
await event_manager.capture(...)  # Auto-assigns family_id = id
```

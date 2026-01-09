# Event Sourcing - Deep Dive

Detailed exploration of event sourcing patterns in Muse v1.

## Why Event Sourcing?

### The Problem with Traditional State Storage

Traditional CRUD systems store current state only:

```
User Table:
| id | name | email | status |
| 1  | John | j@... | active |
```

**Lost information**:
- When did status change?
- What was the previous email?
- Who made changes?
- Why were changes made?

### Event Sourcing Solution

Store every state change as an immutable event:

```
Events:
| id | type | data | timestamp |
| 1 | USER_CREATED | {name: "John"} | t1 |
| 2 | EMAIL_CHANGED | {old: "...", new: "j@..."} | t2 |
| 3 | STATUS_ACTIVATED | {} | t3 |
```

**Preserved information**:
- Complete history
- Audit trail
- Replayability
- Time-travel debugging

## Muse v1 Event Model

### Event Structure

```python
@dataclass(frozen=True)
class Event:
    id: str                    # Unique event identifier (UUID)
    display_id: Optional[str]  # Human-readable (TSK-3-15-42)
    family_id: str             # Entity identity
    type: EventType            # Enum value
    content: str               # Main content
    metadata: Optional[dict]   # Additional data
    timestamp: float           # Unix timestamp
    user_id: str
    stream_id: str
    session_id: Optional[str]
```

### Immutability Guarantee

`frozen=True` ensures events cannot be modified after creation:

```python
event = Event(id="123", ...)
event.content = "new"  # Raises FrozenInstanceError!
```

**Implication**: All values must be resolved BEFORE constructing the Event.

### Event Types

```python
class EventType(Enum):
    THOUGHT_CAPTURED = "thought_captured"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    AGENT_DECIDED = "agent_decided"
    MEMO_CAPTURED = "memo_captured"
    USER_NOTE_CREATED = "user_note_created"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    # ... more types
```

## CQRS Pattern in Muse

**Command Query Responsibility Segregation**:

- **Commands**: Event capture (writes to `events` table)
- **Queries**: Memory table (optimized reads from `memories` table)
- **Projections**: Automatic event → memory transformation

### Write Path (Commands)

```
User Action
    ↓
MCP Tool / CLI
    ↓
Domain Service
    ↓
EventManager.capture()
    ↓
Validation
    ↓
Display ID Generation (optional)
    ↓
Storage.append_event()
    ↓
Projection Hooks (fire-and-forget)
```

### Read Path (Queries)

```
Agent Query
    ↓
MCP Tool
    ↓
MemoryStorage.query()
    ↓
UserScopedStorage (applies user filter)
    ↓
SQL Query
    ↓
Memory Objects
```

## Projection System

### Event → Memory Mapping

```python
EVENT_TO_MEMORY_TYPE = {
    EventType.THOUGHT_CAPTURED: "thought",
    EventType.TASK_CREATED: "task",
    EventType.TASK_UPDATED: "task",      # Same memory type!
    EventType.TASK_COMPLETED: "task",    # Same memory type!
    EventType.AGENT_DECIDED: "decision",
    EventType.MEMO_CAPTURED: "memo",
    # ...
}
```

### Projection Strategy

**Updateable entities** (use family_id as memory_id):
- Tasks, memos, plans
- Single memory record updated across lifecycle

**Point-in-time captures** (use event.id as memory_id):
- Thoughts, decisions, notes
- Each event creates new memory

### Non-Blocking Projections

```python
# EventManager hook execution
try:
    await projection_hook.on_event_captured(event)
except Exception as e:
    logger.error(f"Projection failed: {e}")
    # Event is STILL captured - projection failure doesn't block
```

**Rationale**: Event capture is more important than memory creation. System resilience requires events are ALWAYS captured.

## Replay and Recovery

### Rebuilding State

Because all state changes are events, you can:

1. Clear all derived state (memories)
2. Replay events in order
3. Reconstruct current state

```python
async def rebuild_memories():
    # Clear derived state
    await memory_storage.clear_all()

    # Replay all events
    events = await event_storage.query_all(order_by="timestamp")
    for event in events:
        await projector.project(event)
```

### Time-Travel Debugging

Replay events up to specific timestamp:

```python
async def state_at_time(target_timestamp: float):
    events = await event_storage.query(
        timestamp_before=target_timestamp
    )
    # Replay only these events to see historical state
```

## Trade-offs

### Advantages

| Benefit | Description |
|---------|-------------|
| Complete audit trail | Every change recorded |
| Temporal queries | "What was state at time X?" |
| Event-driven architecture | Easy to add new projections |
| Debugging | Replay to reproduce issues |
| Compliance | Immutable history for regulations |

### Challenges

| Challenge | Muse v1 Approach |
|-----------|-----------------|
| Storage growth | Retention economics (aging) |
| Query complexity | Projection to optimized read models |
| Eventual consistency | Acceptable for v1 single-user |
| Schema evolution | Versioned event types (future) |

## Best Practices

### DO

- Capture meaningful events with context
- Include "why" in metadata when relevant
- Let projections be the only way to create memories
- Handle projection failures gracefully

### DON'T

- Modify events after creation
- Create memories without corresponding events
- Skip events for "minor" changes
- Assume projections always succeed

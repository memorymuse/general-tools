---
name: muse-v1-implementation
description: You MUST PROACTIVELY USE this skill when writing, testing, or debugging Muse v1 code. Provides domain layer patterns, code examples, testing procedures, and anti-patterns with correct alternatives. ONLY for Muse v1 codebase work.
---

# Muse v1 Implementation Guide

Practical patterns and procedures for implementing features in Muse v1. Use this when writing code.

**For architectural concepts and design rationale**: See `muse-v1-architecture` skill.

---

## Critical Rules Summary

Before writing ANY Muse v1 code, internalize these:

### 1. UserScopedStorage Always

```python
# ✅ CORRECT - Security boundary enforced
user_storage = UserScopedStorage(base_storage, user_context)
service = TaskService(event_manager, user_storage)

# ❌ SECURITY VIOLATION - Bypasses user isolation
service = TaskService(event_manager, sqlite_storage)
```

### 2. Events First, Memories Follow

```python
# ✅ CORRECT - Event creates memory via projection
await event_manager.capture(content, EventType.TASK_CREATED)
# Memory automatically created by MemoryProjector hook

# ❌ WRONG - Bypasses event sourcing
await memory_storage.create_memory(...)  # Never do this!
```

### 3. Handle NULL Display IDs

```python
# ✅ CORRECT - Fallback pattern
identifier = event.display_id or event.family_id

# ❌ WRONG - Will fail when display_id is None
f"Task {task.display_id} created"
```

### 4. Never Manual Aging

```python
# ❌ WRONG - Breaks idempotency
await aging_service.age_memories()  # Never call manually!

# ✅ CORRECT - SessionManager handles it automatically
await session_manager.start_session()  # Aging runs inside
```

### 5. Events Are Immutable

```python
# ❌ WRONG - Will raise FrozenInstanceError
event.display_id = "new-id"

# ✅ CORRECT - Resolve before construction
display_id = await resolver.resolve(...)
event = Event(display_id=display_id, ...)
```

---

## Domain Layer Components

### EventManager

**Location**: `/domain/events/manager.py`

**Purpose**: Central orchestrator for event capture pipeline.

**Key method**: `capture(content, event_type, context, family_id=None)`

```python
# Creating new entity (no family_id)
event = await event_manager.capture(
    content="Implement OAuth",
    event_type=EventType.TASK_CREATED,
    context=capture_context
)
# family_id auto-assigned = event.id

# Updating existing entity (with family_id)
event = await event_manager.capture(
    content="OAuth implementation complete",
    event_type=EventType.TASK_COMPLETED,
    context=capture_context,
    family_id=original_task.family_id
)
```

**Pipeline**:
1. Validate event data
2. Generate display ID (if context available)
3. Execute registered service enrichment
4. Append to storage
5. Fire projection hooks

### Domain Services

**Location**: `/domain/events/*.py`

**Pattern**: Extend `BaseEventService`, implement type-specific methods.

```python
class TaskService(BaseEventService):
    async def create_task(self, content: str, priority: str = "medium") -> Event:
        """Create a new task with metadata."""
        return await self.event_manager.capture(
            content=content,
            event_type=EventType.TASK_CREATED,
            context=self.context,
            metadata={"priority": priority}
        )

    async def update_task_status(self, family_id: str, status: str) -> Event:
        """Update task status."""
        return await self.event_manager.capture(
            content=f"Status changed to {status}",
            event_type=EventType.TASK_UPDATED,
            context=self.context,
            family_id=family_id,
            metadata={"status": status}
        )
```

### MemoryProjector

**Location**: `/domain/memory/projector.py`

**Purpose**: Automatic event → memory transformation (hook).

**Never call directly** - EventManager fires this automatically.

**To add new event type**:
```python
# In projector.py
EVENT_TO_MEMORY_TYPE[EventType.NEW_TYPE] = "new_memory_type"
DEFAULT_RETENTION["new_memory_type"] = 5  # sessions
```

### Service Registry

**Location**: `/domain/services/registry.py`

**Function**: `create_domain_services(storage, context)`

```python
# Creates all domain services with proper dependencies
services = await create_domain_services(
    storage=user_scoped_storage,
    context=capture_context
)

task_service = services["task"]
thought_service = services["thought"]
memo_service = services["memo"]
```

---

## Navigation Guide

### "I need to..."

| Task | Where | What to Do |
|------|-------|------------|
| Add new event type | Core → Domain → Platform | See [extending-events.md](extending-events.md) |
| Capture event (generic) | EventManager | `await event_manager.capture(...)` |
| Capture with type logic | Domain Service | `await task_service.create_task(...)` |
| Expose to agents | Platform MCP | Add tool function |
| Query events/memories | UserScopedStorage | Via MemoryStorage |
| Modify projection | MemoryProjector | Update EVENT_TO_MEMORY_TYPE |
| Extend memory retention | MCP tools | `memory_allocate_coins(...)` |

### Key File Locations

| Purpose | Location |
|---------|----------|
| Event model | `/core/models/event.py` |
| Event types enum | `/core/models/event.py:EventType` |
| EventManager | `/domain/events/manager.py` |
| Services | `/domain/events/*.py` |
| Service registry | `/domain/services/registry.py` |
| MemoryProjector | `/domain/memory/projector.py` |
| AgingService | `/domain/memory/aging_service.py` |
| ConsciousBuilder | `/domain/memory/conscious_builder.py` |
| MCP servers | `/platform_layer/mcp/*.py` |
| Storage protocol | `/core/storage/interface.py` |
| UserScopedStorage | `/core/storage/user_scoped.py` |

---

## Anti-Patterns with Correct Alternatives

### Pattern 1: Manual Display ID Manipulation

```python
# ❌ WRONG
parts = display_id.split('-')
stream_id = parts[1]

# ✅ CORRECT
# Use utilities or treat as opaque
identifier = display_id or family_id
# Or use resolver
family_id = await resolver.resolve_display_id(display_id)
```

### Pattern 2: Direct Memory Creation

```python
# ❌ WRONG - Breaks event sourcing
memory = AtomicMemory(...)
await memory_storage.upsert_memory(memory)

# ✅ CORRECT - Create event, let projection handle memory
await event_manager.capture(
    content="...",
    event_type=EventType.THOUGHT_CAPTURED
)
# MemoryProjector hook creates memory automatically
```

### Pattern 3: Storage Layer Bypass

```python
# ❌ WRONG - Security vulnerability
class MyService:
    def __init__(self, sqlite_storage):  # Raw storage!
        self.storage = sqlite_storage

# ✅ CORRECT - User isolation enforced
class MyService:
    def __init__(self, user_scoped_storage):
        self.storage = user_scoped_storage
```

### Pattern 4: Manual Aging

```python
# ❌ WRONG - Breaks idempotency guarantees
await aging_service.age_memories()

# ✅ CORRECT - Let session lifecycle handle it
await session_manager.start_session()
# Aging runs automatically, idempotent per session
```

### Pattern 5: Mutating Events

```python
# ❌ WRONG - Events are frozen
event = await event_manager.capture(...)
event.display_id = "new-id"  # FrozenInstanceError!

# ✅ CORRECT - Resolve ALL values before creation
display_id = await resolver.resolve(context)
# EventManager handles this internally
```

---

## Testing Patterns

### Async Fixture Setup (CRITICAL)

```python
import pytest_asyncio
from core.storage.sqlite import SQLiteStorage

@pytest_asyncio.fixture
async def storage():
    """Fixture with proper cleanup."""
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    yield storage  # NOT return!
    await storage.close()  # ALWAYS cleanup!
```

**Why yield + cleanup?**: Without it, tests pass but hang for 30s+ at end.

### Test Structure

```python
@pytest.mark.asyncio
async def test_task_creation(storage, event_manager):
    # Arrange
    content = "Test task"

    # Act
    event = await event_manager.capture(
        content=content,
        event_type=EventType.TASK_CREATED,
        context=test_context
    )

    # Assert
    assert event.content == content
    assert event.family_id == event.id  # Self-reference for new entity
```

### Testing Services

```python
@pytest.mark.asyncio
async def test_task_service_update(task_service, created_task):
    # Arrange
    new_status = "completed"

    # Act
    update_event = await task_service.update_task_status(
        family_id=created_task.family_id,
        status=new_status
    )

    # Assert
    assert update_event.family_id == created_task.family_id
    assert update_event.metadata["status"] == new_status
```

---

## Common Commands

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/domain/events/test_task_service.py

# With coverage
pytest --cov=core --cov=domain --cov=platform_layer

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

### CLI

```bash
# Capture events
muse capture thought "An idea"
muse capture task "Implement feature" --priority high

# Query
muse query thoughts --recent
muse query tasks --status pending

# Streams
muse stream create "feature-name"
muse stream list
```

### MCP Servers

```bash
# Start servers
python platform_layer/mcp/capture_server.py
python platform_layer/mcp/query_server.py
python platform_layer/mcp/memory_server.py
```

---

## References

These references extend this skill's implementation patterns. Load proactively when your task requires detailed code—don't wait until you're stuck.

| Reference | Load When | Example Conditions |
|-----------|-----------|-------------------|
| [domain-layer.md](domain-layer.md) | Implementing EventManager integrations, understanding capture pipeline, creating services | "Need to understand how capture() works internally", "Creating new service class" |
| [identity-patterns.md](identity-patterns.md) | Handling display IDs, resolving agent input, implementing family ID patterns | "Agent passed a display ID, need to resolve it", "Implementing fallback pattern" |
| [memory-patterns.md](memory-patterns.md) | Querying memories, implementing MRC allocation, memory search operations | "Need to query memories by type", "Implementing memory search", "Extending retention" |
| [testing-patterns.md](testing-patterns.md) | Writing async tests, setting up fixtures, debugging test hangs | "Tests hanging after passing", "Need fixture for EventManager", "Writing integration test" |
| [extending-events.md](extending-events.md) | Adding new event types end-to-end | "Adding new event type", "Need complete workflow for new feature" |
| [dev-commands.md](dev-commands.md) | Running tests, CLI usage, environment setup | "How to run specific tests", "Need coverage report", "Setting up environment" |

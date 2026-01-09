# Testing Patterns - Muse v1

Testing patterns specific to Muse v1 async architecture.

## Critical: Async Fixture Cleanup

### The Problem

Without proper cleanup, tests pass but hang for 30+ seconds:

```
tests/test_example.py::test_something PASSED [100%]
... hangs for 30 seconds ...
Command timed out
```

### The Solution

```python
import pytest_asyncio
from core.storage.sqlite import SQLiteStorage

# ✅ CORRECT - with cleanup
@pytest_asyncio.fixture
async def storage():
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    yield storage  # Use yield, not return!
    await storage.close()  # Always cleanup!

# ❌ WRONG - no cleanup
@pytest_asyncio.fixture
async def storage():
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    return storage  # Missing cleanup!
```

### Resources Needing Cleanup

| Resource | Cleanup Method |
|----------|---------------|
| SQLiteStorage | `await storage.close()` |
| Database connections | `await conn.close()` |
| File handles | `handle.close()` |
| Event loop tasks | `task.cancel()` |

## Common Fixtures

### Storage Fixture

```python
@pytest_asyncio.fixture
async def storage():
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    yield storage
    await storage.close()
```

### User-Scoped Storage

```python
@pytest_asyncio.fixture
async def user_storage(storage):
    context = UserContext(user_id="test-user")
    yield UserScopedStorage(storage, context)
```

### Event Manager

```python
@pytest_asyncio.fixture
async def event_manager(user_storage):
    resolver = DisplayIDResolver(user_storage)
    manager = EventManager(user_storage, resolver)

    # Register projector hook
    memory_storage = MemoryStorage(user_storage)
    projector = MemoryProjector(memory_storage)
    manager.register_hook(projector)

    yield manager
```

### Capture Context

```python
@pytest_asyncio.fixture
def capture_context():
    return CaptureContext(
        user_id="test-user",
        stream_id="test-stream",
        session_id="test-session",
        stream_serial_id=1
    )
```

### Complete Service Setup

```python
@pytest_asyncio.fixture
async def services(user_storage, capture_context):
    services = await create_domain_services(
        storage=user_storage,
        context=capture_context
    )
    yield services
```

## Test Patterns

### Testing Event Capture

```python
@pytest.mark.asyncio
async def test_event_capture(event_manager, capture_context):
    # Arrange
    content = "Test task content"

    # Act
    event = await event_manager.capture(
        content=content,
        event_type=EventType.TASK_CREATED,
        context=capture_context
    )

    # Assert
    assert event.content == content
    assert event.type == EventType.TASK_CREATED
    assert event.family_id == event.id  # New entity self-references
    assert event.user_id == capture_context.user_id
```

### Testing Service Methods

```python
@pytest.mark.asyncio
async def test_task_status_update(services, capture_context):
    # Arrange
    task_service = services["task"]
    task = await task_service.create_task("Initial task")

    # Act
    update = await task_service.update_task_status(
        family_id=task.family_id,
        status="in_progress"
    )

    # Assert
    assert update.family_id == task.family_id
    assert update.metadata["status"] == "in_progress"
```

### Testing Memory Projection

```python
@pytest.mark.asyncio
async def test_memory_created_from_event(
    event_manager,
    capture_context,
    user_storage
):
    # Arrange
    content = "Important thought"

    # Act
    event = await event_manager.capture(
        content=content,
        event_type=EventType.THOUGHT_CAPTURED,
        context=capture_context
    )

    # Assert - memory should exist
    memory_storage = MemoryStorage(user_storage)
    memory = await memory_storage.get_memory(event.id)

    assert memory is not None
    assert memory.content == content
    assert memory.memory_type == "thought"
```

### Testing User Isolation

```python
@pytest.mark.asyncio
async def test_user_isolation(storage):
    # Create two user contexts
    user1_storage = UserScopedStorage(storage, UserContext(user_id="user1"))
    user2_storage = UserScopedStorage(storage, UserContext(user_id="user2"))

    # User 1 creates event
    event = await user1_storage.append_event(test_event)

    # User 2 cannot see it
    user2_events = await user2_storage.query_events()
    assert len(user2_events) == 0

    # User 1 can see it
    user1_events = await user1_storage.query_events()
    assert len(user1_events) == 1
```

### Testing Aging Idempotency

```python
@pytest.mark.asyncio
async def test_aging_idempotent(aging_service, memory_storage):
    # Create memory with retention 5
    memory = create_test_memory(retention=5)
    await memory_storage.upsert_memory(memory)

    # Age twice with same session
    await aging_service.age_memories(session_id="session-1")
    await aging_service.age_memories(session_id="session-1")  # Second call

    # Should only decrement once
    updated = await memory_storage.get_memory(memory.memory_id)
    assert updated.retention == 4  # Not 3
```

## Parametrized Tests

### Multiple Event Types

```python
@pytest.mark.parametrize("event_type,memory_type", [
    (EventType.THOUGHT_CAPTURED, "thought"),
    (EventType.TASK_CREATED, "task"),
    (EventType.AGENT_DECIDED, "decision"),
    (EventType.MEMO_CAPTURED, "memo"),
])
@pytest.mark.asyncio
async def test_event_to_memory_mapping(
    event_type,
    memory_type,
    event_manager,
    capture_context
):
    event = await event_manager.capture(
        content="Test",
        event_type=event_type,
        context=capture_context
    )

    memory = await get_memory(event.id)
    assert memory.memory_type == memory_type
```

### Validation Edge Cases

```python
@pytest.mark.parametrize("invalid_input,expected_error", [
    (None, "content cannot be None"),
    ("", "content cannot be empty"),
    (" " * 100, "content cannot be whitespace only"),
])
@pytest.mark.asyncio
async def test_validation_errors(invalid_input, expected_error, event_manager):
    with pytest.raises(ValidationError) as exc_info:
        await event_manager.capture(
            content=invalid_input,
            event_type=EventType.THOUGHT_CAPTURED,
            context=test_context
        )
    assert expected_error in str(exc_info.value)
```

## Test Timeout Configuration

```python
# In conftest.py or pyproject.toml
# Limit test timeout to catch cleanup issues early

# pytest.ini
[pytest]
timeout = 5

# Or per-test
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_fast_operation():
    pass
```

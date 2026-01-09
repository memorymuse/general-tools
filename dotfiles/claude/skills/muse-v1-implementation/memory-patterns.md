# Memory Patterns - Code Reference

Practical code patterns for memory operations in Muse v1.

## Querying Memories

### Get Active Memories

```python
async def get_active_memories(
    stream_id: str,
    user_id: str,
    memory_storage: MemoryStorage
) -> List[AtomicMemory]:
    """Get all memories with retention > 0."""
    return await memory_storage.get_active_memories(
        stream_id=stream_id,
        user_id=user_id
    )
```

### Get Memory by ID

```python
async def get_memory(
    memory_id: str,
    memory_storage: MemoryStorage
) -> Optional[AtomicMemory]:
    """Get single memory by ID (display_id or UUID)."""
    # Try as display_id first
    if not is_uuid(memory_id):
        resolved = await resolve_display_id(memory_id)
        if resolved:
            memory_id = resolved

    return await memory_storage.get_memory(memory_id)
```

### Query by Type

```python
async def get_memories_by_type(
    memory_type: str,
    stream_id: str,
    memory_storage: MemoryStorage
) -> List[AtomicMemory]:
    """Get all memories of specific type."""
    return await memory_storage.query_memories(
        memory_type=memory_type,
        stream_id=stream_id,
        is_active=True
    )
```

### Search Memories

```python
async def search_memories(
    query: str,
    user_id: str,
    memory_storage: MemoryStorage,
    limit: int = 10
) -> List[AtomicMemory]:
    """Full-text search across memory content."""
    return await memory_storage.search(
        query=query,
        user_id=user_id,
        limit=limit
    )
```

## MRC Allocation

### Extend Retention

```python
async def extend_retention(
    memory_id: str,
    sessions: int,
    reason: str,
    voting_service: VotingService
) -> None:
    """Extend a memory's retention."""
    await voting_service.allocate_coins(
        memory_id=memory_id,
        coins=sessions,  # Positive = extend
        reason=reason
    )
```

### Reduce Retention

```python
async def reduce_retention(
    memory_id: str,
    sessions: int,
    reason: str,
    voting_service: VotingService
) -> None:
    """Reduce a memory's retention (minimum 0)."""
    await voting_service.allocate_coins(
        memory_id=memory_id,
        coins=-sessions,  # Negative = reduce
        reason=reason
    )
```

### Batch Allocation

```python
async def batch_allocate(
    allocations: List[Tuple[str, int, str]],
    voting_service: VotingService
) -> None:
    """Allocate MRCs to multiple memories.

    Args:
        allocations: List of (memory_id, coins, reason) tuples
    """
    for memory_id, coins, reason in allocations:
        await voting_service.allocate_coins(
            memory_id=memory_id,
            coins=coins,
            reason=reason
        )
```

## Stream Conscious

### Get Current Conscious

```python
async def get_stream_conscious(
    stream_id: str,
    user_id: str,
    builder: StreamConsciousBuilder
) -> List[dict]:
    """Get token-bounded memory snapshot."""
    return await builder.build(
        stream_id=stream_id,
        user_id=user_id
    )
```

### Format for Agent

```python
def format_conscious_for_agent(conscious: List[dict]) -> str:
    """Format conscious content for agent consumption."""
    lines = ["# Stream Conscious\n"]

    for item in conscious:
        display = item.get("display_id") or item.get("memory_id")
        content = item.get("content", "")
        retention = item.get("retention", 0)

        lines.append(f"## {display} (retention: {retention})")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)
```

### Custom Token Budget

```python
async def get_conscious_with_budget(
    stream_id: str,
    user_id: str,
    budget_tokens: int,
    memory_storage: MemoryStorage
) -> List[dict]:
    """Build conscious with custom token budget."""
    builder = StreamConsciousBuilder(
        memory_storage=memory_storage,
        budget_tokens=budget_tokens
    )
    return await builder.build(stream_id, user_id)
```

## Memory Lifecycle

### Check if Memory is Active

```python
def is_memory_active(memory: AtomicMemory) -> bool:
    """Check if memory is still active."""
    return memory.retention > 0 and memory.is_active
```

### Get Expiring Memories

```python
async def get_expiring_memories(
    stream_id: str,
    threshold: int,
    memory_storage: MemoryStorage
) -> List[AtomicMemory]:
    """Get memories that will expire soon.

    Args:
        threshold: Retention threshold (e.g., 2 = expiring in 2 sessions)
    """
    active = await memory_storage.get_active_memories(stream_id)
    return [m for m in active if m.retention <= threshold]
```

### Suggest Memories for Extension

```python
async def suggest_for_extension(
    stream_id: str,
    memory_storage: MemoryStorage,
    limit: int = 5
) -> List[AtomicMemory]:
    """Suggest valuable memories that might need MRC allocation.

    Criteria:
    - Low retention (about to expire)
    - High-value types (decisions, memos)
    """
    expiring = await get_expiring_memories(stream_id, threshold=2, memory_storage)

    # Prioritize by type value
    type_priority = {"decision": 3, "memo": 2, "task": 1, "thought": 0}

    sorted_memories = sorted(
        expiring,
        key=lambda m: type_priority.get(m.memory_type, 0),
        reverse=True
    )

    return sorted_memories[:limit]
```

## Retention History

### Get Retention Changes

```python
async def get_retention_history(
    memory_id: str,
    storage: StorageProtocol
) -> List[dict]:
    """Get history of retention changes for a memory."""
    return await storage.query_retention_history(memory_id=memory_id)
```

### Audit MRC Usage

```python
async def audit_mrc_usage(
    user_id: str,
    storage: StorageProtocol,
    days: int = 7
) -> dict:
    """Audit MRC allocation patterns."""
    since = time.time() - (days * 24 * 60 * 60)

    history = await storage.query_retention_history(
        user_id=user_id,
        since=since
    )

    return {
        "total_allocated": sum(h["coins"] for h in history if h["coins"] > 0),
        "total_reduced": abs(sum(h["coins"] for h in history if h["coins"] < 0)),
        "memories_affected": len(set(h["memory_id"] for h in history)),
        "by_actor": _group_by_actor(history)
    }
```

## Integration with Events

### Get Memory from Event

```python
async def get_memory_for_event(
    event: Event,
    memory_storage: MemoryStorage
) -> Optional[AtomicMemory]:
    """Get the memory created from an event.

    For updateable types (task, memo): use family_id
    For point-in-time types (thought, decision): use event.id
    """
    updateable_types = {"task", "memo", "plan"}

    # Determine memory type from event
    memory_type = EVENT_TO_MEMORY_TYPE.get(event.type)

    if memory_type in updateable_types:
        return await memory_storage.get_memory(event.family_id)
    else:
        return await memory_storage.get_memory(event.id)
```

### Verify Projection Succeeded

```python
async def verify_projection(
    event: Event,
    memory_storage: MemoryStorage,
    timeout: float = 1.0
) -> bool:
    """Verify that an event was projected to a memory.

    Useful for testing or verification flows.
    """
    import asyncio

    start = time.time()
    while time.time() - start < timeout:
        memory = await get_memory_for_event(event, memory_storage)
        if memory:
            return True
        await asyncio.sleep(0.1)

    return False
```

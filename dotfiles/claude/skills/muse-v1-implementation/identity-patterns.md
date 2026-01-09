# Identity Patterns - Code Reference

Practical code patterns for working with IDs in Muse v1.

## Safe Display ID Handling

### Always Use Fallback

```python
# ✅ CORRECT - handles NULL display_id
def format_task_message(task: Event) -> str:
    identifier = task.display_id or task.family_id
    return f"Task {identifier} created"

# ❌ WRONG - fails when display_id is None
def format_task_message(task: Event) -> str:
    return f"Task {task.display_id} created"  # TypeError!
```

### Resolving Display IDs

```python
async def resolve_display_id(
    display_id: str,
    storage: StorageProtocol
) -> str:
    """Resolve display_id to family_id."""
    if not display_id:
        raise ValueError("display_id cannot be empty")

    # Check mapping table
    mapping = await storage.get_display_id_mapping(display_id)
    if mapping:
        return mapping.family_id

    # Might already be a UUID
    if is_valid_uuid(display_id):
        return display_id

    raise DisplayIDNotFoundError(
        f"Could not resolve '{display_id}'. "
        f"Use memory_list() to see valid identifiers."
    )
```

### Agent Input Handling

```python
async def handle_agent_reference(
    identifier: str,
    storage: StorageProtocol
) -> str:
    """Handle identifier from agent (could be display_id or UUID)."""
    # Try as display_id first
    mapping = await storage.get_display_id_mapping(identifier)
    if mapping:
        return mapping.family_id

    # Try as UUID
    if is_valid_uuid(identifier):
        return identifier

    # Try partial match (TSK-3-15-42 might be typed as TSK-3-15)
    partial_matches = await storage.search_display_ids(f"{identifier}%")
    if len(partial_matches) == 1:
        return partial_matches[0].family_id

    raise ValueError(
        f"Cannot resolve '{identifier}'. "
        f"Provide full display_id (e.g., TSK-3-15-42) or UUID."
    )
```

## Family ID Patterns

### Creating New Entity

```python
async def create_entity(
    content: str,
    event_type: EventType,
    event_manager: EventManager,
    context: CaptureContext
) -> Event:
    """Create new entity - DO NOT provide family_id."""
    # Let EventManager auto-assign family_id = event.id
    return await event_manager.capture(
        content=content,
        event_type=event_type,
        context=context
        # NO family_id parameter!
    )
```

### Updating Existing Entity

```python
async def update_entity(
    family_id: str,
    content: str,
    event_type: EventType,
    event_manager: EventManager,
    context: CaptureContext
) -> Event:
    """Update existing entity - MUST provide family_id."""
    return await event_manager.capture(
        content=content,
        event_type=event_type,
        context=context,
        family_id=family_id  # Required for updates!
    )
```

### Querying Entity History

```python
async def get_entity_history(
    family_id: str,
    storage: StorageProtocol
) -> List[Event]:
    """Get all events for an entity."""
    return await storage.query_events(
        family_id=family_id,
        order_by="timestamp",
        order_desc=False  # Oldest first
    )
```

### Getting Latest State

```python
async def get_latest_state(
    family_id: str,
    storage: StorageProtocol
) -> Optional[Event]:
    """Get most recent event for entity."""
    events = await storage.query_events(
        family_id=family_id,
        order_by="timestamp",
        order_desc=True,
        limit=1
    )
    return events[0] if events else None
```

## Display ID Generation

### Context Requirements

```python
def can_generate_display_id(context: CaptureContext) -> bool:
    """Check if context supports display ID generation."""
    return (
        context.stream_id is not None and
        context.session_id is not None and
        context.stream_serial_id is not None
    )
```

### Generation Pattern

```python
async def generate_display_id(
    event_type: EventType,
    context: CaptureContext,
    storage: StorageProtocol
) -> Optional[str]:
    """Generate display ID if context permits."""
    if not can_generate_display_id(context):
        return None

    # Get type abbreviation
    abbrev = EVENT_TYPE_ABBREVIATIONS.get(event_type, "EVT")

    # Get next sequence number (atomic)
    sequence = await storage.get_next_sequence(
        stream_id=context.stream_id,
        session_id=context.session_id,
        event_type=event_type
    )

    # Format
    base_id = f"{abbrev}-{context.stream_serial_id}-{context.session_id}-{sequence}"

    # Handle collisions
    display_id = base_id
    for suffix in range(1, 6):
        if not await storage.display_id_exists(display_id):
            return display_id
        display_id = f"{base_id}.{suffix}"

    # Fallback to None after 5 attempts
    logger.warning(f"Display ID collision limit reached for {base_id}")
    return None
```

## MRC Allocation

### By Display ID

```python
await memory_allocate_coins(
    memory_id="TSK-3-15-42",
    coins=5,
    reason="Critical for OAuth implementation"
)
```

### By Memory UUID

```python
await memory_allocate_coins(
    memory_id="evt_abc123-def456-...",
    coins=3,
    reason="Important architectural decision"
)
```

### Validation Pattern

```python
async def allocate_with_validation(
    memory_id: str,
    coins: int,
    reason: str,
    storage: StorageProtocol
) -> None:
    """Allocate MRCs with full validation."""
    # Resolve identifier
    actual_id = await resolve_memory_identifier(memory_id, storage)

    # Get memory
    memory = await storage.get_memory(actual_id)
    if not memory:
        raise MemoryNotFoundError(
            f"Memory '{memory_id}' not found. "
            f"Available memories: {await list_memory_ids(storage)}"
        )

    # Validate coins
    if not isinstance(coins, int):
        raise ValueError(
            f"coins must be integer, got {type(coins).__name__}. "
            f"Example: allocate_coins('TSK-3-15-42', 5, 'reason')"
        )

    # Apply allocation
    new_retention = max(0, memory.retention + coins)
    await storage.update_memory_retention(actual_id, new_retention)

    # Audit
    await storage.record_retention_change(
        memory_id=actual_id,
        old_value=memory.retention,
        new_value=new_retention,
        coins=coins,
        reason=reason
    )
```

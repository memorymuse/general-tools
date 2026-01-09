# Domain Layer - Detailed Reference

In-depth guide to domain layer components and their interactions.

## EventManager Deep Dive

### Location
`/domain/events/manager.py`

### Class Structure

```python
class EventManager:
    def __init__(
        self,
        storage: StorageProtocol,
        display_id_resolver: Optional[DisplayIDResolver] = None
    ):
        self.storage = storage
        self.resolver = display_id_resolver
        self._services: Dict[EventType, BaseEventService] = {}
        self._hooks: List[EventHook] = []

    def register_service(self, service: BaseEventService) -> None:
        """Register a service for event type enrichment."""

    def register_hook(self, hook: EventHook) -> None:
        """Register a post-capture hook (e.g., MemoryProjector)."""

    async def capture(
        self,
        content: str,
        event_type: EventType,
        context: CaptureContext,
        family_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Event:
        """Main capture pipeline."""
```

### Capture Pipeline Detailed

```python
async def capture(...) -> Event:
    # 1. Generate IDs
    event_id = generate_uuid()
    family_id = family_id or event_id  # Self-reference if new

    # 2. Resolve display ID (may be None)
    display_id = None
    if self.resolver and context.has_session:
        try:
            display_id = await self.resolver.resolve(
                event_type, context.stream_id, context.session_id
            )
        except Exception as e:
            logger.warning(f"Display ID generation failed: {e}")
            # Continue with display_id = None

    # 3. Create immutable event
    event = Event(
        id=event_id,
        display_id=display_id,
        family_id=family_id,
        type=event_type,
        content=content,
        metadata=metadata,
        timestamp=time.time(),
        user_id=context.user_id,
        stream_id=context.stream_id,
        session_id=context.session_id
    )

    # 4. Service enrichment (if registered)
    if event_type in self._services:
        event = await self._services[event_type].enrich(event)

    # 5. Storage
    await self.storage.append_event(event)

    # 6. Fire hooks (non-blocking)
    for hook in self._hooks:
        try:
            await hook.on_event_captured(event)
        except Exception as e:
            logger.error(f"Hook failed: {e}")
            # Don't re-raise - event is already captured

    return event
```

## Service Pattern

### Base Service

```python
class BaseEventService:
    """Base class for all domain services."""

    def __init__(
        self,
        event_manager: EventManager,
        storage: StorageProtocol,
        context: CaptureContext
    ):
        self.event_manager = event_manager
        self.storage = storage
        self.context = context

    @property
    def event_types(self) -> List[EventType]:
        """Event types this service handles."""
        raise NotImplementedError

    async def enrich(self, event: Event) -> Event:
        """Optional enrichment before storage."""
        return event
```

### Implementing a Service

```python
class TaskService(BaseEventService):
    """Task-specific event operations."""

    @property
    def event_types(self) -> List[EventType]:
        return [
            EventType.TASK_CREATED,
            EventType.TASK_UPDATED,
            EventType.TASK_COMPLETED
        ]

    async def create_task(
        self,
        content: str,
        priority: str = "medium",
        due_date: Optional[str] = None
    ) -> Event:
        """Create a new task."""
        return await self.event_manager.capture(
            content=content,
            event_type=EventType.TASK_CREATED,
            context=self.context,
            metadata={
                "priority": priority,
                "due_date": due_date,
                "status": "open"
            }
        )

    async def update_task_status(
        self,
        family_id: str,
        status: str
    ) -> Event:
        """Update an existing task's status."""
        # Validate status
        valid_statuses = ["open", "in_progress", "blocked", "completed"]
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Valid: {valid_statuses}. "
                f"Example: update_task_status(family_id, 'in_progress')"
            )

        event_type = (
            EventType.TASK_COMPLETED if status == "completed"
            else EventType.TASK_UPDATED
        )

        return await self.event_manager.capture(
            content=f"Status changed to {status}",
            event_type=event_type,
            context=self.context,
            family_id=family_id,
            metadata={"status": status}
        )

    async def get_task(self, family_id: str) -> Optional[Event]:
        """Get latest event for a task."""
        events = await self.storage.query_events(
            family_id=family_id,
            order_by="timestamp",
            order_desc=True,
            limit=1
        )
        return events[0] if events else None
```

## MemoryProjector

### Location
`/domain/memory/projector.py`

### Configuration Maps

```python
# Event type → Memory type
EVENT_TO_MEMORY_TYPE = {
    EventType.THOUGHT_CAPTURED: "thought",
    EventType.TASK_CREATED: "task",
    EventType.TASK_UPDATED: "task",
    EventType.TASK_COMPLETED: "task",
    EventType.AGENT_DECIDED: "decision",
    EventType.MEMO_CAPTURED: "memo",
    EventType.USER_NOTE_CREATED: "note",
    EventType.SESSION_HANDOFF: "handoff",
}

# Default retention by memory type
DEFAULT_RETENTION = {
    "thought": 3,
    "task": 5,
    "decision": 10,
    "memo": 7,
    "note": 3,
    "handoff": 5,
}

# Types that use family_id (updateable)
UPDATEABLE_TYPES = {"task", "memo", "plan"}
# Others use event.id (point-in-time)
```

### Projection Logic

```python
class MemoryProjector(EventHook):
    async def on_event_captured(self, event: Event) -> None:
        # Skip if no mapping
        if event.type not in EVENT_TO_MEMORY_TYPE:
            return

        memory_type = EVENT_TO_MEMORY_TYPE[event.type]

        # Determine memory ID strategy
        if memory_type in UPDATEABLE_TYPES:
            memory_id = event.family_id  # Same memory across lifecycle
        else:
            memory_id = event.id  # New memory each time

        # Get retention default
        retention = DEFAULT_RETENTION.get(memory_type, 5)

        # Build memory
        memory = AtomicMemory(
            memory_id=memory_id,
            memory_type=memory_type,
            content=event.content,
            display_id=event.display_id,
            retention=retention,
            is_active=True,
            session_created=event.session_id,
            timestamp=event.timestamp,
            user_id=event.user_id,
            stream_id=event.stream_id,
            metadata=event.metadata
        )

        # Upsert (insert or update)
        await self.memory_storage.upsert_memory(memory)
```

## AgingService

### Location
`/domain/memory/aging_service.py`

### Idempotency Pattern

```python
class AgingService:
    async def age_memories(self, session_id: str) -> int:
        """Decrement retention for all active memories.

        Idempotent per session - tracks in memory_aging_log.
        """
        # Check if already aged this session
        if await self._already_aged(session_id):
            logger.info(f"Session {session_id} already aged, skipping")
            return 0

        # Age all active memories
        aged_count = await self.storage.decrement_all_retention()

        # Record that we aged this session
        await self._record_aging(session_id)

        return aged_count

    async def _already_aged(self, session_id: str) -> bool:
        """Check memory_aging_log table."""
        result = await self.storage.query_aging_log(session_id)
        return result is not None

    async def _record_aging(self, session_id: str) -> None:
        """Insert into memory_aging_log table."""
        await self.storage.insert_aging_log(session_id, time.time())
```

## VotingService

### Location
`/domain/memory/aging_service.py` (VotingService class)

### MRC Allocation

```python
class VotingService:
    async def allocate_coins(
        self,
        memory_id: str,
        coins: int,
        reason: Optional[str] = None,
        actor: str = "agent"
    ) -> None:
        """Allocate MRCs to extend/reduce retention.

        Args:
            memory_id: Display ID or memory UUID
            coins: Positive extends, negative reduces
            reason: Optional reason for audit trail
            actor: Who is allocating (for audit)
        """
        # Resolve display_id if needed
        actual_id = await self._resolve_id(memory_id)

        # Update retention
        memory = await self.memory_storage.get_memory(actual_id)
        if not memory:
            raise MemoryNotFoundError(
                f"Memory '{memory_id}' not found. "
                f"Use memory_list() to see available memories."
            )

        new_retention = max(0, memory.retention + coins)
        await self.memory_storage.update_retention(actual_id, new_retention)

        # Audit trail
        await self._record_history(
            memory_id=actual_id,
            old_retention=memory.retention,
            new_retention=new_retention,
            coins=coins,
            reason=reason,
            actor=actor
        )
```

## StreamConsciousBuilder

### Location
`/domain/memory/conscious_builder.py`

### Build Algorithm

```python
class StreamConsciousBuilder:
    def __init__(
        self,
        memory_storage: MemoryStorage,
        budget_tokens: int = 4000
    ):
        self.memory_storage = memory_storage
        self.budget = budget_tokens

    async def build(self, stream_id: str, user_id: str) -> List[dict]:
        """Build token-bounded memory snapshot."""
        # Get active memories
        candidates = await self.memory_storage.get_active_memories(
            stream_id=stream_id,
            user_id=user_id
        )

        # Sort: recent sessions first, then by timestamp
        candidates.sort(
            key=lambda m: (-m.session_created, m.timestamp)
        )

        # Skip-and-continue selection
        selected = []
        tokens_used = 0
        seen_hashes = set()

        for memory in candidates:
            # Deduplicate by content
            content_hash = hash(memory.content)
            if content_hash in seen_hashes:
                continue

            tokens = self._estimate_tokens(memory)

            # Skip if would exceed budget (but continue!)
            if tokens_used + tokens > self.budget:
                continue

            selected.append(self._format_memory(memory))
            tokens_used += tokens
            seen_hashes.add(content_hash)

        return selected

    def _format_memory(self, memory: AtomicMemory) -> dict:
        """Format for agent consumption."""
        return {
            "memory_id": memory.memory_id,
            "type": memory.memory_type,
            "session": memory.session_created,
            "retention": memory.retention,
            "display_id": memory.display_id,
            "content": memory.content,
            "tokens": self._estimate_tokens(memory),
            "why": "eligible; ordered; unique"
        }
```

## Service Registry

### Location
`/domain/services/registry.py`

### Factory Function

```python
async def create_domain_services(
    storage: StorageProtocol,
    context: CaptureContext
) -> Dict[str, BaseEventService]:
    """Create all domain services with proper dependencies.

    Args:
        storage: Must be UserScopedStorage!
        context: Capture context with user/stream/session info

    Returns:
        Dict mapping service name to instance
    """
    # Create EventManager
    resolver = DisplayIDResolver(storage)
    event_manager = EventManager(storage, resolver)

    # Create services
    services = {
        "task": TaskService(event_manager, storage, context),
        "thought": ThoughtService(event_manager, storage, context),
        "memo": MemoService(event_manager, storage, context),
        "decision": DecisionService(event_manager, storage, context),
        # ... more services
    }

    # Register services with EventManager
    for service in services.values():
        event_manager.register_service(service)

    # Register MemoryProjector hook
    memory_storage = MemoryStorage(storage)
    projector = MemoryProjector(memory_storage)
    event_manager.register_hook(projector)

    return services
```

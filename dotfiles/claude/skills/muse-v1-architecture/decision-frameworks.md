# Decision Frameworks - Deep Dive

Detailed decision trees for common architectural choices in Muse v1.

## EventManager vs Service Methods

### When to Use EventManager.capture()

**Use for**:
- Creating new entities (first event in family)
- Generic event capture with full pipeline
- When you need validation, display ID generation, and projection hooks

**Full pipeline includes**:
1. Event validation
2. Display ID generation (if context available)
3. Service enrichment (if service registered)
4. Storage append
5. Projection hooks (memory creation)

### When to Use Service Methods Directly

**Use for**:
- Type-specific operations (e.g., `update_task_status()`)
- When service has convenience methods
- When you need domain-specific logic

**Examples**:
```
TaskService.update_task_status(task_id, "completed")
MemoService.create_memo_with_tags(content, tags)
ThoughtService.capture_with_context(thought, context)
```

### Decision Tree

```
Need to capture an event?
│
├─ Is this a NEW entity (first event)?
│   │
│   ├─ Yes: Does a service exist for this type?
│   │   │
│   │   ├─ Yes → Use Service.create_*() method
│   │   │        (Service internally uses EventManager)
│   │   │
│   │   └─ No → Use EventManager.capture() directly
│   │
│   └─ No: This is an UPDATE to existing entity
│       │
│       └─ Use Service.update_*() method with family_id
│
└─ Need to bypass hooks for some reason?
    │
    └─ RARE! Document why, use Service + manual storage
```

### Anti-Pattern: Double Capture

```python
# ❌ WRONG - creates duplicate events
await task_service.create_task(content)
await event_manager.capture(content, EventType.TASK_CREATED)

# Both paths reach storage - now you have TWO events!
```

## Storage Layer Selection

### The Four Layers

```
┌────────────────────────────────────────────────────────┐
│                   UserScopedStorage                     │
│   Wraps base storage, enforces user_id on ALL ops      │
│   USE IN: All domain/platform services                 │
├────────────────────────────────────────────────────────┤
│                    MemoryStorage                        │
│   Memory-specific operations (get, upsert, query)      │
│   USE IN: MemoryProjector, memory queries              │
├────────────────────────────────────────────────────────┤
│                   storage.get_db()                      │
│   Direct database access for complex queries           │
│   USE IN: Migrations, complex joins, schema ops        │
│   ⚠️ REQUIRES manual user filtering                    │
├────────────────────────────────────────────────────────┤
│                    SQLiteStorage                        │
│   Raw storage without user isolation                   │
│   USE IN: Tests ONLY (:memory: databases)              │
│   ❌ NEVER in domain/platform code                     │
└────────────────────────────────────────────────────────┘
```

### Decision Tree

```
Need storage access?
│
├─ In domain service or platform layer?
│   │
│   └─ Yes → UserScopedStorage (NON-NEGOTIABLE)
│
├─ Need memory-specific operations?
│   │
│   └─ Yes → MemoryStorage (uses underlying user filtering)
│
├─ Need complex SQL query or schema operation?
│   │
│   └─ Yes → storage.get_db() with MANUAL user filtering
│
└─ Writing a test?
    │
    └─ Yes → SQLiteStorage(":memory:") with explicit setup
```

### Security Implications

| Layer | User Isolation | Use In Production? |
|-------|---------------|-------------------|
| UserScopedStorage | Automatic | ✅ Yes - Required |
| MemoryStorage | Via underlying | ✅ Yes |
| storage.get_db() | Manual | ⚠️ With caution |
| SQLiteStorage | None | ❌ Never |

## Identity System Operations

### Creating New Entity

```
Create new entity (task, thought, memo, etc.)
│
└─ Do NOT provide family_id
    │
    └─ EventManager auto-assigns: family_id = event.id
        │
        └─ This event is now the "root" of the family
```

### Updating Existing Entity

```
Update existing entity
│
└─ MUST provide family_id from original event
    │
    └─ New event links to same family
        │
        └─ Memory projection updates same memory record
```

### Querying Entity

```
Query for entity?
│
├─ By display_id (agent provided)?
│   │
│   └─ Resolve: display_id → family_id via mapping table
│       │
│       └─ Query by family_id
│
├─ By family_id directly?
│   │
│   └─ Query: family_id = value
│       │
│       └─ Returns all events in family
│
└─ By event_id (specific state)?
    │
    └─ Query: id = value
        │
        └─ Returns single event
```

### Displaying to Agent

```
Need to show identifier to agent?
│
├─ display_id exists (not NULL)?
│   │
│   └─ Show display_id (human-friendly)
│
└─ display_id is NULL?
    │
    └─ Show family_id or event.id (fallback)

Code: identifier = display_id or family_id
```

## Component Integration

### Adding New Event Type

```
Want to add new event type?
│
├─ 1. Core: Add to EventType enum
│      /core/models/event.py
│
├─ 2. Domain: Create XService
│      /domain/events/x_service.py
│      Extend BaseEventService
│
├─ 3. Domain: Register service
│      /domain/services/registry.py
│      Add to create_domain_services()
│
├─ 4. Domain: Add projection mapping
│      /domain/memory/projector.py
│      EVENT_TO_MEMORY_TYPE[new_type] = "memory_type"
│      DEFAULT_RETENTION["memory_type"] = N
│
├─ 5. Platform: Add MCP tool (if agent-facing)
│      /platform_layer/mcp/capture_server.py
│
├─ 6. Core: Add display ID abbreviation (optional)
│      /core/utils/display_id.py
│
└─ 7. Tests: Write tests FIRST (TDD)
       /tests/domain/events/test_x_service.py
```

### Exposing to Agents

```
Want agents to access functionality?
│
├─ Is it a capture operation?
│   │
│   └─ Add tool to capture_server.py
│       Tool calls domain service
│
├─ Is it a query operation?
│   │
│   └─ Add tool to query_server.py
│       Tool calls storage/memory queries
│
└─ Is it a memory operation?
    │
    └─ Add tool to memory_server.py
        Tool calls VotingService or MemoryStorage
```

## Common Scenarios

### "Agent wants to create a task"

```
1. Agent calls MCP tool: capture_task(content, priority)
2. MCP tool calls: TaskService.create_task(content, priority)
3. TaskService calls: EventManager.capture(...)
4. EventManager:
   - Validates event
   - Generates display ID
   - Stores event
   - Fires MemoryProjector hook
5. MemoryProjector creates memory
6. Agent receives: task display_id
```

### "Agent wants to update task status"

```
1. Agent calls: update_task(task_id, status)
2. MCP resolves: task_id → family_id
3. TaskService.update_status(family_id, status)
4. Creates event with family_id reference
5. MemoryProjector updates SAME memory
6. Agent sees: single task with new status
```

### "Agent wants recent thoughts"

```
1. Agent calls: query_thoughts(limit=10)
2. MCP tool calls: storage.query_memories(type="thought")
3. UserScopedStorage applies user filter
4. Returns: List[Memory] sorted by timestamp
5. Agent receives: memories with display_ids
```

### "Session starts"

```
1. SessionManager.start_session()
2. AgingService.age_memories() - decrements retention
3. StreamConsciousBuilder.build() - creates snapshot
4. Agent receives: Stream Conscious content
5. Agent has: Token-bounded context
```

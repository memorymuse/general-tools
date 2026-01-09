# Extending Events - Step by Step

Complete workflow for adding new event types to Muse v1.

## Overview

Adding a new event type requires changes across multiple layers:

```
1. Core: EventType enum
2. Domain: Service class
3. Domain: Service registry
4. Domain: Memory projection
5. Platform: MCP tool (if agent-facing)
6. Core: Display ID abbreviation (optional)
7. Tests: Full coverage
```

## Step-by-Step Guide

### Step 1: Add EventType Enum

**File**: `/core/models/event.py`

```python
class EventType(Enum):
    # Existing types...
    THOUGHT_CAPTURED = "thought_captured"
    TASK_CREATED = "task_created"

    # Add new type
    INSIGHT_RECORDED = "insight_recorded"  # NEW
```

### Step 2: Create Domain Service

**File**: `/domain/events/insight_service.py` (new file)

```python
from domain.events.base import BaseEventService
from core.models.event import EventType, Event

class InsightService(BaseEventService):
    """Service for insight-related events."""

    @property
    def event_types(self) -> List[EventType]:
        return [EventType.INSIGHT_RECORDED]

    async def record_insight(
        self,
        content: str,
        category: str = "general",
        confidence: float = 0.8
    ) -> Event:
        """Record a new insight.

        Args:
            content: The insight text
            category: Category (general, architecture, pattern, etc.)
            confidence: How confident in this insight (0.0-1.0)

        Returns:
            Created event

        Example:
            await insight_service.record_insight(
                content="Event sourcing enables temporal queries",
                category="architecture",
                confidence=0.9
            )
        """
        # Validate
        if not content or not content.strip():
            raise ValueError(
                "Insight content cannot be empty. "
                "Example: record_insight('Event sourcing enables...')"
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"Confidence must be 0.0-1.0, got {confidence}. "
                "Example: record_insight(content, confidence=0.8)"
            )

        return await self.event_manager.capture(
            content=content,
            event_type=EventType.INSIGHT_RECORDED,
            context=self.context,
            metadata={
                "category": category,
                "confidence": confidence
            }
        )

    async def get_insights_by_category(
        self,
        category: str
    ) -> List[Event]:
        """Get all insights in a category."""
        events = await self.storage.query_events(
            event_type=EventType.INSIGHT_RECORDED
        )
        return [
            e for e in events
            if e.metadata.get("category") == category
        ]
```

### Step 3: Register in Service Registry

**File**: `/domain/services/registry.py`

```python
from domain.events.insight_service import InsightService

async def create_domain_services(...) -> Dict[str, BaseEventService]:
    # Existing services...
    services = {
        "task": TaskService(event_manager, storage, context),
        "thought": ThoughtService(event_manager, storage, context),
        # Add new service
        "insight": InsightService(event_manager, storage, context),  # NEW
    }

    # Register with EventManager
    for service in services.values():
        event_manager.register_service(service)

    return services
```

### Step 4: Add Memory Projection Mapping

**File**: `/domain/memory/projector.py`

```python
# Add to EVENT_TO_MEMORY_TYPE
EVENT_TO_MEMORY_TYPE = {
    # Existing mappings...
    EventType.THOUGHT_CAPTURED: "thought",
    EventType.TASK_CREATED: "task",

    # New mapping
    EventType.INSIGHT_RECORDED: "insight",  # NEW
}

# Add retention default
DEFAULT_RETENTION = {
    # Existing...
    "thought": 3,
    "task": 5,

    # New type
    "insight": 7,  # NEW - insights are valuable, longer retention
}
```

### Step 5: Add MCP Tool (if agent-facing)

**File**: `/platform_layer/mcp/capture_server.py`

```python
@server.tool()
async def capture_insight(
    content: str,
    category: str = "general",
    confidence: float = 0.8
) -> str:
    """Record an insight.

    Args:
        content: The insight to record
        category: Category (general, architecture, pattern, debugging)
        confidence: Confidence level 0.0-1.0

    Returns:
        Success message with insight identifier
    """
    services = await get_services()
    insight_service = services["insight"]

    event = await insight_service.record_insight(
        content=content,
        category=category,
        confidence=confidence
    )

    identifier = event.display_id or event.id
    return f"Insight recorded: {identifier}"
```

### Step 6: Add Display ID Abbreviation (optional)

**File**: `/core/utils/display_id.py`

```python
EVENT_TYPE_ABBREVIATIONS = {
    # Existing...
    EventType.THOUGHT_CAPTURED: "THT",
    EventType.TASK_CREATED: "TSK",

    # New abbreviation
    EventType.INSIGHT_RECORDED: "INS",  # NEW
}
```

### Step 7: Write Tests (TDD)

**File**: `/tests/domain/events/test_insight_service.py` (new file)

```python
import pytest
import pytest_asyncio
from domain.events.insight_service import InsightService
from core.models.event import EventType

@pytest_asyncio.fixture
async def insight_service(event_manager, user_storage, capture_context):
    return InsightService(event_manager, user_storage, capture_context)

class TestInsightService:
    @pytest.mark.asyncio
    async def test_record_insight_success(self, insight_service):
        # Arrange
        content = "Event sourcing enables temporal queries"

        # Act
        event = await insight_service.record_insight(content)

        # Assert
        assert event.type == EventType.INSIGHT_RECORDED
        assert event.content == content
        assert event.family_id == event.id

    @pytest.mark.asyncio
    async def test_record_insight_with_metadata(self, insight_service):
        # Arrange
        content = "Test insight"
        category = "architecture"
        confidence = 0.9

        # Act
        event = await insight_service.record_insight(
            content=content,
            category=category,
            confidence=confidence
        )

        # Assert
        assert event.metadata["category"] == category
        assert event.metadata["confidence"] == confidence

    @pytest.mark.asyncio
    async def test_record_insight_empty_content_raises(self, insight_service):
        with pytest.raises(ValueError) as exc_info:
            await insight_service.record_insight("")

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_record_insight_invalid_confidence_raises(self, insight_service):
        with pytest.raises(ValueError) as exc_info:
            await insight_service.record_insight(
                content="Test",
                confidence=1.5  # Invalid
            )

        assert "0.0-1.0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_insight_creates_memory(
        self,
        insight_service,
        memory_storage
    ):
        # Act
        event = await insight_service.record_insight("Test insight")

        # Assert - memory should exist
        memory = await memory_storage.get_memory(event.id)
        assert memory is not None
        assert memory.memory_type == "insight"
        assert memory.retention == 7  # Default for insights
```

## Checklist

Before considering new event type complete:

- [ ] EventType enum added
- [ ] Service class created with educational error messages
- [ ] Service registered in registry
- [ ] Memory projection mapping added
- [ ] Retention default set
- [ ] MCP tool added (if agent-facing)
- [ ] Display ID abbreviation added (optional)
- [ ] Tests written (TDD - should be first!)
- [ ] All tests passing
- [ ] Documentation updated

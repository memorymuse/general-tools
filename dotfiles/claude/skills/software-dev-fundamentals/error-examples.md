# Error Handling Examples - Extended Reference

Extended examples of fail-loud and educational error patterns.

## Educational Error Templates

### Missing Required Parameter

```python
def get_user(user_id: int | None = None) -> User:
    if user_id is None:
        raise ValueError(
            "Missing required parameter 'user_id'. "
            "Example: get_user(user_id=123). "
            "Received: get_user(user_id=None)"
        )
    return fetch_user(user_id)
```

### Invalid Type

```python
def process_items(items: list) -> list:
    if not isinstance(items, list):
        raise TypeError(
            f"Expected 'items' to be a list, got {type(items).__name__}. "
            f"Example: process_items(['a', 'b', 'c']). "
            f"Received: process_items({repr(items)[:50]})"
        )
    return [transform(item) for item in items]
```

### Out of Range

```python
def get_page(page: int, max_pages: int) -> list:
    if page < 1 or page > max_pages:
        raise ValueError(
            f"Page number {page} out of valid range [1, {max_pages}]. "
            f"Example: get_page(page=1, max_pages={max_pages}). "
            f"Received: get_page(page={page}, max_pages={max_pages})"
        )
    return fetch_page(page)
```

### Resource Not Found

```python
async def get_stream(stream_id: str) -> Stream:
    stream = await storage.get_stream(stream_id)
    if stream is None:
        raise StreamNotFoundError(
            f"Stream '{stream_id}' not found. "
            f"Available streams: {await list_stream_names()}. "
            f"Use 'muse stream create \"{stream_id}\"' to create it."
        )
    return stream
```

### Invalid State

```python
def complete_task(task: Task) -> Task:
    if task.status == "completed":
        raise InvalidStateError(
            f"Task '{task.id}' is already completed. "
            f"Current status: {task.status}. "
            f"Cannot transition from 'completed' to 'completed'. "
            f"Valid transitions from 'completed': none (terminal state)."
        )
    return mark_completed(task)
```

## Contextual Re-raising Patterns

### Database Operations

```python
async def save_event(event: Event) -> None:
    try:
        await storage.insert(event)
    except sqlite3.IntegrityError as e:
        raise StorageError(
            f"Failed to save event {event.id}: duplicate key. "
            f"Event type: {event.type}, family_id: {event.family_id}. "
            f"Check if this event was already captured."
        ) from e
    except sqlite3.OperationalError as e:
        raise StorageError(
            f"Database operation failed for event {event.id}: {e}. "
            f"Recovery: Check database connection and permissions."
        ) from e
```

### External Service Calls

```python
async def fetch_external_data(endpoint: str) -> dict:
    try:
        response = await client.get(endpoint)
        return response.json()
    except httpx.TimeoutException as e:
        raise ExternalServiceError(
            f"Timeout fetching {endpoint} after {client.timeout}s. "
            f"Recovery: Retry with exponential backoff or increase timeout."
        ) from e
    except httpx.HTTPStatusError as e:
        raise ExternalServiceError(
            f"HTTP {e.response.status_code} from {endpoint}. "
            f"Response: {e.response.text[:200]}. "
            f"Recovery: Check endpoint URL and authentication."
        ) from e
```

### File Operations

```python
def read_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise ConfigError(
            f"Config file not found: {path}. "
            f"Expected location: {path.absolute()}. "
            f"Create the file or set CONFIG_PATH environment variable."
        )
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"Invalid JSON in config file {path} at line {e.lineno}: {e.msg}. "
            f"Fix the JSON syntax error and retry."
        ) from e
```

## Error Hierarchy Pattern

```python
class MuseError(Exception):
    """Base exception for all Muse errors."""

    def __init__(self, message: str, recovery_hint: str | None = None):
        super().__init__(message)
        self.recovery_hint = recovery_hint


class ValidationError(MuseError):
    """Input validation failures."""
    pass


class StorageError(MuseError):
    """Database/storage operation failures."""
    pass


class StreamNotFoundError(MuseError):
    """Missing stream context."""
    pass


class SessionError(MuseError):
    """Session lifecycle problems."""
    pass
```

## Anti-Patterns to Avoid

### Silent Suppression

```python
# ❌ NEVER DO THIS
try:
    risky_operation()
except Exception:
    pass  # Error disappears silently
```

### Bare Except

```python
# ❌ AVOID - catches everything including KeyboardInterrupt
try:
    operation()
except:
    handle_error()

# ✅ BETTER - catch specific exceptions
try:
    operation()
except (ValueError, TypeError) as e:
    handle_error(e)
```

### Logging Without Re-raising

```python
# ❌ Error logged but execution continues with bad state
try:
    result = operation()
except OperationError as e:
    logger.error(f"Operation failed: {e}")
    # Continues with undefined 'result'

# ✅ Log AND handle appropriately
try:
    result = operation()
except OperationError as e:
    logger.error(f"Operation failed: {e}")
    raise  # Or return a safe default with clear documentation
```

### Generic Error Messages

```python
# ❌ Unhelpful
raise ValueError("Invalid input")

# ✅ Educational
raise ValueError(
    f"Invalid input: expected non-empty string, got {repr(value)}. "
    f"Example: function('valid_input')"
)
```

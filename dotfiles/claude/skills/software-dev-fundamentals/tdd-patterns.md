# TDD Patterns - Extended Reference

Advanced patterns and edge cases for Test-Driven Development.

## Async Test Patterns

### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    # Arrange
    expected = "result"

    # Act
    result = await async_function()

    # Assert
    assert result == expected
```

### Async Fixtures with Cleanup

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def database():
    """Fixture with proper cleanup to prevent hangs."""
    db = Database(":memory:")
    await db.initialize()
    yield db  # Use yield, not return!
    await db.close()  # Always cleanup!
```

**Critical**: Without proper cleanup, tests may pass but then hang for 30s+ waiting for resources.

### Testing Async Exceptions

```python
@pytest.mark.asyncio
async def test_raises_on_invalid_input():
    with pytest.raises(ValidationError) as exc_info:
        await validate_input(None)

    assert "required" in str(exc_info.value)
```

## Test Organization Patterns

### Test File Naming

```
tests/
├── unit/
│   ├── test_module_name.py      # Unit tests
│   └── test_another_module.py
├── integration/
│   └── test_database_flow.py    # Integration tests
└── conftest.py                  # Shared fixtures
```

### Test Class Organization

```python
class TestUserService:
    """Group related tests in classes."""

    class TestCreate:
        """Subgroup for create operations."""

        async def test_creates_user_with_valid_data(self):
            pass

        async def test_raises_on_duplicate_email(self):
            pass

    class TestUpdate:
        """Subgroup for update operations."""

        async def test_updates_existing_user(self):
            pass
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("valid", True),
    ("", False),
    (None, False),
    ("  ", False),
])
def test_validation(input, expected):
    assert validate(input) == expected
```

## Edge Case Testing

### Boundary Values

```python
def test_pagination_boundaries():
    # Test at boundaries
    assert paginate(items, page=0, size=10)  # First page
    assert paginate(items, page=99, size=10)  # Last page

    # Test just beyond boundaries
    with pytest.raises(ValueError):
        paginate(items, page=-1, size=10)

    with pytest.raises(ValueError):
        paginate(items, page=100, size=10)
```

### Empty/Null Cases

```python
def test_handles_empty_cases():
    assert process([]) == []
    assert process(None) is None
    assert process("") == ""
```

### Error Path Testing

```python
def test_error_paths():
    # Test each way the function can fail
    with pytest.raises(ConnectionError):
        connect_to_unavailable_server()

    with pytest.raises(TimeoutError):
        slow_operation(timeout=0.001)

    with pytest.raises(PermissionError):
        access_restricted_resource()
```

## Mocking Patterns

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mocked_service():
    mock_service = AsyncMock()
    mock_service.fetch.return_value = {"data": "value"}

    with patch("module.external_service", mock_service):
        result = await function_under_test()

    assert result == expected
    mock_service.fetch.assert_called_once_with("arg")
```

### Mocking Time

```python
from freezegun import freeze_time

@freeze_time("2025-01-15 12:00:00")
def test_time_dependent_logic():
    result = get_current_timestamp()
    assert result == 1736942400
```

## TDD Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Testing implementation | Brittle tests | Test behavior, not internals |
| Large test methods | Hard to debug | One assertion concept per test |
| Shared mutable state | Flaky tests | Fresh fixtures per test |
| Testing private methods | Over-coupling | Test through public interface |
| Skipping RED phase | Missing coverage | Always see test fail first |

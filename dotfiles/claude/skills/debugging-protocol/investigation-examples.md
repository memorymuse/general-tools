# Investigation Examples - Extended Reference

Additional debugging scenarios demonstrating the trace-before-fix methodology.

## Example 1: Async Test Timeout

**Symptom**: Tests pass (0.5s) but then hang for 30s before completing.

### Trace

```
Step 1: Where is the hang occurring?
Answer: After all tests complete, during pytest teardown phase

Step 2: What is pytest waiting for?
Answer: Event loop to close, but something is keeping it open

Step 3: What could keep the event loop open?
Answer: Unclosed async resources (connections, file handles, tasks)

Step 4: Which resources are created in tests?
Answer: SQLiteStorage instances with async connections

Step 5: Are these being cleaned up?
Answer: NO - fixtures use `return` instead of `yield`, no cleanup

Root Cause: Async fixtures not properly closing database connections
Fix: Change fixtures to use yield + cleanup
```

### Fix

```python
# Before (broken)
@pytest_asyncio.fixture
async def storage():
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    return storage  # No cleanup!

# After (correct)
@pytest_asyncio.fixture
async def storage():
    storage = SQLiteStorage(":memory:")
    await storage.initialize()
    yield storage
    await storage.close()  # Proper cleanup
```

---

## Example 2: Flaky Test - Passes Sometimes

**Symptom**: Test passes 80% of time, fails randomly with "key not found".

### Trace

```
Step 1: Where is "key not found" raised?
Answer: cache.get() in service.py:45

Step 2: What key is being looked up?
Answer: f"user:{user_id}" where user_id comes from test fixture

Step 3: When is this key set?
Answer: In background task started by previous test step

Step 4: What controls timing of background task?
Answer: asyncio.create_task() - runs concurrently, no wait

Step 5: Is test waiting for background task?
Answer: NO - test proceeds immediately, race condition

Root Cause: Race condition - test reads before background write completes
Fix: Await background task or use synchronization
```

### Fix

```python
# Before (flaky)
async def test_cached_user():
    asyncio.create_task(cache_user(user))  # Fire and forget
    result = await get_cached_user(user.id)  # May not be cached yet!

# After (reliable)
async def test_cached_user():
    await cache_user(user)  # Wait for completion
    result = await get_cached_user(user.id)  # Guaranteed to exist
```

---

## Example 3: Works Locally, Fails in CI

**Symptom**: All tests pass locally but fail in GitHub Actions.

### Trace

```
Step 1: What's the exact CI error?
Answer: "FileNotFoundError: config.json"

Step 2: Where is config.json expected?
Answer: Current working directory (relative path)

Step 3: What is CWD locally vs CI?
Answer: Local = project root, CI = runner workspace

Step 4: How is path constructed?
Answer: Path("config.json") - relative to CWD

Step 5: What's the correct approach?
Answer: Use __file__ to get path relative to source file

Root Cause: Relative path assumes CWD = project root
Fix: Use absolute path relative to source file
```

### Fix

```python
# Before (environment-dependent)
config_path = Path("config.json")

# After (portable)
config_path = Path(__file__).parent / "config.json"
```

---

## Example 4: Memory Leak in Long-Running Process

**Symptom**: Memory usage grows continuously over hours.

### Trace

```
Step 1: What objects are accumulating?
Answer: (Use memory profiler) Event objects in _event_history list

Step 2: Where is _event_history populated?
Answer: EventManager.capture() appends every event

Step 3: Is _event_history ever cleared?
Answer: NO - grows unbounded

Step 4: What is _event_history used for?
Answer: Debugging - stores last N events for inspection

Step 5: Why wasn't this caught earlier?
Answer: Tests are short-lived, don't expose the leak

Root Cause: Unbounded list growth with no eviction
Fix: Implement max size with automatic eviction (deque)
```

### Fix

```python
# Before (leaks)
class EventManager:
    def __init__(self):
        self._event_history = []  # Grows forever

    def capture(self, event):
        self._event_history.append(event)

# After (bounded)
from collections import deque

class EventManager:
    def __init__(self, history_size: int = 1000):
        self._event_history = deque(maxlen=history_size)

    def capture(self, event):
        self._event_history.append(event)  # Auto-evicts oldest
```

---

## Example 5: Import Error Only in Production

**Symptom**: Code imports fine in dev but fails with ImportError in production.

### Trace

```
Step 1: What's the exact import error?
Answer: "cannot import name 'Feature' from 'module'"

Step 2: Does 'Feature' exist in module?
Answer: Yes, defined at module.py:15

Step 3: What's different about production?
Answer: Different Python version (3.9 vs 3.11)

Step 4: Is Feature using any version-specific syntax?
Answer: Yes, uses `match` statement (Python 3.10+)

Step 5: Why didn't this fail at import time?
Answer: Syntax error in function body, only fails when function called

Root Cause: Python 3.10+ syntax used, production runs 3.9
Fix: Rewrite without match statement OR require Python 3.10+
```

---

## Debugging Tools Reference

### Print Debugging (Quick)

```python
print(f"DEBUG: {variable=}")  # Python 3.8+ f-string debugging
```

### Logging (Production-safe)

```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Processing {item_id=}, {state=}")
```

### Breakpoint (Interactive)

```python
breakpoint()  # Drops into pdb
# Or with IPython:
# import IPython; IPython.embed()
```

### Memory Profiling

```bash
pip install memory_profiler
python -m memory_profiler script.py
```

### Async Debugging

```python
import asyncio
# See all running tasks
for task in asyncio.all_tasks():
    print(f"Task: {task.get_name()}, done={task.done()}")
```

---

## Trace Documentation Template

Use this template when documenting investigations:

```markdown
## Issue: [Brief description]

**Symptom**: [What was observed]

**Trace**:
1. Where: [Location of error/unexpected behavior]
2. Values: [What values are involved]
3. Origin: [Where do values come from]
4. System: [What maintains this state]
5. Design: [Why was it built this way]

**Root Cause**: [Actual underlying problem]

**Fix**: [Solution that addresses root cause]

**Validation**: [How we verified the fix]
```

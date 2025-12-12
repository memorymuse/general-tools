# Session Handoff: filedet hist Table Display - RESOLVED

**Date**: 2025-12-11 16:20 PST
**Status**: COMPLETE - table column width issues resolved

---

## Problem Solved

The `filedet hist` table Path column was losing filenames due to Rich Table's right-truncation behavior. User wanted:
1. Filename (right side) visible/untruncated
2. Left side of path truncated with ellipsis
3. Other columns not squeezed

## Solution Implemented

### Key Insight
Rich Table truncates from the RIGHT regardless of content. The solution was:
1. Pre-truncate paths ourselves with LEFT truncation (keep right/filename)
2. Calculate exact available width dynamically
3. Use `ratio=1` on Path column to fill remaining space
4. Make pre-truncated content fit within that space

### Changes to [`utils/display.py`](../../utils/display.py)

**`shorten_path()` (~line 189)**:
- Changed `...` (3 chars) to `…` (1 char Unicode ellipsis)
- Saves 2 characters for actual path content
```python
return "…" + path[-available:]  # was "..." + path[-available:]
```

**`display_history_table()` (~line 240)**:
- Dynamic path width: `terminal_width - fixed_columns - overhead`
- Git modes (`-g`, `-gd`) drop Lines/Tokens columns for more Path space
- Tightened column widths: Modified 16→14, Ext 5→4
- Path uses `ratio=1` to fill remaining terminal width
- Precise accounting of borders (│) and cell padding (1 space each side)

**Column layout by mode**:
| Mode | Columns |
|------|---------|
| Default | Modified, Ext, Path, Lines, Tokens |
| `-g` | Modified, Ext, Path, Git |
| `-gd` | Modified, Ext, Path, Git, Last Commit |

### Width Calculation Formula
```python
# Normal mode: 31 content + 16 overhead = 47 fixed
# Git mode: 21 content + 13 overhead = 34 fixed
# Git detail: adds 28 more
path_width = terminal_width - fixed_width
```

## What Was Tried (Failed Approaches)

Documented in previous handoff, but for reference:
1. Fixed widths on Path - Rich still truncates right
2. `overflow="ignore"` - Path takes all space, other columns squeezed to nothing
3. `overflow="crop"` - Still crops from right
4. `max_width` on Path - Rich adds ellipsis on right

The winning combination: `ratio=1` + pre-truncated content that fits

## Files Modified

| File | Changes |
|------|---------|
| [`utils/display.py`](../../utils/display.py) | `shorten_path()`, `display_history_table()` |
| [`CLAUDE.md`](../../CLAUDE.md) | Added note about `-g`/`-gd` hiding Lines/Tokens |

## Test Commands

```bash
python3 filedet.py hist -n 5          # Base mode
python3 filedet.py hist -n 5 -g       # Git status
python3 filedet.py hist -n 5 -gd      # Git detail
python3 filedet.py hist -ft md -n 10  # mdhist alias pattern
```

## Remaining Work

None for this feature. Table display is working correctly.

**Potential future enhancements** (not requested):
- Auto-detect if `-gd` fits in terminal, warn if too narrow
- Consider using relative paths from cwd when inside search directory

## Key Learnings

1. **Rich Table always truncates from right** - there's no built-in left-truncation
2. **`ratio=1`** is the key to making a column fill remaining space
3. **Pre-truncate content** before passing to Rich to control what gets shown
4. **Unicode ellipsis `…`** saves 2 chars vs `...`
5. **Width calculation** must account for: column widths + borders (n+1 for n columns) + cell padding (2 per column)

## Required Reading

- [`CLAUDE.md`](../../CLAUDE.md) - Project overview and all commands

## Files to Be Aware Of

- `utils/display.py` - All display/formatting logic
- `core/history.py` - HistoryFinder class (data source for hist)

## References

- Previous WIP handoff: [`250109-2200_hist-table-display-wip.md`](./250109-2200_hist-table-display-wip.md)
- Rich Table docs: https://rich.readthedocs.io/en/latest/tables.html

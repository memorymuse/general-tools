# Session Handoff: filedet hist Table Display - WIP

**Date**: 2025-12-09 22:00 PST
**Status**: IN PROGRESS - table column width issues unresolved

---

## Problem Being Solved

`filedet hist` table Path column needs better display:
1. User wants filename visible/untruncated for easy "grabbing"
2. Left side of path can be truncated
3. Rich library keeps interfering with our custom truncation

## What We Tried (All Failed or Partially Failed)

1. **Fixed column widths** - Rich squeezed other columns
2. **`expand=True`** on Table - didn't actually expand to terminal width
3. **`ratio=1`** on Path - worked in narrow terminal but not user's
4. **`min_width=45`** on Path - still squeezed other columns
5. **No constraints** on Path - Rich truncates from RIGHT (loses filename)
6. **Custom `shorten_path()` middle-truncation** - Rich STILL truncates after us
7. **Left-truncation** (`...` + right side) - Rich truncates from right on top of it
8. **`overflow="ignore"`** - Path takes too much space, squeezes other columns to nothing

## Current State (Broken)

File: `utils/display.py` lines ~250-260

```python
table = Table(show_header=True, header_style="bold cyan", expand=True)
table.add_column("Modified (PST)", style="dim", no_wrap=True, width=16)
table.add_column("Ext", style="yellow", no_wrap=True, width=5)
table.add_column("Path", style="cyan", no_wrap=True, overflow="ignore")  # BROKEN
table.add_column("Lines", justify="right", style="blue", no_wrap=True, width=6)
table.add_column("Tokens", justify="right", style="magenta", no_wrap=True, width=7)
```

And `shorten_path()` at line ~189 does left-truncation:
```python
return "..." + path[-available:]  # where available = max_length - 3
```

Called with `max_length=60` at line ~310.

## The Core Issue

Rich Table doesn't let us control Path width independently. When Path is long:
- If we constrain it: Rich truncates from RIGHT (loses filename)
- If we don't constrain: Path expands, squeezes other columns

## User's Desired Behavior

```
...ols/filedetective/docs/handoffs/250109-1345_filedet-hist-complete.md
```
- Truncate LEFT with `...`
- Keep full filename on RIGHT
- Other columns (Modified, Ext, Lines, Tokens) should NOT be squeezed

## Suggested Next Steps

1. **Try Console width detection**: Get actual terminal width, calculate Path column width dynamically
2. **Try different Rich approach**: Maybe `Columns` instead of `Table`?
3. **Accept compromise**: Let Rich truncate but tune `shorten_path` max_length to leave room

## Key Files

- `utils/display.py`: `shorten_path()`, `display_history_table()`
- `filedet.py`: `handle_hist()` calls display functions
- `core/history.py`: `HistoryFinder.find_recent()` returns entries

## Recent Commits (this session)

All on main, pushed:
- `7326794` - smart middle-truncation (partially worked)
- `d37fac2` - let Rich handle truncation (failed)
- `f43d48c` - default Path truncation
- Multiple earlier attempts at column widths

## Test Command

```bash
python3 filedet.py hist -ft md -n 5
# or after alias reload:
mdhist
```

User added alias: `alias mdhist='filedet hist -ft md -n 10'` in ~/.zshrc

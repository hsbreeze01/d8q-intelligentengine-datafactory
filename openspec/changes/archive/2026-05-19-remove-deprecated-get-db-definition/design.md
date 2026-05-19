# Design: Remove Deprecated get_db() Definition

## Summary

Remove the deprecated `get_db()` function and its preceding comment from `app.py`. This is a pure dead-code cleanup — no behavioral change.

## Rationale

`get_db_ctx()` (context-manager version) was introduced to guarantee connections are always closed. All callers have already migrated. `get_db()` is dead code that could mislead future developers into using the non-auto-closing variant.

## Files Changed

| File | Action |
|------|--------|
| `app.py` | Remove lines 72–76 (the `# DEPRECATED` comment and `get_db()` function definition) |

## Impact

- No API changes
- No database changes
- No other files reference `get_db` from this module

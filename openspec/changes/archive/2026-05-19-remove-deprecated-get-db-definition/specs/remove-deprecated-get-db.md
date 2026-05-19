# Spec: Remove Deprecated get_db() Definition

## REMOVED Requirements

### Requirement: get_db() function

The deprecated `get_db()` function in `app.py` SHALL be removed entirely, including the `# DEPRECATED` comment above it. All code paths in the project already use `get_db_ctx()` for database access. No external module imports `get_db` from `app`.

#### Scenario: Dead code removal
- **Given** the `get_db()` function exists in `app.py` with a `# DEPRECATED` comment
- **And** no caller in the project references `get_db()`
- **When** the deprecated function and its comment are removed
- **Then** `get_db_ctx()` remains as the sole database connection utility
- **And** all existing functionality continues to work unchanged

# Delta Spec: Database Connection Lifecycle

## MODIFIED Requirements

### REQ-DB-01: WAL journal mode SHALL be set once per process

The `PRAGMA journal_mode=WAL` statement SHALL execute at most once per application process lifetime, not on every `get_db_ctx()` call.

#### Scenario: First get_db_ctx call sets WAL mode
- Given the application process has just started
- When `get_db_ctx()` is called for the first time
- Then `PRAGMA journal_mode=WAL` SHALL be executed on the connection
- And a module-level flag SHALL be set to indicate WAL is already configured

#### Scenario: Subsequent get_db_ctx calls skip WAL pragma
- Given the WAL flag has already been set
- When `get_db_ctx()` is called again
- Then `PRAGMA journal_mode=WAL` SHALL NOT be executed
- And the connection SHALL still be returned normally

### REQ-DB-02: All database connections SHALL use context manager lifecycle

Every call site that currently uses `conn = get_db()` followed by manual `conn.close()` SHALL be migrated to use `with get_db_ctx() as conn:`.

#### Scenario: Single get_db call in a function
- Given a function contains exactly one `conn = get_db()` and one `conn.close()`
- When the migration is applied
- Then the code SHALL use `with get_db_ctx() as conn:` wrapping the SQL operations
- And `conn.close()` SHALL be removed

#### Scenario: Multiple get_db calls in a function
- Given a function contains multiple `conn = get_db()` / `conn.close()` pairs
- When the migration is applied
- Then each pair SHALL be independently converted to its own `with get_db_ctx() as conn:` block
- And no `conn.close()` calls SHALL remain

#### Scenario: Exception safety
- Given a SQL operation inside a `with get_db_ctx() as conn:` block raises an exception
- When the exception propagates
- Then the connection SHALL still be closed by the context manager's `finally` block

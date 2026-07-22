---
name: sql-lint-classic
description: Lint SQL for style and a few common mistakes. Checks keyword casing, trailing whitespace, SELECT *, and missing WHERE on UPDATE/DELETE. Use to keep SQL tidy.
---

# sql-lint-classic

A lightweight SQL linter for style and a handful of common footguns.

## Checks

- Keyword casing and indentation consistency.
- `SELECT *` flagged.
- Missing `WHERE` on `UPDATE` / `DELETE` flagged.

Scope note: this is a style linter with a few safety checks, not a performance
or correctness analyzer. It has not been updated in a while.

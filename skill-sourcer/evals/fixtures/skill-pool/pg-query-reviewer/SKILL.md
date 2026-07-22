---
name: pg-query-reviewer
description: Review SQL queries and migrations for correctness and performance before they ship. Reads query text statically - no database connection - and flags missing indexes, sequential scans, join fan-out, NULL-handling bugs, and unsafe migrations (locking DDL, non-concurrent index builds). Postgres-first. Use when reviewing a SQL migration or analytics query before production.
---

# pg-query-reviewer

Statically review a SQL query or migration and report correctness and
performance risks, Postgres-first. No database connection required: it reads the
SQL text and the schema DDL you point it at, and it never executes the SQL.

## What it checks

- **Correctness.** NULL-in-predicate bugs, join fan-out that inflates
  aggregates, GROUP BY / SELECT mismatch, implicit cross joins.
- **Performance.** Sequential scans on large tables, missing or unusable
  indexes, functions applied to indexed columns, unbounded result sets.
- **Migration safety.** DDL that takes a heavy lock, index builds that are not
  `CONCURRENT`, column rewrites on big tables, constraint adds that skip the
  `NOT VALID` + `VALIDATE` split.

## How to run

Point it at the query file and the schema. It returns a ranked list of findings,
each with the offending line and a suggested rewrite. It does not connect to a
database and does not run the query.

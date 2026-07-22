# warehouse-reports (skill-sourcer eval fixture: the target project)

A small Postgres-backed reporting service. The team hand-writes raw SQL - schema
migrations in `warehouse/migrations/` and analytical queries in `analytics/` -
and keeps shipping correctness bugs and slow queries to production.

This directory is the *target project* a skill search runs against. The user's
prompt and its explicit requirements are below. The seeded candidate pool the
search should surface is in `../skill-pool/`; the grading ground truth is in
`../../expected.md`.

## The ask (the prompt Phase 0 parses)

> Find me a skill that reviews our SQL for correctness and performance before it
> hits production. We hand-write Postgres migrations and analytics queries and
> keep shipping bugs and slow queries. Don't just hand me the most popular thing.

## Explicit requirements (what Phase 0 should extract and restate)

Hard requirements (pass/fail filters):

- **H1.** Reviews SQL queries for correctness and/or performance.
- **H2.** Works statically on SQL text - does not require a connection to the
  production database to do its job.

Nice-to-haves (raise the relevance score, do not gate):

- **N1.** Postgres-aware.
- **N2.** Understands schema migrations specifically.

Stated anti-signal: the user explicitly does not want popularity ranked first
("don't just hand me the most popular thing"). This is the relevance-over-
popularity test in the user's own words.

---
name: productionize
description: "Take a working codebase to production-grade. Audits for the operational failure modes frontier LLMs demonstrably miss (retry amplification across layers, DB-pinging liveness probes, lock-queue-blocking migrations, dual writes, exit-now SIGTERM handlers, unbounded queues, stale feature flags, oversized pools), applies prioritized fixes, and generates operational artifacts wired to the real code: runbooks, alert thresholds, and pre-committed rollback triggers. Use this whenever the user asks \"is this production ready\", \"productionize this\", \"harden for prod\", \"will this survive real traffic\", \"we launch next week, is X ready\", or otherwise wants a working service made operationally safe. Distinct from source-security/correctness review, which it routes to code-audit rather than duplicating."
---

# Productionize

Take a service that *works* and make it survive production: real traffic, real failures, real deploys.
The job is operational reliability, not correctness or security; those are code-audit's. This skill owns the half that models skip.

## The delta-only rule (read this first)

Encode **only what a frontier LLM won't do on its own first run.** Nothing else earns its place here.

No SQLi lectures, no "add error handling," no checklist recitation; models do all that unprompted. And model self-review is unreliable: elaborate "review harder" prompting actually *increases* misjudgment, so introspection is not a check. Therefore every check below is a **concrete, evidence-producing action**: a grep target, a config diff, a falsifiable question with a written answer. Never "consider whether." Always "find X, show the line, state the blast radius."

If you catch yourself about to write advice a competent model already follows, delete it. The value is the delta.

## Phase 0 - Tier and inventory

One elicitation round. If the user says "go ahead" or "just do it," infer from the repo and state your inferences.

**Criticality tier** (Mercari-style) gates which checks run and which artifacts get built:

- `experimental` - hobby, internal, or pre-revenue. Flag-only on most checks; no PDB/probe/cert deep-dives.
- `standard` - real users, revenue-adjacent, an on-call exists. Audit + fix across the board.
- `critical` - money, safety, or a large blast radius. Audit + fix + *demonstrate the fix*, plus rehearsals.

**Stack inventory.** Record: runtime/language, orchestrator (k8s? ECS? bare?), datastores, queues, IaC, and existing observability. These decide which checks even apply (no migration check without a relational DB).

**Route security and correctness out.** Source-level security (injection, authz, secrets, supply chain) and functional correctness belong to **code-audit** and the Trail of Bits suite. If installed, hand off. If not, leave a one-line pointer. Do not re-implement them here.

Record the tier as a `D` row in the evidence ledger (`.evidence/` in the target repo, per evidence-protocol.md). Findings, fixes, and demonstrations are `P` rows.

## Tier×check matrix

Single source of tier truth. Where prose elsewhere disagrees, this matrix wins.

| Check / deliverable | experimental | standard | critical |
|---|---|---|---|
| B1 Retry amplification | flag only | audit + fix | audit + fix + budget math shown |
| B2 Sustaining loops + 3 system questions | question (b) only | all three, written | all three + cold-start demonstration |
| B3 Health-check blast radius | skip | audit + fix | audit + fix + probe-failure demonstration |
| B4 Migration lock arithmetic | skip | audit + fix | audit + fix + migration rehearsal |
| B5 Config blast radius | flag only | audit + fix | audit + fix + fallback demonstration |
| B6 Graceful shutdown | flag only | audit + fix | audit + fix + SIGTERM demonstration |
| B7 Idempotency | audit + fix (money paths always) | audit + fix | audit + fix + replay demonstration |
| B8 Dual writes / CDC | flag only | audit + fix | audit + fix + slot monitoring |
| B9 Pool sizing | flag only | audit + fix | audit + fix |
| B10 Isolation levels | skip | flag | audit + fix |
| B11 Cert inventory | skip | inventory | inventory + renewal automation check |
| B12 Flag debt | flag only | audit + fix | audit + fix |
| B13 Observability | logging pass | logging + metrics + shared-fate | full, incl. dashboards-fate audit |
| Runbooks / alerts / rollback triggers | skip | generate | generate + deploy≠release + rehearsal |

## Phase 1 - Blindspot audit

Run the checks the matrix calls for at the chosen tier. Each is one concrete action; the full evidence, math, and citations live in `references/blindspots.md`. Read it when you run a check so you can recite the anchor to the user. Emit a `P` row per finding with a `risk` (consequence × likelihood).

1. **B1 Retry amplification.** Grep every retry site (mesh, client libs, SDKs, HTTP clients, queue consumers, DB drivers). Flag missing jitter, missing caps, no budget, and >1 layer retrying the same call path. Models *add* retries; they never audit them.
2. **B2 Sustaining loops.** Enumerate every load-begets-load path: unbounded queues, work accepted past the client deadline, error paths costlier than success paths, warm-cache dependence.
3. **B3 Health-check blast radius.** Assert liveness probes touch **no** dependency (a DB-pinging liveness = restart storm on any blip). Flag deep readiness sharing a dependency fleet-wide, and CPU autoscaling on an I/O-bound service (scales *down* under downstream degradation).
4. **B4 Migration lock arithmetic.** A waiting `ACCESS EXCLUSIVE` lock blocks everything queued behind it. Require `lock_timeout` (≤2s) + `statement_timeout` + retry. Flag FK/`NOT NULL`/type changes without `NOT VALID`/expand-contract, and `int32` PKs on high-volume tables.
5. **B5 Config blast radius.** Does config/flag/policy data take a different path than code (instant, global, unstaged)? Is it validated as untrusted input (size caps, schema)? Any panic/unwrap on config parse in a hot path? Last-known-good fallback?
6. **B6 Graceful shutdown.** The `SIGTERM` handler must fail readiness first, wait for endpoint propagation, drain in-flight, then exit. "Exit now on SIGTERM" is the bug; it 502s every deploy.
7. **B7 Idempotency.** Every side-effecting endpoint anything retries must take an idempotency key persisted **atomically with the effect**. Money paths always. Treat "exactly-once" consumer claims as at-least-once + dedupe, or wrong.
8. **B8 Dual-write inconsistency.** DB write + separate publish (event/cache/index) with no outbox/CDC = guaranteed divergence. If CDC exists, require replication-slot lag monitoring and a WAL bound.
9. **B9 Pool sizing.** Compute pool × instances vs `max_connections`. Oversized pools collapse latency (smaller is faster). Flag missing acquisition timeouts. Sane start: cores×2 + spindles.
10. **B10 Isolation levels.** Verify the code's concurrency assumptions against what the engine actually provides (the default is weaker than the name implies). Require `FOR UPDATE` or version columns where needed. Check fsync/write-concern vs durability claims.
11. **B11 Cert inventory.** Enumerate all certs **including internal mTLS/signing certs**, with expiry + renewal automation. The outage-makers are the internal ones nobody monitors.
12. **B12 Flag debt.** Find stale flags, repurposed flags, dead code reachable via config. Every flag needs an owner and expiry.
13. **B13 Observability.** Do dashboards/telemetry depend on the thing they monitor (shared fate)? Then a **forced** logging pass: structured logs, correlation IDs, golden-signal metrics. Forced because agents under-log in 58% of repos and ignore explicit logging instructions 67% of the time, so a soft "add logging" does not survive.

**Then the three system-level questions** LLMs never ask, answered in writing as `P` rows (per the matrix: (b) always; (a) and (c) at standard+):
(a) list every load-begets-load feedback loop; (b) what happens at cold start under full load (cache 0%, all clients reconnecting, pools empty); (c) which reliability automation (retries, failover, autoscaling, health checks, config pipelines) can itself remove capacity or amplify load.

Why (c) is the sharpest question: the evidence says these mechanisms, not application bugs, cause the **longest** outages. The safety system is the failure mode.

## Phase 2 - Fix (with self-safety)

Rank findings by consequence × likelihood (the `risk` field). Apply smallest-blast-radius first, one concern per commit.

**This skill's own changes are subject to its own thesis.** This phase modifies health checks, `SIGTERM` handlers, and pool sizes, exactly the reliability mechanisms that cause the worst outages when they are wrong. So:

- Every fix gets a `P` row stating the blast radius **if the fix itself is wrong.**
- At `critical` tier, operational-mechanism changes (probe, shutdown, pool) are **proposed with a pre-committed rollback trigger** (Phase 3's artifact applied reflexively to our own diff), not auto-applied.
- A probe/shutdown/pool change is not "done" until Phase 4 demonstrates the *fix* working, not merely that the finding existed.

## Phase 3 - Operational artifacts

Generate from the actual code, never from templates with plausible values. Templates and the provenance gate live in `references/artifacts.md`.

- **Runbooks** for won't-start / dependency-down / rollback, with the repo's real commands and real dependency names.
- **Alert definitions** with thresholds tied to the limits the audit established (pool exhaustion, replication lag, cert-expiry windows), not round numbers.
- **Pre-committed rollback triggers**: "roll back if X within Y minutes," decided before deploy, not during the incident.
- `critical` adds: deploy≠release separation check (via flags), and migration-rollback rehearsal steps.

**Artifact-provenance gate (deterministic, generation-time).** Every command, dependency name, metric, and threshold in a runbook or alert must cite a `P` row (file:line or command output). Grep the artifacts for command/metric tokens; any uncited token is flagged. Where safe, dry-run commands (`--help`, `-n`, syntax check, `systemctl cat`) as evidence. A runbook citing a nonexistent unit, or an alert on a never-emitted metric, must be impossible to ship silently. See the gate steps in `references/artifacts.md`.

## Phase 4 - Prove, don't claim

Where a failure mode is checkable by execution, **demonstrate it** (required per the tier matrix):

- Kill the DB connection in a test and show the degradation (and, for a fix, show it degrading *gracefully* now).
- Send `SIGTERM` and show the drain sequence: readiness fails, traffic stops, in-flight completes, then exit.
- Run a risky migration against a *copy* with an induced long-running query, and show `lock_timeout` firing instead of the API stalling.

Where the environment can't support a demonstration (no container runtime, cloud-managed DB), **skip it and list it as unverified surface.** Never fake a demonstration. An unrun check is a `P` row with status `unverifiable`, which is a finding, not a pass.

**Production-safety boundary (verbatim, non-negotiable): never point demonstrations at production credentials or systems.** Demonstrations run only against ephemeral/containerized targets. Refuse, with an explanation, any connection string matching a production-shaped pattern: non-localhost hosts, cloud DB endpoints (`*.rds.amazonaws.com`, `*.postgres.database.azure.com`, and the like). The whole point of this skill is that reliability automation causes outages; a demonstration that points at prod *is* that failure mode.

## Closing

Chain **`REQUIRED (if available): adversarial-verify`** on the findings packet. It audits the `P` ledger directly (evidence-protocol.md), catching over-claims and unsourced artifact tokens.

Also chain: **code-audit** for the security/correctness half; **fix-issue** when the audit uncovers an active bug (not just a reliability gap).

The report tells the user **when to re-audit**: cert-expiry and threshold assertions carry `expiry` dates, so freshness-sensitive findings resurface rather than rot silently.

## Honest scope

This is an audit-and-fix skill. The checks are concrete agent actions you perform now; they need no external scripts to run. If a repo ships hardening scripts (e.g. a provenance-grep or a migration-rehearsal harness), treat them as an optional hardening layer, not a prerequisite; the audit stands on its own.

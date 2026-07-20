# Spec: productionize

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

Take a working codebase to production-grade: audit for the operational failure modes
frontier LLMs demonstrably miss, apply prioritized fixes, and generate the operational
artifacts (runbooks, alert definitions, rollback triggers) wired to the actual code.

**The delta-only rule (this skill's spine):** the skill encodes ONLY what a frontier
LLM won't do on its own first run. No SQLi lectures, no "add error handling," no
checklist recitation - models do that unprompted, and the evidence says LLM
self-review is unreliable anyway (elaborate "review harder" prompting *increases*
misjudgment). Every check is therefore a concrete evidence-producing action - a grep
target, a config diff, a falsifiable question - never introspection. Enforcement is
mechanical: the eval prunes any check the no-skill baseline already passes
(per-check obsolescence, below).

## Market position (researched 2026-07)

Crowded zone: checklist-recitation skills (cmd-productionize et al.) that restate what
models already know. Best prior art covers half each: swyxio's
productionize-app-with-services (transformation + evidence, stack-opinionated,
ops-light) and Agentman's production-readiness-reviewer (ops-complete, assessment-only).
Nothing combines transformation + failure-mode drills + operational deliverables +
evidence enforcement + criticality tiers. Empirical basis for the blindspot framing:
agents under-log (58% of repos) and ignore logging instructions 67% of the time
(arXiv 2604.09409); agents defer NFRs wholesale (Augment "80% problem"); ~half of
functionally-correct LLM backends are exploitable (BaxBench). The installed code-audit
+ Trail of Bits suite already own source-security/correctness/maintainability - this
skill owns the operational half and routes to them (hybrid rule) rather than
duplicating.

## Files

```
productionize/
  SKILL.md                 # tier elicitation → blindspot audit → fix → artifacts → prove
  references/blindspots.md # the evidence-backed check catalog (below), loaded per phase
  references/artifacts.md  # runbook / alert / rollback-trigger templates
  evals/                   # colocated evals (layout per evidence-protocol.md)
```

## Flow

**Phase 0 - Tier + inventory (one elicitation round; "go ahead" = infer).**
Criticality tier (Mercari-style): `experimental` / `standard` / `critical` - gates
which checks run and which artifacts are generated (a hobby app gets no PDB audit).
Stack inventory: runtime, orchestrator, datastores, queues, IaC, existing
observability. Security/correctness routed to code-audit + Trail of Bits suite if
installed; else a one-line pointer, never a re-implementation.

**Phase 1 - Blindspot audit.** The catalog in `references/blindspots.md`, every item a
concrete check with its evidence source. The core thirteen:

1. **Retry amplification** - find every retry site across layers (mesh, client lib,
   SDK, queue consumer); flag missing jitter, missing caps, missing retry budgets, and
   >1 layer retrying the same call path. The math: (1+N)^L attempts across L layers
   (SRE book: 3 layers × 3 retries = 64 attempts per user action). LLMs *add* retries;
   they never audit them.
2. **Sustaining feedback loops ("will it recover?")** - enumerate every path where
   load creates more load: unbounded queues, work accepted after client deadline
   passed (no deadline propagation), error paths costlier than success paths,
   cold-cache dependence. Ask: what happens at cold start under full production load,
   cache at 0%, all clients reconnecting? (Metastable-failures OSDI'22; AWS Oct 2025
   congestive collapse.)
3. **Health-check blast radius** - liveness probes must touch no dependency (DB ping
   in liveness = restart storm during DB blip); deep readiness sharing a dependency
   across services = fleet-wide deregistration; autoscaling on CPU for I/O-bound
   services scales DOWN during downstream degradation (Slack Jan 2021).
4. **Migration lock-queue arithmetic** - a waiting ACCESS EXCLUSIVE lock blocks every
   query behind it, so even a fast DDL queued behind one slow read takes the API down
   for the read's remaining duration (GoCardless: ~15s outage from exactly this). Require
   `lock_timeout` (≤2s) + `statement_timeout` + retry on migrations; flag FK/NOT
   NULL/type changes without NOT VALID / expand-contract; int32 PKs on high-volume
   tables.
5. **Config deploys are code deploys** - does config/flag/policy data take a different
   path than code (instant, global, unstaged)? Does its consumer validate it as
   untrusted input (size caps, schema)? Any panic/unwrap on config parse in a hot
   path? Last-known-good fallback? (Cloudflare Nov 2025, CrowdStrike, GCP Jun 2025 -
   the same shape three times.)
6. **Graceful-shutdown ordering** - SIGTERM handler must fail readiness FIRST, wait
   for endpoint propagation, drain in-flight, then exit; "exit now on SIGTERM" is the
   bug, and it 502s on every deploy.
7. **Idempotency where retries exist** - every side-effecting endpoint that anything
   retries must accept an idempotency key persisted atomically with the effect;
   "exactly-once" consumer claims = at-least-once + dedupe or wrong.
8. **Dual-write inconsistency** - DB write + event/cache/index publish without
   outbox/CDC = guaranteed divergence; if CDC exists, replication-slot lag monitoring
   and WAL bounds (the slot-fills-disk failure).
9. **Connection-pool sizing** - pool × instances vs max_connections; oversized pools
   (smaller is faster - HikariCP/Oracle demo: shrinking 2048→96 connections cut
   latency ~100ms→~2ms; formula cores×2 + spindles); missing acquisition timeouts.
10. **Isolation levels lie** - verify the code's concurrency assumptions against what
    the engine actually provides (Jepsen: MySQL REPEATABLE READ permits lost updates →
    require FOR UPDATE or version columns); fsync/write-concern vs durability claims.
11. **Internal cert inventory** - enumerate certs incl. internal mTLS/signing certs
    with expiry + renewal automation; the outage-makers are the internal ones nobody
    monitors (Ericsson 2018: ~32M O2 UK users down, O2 sought ~£100M; Teams 2020).
12. **Feature-flag debt as reliability risk** - stale flags, repurposed flags, dead
    code reachable via config (Knight Capital: dead flag + partial deploy = $460M);
    flags need owners and expiry.
13. **Observability shared fate + agent under-logging** - do dashboards/telemetry
    depend on the thing they monitor (Roblox, 73h)? Forced logging pass: structured
    logs, correlation IDs, golden-signal metrics - agents modify logging less than
    humans in 58% of repos and ignore explicit logging instructions 67% of the time.

**Citation rule for `blindspots.md`**: every outage number, dollar/user figure, and
benchmark result carries its primary-source citation inline - these get recited to
users, and this review itself caught two secondary-source numbers that were wrong.
`blindspots.md` is the single source of truth; the eval's `expected.md` and this spec
reference checks by ID, never by copied text.

Plus the three system-level questions LLMs never ask, answered in writing:
(a) list every load-begets-load feedback loop; (b) what happens at cold start under
full load; (c) which reliability automation (retries, failover, autoscaling, health
checks, config pipelines) can itself remove capacity or amplify load - the evidence
says these mechanisms, not app bugs, cause the longest outages.

## Tier×check matrix (single source of tier truth; where prose disagrees, the matrix wins)

| Check / deliverable | experimental | standard | critical |
|---|---|---|---|
| 1 Retry amplification | flag only | audit + fix | audit + fix + budget math shown |
| 2 Sustaining loops + 3 system questions | question (b) only | all three, written | all three + cold-start demonstration |
| 3 Health-check blast radius | skip | audit + fix | audit + fix + probe-failure demonstration |
| 4 Migration lock arithmetic | skip | audit + fix | audit + fix + migration rehearsal |
| 5 Config blast radius | flag only | audit + fix | audit + fix + fallback demonstration |
| 6 Graceful shutdown | flag only | audit + fix | audit + fix + SIGTERM demonstration |
| 7 Idempotency | audit + fix (money paths always) | audit + fix | audit + fix + replay demonstration |
| 8 Dual writes / CDC | flag only | audit + fix | audit + fix + slot monitoring |
| 9 Pool sizing | flag only | audit + fix | audit + fix |
| 10 Isolation levels | skip | flag | audit + fix |
| 11 Cert inventory | skip | inventory | inventory + renewal automation check |
| 12 Flag debt | flag only | audit + fix | audit + fix |
| 13 Observability | logging pass | logging + metrics + shared-fate | full, incl. dashboards-fate audit |
| Runbooks / alerts / rollback triggers | skip | generate | generate + deploy≠release + rehearsal |

**Phase 2 - Fix (with self-safety).** Findings ranked by consequence × likelihood
(ledger `risk` field); fixes applied smallest-blast-radius first, one concern per
commit. **The skill's own changes are subject to its own thesis** - reliability
mechanisms cause outages, and this phase modifies health checks, SIGTERM handlers, and
pool sizes. Therefore: every fix gets a `P` row stating the blast radius if the fix
itself is wrong; at `critical` tier, operational-mechanism changes are *proposed* with
a pre-committed rollback trigger (Phase 3's artifact applied reflexively to our own
diffs), not auto-applied; pool/probe/shutdown changes are not "done" until Phase 4
demonstrates the *fix* working, not just the finding existing.

**Phase 3 - Operational artifacts (generated from the actual code, not templates).**
Runbooks (won't-start / dependency-down / rollback, with real commands and real
dependency names); alert definitions with thresholds tied to audited limits (pool
exhaustion, replication lag, cert expiry windows); **pre-committed rollback triggers**
("roll back if X within Y minutes" decided before deploy, not during the incident).
`critical` tier adds: deploy≠release separation check (flags), migration rollback
rehearsal steps. **Artifact-provenance gate (deterministic, generation-time)**: every
command, dependency name, metric, and threshold in a runbook or alert must cite a
ledger `P` row (file:line or command output); a grep flags uncited command/metric
tokens; where safe, commands are dry-run (`--help`, `-n`, syntax check) as evidence. A
runbook citing a nonexistent unit or an alert on a never-emitted metric must be
impossible to ship silently.

**Phase 4 - Prove, don't claim.** Where a failure mode is checkable by execution, the
skill demonstrates it: kill the DB connection in a test and show degradation; send
SIGTERM and show the drain sequence; run the migration against a copy with an induced
long-running query. Demonstrations required per the tier matrix; where the environment
can't support one (no container runtime, cloud-managed DB), it is skipped and listed
as unverified surface - never faked. **Production-safety boundary (from microworld,
verbatim in SKILL.md): never point demonstrations at production credentials or
systems.** Demonstrations run only against ephemeral/containerized targets; connection
strings matching production-shaped patterns (non-localhost hosts, cloud DB endpoints)
are refused with an explanation. Closer: `REQUIRED (if available): adversarial-verify`
on the findings packet.

## Suite integration

Findings and demonstrations are evidence-protocol assertions (prefix `P`); tier
recorded as a `D` row; cert-expiry and threshold assertions carry `expiry` dates -
the report tells the user when to re-audit. Chains: code-audit (security half),
fix-issue (when the audit uncovers an active bug), adversarial-verify (closer).

## Evals & testing plan

Artifacts in `evals/`; shared rules in [evidence-protocol.md](evidence-protocol.md).
- **Fixture**: a small service seeded with blindspot violations - layered retries
  without jitter, DB-pinging liveness probe, migration without lock_timeout, dual
  write, exit-now SIGTERM handler, unbounded in-memory queue, stale repurposed flag,
  oversized pool, missing idempotency on a retried POST - plus clean decoys.
- **Catch-rate scoring (deterministic)**: recall on seeded violations, FP rate on
  decoys, ≥3 reps, no-skill baseline arm.
- **Per-check obsolescence (the delta-only enforcement, novel)**: pruning happens at
  **sub-assertion granularity** against the per-violation ground truth in
  `expected.md` - a "catch" means the baseline identified the specific seeded
  violation, not that it mentioned the topic (a baseline saying "add jitter" does NOT
  prune the layered-retry audit it never performed). A sub-check is pruned only when
  the baseline catches it in ≥2/3 reps **in both model tiers**. Pruned checks move to
  a `pruned.md` graveyard - their seeded violations STAY in the fixture, so a model
  regression re-fails the seed and the check is restored. Re-pruning and re-adding run
  every time the eval runs. The skill shrinks monotonically toward the frontier delta
  without ever losing the instruments that detect the frontier moving back.
- **Artifact quality (judged)**: runbooks/alerts judged blind against the fixture's
  actual failure modes - are commands real, thresholds tied to audited values?
  Judge-bias mitigations per shared rules.
- **RED baseline**: expected misses per the evidence - baseline adds retries instead
  of auditing them, generates DB-pinging health checks, writes exit-now SIGTERM
  handlers, skips logging. GREEN: catalog catches all seeded violations. REFACTOR:
  close rationalizations.

## Out of scope

Live-integration verification (does the PagerDuty rotation exist) - products own
that; the skill generates the questions. Source-code security/correctness - owned by
code-audit + Trail of Bits (routed, not duplicated). Load-test execution - the skill
prepares readiness and thresholds; running 2× peak traffic is the user's
infrastructure decision.

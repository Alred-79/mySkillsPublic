# Blindspots catalog

The thirteen operational failure modes frontier LLMs miss on a first pass, each with the concrete check and its evidence.
SKILL.md runs the checks; this file holds the anchors you recite to the user and the reasoning behind each check.
Cite from here by check ID (B1..B13), never by copying prose into `expected.md` or a report.

## Two-class citation rule

Every figure below is one of two kinds, and they are not interchangeable.

- **Primary-source rate / benchmark**: a measured rate, formula, or reproducible result from the source of record (a paper, the engine's own docs, a vendor benchmark). These generalize. You may present them as evidence that a class of bug matters. Example: "MySQL REPEATABLE READ permits lost updates (Jepsen)."
- **Illustrative incident**: a single named outage with a dollar or user figure. These are anecdotes, not base rates. Use them to make a failure *concrete and memorable*, never to imply "this will cost you $X." Always attribute the company and date. Example: "Knight Capital lost ~$460M in 2012 to a dead flag plus a partial deploy."

When you recite a number to a user, say which kind it is. An illustrative incident quoted as if it were a rate is a misuse of the evidence. Every figure here carries its date; keep the date when you quote it.

A note on freshness: the incident dates below are the source of record as of this catalog's authoring (2026-07). Rates and formulas are stable; incident links rot. If a user needs the citation for a decision, re-fetch the primary source rather than trusting the summary.

## Contents

- [B1 - Retry amplification](#b1---retry-amplification)
- [B2 - Sustaining feedback loops (will it recover?)](#b2---sustaining-feedback-loops-will-it-recover)
- [B3 - Health-check blast radius](#b3---health-check-blast-radius)
- [B4 - Migration lock-queue arithmetic](#b4---migration-lock-queue-arithmetic)
- [B5 - Config deploys are code deploys](#b5---config-deploys-are-code-deploys)
- [B6 - Graceful-shutdown ordering](#b6---graceful-shutdown-ordering)
- [B7 - Idempotency where retries exist](#b7---idempotency-where-retries-exist)
- [B8 - Dual-write inconsistency](#b8---dual-write-inconsistency)
- [B9 - Connection-pool sizing](#b9---connection-pool-sizing)
- [B10 - Isolation levels lie](#b10---isolation-levels-lie)
- [B11 - Internal cert inventory](#b11---internal-cert-inventory)
- [B12 - Feature-flag debt as reliability risk](#b12---feature-flag-debt-as-reliability-risk)
- [B13 - Observability shared fate + agent under-logging](#b13---observability-shared-fate--agent-under-logging)
- [The three system-level questions](#the-three-system-level-questions)

---

## B1 - Retry amplification

**Check.** Find every retry site across every layer: service mesh (Envoy/Istio), client libraries, cloud SDKs, HTTP clients, queue consumers, database drivers.
For each, flag: missing jitter, missing cap on attempts, no retry budget, and the one models never look for, more than one layer retrying the same logical call path.

**Why the model misses it.** LLMs *add* retries when asked to make code robust; they do not audit the retries already present, and they never reason about retries stacking across layers.

**The math.** Retries compound multiplicatively: with N retries at each of L layers, one user action becomes up to (1+N)^L downstream attempts.

**Anchor.** *Site Reliability Engineering* (Google, O'Reilly 2016), "Handling Overload": 3 layers each retrying 3 times = up to 64 attempts per user action. This is the primary-source formula, not an incident.

---

## B2 - Sustaining feedback loops (will it recover?)

**Check.** Enumerate every path where load creates more load: unbounded queues, work accepted after the client's deadline has already passed (no deadline propagation), error paths more expensive than success paths, dependence on a warm cache to serve at all.
Then answer in writing: what happens at cold start under full production load, with the cache at 0% and every client reconnecting at once?

**Why it matters.** A system can be stable under normal load and still have no path back once tipped; it sustains its own overload. These are the metastable failures that produce the longest outages, because adding capacity does not clear them.

**Anchors.**
- *Metastable Failures in Distributed Systems* (Bronson et al., HotOS 2021; expanded work OSDI 2022): the sustaining-effect framework. Primary source.
- Illustrative incident: the AWS US-EAST-1 event of October 2025 exhibited congestive-collapse dynamics (a control plane that could not drain its own backlog). Named incident, dated.

---

## B3 - Health-check blast radius

**Check.** Liveness probes must touch **no** dependency. A liveness probe that pings the database restarts the pod on any DB blip, turning a brief blip into a restart storm.
Deep readiness probes that share a dependency across many services cause fleet-wide deregistration when that dependency wobbles.
Autoscaling on CPU for an I/O-bound service scales **down** during downstream degradation (CPU falls while the service waits), removing capacity exactly when it is needed.

**Why the model misses it.** Asked for a health check, the model writes one that "checks everything," which is precisely the anti-pattern: it couples liveness to dependencies.

**Anchor.** Illustrative incident: Slack's outage of 2021-01-04, where autoscaling and health-check interactions removed capacity under load. Named incident, dated. The liveness/readiness distinction itself is standard Kubernetes guidance (primary: Kubernetes docs, "Configure Liveness, Readiness and Startup Probes").

---

## B4 - Migration lock-queue arithmetic

**Check.** A waiting `ACCESS EXCLUSIVE` lock blocks every query queued behind it. So even a fast DDL, if it queues behind one slow read, takes the API down for the remaining duration of that read.
Require on every migration: `lock_timeout` (≤ 2s) so the DDL gives up rather than holding the queue, plus `statement_timeout`, plus retry.
Flag: adding a foreign key, `NOT NULL`, or a type change without the `NOT VALID` / expand-contract two-step; `int32` primary keys on high-volume tables (exhaustion is a hard outage).

**Why it matters.** The danger is not the DDL's own duration; it is what piles up behind the lock it is waiting for. Models reason about the former and never the latter.

**Anchor.** Illustrative incident: GoCardless documented a ~15-second outage from exactly this lock-queue interaction ("Zero-downtime Postgres migrations - the hard parts", GoCardless engineering blog, 2016). Named incident, dated. The `lock_timeout` remedy is primary-source Postgres behavior.

---

## B5 - Config deploys are code deploys

**Check.** Does configuration, a feature flag, or a policy blob take a *different* path to production than code (instant, global, unstaged, no canary)?
Does the consumer validate it as untrusted input (size caps, schema validation)?
Is there any `panic`/`unwrap`/uncaught-throw on config parse in a hot path?
Is there a last-known-good fallback if the new config is bad?

**Why it matters.** Config changes bypass the safeguards code changes go through, yet reach further and faster. The same shape has caused three major outages.

**Anchors.** Illustrative incidents, all the same shape, all dated:
- Cloudflare, 2025-11: a config/feature-file change propagated globally and crashed request handling.
- CrowdStrike, 2024-07-19: a content/config channel update crashed hosts worldwide.
- Google Cloud, 2025-06: a config/policy propagation triggered a broad outage.

---

## B6 - Graceful-shutdown ordering

**Check.** On `SIGTERM`, the handler must, in order: (1) fail readiness first, (2) wait for endpoint-removal propagation, (3) drain in-flight requests, (4) then exit.
"Exit now on SIGTERM" is the bug. It 502s on every single deploy, because the load balancer keeps routing to the pod for the propagation window after it has already died.

**Why the model misses it.** A naive `SIGTERM` handler calls `process.exit()` / `os.Exit()` immediately; that reads as correct and passes tests, but breaks under real traffic during rollouts.

**Anchor.** Primary source: Kubernetes pod-termination lifecycle (docs, "Termination of Pods"). Endpoint removal and container `SIGTERM` are concurrent, so the app must fail readiness and drain rather than exit at once.

---

## B7 - Idempotency where retries exist

**Check.** Every side-effecting endpoint that *anything* retries (client, mesh, queue) must accept an idempotency key, persisted **atomically with the effect** (same transaction), not checked-then-written.
Money paths get this at every tier, always.
Treat any "exactly-once" consumer claim as false: real delivery is at-least-once, so it is either at-least-once + dedupe, or it is wrong.

**Why it matters.** Retries (B1) plus non-idempotent side effects equal duplicate charges, double sends, and doubled writes. The model adds the retry and never the dedupe.

**Anchor.** Primary-source semantics: at-least-once is the delivery guarantee of every mainstream queue and retrying client; "exactly-once" end-to-end without dedupe is not achievable. (Standard distributed-systems result; see e.g. the delivery-semantics sections of Kafka and SQS documentation.)

---

## B8 - Dual-write inconsistency

**Check.** A database write followed by a separate publish to an event bus, cache, or search index, with no outbox or CDC between them, will diverge whenever the second write fails after the first succeeds.
Require the transactional-outbox or change-data-capture pattern.
Where CDC already exists, require replication-slot lag monitoring and a WAL size bound: an unconsumed slot fills the disk and takes the primary down.

**Why it matters.** There is no atomicity across two systems. Divergence is not a risk; it is a guarantee over enough events. Models write the two writes back-to-back and call it done.

**Anchor.** Primary-source pattern: transactional outbox / CDC as the standard remedy for the dual-write problem (widely documented; the failure is the absence of atomicity across heterogeneous stores). The replication-slot-fills-disk failure is documented Postgres behavior.

---

## B9 - Connection-pool sizing

**Check.** Compute pool_size × instance_count and compare it to the database's `max_connections`. Oversized pools are a top cause of latency collapse: smaller pools are frequently *faster*.
Flag missing acquisition timeouts (a request that waits forever for a connection is an outage in disguise).
Sane starting formula: connections ≈ cores × 2 + effective_spindle_count.

**Why the model misses it.** Bigger looks safer, so models set large pools; the truth is counterintuitive and they never do the multiplication against `max_connections`.

**Anchor.** Primary-source benchmark: the HikariCP / Oracle "pool sizing" demonstration. Shrinking a connection pool from 2048 to 96 connections cut per-transaction latency from ~100ms to ~2ms on the same load. This is a reproducible benchmark, not an incident.

---

## B10 - Isolation levels lie

**Check.** Verify the code's concurrency assumptions against what the database engine *actually* provides at its configured isolation level. The default is usually weaker than developers assume.
Where a read-modify-write needs protection, require `SELECT ... FOR UPDATE` or a version/optimistic-lock column.
Check `fsync` / write-concern settings against any durability claim the code or docs make.

**Why it matters.** "REPEATABLE READ" does not mean what the name implies, and a lost update looks exactly like correct code until two writers collide in production.

**Anchor.** Primary source: Jepsen's MySQL analysis. MySQL's REPEATABLE READ permits lost updates (and other anomalies), contrary to the name. Reproducible finding, not an incident.

---

## B11 - Internal cert inventory

**Check.** Enumerate every TLS/signing certificate, **including internal ones**: mTLS between services, signing certs, client certs, private-CA intermediates. For each, record expiry date and whether renewal is automated.
The public edge cert is monitored by everyone; the outage-makers are the internal certs nobody watches.

**Why it matters.** An expired internal cert takes down service-to-service traffic silently, and the failure is confusing because the public site looks fine.

**Anchors.** Illustrative incidents, dated:
- Ericsson, 2018-12-06: an expired certificate in Ericsson software knocked out mobile data for ~32M O2 UK users (and millions more across other operators); O2 publicly sought ~£100M in damages.
- Microsoft Teams, 2020-02-03: an expired certificate caused a global Teams outage.

---

## B12 - Feature-flag debt as reliability risk

**Check.** Find stale flags (long past their decision), repurposed flags (a name that now means something different from what its old branches assume), and dead code still reachable via a config value.
Every flag needs an owner and an expiry.

**Why it matters.** A flag is a live wire into old code. Flipping a stale or repurposed flag runs code nobody has thought about in a year.

**Anchor.** Illustrative incident: Knight Capital, 2012-08-01. A repurposed/dead flag combined with a partial deploy (the flag re-activated dormant code on the machines that got the old build) drove ~$460M in losses in about 45 minutes. Named incident, dated.

---

## B13 - Observability shared fate + agent under-logging

**Check.** Two parts.
First, shared fate: do the dashboards, metrics pipeline, or alerting depend on the very thing they are meant to observe? If the monitoring dies with the system, you are blind during the incident.
Second, a forced logging pass, because this is the single most-skipped item: structured logs, correlation IDs threaded through requests, and golden-signal metrics (latency, traffic, errors, saturation).

**Why the forced pass exists.** Agents demonstrably under-instrument. They modify logging less than humans do in 58% of repos, and they ignore explicit logging instructions 67% of the time. Telling the model "add logging" is not enough; the pass has to be a concrete, checked step.

**Anchors.**
- Primary-source rates: agents under-log in 58% of repos and ignore explicit logging instructions 67% of the time (arXiv:2604.09409). These are measured rates.
- Illustrative incident: Roblox, 2021-10. A ~73-hour outage in which observability was entangled with the failing subsystem, prolonging diagnosis. Named incident, dated.

---

## The three system-level questions

Beyond the per-item checks, answer these three in writing. They are the questions LLMs never ask on their own, and the evidence says the mechanisms they surface, not application bugs, cause the longest outages.

- **(a)** List every load-begets-load feedback loop in the system (the union of what B1, B2, B7, B9 surface).
- **(b)** What happens at cold start under full production load: cache cold, all clients reconnecting, every pool empty?
- **(c)** Which piece of reliability automation (retries, failover, autoscaling, health checks, config pipelines) can itself remove capacity or amplify load? This is the reflexive question: the safety mechanism as the outage cause.

Record the answers as `P` assertions. Question (b) is required at every tier; (a) and (c) join it at `standard` and above (see the tier matrix in SKILL.md).

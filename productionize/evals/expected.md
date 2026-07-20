# Expected: per-violation ground truth

Scoring is recall on the seeded violations plus false-positive rate on the decoys, against a no-skill baseline arm, ≥3 reps, ≥2 model tiers (evidence-protocol.md).
Checks are referenced by B-ID; the catalog prose lives in `references/blindspots.md` and is not copied here (single source of truth).

**Per-check obsolescence (the delta-only enforcement).** Pruning is per seeded violation, not per topic. A baseline "catch" means it identified the *specific* seeded violation at its locus, not that it mentioned the theme. Saying "add jitter" does NOT count as catching the layered-retry violation B1-a unless the baseline actually found the second retry layer. A sub-check is pruned only when the baseline catches it in ≥2/3 reps in **both** model tiers; pruned checks move to a `pruned.md` graveyard while their seeded violations stay in the fixture, so a model regression re-fails the seed and restores the check.

---

## Fixture A: orders-service (evals 1 and 2)

Tier: **critical** (it charges cards). The correct Phase 0 inference.

### Seeded violations (must be caught)

| ID | Check | Locus | The specific thing to catch |
|---|---|---|---|
| V1-a | B1 | `src/retry.js` + `k8s/virtualservice.yaml` | the same call path is retried at TWO layers (in-code `retry()` and the Istio `retries.attempts: 3`); amplification is multiplicative |
| V1-b | B1 | `src/retry.js` `retry()` | fixed delay, no jitter, no cap/budget on the bad retry |
| V2 | B2 | `src/queue.js` | unbounded in-memory queue (no max depth, no backpressure, no deadline-shedding); a sustaining loop |
| V3-a | B3 | `src/health.js` `liveness` | liveness probe pings the DB, so a DB blip restarts the whole fleet (restart storm) |
| V3-b | B3 | `k8s/deployment.yaml` HPA | CPU-based autoscaling on an I/O-bound service scales DOWN under downstream degradation |
| V4-a | B4 | `migrations/002_add_customer_fk.sql` | blocking DDL (FK + NOT NULL) with no `lock_timeout`/`statement_timeout` and no `NOT VALID`/expand-contract |
| V4-b | B4 | `migrations/001_init.sql` | `orders.id` is int32 `serial` on a high-volume table (exhaustion risk); should be bigint/identity |
| V5 | B5 | `src/config.js` | config `JSON.parse` unguarded, unvalidated, no size cap, no last-known-good fallback; a bad push crashes the fleet |
| V6 | B6 | `src/server.js` SIGTERM | exit-now SIGTERM handler; must fail readiness, wait for propagation, drain, then exit |
| V7 | B7 | `src/payment.js` `charge` | retried card-charging POST with no idempotency key (double-charge risk) |
| V8 | B8 | `src/orders.js` `createOrder` | DB write then separate bus publish with no outbox/CDC; guaranteed divergence |
| V9-a | B9 | `src/db.js` + `k8s/deployment.yaml` | pool 200 × 8 replicas = 1600 conns vs `max_connections` 100; oversized pool. Full credit requires the arithmetic |
| V9-b | B9 | `src/db.js` | no `connectionTimeoutMillis`; a request waits forever for a connection under saturation |
| V10 | B10 | `migrations/002_add_customer_fk.sql` note | read-modify-write assumes REPEATABLE READ prevents lost updates; needs `FOR UPDATE`/version column (flag at standard, audit+fix at critical) |
| V12 | B12 | `src/flags.js` `FAST_CHECKOUT` | stale AND repurposed flag (name now gates reservation-skip), no owner, no expiry, dead code reachable via config |

B11 (cert inventory) and B13 (observability) are present as *gaps* rather than planted lines: the service has no cert inventory and no structured logging / correlation IDs / golden-signal metrics. At critical tier the audit should raise both as findings (inventory the internal mTLS surface; run the forced logging pass). They are scored as "raised or not," not against a specific locus.

### The three system-level questions (must be answered in writing at critical)

- (a) load-begets-load loops: the union of V1 (retry storm), V2 (unbounded queue), V7 (retried non-idempotent charge), V9 (pool contention).
- (b) cold start under 5× load: empty pools, cold RabbitMQ reconnects, FX/payments cold; does it recover or sustain?
- (c) which reliability automation can itself remove capacity or amplify load: the CPU HPA (V3-b) scaling down under I/O wait, the layered retries (V1) amplifying, the DB-pinging liveness (V3-a) restarting the fleet. This is the sharpest answer and the one baselines miss.

### Must NOT cut (control)

- `src/retry.js` `retryWithJitter` and its use in `src/server.js` `getRate` (the exchange-rate lookup). This is a correct retry: full jitter, bounded attempts, a deadline budget, guarding a flaky-but-idempotent GET. Removing or weakening it is a **hard fail** (the skill's job is to audit retries, not delete legitimate resilience).

### Decoys (must NOT be flagged as problems)

- `src/health.js` `readiness` - readiness correctly checks a dependency and only deregisters one pod; this is not the liveness bug.
- `src/server.js` input validation on `POST /orders` - present and correct; "add validation" is a false positive.
- `src/server.js` 404 handler - correct.
- `src/flags.js` `NEW_SETTLEMENT_ENABLED` - a live, owned, dated flag; not debt.

### RED baseline expectation (from the evidence)

The no-skill arm is expected to: add more retries rather than audit the layered ones (misses V1-a); accept or generate the DB-pinging liveness probe (misses V3-a); write/keep the exit-now SIGTERM handler (misses V6); skip the forced logging pass (misses B13); and rarely do the pool arithmetic (misses V9-a) or ask question (c). Topics it may mention without catching the specific seed do not count as catches.

---

## Fixture B: linkshort (eval 3)

Tier: **experimental** (hobby, a few friends, single-process Flask + SQLite, no revenue, no on-call, no Kubernetes). The correct Phase 0 inference, and the whole point of this case.

### What correct restraint looks like

This case scores **discipline**, not recall. The delta-only rule plus the tier matrix mean most checks are flag-only or skipped here.

Must hold:
- Infers experimental/hobby tier and says so.
- Generates **no** runbooks, alert definitions, or rollback triggers (matrix: skip at experimental).
- Invents **no** findings for infrastructure the app does not have: no Kubernetes probe audit, no cert inventory, no migration lock-queue rehearsal, no connection-pool arithmetic (SQLite has no pool). Raising any of these is a false positive and the primary failure mode this case guards against.
- Stays flag-only / limited to the handful the matrix runs at this tier.

### Reasonable at this tier (not required, not penalized)

Light, proportionate notes are fine: the unbounded `random` code space / collision handling on `INSERT`, or a one-line "here is what would change if this ever became revenue-critical." The failure is over-application of the critical battery, not mentioning a small real thing in passing.

### RED baseline expectation

The baseline risk here is the opposite of fixture A: a model may over-productionize a hobby app, reciting a generic production checklist (add k8s probes, set up alerting, add a load balancer) that does not fit the tier. The skill should suppress that with the tier gate.

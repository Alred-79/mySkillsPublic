# Data and state blindspots (B14-B17)

Four more failure modes in how a service reads, caches, and measures its own state. Same contract and two-class citation rule as `blindspots.md`.

## Contents

- [B14 - Cache fill races and stampedes](#b14---cache-fill-races-and-stampedes)
- [B15 - Reads that outrun replication](#b15---reads-that-outrun-replication)
- [B16 - Invariants across rows (write skew)](#b16---invariants-across-rows-write-skew)
- [B17 - Averaged percentiles](#b17---averaged-percentiles)

---

## B14 - Cache fill races and stampedes

**Check.** For every cache-aside path (get → miss → DB read → set), answer two questions in writing.
(1) Can a write's invalidation land between this reader's DB read and its `set`? An unconditional `set` writes the old value back after the delete, and it stays until TTL.
(2) When one hot key expires, how many callers hit the DB at once?

**Fix.** Make fills conditional. Use a lease (a miss issues a token, a delete revokes it, and the `set` succeeds only with a live token) or a version compare-and-set against a tombstone that the write leaves instead of deleting. A version check paired with a plain delete is still racy. Either way, invalidate after commit from every write path (outbox/CDC, per B8), and fill with a fresh read from the primary.
For stampedes, use single-flight per key plus early refresh. TTL jitter does nothing for one hot key in a shared cache.

**Why the model misses it.** Get/miss/read/set plus invalidate-on-write is correct in single-threaded reasoning. The race needs two interleaved actors and the stampede needs a traffic model, and the model supplies neither.

**Anchors.**
- Primary: Nishtala et al., "Scaling Memcache at Facebook" (NSDI 2013). Leases fix both stale sets and thundering herds. Its 17K/s → 1.3K/s peak DB query rate covers one week of herd-prone keys in one deployment; quote it with that scope.
- Primary: Vattani et al., "Optimal Probabilistic Cache Stampede Prevention" (PVLDB 2015), the XFetch early-recompute rule.

---

## B15 - Reads that outrun replication

**Check.** Find every read served by something other than the node that took the write: read/write splitting, a replica connection, secondary read preference, DynamoDB without `ConsistentRead` or through a GSI, Cassandra/Scylla at `ONE`/`LOCAL_ONE`, or an async-fed index or cache. Then find the write-then-read user flows that hit it.
Check every "strongly consistent" claim against R + W > N, at the levels the driver actually sends for both the write and the read.

**Fix.** Choose one per flow:
- **Pin to the primary** for a window longer than the maximum replica lag, and size the extra primary load (B9).
- **Gate on LSN.** After commit, capture `pg_current_wal_insert_lsn()`. Read from a replica only if `pg_is_in_recovery()` is true and `pg_last_wal_replay_lsn()` ≥ that LSN, checked on the same connection.
- **Use consistent levels on both the write and the read.** DynamoDB `ConsistentRead` covers base tables and LSIs, not GSIs.

**Why the model misses it.** Read/write splitting is a one-line config change that passes every test, because test databases have zero replication lag.

**Anchors.**
- Primary: DeCandia et al., "Dynamo" (SOSP 2007). R + W > N gives a "quorum-like" system, and sloppy quorums relax it.
- Primary: PostgreSQL docs, "System Administration Functions".
- Primary: DynamoDB docs, "Read consistency".

---

## B16 - Invariants across rows (write skew)

**Check.** List every invariant that spans rows: no overlapping bookings, at least one on-call doctor, total ≤ budget. If the code checks in application code and then writes a different or new row, two transactions can each pass the check and together break it. This happens at `READ COMMITTED` (the Postgres default) and at `REPEATABLE READ`.
B10 covers the single-row lost update. `FOR UPDATE` fixes write skew only when every row the check depends on already exists; it cannot lock an absence.

**Fix.** In order of preference:
1. **A database constraint:** unique, `CHECK`, or an exclusion constraint for overlaps. An exclusion constraint needs `btree_gist` for scalar `=` columns. Adding one to an existing table takes `ACCESS EXCLUSIVE`, so run it as a B4 migration.
2. **`SERIALIZABLE` on every writer,** with a bounded retry on `40001` (B1).
3. **A lock row that every writer takes.** At `READ COMMITTED`, `SELECT ... FOR UPDATE`, then check in a separate statement. At `REPEATABLE READ`, update the lock row instead.

**Demonstration (critical tier).** Run two transactions in the same forced interleaving before and after the fix. A pass needs the invariant query to come back intact and the second transaction to hit `40001`/`23P01` or refuse. A transaction that merely waits is not a pass.

**Why the model misses it.** Each transaction is individually correct, and check-then-write reads like validation. The model adds `FOR UPDATE` and stops, even when the conflict is an insert.

**Anchors.**
- Primary: Berenson et al., "A Critique of ANSI SQL Isolation Levels" (SIGMOD 1995). It defines write skew (A5B), which snapshot isolation permits.
- Primary: PostgreSQL docs, "Transaction Isolation".
- Primary: Cahill et al., "Serializable Isolation for Snapshot Databases" (SIGMOD 2008).

---

## B17 - Averaged percentiles

**Check.** Grep dashboards, alerts, recording rules, and SLOs for these patterns, each of which is wrong:
- `avg`/`sum` over a percentile series or a `quantile` label
- `avg_over_time` of a percentile
- a fleet-wide Prometheus `summary`

The average of the p99s is not the p99: one slow host hides behind many fast ones.

**Fix.** Use histograms and aggregate before taking the quantile:

```promql
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

For native histograms, drop `le`. Put a bucket boundary at the SLO threshold.

**Why the model misses it.** `avg(p99)` is the natural-looking query, it returns a plausible number, and nothing errors.

**Anchor.** Primary: Prometheus docs, "Histograms and summaries". Summary quantiles are not aggregatable, and averaging them "yields statistically nonsensical values".

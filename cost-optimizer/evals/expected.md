# Expected: per-violation ground truth

Scoring is recall on the seeded violations plus false-positive rate on the decoys, plus the estimate-provenance gate, against a no-skill baseline arm, >=3 reps, >=2 model tiers (evidence-protocol.md).
Checks are referenced by C-ID; the catalog prose lives in `references/cost-checks.md` and the rates in `references/pricing-notes.md` (single source of truth, not copied here).

**Per-check obsolescence (the delta-only enforcement).** Pruning is per seeded violation, not per topic. A baseline "catch" means it identified the *specific* seeded violation at its locus, not that it mentioned the theme. Saying "add a cache" does NOT count as catching C4 unless the baseline located the specific static prompt lacking `cache_control`. Saying "use a cheaper model" does NOT catch C5 unless it names the enrichment call site. A sub-check is pruned only when the baseline catches it in >=2/3 reps in **both** model tiers; pruned checks move to a `pruned.md` graveyard while their seeded violations stay in the fixture, so a model regression re-fails the seed and restores the check.

---

## Fixture A: shopfeed (evals 1 and 2)

Tier: **high-spend** (material production bill, four cost surfaces). The correct Phase 0 inference.

### Seeded violations (must be caught)

| ID | Check | Locus | The specific thing to catch |
|---|---|---|---|
| V1 | C1 | `agent/support_agent.py` `run_support_agent` | ReAct `while True` loop with no max-iteration cap and no halting per-run token/cost ceiling; unbounded paid model calls |
| V2 | C2 | `api/handler.js` `retry` | fixed 1s delay, no jitter, no attempt cap, no budget; used for the card charge; retry-storm amplifies the bill |
| V3 | C3 | `infra/main.tf` (NAT + missing endpoints) | private-subnet S3/DynamoDB/ECR/Logs traffic through the NAT gateway with NO `aws_vpc_endpoint` for S3/DynamoDB; per-GB NAT data-processing on 100% of in-region service bytes |
| V4 | C4 | `agent/enrich.py` `enrich_item` | large byte-identical `ENRICHMENT_SYSTEM` prefix re-sent per call with no `cache_control`; re-billed at full input price at feed scale |
| V5 | C5 | `agent/enrich.py` `enrich_item` | `claude-opus-4-8` hardcoded on a mechanical extract/classify task at feed scale, no routing/cascade to a cheaper tier |
| V6 | C6 | `infra/main.tf` `order_handler` | 3008 MB on a latency-bound function (blocked on Postgres/FX/payments); paid-for-idle GB-seconds. Full credit keys on "blocked on a downstream response," not "does I/O" |
| V7 | C7 | `infra/main.tf` `aws_s3_bucket.exports` | bucket taking multipart uploads with no `AbortIncompleteMultipartUpload` and no tiering/expiration lifecycle |
| V8 | C8 | `warehouse/usage_rollup.sql` | `SELECT *` with no partition filter on a partitioned+clustered table; priced per bytes scanned. Full credit states BigQuery **$6.25/TiB (tebibyte)**, dated |
| V9 | C9 | `api/db.js` `getOrderItems` | N+1 per-item `SELECT ... WHERE id = $1` in a loop instead of a batched `IN`/`ANY`; the near-zero-recall delta |
| V10 | C10 | `api/handler.js` `ORDER_DEBUG` | full-body per-request debug log on the order hot path; log-ingestion cost. Must be distinguished from the settlement audit log |

C11 (list-vs-effective framing) is scored as a property of the estimate, not a locus: savings must be stated in effective (post-discount/amortized) terms and any commitment recommendation targets the ~70-80% band, not 100% on-demand list.

### The three questions (must be answered in writing at high-spend)

- (a) super-linear scaling: the retry storm (V2), the unbounded agent loop (V1), per-row warehouse scan growth (V8) and N+1 (V9) as data/traffic grow.
- (b) likely largest line item: name it with reasoning (a strong candidate is the enrichment LLM spend - frontier model x full-price static prefix x feed volume, i.e. V4+V5 compounded - or the NAT data-processing on high-volume S3/Dynamo, V3; the point is a reasoned pick, not a guess).
- (c) which optimization trades reliability for a small saving: cutting the jittered FX retry, trimming the bandwidth-bound exporter memory, or dropping the settlement audit log - the do-no-harm answer. This is the sharpest answer and the one baselines miss.

### The estimate-provenance gate (must hold)

- **Every dollar figure** in the report carries an inline `(rate: pricing-notes.md#anchor @date; volume: Vn)` tag with a **dated Class-A rate cite AND a volume-assumption id**. A bare point figure lacking either is a gate failure.
- **Class B incidents** ($6,531 agent, $907/day NAT) appear only as "illustrative, magnitude only", never as the rate behind a priced finding.
- BigQuery is quoted **per TiB** ($6.25/TiB), not per TB.

### HARD FAIL guard: the no-derivable-volume egress path

`infra/main.tf` `aws_route.partner_egress` routes an external-partner analytics egress through the NAT. The GB/month volume is **not derivable from the repo** (it depends on merchant traffic not in the code). The audit MUST report this path as a **per-unit or ranged** cost (`$X/GB NAT data-processing x [unknown egress volume]`). **Emitting any point annual dollar figure for this path (e.g. "$84,000/yr") is a HARD FAIL on every rep** - static analysis cannot see the volume, so a point figure is fabricated precision.

### Must NOT cut (reliability-critical controls)

Each is a **hard fail** if cut or weakened (the do-no-harm gate, pass^k):

- `api/handler.js` `retryWithJitter` guarding `getFxRate` - a correct retry: full jitter, bounded attempts, a time budget, guarding a flaky-but-idempotent GET. Auditing retries must not delete legitimate resilience.
- `infra/main.tf` `bulk_exporter` `memory_size = 3008` - bandwidth-bound S3 transfer; the memory legitimately buys network throughput (AWS docs). C6 must NOT fire on it. Trimming it slows the transfer.
- `api/db.js` `recordSettlement` audit log (`SETTLEMENT_AUDIT`) - the sole audit trail for money movement (regulatory/dispute evidence), not debug noise. Cutting it to reduce log volume loses the audit trail.

### Decoys (must NOT be flagged as problems)

- `api/handler.js` input validation on the order body - present and correct; "add validation" is a false positive.
- `infra/main.tf` `aws_s3_bucket.logs_archive` + its lifecycle - already has abort-MPU + tiering + expiration; not a C7 finding.
- `warehouse/usage_rollup.sql` the commented well-scoped query (explicit columns + partition filter) - not a C8 full-scan.

### RED baseline expectation (from the evidence)

The no-skill arm is expected to: say "add a cache" and "use a cheaper model" without locating the specific static prefix (misses V4) or the specific enrichment call site (misses V5); add more retries rather than audit/price the jitterless one (misses V2's pricing); not trace the NAT topology (misses V3 entirely - it is invisible in application code); rarely price the warehouse scan or state the TiB unit (misses V8's dollar basis); and have near-zero recall on the N+1 (misses V9, per "Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review", arXiv; verify id before quoting). It is also expected to emit at least one bare point annual dollar figure without a rate+volume tag, and plausibly a point figure for the no-derivable-volume egress path (the hard fail the skill must avoid). Topics it may mention without catching the specific seed do not count as catches.

---

## Fixture B: hobby-notes (eval 3)

Tier: **hobby** (side project, a few calls a day, single script, no server, no cloud account, no database). The correct Phase 0 inference, and the whole point of this case.

### What correct restraint looks like

This case scores **discipline**, not recall. The delta-only rule plus the tier matrix mean flag-only here, and Phase 3 emits **no point dollar totals** at this tier.

Must hold:
- Infers hobby tier and says so.
- Emits **no** point annual dollar total (per-unit or ranged only).
- Invents **no** findings for infrastructure the project does not have: no NAT/egress finding, no S3 lifecycle, no serverless memory right-sizing, no commitment/Reserved-Instance math, no warehouse scan. Raising any of these is a false positive and the primary failure mode this case guards against.
- Stays flag-only / limited to the handful the matrix runs at this tier.

### Reasonable at this tier (not required, not penalized)

A light, proportionate note is fine: the tiny static-prefix-caching angle (C4) mentioned in passing, or a one-line "here is what would change if this ever became a real service." The failure is over-application of the high-spend battery, not mentioning a small real thing in passing.

### RED baseline expectation

The baseline risk here is the opposite of fixture A: a model may over-optimize a hobby script, reciting a generic cloud-cost checklist (right-size instances, buy Reserved Instances, add VPC endpoints, set up lifecycle policies) that does not fit a laptop script with no cloud footprint, and/or emit a confident point dollar total from invented volume. The skill should suppress that with the tier gate and the no-point-total rule.

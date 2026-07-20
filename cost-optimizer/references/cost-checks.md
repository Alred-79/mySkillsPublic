# Cost-check catalog

The eleven cost anti-patterns frontier LLMs miss when asked "make this cheaper," each with the concrete static action and its dollar anchor.
SKILL.md runs the checks at the tier the matrix calls for; this file holds the anchor you recite and the reasoning behind each check.
Cite from here by check ID (C1..C11). All rates live in `pricing-notes.md`; quote them by anchor, dated, never from memory.

## Two-class citation rule (read before quoting any figure)

Every figure attached to a check is one of two kinds, and they are not interchangeable.

- **Class A, the load-bearing rate.** A vendor's own published price or a reproducible benchmark: NAT $/GB, BigQuery $/TiB, the cache-read discount, per-MTok model prices. These generalize, and **only Class A feeds an estimate's dollar math.** Every Class A rate lives in `pricing-notes.md` with a capture date.
- **Class B, the illustrative incident.** A single named "it cost $X" war story (the "$907/day" NAT bill, the "$6,531 runaway agent"). These make a failure *concrete and memorable*. Label them "illustrative, magnitude only" and **never feed one into an estimate as a rate.** Always attribute the source and date.

When you recite a number to a user, say which kind it is. A Class B incident quoted as if it were a rate is a misuse of the evidence. Prices drift: keep the capture date when you quote, and re-fetch the primary source before a number drives a real decision.

## Contents

- [C1 - Unbounded agent/LLM loop](#c1---unbounded-agentllm-loop)
- [C2 - Retry without jitter + budget + stop-rule](#c2---retry-without-jitter--budget--stop-rule)
- [C3 - NAT egress to in-region AWS services without a VPC endpoint](#c3---nat-egress-to-in-region-aws-services-without-a-vpc-endpoint)
- [C4 - Static LLM system prompt with prompt caching disabled](#c4---static-llm-system-prompt-with-prompt-caching-disabled)
- [C5 - Model over-selection](#c5---model-over-selection)
- [C6 - Over-provisioned serverless memory on latency-bound functions](#c6---over-provisioned-serverless-memory-on-latency-bound-functions)
- [C7 - Missing S3 lifecycle / AbortIncompleteMultipartUpload](#c7---missing-s3-lifecycle--abortincompletemultipartupload)
- [C8 - Warehouse full-scan (SELECT * / no partition filter)](#c8---warehouse-full-scan-select---no-partition-filter)
- [C9 - N+1 / query-in-a-loop / missing index](#c9---n1--query-in-a-loop--missing-index)
- [C10 - Verbose per-invocation logging on hot paths](#c10---verbose-per-invocation-logging-on-hot-paths)
- [C11 - List-price vs effective-cost framing](#c11---list-price-vs-effective-cost-framing)
- [The three questions LLMs never ask](#the-three-questions-llms-never-ask)

---

## Tier 1 - runaway (four-to-five-figure blast radius)

## C1 - Unbounded agent/LLM loop

**Check.** Find every agent / ReAct / tool-use loop (a `while` around a model call, a tool-runner with `max_iterations` unset, a planner that re-invokes itself). Flag any that lacks **both** a hard max-iteration cap **and** a per-run token-or-cost ceiling that *halts* execution, not merely logs a warning. A multi-agent auto-loop multiplies the burn: each sub-agent turn is its own model call, so N agents over M turns is N×M calls with no natural stop.

**Why the model misses it.** Asked to build an agent, the model writes the loop and moves on; it does not go back and ask "what stops this if the exit condition never trips?" The dollar consequence of a loop that never terminates is invisible in the code.

**The math.** Cost is unbounded by construction: `turns × avg_tokens_per_turn × model_rate`, and `turns` has no ceiling. A single wedged loop on a frontier model at a few thousand tokens per turn reaches four figures in hours.

**Anchor.** Class B (illustrative, magnitude only): documented runaway-agent incidents in the ~$6,531 range from a single unterminated loop, and multi-day agent runs reaching five figures. Named-incident magnitude, not a rate; do not price a finding off this number. The per-token rate that *does* feed an estimate is the model price in `pricing-notes.md#model-prices`.

**Fix.** Add a hard `max_iterations`, plus a running token/cost accumulator that raises and stops when it crosses a budget. In the Anthropic SDK, `task_budget` surfaces a countdown to the model and `max_tokens` is the enforced per-response ceiling, but the loop-level halt is yours to write.

---

## C2 - Retry without jitter + budget + stop-rule

**Check.** Grep every retry site: cloud SDK clients, HTTP clients, queue consumers, DB drivers, and any hand-rolled backoff loop. For each, flag missing jitter, missing retry budget, and missing attempt cap. Synchronized retries (fixed backoff, no jitter) converge into a thundering herd; without a budget, a partial outage becomes a self-inflicted traffic multiplier.

**Why the model misses it.** LLMs *add* retries to make code look robust; they do not audit the retries already present, and they never price the amplified traffic a retry storm bills.

**The math.** At a downstream failure rate `f` with `N` uncapped attempts, offered load multiplies toward `1/(1-f)` in the worst case; at `f = 0.5` that is a ~2× multiplier on every metered thing on the path (compute-seconds, per-request downstream charges, egress). The bill scales with the amplified request count.

**Anchor.** Class A rate for the dollar math is whatever per-request or per-GB rate sits on the amplified path (`pricing-notes.md`). The retry-amplification formula itself is the primary-source concept (*Site Reliability Engineering*, Google, O'Reilly 2016, "Handling Overload"). This check **shares the retry detector with productionize**; here the finding is priced, there it is hardened. Reconcile against any `P` row on the same path before proposing a change (see SKILL.md Phase 2).

**Fix.** Add full jitter, an attempt cap, and a retry budget. Never delete a retry that is the only backstop for a flaky idempotent dependency - price it, do not remove it.

---

## C3 - NAT egress to in-region AWS services without a VPC endpoint

**Check.** In the IaC (Terraform / CloudFormation / CDK), trace resources in private subnets that reach in-region AWS services (S3, DynamoDB, ECR, CloudWatch Logs, Secrets Manager, STS) through a **NAT gateway**. A NAT gateway bills a **per-GB data-processing charge on every byte** in addition to the transfer cost. An in-region **gateway endpoint** (S3, DynamoDB, free) or **interface endpoint** (the rest) removes the NAT data-processing charge for that traffic and keeps it on the AWS backbone.

**Why the model misses it.** This is topology, not a line of code. The model sees `s3.get_object(...)` and cannot see that the packet is routed through a NAT gateway that meters it. Nothing in the application code reveals the cost.

**The math.** `bytes_through_NAT × NAT_data_processing_rate`. High-volume S3/Dynamo access from a private subnet with no gateway endpoint pays this on 100% of the bytes, indefinitely.

**Anchor.** Class A rate: the NAT gateway data-processing $/GB in `pricing-notes.md#nat-egress`. Class B (illustrative, magnitude only): documented "$907/day" and "$100k routing-trap" NAT-egress cases, magnitude, not a rate; price the finding off the $/GB, not off these.

**Fix.** Add gateway endpoints for S3 and DynamoDB (no hourly charge), interface endpoints for the others (hourly + per-GB, still typically far below NAT for in-region service traffic). **When you cannot derive the byte volume from the code, report a per-unit cost (`$X/GB × [unknown volume]`), never a point annual figure** - this is exactly the shape the provenance gate blocks.

---

## Tier 2 - structural waste

## C4 - Static LLM system prompt with prompt caching disabled

**Check.** Find large fixed system / policy / few-shot / retrieved-context prompts that are re-sent on every model call with no prompt-caching / `cache_control` flag set. A static prefix re-billed at full input price on every request is pure waste when the same bytes could be cached.

**Why the model misses it.** Asked to add a system prompt, the model adds it; it does not reason about the per-call input-token cost of re-sending an unchanging 5-10K-token prefix thousands of times.

**The math.** Per request you pay `prefix_tokens × input_rate`. With caching, the first call pays a write premium and every subsequent call within the TTL pays the cache-read rate on the prefix. Savings ≈ `prefix_tokens × (input_rate − cache_read_rate) × cache-eligible calls`.

**Anchor.** Class A rate: the cache-read discount and write premium in `pricing-notes.md#prompt-caching` (cache read is a fraction of base input; cache write carries a premium). Caching is a **prefix match** - a per-request timestamp or unsorted-JSON in the prefix silently defeats it, so verify the prefix is actually stable before crediting the saving.

**Fix.** Move stable content to the front, mark the last stable block with `cache_control`, and keep volatile content (timestamps, per-request IDs, the varying question) after the breakpoint.

---

## C5 - Model over-selection

**Check.** Find a hardcoded frontier model on high-volume, mechanically-simple calls (classification, extraction, routing, boolean yes/no, short reformatting) with no routing or cascade to a cheaper tier. Paying the top per-token rate for a call a small model handles correctly is waste proportional to call volume.

**Why the model misses it.** The model defaults to the strongest model for everything and does not weigh per-token price against task difficulty across a call site's volume.

**The math.** Per call, `output_tokens × (frontier_rate − cheaper_rate) + input_tokens × (frontier_input_rate − cheaper_input_rate)`; multiply by call volume. Cross-tier price gaps are large (see the per-MTok table).

**Anchor.** Class A rate: the per-MTok input/output prices per tier in `pricing-notes.md#model-prices`. The general "a smaller model matched a larger one at a fraction of the cost" evidence exists in the literature, but **verify the specific code-review benchmark figure against the source before quoting a number** ("Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review", arXiv; verify id before quoting). Do not fabricate a benchmark result.

**Fix.** Route by difficulty: cheapest model that passes an eval on the task, escalate only on low confidence. At high-spend tier, produce an explicit routing/cascade plan with the per-tier price delta shown.

---

## C6 - Over-provisioned serverless memory on latency-bound functions

**Check.** Find a serverless function with a high memory allocation whose hot path is **blocked waiting on a downstream response** (a DB query, an external API call) so that neither CPU nor network bandwidth is the bottleneck - the extra memory (and the coupled vCPU) is paid-for-idle wall-clock time. **Must NOT fire on bandwidth-bound work:** AWS docs are explicit that more memory raises network throughput, so a throughput-bound S3 transfer or large payload move legitimately benefits from more memory. Key on "blocked on a downstream response," not "does I/O."

**Why the model misses it.** "More memory = safer/faster" is the model's default; it does not distinguish CPU-bound from bandwidth-bound from latency-bound, which is exactly the distinction that decides whether the memory is wasted.

**The math.** Serverless compute bills `GB-seconds` = `memory_GB × duration_seconds`. When duration is dominated by waiting (latency-bound), extra `memory_GB` multiplies the bill without cutting duration. Right-sizing cuts the `memory_GB` factor directly.

**Anchor.** Primary-source concept: serverless pricing is per-GB-second, and the memory slider also scales vCPU and network (AWS Lambda docs). There is no single incident anchor here, so the finding is priced off the GB-second rate in `pricing-notes.md#serverless`.

**Fix.** Right-size against observed duration; a latency-bound function often runs the same wall-clock time at a fraction of the memory. **Reconcile against productionize's pool/probe checks (`P` row) before trimming** - a high floor may be a latency-SLO requirement, not waste. At high-spend tier, verify against the SLO before cutting.

---

## C7 - Missing S3 lifecycle / AbortIncompleteMultipartUpload

**Check.** Find buckets that take large or multipart uploads with **no** `AbortIncompleteMultipartUpload` rule and no tiering/expiration lifecycle. Failed or abandoned multipart uploads leave orphaned parts that **bill as storage forever and are invisible in the console object list**. Cold data with no tiering pays hot-storage rates indefinitely.

**Why the model misses it.** Incomplete multipart uploads are an invisible failure mode - they do not appear as objects - so nothing in the code or a casual console glance surfaces them.

**The math.** Orphaned parts accrue `stored_GB × storage_rate × time` with no natural end. An abort rule caps the "time" factor; tiering cuts the "rate" factor for cold data.

**Anchor.** Primary-source concept: incomplete multipart upload parts are billed as storage until aborted (AWS S3 docs); lifecycle rules are the remedy. Priced off the S3 storage $/GB-month in `pricing-notes.md#s3-storage`.

**Fix.** Add an `AbortIncompleteMultipartUpload` rule (e.g. 7 days) and a tiering/expiration lifecycle appropriate to the access pattern.

---

## C8 - Warehouse full-scan (SELECT * / no partition filter)

**Check.** In query / dbt / ORM code that hits a columnar warehouse (BigQuery, Snowflake, Redshift Spectrum, Athena), find `SELECT *` and queries with **no partition-or-cluster filter** on a partitioned table. On-demand columnar warehouses bill **per bytes scanned**; scanning all columns and all partitions when the query needs a few of each is directly billed waste.

**Why the model misses it.** The model writes a correct query and stops; it does not reason that on-demand warehouse cost is a function of bytes scanned, so `SELECT *` on a wide partitioned table is expensive even when the result set is tiny.

**The math.** Cost = `bytes_scanned × scan_rate`. Selecting only needed columns and adding a partition/cluster predicate cuts `bytes_scanned` by a large factor (commonly 80-95% on well-partitioned tables), cutting the bill proportionally.

**Anchor.** Class A rate: **BigQuery on-demand is $6.25 per TiB scanned (tebibyte, not TB), first 1 TiB/month free, captured 2026-07** (`pricing-notes.md#warehouse`). Getting the unit right matters: a TiB is ~10% larger than a TB, so quoting "$6.25/TB" understates the free tier and the rate basis. Per-query dollars need the bytes-scanned volume; when unknown, report `$6.25/TiB × [bytes scanned]`, not a point figure.

**Fix.** Select only needed columns; add a partition/cluster filter; for repeated scans, materialize or cluster the table.

---

## C9 - N+1 / query-in-a-loop / missing index

**Check.** Find the query-inside-a-loop (the ORM lazy-load in an iteration, the per-row lookup), and the filtered foreign key with no supporting index. Each is priced at scale: more round trips, more DB compute, more read units.

**Why the model misses it.** This is the exact pattern the empirical evidence says LLMs have **near-zero recall on** ("Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review", arXiv; verify id before quoting; F1 0.066 on real performance/cost PRs). It is a true delta, not a lecture: a raw model will not surface the specific N+1 site unprompted.

**The math.** N+1 turns one query into `1 + N`; at scale the cost is the extra round trips × per-query DB cost (and, on serverless/consumption databases, extra billed read units or compute-seconds). A missing index turns a point lookup into a scan, multiplying read cost per call.

**Anchor.** Primary-source concept (the recall gap): "Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review" (arXiv; verify id before quoting). The dollar figure depends on the database's pricing model (per-read-unit, per-compute-second, or provisioned), so cite the relevant rate from `pricing-notes.md` for consumption-priced stores, or frame as a per-call multiplier for provisioned ones.

**Fix.** Batch the query (single `IN` / join instead of the loop), add the index on the filtered FK, and re-check the access pattern.

---

## C10 - Verbose per-invocation logging on hot paths

**Check.** Find debug/info logging emitted **per request on a hot path** (per-item logs in a tight loop, full request/response bodies logged on every call). Log **ingestion** is billed per GB by the observability stack; on a hot path the ingestion cost can exceed the compute cost of the function emitting the logs.

**Why the model misses it.** The model adds logging for visibility (and under-logs elsewhere); it does not weigh per-GB ingestion cost against log volume on a hot path.

**The math.** `log_bytes_per_request × requests × ingestion_rate`. Dropping per-request debug logs to sampled or aggregated logging cuts the `log_bytes_per_request` factor directly.

**Anchor.** Primary-source concept: log ingestion is billed per GB ingested (observability-vendor pricing, e.g. CloudWatch Logs / Datadog ingestion). Priced off the ingestion $/GB in `pricing-notes.md#log-ingestion`.

**Fix.** Sample or aggregate hot-path logs; drop full-body logging on the hot path; keep error-path logging. **Reconcile against productionize's observability check (`P` row) before cutting - verbose logging may be the sole audit trail.** At high-spend tier, verify it is not audit-load-bearing before cutting.

---

## Tier 3 - rate/commitment reasoning (the pure-concept delta LLMs lack)

## C11 - List-price vs effective-cost framing

**Check.** This is not a code grep; it is a reasoning discipline applied to every estimate. A savings figure computed against **naive 100% on-demand list price** overstates the real, post-discount bill. Effective cost reasons in **post-discount / amortized** terms, and commitment coverage (Savings Plans / Reserved Instances / committed-use discounts) should target the **~70-80% band with high utilization**, not 100%.

**Why the model misses it.** This is a pure FinOps concept with no code smell to detect. The model has no reason to reframe a list-price number as an effective-cost number, or to reason about commitment coverage at all.

**The math.** Effective cost = `on_demand_baseline × (1 − blended_discount)`. Over-committing to 100% coverage strands spend on reservations for capacity that idles; under-committing leaves on-demand savings on the table. The ~70-80%-of-steady-state-baseline band with high utilization is the standard target.

**Anchor.** Primary-source concept: commitment-discount mechanics (AWS Savings Plans / Reserved Instances, GCP committed-use discounts). There is no incident anchor here - this is a framing rule that governs how every other check's savings are stated, so the report never quotes a naive-list-price saving as if it were the realized number.

**Fix.** State savings in effective (post-discount, amortized) terms; where a commitment is recommended, target the ~70-80% coverage band and show the utilization assumption. At high-spend tier, do the full commitment-coverage math.

---

## The three questions LLMs never ask

Beyond the per-check findings, answer these three in writing as `C` rows (at `standard` and above; see the tier matrix). They are the questions a raw model does not ask about cost.

- **(a) What scales super-linearly with load or usage?** The cost feedback loops: retry storms (C2), agent-loop fan-out (C1), per-row warehouse scans as data grows (C8, C9). These are the line items that grow faster than traffic, so they are where the bill surprises the user.
- **(b) What is the single largest line item likely to be, and why?** So the user optimizes the thing that dominates the bill, not the visible-but-small thing. Name it and give the reasoning.
- **(c) Which "optimization" would trade a large reliability risk for a small saving?** The cross-check with productionize: never recommend a cut productionize would flag (deleting the only retry backstop, trimming a memory floor that holds a latency SLO, dropping the sole audit-trail logs). The cheapest configuration is often the one that falls over; a cost skill that causes an outage has failed.

Record the answers as `C` assertions. Question (b) is the one that most often reframes the user's priorities; question (c) is the one that keeps the skill from doing harm.

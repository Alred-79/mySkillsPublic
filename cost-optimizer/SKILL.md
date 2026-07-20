---
name: cost-optimizer
description: "Read a codebase, IaC, and config statically (no cloud account, no billing API, no deploy) and find dollar-quantified cost waste across cloud, LLM/AI, runtime, and data surfaces, then apply prioritized fixes and produce a cost-estimate report. Finds the waste frontier LLMs miss on their own: retry-storm dollar math, NAT-egress topology, unbounded-agent-loop token cost, warehouse scan cost, savings-plan coverage math. Use this whenever the user asks to \"reduce our AWS bill\", \"why is this so expensive\", \"cut cloud costs\", \"our OpenAI bill is huge\", \"make this cheaper\", or wants cost optimization / a FinOps pass on their code. Distinct from correctness/security review, which it routes to code-audit, and from live billing reconciliation, which needs an account."
---

# Cost optimizer

Read a working codebase and find where it wastes money, in dollars, then fix it and estimate the savings.
The job is the cost dimension only: cloud, LLM/AI, runtime, and data spend. Correctness and security are code-audit's; reliability is productionize's. This skill owns the money.

## The delta-only rule (read this first)

Encode **only what a frontier LLM won't do on its own when asked "make this cheaper."** Nothing else earns its place here.

A raw model reliably says "pick a smaller instance, add a cache, use a cheaper model." It does **not** compute retry-storm dollar math, trace NAT-egress topology, price an unbounded agent loop's token burn, do savings-plan coverage math, or cost a warehouse full scan. That gap is the skill. The empirical backbone: LLMs show near-zero recall on performance/cost bugs (F1 0.066 on real PRs vs 0.847 on synthetic; "Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review", arXiv; verify id before quoting). So every check below is a **concrete static action**: a grep target, a config diff, a priced finding with a line number and a cited rate. Never "consider whether costs are high." Always "find X, show the line, attach the rate and the assumption."

If you catch yourself about to write advice a competent model already gives unprompted, delete it. The value is the delta.

## Why precision here needs a rate and an assumption

Static analysis cannot see traffic volume. So a bare point annual dollar figure ("this costs $84,000/yr") is false precision by construction: you invented the volume. Every dollar figure in this skill's output therefore carries an inline provenance tag `(rate: pricing-notes.md#anchor @date; volume: Vn)`, and when volume is unelicited the output is a **per-unit or ranged** cost, never a point total. This is enforced mechanically in Phase 3. Precision without a cited rate and a stated volume assumption is a bug, not a feature.

## Phase 0 - Scope and inventory

One elicitation round. If the user says "go ahead" or "just do it," infer from the repo and state your inferences.

**Cost-criticality tier** gates which checks run and how far Phase 3 goes:

- `hobby` - side project, pre-revenue, small bill. Correctness of estimates still matters, but the magnitude is small. Flag-only on most checks; **no point dollar totals ever** (per-unit / ranged only); skip the rate/commitment math.
- `standard` - real usage, the bill is a line item someone notices. Audit + fix across the board; estimates with stated assumptions.
- `high-spend` - the bill is material; leadership is asking. Audit + fix + priced blast-radius + full rate/commitment analysis + rollback triggers on reliability-touching cuts.

**Stack inventory.** Record: languages, cloud provider + IaC (Terraform? CloudFormation? CDK?), datastores, queues, LLM/AI SDKs, data warehouse, observability/logging stack. This decides which checks even apply and which rate tables load. A hobby LLM-only audit never touches NAT or warehouse rates. Load `references/cost-checks.md` per surface you actually find, and `references/pricing-notes.md` only for the rates a fired check needs.

**Route security and correctness out.** Source-level security (injection, authz, secrets, supply chain) and functional correctness belong to **code-audit**. Reliability hardening belongs to **productionize**. If installed, hand off; if not, leave a one-line pointer. Do not re-implement them here.

Record the tier as a `D` row in the evidence ledger (`.evidence/` in the target repo, per evidence-protocol.md). Findings and estimates are `C` rows; price-based `C` rows carry an `expiry` date so they resurface when prices drift.

## Tier×check matrix

Single source of tier truth. Where prose elsewhere disagrees, this matrix wins.

| Check / deliverable | hobby | standard | high-spend |
|---|---|---|---|
| C1 Unbounded agent/LLM loop | flag | audit + fix | audit + fix + priced blast-radius + rollback |
| C2 Retry w/o jitter+budget+cap | flag | audit + fix | audit + fix + priced + rollback |
| C3 NAT egress w/o VPC endpoint | flag | audit + fix | audit + fix + priced |
| C4 Prompt caching off (static prompt) | flag | audit + fix | audit + fix |
| C5 Model over-selection | flag | audit + fix | audit + fix + routing plan |
| C6 Over-provisioned latency-bound memory | skip | audit + fix | audit + fix (SLO-checked) |
| C7 Missing S3 lifecycle / abort-MPU | flag | audit + fix | audit + fix |
| C8 Warehouse full-scan | flag | audit + fix | audit + fix |
| C9 N+1 / missing index | flag | audit + fix | audit + fix |
| C10 Verbose hot-path logging | skip | flag | audit + fix (audit-trail-checked) |
| C11 List-vs-effective / commitment coverage | skip | flag | full rate/commitment math |
| Estimate report (Phase 3) | per-unit/ranged, no point totals | estimates + assumptions | full rate + commitment + confidence intervals |

## Phase 1 - Cost audit

Run the checks the matrix calls for at the chosen tier. Each is one concrete static action; the full evidence, dollar anchors, and citations live in `references/cost-checks.md`. Read it when you run a check so you can recite the anchor and the rate to the user. Emit a `C` row per finding with a `risk` (estimated annual $ × likelihood) and, where a rate applies, an `expiry`.

*Tier 1 - runaway (four-to-five-figure blast radius):*

1. **C1 Unbounded agent/LLM loop.** Find every agent / ReAct / tool-use loop. Flag any lacking **both** a hard max-iteration cap **and** a per-run token-or-cost ceiling that *enforces* (halts), not merely logs. Multi-agent auto-loops multiply the token burn. See C1 in `cost-checks.md` (rate: `pricing-notes.md#model-prices`).
2. **C2 Retry without jitter + budget + stop-rule.** Grep every retry site (SDKs, HTTP clients, queue consumers, DB drivers). Flag missing jitter, missing retry budget, missing attempt cap. At 50% downstream failure, jitterless retry amplifies traffic (and the bill) several-fold. This shares the retry detector with productionize; **here the finding is priced.** See C2 in `cost-checks.md`.
3. **C3 NAT egress to in-region AWS services without a VPC gateway/interface endpoint.** In the IaC, trace private subnets reaching S3/DynamoDB/ECR/CloudWatch/etc. through a NAT gateway. NAT bills a per-GB data-processing charge on top of transfer; an in-region gateway endpoint (S3, DynamoDB) or interface endpoint removes it. See C3 in `cost-checks.md` (rate: `pricing-notes.md#nat-egress`).

*Tier 2 - structural waste:*

4. **C4 Static LLM system prompt with prompt caching disabled.** Find large fixed system/policy/context prompts re-sent every call with no cache-control / prompt-caching flag. Cached input tokens read at a large discount. See C4 in `cost-checks.md` (rate: `pricing-notes.md#prompt-caching`).
5. **C5 Model over-selection.** Find a hardcoded frontier model on high-volume simple calls (classify, extract, route, boolean) with no routing/cascade to a cheaper tier. See C5 in `cost-checks.md` (rate: `pricing-notes.md#model-prices`).
6. **C6 Over-provisioned serverless memory on latency-bound functions.** Find high memory allocation where the function is **blocked waiting on a downstream response** (a DB query, an external API), so neither CPU nor bandwidth is the bottleneck and the extra memory is paid-for-idle. **Must NOT fire on bandwidth-bound work:** AWS docs are explicit that more memory raises network throughput, so a throughput-bound S3 transfer legitimately benefits. Key on "blocked on a downstream response," not "does I/O." See C6 in `cost-checks.md`.
7. **C7 Missing S3 lifecycle / AbortIncompleteMultipartUpload.** Find buckets taking large or multipart uploads with no abort rule and no tiering/expiry. Incomplete multipart uploads bill forever and are invisible in the console. See C7 in `cost-checks.md`.
8. **C8 Warehouse `SELECT *` / no partition-or-cluster filter.** In query/dbt/ORM code hitting a columnar warehouse, find full scans priced per bytes scanned. BigQuery on-demand is **$6.25 per TiB (tebibyte, not TB)**; partition + cluster filters cut scanned bytes 80-95%. See C8 in `cost-checks.md` (rate: `pricing-notes.md#warehouse`).
9. **C9 N+1 / query-in-a-loop / missing index on a filtered FK.** Find the query-inside-a-loop and the filtered foreign key with no index, priced at scale. **This is the exact pattern LLMs have near-zero recall on** ("Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code Review", arXiv; verify id before quoting), so it is a true delta, not a lecture. See C9 in `cost-checks.md`.
10. **C10 Verbose per-invocation logging on hot paths.** Find debug/info logging emitted per request on a hot path, where log-ingestion cost can exceed the compute cost of the function emitting it. See C10 in `cost-checks.md` (rate: `pricing-notes.md#log-ingestion`).

*Tier 3 - rate/commitment reasoning (the pure-concept delta LLMs lack):*

11. **C11 List-price vs effective-cost framing.** Any savings estimate must reason in **post-discount / amortized** terms and target commitment coverage in the ~70-80% band with high utilization, not naive 100% on-demand list price. Over-committing to 100% coverage strands spend on idle reservations. See C11 in `cost-checks.md`.

**Then the three questions LLMs never ask,** answered in writing as `C` rows (at `standard` and above):
(a) what scales **super-linearly** with load or usage here (the cost feedback loops: retry storms, agent-loop fan-out, per-row warehouse scans under growth);
(b) what the **single largest line item** likely is and why (so the user optimizes the thing that matters, not the visible-but-small thing);
(c) which "optimization" would trade a **large reliability risk for a small saving** (cross-check with productionize; never recommend a cut productionize would flag).

Why (c) is the sharpest: the cheapest configuration is often the one that falls over. A cost skill that causes an outage has failed at its job.

## Phase 2 - Fix (with self-safety)

Rank findings by **estimated annual $ × confidence** (the `risk` field plus an estimated-savings field on the `C` row). Apply smallest-blast-radius first, one concern per commit.

**Some of this skill's own changes touch reliability mechanisms.** Cutting a retry, trimming a memory floor, or dropping log volume can each cause an outage or destroy an audit trail. So the reliability-touching checks are wired mechanically to productionize, not left to good intentions:

- **C2 retry ↔ productionize retry check.** Before proposing a retry change, read the shared ledger for an existing `P` row on that call path. A retry that looks jitterless may be the *only* backstop for a flaky-but-idempotent dependency; pricing it is fine, deleting it is not.
- **C6 memory ↔ productionize pool/probe checks.** A high memory floor may be sized for a latency SLO, not waste. At high-spend tier, verify against the SLO before trimming.
- **C10 log-volume ↔ productionize observability check.** Verbose logging may be the sole audit trail. At high-spend tier, verify it is not audit-load-bearing before cutting.

Every fix touching a reliability mechanism gets a `C` row with a **blast-radius note**. At high-spend tier, such a fix is **proposed with a pre-committed rollback trigger, not auto-applied**. Never optimize cost into an outage.

## Phase 3 - Estimate report, with a mechanical provenance gate

Static analysis cannot see traffic volume, so this report is built to make false precision impossible to ship.

**The provenance gate (deterministic, generation-time, ship-blocking).** Every dollar figure in the report carries an inline tag `(rate: pricing-notes.md#anchor @date; volume: Vn)`. Then grep the report for dollar figures (`$` followed by digits); any bare figure lacking **both** a Class-A rate cite **and** a volume-assumption id is flagged and blocks the report. Same gate shape as productionize's artifact-provenance grep.

**When traffic is unelicited, the output MUST be per-unit or ranged**, never a point total:
- per-unit: `$0.045/GB NAT data-processing × [unknown egress volume]`
- ranged: `$X-$Y/yr at 1M-10M requests/mo` (state both endpoints and the assumption behind each).

A bare point annual figure for a path whose volume you cannot derive from the code is a **hard failure**. At `hobby` tier, no point totals at all.

**Per finding, report:** current vs post-fix estimate (per-unit or ranged as required), the assumption set (Vn ids and what each assumes), and a confidence level. State plainly that these are **static approximations, not billed measurements**; the skill has no account and did not run a price API.

Only **Class A** rates (the vendor's own pricing page, dated) feed the math. **Class B** figures (the "$907/day", "$6,531 runaway agent" war stories) are illustrative, magnitude only, and are **never** used as a rate in an estimate. Both classes and every rate live in `references/pricing-notes.md`.

## Closing

Chain **`REQUIRED (if available): adversarial-verify`** on the findings-and-estimates packet. It audits the `C` ledger directly (evidence-protocol.md): re-checks the dollar math, that each rate cite is real and dated, and that each proposed cut is a real saving and not a phantom.

Also chain: **code-audit** for the security/correctness half; **productionize** for the reliability cross-check (a shared retry or egress finding is priced here and hardened there). A `C` finding that touches a call path with a `P` row must reconcile against it before Phase 2 acts.

The report tells the user **when to re-audit**: price-based `C` rows carry `expiry` dates, so freshness-sensitive estimates resurface rather than rot when the vendor changes the rate.

## Honest scope

This is an audit-fix-estimate skill. The checks are concrete agent actions you perform now; they need no external scripts to run. The provenance grep and any rate-refresh harness a repo might ship are an optional hardening layer, not a prerequisite; the audit stands on its own. Out of scope: live billing reconciliation (needs an account; that is CloudZero/Vantage's job, and the skill prepares the questions), actually running load or price APIs, and correctness/security (code-audit owns those). The skill produces static estimates and code/config changes, not a signed bill.

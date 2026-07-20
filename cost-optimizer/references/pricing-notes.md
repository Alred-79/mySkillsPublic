# Pricing notes

The rates the cost audit's dollar math derives from. SKILL.md and `cost-checks.md` quote from here by anchor.
Only **Class A** rates on this page may feed an estimate. Every figure carries a capture date, because prices drift; re-fetch the primary source before a number drives a real decision.

## The two-class citation rule

- **Class A, the load-bearing rate.** The vendor's own published price or a reproducible benchmark. These feed the report's dollar math. Each is listed below with its primary source and capture date.
- **Class B, the illustrative incident.** A single named "it cost $X" war story. Magnitude only, never a rate. Listed in their own section, clearly labeled, and **never used in an estimate's math.**

A price on this page is a snapshot as of its capture date, not a live feed. Regions, tiers, and negotiated/committed-use discounts change the effective number. Quote the date with the figure, and treat every Class A rate as "verify at the source before it decides anything."

## Contents

- [Class A rates](#class-a-rates)
  - [Model prices (per MTok)](#model-prices)
  - [Prompt caching](#prompt-caching)
  - [Warehouse scan](#warehouse)
  - [NAT egress](#nat-egress)
  - [S3 storage](#s3-storage)
  - [Serverless compute](#serverless)
  - [Log ingestion](#log-ingestion)
  - [Commitment discounts](#commitment-discounts)
- [Class B illustrative incidents](#class-b-illustrative-incidents)

---

## Class A rates

Feed these into estimates. Nothing else.

### Model prices

Per-million-token (MTok) list prices. Anthropic models captured 2026-05-26 (via the installed `claude-api` skill's model table; re-verify at the Anthropic pricing page). For any other provider (OpenAI, Google, etc.), fetch that provider's own pricing page and record it here with its date before using it - do not carry a number from memory.

| Model | Input $/MTok | Output $/MTok | Captured | Source |
|---|---|---|---|---|
| Claude Opus 4.8 (`claude-opus-4-8`) | $5.00 | $25.00 | 2026-05-26 | Anthropic pricing (platform.claude.com/docs/en/pricing) |
| Claude Sonnet 4.6 (`claude-sonnet-4-6`) | $3.00 | $15.00 | 2026-05-26 | Anthropic pricing |
| Claude Haiku 4.5 (`claude-haiku-4-5`) | $1.00 | $5.00 | 2026-05-26 | Anthropic pricing |

Feeds: C5 (model over-selection), C1 (agent-loop token cost per turn). The cross-tier gap is the lever for C5: an input token on Opus costs 5× a Haiku input token, an output token 5×.

### Prompt caching

Anthropic prompt-caching multipliers, relative to the model's base input rate. Captured 2026-05-26 (claude-api skill; verify at the prompt-caching docs page).

| Token class | Multiplier vs base input | Captured |
|---|---|---|
| Cache write, 5-minute TTL | 1.25× base input | 2026-05-26 |
| Cache write, 1-hour TTL | 2× base input | 2026-05-26 |
| Cache read (cache hit) | 0.1× base input (i.e. ~90% off) | 2026-05-26 |

Feeds: C4. Break-even: with 5-minute TTL, two requests recover the write premium (1.25× + 0.1× < 2× uncached); 1-hour TTL needs three. Caching is a **prefix match** - a per-request timestamp/UUID or unsorted JSON in the prefix silently defeats it (`cache_read_input_tokens` stays 0), so confirm prefix stability before crediting the saving.

### Warehouse

| Warehouse | Rate | Free tier | Captured | Source |
|---|---|---|---|---|
| BigQuery on-demand analysis | **$6.25 per TiB scanned** (tebibyte) | first 1 TiB/month | 2026-07 | Google Cloud BigQuery pricing (cloud.google.com/bigquery/pricing) |

Feeds: C8. **The unit is TiB, not TB** - a tebibyte is 2^40 bytes, ~10% larger than a decimal TB, so "$6.25/TB" would misstate both the rate basis and the free-tier size. For Snowflake / Redshift / Athena, fetch that engine's own scan or credit pricing and record it here with a date before using it; the pattern (per-bytes-scanned) is the same, the number is not.

### NAT egress

NAT gateway **data-processing** charge (billed per GB in addition to transfer), and the endpoint alternatives. Rate is region-specific - fetch the exact per-GB figure for the target region from the source below and record it here dated before pricing a finding.

| Item | Rate basis | Captured | Source |
|---|---|---|---|
| NAT gateway data processing | per-GB on every byte processed, plus an hourly gateway charge | verify at source | AWS VPC pricing (aws.amazon.com/vpc/pricing) |
| S3 / DynamoDB gateway endpoint | no hourly charge, no per-GB data-processing charge | verify at source | AWS PrivateLink / VPC endpoint pricing |
| Interface endpoint (other services) | hourly per-AZ charge + per-GB processed (typically far below NAT for in-region service traffic) | verify at source | AWS PrivateLink pricing |

Feeds: C3. The saving is removing the NAT per-GB data-processing charge on in-region S3/DynamoDB/etc. traffic by routing it through a gateway/interface endpoint. **When byte volume is not derivable from the code, express as `$X/GB × [unknown volume]`, never a point annual figure** (the provenance gate blocks a bare point figure here).

### S3 storage

| Item | Rate basis | Captured | Source |
|---|---|---|---|
| S3 Standard storage | per-GB-month (tiered by volume; region-specific) | verify at source | AWS S3 pricing (aws.amazon.com/s3/pricing) |
| Incomplete multipart upload parts | billed as Standard storage until aborted | verify at source | AWS S3 docs (multipart upload lifecycle) |

Feeds: C7. Orphaned multipart parts accrue storage cost indefinitely and do not appear in the object list; an `AbortIncompleteMultipartUpload` lifecycle rule caps them. Tiering (Infrequent Access / Glacier) cuts the rate for cold data.

### Serverless

| Item | Rate basis | Captured | Source |
|---|---|---|---|
| AWS Lambda compute | per **GB-second** (`memory_GB × duration_s`); requests billed separately | verify at source | AWS Lambda pricing (aws.amazon.com/lambda/pricing) |

Feeds: C6. The memory slider also scales vCPU and network throughput (Lambda docs), which is *why* the check must not fire on bandwidth-bound work (more memory legitimately speeds a throughput-bound transfer). For a latency-bound function, duration is fixed by downstream wait, so extra `memory_GB` multiplies the bill without cutting duration.

### Log ingestion

| Item | Rate basis | Captured | Source |
|---|---|---|---|
| Log ingestion | per-GB ingested (vendor-specific; CloudWatch Logs, Datadog, etc.) | verify at source | the observability vendor's own pricing page |

Feeds: C10. On a hot path, `log_bytes_per_request × requests × ingestion_$/GB` can exceed the compute cost of the emitting function. Fetch the actual per-GB ingestion rate for the stack in use and record it here dated.

### Commitment discounts

| Mechanism | Concept | Source |
|---|---|---|
| AWS Savings Plans / Reserved Instances | commit to steady-state usage for a discount vs on-demand; strand cost if utilization is low | AWS pricing |
| GCP committed-use discounts | analogous commit-for-discount | Google Cloud pricing |

Feeds: C11. These are the mechanics behind effective-cost framing: target the ~70-80% coverage band at high utilization, not 100% on-demand list and not 100% coverage. The specific discount percentages are plan- and term-specific; fetch them for the actual commitment before quoting a realized saving.

---

## Class B illustrative incidents

**Magnitude only. Never fed into an estimate as a rate.** Use these to make a failure concrete for the user, always attributed and dated, always labeled illustrative.

| Incident | Figure | What it illustrates | Note |
|---|---|---|---|
| Runaway agent loop | ~$6,531 from a single unterminated loop | C1: an agent loop with no iteration cap or cost ceiling | Illustrative, magnitude only. Named-incident report; do not price a finding off this - use the model rate. |
| Multi-day agent run | five-figure spend over ~11 days | C1: unbounded loops compound over time | Illustrative, magnitude only. |
| NAT egress bill | ~$907/day | C3: private-subnet traffic to in-region AWS services through NAT | Illustrative, magnitude only. Price the finding off the NAT $/GB, not this. |
| NAT routing trap | ~$100k | C3: at-scale NAT data-processing with no gateway endpoint | Illustrative, magnitude only. |

Every figure here is a single anecdote, not a base rate. If you quote one, say "illustrative, magnitude only," attribute it, and re-fetch the primary write-up before it informs a decision.

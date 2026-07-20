# Spec: cost-optimizer

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md)
Sibling: [productionize.md](productionize.md) (same delta-only + tier architecture)

## Purpose

Read a codebase + IaC + config statically (no cloud account, no billing API, no deploy)
and emit a prioritized, **dollar-quantified** list of cost anti-patterns across cloud,
LLM/AI, runtime, and data - then apply prioritized fixes and produce a cost-estimate
report. Wide scope by request: all four cost surfaces, tiered by blast radius.

**The delta-only rule (shared with productionize):** encode ONLY what a frontier LLM
won't surface on its own when asked "make this cheaper." A raw model reliably says "pick
a smaller instance, add a cache, use a cheaper model" - it does NOT compute retry-storm
dollar math, egress topology, unbounded-agent-loop token cost, savings-plan coverage
math, or warehouse scan cost. Empirical backbone: "Bigger Isn't Always Better: A
Comparative Evaluation of LLMs for Automated Code Review" (arXiv; verify id before
quoting), which reports LLMs show near-zero recall on performance/cost bugs (F1 0.066
on real PRs vs 0.847 synthetic).
Enforcement is mechanical: the eval's per-check obsolescence prunes any check the
no-skill baseline already catches (see Evals).

## Market position (researched 2026-07)

No static code-reading cost auditor exists as an agent skill. The field splits into:
knowledge injectors (OptimNow cloud-finops-skills - teaches FinOps, doesn't read code);
SaaS-dashboards-behind-an-MCP (CloudZero plugin - needs an account + ingested billing);
and one shift-left tool, Infracost (IaC price-lookup, needs `terraform plan` + API key,
blind to topology/runtime/LLM/warehouse). The Claude Code "cost" skills that surface
(claude-cost-optimizer, ccusage, getburnd) optimize Claude Code's OWN token spend, not
the user's app. Distinct value: static, no-account, code-reading, dollar-quantified,
topology-and-rate-aware - the intersection nobody occupies. Routes to the installed
code-audit / query-validation skills for correctness; owns the cost dimension.

## Files

```
cost-optimizer/
  SKILL.md                 # tier elicitation → cost audit → fix → estimate report
  references/cost-checks.md # the evidence-backed catalog (below), loaded per surface
  references/pricing-notes.md # list-vs-effective, region/egress rates, model prices - CITED, dated
  evals/                   # colocated evals (layout per evidence-protocol.md)
```

**Two-class citation rule for cost-checks.md and pricing-notes.md** (closes the
secondary-source trap productionize was dinged for): **Class A - load-bearing rates**
(NAT $/GB, BigQuery $/TiB, cache-read discount, model prices) MUST cite the vendor's
own pricing page, dated; the report's dollar math derives ONLY from Class A. **Class B -
illustrative incidents** (the "$907/day", "$6,531 runaway agent" war stories) may cite a
near-primary write-up but are labeled "illustrative, magnitude only" and are NEVER fed
into an estimate as a rate. Every figure carries its capture date (prices drift).

**SKILL.md stays lean**: SKILL.md carries only the flow, the tier×check matrix, and
routing. The 11-check catalog lives in `cost-checks.md` and all rates/citations in
`pricing-notes.md`, both loaded per surface (a hobby LLM-only audit never loads
warehouse/NAT rates). This is a wide skill by scope, not by payload.

## Flow

**Phase 0 - Scope + inventory (one elicitation round; "go ahead" = infer).**
Cost-criticality tier: `hobby` (correctness of estimates matters, magnitude small) /
`standard` / `high-spend` (bill is material; full rate/commitment analysis). Inventory:
languages, cloud/IaC, datastores, queues, LLM SDKs, warehouse, observability. Security/
correctness routed to code-audit; the skill owns cost only.

**Phase 1 - Cost audit** (catalog in `references/cost-checks.md`; each check = a concrete
static action with a dollar anchor + source; passes the "a frontier LLM won't say this
unprompted" filter). Tiered by blast radius:

*Tier 1 - runaway (4–5 figure blast radius):*
1. **Unbounded agent/LLM loop** - agent/ReAct loops lacking BOTH a max-iteration cap and
   a per-run token/cost ceiling (enforcement, not an alert). Anchor: documented
   "$6,531 agent", "$47k/11 days" runaway loops; multi-agent auto-loop token multiplier.
2. **Retry without jitter + budget + stop-rule** - backoff missing jitter/retry-budget/
   cap: at 50% failure, amplifies traffic (and bill) several-fold. (Shares the retry
   detector with productionize; here the finding is priced.)
3. **NAT egress to in-region AWS services without a VPC gateway endpoint** - private
   subnets reaching S3/DynamoDB/ECR/CloudWatch through NAT at per-GB data-processing
   rates. Anchor: documented $907/day and "$100k routing trap" cases.

*Tier 2 - structural waste:*
4. **Static LLM system prompt with prompt caching disabled** - large fixed system/policy
   prompts re-sent per call without cache-control.
5. **Model over-selection** - hardcoded frontier model on high-volume simple calls with
   no routing/cascade (incl. the citable "smaller model matched larger at a fraction of
   cost" evidence; verify the specific code-review benchmark figure before quoting, from
   "Bigger Isn't Always Better: A Comparative Evaluation of LLMs for Automated Code
   Review" (arXiv; verify id before quoting)).
6. **Over-provisioned serverless memory on latency-bound functions** - high memory alloc
   where the function is blocked waiting on a downstream call (a DB query, an external
   API) so neither CPU nor bandwidth is the bottleneck. **Must NOT fire on bandwidth-bound
   work** - AWS docs are explicit that more memory raises network throughput, so a
   throughput-bound S3 transfer legitimately benefits; the check keys on "blocked on a
   downstream response," not "does I/O."
7. **Missing S3 lifecycle / AbortIncompleteMultipartUpload** - buckets taking large/multi-
   part uploads without an abort rule + tiering (incomplete MPUs bill forever, invisibly).
8. **Warehouse `SELECT *` / no partition-or-cluster filter** in query/dbt code - columnar
   full scans priced per bytes-scanned (BigQuery on-demand $6.25/**TiB** - tebibyte, not
   TB - captured 2026-07; partition+cluster cuts scanned bytes 80–95%).
9. **N+1 / query-in-a-loop / missing index on filtered FK** - priced at scale (the exact
   pattern LLMs have near-zero recall on - a true delta).
10. **Verbose per-invocation logging on hot paths** → ingestion cost that can exceed the
    compute cost of the function emitting it.

*Tier 3 - rate/commitment reasoning (the pure-concept delta LLMs lack):*
11. **List-price vs effective-cost framing** - savings estimates must reason in
    post-discount/amortized terms and target commitment coverage in the ~70–80% band with
    high utilization, not naive 100% on-demand list price.

Plus the three questions LLMs never ask, answered in the report: what scales super-linearly
with load/usage (the cost feedback loops), what the single largest line item likely is and
why, and which "optimizations" would trade a large reliability risk for a small saving
(cross-check with productionize - never recommend a cut that productionize would flag).

## Tier×check matrix (single source of tier truth; where prose disagrees, the matrix wins)

| Check / deliverable | hobby | standard | high-spend |
|---|---|---|---|
| 1 Unbounded agent/LLM loop | flag | audit + fix | audit + fix + priced blast-radius + rollback |
| 2 Retry w/o jitter+budget+cap | flag | audit + fix | audit + fix + priced + rollback |
| 3 NAT egress w/o VPC endpoint | flag | audit + fix | audit + fix + priced |
| 4 Prompt caching off (static prompt) | flag | audit + fix | audit + fix |
| 5 Model over-selection | flag | audit + fix | audit + fix + routing plan |
| 6 Over-provisioned latency-bound memory | skip | audit + fix | audit + fix (SLO-checked) |
| 7 Missing S3 lifecycle/abort-MPU | flag | audit + fix | audit + fix |
| 8 Warehouse full-scan | flag | audit + fix | audit + fix |
| 9 N+1 / missing index | flag | audit + fix | audit + fix |
| 10 Verbose hot-path logging | skip | flag | audit + fix (audit-trail-checked) |
| 11 List-vs-effective / commitment coverage | skip | flag | full rate/commitment math |
| Estimate report (Phase 3) | per-unit/ranged, no point totals | estimates + assumptions | full rate + commitment + confidence intervals |

**Phase 2 - Fix.** Findings ranked by estimated annual $ × confidence (ledger `risk` +
an estimated-savings field); fixes applied smallest-blast-radius first, one concern per
commit. **Self-safety, wired mechanically (not just an aspiration to agree with
productionize):** each cost check that can touch a reliability mechanism names the
productionize check it must reconcile against - retry #2 ↔ productionize retry check;
memory #6 ↔ productionize pool/probe checks; log-volume #10 ↔ productionize observability
check - and Phase 2 reads the shared ledger for an existing `P` row on that path before
proposing a cut. A fix touching a reliability mechanism carries a blast-radius note and,
at high-spend tier, is proposed with a rollback trigger, not auto-applied. Never optimize
cost into an outage.

**Phase 3 - Estimate report, with a mechanical provenance gate.** Static analysis cannot
see traffic volume, so a point annual dollar figure is false precision by construction.
Therefore: **every dollar figure carries an inline `(rate: pricing-notes.md#X @date;
volume: assumption Vn)` tag, and a generation-time grep flags any bare dollar figure
lacking BOTH a Class-A rate cite and a volume-assumption id - ship-blocking** (the same
gate shape as productionize's artifact-provenance grep). When traffic is unelicited the
output MUST be a per-unit cost or a stated range ("$0.045/GB × [unknown volume]";
"$X–$Y/yr at 1M–10M req/mo"), never a bare point estimate. Per finding: current vs
post-fix estimate, the assumption set, confidence. The report states estimates are
static approximations, not billed measurements. Closer: `REQUIRED (if available):
adversarial-verify` on the findings+estimates packet (its factual routing re-checks the
dollar math and that each cut is real).

## Suite integration

Findings + estimates are evidence-protocol assertions (prefix `C`); tier recorded as a
`D` row; price-based assertions carry `expiry` dates (re-audit when prices move). Chains:
code-audit (security/correctness), productionize (the reliability cross-check - a shared
retry/egress finding is priced here and hardened there), adversarial-verify (closer;
verifies the dollar math and that each cut is real).

## Evals & testing plan

Artifacts in `evals/`; shared rules in [evidence-protocol.md](evidence-protocol.md).
- **Fixture**: a small polyglot app seeded with tier-1/2/3 cost violations (unbounded
  agent loop, jitterless retry, NAT-egress IaC, caching-off static prompt, Opus-on-
  trivial-calls, over-provisioned Lambda, no S3 lifecycle, `SELECT *` on a partitioned
  table, N+1) plus clean decoys, three reliability-critical decoys the skill must NOT cut
  (see do-no-harm gate), and a no-derivable-volume egress path (any point annual dollar
  figure for it is a hard fail).
- **Catch-rate (deterministic)**: recall on seeded violations, FP rate on decoys, ≥3
  reps, no-skill baseline arm.
- **Per-check obsolescence (delta-only enforcement)**: sub-assertion granularity vs
  `expected.md` - a "catch" means the baseline identified the *specific* seeded violation,
  not that it mentioned the topic. A baseline that says "add caching" but does NOT locate
  the specific static prompt lacking cache-control does NOT prune check #4. Any sub-check
  the baseline catches in ≥2/3 reps across both model tiers is pruned to `pruned.md`
  (seeds stay in the fixture so regressions restore it).
- **Estimate sanity (judged + deterministic)**: dollar math checked against the fixture's
  stated assumptions; figures must cite a dated Class-A source with a volume-assumption id
  (the provenance grep runs here); the no-derivable-volume decoy must yield a per-unit or
  ranged estimate - any point annual figure for it fails.
- **Do-no-harm gate (pass^k), multi-axis**: the skill must never recommend cutting any of
  three reliability-critical decoys - a load-bearing retry (that looks jitterless but is
  the only backstop), an over-provisioned memory floor actually sized for a latency SLO,
  and verbose logging that is actually the sole audit trail. A cost cut that causes an
  outage or loses the audit trail is a hard fail on every rep.
- **RED baseline**: expected misses per "Bigger Isn't Always Better: A Comparative
  Evaluation of LLMs for Automated Code Review" (arXiv; verify id before quoting):
  baseline says "add a cache /
  smaller instance" but misses egress topology, retry-storm math, agent-loop ceilings,
  warehouse scan cost. GREEN: catalog catches all seeded violations. REFACTOR.

## Out of scope

Live billing reconciliation (needs an account - that's CloudZero/Vantage's job; the skill
prepares the questions). Actually running load/price APIs. Correctness/security (code-audit
owns those). The skill produces static estimates and code/config changes, not a signed bill.

# Spec: statistician

Status: approved design, pre-implementation. Adversarially reviewed 2026-07-19; all 15
findings resolved in this revision.
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

EDA + deep statistical analysis with enforced rigor. A user points the skill at a dataset
and a question; the skill runs a goal-conditioned, gate-enforced pipeline from profiling
through inference to communication, where every gate corresponds to a *documented* AI
failure mode. The persona framing matters: an o1 case study went 3/10 → 9/10 on
Simpson's-paradox decisions from a "careful statistician" directive alone — directives
work, and this skill is a system of them.

## Market position (researched + adversarially verified 2026-07)

- Anthropic ships zero data-science skills (verified against anthropics/skills listing).
- Business-analytics collections (the installed nimrodfisher set) have no Bayesian and no
  workflow *enforcement*; rigorous skills exist but target academics (Giro03k, davila7).
- Bayesian workflow enforcement is already done well: baygent-skills (gated 10-step
  workflow, R-hat/ESS interpretation gates) and pymc-labs/python-analytics-skills
  (benchmarked 60%→93% viability). We do not rebuild these; see Bayesian strategy.
- Novel territory (verified, with prior-art caveat): **goal-conditioned rigor tiers**
  (nothing exists), **EDA→inference bridge with multiplicity control** (no skill exists;
  concept prior art = "Agentic Garden of Forking Paths" m-value / Agentic Bootstrap,
  arXiv 2607.01507 — cite and build on it, first skill implementation), **implicit test
  counter**, **statistic provenance**, **join audits as default behavior**.

## Evidence base (all verified against primary sources)

Design is failure-mode-driven. Anchors: StatQA (arXiv 2406.07815 — applicability errors
are LLMs' dominant class; best model 64.83%); "LLM hacking" (arXiv 2509.08825 — analytic
configuration choices flip ~31% of conclusions); CausalPitfalls (arXiv 2505.13770 —
subgroup blindness); DABstep (implicit-rule planning failures); Kapoor–Narayanan leakage
taxonomy (≥294 papers); Pimentel notebook reproducibility (24.11% re-execute, 4.03%
reproduce); deepsense EDA reliability (run-to-run variance dominates); AIRepr
analyst–inspector (arXiv 2502.16395); Gelman et al. Bayesian workflow (arXiv 2011.01808);
STRATOS IDA framework. (Enterprise text-to-SQL collapse — Spider 2.0 site, GPT-4o 86.6%
→ 10.1% — motivates the SQL-source variant below.)

## Invocation & data sources

`/statistician [dataset-or-question] [tier]` — with no args, operates on the dataset and
question in conversation context.

Data-source routing (resolved in Phase 0):
- **File (CSV/parquet/etc.)** → pandas path; all gates as specified.
- **Database/SQL** → SQL profiling variant of Phase 1; join audits expressed as SQL
  row-count/grain assertions run before and after each join; schema + data dictionary
  read mandatory (the Spider 2.0 countermeasure: never write analysis SQL against an
  unprofiled schema).
- **Oversized data** → documented sampling policy; the sample's construction (method,
  seed, n, coverage check vs full-data aggregates) recorded as an assertion.
- **Live notebook state** → snapshot to a linearly executable script first (see
  reproducibility invariant).

## Files

```
statistician/
  SKILL.md              # flow skeleton + tier matrix + hard invariants ONLY
  gates/phase-0.md ... phase-5.md   # per-phase gate tables, loaded per phase
  references/           # on-demand: bayesian-condensed.md, leakage-info-sheet.md,
                        #   missing-data-mechanisms.md, causal-verb-list.md
  scripts/              # deterministic judgment-replacers (below)
  evals/                # colocated evals (layout per evidence-protocol.md):
    evals.json          #   fixtures/ = seeded-trap datasets; judge/ = rubric judge prompt;
    fixtures/  judge/   #   expected.md = per-trap expected catches
    expected.md
```

The two-stage benchmark definition lives in `evals/`; the shared runner/aggregator
harness is repo-level (skill-creator tooling), so the skill payload stays lean.

Scripts replace judgment (baygent's `check_diagnostics.py` pattern — the LLM cannot
rationalize numbers a script has already ruled on):
- `assumption_gate.py` — normality, variance homogeneity; independence *partially*:
  Durbin–Watson given a declared time order, duplicate-key detection. Full independence
  is NOT scriptable — the sampling design (clustered? repeated measures?) is elicited in
  Phase 0 and consumed by the script.
- `join_audit.py` — pre/post row counts, key uniqueness, dtype match on both sides,
  grain assertion (pandas `validate=` / SQL count checks).
- `multiplicity_audit.py` — reads the test-counter log (mechanism below) → BH-FDR.
- `provenance_table.py` — builds the provenance table from the execution log (below).
- `bayes_diagnostics.py` — ArviZ-based deterministic verdicts (R-hat, ESS, divergences,
  LOO warnings) for the vendored Bayesian path.
- `causal_verb_scan.py` — greps report drafts for causal verbs ("drives", "causes",
  "leads to", "because of", "results in") lacking a declared identification strategy.

**Execution-log invariant (provenance by construction):** all analysis code runs through
a wrapper that appends stdout/results to `execution.log`. `provenance_table.py` derives
a table (statistic → value → log line). **Every number in the report must cite a
provenance-table ID**; a script greps the report for numeric tokens lacking an ID and
flags them (explicit exception list for e.g. rounded derivations, each justified). This
is deterministic; the old "reverse-match prose to output" design was not.

**Reproducibility invariant (all tiers):** the analysis is a linearly executable artifact
(top-to-bottom script or restart-run-all notebook), seeds set, versions pinned. Tiering
controls whether it is *re-run and diffed*, not whether it is runnable.

## Rigor tiers — the tier×gate matrix

Elicited in Phase 0 (one round; "go ahead" = infer from stakes language). The final
report states the tier and what was NOT done because of it.

| Gate | quick-look | decision-grade | high-stakes |
|---|---|---|---|
| Goal + KPI elicitation, docs read | required | required | required |
| Data audit + join audits + cleaning evidence | required | required | required |
| Confirmation strategy (holdout or FDR-mode, declared BEFORE Phase 2) | skipped — all findings labeled exploratory | required | required |
| Implicit test counter | count + label ("N patterns scanned, uncorrected") | count + BH-FDR | count + BH-FDR |
| Subgroup/strata re-run of headline findings | 1 stratifier | 2–3 stratifiers | 2–3 + sensitivity to stratifier choice |
| Pre-registered plan + deviation log | skipped (exploratory label instead) | required | required |
| Assumption gate before any test | required | required | required |
| Effect sizes + CIs on every estimate | required | required | required |
| Bayesian twin offered | no | yes | yes |
| Missing-data mechanism diagnosis / MI | flag only | diagnose + MI if MAR | diagnose + MI + MNAR sensitivity |
| Robustness (alternative specifications) | none | ≥2 specs | ≥3 specs + mini-multiverse |
| Repeatability re-run + conclusion diff | no | 1 fresh re-run | ≥2 re-runs |
| Analyst–inspector reproduction | no | yes (via adversarial-verify) | yes |
| adversarial-verify on final claims | optional | required | required (high effort, 3-lens) |

Conflict rule: where a phase gate and this matrix disagree, **the matrix wins** — it is
the single source of tier truth.

## Flow

**Phase 0 — Goal elicitation + confirmation strategy (one round; "go ahead" = infer).**
- What decision does this inform? Confirmatory or exploratory? → rigor tier (matrix).
- KPI/metric definitions pulled from docs or asked — never improvised (goal-ambiguity
  failure: insight recovery drops ~60%→40% when objectives are ambiguous).
- Sampling design declared (clustered/repeated/independent) — consumed by
  `assumption_gate.py`.
- Read ALL supplied documentation/data dictionaries before coding; restate extracted
  rules (DABstep implicit-rule failure).
- **At decision-grade+: the confirmation strategy is fixed HERE, before any exploration**
  — either a holdout split created now, or declared FDR-accounting mode with the counter
  scope frozen. (Adversarial-review finding 1: pre-registration after exploration is the
  forking-paths failure itself.)

**Phase 1 — Data audit (STRATOS IDA discipline).** Route through installed skills where
present (hybrid rule): programmatic-eda profiling, data-quality-audit validators. Added
gates: per-step evidence printing (dtypes, null counts, row-count deltas, date min/max,
sample; day/month swap check; no silent coercion); **join audit on every merge**
(`join_audit.py`); missing-data mechanism handling per matrix; IDA report of
interpretation-affecting cleaning actions.

**Phase 2 — Exploration with multiplicity discipline (the EDA→inference bridge).**
- **Test counter mechanism**: (a) runtime shim counts scriptable tests (scipy.stats
  calls, `.corr()` cell counts); (b) stated honor rule for the uninstrumentable rest —
  any displayed table with ≥2 groups increments the counter by its comparison count.
  Counter handling per matrix.
- Anchoring counter: ≥3 candidate hypotheses before deep-diving one.
- Strata re-run per matrix (Simpson's/CausalPitfalls countermeasure).
- Exploratory findings labeled as such; confirmatory claims only via the Phase-0
  strategy (m-value-inspired; arXiv 2607.01507).

**Phase 3 — Inference.**
- At decision-grade+: analysis plan (variables, transforms, test, decision rule) written
  before any confirmatory test runs on the confirmation set; deviations logged.
- **Assumption gate before any test** (`assumption_gate.py`): the test is chosen FROM
  the check results — never named first (StatQA countermeasure). Routing: parametric /
  nonparametric (Mann-Whitney, Kruskal-Wallis, permutation) / bootstrap.
- Effect sizes with interpretation + CIs always; a-priori power where applicable;
  post-hoc power banned (sensitivity analysis instead).
- Causal language discipline: associational wording unless an identification strategy is
  declared; rival-hypothesis steelmanning — state what would DISCONFIRM the user's
  hypothesis and test ≥1 rival before endorsing (anti-sycophancy).
- For experiment data: route to installed ab-test-analysis (SRM, power, guardrails);
  statistician's gates (multiplicity, effect sizes, provenance) still apply on top.
  analysis-assumptions-log, if installed, is superseded by the deviation log — do not
  run both.
- **Bayesian route (hybrid)**: vendored condensed workflow (references/bayesian-
  condensed.md): generative model → justified priors → prior predictive BEFORE fitting →
  convergence gate enforced by `bayes_diagnostics.py` (never LLM judgment) → posterior
  predictive → LOO; credible intervals, never point estimates alone. If baygent/
  pymc-labs skills are installed, invoke them instead — **their outputs still pass
  Phase 4 gates** (provenance, multiplicity, inspector).
- Leakage gates for any modeling: split before fitting-dependent preprocessing;
  Kapoor–Narayanan info-sheet (references/leakage-info-sheet.md).
- Baseline integrity: "improvement" claims require re-running the baseline in-session.
  Impossible-result checks, enumerated: rates outside [0,100%], improvement exceeding
  available headroom, n exceeding population, subgroup counts exceeding totals,
  variance ≤ 0, perfect scores on noisy data.

**Phase 4 — Verification.**
- Provenance check (execution-log invariant above).
- `causal_verb_scan.py` on the report draft.
- Repeatability + robustness per matrix.
- **Analyst–inspector = an adversarial-verify invocation** with packet type
  "reproduce-from-plan": the packet is the pre-registered plan + execution log; the
  verifier reproduces the workflow and diffs conclusions. (No duplicated machinery —
  adversarial-review finding 8.) Division of labor: inspector = reproduction fidelity;
  the closing adversarial-verify run = claim audit.
- Feedback discipline: on critique, re-verify against data before changing any answer.

**Phase 5 — Communication.** Route through installed skills (insight-synthesis,
executive-summary-generator, visualization-builder). Every estimate ships with an
interval; evidence-strength tags; uncertainty survives the executive summary (no
de-hedging); limitations include the tier disclosure.

## Benchmark (defined in evals/, run by the repo-level shared harness)

PyMC Labs pattern: 5–8 tasks seeded with documented traps (fan-out join, day/month
dates, non-normal small-n comparison, Simpson's stratification, implicit multi-test scan,
leakage bait, baseline bait). Two-stage scoring: binary viability gate + 0–5 rubric per
dimension, scored by an **LLM judge whose prompt ships with the benchmark** (judge bias
is a stated threat; judge prompt is part of the deliverable). ≥3 replicates per arm.
Report Cohen's d on the with/without delta; **pass^k for the gates** (they are
verifiers); report cost (tokens/turns — rigor isn't free); the report separates the
viability-gate pass rate from graded quality (averaging hides gate gaps). Keep the
no-skill baseline in every run as the obsolescence signal. Fixtures double as
writing-skills RED-phase pressure tests. Shared eval rules:
[evidence-protocol.md](evidence-protocol.md).

## Testing plan

RED baseline (no skill) on fixtures — expected failures per evidence base: test named
before assumptions checked, fan-out join unnoticed, aggregate reported without strata,
every scanned pattern reported as a finding, no intervals, non-runnable notebook.
GREEN: gates catch each seeded trap. REFACTOR: log rationalizations, counter in gates/.

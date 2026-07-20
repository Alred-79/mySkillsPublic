---
name: statistician
description: "Rigorous exploratory data analysis and statistical inference with enforced gates that catch the mistakes LLMs reliably make - applicability errors, silent join fan-out, Simpson's paradox, uncorrected multiple testing, leakage, ungrounded numbers. Runs a goal-conditioned pipeline from profiling through inference to communication, choosing each test FROM its assumption checks rather than naming it first. Use whenever a user points you at data and a question: \"analyze this dataset\", \"is this difference significant\", \"run an A/B test analysis\", \"explore this CSV\", \"what's driving this metric\", \"fit a model to this data\", \"does this correlation hold\", a parquet/SQL table plus a decision to make, or any request to profile, compare groups, test a hypothesis, model, or find drivers. Reach for it even when the user does not say \"statistics\" but is clearly asking a question that data must answer."
---

# statistician

You are doing data analysis the user will act on. The failure mode this skill exists to prevent is the **confident wrong number**: you name a t-test before checking its assumptions, you merge two tables and never notice the row count exploded, you report an aggregate that reverses inside every subgroup, you scan forty correlations and headline the one that cleared p<0.05 by chance, and it all reads fluently while being wrong.

That failure mode is not hypothetical for LLMs - it is the dominant one. On StatQA (arXiv 2406.07815), applicability errors (picking a method whose assumptions the data violates) are the largest error class and the best model scored 64.83%. Analytic-configuration choices flip ~31% of conclusions ("LLM hacking", arXiv 2509.08825). Subgroup blindness is a named pitfall (CausalPitfalls, arXiv 2505.13770). And an o1 case study went 3/10 to 9/10 on Simpson's-paradox decisions from a "careful statistician" directive alone. Directives work. This skill is a system of them, backed by scripts that rule on the numbers before you can rationalize them.

The core discipline, in one line: **every number in the report cites a line in the execution log, every test is chosen from an assumption check, and every gate that the tier demands is passed - not narrated, passed.**

## How to use this skill

Work Phases 0-5 in order. Each phase has a gate table in `gates/phase-N.md` - read that file when you enter the phase; it holds the checkable gates and the failure each one prevents. This SKILL.md carries only the spine: routing, the tier matrix, the two invariants, and pointers. Do not inline the gate tables here; load them per phase so context stays lean.

The rigor **tier** (set in Phase 0) decides how many gates fire. The tier matrix below is the single source of truth for that. Where a phase file and the matrix disagree, **the matrix wins**.

### Invocation

`/statistician [dataset-or-question] [tier]`. With no arguments, operate on the dataset and question already in the conversation. The tier is elicited in Phase 0 (one round); "go ahead" means infer the tier from how the user talks about stakes.

### Data-source routing (resolve in Phase 0)

The source decides which Phase 1 variant you run. Do not start profiling until you know which of these you are in:

- **File (CSV / parquet / Excel / JSON)** - pandas path; all gates as written.
- **Database / SQL** - SQL profiling variant. Read the schema and data dictionary *before writing any analysis SQL* (the Spider 2.0 countermeasure: text-to-SQL accuracy collapses from 86.6% to 10.1% on real unprofiled schemas). Express join audits as SQL row-count and grain assertions run before and after every join.
- **Oversized data** - documented sampling policy. Record the sample's construction as an assertion: method, seed, n, and a coverage check of sample aggregates against full-data aggregates. An unrecorded sample is an unreproducible result.
- **Live notebook state** - snapshot to a linearly executable script *first* (reproducibility invariant below). Analysis run against hidden out-of-order cell state cannot be reproduced or trusted.

### Hybrid dependency rule

Several steps name a companion skill (programmatic-eda, data-quality-audit, ab-test-analysis, insight-synthesis, adversarial-verify, baygent / pymc-labs for Bayesian work). The rule is always: **if that skill is installed, invoke it; otherwise apply the inline procedure given in the phase file.** The named skills are upgrades, not requirements - this skill is self-contained. Never claim you ran a tool you do not have. When you route Bayesian work out to baygent or pymc-labs, their outputs still pass this skill's Phase 4 gates (provenance, multiplicity, inspector).

### Scripts replace judgment

The scripts in `scripts/` exist because the LLM cannot rationalize a number a script has already ruled on. Reach for them at the phase that names them rather than eyeballing:

| Script | Phase | Ruling it makes |
|---|---|---|
| `assumption_gate.py` | 3 | Normality (Shapiro / Anderson), variance homogeneity (Levene), autocorrelation (Durbin-Watson given a time order), duplicate-key detection - then routes parametric / nonparametric / bootstrap. |
| `join_audit.py` | 1 | Pre/post row counts, key uniqueness each side, dtype match, grain assertion (`pandas validate=`). Catches fan-out. |
| `multiplicity_audit.py` | 2 | Reads the test-counter log, applies Benjamini-Hochberg FDR, reports which "findings" survive. |
| `provenance_table.py` | 4 | Builds statistic -> value -> log-line table from `execution.log`; greps the report for numeric tokens lacking an id. |
| `bayes_diagnostics.py` | 3 | ArviZ R-hat / ESS / divergences / LOO verdicts for the vendored Bayesian path. |
| `causal_verb_scan.py` | 4 | Greps a draft for causal verbs lacking a declared identification strategy. |

Each script fails gracefully: if a dependency is missing it prints exactly what to `pip install` rather than faking a verdict. Dependencies are listed in `scripts/requirements.txt`. `join_audit.py`, `multiplicity_audit.py`, `provenance_table.py`, and `causal_verb_scan.py` need only numpy/pandas (or the stdlib) and run today; `assumption_gate.py` needs scipy/statsmodels; `bayes_diagnostics.py` needs arviz.

## The two invariants (all tiers, no exceptions)

These hold at every tier. The tier controls the *gates*, never these.

**Execution-log invariant - provenance by construction.** Run all analysis code through a thin wrapper that appends each result to `execution.log` with an id. `provenance_table.py` then derives a table mapping every statistic to its value and its log line. **Every number in the final report must cite a provenance-table id.** The script greps the report for numeric tokens that lack an id and flags them; the only allowed exceptions are rounded derivations of an already-cited number, each listed explicitly with its justification. This is deterministic on purpose - "reverse-match the prose to the output by reading" is exactly the check LLMs rationalize past, so it is not the check.

**Reproducibility invariant - a runnable artifact.** The analysis is a single linearly executable thing: a top-to-bottom script, or a notebook that produces the same result under restart-and-run-all. Seeds set, library versions pinned. Tiering decides whether the artifact is *re-run and diffed* (repeatability gate), never whether it is runnable. A result you cannot re-execute is not a result.

## Rigor tiers - the tier x gate matrix

Elicited in Phase 0, one round. The final report states the tier **and what was not done because of it** - the tier disclosure is a deliverable, not a footnote. The chosen tier is recorded as a `D` assertion row in the evidence ledger (shared evidence-protocol).

| Gate | quick-look | decision-grade | high-stakes |
|---|---|---|---|
| Goal + KPI elicitation, docs read | required | required | required |
| Data audit + join audits + cleaning evidence | required | required | required |
| Confirmation strategy (holdout or FDR-mode, declared BEFORE Phase 2) | skipped - all findings labeled exploratory | required | required |
| Implicit test counter | count + label ("N patterns scanned, uncorrected") | count + BH-FDR | count + BH-FDR |
| Subgroup / strata re-run of headline findings | 1 stratifier | 2-3 stratifiers | 2-3 + sensitivity to stratifier choice |
| Pre-registered plan + deviation log | skipped (exploratory label instead) | required | required |
| Assumption gate before any test | required | required | required |
| Effect sizes + CIs on every estimate | required | required | required |
| Bayesian twin offered | no | yes | yes |
| Missing-data mechanism diagnosis / MI | flag only | diagnose + MI if MAR | diagnose + MI + MNAR sensitivity |
| Robustness (alternative specifications) | none | >=2 specs | >=3 specs + mini-multiverse |
| Repeatability re-run + conclusion diff | no | 1 fresh re-run | >=2 re-runs |
| Analyst-inspector reproduction | no | yes (via adversarial-verify) | yes |
| adversarial-verify on final claims | optional | required | required (high effort, 3-lens) |

Conflict rule: where a phase gate and this matrix disagree, **the matrix wins**. It is the single source of tier truth.

## The phases

Each phase is a pointer. Read the gate file when you enter the phase; it holds the gate table, the WHY per gate, and the inline fallback for any companion skill you do not have.

**Phase 0 - Goal elicitation + confirmation strategy** (`gates/phase-0.md`). One round of questions. What decision does this inform, confirmatory or exploratory (this sets the tier). Pull KPI definitions from the docs or ask - never improvise a metric, because insight recovery drops from ~60% to ~40% when objectives are ambiguous. Declare the sampling design (clustered / repeated-measures / independent) - `assumption_gate.py` consumes it, and independence is not something a script can infer. Read every supplied data dictionary and restate the extracted rules before touching code. At decision-grade and above, **fix the confirmation strategy here, before any exploration** - a holdout split created now, or FDR-accounting mode with the counter scope frozen. Pre-registering after you have already looked is the forking-paths failure itself. Grep the repo's `data-gotchas.md` at the start: a trap confirmed on this dataset before (grain, timezone, key duplication) is free knowledge.

**Phase 1 - Data audit** (`gates/phase-1.md`). STRATOS IDA discipline. Print evidence at every step: dtypes, null counts, row-count deltas, date min/max, a sample. Check for a day/month swap on every date column. Never coerce silently. Run `join_audit.py` on **every** merge - the fan-out join is the highest-frequency silent corruption in this whole pipeline. Handle missing data per the tier matrix. Produce an IDA note of every cleaning action that could change an interpretation. Write confirmed dataset traps to `data-gotchas.md`.

**Phase 2 - Exploration with multiplicity discipline** (`gates/phase-2.md`). This is the EDA-to-inference bridge. Keep a test counter: a runtime shim counts scriptable tests (scipy.stats calls, correlation-matrix cells), and an honor rule covers the rest - any displayed table with >=2 groups increments the counter by its comparison count. Handle the count per the matrix (label-only at quick-look, BH-FDR above). Force >=3 candidate hypotheses before you deep-dive one, or you are just confirming the first thing you saw. Re-run headline findings across strata (the Simpson's countermeasure). Label exploratory findings as exploratory; a confirmatory claim is only allowed through the Phase-0 strategy.

**Phase 3 - Inference** (`gates/phase-3.md`). At decision-grade+, write the analysis plan (variables, transforms, test, decision rule) before any confirmatory test runs on the confirmation set; log deviations. **Run `assumption_gate.py` before any test and choose the test FROM its output** - never name the test first. This is the single most important gate in the skill: it is the direct countermeasure to the dominant LLM error class. Report effect sizes with interpretation and CIs on everything; a-priori power where it applies; post-hoc power is banned (do a sensitivity analysis instead). Use associational language unless you have declared an identification strategy, and steelman a rival - state what would disconfirm the user's hypothesis and test at least one rival before endorsing (this is the anti-sycophancy gate). For experiment data, route to ab-test-analysis (SRM, power, guardrails) and keep this skill's gates on top. For Bayesian work, follow the vendored condensed workflow or route to baygent / pymc-labs; either way the convergence gate is `bayes_diagnostics.py`, never your own read of the trace. For any modeling, split before any fitting-dependent preprocessing (leakage). "Improvement" claims require re-running the baseline in-session, and every result passes the impossible-value checks (rates in [0,100%], improvement within headroom, n within population, subgroup counts within totals, variance > 0, no perfect scores on noisy data).

**Phase 4 - Verification** (`gates/phase-4.md`). Run the provenance check (execution-log invariant). Run `causal_verb_scan.py` on the draft. Do the repeatability re-run and robustness specs per the matrix. The analyst-inspector step **is** an adversarial-verify invocation with packet type "reproduce-from-plan" (the packet is the pre-registered plan plus the execution log; the verifier reproduces the workflow and diffs conclusions) - do not build separate machinery for it. On any critique, re-verify against the data before you change a single answer.

**Phase 5 - Communication** (`gates/phase-5.md`). Route through insight-synthesis, executive-summary-generator, visualization-builder if installed. Every estimate ships with its interval. Tag evidence strength. Uncertainty must survive into the executive summary - no de-hedging on the way up. Limitations include the tier disclosure: name what the tier did not buy.

## Definition of done

The report states its tier and what the tier skipped; every number in it cites a provenance id (exceptions listed); every test was chosen from an assumption check; the join audits, multiplicity handling, strata re-runs, and adversarial-verify demanded by the tier all ran and are recorded; the artifact re-executes top-to-bottom; and the uncertainty is still visible in the summary. Anything short of that is a draft, not a finding.

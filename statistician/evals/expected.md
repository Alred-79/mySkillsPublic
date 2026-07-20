# Expected results - statistician evals

Ground truth for the `evals/` cases and the seeded-trap fixtures. The three cases in
`evals.json` exercise a subset of the traps directly; the full fixture set (seven traps)
ships so the skill can be pressure-tested against each documented AI failure mode, and so
these fixtures double as the writing-skills RED-phase tests.

All fixtures are generated deterministically by `fixtures/make_fixtures.py` (seed 20260720),
so the numbers below are exact and reproducible. Regenerate with `python make_fixtures.py`.

## The traps, decoded

Each trap corresponds to a gate in the skill and a documented failure mode in the spec's
evidence base. The "expected catch" is what a passing run must do; the script named is the
deterministic judgment-replacer that rules on it.

### Trap 1 - fan-out join (`orders.csv` + `customers_regions.csv`)

`orders.csv` is 1 row per order (8 orders, true total revenue **815**). `customers_regions.csv`
has **duplicate** `customer_id` rows (a customer appears once per shipping region), so customers
1 and 3 each have two region rows. A `left` join on `customer_id` fans out: their 4 orders
double, giving **12 rows** and an inflated revenue of **1275**.

- **Expected catch:** run `join_audit.py` (Phase 1 gate) before trusting the merge. It must
  report: right key not unique, rows 8 -> 12, `order_id` grain broken. The analysis must NOT
  report 1275 as real revenue.
- **Failure mode:** silent join fan-out (the highest-frequency silent corruption in a pipeline).
- **Verify:** `python scripts/join_audit.py --left evals/fixtures/orders.csv --right evals/fixtures/customers_regions.csv --on customer_id --how left --grain order_id` -> VERDICT: FAIL.

### Trap 2 - day/month date ambiguity (`events_ddmm.csv`)

Dates are written `DD/MM/YYYY`. A naive `MM/DD` parse silently mangles rows where day<=12 and
misreads the rest. The values `13/01/2024` and `25/12/2023` are unambiguous DD/MM tells (no
13th or 25th month), so a correct reader must detect the format, not assume US ordering.

- **Expected catch:** Phase 1 day/month swap check. Detect that day values exceed 12, conclude
  DD/MM, and parse accordingly (or flag the ambiguity and ask). No silent US-format coercion.
- **Failure mode:** locale-flipped date parse corrupting a third of rows.

### Trap 3 - non-normal small-n comparison (`small_n_groups.csv`)

Two groups, **n=12 each**, drawn from a right-skewed lognormal with a fat outlier in group A
(skew ~1.72). A Student's t-test is the wrong instinct here.

- **Expected catch:** run `assumption_gate.py` (Phase 3 central gate) and let it route. Normality
  fails / n is small, so the route is nonparametric (Mann-Whitney) or bootstrap - chosen FROM the
  check, never named first. An effect size with a CI ships regardless.
- **Failure mode:** the applicability error (StatQA's dominant LLM error class).
- **Verify (needs scipy):** `python scripts/assumption_gate.py evals/fixtures/small_n_groups.csv --value response --group group` -> routes off parametric.

### Trap 4 - Simpson's paradox (`simpsons_recovery.csv`)

Aggregate recovery: **control 0.783 vs treatment 0.458** (control looks far better). But within
every severity stratum, treatment wins: **mild 0.95 vs 0.89**, **severe 0.36 vs 0.25**. Treatment
was concentrated in severe patients (100 severe treated vs 20 severe control), which drags its
aggregate down. The aggregate conclusion is the exact opposite of the truth.

- **Expected catch:** Phase 2 strata re-run of the headline finding. Detect the reversal, report
  it as the headline, and name severity as the confounder. Do NOT report "treatment is worse."
- **Failure mode:** subgroup blindness (CausalPitfalls); the o1 3/10 -> 9/10 case.

### Trap 5 - implicit multi-test bait (`multitest_features.csv` + `multitest_counter.log`)

20 candidate features vs a binary outcome, **all pure noise** (outcome is independent of every
feature). Scanning "which feature predicts outcome" surfaces ~1-2 spurious p<0.05 by chance. The
pre-baked counter log holds the 20 p-values; **2 clear naive p<0.05, 0 survive** Benjamini-Hochberg.

- **Expected catch:** Phase 2 test counter + `multiplicity_audit.py`. Report that the naively
  significant features do NOT survive FDR correction, so they are not findings.
- **Failure mode:** garden of forking paths / reporting the winner of many uncounted tests.
- **Verify:** `python scripts/multiplicity_audit.py evals/fixtures/multitest_counter.log` -> 2 naive, 0 survive, VERDICT flags the gap.

### Trap 6 - leakage bait (`churn_leakage.csv`)

`days_since_cancellation` is populated **only when `churned==1`** and NaN otherwise. It is a
downstream consequence of the label, not a feature available at prediction time. Including it
gives near-perfect accuracy - textbook target leakage.

- **Expected catch:** Phase 3 leakage gate (`references/leakage-info-sheet.md`). Identify the
  column as a target proxy, exclude it, and apply split-before-preprocessing discipline for any
  model. A suspiciously high accuracy is treated as a leak to disprove, not a success.
- **Failure mode:** the Kapoor-Narayanan leakage taxonomy (>=294 papers).

### Trap 7 - baseline bait (`model_scores.csv`)

A "new model" vs an "old model" on 500 labeled rows. The old model's true accuracy is **0.774**
and the new model's is **0.810** - a real but modest ~3.6-point lift. A prompt that claims a
dramatic improvement must be checked by re-running the baseline in-session; the claimed lift
should shrink to the true one.

- **Expected catch:** Phase 3 baseline integrity gate. Re-run the baseline (do not quote a
  remembered number), report the true delta with its uncertainty, and run the impossible-value
  checks (accuracy in [0,1], improvement within headroom).
- **Failure mode:** unfalsifiable "X% better" claims against a baseline never actually run.

## Cross-cutting gates (should hold on every case)

- **Provenance:** every number in the report cites a provenance id; `provenance_table.py` finds no
  ungrounded numbers. Verify the mechanism on the shipped example in the script's docstring.
- **Causal language:** `causal_verb_scan.py` finds no causal verb without a declared identification
  strategy. None of the fixture prompts describe a randomized design, so causal claims are unearned.
- **Tier disclosure:** the report states its tier and what the tier did not buy.
- **Reproducibility:** the analysis is a single top-to-bottom runnable artifact with a seed set.

## What a no-skill baseline typically gets wrong

Kept here because the baseline is the obsolescence signal - when it stops failing these, the skill
has stopped adding value (evidence base: StatQA, LLM-hacking, CausalPitfalls, Kapoor-Narayanan):

- Merges `orders` and `customers_regions` and reports the inflated 1275 without noticing the row
  count changed.
- Reaches for a t-test on the n=12 skewed groups without checking normality.
- Reports the Simpson's aggregate ("treatment is worse") and never stratifies.
- Calls the 2 naively-significant noise features "drivers of churn."
- Trains on `days_since_cancellation`, gets ~perfect accuracy, and reports it as a great model.
- Repeats a claimed improvement over the old model without re-running the old model.
- Writes causal prose ("X drives churn") from observational data, and drops the intervals on the
  way to the summary.

## Judge

Subjective dimensions (did the write-up communicate the uncertainty, was the tier disclosure
meaningful) are scored by the rubric judge in `judge/rubric.md`. Objective catches (the six
verifiable script verdicts and the fixture arithmetic above) are checked directly - script exit
codes and value matches, not judgment.

# Phase 3 - Inference

The purpose of Phase 3 is to answer the question with a test whose assumptions the data actually satisfies, an effect size the user can act on, and language that does not overclaim causation. The failure this phase prevents is the dominant LLM statistical error: **naming the test before checking whether the data supports it** (StatQA, arXiv 2406.07815 - applicability errors are the largest error class, best model 64.83%). The countermeasure is mechanical: choose the test FROM the assumption check, never the reverse.

## The central gate: assumption check chooses the test

Run `assumption_gate.py` before any test. It checks normality (Shapiro / Anderson), variance homogeneity (Levene), autocorrelation (Durbin-Watson, given the declared time order), and duplicate keys, then prints a verdict that routes you:

- assumptions hold -> **parametric** (t-test, ANOVA, OLS)
- normality violated (esp. small n) -> **nonparametric** (Mann-Whitney, Kruskal-Wallis, permutation)
- messy / small / weird -> **bootstrap** the statistic and its CI

You do not pick the branch. The script picks it from the data. Independence is the one assumption it cannot fully check - it consumes the sampling design you declared in Phase 0, and if the design is clustered or repeated-measures, standard tests are wrong regardless of what the other checks say.

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Pre-registered plan (decision-grade+)** | Before any confirmatory test runs on the confirmation set, write the plan: variables, transforms, test, decision rule. Log every deviation. | Choosing the test after seeing the confirmation-set result is p-hacking with extra steps. |
| **Assumption gate before every test** | `assumption_gate.py` runs first; the test is whatever it routes to. | The applicability error - the dominant LLM failure. A t-test on non-normal small-n data is confidently wrong. |
| **Effect sizes + CIs always** | Every estimate ships with an effect size (Cohen's d, odds ratio, r, etc.), its plain-language interpretation, and a confidence interval. | "p < 0.05" with no effect size hides whether the effect is trivially small. A CI shows the range the data is actually consistent with. |
| **Power done right** | A-priori power where applicable. **Post-hoc (observed) power is banned** - do a sensitivity analysis (what effect could this n have detected?) instead. | Post-hoc power is a deterministic function of the p-value; it adds nothing and misleads. |
| **Causal-language discipline** | Associational wording ("is associated with") unless you have declared an identification strategy (see `references/causal-verb-list.md`). | "X drives Y" from observational data is an unearned causal claim. The verbs that assert causation need a design that supports them. |
| **Rival-hypothesis steelmanning** | State what would DISCONFIRM the user's hypothesis, and test >=1 rival explanation before endorsing theirs. | Sycophancy. Confirming the hypothesis the user clearly wants, without seriously trying to break it, is the anti-pattern this gate exists for. |
| **Leakage control (any modeling)** | Split the data before any fitting-dependent preprocessing (scaling, imputation, feature selection, target encoding). See `references/leakage-info-sheet.md`. | Preprocessing on the full dataset leaks test information into training; the Kapoor-Narayanan taxonomy documents this across >=294 papers. |
| **Baseline integrity** | An "improvement" claim requires re-running the baseline in-session, not quoting a remembered number. | "20% better than before" against a baseline you never actually ran is unfalsifiable. |
| **Impossible-value checks** | Enumerate and check: rates in [0,100%], improvement within available headroom, n within population, subgroup counts within totals, variance > 0, no perfect scores on noisy data. | These catch join fan-out, double-counting, and unit errors that produce numerically impossible results that still read fine in prose. |

## Experiment data

If the data is from an experiment (A/B test), route to `ab-test-analysis` (SRM check, power, guardrail metrics) under the hybrid rule. This skill's gates stay on top: multiplicity, effect sizes, provenance still apply. If `analysis-assumptions-log` is installed, it is superseded by the deviation log here - do not run both.

## Bayesian route (hybrid)

If `baygent` or `pymc-labs` skills are installed, invoke them - their outputs still pass Phase 4 gates. Otherwise use the vendored condensed workflow in `references/bayesian-condensed.md`:

generative model -> justified priors -> **prior predictive check BEFORE fitting** -> convergence gate via `bayes_diagnostics.py` (R-hat, ESS, divergences - never your own read of the trace) -> posterior predictive check -> LOO. Report credible intervals, never point estimates alone.

The convergence gate is `bayes_diagnostics.py`, not LLM judgment. A model that has not converged produces confident garbage; only the diagnostic script may certify it.

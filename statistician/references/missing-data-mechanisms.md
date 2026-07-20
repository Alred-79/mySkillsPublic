# Missing-data mechanisms

Load in Phase 1 when a column has missingness and the tier is decision-grade or above (quick-look flags only). The mechanism determines whether dropping rows is safe or biasing. Complete-case-by-default is a silent, common error: it is only valid under MCAR, which is the rarest case.

## The three mechanisms

| Mechanism | Definition | Can you drop rows? | Handling |
|---|---|---|---|
| **MCAR** (completely at random) | Missingness is independent of everything, observed and unobserved. A dropped sensor reading. | Yes - complete-case is unbiased, just less powerful. | Complete-case is acceptable. Still consider MI for power. |
| **MAR** (at random) | Missingness depends only on *observed* variables. Older users skip an income field, and you observe age. | No - complete-case biases. | **Multiple imputation** (MICE), using the observed variables that predict missingness. |
| **MNAR** (not at random) | Missingness depends on the *unobserved* value itself. High earners hide their income *because* it is high. | No - and MI alone does not fix it. | MI plus an **MNAR sensitivity analysis**: model plausible non-random mechanisms and show how much the conclusion moves. |

## How to diagnose (you cannot fully prove it, but you can rule things out)

- **Test against observed variables.** Create a missingness indicator and check whether it is associated with other observed columns. Association -> not MCAR (it is at least MAR).
- **No association with observed variables** is consistent with MCAR but does not prove it - the dependence could be on the unobserved value (MNAR), which is untestable from the data alone. This is why MNAR needs domain reasoning and a sensitivity analysis, not a test.
- **Use domain knowledge for MNAR.** Whether "income missing because income is high" is plausible is a question about the world, not the dataframe. Ask it explicitly.

## Multiple imputation, briefly

Impute each missing value multiple times (m >= 5) to reflect the uncertainty of the imputation, fit the analysis on each completed dataset, and pool the results with Rubin's rules. Single imputation (mean-fill) understates uncertainty by pretending the imputed values are known - it produces intervals that are too narrow.

## Tier mapping (from the matrix)

- quick-look: flag the missingness and its rate, no imputation.
- decision-grade: diagnose the mechanism, multiply-impute if MAR.
- high-stakes: the above plus an MNAR sensitivity analysis.

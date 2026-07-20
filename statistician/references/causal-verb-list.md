# Causal-verb list and identification strategies

Load in Phase 3 (causal-language discipline) and Phase 4 (`causal_verb_scan.py` uses this list). The rule: **associational language by default; a causal verb is licensed only by a declared identification strategy.** Observational correlation does not earn "causes".

## The banned-without-a-strategy verbs

`causal_verb_scan.py` greps report drafts for these. Each occurrence must either sit behind a declared identification strategy or be rewritten:

- drives, driver of
- causes, caused by
- leads to
- results in
- because of, due to
- increases / decreases / raises / lowers / boosts / reduces (when asserting one variable moves another)
- impact of, effect of, influences
- makes (as in "X makes Y happen")

## The associational replacements

| Causal (needs a strategy) | Associational (always allowed) |
|---|---|
| X drives Y | X is associated with Y |
| X causes a 5% increase in Y | Y is 5% higher when X is present |
| The effect of X on Y | The relationship between X and Y |
| X leads to Y | X predicts Y / X co-occurs with Y |
| Because of X, Y rose | Y rose alongside X |

## What counts as a declared identification strategy

A causal verb is licensed if the analysis rests on one of these, stated explicitly:

- **Randomized experiment** - treatment was randomly assigned (an A/B test with a clean SRM check). The gold standard; randomization handles confounders you did not measure.
- **Difference-in-differences** - a treated and a control group, before and after, with a defended parallel-trends assumption.
- **Regression discontinuity** - assignment is determined by a threshold on a running variable, and you analyze near the cutoff.
- **Instrumental variable** - an instrument that moves the treatment but affects the outcome only through it (relevance + exclusion, both argued).
- **Controlled observational design with a stated DAG** - you name the confounders, justify that the measured set is sufficient for adjustment (backdoor criterion), and acknowledge the assumption is unfalsifiable from the data.

If none of these is declared, the claim is associational and the verb must change. "We controlled for a few things in a regression" is not, by itself, an identification strategy - regression adjustment only removes confounding from the confounders you actually measured and modeled correctly.

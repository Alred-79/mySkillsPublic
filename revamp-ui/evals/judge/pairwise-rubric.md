# Judge: blind pairwise screenshot rubric

Used for Tier-2 qualitative scoring of a revamp (evals/expected.md), following the anthropics/skills PR #210 protocol: bank of before-states, revamp vs baseline, screenshots, anonymized A/B to a judge, order-swapped, binomial test on decisive wins. This is judgment, not golden-output matching, so it scores fit-to-brief and never similarity-to-any-reference.

## Inputs to the judge

- **The brief** (the eval prompt) and **the target dial** the brief implies (from the contract or the case's expected.md).
- **Two screenshots, A and B**, one from the with-skill arm and one from the baseline arm, provenance stripped. The judge is NOT told which is which.
- Desktop and mobile captures where available.

## Judge-bias mitigations (mandatory, per evidence-protocol.md)

1. **Order swap.** Run every pair twice with A and B swapped. Count only verdicts that stay consistent across the swap; a verdict that flips with order is discarded as position bias.
2. **Anonymize provenance.** Never reveal which arm produced which image. No filenames, no "the skill version".
3. **Allow "Unknown".** If neither is clearly better on a dimension, the judge returns Unknown rather than guessing. Unknown is a real outcome, not a failure to score.
4. **Isolate per dimension.** Score each dimension independently; do not let a strong Aesthetic score halo the UX score.
5. **Instruct on verbosity / polish bias.** More elements or more animation is not automatically better. Judge against the brief's dial: for a calm brief, restraint IS the win; more motion is a loss.
6. **Periodic human calibration.** Spot-check a sample of verdicts against a human to catch judge drift.

## Dimensions (score each: A better / B better / Unknown, with one line of why)

1. **Prompt Adherence.** Which better delivers what the brief actually asked for, at the intensity the dial implies? This dimension is what keeps divergence-from-brief from winning: a beautiful maximal page loses here against a calm brief.
2. **Aesthetic Fit.** Which better fits the stated aesthetic family and audience? Not "which is prettier in the abstract" - which is right for THIS product.
3. **Visual Polish.** Type, spacing, hierarchy, alignment, restraint of effects. Craft quality.
4. **UX.** Clarity, scannability, obvious affordances, hierarchy of attention.
5. **Creative Distinction.** How far it escapes the generic-AI-template look, in a way that still serves the brief. **Divergence is a scored criterion here, not a penalty.** A brave, brief-appropriate direction beats a safe, templated one. But distinction that fights the brief (a wild layout on a calm editorial brief) does NOT score here - it loses Prompt Adherence, and this dimension rewards distinction *in service of* the brief, never novelty for its own sake.

## Anti-Goodhart

Creative Distinction and Prompt Adherence are separate axes and BOTH must hold. High Distinction with low Adherence is off-brief flair and loses overall. High Adherence with zero Distinction is a competent-but-generic result. The win is the design that is both on-brief and distinctive; this is why the two are scored independently rather than merged.

## Aggregation

Per dimension, count decisive wins (order-consistent, non-Unknown) for each arm and run a binomial test on the with-skill arm's win rate. Report the win rate and p-value per dimension and overall. The reference bar from PR #210 was ~75% win rate at p=0.006 over ~30 comparisons; treat that as the target signal, not a hard threshold.

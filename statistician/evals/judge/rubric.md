# Statistician eval judge - rubric prompt

You are grading one statistical analysis produced for a fixed prompt against a fixed dataset.
Grade only what is in front of you. This prompt ships with the benchmark on purpose: the judge
is itself a source of bias, so its instructions are part of the deliverable and are auditable.

## Two-stage scoring

**Stage 1 - viability gate (binary).** Before any quality score, decide: is this a usable,
non-broken analysis that a competent analyst would accept as a starting point? A run that fabricated
numbers, reported an impossible result, or never actually addressed the question fails the gate and
scores 0 on every dimension. Report the viability-gate pass rate SEPARATELY from the graded quality -
averaging them hides gate gaps.

**Stage 2 - rubric (0-5 per dimension).** Only for runs that pass the gate. Score each dimension
independently; do not let a strong dimension inflate a weak one.

## Dimensions

Score each 0-5 (0 = absent/wrong, 3 = adequate, 5 = exemplary). Some dimensions are objective enough
that you should verify them against the ground truth in `../expected.md` rather than judging - where a
trap has a script verdict or an exact number, check it, do not opine.

1. **Trap catches (objective - verify, do not judge).** Did the run catch the traps its prompt
   plants? Score by the fraction of the case's expected catches in `../expected.md` that were made.
   The fan-out (rows 8->12), the Simpson's reversal (treatment wins every stratum), the FDR result
   (0 of 2 survive), and the leakage column are exact - credit only if actually caught.

2. **Test appropriateness.** Was the statistical test chosen FROM an assumption check rather than
   named first? A t-test on the n=12 skewed data is a fail here even if the p-value is "right".

3. **Uncertainty communication.** Does every estimate carry an interval, and does the uncertainty
   survive into the summary (no de-hedging)? A bare point estimate or a summary that drops the CIs
   loses points even if the body was careful.

4. **Causal discipline.** Is the language associational unless an identification strategy is declared?
   None of the fixture prompts describe randomization, so any "X drives/causes Y" is unearned.

5. **Tier and provenance.** Is the rigor tier stated with what it did not buy, and does every number
   trace to the analysis (no orphan figures in the prose)?

## Judge-bias mitigations (follow all of these)

These exist because LLM judges have measurable, correctable biases. Skipping them makes the score
untrustworthy.

- **Order swap.** When comparing two runs (with-skill vs baseline), grade them in BOTH orders (A-then-B
  and B-then-A) and count only verdicts that are consistent across both orders. An order-dependent
  verdict is discarded.
- **Anonymize provenance.** Do not be told, and do not infer, which run had the skill. Judge the
  artifact, not its origin.
- **Verbosity is not quality.** A longer analysis is not a better one. Reward the correct catch and the
  honest hedge; do not reward volume. A terse run that caught every trap beats a verbose one that missed.
- **"Unknown" is allowed.** If the evidence in the artifact does not let you decide a dimension, score
  it Unknown rather than guessing. Unknown is a real outcome, not a middling score.
- **One dimension at a time.** Judge each dimension in isolation. Do not let a run's fluent writing
  raise its trap-catch score, or a missed trap lower its writing score.
- **Human calibration.** Periodically, a human re-grades a sample of the judge's verdicts; persistent
  disagreement is a signal to revise this rubric, not the runs.

## Output format

For each run, emit:

```
viability_gate: pass | fail   (one-line reason)
dimensions:
  trap_catches:            <0-5 | Unknown>  (which expected catches were/were not made)
  test_appropriateness:    <0-5 | Unknown>
  uncertainty_comms:       <0-5 | Unknown>
  causal_discipline:       <0-5 | Unknown>
  tier_and_provenance:     <0-5 | Unknown>
notes: <one or two sentences, specific>
```

Do not compute a single overall number here - the aggregator combines dimensions across replicates
and reports the with/without delta (Cohen's d on the uplift) and pass^k on the gate dimensions.

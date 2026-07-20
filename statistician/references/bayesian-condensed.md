# Bayesian workflow (condensed)

Load this only on the Bayesian route (Phase 3), and only when `baygent` / `pymc-labs` are NOT installed - if they are, use them instead and bring their output back through Phase 4. This is the vendored fallback, condensed from Gelman et al.'s Bayesian workflow (arXiv 2011.01808). The convergence gate is `bayes_diagnostics.py`, never your own read of the trace.

## The steps, in order

1. **Generative model.** Write the data-generating story explicitly: what produces each observation, which parameters govern it, what likelihood family fits. State it before you touch a sampler.

2. **Justified priors.** Every prior gets a one-line justification tied to domain knowledge or a defensible weakly-informative default. "Flat because I didn't think about it" is not a justification. Note the scale - a prior that is wide on the wrong scale is informative in the wrong direction.

3. **Prior predictive check - BEFORE fitting.** Simulate data from the priors alone and check it is physically plausible (no negative counts, no rates above 1, magnitudes in a sane range). This catches broken priors before the data can mask them. Doing it after fitting defeats the point.

4. **Fit, then the convergence gate.** Sample, then run `bayes_diagnostics.py`. It rules on:
   - **R-hat** - must be < 1.01. Above that, chains have not mixed; the posterior is not trustworthy.
   - **ESS** (bulk and tail) - too low means the effective sample is too small to summarize the posterior reliably.
   - **Divergences** - more than a handful means the sampler could not explore the geometry; the result is biased. Reparameterize or raise `target_accept`.
   Do not summarize a posterior the script has not cleared. A non-converged model produces confident nonsense.

5. **Posterior predictive check.** Simulate from the fitted posterior and compare to the observed data. Systematic misfit means the model is wrong even if it converged.

6. **LOO / model comparison.** Use LOO-CV (`bayes_diagnostics.py` surfaces Pareto-k warnings) to compare models honestly. High Pareto-k values flag observations the LOO approximation handles badly - do not compare on a metric the diagnostics say is unreliable.

## Reporting

Report **credible intervals, never point estimates alone**. A posterior mean with no interval throws away the entire reason to go Bayesian. State the prior sensitivity: if a defensible alternative prior moves the conclusion, that is a finding, not a detail.

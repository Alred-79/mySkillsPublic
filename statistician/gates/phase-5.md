# Phase 5 - Communication

The purpose of Phase 5 is to deliver the finding without laundering out the uncertainty on the way to the executive. The failure it prevents is de-hedging: the analysis was appropriately cautious, and then the summary rounded "a 3% lift, 95% CI [-1%, 7%], exploratory" up to "we grew 3%." The number survived; the honesty did not.

Route through installed skills under the hybrid rule: `insight-synthesis`, `executive-summary-generator`, `visualization-builder`. If none are installed, the gates below are the procedure.

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Every estimate ships with its interval** | No point estimate travels alone; each carries its CI or credible interval. | A bare number implies a precision the data does not have. The interval is the honest width. |
| **Evidence-strength tags** | Tag each claim with its strength (confirmatory vs exploratory, effect size, whether it survived multiplicity correction and stratification). | The reader cannot weigh a finding they cannot see the strength of. A pre-registered confirmatory result and a scanned exploratory pattern must not read identically. |
| **Uncertainty survives the summary** | The hedges in the body appear in the executive summary too. No de-hedging on the way up. | The most-read part of the report is the summary; that is exactly where uncertainty gets quietly dropped. If it is uncertain in the body, it is uncertain in the summary. |
| **Tier disclosure in limitations** | State the tier and what it did not buy: the robustness specs you skipped, the re-runs you did not do, the Bayesian twin you did not fit. | The reader is entitled to know the rigor level they are acting on. "Quick-look, so no multiplicity correction and single-strata only" is a limitation, not a footnote. |
| **Stratification reversals reported** | Any finding that reversed or vanished under stratification (Phase 2) is stated plainly, not buried. | The Simpson's reversal is the most decision-relevant thing you found; burying it defeats the whole exercise. |

## Note

The tier disclosure is a deliverable, promised since Phase 0. It is not an apology - it is the scope contract. Naming what the analysis did not do is what lets the user trust what it did do.

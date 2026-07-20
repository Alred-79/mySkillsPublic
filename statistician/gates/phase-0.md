# Phase 0 - Goal elicitation + confirmation strategy

The purpose of Phase 0 is to make every downstream choice non-arbitrary: the tier, the metric definitions, the sampling model, and - at decision-grade and above - the confirmation strategy that must be fixed **before** you look at the data. Skipping this phase is how analyses drift into forking paths and improvised KPIs.

Do this in **one round** of questions. If the user says "go ahead" or otherwise waves you on, infer the tier from how they talk about stakes (a board decision is high-stakes; a curiosity is quick-look) and proceed - state the tier you inferred.

## Start-of-run: grep prior knowledge

Before anything else, grep the working repo's `data-gotchas.md` (shared evidence-protocol memory file). A trap confirmed on this dataset in a prior session - grain, timezone, a duplicated key, a metric-definition quirk - is knowledge you get for free. If the file does not exist, skip; Phase 1 and Phase 4 create and append to it.

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Decision framing** | Name the decision this analysis informs, in one sentence. Classify confirmatory vs exploratory. | Analysis with no decision behind it optimizes nothing; the confirmatory/exploratory split is what licenses (or forbids) causal and significance claims later. |
| **Tier set** | Set the rigor tier (quick-look / decision-grade / high-stakes) from the framing and stakes. Record it as a `D` assertion row. | The tier drives the whole gate matrix. An unset tier means gates fire arbitrarily. |
| **KPI definitions grounded** | Pull every metric definition from the supplied docs, or ask. Never improvise a definition. | Insight recovery drops from ~60% to ~40% when objectives are ambiguous. "Active user" and "conversion" have five definitions each; guessing one silently picks a different answer. |
| **Sampling design declared** | State whether observations are independent, clustered, or repeated-measures. | `assumption_gate.py` consumes this. Independence is not inferable from a dataframe - clustered or repeated data breaks the standard-error math of most tests, and only you can know the design. |
| **Docs read and restated** | Read ALL supplied documentation and data dictionaries before writing code. Restate the extracted rules back. | The DABstep implicit-rule failure: models skip the rules doc and violate constraints that were written down. Restating proves you read them. |
| **Confirmation strategy fixed (decision-grade+)** | Before any exploration: either create a holdout split now, or declare FDR-accounting mode with the test-counter scope frozen. | Pre-registration *after* exploration is the forking-paths failure itself (adversarial-review finding 1). Once you have seen the data, you cannot un-see it; the strategy has to predate the looking. |

## Notes

- **"go ahead" handling.** Inferring the tier is allowed; inferring a metric definition is not. If the metric is genuinely ambiguous and undocumented, that is the one thing worth a second question.
- **The tier disclosure starts here.** Whatever the tier skips (per the matrix) is what the final report must disclose. Note it now so Phase 5 has it.
- **Confirmatory means confirmatory.** If the user wants a yes/no decision on a specific hypothesis, that is confirmatory and needs the Phase-0 strategy. If they want to know "what's interesting in here", that is exploratory - and every finding ships labeled exploratory, no significance stars.

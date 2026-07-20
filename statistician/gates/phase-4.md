# Phase 4 - Verification

The purpose of Phase 4 is to try to break your own result before the user does. The failure it prevents is the analysis that is internally fluent but wrong: a number in the prose that no code produced, a causal verb with no design behind it, a conclusion that would not survive a fresh re-run. Verification here is deterministic where it can be and adversarial where it must be.

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Provenance check** | Run `provenance_table.py`. Every number in the report cites a provenance-table id; the script flags any numeric token without one. The only allowed exceptions are rounded derivations of an already-cited number, each listed with justification. | The ungrounded number - a figure that appears in the prose but traces to no line in `execution.log`. Reading the prose to match it by eye is the check LLMs rationalize past, so the check is a grep, not a read. |
| **Causal-verb scan** | Run `causal_verb_scan.py` on the report draft. Every causal verb ("drives", "causes", "leads to", "because of", "results in") must have a declared identification strategy or be rewritten to associational language. | Causal overclaim slips into prose even when the analysis was careful. A grep catches the verb the writing smuggled in. |
| **Repeatability re-run (per tier)** | decision-grade: one fresh re-run of the full artifact, diff the conclusions. high-stakes: >=2 re-runs. | Run-to-run variance dominates LLM EDA (deepsense). A conclusion that changes when you re-run the same analysis was never stable. |
| **Robustness (per tier)** | decision-grade: >=2 alternative specifications. high-stakes: >=3 + a mini-multiverse. | A result that holds under one specification and collapses under a defensible alternative is fragile; the user should know that before deciding. |
| **Analyst-inspector reproduction** | An `adversarial-verify` invocation with packet type "reproduce-from-plan": the packet is the pre-registered plan + `execution.log`; the verifier reproduces the workflow and diffs conclusions. | Self-review misses what the author is blind to. Reproduction fidelity is the inspector's job; do not build separate machinery for it (adversarial-review finding 8). |
| **Feedback discipline** | On any critique, re-verify against the data before changing any answer. | Flipping an answer to appease a critic, without re-checking, replaces one unverified claim with another. |

## Division of labor

- **Analyst-inspector run** (this phase) = reproduction fidelity: does the workflow, re-run from the plan and log, reach the same conclusions?
- **Closing adversarial-verify run** (the tier's final-claims gate) = claim audit: are the specific claims in the report each supported?

They are the same tool (`adversarial-verify`) pointed at two different questions. If the skill is not installed, do the inline version of each: for reproduction, re-execute the artifact from a clean state and diff; for the claim audit, re-read each claim as a hostile reviewer asking "what evidence supports exactly this sentence, and what input would make it false?"

## Note

Because the analyst-inspector step and the shared evidence-protocol ledger use the same assertion format, `adversarial-verify` can audit the ledger directly - it does not need a translation layer. Hand it the ledger and the execution log.

# Phase 2 - Exploration with multiplicity discipline

The purpose of Phase 2 is the EDA-to-inference bridge: explore freely, but count every comparison you make so the exploration cannot silently become a fishing expedition. The failure this phase prevents is the classic garden of forking paths - scan forty relationships, headline the one that cleared p<0.05, and report it as if it were the only test you ran. (Concept prior art: the "Agentic Garden of Forking Paths" m-value, arXiv 2607.01507.)

## The test-counter mechanism

You cannot correct for tests you did not count, and you will not remember them honestly after the fact, so count them as you go.

- **Scriptable tests - runtime shim.** Wrap `scipy.stats` calls and count them. A correlation matrix counts as its number of off-diagonal cells (a 10x10 `.corr()` is 45 comparisons, not one). Each increment appends to the test-counter log that `multiplicity_audit.py` reads.
- **Uninstrumentable tests - honor rule.** For visual and manual comparisons the shim cannot see, apply a stated rule: **any displayed table or chart with >=2 groups increments the counter by its number of pairwise comparisons.** Eyeballing a bar chart of 8 segments for "the tall one" is 28 implicit comparisons.

Handle the count per the tier matrix:

| Tier | Handling |
|---|---|
| quick-look | Count and label: "N patterns scanned, uncorrected - findings are exploratory." No correction, but the count is disclosed so no finding masquerades as confirmatory. |
| decision-grade / high-stakes | Count, then run `multiplicity_audit.py` for Benjamini-Hochberg FDR. Report which findings survive correction and which do not. |

## Gates

| Gate | Requirement | The failure it prevents |
|---|---|---|
| **Test counter running** | The counter (shim + honor rule) is active from the first comparison. | Retroactive counting is guessing. The count has to accumulate live. |
| **Multiplicity handled per tier** | Label-only (quick-look) or BH-FDR (decision-grade+). | Reporting the winner of 40 uncounted tests as a single significant finding - the forking-paths failure. |
| **Anchoring counter** | Generate >=3 candidate hypotheses before deep-diving any one. | Latching onto the first pattern you notice and confirming it. Breadth before depth. |
| **Strata re-run of headline findings** | Re-run every headline finding within strata (per tier: 1 stratifier at quick-look, 2-3 above). | Simpson's paradox / subgroup blindness (CausalPitfalls). An aggregate can point the opposite way inside every subgroup; you only see it if you stratify. |
| **Exploratory labeling** | Label exploratory findings as exploratory. A confirmatory claim is allowed only through the Phase-0 confirmation strategy. | Laundering an exploratory pattern into a confirmatory claim without the pre-registered strategy that would justify it. |

## Note

If a headline finding reverses or vanishes under stratification, that reversal *is* the finding - carry it to Phase 3 and Phase 5, do not bury it. A stratifier that flips the sign of an effect is the single highest-value thing this phase can surface.

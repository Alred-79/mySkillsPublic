# Hypothesis Ledger - <one-sentence bug restatement>

Task: <what is being debugged, and the repo/path>
Pass/fail command: `<the deterministic command that fails now and passes when fixed>`
Bug class: <logic | regression | flaky-timing | performance | memory | build-CI | environment-config | security-shaped>
Started: <date>

This ledger uses the shared evidence-protocol assertion format. Hypotheses take the `H` prefix.
The rule that makes it trustworthy: **prediction before observation.** Fill the `predicted observation`
for a row *before* you run its experiment. The `evidence` field then records predicted-vs-actual - a row
whose prediction was written after peeking proves nothing.

No row reaches a terminal status (`verified` / `refuted` / `disputed` / `unverifiable`) without a citation
in `evidence`: a `file:line`, a command plus its output summary, or a log excerpt. `unverifiable` is a real
finding (no evidence either way), never a quiet pass.

## Hypotheses

| id | assertion (mechanism) | predicted observation | status | evidence (predicted vs actual) | risk |
|----|-----------------------|-----------------------|--------|--------------------------------|------|
| H1 | <a concrete, checkable mechanism for the bug> | <what you expect to see in logs/state if H1 is the cause> | proposed | <fill after experiment: predicted X, observed Y, at file:line / command> | high\|med\|low |
| H2 | <a genuinely different mechanism> | <its distinct predicted observation> | proposed | | |
| H3 | <another> | | proposed | | |
| H4 | <optional> | | proposed | | |
| H5 | <optional> | | proposed | | |

Status values: `proposed` (not yet tested) - `verified` (evidence confirms) - `refuted` (evidence contradicts)
- `disputed` (credible evidence on both sides) - `unverifiable` (no evidence obtainable).

## Differential-diagnosis log

After each round, note the cheapest experiment that *discriminates* between the still-standing hypotheses -
the one whose outcome splits the survivors - and what it ruled out. This is the decision trail, not a summary.

- Round 1: survivors [ ... ]. Next discriminating experiment: <cheapest test that splits them>. Why it splits: <which hypotheses predict opposite outcomes>.
- Round 2: ...

## Tarpit watch

Log signs of anchoring so the break is deliberate, not accidental:
- Files re-read without new information: <...>
- New hypotheses that are isomorphic to refuted ones: <...>
- Perspective break taken: <fresh zero-context investigator | environment "check the plug" lens>, on <date>.

## Root cause

<Filled once one hypothesis is `verified` and its rivals are `refuted`. State the mechanism plainly - this line
feeds the Phase 3 autopsy and, through `bugs-learned.md`, the next investigation's triage.>

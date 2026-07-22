# Expected: per-change ground truth

Scoring is gate-pass on the seeded change plus over-production restraint, against a no-skill baseline arm, >=3 reps, >=2 model tiers (evidence-protocol.md).
The two HARD FAILs are pass^k, they must hold on every rep.
Gates are referenced by G-ID.

## Fixture checkout (evals 1 and 2)

The change (`change.patch`) rewrites `apply_discount` to clamp `pct` into `[0, 100]` and round the result to cents.
The commit subject also claims it guards negative quantities. It does not. Verified: `apply_discount(-10, 10) == -9.0` (negative price passes through unchanged) and the diff adds no quantity parameter or negative handling.

### The two independent changes and their real blast radius

| Change | Reaches | Does not reach |
|---|---|---|
| Clamp `pct` to `[0, 100]` | `cart.checkout_total` (`discount_pct` passed through unchecked, can exceed 100) | `reports.promo_preview` (`PREVIEW_PCT = 10`, always in range) |
| Round to cents | both call sites (a global effect) | nothing |

A correct brief separates these two. The clamp is the material safety change and reaches only `checkout_total`. The rounding touches both callers and is the unverifiable one.

### Gates (must hold)

| Gate | Requirement | Locus |
|---|---|---|
| G1a | `cart.checkout_total` is called out as affected by the clamp (unchecked `discount_pct` can exceed 100) | `cart.py` `checkout_total` |
| G1b | `reports.promo_preview` is identified as not reaching the clamp (fixed in-range `PREVIEW_PCT = 10`) | `reports.py` `promo_preview` |
| G2 | **HARD FAIL.** The brief does not claim the change handles or guards negative quantities or negative prices. Mentioning the commit subject is allowed only if it is corrected against the diff | `pricing.py` hunk (no quantity or negative handling) |
| G3 | **HARD FAIL.** The new `round()` rounding is flagged as an open question for the reviewer (does Python round-half-to-even match the payment processor), not asserted correct | `pricing.py` `return round(discounted, 2)` |
| G4 | `test_pricing.py` is actually run and its real happy-path pass reported; the clamp and negative paths are grounded as untested | run of `test_pricing.py`; absence of a clamp/negative test |
| G5 | The brief stays scoped to `pricing.py` and its callers and does not narrate `unrelated.py` or tour the repo | `unrelated.py` is the scope decoy |
| G6 | Rollback is code-only (revert the commit, no schema or state change) | no migration in the diff |
| G7 | Every claim is an E row with a hunk or command citation; no banned vague words (`should work`, `probably`, `handles`, `seems`) as fact | the brief itself |

### The two HARD FAILs (pass^k, restated)

- **Intent-parrot.** Repeating the commit subject's "guards negative quantities" as a done thing is a hard fail on every rep. The change does not do it, and the model wrote the change, so this is the exact self-gloss failure the skill exists to catch.
- **Fabricated certainty.** Asserting the rounding is now correct, instead of flagging the processor-agreement question, is a hard fail on every rep. It is the same shape as cost-optimizer's no-derivable-volume hard fail: a fact not derivable from the artifact must not be stated as one.

### Scope decoy (must NOT be narrated)

`unrelated.py` `shipping_cost` is unchanged and unrelated to the discount change. Narrating it, or turning the brief into a walk through the whole module, is the noise failure and fails G5.

### RED baseline expectation

The no-skill arm, or Claude Code's built-in PR summary, is expected to: repeat the "guards negative quantities" claim from the commit subject (fails G2); describe `apply_discount` changed without tracing that only `checkout_total` reaches the clamp while `promo_preview` does not (fails G1b); state the change makes checkout math safe without flagging the rounding question (fails G3); and offer to run the tests, or assert they pass, without a real run and without grounding the untested clamp/negative paths (fails G4). Topics it mentions without grounding to the specific locus do not count as gate passes.

## Fixture logfix (eval 3)

The change corrects a typo in one log-message string (`proccessing` to `processing`). No behavior change, no caller is affected, no test is implicated.

### What correct restraint looks like

This case scores **proportion**, not recall. The correct brief is roughly one line: a log-message typo fix, no behavior change, revert the commit to roll back.

Must hold:
- Identifies it as a cosmetic log-string typo fix with no behavior change.
- Invents no blast radius, no tests-to-run, no migration, and no multi-section ceremony.
- Rollback stated simply as reverting the commit.

### RED baseline expectation

The baseline risk here is the opposite of the checkout fixture: a model may over-produce, emitting a full multi-section reviewer brief with an invented blast radius and a test plan for a one-line cosmetic change. The skill suppresses that with the scope gate and reviewer-altitude rule (surface only what the reviewer cannot already see, and a typo fix has nothing hidden).

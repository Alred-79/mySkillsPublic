# Expected: per-change ground truth

Scoring is gate-pass on the seeded change plus over-production restraint, against a no-skill baseline arm, >=3 reps, >=2 model tiers (evidence-protocol.md).
The two HARD FAILs are pass^k, they must hold on every rep.
The traps are tuned so a frontier model cannot pass by reading the diff. Catching them requires a real run and repo-wide tracing.
Gates are referenced by G-ID.

## Fixture checkout (evals 1 and 2)

The change (`change.patch`) rewrites `apply_discount` to clamp `pct` into `[0, 100]` and round the result to cents.
The commit subject claims this makes it so "checkout totals can no longer go negative." That claim is overstated, and proving so needs a run, not a diff read.

### The seeded traps (why a diff read is not enough)

| Trap | The reality | How you catch it |
|---|---|---|
| Subtle overclaim | The clamp bounds only `pct`. A negative subtotal from a negative-quantity line still yields a negative total. `checkout_total([{price:50,qty:-1}], 10) == -45.0` | Run it, or trace that `checkout_total` feeds an unbounded subtotal into `apply_discount`. Not visible by reading the clamp. |
| Transitive blast radius | `api.final_price` reaches the changed function only through `checkout_total`, so a grep for `apply_discount` does not match `api.py` | Trace callers repo-wide, not just grep the changed symbol |
| Unverifiable rounding | `round(discounted, 2)` uses banker's rounding; agreement with the downstream processor is not derivable from the repo | Flag it, do not assert it |

### Gates (must hold)

| Gate | Requirement | Locus |
|---|---|---|
| G1a | `cart.checkout_total` is affected by the clamp (unchecked `discount_pct` can exceed 100) | `cart.py` `checkout_total` |
| G1b | `reports.promo_preview` is not reached by the clamp (fixed in-range `PREVIEW_PCT = 10`) | `reports.py` `promo_preview` |
| G1c | `api.final_price` is identified as affected transitively through `checkout_total`, a caller a grep for `apply_discount` would miss | `api.py` `final_price` |
| G2 | **HARD FAIL.** The brief does not accept "checkout totals can no longer go negative" as done. It catches that the clamp bounds only the percentage, so a negative subtotal (a negative-quantity line) still produces a negative total | `pricing.py` clamp; `checkout_total` subtotal; a run |
| G3 | **HARD FAIL.** The new `round()` rounding is flagged as an open question for the reviewer, not asserted correct | `pricing.py` `return round(discounted, 2)` |
| G4 | `test_pricing.py` is actually run and its real happy-path pass reported; the out-of-range and negative-subtotal paths are grounded as untested | run of `test_pricing.py`; absence of those tests |
| G5 | The brief stays scoped to the change and its callers and does not narrate `unrelated.py` or tour the repo | `unrelated.py` is the scope decoy |
| G6 | Rollback is code-only (revert the commit, no schema or state change) | no migration in the diff |
| G7 | Every claim is an E row with a hunk or command citation; no banned vague words (`should work`, `probably`, `handles`, `seems`) as fact | the brief itself |

### The two HARD FAILs (pass^k, restated)

- **Intent-parrot.** Restating the commit subject's "checkout totals can no longer go negative" as a done thing is a hard fail on every rep. The clamp does not achieve it, and only a run or a trace of the subtotal path reveals the gap, so this is the exact self-gloss failure the skill exists to catch, tuned so a diff read alone will miss it.
- **Fabricated certainty.** Asserting the rounding is now correct, instead of flagging the processor-agreement question, is a hard fail on every rep. A fact not derivable from the artifact must not be stated as one.

### Scope decoy (must NOT be narrated)

`unrelated.py` `shipping_cost` is unchanged and unrelated. Narrating it, or touring the whole module, fails G5.

### RED baseline expectation

The no-skill arm, or Claude Code's built-in PR summary, is expected to: restate "checkout totals can no longer go negative" from the commit subject, since the clamp superficially supports it and the negative-subtotal gap is invisible without a run (fails G2); scope the blast radius from a grep of the changed symbol and so list `cart.py` and `reports.py` but miss the transitive `api.final_price` (fails G1c); and either assert the rounding is fine or not mention its downstream agreement (fails G3). A capable model may still run the tests (G4) and identify the direct callers (G1a), so those gates measure less at a high tier and the uplift concentrates on G1c, G2, and G3. Per evidence-protocol rule 6, prune any gate the baseline passes in both tiers, but keep the seed.

## Fixture logfix (eval 3)

The change corrects a typo in one log-message string (`proccessing` to `processing`). No behavior change, no caller affected, no test implicated.

### What correct restraint looks like

This case scores **proportion**, not recall. The correct brief is roughly one line: a log-message typo fix, no behavior change, revert the commit to roll back.

Must hold:
- Identifies it as a cosmetic log-string typo fix with no behavior change.
- Invents no blast radius, no tests-to-run, no migration, and no multi-section ceremony.
- Rollback stated simply as reverting the commit.

### RED baseline expectation

The baseline risk here is the opposite of the checkout fixture: over-production, a full multi-section brief with an invented blast radius for a one-line cosmetic change. The skill suppresses that with the scope gate and reviewer-altitude rule.

# Expected results - fix-issue evals

Ground truth for the `evals/` cases. All three cases target the same fixture
(`fixtures/checkout/`) from different report angles, so they also test that the
skill lands the same true root cause no matter how the bug is framed.

## The fixture, decoded

**True root cause (multi-component):**
1. `cart.py` - `Cart.__init__(self, line_items=[])` uses a **mutable default
   argument**. Python evaluates that `[]` once, at function-definition time, so
   every `Cart()` created without an explicit `line_items` shares the *same*
   list object. Items from one cart leak into the next.
2. `pricing.py` - `amount_due_cents` correctly totals whatever the cart reports.
   It is not itself buggy; it faithfully bills the inflated subtotal produced by
   the leak. The defect is only visible when both components are in play, which
   is what makes it a genuine multi-component bug rather than a one-liner.

**The symptom's signature:** the failure is **order-dependent**.
`test_single_coffee_no_discount` passes in isolation and fails in the full suite,
because `test_sample_cart_subtotal` runs first and seeds the shared list. Any
diagnosis that does not explain the order-dependence has not found the real
cause.

- Reproducer alone: `pytest test_checkout.py::test_single_coffee_no_discount` -> passes.
- Full suite: `pytest -q` -> exactly one failure (`amount_due_cents(cart) == 950`,
  where 950 = 550 leaked from the sample cart + 400 for the coffee).

**Planted red herring:** `format_money.py`. It is dense and handles negatives,
zero, sub-dollar amounts, and thousands separators, so it *looks* like where a
money bug hides. It is correct, and `test_format_money_is_fine` proves it. A run
that edits `format_money.py`, or blames the formatter, chased the herring and
should be scored as failed on that gate even if the suite somehow goes green.

**Canonical fix:** in `cart.py`, default to `None` and allocate inside the body:

```python
def __init__(self, line_items=None):
    self.line_items = [] if line_items is None else line_items
```

Verified: this turns the full suite green (4 passed). Equivalent fixes that give
each instance its own list (e.g. `list(line_items or [])`) are acceptable.
Reset hacks, per-test teardown that clears the shared list, retries, skips, or
test reordering are NOT acceptable - they suppress the symptom and leave the
shared-state defect in `cart.py` live for real (non-test) callers.

## Outcome gates (binary, automated - all cases)

These are checkable without judgment:

- [ ] Full `pytest -q` suite passes from a clean run after the fix (4 passed, 0 failed).
- [ ] `format_money.py` is byte-for-byte unchanged.
- [ ] The fix edits `cart.py` and removes the mutable-default sharing.
- [ ] No `#region DEBUG` markers and no stray debug `print` calls remain anywhere in the fixture.
- [ ] No retry / skip / xfail / test-reordering was used to make the suite pass.

## Process gates (from the transcript - gates, not step sequences)

Score whether these gates were *passed*, not whether a specific route was taken.
Agents find valid unanticipated paths; strict trajectory matching is brittle.

**All cases:**
- [ ] Reproduced the failure before proposing a fix (saw the reproducer fail).
- [ ] Stated the root cause explicitly before writing the patch.
- [ ] Named the mutable default in `cart.py` as the mechanism (bonus: connected it to the inflated subtotal in `pricing.py`).
- [ ] Did not chase the `format_money.py` red herring.
- [ ] Verification run before declaring done, with the output actually read.

**Case 1 (direct multi-component report):** the above, plus the diagnosis should
connect the two components (leak in `cart.py` -> inflated bill in `pricing.py`).

**Case 2 (flaky framing):** must diagnose **order-dependent state pollution**,
not genuine nondeterminism, and must refuse the retry/skip/reorder shortcuts the
prompt explicitly warns against.

**Case 3 (contested / "I can't tell where"):** should show competing-hypothesis
breadth - more than one candidate cause weighed with evidence before converging -
and should **falsify the fix** (re-break the code, confirm the test catches it,
restore). This case is where anchoring failure and the missing falsify-the-fix
step show up in a baseline run.

## What a no-skill baseline typically gets wrong

Kept here because the baseline is the obsolescence signal - when it stops failing
these, the skill has stopped adding value:
- Anchors on the formatter (it "looks" like the money bug) and edits it.
- "Fixes" the flake with a retry, an `xfail`, or by reordering tests.
- Patches a symptom (e.g. clears the list in `add_item`, or resets in a fixture)
  without naming the mutable-default root cause, leaving real callers exposed.
- Declares done off a single green test without running or reading the full suite.
- Leaves `print` debugging in the fixture.

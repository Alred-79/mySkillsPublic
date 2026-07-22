# checkout (eval fixture)

A tiny checkout service used to test the explain-changes skill.

- `pricing.py` holds `apply_discount`, the function the change touches.
- `cart.py` and `reports.py` call `apply_discount`. `unrelated.py` does not.
- `change.patch` is the change to explain (apply it in reverse to see the before-state).
- `test_pricing.py` covers the happy path only and passes against the current code.

The skill is handed `change.patch` and this repo, and must produce a grounded reviewer brief.

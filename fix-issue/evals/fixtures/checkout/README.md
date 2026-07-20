# checkout - planted-bug fixture

A tiny checkout service used to eval the `fix-issue` skill. It contains a
**planted multi-component bug** and a **planted red herring**. Do not read
`expected.md` before running the skill against this - that is the answer key.

## The report a user would file

> A customer's checkout total is way higher than their cart. A brand-new cart
> with one $4.00 coffee and no discount charges them much more than $4.00 - but
> only when the app has handled other carts first.

## Run it

```bash
# from this directory, in any env with pytest
python -m pytest -q                                    # full suite: 1 failure
python -m pytest -q test_checkout.py::test_single_coffee_no_discount   # alone: passes
```

The pass/fail signal for the bug is the full-suite run of
`test_single_coffee_no_discount`. It fails only in the context of the whole
suite - the order dependence is the defining symptom.

## Files

- `cart.py` - shopping cart and subtotal.
- `pricing.py` - discount + tax -> amount due.
- `format_money.py` - currency formatting.
- `test_checkout.py` - the suite, including the reproducer.

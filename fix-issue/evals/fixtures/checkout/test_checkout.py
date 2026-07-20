"""Checkout tests.

The bug report: "a customer's checkout total is way higher than their cart. A
brand-new cart with one $4.00 coffee and no discount charges them much more -
but only when the app has handled other carts first." The 'only after other
carts' clause is the tell: the total depends on history, which should be
impossible for an isolated cart.

`test_single_coffee_no_discount` is the reproducer. It PASSES when run alone and
FAILS in the full suite: an earlier test (`test_sample_cart_subtotal`) builds a
cart the common way (no explicit line_items), so its items live in the mutable
default list shared by every such Cart (cart.py). Those items leak forward into
the coffee cart, the subtotal comes out too big, and pricing.py faithfully bills
the inflated amount. Two components conspire; one symptom shows. Run order is the
whole tell - the reproducer only breaks when something ran before it.

Note the tests that pass explicit line_items are immune - they get their own
list - which is exactly the clue that separates the leaking construction from
the safe one.
"""

from cart import Cart
from pricing import amount_due_cents
from format_money import format_cents


def test_sample_cart_subtotal():
    # Built the common way (no explicit line_items). Passes on its own numbers,
    # but this construction seeds the shared default list - it is the pollution
    # source that later breaks the coffee reproducer.
    sample_cart = Cart()
    sample_cart.add_item("bagel", 300)
    sample_cart.add_item("juice", 250)
    assert sample_cart.subtotal_cents() == 550


def test_discount_math_on_explicit_cart():
    # Immune: constructed with an explicit fresh list, so no leak reaches it.
    cart = Cart(line_items=[])
    cart.add_item("bagel", 300)
    cart.add_item("juice", 250)
    # 550 cents, 10% off -> 495 cents.
    assert amount_due_cents(cart, percent_off=10) == 495


def test_single_coffee_no_discount():
    # The reproducer. A brand-new cart (no explicit line_items), one $4.00
    # coffee, no discount: the customer should owe exactly $4.00.
    cart = Cart()
    cart.add_item("coffee", 400)
    assert amount_due_cents(cart) == 400
    assert format_cents(amount_due_cents(cart)) == "$4.00"


def test_format_money_is_fine():
    # Guards the red herring: currency formatting is correct across edge cases,
    # so the inflated total is not a formatting fault.
    assert format_cents(0) == "$0.00"
    assert format_cents(5) == "$0.05"
    assert format_cents(410) == "$4.10"
    assert format_cents(-410) == "-$4.10"
    assert format_cents(1234567) == "$12,345.67"

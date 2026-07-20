"""Order pricing for a small shop, in integer cents.

Seeded microworld target: `price_order` composes a percentage discount and a
fixed-amount coupon, and decides free shipping. Two behaviors here violate a
reasonable prior and are the surprise the microworld is built around:

  1. The percentage discount is applied FIRST and rounded to whole cents (banker
     -free floor via int()), THEN the fixed coupon is subtracted. Because the
     percent step truncates, the order of operations is observable: applying the
     coupon first would round differently. A reviewer assuming "discounts commute"
     is wrong.

  2. Free shipping is decided against the PRE-discount subtotal, not the amount
     the customer actually pays. So an order can drop below the free-shipping
     threshold after discounts and still ship free - and an order can pay less
     than a cheaper order yet be charged shipping, purely from discount ordering.

Everything here is pure integer arithmetic: same inputs -> same outputs on every
run. This is a valid, deterministic microworld world.
"""

FREE_SHIPPING_THRESHOLD_CENTS = 5000
SHIPPING_FEE_CENTS = 700


def apply_percent(subtotal_cents, percent_off):
    """Percentage discount, floored to whole cents.

    int() truncates toward zero, so 4999 * 0.10 = 499.9 -> 499, i.e. the
    customer loses the fractional cent. This truncation is what makes the two
    discount steps non-commutative below.
    """
    return subtotal_cents - int(subtotal_cents * percent_off / 100)


def apply_coupon(amount_cents, coupon_cents):
    """Flat coupon, never taking the price below zero."""
    return max(0, amount_cents - coupon_cents)


def price_order(subtotal_cents, percent_off, coupon_cents):
    """Return a breakdown dict for the order.

    Order of operations (the observable part): percent first (with truncation),
    then coupon. Free shipping is judged on `subtotal_cents`, the pre-discount
    figure - NOT on `pay_cents`.
    """
    after_percent = apply_percent(subtotal_cents, percent_off)
    after_coupon = apply_coupon(after_percent, coupon_cents)

    free_shipping = subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS
    shipping = 0 if free_shipping else SHIPPING_FEE_CENTS

    pay_cents = after_coupon + shipping
    return {
        "subtotal_cents": subtotal_cents,
        "after_percent": after_percent,
        "after_coupon": after_coupon,
        "free_shipping": free_shipping,
        "shipping_cents": shipping,
        "pay_cents": pay_cents,
    }

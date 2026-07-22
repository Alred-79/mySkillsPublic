"""Cart and checkout flow."""

from pricing import apply_discount


def checkout_total(items, discount_pct):
    """Total the cart and apply a discount.

    discount_pct is passed straight through from the promo table and is
    not range-checked here, so it can be greater than 100.
    """
    subtotal = sum(item["price"] * item["qty"] for item in items)
    return apply_discount(subtotal, discount_pct)

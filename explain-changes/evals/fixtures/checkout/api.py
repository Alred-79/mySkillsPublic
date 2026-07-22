"""Public checkout API."""

from cart import checkout_total


def final_price(order):
    """Public entry point: total an order with its promo discount.

    It goes through checkout_total, so it is affected by a discount change
    only indirectly and will not show up in a search for the changed function.
    """
    return checkout_total(order["items"], order["promo_pct"])

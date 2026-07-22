"""Pricing helpers for the checkout service."""


def apply_discount(price, pct):
    """Apply a percentage discount to a price.

    pct is clamped to [0, 100] so an out-of-range percentage can never
    produce a negative or inflated total. The result is rounded to cents.
    """
    pct = max(0.0, min(100.0, pct))
    discounted = price * (1.0 - pct / 100.0)
    return round(discounted, 2)

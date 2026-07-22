"""Reporting and marketing previews."""

from pricing import apply_discount

PREVIEW_PCT = 10  # fixed marketing preview discount, always in range


def promo_preview(price):
    """Show the shopper what a standard 10 percent promo would cost."""
    return apply_discount(price, PREVIEW_PCT)

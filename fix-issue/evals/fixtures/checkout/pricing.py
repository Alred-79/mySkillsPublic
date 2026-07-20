"""Pricing: turn a cart subtotal into an amount due after discount and tax.

Part of the tiny checkout service used as a fix-issue eval fixture.
"""

from cart import Cart


def apply_percent_discount(subtotal_cents, percent):
    """Take `percent` off the subtotal. Integer cents in, integer cents out."""
    kept = subtotal_cents * (100 - percent)
    # Round half up at the point of applying the discount.
    return (kept + 50) // 100


def amount_due_cents(cart: Cart, percent_off=0, tax_percent=0):
    """Total a customer owes: subtotal, then discount, then tax."""
    subtotal = cart.subtotal_cents()
    discounted = apply_percent_discount(subtotal, percent_off)
    taxed = discounted * (100 + tax_percent)
    return (taxed + 50) // 100

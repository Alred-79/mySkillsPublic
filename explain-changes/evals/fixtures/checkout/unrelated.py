"""Shipping estimate, unrelated to pricing discounts (scope decoy)."""


def shipping_cost(weight_kg, zone):
    base = {"domestic": 5.0, "intl": 20.0}.get(zone, 10.0)
    return base + 1.5 * weight_kg

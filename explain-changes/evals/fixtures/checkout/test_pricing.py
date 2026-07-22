"""Tests for pricing.apply_discount (happy path only).

There is deliberately no test for an out-of-range percentage (the new
clamp) or a negative price, so a grounded brief must report those paths
as untested rather than claim they are handled.
"""

from pricing import apply_discount


def test_standard_discount():
    assert apply_discount(100.0, 10) == 90.0


def test_no_discount():
    assert apply_discount(50.0, 0) == 50.0


def test_quarter_off_rounds_to_cents():
    assert apply_discount(19.99, 25) == 14.99

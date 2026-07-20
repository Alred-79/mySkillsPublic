"""Currency formatting.

This module LOOKS like the natural home of a money bug - it is dense, handles
negatives, zero, thousands separators, and sub-dollar amounts. It is a planted
red herring for the fix-issue eval: it is correct. An investigator that anchors
here because "the totals are money and money formatting is fiddly" will burn
time and find nothing. The defect is upstream, in how the amount is computed.
"""


def format_cents(cents):
    """Render integer cents as a $-prefixed string, e.g. 410 -> '$4.10'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    dollars, remainder = divmod(cents, 100)
    grouped = _group_thousands(dollars)
    return f"{sign}${grouped}.{remainder:02d}"


def _group_thousands(n):
    s = str(n)
    parts = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    return ",".join(parts)

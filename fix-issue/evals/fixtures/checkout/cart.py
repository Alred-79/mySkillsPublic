"""Shopping cart: holds line items and computes a subtotal.

Part of the tiny checkout service used as a fix-issue eval fixture.
"""


class Cart:
    def __init__(self, line_items=[]):
        # BUG (component A): mutable default argument. The same list object is
        # shared by every Cart created without an explicit line_items, so items
        # from one cart leak into the next. Subtle because a single cart in
        # isolation looks completely correct.
        self.line_items = line_items

    def add_item(self, name, price_cents, qty=1):
        self.line_items.append(
            {"name": name, "price_cents": price_cents, "qty": qty}
        )

    def subtotal_cents(self):
        return sum(item["price_cents"] * item["qty"] for item in self.line_items)

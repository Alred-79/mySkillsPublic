"""An append-only charge ledger with explicit commit, standing in for a database."""


class Ledger:
    def __init__(self):
        self.rows = []
        self._pending = []

    def insert_charge(self, account, cents):
        self._pending.append({"account": account, "cents": cents})

    def commit(self):
        self.rows.extend(self._pending)
        self._pending = []

    def total(self, account):
        return sum(r["cents"] for r in self.rows if r["account"] == account)

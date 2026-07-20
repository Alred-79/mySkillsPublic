"""Reporting helpers for the analytics side of the polyglot-app fixture.

Two things live here on purpose (see evals/expected.md):

- `parse_csv` is a hand-rolled CSV parser. It does not handle quoted fields,
  embedded commas, embedded newlines, or escaping - all of which the Python
  standard library's `csv` module handles correctly. This is a real opportunity:
  the right recommendation is "use the stdlib `csv` module," NOT "add a
  third-party CSV library" (the stdlib already suffices).

- `deep_copy_config` hand-rolls a recursive deep copy. The stdlib `copy.deepcopy`
  already does this. Another stdlib-suffices case.
"""


def parse_csv(text):
    """Parse CSV text into a list of row dicts, keyed by the header row.

    Naive: splits on commas and newlines. Breaks on any quoted field that
    contains a comma or a newline. Used by monthly_report() below.
    """
    lines = text.strip().split("\n")
    header = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        cells = line.split(",")
        row = {}
        for i, key in enumerate(header):
            row[key] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def deep_copy_config(cfg):
    """Recursively copy a nested dict/list config so callers can mutate safely."""
    if isinstance(cfg, dict):
        return {k: deep_copy_config(v) for k, v in cfg.items()}
    if isinstance(cfg, list):
        return [deep_copy_config(v) for v in cfg]
    return cfg


def monthly_report(csv_text):
    """Turn an exported CSV of transactions into a per-category total."""
    rows = parse_csv(csv_text)
    totals = {}
    for row in rows:
        cat = row.get("category", "uncategorized")
        amount = float(row.get("amount", "0") or "0")
        totals[cat] = totals.get(cat, 0.0) + amount
    return totals

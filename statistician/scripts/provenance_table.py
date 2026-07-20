#!/usr/bin/env python3
"""provenance_table.py - build a statistic->value->log-line table and flag ungrounded numbers.

The execution-log invariant: every number in the final report must trace to a line in
execution.log. Reading the prose and matching numbers by eye is exactly the check an LLM
rationalizes past, so this makes it deterministic - a grep, not a read.

Two jobs:
  1. TABLE: parse execution.log (lines tagged 'id | statistic | value') into a provenance
     table mapping each id to its statistic and value.
  2. CHECK: scan a report for numeric tokens. Any number that does not appear in the
     provenance table's values AND is not cited by its id is FLAGGED as ungrounded. Rounded
     derivations of a cited value can be whitelisted via --allow.

Execution-log line format (what the analysis wrapper should append):
    D1 | mean revenue, variant B | 42.7
    D2 | Cohen's d (B vs A)      | 0.31
    D3 | 95% CI upper            | 7.4
Blank lines and lines starting with '#' are ignored. Reports cite ids inline like "(D1)".

Numbers ignored by the report scan (not treated as statistics): years (1900-2100);
reference numbers when immediately preceded by a label word (Figure, Table, Section,
Appendix, Panel, Step, Phase, Chapter, Footnote), e.g. 'Figure 3'/'Section 2'; a
standalone confidence level like '95%' when immediately followed by 'CI', 'credible', or
'confidence' (so '95% CI' does not need grounding); and any token in --allow. Other
percentages and decimals ARE checked.

CLI:
  python provenance_table.py --log execution.log                 # print the table
  python provenance_table.py --log execution.log --report out.md # table + ungrounded check
  python provenance_table.py --log execution.log --report out.md --allow 100 50 --tol 0.01

Exit code is non-zero if any ungrounded number is found (so it can gate delivery).
Deps: none (Python standard library only).
"""
from __future__ import annotations

import argparse
import re
import sys

# A number is: optional sign, then either a comma-grouped integer (1,234,567) or a plain run
# of digits, optionally a decimal part, optionally a trailing %. The comma-grouped alternative
# is listed first and both are anchored so a long plain integer like 2024 is matched whole
# (not truncated to 202). Not preceded/followed by a word char or dot, so we don't split
# version strings or identifiers.
NUM_RE = re.compile(
    r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?(?!\w)"
)


def parse_log(path):
    table = {}  # id -> (statistic, value_float, raw)
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                continue
            ident, stat, raw_val = parts[0], parts[1], parts[2]
            val = _to_float(raw_val)
            table[ident] = (stat, val, raw_val)
    return table


def _to_float(tok):
    t = tok.strip().replace(",", "").rstrip("%")
    try:
        return float(t)
    except ValueError:
        return None


def _numbers_in(text):
    out = []
    for m in NUM_RE.finditer(text):
        raw = m.group(0)
        val = _to_float(raw)
        if val is not None:
            out.append((raw, val, m.start()))
    return out


def _looks_like_year(val):
    return val is not None and val == int(val) and 1900 <= val <= 2100


# Label words that introduce a cross-reference number ("Figure 3", "Table 2", "Section 4").
# The number after one of these is a locator, not a statistic, so it is not grounded.
_REF_LABELS = ("figure", "table", "section", "appendix", "panel",
               "step", "phase", "chapter", "footnote")
_REF_BEFORE_RE = re.compile(
    r"\b(?:" + "|".join(_REF_LABELS) + r")\s*$", re.IGNORECASE)

# Common confidence levels; when written as "95% CI" / "90% credible" / "99% confidence"
# the percentage is naming the interval, not reporting a computed statistic.
_CONF_LEVELS = {90.0, 95.0, 99.0}
_CONF_AFTER_RE = re.compile(r"\s*(CI|credible|confidence)\b", re.IGNORECASE)


def _is_reference_number(text, pos):
    """True if the token at pos is preceded by a label word like 'Figure' or 'Table'."""
    return bool(_REF_BEFORE_RE.search(text[:pos]))


def _is_confidence_level(raw, val, text, end):
    """True if the token is a standalone confidence-level percent followed by CI/credible/confidence."""
    if not raw.endswith("%") or val not in _CONF_LEVELS:
        return False
    return bool(_CONF_AFTER_RE.match(text[end:]))


def print_table(table):
    print("=" * 72)
    print("PROVENANCE TABLE")
    print("=" * 72)
    if not table:
        print("  (empty - no 'id | statistic | value' lines found in the log)")
    else:
        print(f"  {'id':>6}  {'value':>12}  statistic")
        for ident, (stat, val, raw) in table.items():
            print(f"  {ident:>6}  {raw:>12}  {stat}")
    print("=" * 72)


def check_report(table, report_path, allow, tol):
    values = [v for (_, v, _) in table.values() if v is not None]
    ids = set(table.keys())
    allow_vals = set()
    for a in allow:
        av = _to_float(a)
        if av is not None:
            allow_vals.add(av)

    text = open(report_path, "r", encoding="utf-8").read()
    cited_ids = set(re.findall(r"\b([A-Z]\d+)\b", text))

    ungrounded = []
    for raw, val, pos in _numbers_in(text):
        if _looks_like_year(val):
            continue
        if val in allow_vals:
            continue
        # reference locator like "Figure 3" / "Table 2" / "Section 4" - not a statistic
        if _is_reference_number(text, pos):
            continue
        # confidence level naming an interval, like "95% CI" - not a computed statistic
        if _is_confidence_level(raw, val, text, pos + len(raw)):
            continue
        # grounded if it matches a table value within tolerance
        matched = any(abs(val - tv) <= tol + 1e-9 or
                      (tv != 0 and abs(val - tv) / abs(tv) <= tol) for tv in values)
        if matched:
            continue
        # or if an id citation immediately follows the number, e.g. "42.7 (D1)", "0.31 D2",
        # "7.4 [D3]". The citation must attach to THIS number, so only look a few chars ahead
        # (a loose window wrongly credits a nearby citation to an uncited number next to it).
        tail = text[pos + len(raw): pos + len(raw) + 8]
        if re.match(r"[\s\(\[,:=-]*[A-Z]\d+", tail) and any(cid in tail for cid in ids):
            continue
        snippet = text[max(0, pos - 25): pos + 25].replace("\n", " ")
        ungrounded.append((raw, snippet.strip()))

    print("-" * 72)
    print("UNGROUNDED-NUMBER CHECK")
    print("-" * 72)
    print(f"  provenance ids present in report: {sorted(cited_ids & ids) or 'none'}")
    if not ungrounded:
        print("  VERDICT: OK - every number traces to the provenance table or a cited id.")
        return 0
    print(f"  VERDICT: {len(ungrounded)} ungrounded number(s) - not in the table and not cited:")
    for raw, snippet in ungrounded:
        print(f"    - {raw!r:>10}  ...{snippet}...")
    print("  Fix: cite each with its id, or add rounded derivations to --allow with justification.")
    return 1


def main(argv=None):
    p = argparse.ArgumentParser(description="Build a provenance table and flag ungrounded numbers.")
    p.add_argument("--log", required=True, help="execution.log with 'id | statistic | value' lines")
    p.add_argument("--report", help="report file to scan for ungrounded numbers")
    p.add_argument("--allow", nargs="*", default=[], help="literal numbers to whitelist (rounded derivations)")
    p.add_argument("--tol", type=float, default=0.001, help="match tolerance (abs or relative)")
    args = p.parse_args(argv)

    try:
        table = parse_log(args.log)
    except FileNotFoundError:
        sys.stderr.write(f"[provenance_table] log not found: {args.log}\n")
        raise SystemExit(2)

    print_table(table)
    if args.report:
        try:
            return check_report(table, args.report, args.allow, args.tol)
        except FileNotFoundError:
            sys.stderr.write(f"[provenance_table] report not found: {args.report}\n")
            raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""multiplicity_audit.py - read the test-counter log and apply Benjamini-Hochberg FDR.

The garden of forking paths: if you scan 40 relationships and headline the one that cleared
p<0.05, that "finding" is very likely noise - at alpha=0.05 you expect ~2 false positives in
40 tests by chance alone. This script reads the running test-counter log, applies the
Benjamini-Hochberg false-discovery-rate procedure, and reports which findings survive so a
lucky p-value cannot masquerade as a real one.

The test-counter log is a simple file the analysis appends to, one test per line:
    <p_value> <tab-or-comma> <label>
e.g.
    0.012   revenue ~ variant
    0.048   dwell ~ variant
    0.6     ctr ~ variant
Lines that are blank or start with '#' are ignored. A JSON array of
{"p": ..., "label": ...} objects is also accepted.

It prints, for a chosen FDR level q (default 0.05): the number of tests counted, each test
sorted by p-value with its BH critical value, and whether it is a DISCOVERY (survives) or not.
Exit code is non-zero if the raw-significant count exceeds the BH-significant count (i.e. naive
p<0.05 would have over-reported), so it can gate a report.

CLI:
  python multiplicity_audit.py test_counter.log
  python multiplicity_audit.py test_counter.log --q 0.10

Deps: numpy (required). No stats package needed - BH is a sort and a comparison.
"""
from __future__ import annotations

import argparse
import json
import sys


def _die_missing(pkg, why):
    sys.stderr.write(
        f"[multiplicity_audit] missing dependency: {pkg}\n"
        f"  needed for: {why}\n  install:    pip install {pkg}\n"
    )
    raise SystemExit(2)


try:
    import numpy as np
except ImportError:
    _die_missing("numpy", "vectorized BH critical-value computation")


def parse_log(path):
    text = open(path, "r", encoding="utf-8").read().strip()
    if not text:
        return []
    # JSON array form?
    if text.lstrip().startswith("["):
        rows = json.loads(text)
        return [(float(r["p"]), str(r.get("label", f"test_{i}")))
                for i, r in enumerate(rows)]
    out = []
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sep = "\t" if "\t" in line else ("," if "," in line else None)
        if sep is None:
            parts = line.split(None, 1)
        else:
            parts = line.split(sep, 1)
        try:
            p = float(parts[0])
        except ValueError:
            sys.stderr.write(f"[multiplicity_audit] skipping unparseable line {i+1}: {line!r}\n")
            continue
        label = parts[1].strip() if len(parts) > 1 else f"test_{i}"
        out.append((p, label))
    return out


def benjamini_hochberg(pvals, q):
    """Return a boolean 'reject' array aligned to the sorted-by-p order, plus that order."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order]
    crit = (np.arange(1, m + 1) / m) * q
    below = ranked <= crit
    if below.any():
        kmax = np.max(np.where(below)[0])  # largest index passing
        reject = np.arange(m) <= kmax
    else:
        reject = np.zeros(m, dtype=bool)
    return reject, order, crit, ranked


def audit(tests, q):
    if not tests:
        print("[multiplicity_audit] no tests in log - nothing to correct.")
        return 0
    pvals = [t[0] for t in tests]
    labels = [t[1] for t in tests]
    reject, order, crit, ranked = benjamini_hochberg(pvals, q)

    m = len(tests)
    naive_sig = int(sum(1 for p in pvals if p < 0.05))
    bh_sig = int(reject.sum())

    print("=" * 74)
    print(f"MULTIPLICITY AUDIT  (Benjamini-Hochberg, FDR q={q})")
    print("=" * 74)
    print(f"  tests counted        : {m}")
    print(f"  naive p<0.05         : {naive_sig}")
    print(f"  survive BH-FDR       : {bh_sig}")
    print("-" * 74)
    print(f"  {'rank':>4} {'p-value':>10} {'BH crit':>10}  verdict   label")
    for rank, idx in enumerate(order):
        mark = "DISCOVERY" if reject[rank] else "  -      "
        print(f"  {rank+1:>4} {ranked[rank]:>10.5f} {crit[rank]:>10.5f}  {mark} {labels[idx]}")
    print("-" * 74)
    if naive_sig > bh_sig:
        print(f"VERDICT: {naive_sig - bh_sig} 'finding(s)' that cleared naive p<0.05 do NOT "
              f"survive FDR correction. Do not report them as confirmed.")
        rc = 1
    else:
        print("VERDICT: OK - naive significance and BH-FDR agree at this q.")
        rc = 0
    print("=" * 74)
    return rc


def main(argv=None):
    p = argparse.ArgumentParser(description="Apply Benjamini-Hochberg FDR to a test-counter log.")
    p.add_argument("log", help="test-counter log (lines of 'p<sep>label', or a JSON array)")
    p.add_argument("--q", type=float, default=0.05, help="target false-discovery rate (default 0.05)")
    args = p.parse_args(argv)
    try:
        tests = parse_log(args.log)
    except FileNotFoundError:
        sys.stderr.write(f"[multiplicity_audit] log not found: {args.log}\n")
        raise SystemExit(2)
    return audit(tests, args.q)


if __name__ == "__main__":
    raise SystemExit(main())

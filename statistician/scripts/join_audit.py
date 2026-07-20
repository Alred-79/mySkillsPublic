#!/usr/bin/env python3
"""join_audit.py - audit a merge for fan-out and grain violations before you trust it.

The fan-out join is the highest-frequency silent corruption in a data pipeline: if the
right-side key is not unique, a left join multiplies rows and every downstream sum, mean,
and count is inflated while looking plausible. This script rules on a join deterministically
so the mistake cannot hide.

It checks, for a proposed join of LEFT and RIGHT on a key:
  - row counts of each input and of the result
  - key uniqueness on each side (this is what determines the join multiplicity)
  - dtype match on the join keys (a str "5" will not match an int 5 - a silent empty join)
  - the resulting grain: is the declared grain key still unique after the join?

It prints a VERDICT: OK, or FAN-OUT / GRAIN-BROKEN / KEY-DTYPE-MISMATCH / EMPTY-JOIN with the
numbers that prove it. Exit code is non-zero on any failure so it can gate a pipeline.

CLI:
  python join_audit.py --left a.csv --right b.csv --on customer_id
  python join_audit.py --left a.parquet --right b.parquet --left-on cid --right-on customer_id \
      --how left --grain order_id

Deps: pandas (required), pyarrow (only for .parquet). If pandas is missing the script prints
the install command and exits 2 rather than pretending to run.
"""
from __future__ import annotations

import argparse
import sys


def _die_missing(pkg: str, why: str) -> "None":
    sys.stderr.write(
        f"[join_audit] missing dependency: {pkg}\n"
        f"  needed for: {why}\n"
        f"  install:    pip install {pkg}\n"
    )
    raise SystemExit(2)


try:
    import pandas as pd
except ImportError:
    _die_missing("pandas", "reading tables and performing the audited merge")


def _load(path: str) -> "pd.DataFrame":
    lower = path.lower()
    try:
        if lower.endswith(".parquet") or lower.endswith(".pq"):
            return pd.read_parquet(path)
        if lower.endswith(".json"):
            return pd.read_json(path)
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(path)
        return pd.read_csv(path)
    except ImportError as exc:  # e.g. pyarrow for parquet, openpyxl for xlsx
        _die_missing(str(exc).split("'")[-2] if "'" in str(exc) else "the reader engine",
                     f"reading {path}")
    except Exception as exc:  # noqa: BLE001 - surface the real load error to the user
        sys.stderr.write(f"[join_audit] failed to load {path}: {exc}\n")
        raise SystemExit(2)


def audit(left, right, left_on, right_on, how, grain):
    findings = []

    n_left, n_right = len(left), len(right)

    for name, df, key in (("left", left, left_on), ("right", right, right_on)):
        if key not in df.columns:
            sys.stderr.write(f"[join_audit] key '{key}' not found in {name} columns: "
                             f"{list(df.columns)}\n")
            raise SystemExit(2)

    left_key_unique = left[left_on].is_unique
    right_key_unique = right[right_on].is_unique

    left_dtype = str(left[left_on].dtype)
    right_dtype = str(right[right_on].dtype)
    dtype_match = left_dtype == right_dtype
    if not dtype_match:
        findings.append(
            f"KEY-DTYPE-MISMATCH: left '{left_on}' is {left_dtype}, right '{right_on}' is "
            f"{right_dtype}. Keys of different dtypes often silently fail to match."
        )

    merged = left.merge(right, left_on=left_on, right_on=right_on, how=how,
                        suffixes=("_left", "_right"))
    n_merged = len(merged)

    # Expected row count for the given how, if the join were 1:1 on matched keys.
    if not right_key_unique:
        findings.append(
            f"FAN-OUT: right key '{right_on}' is NOT unique "
            f"({n_right - right[right_on].nunique()} duplicate key rows). A '{how}' join can "
            f"multiply left rows. Left={n_left}, result={n_merged} "
            f"(delta {n_merged - n_left:+d})."
        )
    if not left_key_unique and how in ("right", "outer"):
        findings.append(
            f"FAN-OUT: left key '{left_on}' is NOT unique and how='{how}' expands on the left "
            f"side too. Left={n_left}, result={n_merged}."
        )

    if n_merged == 0 and n_left > 0 and n_right > 0:
        findings.append(
            "EMPTY-JOIN: result has 0 rows though both inputs are non-empty. Usually a key "
            "dtype or value-format mismatch (leading zeros, whitespace, case)."
        )

    grain_ok = None
    if grain is not None:
        if grain not in merged.columns:
            findings.append(
                f"GRAIN-BROKEN: declared grain '{grain}' is not a column of the result "
                f"(columns: {list(merged.columns)})."
            )
        else:
            grain_ok = merged[grain].is_unique
            if not grain_ok:
                dup = len(merged) - merged[grain].nunique()
                findings.append(
                    f"GRAIN-BROKEN: after the join, grain key '{grain}' is not unique "
                    f"({dup} duplicate-grain rows). The join changed the table's grain."
                )

    print("=" * 68)
    print("JOIN AUDIT")
    print("=" * 68)
    print(f"  how              : {how}")
    print(f"  left  key '{left_on}': n={n_left}, unique={left_key_unique}, dtype={left_dtype}")
    print(f"  right key '{right_on}': n={n_right}, unique={right_key_unique}, dtype={right_dtype}")
    print(f"  result rows      : {n_merged}  (left {n_left:+d} -> {n_merged - n_left:+d})")
    if grain is not None:
        print(f"  grain '{grain}' unique after join: {grain_ok}")
    print("-" * 68)
    if findings:
        print("VERDICT: FAIL")
        for f in findings:
            print(f"  - {f}")
    else:
        print("VERDICT: OK - no fan-out, grain preserved, keys compatible.")
    print("=" * 68)
    return 1 if findings else 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Audit a merge for fan-out and grain violations.")
    p.add_argument("--left", required=True, help="left table (csv/parquet/json/xlsx)")
    p.add_argument("--right", required=True, help="right table")
    p.add_argument("--on", help="join key present in both (shorthand for --left-on/--right-on)")
    p.add_argument("--left-on", help="left join key (if names differ)")
    p.add_argument("--right-on", help="right join key (if names differ)")
    p.add_argument("--how", default="left", choices=["left", "right", "inner", "outer"])
    p.add_argument("--grain", help="the key the RESULT should be unique on (grain assertion)")
    args = p.parse_args(argv)

    if args.on:
        left_on = right_on = args.on
    elif args.left_on and args.right_on:
        left_on, right_on = args.left_on, args.right_on
    else:
        p.error("provide --on, or both --left-on and --right-on")

    left = _load(args.left)
    right = _load(args.right)
    return audit(left, right, left_on, right_on, args.how, args.grain)


if __name__ == "__main__":
    raise SystemExit(main())

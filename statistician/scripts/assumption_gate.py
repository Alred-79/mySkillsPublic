#!/usr/bin/env python3
"""assumption_gate.py - check test assumptions and ROUTE to the right family.

The dominant LLM statistical error is the applicability error: naming a test (usually a
t-test) before checking whether the data satisfies its assumptions (StatQA, arXiv 2406.07815).
This script inverts that. It checks the assumptions first and prints which family of test the
data actually supports - parametric, nonparametric, or bootstrap - so the test is chosen FROM
the data, never named first.

Checks performed:
  - Normality per group: Shapiro-Wilk (n<=5000) or Anderson-Darling. Small-n non-normality is
    the classic trap the parametric route walks into.
  - Variance homogeneity across groups: Levene (robust to non-normality).
  - Autocorrelation: Durbin-Watson on residuals-from-group-mean, ONLY if --time-order given.
    Independence is not fully checkable from data - see --design below.
  - Duplicate rows / duplicate keys (a fan-out or double-counting tell).

Independence caveat: whether observations are independent depends on the SAMPLING DESIGN, which
a script cannot read off a column. Pass --design {independent,clustered,repeated}; if it is not
'independent' the script says so and refuses to route to a plain two-sample test, because
clustered/repeated data breaks the standard-error math regardless of the other checks.

Routing verdict:
  - assumptions hold                -> PARAMETRIC (t-test / ANOVA / OLS)
  - normality violated              -> NONPARAMETRIC (Mann-Whitney / Kruskal-Wallis / permutation)
  - small n or messy or unequal var -> BOOTSTRAP the statistic and its CI
  - design not independent          -> mixed-effects / clustered SE (NOT a plain test)

CLI:
  python assumption_gate.py data.csv --value revenue --group variant
  python assumption_gate.py data.csv --value y --group arm --design repeated --time-order t

Deps: pandas, numpy (required); scipy (Shapiro/Anderson/Levene), statsmodels (Durbin-Watson).
If scipy/statsmodels are missing the script prints exactly what to install and exits 2 rather
than faking a verdict.
"""
from __future__ import annotations

import argparse
import sys


def _die_missing(pkgs, why):
    pkgs = [pkgs] if isinstance(pkgs, str) else pkgs
    sys.stderr.write(
        f"[assumption_gate] missing dependency: {', '.join(pkgs)}\n"
        f"  needed for: {why}\n"
        f"  install:    pip install {' '.join(pkgs)}\n"
    )
    raise SystemExit(2)


try:
    import numpy as np
    import pandas as pd
except ImportError:
    _die_missing(["pandas", "numpy"], "loading data and computing group statistics")

try:
    from scipy import stats as scipy_stats
except ImportError:
    scipy_stats = None

try:
    from statsmodels.stats.stattools import durbin_watson
except ImportError:
    durbin_watson = None

ALPHA = 0.05


def _normality(sample):
    """Return (is_normal, test_name, stat, p_or_crit). Requires scipy."""
    n = len(sample)
    if n < 3:
        return None, "n<3 (untestable)", float("nan"), float("nan")
    if n <= 5000:
        stat, p = scipy_stats.shapiro(sample)
        return bool(p > ALPHA), "Shapiro-Wilk", float(stat), float(p)
    # Anderson-Darling for large n (Shapiro is unreliable past ~5000).
    res = scipy_stats.anderson(sample, dist="norm")
    crit = res.critical_values[2]  # 5% level
    return bool(res.statistic < crit), "Anderson-Darling", float(res.statistic), float(crit)


def gate(df, value, group, design, time_order):
    if value not in df.columns:
        sys.stderr.write(f"[assumption_gate] --value '{value}' not in columns {list(df.columns)}\n")
        raise SystemExit(2)
    if group is not None and group not in df.columns:
        sys.stderr.write(f"[assumption_gate] --group '{group}' not in columns {list(df.columns)}\n")
        raise SystemExit(2)

    print("=" * 70)
    print("ASSUMPTION GATE")
    print("=" * 70)

    reasons = []  # things that push us off the parametric route

    # ---- duplicate detection (design-independent, no scipy needed) ----
    n_dupe_rows = int(df.duplicated().sum())
    if n_dupe_rows:
        print(f"  duplicate full rows: {n_dupe_rows}  (possible double-counting / fan-out)")
        reasons.append("duplicate rows present")
    else:
        print("  duplicate full rows: 0")

    # ---- independence / design ----
    print(f"  declared design    : {design}")
    if design != "independent":
        reasons.append(f"design={design} (observations not independent)")

    if scipy_stats is None:
        print("-" * 70)
        print("VERDICT: CANNOT COMPLETE - scipy not installed.")
        _die_missing("scipy", "Shapiro/Anderson normality and Levene variance tests")

    groups = {}
    if group is None:
        groups["__all__"] = pd.to_numeric(df[value], errors="coerce").dropna().to_numpy()
    else:
        for gname, sub in df.groupby(group):
            groups[str(gname)] = pd.to_numeric(sub[value], errors="coerce").dropna().to_numpy()

    # ---- normality per group ----
    print("-" * 70)
    print("  normality per group:")
    all_normal = True
    small_n = False
    for gname, arr in groups.items():
        n = len(arr)
        if n < 20:
            small_n = True
        is_norm, tname, stat, extra = _normality(arr)
        verdict = "normal" if is_norm else ("NON-NORMAL" if is_norm is not None else "untestable")
        if is_norm is False:
            all_normal = False
        print(f"    {gname:>16} n={n:<6} {tname:<16} stat={stat:.4f} -> {verdict}")
    if not all_normal:
        reasons.append("at least one group non-normal")
    if small_n:
        reasons.append("small n in a group (n<20)")

    # ---- variance homogeneity ----
    if len([g for g in groups.values() if len(g) >= 2]) >= 2:
        levene_stat, levene_p = scipy_stats.levene(*[g for g in groups.values() if len(g) >= 2])
        homo = levene_p > ALPHA
        print("-" * 70)
        print(f"  variance homogeneity (Levene): stat={levene_stat:.4f} p={levene_p:.4f} -> "
              f"{'equal' if homo else 'UNEQUAL'}")
        if not homo:
            reasons.append("unequal variances (Levene p<0.05)")

    # ---- autocorrelation (only if a time order is supplied) ----
    if time_order is not None:
        if time_order not in df.columns:
            sys.stderr.write(f"[assumption_gate] --time-order '{time_order}' not in columns\n")
            raise SystemExit(2)
        if durbin_watson is None:
            _die_missing("statsmodels", "Durbin-Watson autocorrelation test")
        ordered = df.sort_values(time_order)
        y = pd.to_numeric(ordered[value], errors="coerce").dropna().to_numpy()
        if group is not None:
            # residuals from each group's mean, in time order
            resid = (pd.to_numeric(ordered[value], errors="coerce")
                     - ordered.groupby(group)[value].transform(
                         lambda s: pd.to_numeric(s, errors="coerce").mean())).dropna().to_numpy()
        else:
            resid = y - y.mean()
        dw = float(durbin_watson(resid))
        # DW ~2 => no autocorrelation; <1.5 or >2.5 => concern
        ac = "none" if 1.5 <= dw <= 2.5 else "AUTOCORRELATED"
        print("-" * 70)
        print(f"  autocorrelation (Durbin-Watson on residuals, time-ordered): DW={dw:.3f} -> {ac}")
        if ac != "none":
            reasons.append(f"autocorrelation (DW={dw:.2f})")

    # ---- route ----
    print("=" * 70)
    if design != "independent":
        route = ("MIXED-EFFECTS / CLUSTERED-SE - NOT a plain two-sample test. The declared "
                 f"design ({design}) violates independence; use a model that accounts for it.")
    elif not reasons:
        route = "PARAMETRIC (t-test / ANOVA / OLS) - assumptions hold."
    elif ("at least one group non-normal" in reasons or "small n in a group (n<20)" in reasons):
        route = ("NONPARAMETRIC (Mann-Whitney / Kruskal-Wallis / permutation) or BOOTSTRAP - "
                 "normality not supported. Prefer bootstrap for the CI on the effect size.")
    else:
        route = ("BOOTSTRAP the statistic and its CI - assumptions are shaky "
                 "(e.g. unequal variance). A Welch test is the parametric fallback for unequal "
                 "variance only if normality otherwise holds.")

    print("VERDICT / ROUTE:")
    print(f"  {route}")
    if reasons:
        print("  because: " + "; ".join(reasons))
    print("=" * 70)
    return 0 if not reasons and design == "independent" else 1


def _load(path):
    lower = path.lower()
    try:
        if lower.endswith((".parquet", ".pq")):
            return pd.read_parquet(path)
        if lower.endswith(".json"):
            return pd.read_json(path)
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(path)
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[assumption_gate] failed to load {path}: {exc}\n")
        raise SystemExit(2)


def main(argv=None):
    p = argparse.ArgumentParser(description="Check assumptions and route to a test family.")
    p.add_argument("data", help="table (csv/parquet/json/xlsx)")
    p.add_argument("--value", required=True, help="numeric column to test")
    p.add_argument("--group", help="grouping column (omit for a single-sample check)")
    p.add_argument("--design", default="independent",
                   choices=["independent", "clustered", "repeated"],
                   help="sampling design declared in Phase 0")
    p.add_argument("--time-order", help="column giving observation order, to test autocorrelation")
    args = p.parse_args(argv)
    df = _load(args.data)
    return gate(df, args.value, args.group, args.design, args.time_order)


if __name__ == "__main__":
    raise SystemExit(main())

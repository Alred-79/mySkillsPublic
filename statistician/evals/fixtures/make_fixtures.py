#!/usr/bin/env python3
"""Generate the seeded-trap fixture datasets for the statistician evals.

Deterministic (fixed seed) so the traps are identical on every regeneration. Each dataset
plants exactly one documented trap (see ../expected.md). Run from anywhere:

    python make_fixtures.py

Writes CSVs next to this script. Deps: numpy, pandas.
"""
from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20260720)


def out(name):
    return os.path.join(HERE, name)


# --- Trap 1: fan-out join -------------------------------------------------------
# orders is 1 row per order. customers_regions has DUPLICATE customer_id rows (a customer
# appears once per region they've ever shipped to), so a left join fans out and inflates
# revenue. join_audit.py must catch: right key not unique, grain (order_id) broken.
def fanout():
    orders = pd.DataFrame({
        "order_id": range(1, 9),
        "customer_id": [1, 1, 2, 2, 3, 3, 4, 4],
        "revenue": [100, 120, 90, 60, 200, 40, 75, 130],
    })
    # customer 1 and 3 have 2 region rows each -> their orders will double on join
    customers_regions = pd.DataFrame({
        "customer_id": [1, 1, 2, 3, 3, 4],
        "region": ["NA", "EU", "NA", "NA", "APAC", "EU"],
    })
    orders.to_csv(out("orders.csv"), index=False)
    customers_regions.to_csv(out("customers_regions.csv"), index=False)


# --- Trap 2: day/month date ambiguity ------------------------------------------
# Dates written DD/MM/YYYY. A naive MM/DD parse silently mangles rows where day<=12, and
# ERRORS or misreads on day>12. Includes 13/01 and 25/12 which are unambiguous DD/MM tells.
def dates():
    df = pd.DataFrame({
        "event_id": range(1, 9),
        "event_date": ["01/02/2024", "13/01/2024", "25/12/2023", "03/04/2024",
                       "31/05/2024", "07/08/2024", "12/11/2024", "28/02/2024"],
        "value": [10, 12, 9, 11, 14, 13, 8, 10],
    })
    df.to_csv(out("events_ddmm.csv"), index=False)


# --- Trap 3: non-normal small-n comparison -------------------------------------
# Two groups, n=12 each, heavily right-skewed (lognormal) with an outlier. A t-test is the
# wrong call; assumption_gate.py must route to nonparametric/bootstrap.
def nonnormal_smalln():
    a = RNG.lognormal(mean=1.0, sigma=1.0, size=12)
    b = RNG.lognormal(mean=1.2, sigma=1.0, size=12)
    a[0] = a[0] * 20  # a fat outlier
    df = pd.DataFrame({
        "group": ["A"] * 12 + ["B"] * 12,
        "response": np.concatenate([a, b]).round(3),
    })
    df.to_csv(out("small_n_groups.csv"), index=False)


# --- Trap 4: Simpson's paradox stratification ----------------------------------
# Overall, treatment looks WORSE than control, but within every severity stratum it is
# BETTER. Classic confounding by severity (sicker patients got treatment more often).
def simpsons():
    rows = []
    # mild stratum: treatment mostly avoided; both do well, treatment slightly better
    # severe stratum: treatment mostly used; both do worse, treatment slightly better
    # aggregate reverses because treatment is concentrated in the severe stratum.
    def block(severity, treated, n, success_rate):
        for _ in range(n):
            rows.append({
                "patient_id": len(rows) + 1,
                "severity": severity,
                "treatment": treated,
                "recovered": int(RNG.random() < success_rate),
            })
    block("mild", "control", 100, 0.90)
    block("mild", "treatment", 20, 0.93)
    block("severe", "control", 20, 0.30)
    block("severe", "treatment", 100, 0.35)
    pd.DataFrame(rows).to_csv(out("simpsons_recovery.csv"), index=False)


# --- Trap 5: implicit multi-test bait ------------------------------------------
# 20 candidate features vs a binary outcome, all pure noise (no real relationship). Scanning
# for "which feature predicts outcome" will surface ~1 spurious p<0.05 by chance. A test log
# is emitted so multiplicity_audit.py can show it does not survive BH-FDR.
def multitest():
    n = 200
    data = {f"feat_{i:02d}": RNG.normal(size=n) for i in range(20)}
    data["outcome"] = RNG.integers(0, 2, size=n)  # independent of every feature
    pd.DataFrame(data).to_csv(out("multitest_features.csv"), index=False)

    # a pre-baked test-counter log: 20 p-values, ~1 under 0.05 by chance, none real.
    # Uses scipy if present; otherwise a normal-approximation two-sided p from Pearson r,
    # so the fixture generator runs without the stats stack installed.
    df = pd.DataFrame(data)
    try:
        from scipy import stats as st

        def pval(y, x):
            return float(st.pointbiserialr(y, x)[1])
    except ImportError:
        def pval(y, x):
            y = np.asarray(y, dtype=float)
            x = np.asarray(x, dtype=float)
            r = np.corrcoef(y, x)[0, 1]
            nn = len(y)
            # Fisher z -> two-sided normal-approx p (adequate for a fixture log)
            r = min(max(r, -0.999999), 0.999999)
            z = np.arctanh(r) * np.sqrt(nn - 3)
            return float(2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))))

    lines = []
    for i in range(20):
        col = f"feat_{i:02d}"
        lines.append(f"{pval(df['outcome'], df[col]):.5f}\toutcome ~ {col}")
    with open(out("multitest_counter.log"), "w", encoding="utf-8") as fh:
        fh.write("# p-value <tab> label  (20 features scanned against outcome)\n")
        fh.write("\n".join(lines) + "\n")


# --- Trap 6: leakage bait ------------------------------------------------------
# A churn dataset with a feature 'days_since_cancellation' that only has a value for churned
# customers - it is a downstream consequence of the label, not a predictor available at
# prediction time. Using it gives near-perfect accuracy (leakage). expected.md documents it.
def leakage():
    n = 300
    churned = RNG.integers(0, 2, size=n)
    df = pd.DataFrame({
        "customer_id": range(1, n + 1),
        "tenure_months": RNG.integers(1, 60, size=n),
        "monthly_spend": RNG.normal(50, 15, size=n).round(2),
        "support_tickets": RNG.poisson(2, size=n),
        # LEAKY: defined only when churned==1, NaN otherwise. A proxy for the target.
        "days_since_cancellation": np.where(churned == 1, RNG.integers(1, 90, size=n), np.nan),
        "churned": churned,
    })
    df.to_csv(out("churn_leakage.csv"), index=False)


# --- Trap 7: baseline bait -----------------------------------------------------
# A "new model" scores file. The prompt will claim a big improvement "over the old model".
# The old model's scores are present and must be re-run/compared in-session, not taken on
# faith. Here the "improvement" partly evaporates once the baseline is actually computed.
def baseline():
    n = 500
    y_true = RNG.integers(0, 2, size=n)
    # old model: decent. new model: marginally better, NOT the dramatic lift a prompt claims.
    old_pred = np.where(RNG.random(n) < 0.78, y_true, 1 - y_true)
    new_pred = np.where(RNG.random(n) < 0.81, y_true, 1 - y_true)
    pd.DataFrame({
        "id": range(1, n + 1),
        "y_true": y_true,
        "old_model_pred": old_pred,
        "new_model_pred": new_pred,
    }).to_csv(out("model_scores.csv"), index=False)


def main():
    fanout()
    dates()
    nonnormal_smalln()
    simpsons()
    multitest()
    leakage()
    baseline()
    print("fixtures written to", HERE)
    for f in sorted(os.listdir(HERE)):
        if f.endswith((".csv", ".log")):
            print("  -", f)


if __name__ == "__main__":
    main()

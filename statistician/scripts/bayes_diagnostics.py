#!/usr/bin/env python3
"""bayes_diagnostics.py - deterministic convergence verdicts for the Bayesian route.

A Bayesian model that has not converged produces confident nonsense, and the LLM cannot be
trusted to eyeball a trace and rule on it. This script hands the ruling to ArviZ: it reads an
inference object (NetCDF / .nc from arviz.to_netcdf, or a directory ArviZ can load) and prints
PASS/FAIL verdicts on the standard diagnostics, so only the diagnostics may certify a posterior.

Verdicts:
  - R-hat   : FAIL if any parameter's R-hat >= 1.01 (chains not mixed).
  - ESS     : FAIL if bulk or tail ESS < 400 for any parameter (too few effective samples).
  - Divergences: FAIL if any divergent transitions (sampler could not explore the geometry).
  - LOO Pareto-k (if the object has log-likelihood): WARN on k>0.7 observations.

CLI:
  python bayes_diagnostics.py idata.nc
  python bayes_diagnostics.py idata.nc --ess-min 400 --rhat-max 1.01

Exit code is non-zero if any diagnostic FAILs, so it can gate the model.

Deps: arviz (required). If arviz is missing the script prints exactly what to install and exits
2 rather than faking a verdict - it never certifies a model it could not actually check. If the
Bayesian work runs under the baygent or pymc-labs skills instead, use their diagnostic gate;
this is the vendored fallback for the condensed workflow.
"""
from __future__ import annotations

import argparse
import sys


def _die_missing(pkg, why):
    sys.stderr.write(
        f"[bayes_diagnostics] missing dependency: {pkg}\n"
        f"  needed for: {why}\n  install:    pip install {pkg}\n"
    )
    raise SystemExit(2)


def _import_arviz():
    """Import arviz + numpy lazily so --help works without the dependency installed."""
    try:
        import arviz as az
        import numpy as np
        return az, np
    except ImportError:
        _die_missing("arviz", "R-hat / ESS / divergence / LOO diagnostics on the posterior")


def _load(path, az):
    try:
        return az.from_netcdf(path)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[bayes_diagnostics] could not load inference data from {path}: {exc}\n")
        sys.stderr.write("  expected a NetCDF file written by arviz.InferenceData.to_netcdf().\n")
        raise SystemExit(2)


def diagnose(idata, rhat_max, ess_min, az, np):
    print("=" * 70)
    print("BAYESIAN CONVERGENCE DIAGNOSTICS")
    print("=" * 70)
    failed = []

    # R-hat
    try:
        rhat = az.rhat(idata)
        worst_rhat = float(max(float(rhat[v].max()) for v in rhat.data_vars))
        ok = worst_rhat < rhat_max
        print(f"  R-hat   : worst={worst_rhat:.4f}  threshold<{rhat_max}  -> "
              f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append(f"R-hat {worst_rhat:.4f} >= {rhat_max} (chains not mixed)")
    except Exception as exc:  # noqa: BLE001
        print(f"  R-hat   : could not compute ({exc})")

    # ESS (bulk + tail)
    try:
        ess_bulk = az.ess(idata, method="bulk")
        ess_tail = az.ess(idata, method="tail")
        min_bulk = float(min(float(ess_bulk[v].min()) for v in ess_bulk.data_vars))
        min_tail = float(min(float(ess_tail[v].min()) for v in ess_tail.data_vars))
        ok = min_bulk >= ess_min and min_tail >= ess_min
        print(f"  ESS     : min bulk={min_bulk:.0f}, min tail={min_tail:.0f}  threshold>={ess_min}"
              f"  -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append(f"ESS below {ess_min} (bulk={min_bulk:.0f}, tail={min_tail:.0f})")
    except Exception as exc:  # noqa: BLE001
        print(f"  ESS     : could not compute ({exc})")

    # Divergences
    try:
        n_div = None
        if hasattr(idata, "sample_stats") and "diverging" in idata.sample_stats:
            n_div = int(np.asarray(idata.sample_stats["diverging"]).sum())
        if n_div is None:
            print("  Diverg. : no sample_stats.diverging in the object (skipped)")
        else:
            ok = n_div == 0
            print(f"  Diverg. : {n_div} divergent transitions  -> {'PASS' if ok else 'FAIL'}")
            if not ok:
                failed.append(f"{n_div} divergent transitions (biased exploration)")
    except Exception as exc:  # noqa: BLE001
        print(f"  Diverg. : could not compute ({exc})")

    # LOO Pareto-k (only if log-likelihood present)
    try:
        if hasattr(idata, "log_likelihood"):
            loo = az.loo(idata, pointwise=True)
            k = np.asarray(loo.pareto_k)
            n_bad = int((k > 0.7).sum())
            print(f"  LOO k   : {n_bad} observation(s) with Pareto-k>0.7  -> "
                  f"{'WARN' if n_bad else 'OK'}")
            if n_bad:
                print("            (LOO estimate unreliable for those points; do not compare "
                      "models on it without refitting/PSIS-checks.)")
        else:
            print("  LOO k   : no log_likelihood in the object (skipped)")
    except Exception as exc:  # noqa: BLE001
        print(f"  LOO k   : could not compute ({exc})")

    print("-" * 70)
    if failed:
        print("VERDICT: DO NOT TRUST THIS POSTERIOR.")
        for f in failed:
            print(f"  - {f}")
        print("  Reparameterize, raise target_accept, or draw more samples, then re-run.")
        rc = 1
    else:
        print("VERDICT: converged - the posterior may be summarized (report credible intervals).")
        rc = 0
    print("=" * 70)
    return rc


def main(argv=None):
    p = argparse.ArgumentParser(description="Deterministic Bayesian convergence verdicts (ArviZ).")
    p.add_argument("idata", help="InferenceData as NetCDF (.nc) from arviz.to_netcdf")
    p.add_argument("--rhat-max", type=float, default=1.01, help="R-hat failure threshold")
    p.add_argument("--ess-min", type=float, default=400.0, help="minimum acceptable ESS")
    args = p.parse_args(argv)
    az, np = _import_arviz()
    idata = _load(args.idata, az)
    return diagnose(idata, args.rhat_max, args.ess_min, az, np)


if __name__ == "__main__":
    raise SystemExit(main())

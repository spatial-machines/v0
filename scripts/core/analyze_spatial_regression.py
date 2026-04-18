#!/usr/bin/env python3
"""Spatial regression pipeline: OLS → diagnostics → Spatial Lag or Spatial Error.

Workflow:
  1. Run OLS (spreg.OLS)
  2. Run Lagrange Multiplier tests to diagnose spatial dependence
  3. If LM-Lag significant and not LM-Error → Spatial Lag model
     If LM-Error significant and not LM-Lag → Spatial Error model
     If both significant → use robust versions to decide, or run both
     If neither significant → report OLS results, note no spatial pattern in residuals
  4. Output: model results table, residual map, model selection rationale, handoff JSON

Usage:
    python analyze_spatial_regression.py \\
        --input data/processed/tracts_poverty.gpkg \\
        --dependent poverty_rate \\
        --independent uninsured_rate median_age pct_rural \\
        [--output outputs/regression/poverty_model.json] \\
        [--output-map outputs/maps/poverty_residuals.png] \\
        [--weights queen]
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).parent.parent


def build_weights(gdf, kind="queen"):
    from libpysal.weights import Queen, Rook, KNN
    kind = kind.lower()
    if kind == "queen":
        w = Queen.from_dataframe(gdf, silence_warnings=True)
    elif kind == "rook":
        w = Rook.from_dataframe(gdf, silence_warnings=True)
    elif kind.startswith("knn"):
        k = int(kind.replace("knn", "") or "5")
        w = KNN.from_dataframe(gdf, k=k, silence_warnings=True)
    else:
        w = Queen.from_dataframe(gdf, silence_warnings=True)
    w.transform = "R"
    return w


def format_stars(pval):
    if pval < 0.001:
        return "***"
    if pval < 0.01:
        return "**"
    if pval < 0.05:
        return "*"
    if pval < 0.1:
        return "."
    return ""


def summarize_ols(model):
    rows = []
    for i, name in enumerate(model.name_x):
        rows.append({
            "variable": name,
            "coefficient": round(float(model.betas[i][0]), 6),
            "std_error": round(float(model.std_err[i]), 6),
            "t_stat": round(float(model.t_stat[i][0]), 4),
            "p_value": round(float(model.t_stat[i][1]), 4),
            "significance": format_stars(model.t_stat[i][1]),
        })
    return rows


def summarize_spatial(model, model_type):
    rows = []
    # spreg spatial models have z_stat
    for i, name in enumerate(model.name_x):
        rows.append({
            "variable": name,
            "coefficient": round(float(model.betas[i][0]), 6),
            "std_error": round(float(model.std_err[i]), 6),
            "z_stat": round(float(model.z_stat[i][0]), 4),
            "p_value": round(float(model.z_stat[i][1]), 4),
            "significance": format_stars(model.z_stat[i][1]),
        })
    if model_type == "lag":
        rho = float(model.rho)
        rows.append({
            "variable": "Spatial Lag (rho)",
            "coefficient": round(rho, 6),
            "std_error": None,
            "z_stat": None,
            "p_value": None,
            "significance": "",
        })
    elif model_type == "error":
        lam = float(model.lam)
        rows.append({
            "variable": "Spatial Error (lambda)",
            "coefficient": round(lam, 6),
            "std_error": None,
            "z_stat": None,
            "p_value": None,
            "significance": "",
        })
    return rows


def plot_residuals(gdf, residuals, title, out_path, model_type="OLS"):
    import matplotlib.colors as mcolors

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    gdf_plot = gdf.copy()
    gdf_plot["_residual"] = residuals

    # Diverging colormap centered on 0
    vmax = float(np.abs(residuals).quantile(0.95))
    vmin = -vmax

    gdf_plot.plot(
        column="_residual",
        ax=ax,
        cmap="RdBu_r",
        vmin=vmin,
        vmax=vmax,
        legend=True,
        legend_kwds={
            "label": "Residual",
            "orientation": "vertical",
            "shrink": 0.6,
            "pad": 0.01,
        },
        edgecolor="white",
        linewidth=0.18,
    )

    try:
        gdf_plot.dissolve().boundary.plot(ax=ax, edgecolor="#333333", linewidth=1.2, zorder=10)
    except Exception:
        pass

    ax.set_title(f"{title} — {model_type} Residuals", fontsize=14, fontweight="bold", loc="left", pad=12)
    ax.set_axis_off()
    ax.text(0.99, 0.01, "Blue = underpredicted  |  Red = overpredicted",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#666")

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved residual map: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--layer", default=None, help="Layer name within GeoPackage")
    parser.add_argument("--dependent", required=True, help="Dependent variable column")
    parser.add_argument("--independent", nargs="+", required=True, help="Independent variable columns")
    parser.add_argument("--weights", default="queen", help="Spatial weights: queen, rook, knnN (default: queen)")
    parser.add_argument("-o", "--output", help="Output JSON results path")
    parser.add_argument("--output-map", help="Output residual map PNG path")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"Input not found: {src}")
        return 1

    gdf = gpd.read_file(src, layer=args.layer) if args.layer else gpd.read_file(src)
    print(f"Loaded {len(gdf)} features")

    # Prep data — drop nulls in dependent + independent
    cols = [args.dependent] + args.independent
    missing = [c for c in cols if c not in gdf.columns]
    if missing:
        print(f"Columns not found: {missing}")
        print(f"Available: {[c for c in gdf.columns if c != 'geometry']}")
        return 2

    for col in cols:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")

    gdf_clean = gdf.dropna(subset=cols).copy()
    n_dropped = len(gdf) - len(gdf_clean)
    if n_dropped > 0:
        print(f"Dropped {n_dropped} rows with nulls in model variables")
    if len(gdf_clean) < 30:
        print(f"WARNING: Only {len(gdf_clean)} observations — results may be unreliable")

    y = gdf_clean[[args.dependent]].values
    x_cols = args.independent
    X = gdf_clean[x_cols].values

    # Build weights
    print(f"Building {args.weights} spatial weights...")
    w = build_weights(gdf_clean, args.weights)

    # 1. OLS
    print("Running OLS...")
    from spreg import OLS
    ols = OLS(
        y, X,
        w=w,
        name_y=args.dependent,
        name_x=x_cols,
        spat_diag=True,
        moran=True,
    )

    print(f"\n--- OLS Results ---")
    print(f"R²: {ols.r2:.4f}  |  Adj R²: {ols.ar2:.4f}  |  AIC: {ols.aic:.2f}")
    print(f"Moran's I (residuals): {ols.moran_res[0]:.4f}  p={ols.moran_res[1]:.4f}")

    # LM diagnostics
    lm_lag = ols.lm_lag
    lm_error = ols.lm_error
    rlm_lag = ols.rlm_lag
    rlm_error = ols.rlm_error

    print(f"\n--- Lagrange Multiplier Diagnostics ---")
    print(f"LM-Lag:       stat={lm_lag[0]:.4f}  p={lm_lag[1]:.4f}{format_stars(lm_lag[1])}")
    print(f"LM-Error:     stat={lm_error[0]:.4f}  p={lm_error[1]:.4f}{format_stars(lm_error[1])}")
    print(f"Robust LM-Lag:   stat={rlm_lag[0]:.4f}  p={rlm_lag[1]:.4f}{format_stars(rlm_lag[1])}")
    print(f"Robust LM-Error: stat={rlm_error[0]:.4f}  p={rlm_error[1]:.4f}{format_stars(rlm_error[1])}")

    # Model selection
    lag_sig = lm_lag[1] < 0.05
    error_sig = lm_error[1] < 0.05
    rlm_lag_sig = rlm_lag[1] < 0.05
    rlm_error_sig = rlm_error[1] < 0.05

    if not lag_sig and not error_sig:
        selected_model = "ols"
        rationale = "Neither LM-Lag nor LM-Error significant. OLS residuals show no spatial dependence. OLS is appropriate."
    elif lag_sig and not error_sig:
        selected_model = "lag"
        rationale = "LM-Lag significant, LM-Error not. Spatial Lag model selected."
    elif error_sig and not lag_sig:
        selected_model = "error"
        rationale = "LM-Error significant, LM-Lag not. Spatial Error model selected."
    else:
        # Both significant — use robust tests
        if rlm_lag_sig and not rlm_error_sig:
            selected_model = "lag"
            rationale = "Both LM tests significant. Robust LM-Lag significant, Robust LM-Error not → Spatial Lag selected."
        elif rlm_error_sig and not rlm_lag_sig:
            selected_model = "error"
            rationale = "Both LM tests significant. Robust LM-Error significant, Robust LM-Lag not → Spatial Error selected."
        else:
            selected_model = "lag"
            rationale = "Both LM and Robust LM tests significant. Defaulting to Spatial Lag (common choice when ambiguous). Consider running both and comparing AIC."

    print(f"\n→ Model selection: {selected_model.upper()}")
    print(f"  {rationale}")

    result = {
        "step": "analyze_spatial_regression",
        "source": str(src),
        "dependent": args.dependent,
        "independent": args.independent,
        "n_observations": len(gdf_clean),
        "n_dropped_nulls": n_dropped,
        "weights": args.weights,
        "model_selected": selected_model,
        "model_selection_rationale": rationale,
        "ols": {
            "r2": round(float(ols.r2), 4),
            "r2_adj": round(float(ols.ar2), 4),
            "aic": round(float(ols.aic), 2),
            "moran_i_residuals": round(float(ols.moran_res[0]), 4),
            "moran_p": round(float(ols.moran_res[1]), 4),
            "lm_lag": {"stat": round(float(lm_lag[0]), 4), "p": round(float(lm_lag[1]), 4)},
            "lm_error": {"stat": round(float(lm_error[0]), 4), "p": round(float(lm_error[1]), 4)},
            "rlm_lag": {"stat": round(float(rlm_lag[0]), 4), "p": round(float(rlm_lag[1]), 4)},
            "rlm_error": {"stat": round(float(rlm_error[0]), 4), "p": round(float(rlm_error[1]), 4)},
            "coefficients": summarize_ols(ols),
        },
    }

    # 2. Spatial model
    final_model = ols
    final_residuals = ols.u.flatten()

    if selected_model == "lag":
        print("\nRunning Spatial Lag model...")
        from spreg import ML_Lag
        lag_model = ML_Lag(y, X, w=w, name_y=args.dependent, name_x=x_cols)
        print(f"Spatial Lag — Pseudo-R²: {lag_model.pr2:.4f}  |  AIC: {lag_model.aic:.2f}  |  ρ={lag_model.rho:.4f}")
        result["spatial_lag"] = {
            "pseudo_r2": round(float(lag_model.pr2), 4),
            "aic": round(float(lag_model.aic), 2),
            "rho": round(float(lag_model.rho), 4),
            "coefficients": summarize_spatial(lag_model, "lag"),
        }
        final_model = lag_model
        final_residuals = lag_model.u.flatten()

    elif selected_model == "error":
        print("\nRunning Spatial Error model...")
        from spreg import ML_Error
        err_model = ML_Error(y, X, w=w, name_y=args.dependent, name_x=x_cols)
        print(f"Spatial Error — Pseudo-R²: {err_model.pr2:.4f}  |  AIC: {err_model.aic:.2f}  |  λ={err_model.lam:.4f}")
        result["spatial_error"] = {
            "pseudo_r2": round(float(err_model.pr2), 4),
            "aic": round(float(err_model.aic), 2),
            "lambda": round(float(err_model.lam), 4),
            "coefficients": summarize_spatial(err_model, "error"),
        }
        final_model = err_model
        final_residuals = err_model.u.flatten()

    # Residual map
    map_path = args.output_map
    if not map_path:
        map_dir = PROJECT_ROOT / "outputs" / "maps"
        map_path = str(map_dir / f"{src.stem}_{args.dependent}_residuals.png")

    plot_residuals(
        gdf_clean,
        pd.Series(final_residuals, index=gdf_clean.index),
        title=f"{args.dependent.replace('_', ' ').title()}",
        out_path=map_path,
        model_type=selected_model.upper(),
    )
    result["output_map"] = map_path

    # Output JSON
    if args.output:
        out_path = Path(args.output).expanduser().resolve()
    else:
        out_dir = PROJECT_ROOT / "outputs" / "regression"
        out_path = out_dir / f"{src.stem}_{args.dependent}_regression.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved results: {out_path}")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
calibrate.py - fit the wear calibration on one tool, test it blind on another.

Fits VB = m * rise + c on the FIT_CASE, then applies that calibration,
unchanged, to TEST_CASE - a different insert run at the same cutting
conditions. Fitting and testing on the same data would prove nothing, so the
reported error is the out-of-sample one.

    python calibrate.py [--runs runs.csv] [--plots]
"""

import argparse

import numpy as np
import pandas as pd

FIT_CASE = 3
TEST_CASE = 11
VB_CRIT = 0.30   # mm, flank wear limit per ISO 3685


def load(path, case):
    df = pd.read_csv(path)
    return df[(df.case == case)].dropna(subset=["VB_mm", "rise"])


def fit(df):
    """Least-squares straight line through rise vs measured VB."""
    m, c = np.polyfit(df["rise"], df["VB_mm"], 1)
    pred = m * df["rise"] + c
    ss_res = ((df["VB_mm"] - pred) ** 2).sum()
    ss_tot = ((df["VB_mm"] - df["VB_mm"].mean()) ** 2).sum()
    return m, c, 1 - ss_res / ss_tot


def report(df, m, c):
    """Apply the calibration and summarise the error.

    Sign convention: error = predicted - measured. A positive error means the
    estimate claims MORE wear than the microscope found, which is the safe
    direction; negative means it claims less.
    """
    df = df.copy()
    df["VB_pred"] = m * df["rise"] + c
    df["error"] = df["VB_pred"] - df["VB_mm"]

    print(df[["run", "VB_mm", "rise", "VB_pred", "error"]].round(4).to_string(index=False))

    below = df[df.VB_mm <= VB_CRIT]
    above = df[df.VB_mm > VB_CRIT]
    print(f"\nn = {len(df)}")
    print(f"MAE  overall              {df['error'].abs().mean():.4f} mm")
    print(f"worst single error        {df['error'].abs().max():.4f} mm")
    print(f"MAE  VB <= {VB_CRIT:.2f} mm (n={len(below):2d})  {below['error'].abs().mean():.4f} mm"
          f"   mean error {below['error'].mean():+.4f} mm")
    print(f"MAE  VB >  {VB_CRIT:.2f} mm (n={len(above):2d})  {above['error'].abs().mean():.4f} mm"
          f"   mean error {above['error'].mean():+.4f} mm")
    return df


def plots(fit_df, test_df, m, c, r2):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

    xs = np.linspace(0, fit_df["rise"].max() * 1.05, 50)
    ax[0].plot(xs, m * xs + c)
    ax[0].scatter(fit_df["rise"], fit_df["VB_mm"])
    ax[0].axhline(VB_CRIT, linestyle="--")
    ax[0].set_xlabel("current rise vs fresh tool")
    ax[0].set_ylabel("measured VB (mm)")
    ax[0].set_title(f"case {FIT_CASE} - calibration  (R2 = {r2:.2f}, n = {len(fit_df)})")

    ax[1].plot(test_df["run"], test_df["VB_mm"], "o-", label="measured (microscope)")
    ax[1].plot(test_df["run"], test_df["VB_pred"], "s--", label="estimated from current")
    ax[1].axhline(VB_CRIT, linestyle="--", label=f"wear limit {VB_CRIT} mm")
    ax[1].set_xlabel("run")
    ax[1].set_ylabel("VB (mm)")
    ax[1].legend()
    ax[1].set_title(f"case {TEST_CASE} - calibration fitted on a different tool")

    plt.tight_layout()
    plt.show()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", default="runs.csv")
    p.add_argument("--plots", action="store_true")
    args = p.parse_args()

    fit_df = load(args.runs, FIT_CASE)
    m, c, r2 = fit(fit_df)
    print(f"calibration on case {FIT_CASE}:  "
          f"VB = {m:.4f} * rise + {c:.4f}   R2 = {r2:.4f}   n = {len(fit_df)}")
    print(f"intercept {c:.4f} mm is what the line claims for a fresh tool; "
          f"measured VB at run 1 is {fit_df['VB_mm'].iloc[0]:.2f} mm "
          f"- the gap is break-in wear the linear form cannot follow.\n")

    test_df = report(load(args.runs, TEST_CASE), m, c)

    if args.plots:
        plots(fit_df, test_df, m, c, r2)


if __name__ == "__main__":
    main()

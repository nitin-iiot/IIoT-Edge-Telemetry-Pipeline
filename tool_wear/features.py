"""
features.py - reduce the NASA milling recordings to one table row per cut.

Reads mill.mat, isolates the steady cutting portion of every sensor trace,
reduces each trace to mean and RMS, drops corrupted recordings, computes the
relative current rise against each tool's own first cut, and writes runs.csv.

    python features.py [--mat mill.mat] [--out runs.csv]

mill.mat is the public NASA milling dataset and is not redistributed with
this repository - see README for the download link.
"""

import argparse

import numpy as np
import pandas as pd
import scipy.io as sio

SENSORS = ["smcAC", "smcDC", "vib_table", "vib_spindle", "AE_table", "AE_spindle"]

WINDOW_FRAC = 0.5   # keep samples whose magnitude exceeds this fraction of the
                    # rough cutting level; set by eye in explore.py, step 3
MIN_WINDOW = 1000   # if the threshold keeps fewer samples than this, the trace
                    # is not shaped like a normal cut - fall back to middle 60%
CORRUPT_FACTOR = 10  # drop a run whose smcAC_rms exceeds this multiple of its
                     # own case median; Traini et al. report 33 such signals
                     # in 1020, orders of magnitude beyond anything physical


def cutting_window(sig):
    """Return the part of `sig` where the machine was actually cutting.

    The ramp-up and ramp-down at each end of a recording are not comparable
    between runs; only the flat middle is. A fixed fraction would assume every
    run has the same shape, so each run sets its own threshold instead.

    Two passes: take the middle 60% as a rough idea of the cutting level, then
    keep every sample whose magnitude clears WINDOW_FRAC of it. Magnitude, not
    raw value, so the same rule works for AC (a band centred near zero) and DC
    (a level).
    """
    mag = np.abs(sig)
    a, b = int(0.2 * len(sig)), int(0.8 * len(sig))
    level = mag[a:b].mean()
    keep = sig[mag > WINDOW_FRAC * level]
    return keep if len(keep) > MIN_WINDOW else sig[a:b]


def scalar(rec, field):
    """Pull a single number out of a record field.

    VB is absent on some runs and arrives as an empty array, so check .size
    before indexing.
    """
    v = rec[field]
    return float(v.flatten()[0]) if v.size else np.nan


def make_row(rec):
    """Reduce one recording to a single table row."""
    row = {
        "case": int(scalar(rec, "case")),
        "run": int(scalar(rec, "run")),
        "VB_mm": scalar(rec, "VB"),
        "feed_mm": scalar(rec, "feed"),
        "DOC_mm": scalar(rec, "DOC"),
        "material": int(scalar(rec, "material")),
    }
    for s in SENSORS:
        w = cutting_window(rec[s].flatten())
        row[f"{s}_mean"] = w.mean()
        row[f"{s}_rms"] = np.sqrt(np.mean(w ** 2))
    return row


def drop_corrupted(df):
    """Remove runs whose AC current RMS is implausible for their own case.

    A case median is used rather than a mean so that one corrupted run cannot
    raise the threshold enough to hide itself.
    """
    med = df.groupby("case")["smcAC_rms"].transform("median")
    bad = df["smcAC_rms"] > CORRUPT_FACTOR * med
    if bad.any():
        pairs = ", ".join(f"case {c} run {r}"
                          for c, r in zip(df.loc[bad, "case"], df.loc[bad, "run"]))
        print(f"dropping {int(bad.sum())} corrupted run(s): {pairs}")
    return df[~bad].reset_index(drop=True)


def add_rise(df):
    """Add the relative AC current rise against each tool's own first cut.

    The sensor units are undocumented, so absolute values carry no meaning; a
    ratio against the tool's own run 1 cancels the unknown gain.

    If run 1 of a case was dropped as corrupted, there is no fresh-tool
    reference: transform("first") would silently take the next surviving run,
    which is already partly worn. Those cases get NaN instead of a wrong
    number.
    """
    df = df.sort_values(["case", "run"]).reset_index(drop=True)
    first_run = df.groupby("case")["run"].transform("min")
    baseline = df.groupby("case")["smcAC_rms"].transform("first")

    df["rise"] = (df["smcAC_rms"] - baseline) / baseline

    no_ref = first_run != 1
    if no_ref.any():
        lost = sorted(df.loc[no_ref, "case"].unique())
        print(f"no fresh-tool baseline for case(s) {lost} - run 1 missing; "
              f"rise set to NaN")
        df.loc[no_ref, "rise"] = np.nan
    return df


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mat", default="mill.mat")
    p.add_argument("--out", default="runs.csv")
    args = p.parse_args()

    mill = sio.loadmat(args.mat)["mill"]
    print(f"{mill.shape[1]} recordings in {args.mat}")

    df = pd.DataFrame([make_row(mill[0, i]) for i in range(mill.shape[1])])
    df = drop_corrupted(df)
    df = add_rise(df)
    df.to_csv(args.out, index=False)

    print(f"wrote {args.out}: {len(df)} runs, {df.case.nunique()} tools, "
          f"{int(df.VB_mm.notna().sum())} with a measured VB")


if __name__ == "__main__":
    main()

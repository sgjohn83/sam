#!/usr/bin/env python3
"""Draw every results figure of the paper from the stored results.

    python3 figures.py            writes PNG and PDF files into figures/

Every number drawn is read from results/. Nothing is typed in by hand.
Before drawing, the script checks the inputs against each other: the
sweep files against their sealed hashes, the selection rule against the
sealed operating points, and every carried interval against the sealed
point estimates. Any disagreement stops the build.

Figures produced
    Figure 3   unlinkability across the 80-configuration design space
    Figure 4   recognition and unlinkability frontier
    Figure 5   development, held-out and external results with intervals
    Figure 6   ablation: the three arms on EER and Dsys
    Figure 7   revocation, one dot per fresh key
    Figure 8   inversion: threshold reached and embedding recovered
    Figure S2  how the operating point was selected
    Figure P   protection cost against the unprotected baseline

Not produced here: the DET curves and score distributions (paper Figures
A to D, left panels). They need the per-comparison score histograms,
which are not in this package; see code/runtime/figures_only.py.

Needs numpy and matplotlib. The drawing itself lives in
code/runtime/results_plots.py, shared with the ALL_FIGURES notebook.
"""


import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
OUT = HERE / "figures"

# The drawing code is shared with the ALL_FIGURES Colab notebook, which
# draws the same figures from results it computes itself.
_spec = importlib.util.spec_from_file_location(
    "results_plots", HERE / "code" / "runtime" / "results_plots.py")
results_plots = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(results_plots)

# Hashes of the two sealed sweeps, as recorded in RESULTS_SUMMARY.md.
SWEEP_SHA256 = {
    "face": "89f28dc86a7844144afdb0be9ab7f2f2a4625ccc908d81993788083e07f079e2",
    "voice": "819232a6f9868cda2f4aea245a2da769400980e6141ca47e5c17eae3956abac1",
}
# Recognition floors of the selection rule (paper Sections 4.4 and 5.1):
# (maximum EER, minimum TAR) on the development identities.
FLOOR = {"voice": (0.01, 0.95), "face": (0.03, 0.85)}


def check(cond, what):
    if not cond:
        raise SystemExit(f"input check failed: {what}")


def close(a, b, tol):
    return abs(a - b) <= tol


def jload(rel):
    return json.loads((RES / rel).read_text())


# ================================================================== inputs
def load_sweep(mod):
    path = RES / "sweep" / f"{mod}_sweep_80.csv"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    check(digest == SWEEP_SHA256[mod], f"{path.name} does not match its sealed hash")
    rows = list(csv.DictReader(path.open()))
    for r in rows:
        for k in ("EER", "TAR_DEV", "FMR_DEV", "Dsys_DEV"):
            r[k] = float(r[k])
        for k in ("M", "q", "o"):
            r[k] = int(r[k])
    check(len(rows) == 80, f"{mod} sweep has {len(rows)} rows, expected 80")
    return rows


def eligible(rows, mod):
    e, t = FLOOR[mod]
    return [r for r in rows if r["EER"] <= e and r["TAR_DEV"] >= t]


SWEEP = {m: load_sweep(m) for m in ("face", "voice")}
HELD = {m: jload(f"heldout/{m}_heldout_result.json") for m in ("face", "voice")}
EXT = jload("external/voice_external_result.json")
ABL = jload("ablation/ablation_result.json")["modalities"]
REV = jload("revocation/revocation_result.json")
INV = jload("inversion/inversion_result.json")["modalities"]
BASE = jload("scores/unprotected_baseline.json")
CIS = jload("heldout/confidence_intervals.json")["partitions"]

# The selection rule, re-run on the sweeps, must give the sealed points.
SEL = {}
for mod in ("face", "voice"):
    h = HELD[mod]
    sealed = (h["M"], h["q"], h["o"])
    elig = eligible(SWEEP[mod], mod)
    best = min(elig, key=lambda r: r["Dsys_DEV"])
    check((best["M"], best["q"], best["o"]) == sealed,
          f"{mod}: selection rule picks {best['M'], best['q'], best['o']}, sealed {sealed}")
    dev = h["development_reference"]
    check(close(best["EER"], dev["EER"], 1e-9) and
          close(best["Dsys_DEV"], dev["Dsys_DEV"], 1e-9),
          f"{mod}: sweep row differs from the sealed development reference")
    SEL[mod] = best
    print(f"  {mod}: {len(elig)} of 80 settings meet the floor; the rule "
          f"selects M={sealed[0]} q={sealed[1]} o={sealed[2]}, as sealed")

# Carried intervals: each point must equal the sealed point estimate.
SEALED_POINT = {
    "voice/evaluation": (HELD["voice"], "HOLDOUT"),
    "face/evaluation": (HELD["face"], "HOLDOUT"),
    "voice/external": (EXT, "EXT"),
}
for part, (res, tag) in SEALED_POINT.items():
    sealed = {"EER": res[f"EER_{tag}"] * 100,
              "TAR": res[f"TAR_{tag}_at_dev_threshold"] * 100,
              "FMR": res[f"FMR_{tag}_at_dev_threshold"] * 100,
              "Dsys": res[f"Dsys_{tag}"]}
    for k, (p, lo, hi) in CIS[part].items():
        tol = 5e-4 if k != "Dsys" else 5e-6
        check(close(p, sealed[k], tol), f"{part} {k}: {p} vs sealed {sealed[k]:.6f}")
        check(lo <= p <= hi, f"{part} {k}: interval does not contain its point")


def clopper_pearson_upper(k, n, conf=0.95):
    """One-sided upper bound on a binomial rate, by bisection."""
    alpha = 1 - conf
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i)
                  for i in range(k + 1))
        lo, hi = (mid, hi) if cdf > alpha else (lo, mid)
    return hi


for p in BASE["partitions"]:
    k = math.floor(p["unprotected_eer"] / 100 * p["n_genuine"])
    ub = clopper_pearson_upper(k, p["n_genuine"]) * 100
    check(close(ub, p["unprotected_upper_bound_95"], 6e-4),
          f"{p['modality']}/{p['partition']}: bound {ub:.4f} vs stored "
          f"{p['unprotected_upper_bound_95']}")
print("  all input checks passed\n")



def main():
    data = {"sweep": SWEEP, "floor": FLOOR, "selected": SEL,
            "intervals": CIS, "baseline": BASE["partitions"],
            "ablation": ABL, "revocation": REV, "inversion": INV}
    stems = results_plots.draw_all(data, OUT)
    print(f"\n{len(stems)} figures in {OUT}")


if __name__ == "__main__":
    main()

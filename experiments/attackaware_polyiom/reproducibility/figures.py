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

Needs numpy and matplotlib.
"""

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
OUT = HERE / "figures"

# Hashes of the two sealed sweeps, as recorded in RESULTS_SUMMARY.md.
SWEEP_SHA256 = {
    "face": "89f28dc86a7844144afdb0be9ab7f2f2a4625ccc908d81993788083e07f079e2",
    "voice": "819232a6f9868cda2f4aea245a2da769400980e6141ca47e5c17eae3956abac1",
}
# Recognition floors of the selection rule (paper Sections 4.4 and 5.1):
# (maximum EER, minimum TAR) on the development identities.
FLOOR = {"voice": (0.01, 0.95), "face": (0.03, 0.85)}

# ------------------------------------------------------------------ style
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, DEEMPH, CRITICAL = "#e1e0d9", "#c3c2b7", "#c9c8c2", "#d03b3b"
VOICE, FACE = "#2a78d6", "#eb6834"
BLUES = LinearSegmentedColormap.from_list("blues", [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95",
    "#0d366b"])

ARMS = ["polyiom", "iom_only", "randproj_iom"]
LABEL = {"polyiom": "PolyIoM (ours)", "iom_only": "IoM only",
         "randproj_iom": "Linear map + IoM"}
HUE = {"polyiom": VOICE, "iom_only": FACE, "randproj_iom": "#1baf7a"}
SHAPE = {"polyiom": "o", "iom_only": "s", "randproj_iom": "^"}

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5, "axes.titlesize": 8.6, "axes.labelsize": 8.2,
    "xtick.labelsize": 7.6, "ytick.labelsize": 7.6, "legend.fontsize": 7.6,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "grid.color": GRID,
    "grid.linewidth": 0.6, "grid.linestyle": "-", "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def check(cond, what):
    if not cond:
        raise SystemExit(f"input check failed: {what}")


def close(a, b, tol):
    return abs(a - b) <= tol


def jload(rel):
    return json.loads((RES / rel).read_text())


def save(fig, stem):
    OUT.mkdir(exist_ok=True)
    # No timestamps in the files, so a rerun reproduces them byte for byte.
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight",
                metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote figures/{stem}.png and .pdf")


def style(ax, grid_axis="both"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(True, axis=grid_axis)
    ax.tick_params(length=3, pad=3)


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


# ======================================== Figure S2: operating-point selection
def figure_selection():
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.2))
    style(axa)
    for mod, col in (("face", FACE), ("voice", VOICE)):
        rows = SWEEP[mod]
        axa.scatter([r["EER"] * 100 for r in rows], [r["TAR_DEV"] * 100 for r in rows],
                    s=26, c=col, alpha=0.75, linewidths=0.7, edgecolors=SURFACE,
                    zorder=3, label=f"{mod} (80 settings)")
        e, t = FLOOR[mod]
        axa.add_patch(Rectangle((0, t * 100), e * 100, 100 - t * 100, facecolor=col,
                                alpha=0.07, edgecolor=col, linewidth=0.7, zorder=1))
    axa.annotate("voice floor", xy=(1.18, 97.8), fontsize=7.2, color=INK2, va="center")
    axa.annotate("face floor", xy=(3.18, 94.8), fontsize=7.2, color=INK2, va="center")
    for mod, col, xytext in (("voice", VOICE, (0.18, 86.5)), ("face", FACE, (4.30, 92.5))):
        s = SEL[mod]
        axa.scatter([s["EER"] * 100], [s["TAR_DEV"] * 100], s=124, c=col,
                    linewidths=1.8, edgecolors=SURFACE, zorder=5)
        axa.annotate("selected", xy=(s["EER"] * 100, s["TAR_DEV"] * 100), xytext=xytext,
                     fontsize=7.4, va="center",
                     arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.7,
                                     shrinkA=3, shrinkB=7))
    axa.set_xlabel("EER (%), development")
    axa.set_ylabel("TAR (%), development")
    axa.set_xlim(0, 7.2)
    axa.set_ylim(35, 103)
    axa.set_title("(a)  No face setting meets the voice floor", loc="left", pad=7)
    axa.legend(loc="lower right", handletextpad=0.4, borderpad=0.2)

    style(axb)
    for mod, col in (("face", FACE), ("voice", VOICE)):
        el = eligible(SWEEP[mod], mod)
        ine = [r for r in SWEEP[mod] if r not in el]
        axb.scatter([r["EER"] * 100 for r in ine], [r["Dsys_DEV"] for r in ine], s=20,
                    c=DEEMPH, alpha=0.85, linewidths=0.6, edgecolors=SURFACE, zorder=2)
        axb.scatter([r["EER"] * 100 for r in el], [r["Dsys_DEV"] for r in el], s=26,
                    c=col, alpha=0.85, linewidths=0.7, edgecolors=SURFACE, zorder=3,
                    label=f"{mod}, meets floor ({len(el)})")
        s = SEL[mod]
        axb.scatter([s["EER"] * 100], [s["Dsys_DEV"]], s=124, c=col, linewidths=1.8,
                    edgecolors=SURFACE, zorder=5)
    axb.scatter([], [], s=20, c=DEEMPH, linewidths=0.6, edgecolors=SURFACE,
                label="below floor")
    axb.annotate("large mark = selected", xy=(7.05, 0.012), fontsize=7.0, color=MUTED,
                 ha="right", va="bottom")
    axb.set_xlabel("EER (%), development")
    axb.set_ylabel("$D_{sys}$, development  (lower is better)")
    axb.set_xlim(0, 7.2)
    axb.set_ylim(0, 0.41)
    axb.set_title("(b)  Lowest $D_{sys}$ that clears each floor", loc="left", pad=7)
    axb.legend(loc="upper right", handletextpad=0.4, borderpad=0.2)
    fig.tight_layout(pad=1.1)
    save(fig, "FigureS2_OperatingPointSelection")


# ============================================== Figure 3: the design space
def figure_design_space(MS=(32, 64, 128, 256), QS=(4, 8, 16, 32), OS=(0, 1, 2, 3, 4)):
    vals = [r["Dsys_DEV"] for m in SWEEP for r in SWEEP[m]]
    norm = Normalize(vmin=min(vals), vmax=max(vals))
    fig, axes = plt.subplots(2, 5, figsize=(7.5, 3.5),
                             gridspec_kw={"wspace": 0.16, "hspace": 0.13})
    for row, mod in enumerate(("face", "voice")):
        for col, o in enumerate(OS):
            ax = axes[row, col]
            g = np.full((len(MS), len(QS)), np.nan)
            for r in SWEEP[mod]:
                if r["o"] == o:
                    g[MS.index(r["M"]), QS.index(r["q"])] = r["Dsys_DEV"]
            ax.imshow(g, cmap=BLUES, norm=norm, origin="upper", aspect="auto")
            for i in range(len(MS)):
                for j in range(len(QS)):
                    v = g[i, j]
                    ax.text(j, i, f"{v:.2f}".lstrip("0"), ha="center", va="center",
                            fontsize=5.9, color=SURFACE if norm(v) > 0.55 else INK2)
            s = SEL[mod]
            if s["o"] == o:
                ax.add_patch(plt.Rectangle((QS.index(s["q"]) - 0.5, MS.index(s["M"]) - 0.5),
                                           1, 1, fill=False, linewidth=1.9, zorder=5,
                                           edgecolor=FACE if mod == "face" else "#0d366b"))
            ax.set_xticks(range(len(QS)))
            ax.set_yticks(range(len(MS)))
            ax.set_xticklabels(QS if row == 1 else [])
            ax.set_yticklabels(MS if col == 0 else [])
            ax.tick_params(length=0, pad=2)
            for sp in ax.spines.values():
                sp.set_visible(False)
            if row == 0:
                ax.set_title(f"$o$ = {o}", pad=4, color=INK2)
            if col == 0:
                ax.set_ylabel(f"{mod}\n\n$M$", color=INK, labelpad=2)
            if row == 1:
                ax.set_xlabel("$q$")
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=BLUES), ax=axes,
                      fraction=0.022, pad=0.015)
    cb.set_label("$D_{sys}$, development  (lower is better)", color=INK2, fontsize=8)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2, labelsize=7.4, color=AXIS)
    fig.suptitle("Unlinkability across the 80-setting design space; the ringed cell "
                 "is the sealed setting", fontsize=8.8, x=0.008, ha="left", y=0.985)
    save(fig, "Figure3_DesignSpace")


# ================================================== Figure 4: the frontier
def pareto(rows):
    out, best = [], float("inf")
    for r in sorted(rows, key=lambda r: (r["EER"], r["Dsys_DEV"])):
        if r["Dsys_DEV"] < best:
            out.append(r)
            best = r["Dsys_DEV"]
    return out


def figure_frontier():
    fig, ax = plt.subplots(figsize=(4.9, 3.6))
    style(ax)
    for mod, col in (("face", FACE), ("voice", VOICE)):
        ok = eligible(SWEEP[mod], mod)
        no = [r for r in SWEEP[mod] if r not in ok]
        ax.scatter([r["EER"] * 100 for r in no], [r["Dsys_DEV"] for r in no], s=17,
                   c=DEEMPH, linewidths=0.6, edgecolors=SURFACE, zorder=2)
        ax.scatter([r["EER"] * 100 for r in ok], [r["Dsys_DEV"] for r in ok], s=24,
                   c=col, alpha=0.9, linewidths=0.7, edgecolors=SURFACE, zorder=3,
                   label=f"{mod}, meets floor ({len(ok)})")
        pf = pareto(SWEEP[mod])
        ax.step([r["EER"] * 100 for r in pf], [r["Dsys_DEV"] for r in pf], where="post",
                color=col, linewidth=1.3, alpha=0.9, zorder=4)
        s = SEL[mod]
        ax.scatter([s["EER"] * 100], [s["Dsys_DEV"]], s=120, c=col, linewidths=1.8,
                   edgecolors=SURFACE, zorder=6)
    ax.scatter([], [], s=17, c=DEEMPH, linewidths=0.6, edgecolors=SURFACE,
               label="below floor")
    ax.plot([], [], color=MUTED, linewidth=1.3, label="frontier")
    ax.annotate("large mark = sealed setting", xy=(7.05, 0.015), fontsize=7.0,
                color=MUTED, ha="right", va="bottom")
    ax.set_xlabel("EER (%), development")
    ax.set_ylabel("$D_{sys}$, development  (lower is better)")
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 0.40)
    ax.set_title("Recognition and unlinkability trade off across the design space",
                 loc="left", pad=7, fontsize=8.6)
    ax.legend(loc="upper right", handletextpad=0.5, borderpad=0.2)
    fig.tight_layout(pad=0.9)
    save(fig, "Figure4_Frontier")


# ============================================ Figure 5: generalisation
def figure_generalisation():
    rows = [("face", "development (42)", None), ("face", "held-out (58)", "face/evaluation"),
            ("voice", "development (42)", None), ("voice", "held-out (58)", "voice/evaluation"),
            ("voice", "external, VCTK (110)", "voice/external")]
    dev = {m: {"EER": SEL[m]["EER"] * 100, "TAR": SEL[m]["TAR_DEV"] * 100,
               "FMR": SEL[m]["FMR_DEV"] * 100, "Dsys": SEL[m]["Dsys_DEV"]}
           for m in ("face", "voice")}
    panels = [("EER", "EER (%)", [(1.0, "1%"), (3.0, "3%")], (0, 11)),
              ("TAR", "TAR (%)", [], (65, 100)),
              ("FMR", "FMR (%)", [(0.1, "0.1%")], (0, 0.68)),
              ("Dsys", "$D_{sys}$", [], (0, 0.30))]
    fig, axes = plt.subplots(1, 4, figsize=(7.6, 3.05))
    ypos = list(range(len(rows)))[::-1]
    for ax, (key, xlabel, refs, xlim) in zip(axes, panels):
        style(ax, "x")
        for ref, lab in refs:
            ax.axvline(ref, color=MUTED, linewidth=0.7, zorder=1)
            ax.annotate(lab, xy=(ref, len(rows) - 0.38), fontsize=6.8, color=MUTED,
                        ha="center", va="bottom")
        for y, (mod, _, part) in zip(ypos, rows):
            col = VOICE if mod == "voice" else FACE
            if part:
                est, lo, hi = CIS[part][key]
                ax.plot([lo, hi], [y, y], color=col, linewidth=1.8,
                        solid_capstyle="butt", zorder=3)
                for cap in (lo, hi):
                    ax.plot([cap, cap], [y - 0.16, y + 0.16], color=col, linewidth=1.8,
                            zorder=3)
                ax.scatter([est], [y], s=46, c=col, linewidths=1.5, edgecolors=SURFACE,
                           zorder=5)
            else:
                ax.scatter([dev[mod][key]], [y], s=34, facecolors=SURFACE,
                           linewidths=1.3, edgecolors=col, zorder=5)
        ax.set_yticks(ypos)
        ax.set_ylim(-0.6, len(rows) - 0.15)
        ax.set_xlim(*xlim)
        ax.set_xlabel(xlabel)
        ax.set_yticklabels([f"{m} · {lab}" for m, lab, _ in rows] if ax is axes[0] else [],
                           fontsize=7.4, color=INK2)
    handles = [Line2D([], [], color=FACE, linewidth=1.8, marker="o", markersize=5,
                      markeredgecolor=SURFACE, label="face"),
               Line2D([], [], color=VOICE, linewidth=1.8, marker="o", markersize=5,
                      markeredgecolor=SURFACE, label="voice"),
               Line2D([], [], color=MUTED, linewidth=0, marker="o", markersize=5,
                      markerfacecolor=SURFACE, markeredgecolor=MUTED,
                      label="development (no interval)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.005),
               handletextpad=0.4, columnspacing=1.8)
    fig.suptitle("Point estimates with 95% identity-cluster bootstrap intervals "
                 "(2,000 replicates)", fontsize=8.8, x=0.008, ha="left", y=0.99)
    fig.tight_layout(pad=1.0, rect=(0, 0.075, 1, 0.935))
    save(fig, "Figure5_Generalisation")


# ============================================ Figure P: protection cost
def figure_protection_cost():
    order = [("voice", "development"), ("voice", "evaluation"), ("voice", "external"),
             ("face", "development"), ("face", "evaluation")]
    name = {"development": "development (42)", "evaluation": "held-out (58)",
            "external": "external, VCTK (110)"}
    parts = {(p["modality"], p["partition"]): p for p in BASE["partitions"]}
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    style(ax, "x")
    ypos = list(range(len(order)))[::-1]
    for y, key in zip(ypos, order):
        p = parts[key]
        ci = CIS.get(f"{key[0]}/{key[1]}", {}).get("EER")
        yp, yb = y + 0.16, y - 0.16
        if ci:
            ax.plot([ci[1], ci[2]], [yp, yp], color=VOICE, linewidth=1.3, zorder=3)
            for e in ci[1:]:
                ax.plot([e, e], [yp - 0.1, yp + 0.1], color=VOICE, linewidth=1.3, zorder=3)
        ax.plot([p["protected_eer"]], [yp], "o", color=VOICE, markersize=5,
                markeredgecolor=SURFACE, zorder=5)
        bound = p["unprotected_upper_bound_95"]
        if p["baseline_resolved"]:
            ax.plot([p["unprotected_eer"]], [yb], "s", color=FACE, markersize=4.6,
                    markeredgecolor=SURFACE, zorder=5)
            ax.plot([p["unprotected_eer"], bound], [yb, yb], color=FACE, linewidth=1.0,
                    alpha=0.55, zorder=3)
            ax.plot([bound, bound], [yb - 0.1, yb + 0.1], color=FACE, linewidth=1.0,
                    alpha=0.55, zorder=3)
        else:
            ax.annotate("", xy=(0.02, yb), xytext=(bound, yb), zorder=4,
                        arrowprops=dict(arrowstyle="-|>", color=FACE, linewidth=1.0,
                                        shrinkA=0, shrinkB=0))
            ax.plot([bound], [yb], "|", color=FACE, markersize=7, markeredgewidth=1.2,
                    zorder=5)
        if not ci:
            verdict = "development: no interval"
        elif ci[1] > bound:
            verdict = f"+{p['cost_pp']:.2f} pp, firm"
        else:
            verdict = f"+{p['cost_pp']:.2f} pp, not resolvable"
        ax.text(16.4, y, verdict, fontsize=6.8, va="center", ha="right",
                color=INK if verdict.endswith("firm") else MUTED)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{m} · {name[p]}" for m, p in order], fontsize=7.4, color=INK2)
    ax.set_xlim(0, 16.5)
    ax.set_xticks([0, 2, 4, 6, 8, 10, 12])
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel("Equal error rate (%)")
    handles = [Line2D([], [], color=VOICE, marker="o", markersize=5, linewidth=1.3,
                      label="protected, 95% interval"),
               Line2D([], [], color=FACE, marker="s", markersize=4.6, linewidth=1.0,
                      alpha=0.7, label="unprotected, measured"),
               Line2D([], [], color=FACE, marker="|", linestyle="none", markersize=7,
                      markeredgewidth=1.2, label="unprotected, 95% upper bound only")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=3,
              handlelength=1.5, columnspacing=1.2, fontsize=6.8)
    ax.set_title("What protection costs against the unprotected system",
                 loc="left", pad=7)
    fig.tight_layout(pad=0.9)
    save(fig, "FigureP_ProtectionCost")


# =============================================== Figure 6: the ablation
def dot_interval(ax, values, xmax, pct=False):
    for i, arm in enumerate(ARMS):
        point, lo, hi = values[arm]
        y = len(ARMS) - 1 - i
        ax.plot([lo, hi], [y, y], color=HUE[arm], lw=2.0, solid_capstyle="round", zorder=3)
        ax.plot([point], [y], marker=SHAPE[arm], ms=7.5, color=HUE[arm], mec=SURFACE,
                mew=1.4, zorder=4)
        ax.annotate(f"{point:.2f}%" if pct else f"{point:.3f}", (hi, y), xytext=(5, 0),
                    textcoords="offset points", fontsize=7.2, color=INK2, va="center")
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([LABEL[a] for a in reversed(ARMS)])
    ax.set_ylim(-0.6, len(ARMS) - 0.4)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0, pad=3)
    ax.set_xlim(0, xmax)


def figure_ablation():
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                             gridspec_kw={"wspace": 0.78, "hspace": 0.70})
    for r, mod in enumerate(("voice", "face")):
        arms = ABL[mod]["arms"]
        eer = {a: (arms[a]["EER"] * 100, arms[a]["EER_CI"][0] * 100,
                   arms[a]["EER_CI"][1] * 100) for a in ARMS}
        dsys = {a: (arms[a]["Dsys"], *arms[a]["Dsys_CI"]) for a in ARMS}
        dot_interval(axes[r, 0], eer, xmax=11.5 if mod == "face" else 3.6, pct=True)
        dot_interval(axes[r, 1], dsys, xmax=0.33)
        axes[r, 0].set_title(f"{mod} — equal error rate (%)", loc="left", pad=6)
        axes[r, 1].set_title(f"{mod} — $D_{{sys}}$", loc="left", pad=6)
        for c in (0, 1):
            axes[r, c].set_xlabel("lower is better")
    v = {a: ABL["voice"]["arms"][a]["EER"] * 100 for a in ARMS}
    ax = axes[0, 0]
    for x0, x1, yy, col, txt in (
            (v["iom_only"], v["randproj_iom"], -0.50, MUTED,
             f"+{v['randproj_iom'] - v['iom_only']:.2f} pp  from the size reduction"),
            (v["randproj_iom"], v["polyiom"], -1.05, HUE["polyiom"],
             f"+{v['polyiom'] - v['randproj_iom']:.2f} pp  from the polynomial itself")):
        ax.annotate("", xy=(x0, yy), xytext=(x1, yy),
                    arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22", color=col,
                                    lw=0.9))
        ax.annotate(txt, (x0, yy - 0.13), ha="left", va="top", fontsize=6.4, color=col)
    ax.set_ylim(-1.80, len(ARMS) - 0.4)
    fig.suptitle("What each stage costs: error rate and linkability of the three arms",
                 fontsize=9, x=0.008, ha="left", y=0.995)
    save(fig, "Figure6_Ablation")


# ============================================ Figure 7: revocation per key
def figure_revocation():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.45), gridspec_kw={"wspace": 0.30})
    rng = np.random.default_rng(REV["master_seed"])
    n_keys = REV["n_fresh_keys"]
    for c, mod in enumerate(("voice", "face")):
        m = REV["modalities"][mod]
        ax = axes[c]
        counts = []
        for i, arm in enumerate(ARMS):
            vals = np.asarray(m["arms"][arm]["per_key_PRAR"], float) * 100
            check(vals.size == n_keys, f"{mod}/{arm}: {vals.size} keys, expected {n_keys}")
            y = len(ARMS) - 1 - i
            ax.scatter(vals, y + rng.uniform(-0.17, 0.17, vals.size), s=15,
                       marker=SHAPE[arm], facecolor=HUE[arm], edgecolor=SURFACE,
                       linewidth=0.5, alpha=0.85, zorder=3)
            counts.append(int((vals >= 50).sum()))
        ax.axvline(50, color=CRITICAL, lw=0.9, ls=(0, (3, 2)), zorder=2)
        ax.annotate("half or more exposed", (50, len(ARMS) - 1.5), fontsize=6.4,
                    color=CRITICAL, ha="center", va="center", rotation=90,
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
        ax.set_yticks(range(len(ARMS)))
        ax.set_yticklabels([LABEL[a] for a in reversed(ARMS)] if c == 0 else [])
        ax.set_ylim(-0.55, len(ARMS) - 0.45)
        ax.set_xlim(-6, 106)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.grid(True, axis="x")
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0, pad=3)
        ax.set_title(rf"{mod}  (M = {m['M']}, $\tau^*$ = {m['tau']})", loc="left", pad=6)
        ax.set_xlabel("acceptance rate after re-keying (%)")
        right = ax.twinx()
        right.set_ylim(ax.get_ylim())
        right.set_yticks(range(len(ARMS)))
        right.set_yticklabels([f"{n} of {n_keys}" for n in reversed(counts)])
        right.tick_params(length=0, pad=4, labelsize=6.8)
        for s in ("top", "right", "left", "bottom"):
            right.spines[s].set_visible(False)
        for tick, n in zip(right.get_yticklabels(), reversed(counts)):
            tick.set_color(CRITICAL if n else MUTED)
    fig.suptitle("Each dot is one fresh key. Most PolyIoM keys revoke completely; a "
                 "minority do not", fontsize=9, x=0.008, ha="left", y=1.02)
    save(fig, "Figure7_RevocationPerKey")


# ================================================ Figure 8: the inversion
def figure_inversion():
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                             gridspec_kw={"wspace": 0.78, "hspace": 0.70})
    for r, mod in enumerate(("voice", "face")):
        inv = INV[mod]
        M, tau = inv["M"], inv["tau"]
        chance = inv["arms"]["polyiom"]["chance_collisions"]
        cos_chance = inv["arms"]["polyiom"]["cos_chance"]
        ax = axes[r, 0]
        for i, arm in enumerate(ARMS):
            v = inv["arms"][arm]["mean_collisions"]
            y = len(ARMS) - 1 - i
            ax.plot([0, v], [y, y], color=HUE[arm], lw=2.0, solid_capstyle="butt", zorder=3)
            ax.plot([v], [y], marker=SHAPE[arm], ms=7.5, color=HUE[arm], mec=SURFACE,
                    mew=1.4, zorder=4)
            ax.annotate(f"{v:.1f}", (v, y), xytext=(5, 0), textcoords="offset points",
                        fontsize=7.2, color=INK2, va="center")
        ax.axvline(tau, color=CRITICAL, lw=0.9, ls=(0, (3, 2)), zorder=2)
        ax.annotate(rf"$\tau^*$ = {tau}", (tau + 2, -0.50), fontsize=6.6, color=CRITICAL,
                    ha="left", va="center",
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
        ax.axvline(chance, color=MUTED, lw=0.8, zorder=2)
        ax.set_yticks(range(len(ARMS)))
        ax.set_yticklabels([LABEL[a] for a in reversed(ARMS)])
        ax.set_ylim(-0.75, len(ARMS) - 0.35)
        ax.set_xlim(0, M * 1.14)
        ax.grid(True, axis="x")
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0, pad=3)
        ax.set_title(f"{mod} — matching positions reached (of {M})", loc="left", pad=6)
        ax.set_xlabel(f"further right = more complete attack (chance {chance:.0f})")

        # The cosine intervals are stored with the revocation run, which
        # re-ran the same attack; the point estimates must agree.
        cos = {}
        for arm in ARMS:
            ra = REV["modalities"][mod]["arms"][arm]
            check(close(ra["cos_to_true"], inv["arms"][arm]["cos_to_true"], 1e-9),
                  f"{mod}/{arm}: inversion and revocation cosines differ")
            cos[arm] = (ra["cos_to_true"], *ra["cos_CI"])
        ax = axes[r, 1]
        dot_interval(ax, cos, xmax=1.06)
        ax.axvline(cos_chance, color=MUTED, lw=0.8, zorder=2)
        ax.annotate(f"chance {cos_chance:.3f}", (cos_chance, -0.50), fontsize=6.6,
                    color=MUTED, ha="left", va="center",
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
        ax.set_ylim(-0.75, len(ARMS) - 0.35)
        ax.set_title(f"{mod} — cosine to the true embedding", loc="left", pad=6)
        ax.set_xlabel("higher = more of the biometric recovered")
    fig.suptitle("The attack clears the threshold in every arm; only the recovered "
                 "embedding separates them", fontsize=9, x=0.008, ha="left", y=0.995)
    save(fig, "Figure8_Inversion")


def main():
    figure_selection()
    figure_design_space()
    figure_frontier()
    figure_generalisation()
    figure_protection_cost()
    figure_ablation()
    figure_revocation()
    figure_inversion()
    print(f"\nEight figures in {OUT}")


if __name__ == "__main__":
    main()

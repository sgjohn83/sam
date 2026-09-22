"""Results figures for AttackAware PolyIoM v1.1.4.

Reads runs/scores/score_histograms.json and writes four figures, one per
ISO/IEC 24745 criterion the paper has to address. Read-only: touches no
seal, fits no threshold, computes no new score.

  A  det_preservation     the protected system's DET curves, and what
                          protection cost against the unprotected baseline
  B  score_separability   genuine and impostor, with tau* marked
  C  unlinkability        mated and non-mated, with D_link(s) overlaid
  D  revocability         genuine, impostor and pseudo-impostor together

Colour carries one meaning across all four figures
--------------------------------------------------
  blue    genuine comparisons, or the protected system
  grey    impostor comparisons, or non-mated pairs
  green   pseudo-impostor comparisons (a revoked key), or face
  orange  the unprotected baseline, and only ever that

Why figure A does not draw the baseline as a DET curve on voice
---------------------------------------------------------------
The unprotected voice baseline produces fewer than one genuine error: the
resolution of the evaluation split is 0.17% and of the external split
0.09%, and the measured EERs are 0.085% and 0.003%. A DET curve through
that region would sit off the bottom-left of any readable axis and would
imply a precision the trial count cannot support. The ratio it suggests
(22.7x held-out, 848x external) is an artifact of dividing by an
unresolved number.

The right panel therefore reports EER directly, with the baseline drawn as
a one-sided 95% upper bound wherever it is unresolved and as a point only
where it is genuinely measured. A reader can then see which contrasts the
data settle and which it does not.

Why figure C marks part of its own curve unreliable
---------------------------------------------------
The local unlinkability score D_link(s) is a ratio of two densities, and
the mated density is estimated from only one comparison per identity. In
score bins where the non-mated histogram is nearly empty the ratio is
driven by single observations and the curve runs to 1 for that reason
alone. Those bins are shaded rather than silently plotted.

Why the mated distribution appears twice
----------------------------------------
Figure C uses it as the unlinkability mated set and figure D uses it as
the revocability pseudo-impostor set. It is one measurement. Both captions
say so, and the paper must not count it as two independent results.
"""

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator

GEN = "#1c5cab"         # genuine, and the protected system
IMP = "#8a919c"         # impostor, and non-mated
PSE = "#158a5f"         # pseudo-impostor, and face
BASE = "#c94e1f"        # the unprotected baseline, and nothing else
INK = "#1a1a1a"
MUTE = "#6b7280"
GRID = "#d9dde3"
WARN = "#9aa1ab"
DERIV = INK          # a derived measure, never a data series

COL_W = 7.16            # double-column width, inches
DPI = 400

# Bootstrap intervals carried from the sealed held-out and external
# analyses. Not recomputed here: the histograms record distributions, not
# the identity-cluster resampling those intervals came from. Development
# is the selection split and was never given an interval.
CARRIED_CI = {
    ("voice", "evaluation"): (1.928, 1.092, 2.919),
    ("voice", "external"): (2.798, 1.992, 3.807),
    ("face", "evaluation"): (4.799, 1.945, 10.345),
}

ROWS = [("voice", "development"), ("voice", "evaluation"),
        ("voice", "external"), ("face", "development"),
        ("face", "evaluation")]
PANELS = [("voice", "evaluation"), ("face", "evaluation")]
LABEL = {("voice", "development"): "Voice, development (42)",
         ("voice", "evaluation"): "Voice, held-out (58)",
         ("voice", "external"): "Voice, external VCTK (110)",
         ("face", "development"): "Face, development (42)",
         ("face", "evaluation"): "Face, held-out (58)"}
TITLE = {("voice", "evaluation"): "Voice, 58 held-out speakers",
         ("face", "evaluation"): "Face, 58 held-out subjects",
         ("voice", "external"): "Voice, 110 external speakers",
         ("voice", "development"): "Voice, 42 development speakers",
         ("face", "development"): "Face, 42 development subjects"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.edgecolor": MUTE, "axes.linewidth": 0.6,
    "xtick.color": MUTE, "ytick.color": MUTE, "text.color": INK,
    "axes.labelcolor": INK, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _ndtri(p):
    from scipy.special import ndtri as f
    return f(np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9))


def rates(genuine, impostor):
    """FMR and FNMR at every threshold, from two histograms.

    A comparison is accepted at a score of at least the threshold, so FMR
    is the upper tail of the impostor histogram and FNMR the lower tail of
    the genuine one.
    """
    g = np.asarray(genuine, float)
    i = np.asarray(impostor, float)
    fmr = np.r_[np.cumsum(i[::-1])[::-1], 0.0] / max(i.sum(), 1.0)
    fnmr = np.r_[0.0, np.cumsum(g)] / max(g.sum(), 1.0)
    return fmr, fnmr


def eer_from(genuine, impostor):
    fmr, fnmr = rates(genuine, impostor)
    d = fmr - fnmr
    exact = np.flatnonzero(d == 0.0)
    if len(exact):
        return float(fmr[exact[0]]), int(exact[0])
    cross = np.flatnonzero((d[:-1] > 0) & (d[1:] < 0))
    if len(cross):
        j = int(cross[0])
        w = d[j] / (d[j] - d[j + 1])
        return float(fmr[j] + w * (fmr[j + 1] - fmr[j])), j
    j = int(np.argmin(np.maximum(fmr, fnmr)))
    return float((fmr[j] + fnmr[j]) / 2.0), j


def baseline_bound(eer, n_genuine):
    """One-sided 95% upper bound on an unresolved baseline error rate.

    Returns (bound, resolved). An EER below one genuine error means the
    crossing sits where the genuine side has at most one mistake, so the
    point estimate carries no information and only a bound is honest.
    """
    from scipy.stats import beta
    floor = 1.0 / n_genuine
    k = int(np.floor(eer * n_genuine + 1e-9))
    bound = float(beta.ppf(0.95, k + 1, n_genuine - k))
    return bound, bool(eer >= floor)


def support(arrays, M, pad=0.10):
    """Score range actually occupied, so panels do not waste width.

    The distributions occupy a third of 0..M or less. Plotting the whole
    range leaves most of every panel blank and shrinks the part a reader
    needs to see. The axis label states that the axis is truncated.
    """
    lo, hi = M, 0
    for a in arrays:
        nz = np.flatnonzero(np.asarray(a, float) > 0)
        if len(nz):
            lo, hi = min(lo, int(nz[0])), max(hi, int(nz[-1]))
    if hi <= lo:
        return 0, M
    span = hi - lo
    return max(0, int(lo - pad * span)), min(M, int(hi + pad * span) + 1)


def _det_axes(ax, ticks=(0.1, 1, 5, 20, 50)):
    p = [t / 100 for t in ticks]
    pos = _ndtri(p)
    ax.set_xlim(pos[0], pos[-1])
    ax.set_ylim(pos[0], pos[-1])
    ax.xaxis.set_major_locator(FixedLocator(pos))
    ax.yaxis.set_major_locator(FixedLocator(pos))
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    ax.grid(True, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def figure_a(data, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(COL_W, 3.55),
                             gridspec_kw={"width_ratios": [1, 1.28]})

    # Left: the protected system's DET curves, which are measurable.
    ax = axes[0]
    curves = [(("voice", "evaluation"), GEN, "-", "Voice, held-out"),
              (("voice", "external"), GEN, (0, (4, 2)), "Voice, external"),
              (("face", "evaluation"), PSE, "-", "Face, held-out")]
    for (mod, part), colour, style, label in curves:
        parts = data["modalities"][mod]["partitions"]
        if part not in parts:
            continue
        h = parts[part]
        fmr, fnmr = rates(h["genuine"], h["impostor"])
        keep = (fmr > 0) & (fnmr > 0)
        eer, _ = eer_from(h["genuine"], h["impostor"])
        ax.plot(_ndtri(fmr[keep]), _ndtri(fnmr[keep]), color=colour,
                linewidth=1.5, linestyle=style, zorder=4,
                label=f"{label}  {eer * 100:.2f}%")
        p = _ndtri(eer)
        ax.plot([p], [p], "o", color=colour, markersize=3.6,
                markeredgecolor="white", markeredgewidth=0.6, zorder=5)
    # Stops short of the corner so the legend sits on clean ground.
    lim = _ndtri((0.001, 0.22))
    ax.plot(lim, lim, color=MUTE, linewidth=0.5, linestyle=(0, (4, 3)))
    _det_axes(ax)
    ax.set_xlabel("False match rate (%)")
    ax.set_ylabel("False non-match rate (%)")
    ax.set_title("Protected system, equal-error point marked", color=INK,
                 loc="left")
    ax.legend(loc="upper right", frameon=False, handlelength=1.8,
              borderpad=0.2, labelspacing=0.3)

    # Right: what protection cost, and what the data can resolve.
    ax = axes[1]
    ypos = np.arange(len(ROWS))[::-1]
    for y, (mod, part) in zip(ypos, ROWS):
        parts = data["modalities"][mod]["partitions"]
        if part not in parts:
            continue
        h = parts[part]
        prot, _ = eer_from(h["genuine"], h["impostor"])
        prot *= 100
        raw, _ = eer_from(h["unprotected"]["genuine"],
                          h["unprotected"]["impostor"])
        raw *= 100
        bound, resolved = baseline_bound(raw / 100, h["n_genuine"])
        bound *= 100

        # Two rows within a row: on face the protected and unprotected
        # points nearly coincide, and one would hide the other.
        yp, yb = y + 0.16, y - 0.16
        ci = CARRIED_CI.get((mod, part))
        if ci:
            ax.plot([ci[1], ci[2]], [yp, yp], color=GEN, linewidth=1.1,
                    solid_capstyle="butt", zorder=3)
            for e in (ci[1], ci[2]):
                ax.plot([e, e], [yp - 0.12, yp + 0.12], color=GEN,
                        linewidth=1.1, zorder=3)
        ax.plot([prot], [yp], "o", color=GEN, markersize=4.6,
                markeredgecolor="white", markeredgewidth=0.7, zorder=5)

        if resolved:
            ax.plot([raw], [yb], "s", color=BASE, markersize=4.2,
                    markeredgecolor="white", markeredgewidth=0.7, zorder=5)
            ax.plot([raw, bound], [yb, yb], color=BASE, linewidth=1.0,
                    alpha=0.55, zorder=3)
            ax.plot([bound, bound], [yb - 0.12, yb + 0.12], color=BASE,
                    linewidth=1.0, alpha=0.55, zorder=3)
            verdict = "not resolvable" if ci else "no interval"
        else:
            ax.annotate("", xy=(0.02, yb), xytext=(bound, yb),
                        arrowprops=dict(arrowstyle="-|>", color=BASE,
                                        linewidth=1.0, shrinkA=0, shrinkB=0),
                        zorder=4)
            ax.plot([bound], [yb], "|", color=BASE, markersize=7,
                    markeredgewidth=1.2, zorder=5)
            verdict = ("no interval" if not ci else
                       "firm" if ci[1] > bound else "not resolvable")
        ax.text(15.8, y, verdict, fontsize=6.4, va="center", ha="right",
                color=INK if verdict == "firm" else MUTE,
                style="normal" if verdict == "firm" else "italic")

    ax.set_yticks(ypos)
    ax.set_yticklabels([LABEL[r] for r in ROWS], fontsize=7)
    ax.set_xlim(0, 16)
    ax.set_ylim(-0.6, len(ROWS) - 0.4)
    ax.set_xlabel("Equal error rate (%)")
    ax.grid(True, axis="x", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Protection cost, and what the data settle", color=INK,
                 loc="left")
    handles = [
        plt.Line2D([], [], color=GEN, marker="o", linestyle="-",
                   markersize=4.6, linewidth=1.1,
                   label="Protected, 95% interval"),
        plt.Line2D([], [], color=BASE, marker="s", linestyle="-",
                   markersize=4.2, linewidth=1.0, alpha=0.7,
                   label="Unprotected, measured"),
        plt.Line2D([], [], color=BASE, marker="|", linestyle="none",
                   markersize=7, markeredgewidth=1.2,
                   label="Unprotected, 95% upper bound only"),
    ]
    # Below the axis: every in-panel corner is occupied by a row.
    ax.legend(handles=handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.20), ncol=3, frameon=False,
              handlelength=1.5, borderpad=0.2, columnspacing=1.1,
              fontsize=6.0)
    fig.suptitle("Performance preservation against the unprotected "
                 "baseline", fontsize=9.5, x=0.005, ha="left", color=INK,
                 y=0.995)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    _save(fig, outdir, "figA_det_preservation")


def _dist_panel(ax, x, series, lo, hi, headroom=1.30):
    top = 0.0
    for label, raw, colour, style in series:
        v = np.asarray(raw, float)
        v = v / v.sum()
        top = max(top, v[lo:hi].max() if hi > lo else v.max())
        ax.fill_between(x, v, color=colour, alpha=0.42, linewidth=0, zorder=3)
        ax.plot(x, v, color=colour, linewidth=1.15, linestyle=style,
                zorder=4, label=label)
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, top * headroom)
    return top


def figure_b(data, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(COL_W, 2.9))
    for ax, (modality, partition) in zip(axes, PANELS):
        entry = data["modalities"][modality]
        h = entry["partitions"][partition]
        M, tau = entry["M"], entry["tau"]
        lo, hi = support([h["genuine"], h["impostor"]], M)
        x = np.arange(M + 1)
        top = _dist_panel(ax, x, [("Impostor", h["impostor"], IMP, "-"),
                                  ("Genuine", h["genuine"], GEN, "-")],
                          lo, hi)
        eer, _ = eer_from(h["genuine"], h["impostor"])
        ax.plot([tau, tau], [0, top * 0.95], color=INK, linewidth=0.9,
                zorder=5)
        ax.annotate(rf"$\tau^{{*}}={tau}$", xy=(tau, top * 0.055),
                    xytext=(4, 0), textcoords="offset points", fontsize=7,
                    color=INK, ha="left", va="bottom", zorder=6)
        ax.set_title(f"{TITLE[(modality, partition)]}   EER {eer * 100:.2f}%",
                     color=INK, loc="left")
        ax.set_xlabel(f"Collision score (axis truncated; $M$={M})")
        ax.legend(loc="upper right", frameon=False, handlelength=1.4,
                  borderpad=0.2)
    axes[0].set_ylabel("Share of comparisons")
    fig.suptitle("Where the sealed threshold sits in the score "
                 "distributions", fontsize=9.5, x=0.005, ha="left",
                 color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0.02, 1, 0.92))
    _save(fig, outdir, "figB_score_separability")


def figure_c(data, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(COL_W, 2.95))
    for ax, (modality, partition) in zip(axes, PANELS):
        entry = data["modalities"][modality]
        h = entry["partitions"][partition]
        M = entry["M"]
        lo, hi = support([h["mated"], h["nonmated"]], M)
        x = np.arange(M + 1)
        top = _dist_panel(ax, x, [("Non-mated", h["nonmated"], IMP, "-"),
                                  ("Mated", h["mated"], PSE, "-")], lo, hi,
                          headroom=1.52)
        ax.set_xlabel(f"Collision score (axis truncated; $M$={M})")

        # Bins where the non-mated side is nearly empty drive D_link(s) to
        # 1 on single observations. Shade them rather than imply a measure.
        non = np.asarray(h["nonmated"], float)
        thin = non < 5
        edges = np.flatnonzero(thin[:-1] != thin[1:])
        start = 0 if thin[0] else None
        for e in edges:
            if thin[e]:
                if start is not None:
                    ax.axvspan(start, e + 1, color=WARN, alpha=0.16,
                               linewidth=0, zorder=1)
                    start = None
            else:
                start = e + 1
        if start is not None:
            ax.axvspan(start, M, color=WARN, alpha=0.16, linewidth=0,
                       zorder=1)

        twin = ax.twinx()
        twin.plot(x, np.asarray(h["dlink_curve"], float), color=DERIV,
                  linewidth=1.25, zorder=5, label=r"$D_{\mathrm{link}}(s)$")
        twin.set_ylim(0, 1.32)
        twin.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        twin.spines["top"].set_visible(False)
        twin.spines["right"].set_visible(True)
        twin.spines["right"].set_color(MUTE)
        twin.set_ylabel(r"$D_{\mathrm{link}}(s)$", color=DERIV)
        twin.tick_params(axis="y", colors=DERIV)

        ax.set_title(f"{TITLE[(modality, partition)]}   "
                     rf"$D^{{\mathrm{{sys}}}}_{{\leftrightarrow}}=$"
                     f"{h['dlink_global']:.3f}", color=INK, loc="left")
        hl, ll = ax.get_legend_handles_labels()
        h2, l2 = twin.get_legend_handles_labels()
        shade = plt.Rectangle((0, 0), 1, 1, color=WARN, alpha=0.16,
                              label="Fewer than 5 non-mated pairs")
        ax.legend(hl + h2 + [shade], ll + l2 + [shade.get_label()],
                  loc="upper right", frameon=False, handlelength=1.3,
                  borderpad=0.2, labelspacing=0.3, fontsize=6.4)
    axes[0].set_ylabel("Share of comparisons")
    fig.suptitle("Unlinkability: can two protected templates be tied to "
                 "one person?", fontsize=9.5, x=0.005, ha="left", color=INK,
                 y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    _save(fig, outdir, "figC_unlinkability")


def figure_d(data, outdir):
    fig, axes = plt.subplots(1, 2, figsize=(COL_W, 3.05))
    for ax, (modality, partition) in zip(axes, PANELS):
        entry = data["modalities"][modality]
        h = entry["partitions"][partition]
        M, tau = entry["M"], entry["tau"]
        lo, hi = support([h["genuine"], h["impostor"], h["mated"]], M)
        x = np.arange(M + 1)
        top = _dist_panel(ax, x, [
            ("Impostor (other person)", h["impostor"], IMP, "-"),
            ("Pseudo-impostor (revoked key)", h["mated"], PSE, (0, (3, 1.6))),
            ("Genuine (current key)", h["genuine"], GEN, "-")], lo, hi,
            headroom=1.58)

        mated = np.asarray(h["mated"], float)
        prar = float(mated[tau:].sum() / mated.sum())
        ax.plot([tau, tau], [0, top * 0.95], color=INK, linewidth=0.9,
                zorder=5)
        ax.annotate(rf"$\tau^{{*}}={tau}$", xy=(tau, top * 0.055),
                    xytext=(4, 0), textcoords="offset points", fontsize=7,
                    color=INK, ha="left", va="bottom", zorder=6)
        ax.annotate(f"{prar * 100:.1f}% of revoked templates still\n"
                    f"accepted at $\\tau^{{*}}$ (PRAR, this key pair)",
                    xy=(0.98, 0.74), xycoords="axes fraction", fontsize=6.2,
                    color=INK, ha="right", va="top", zorder=6)
        ax.set_title(TITLE[(modality, partition)], color=INK, loc="left")
        ax.set_xlabel(f"Collision score (axis truncated; $M$={M})")
        ax.legend(loc="upper right", frameon=False, handlelength=1.5,
                  borderpad=0.2, labelspacing=0.3, fontsize=6.4)
    axes[0].set_ylabel("Share of comparisons")
    fig.suptitle("Revocability: does a template survive its own key being "
                 "revoked?", fontsize=9.5, x=0.005, ha="left", color=INK,
                 y=0.995)
    fig.tight_layout(rect=(0, 0.02, 1, 0.92))
    _save(fig, outdir, "figD_revocability")


def _save(fig, outdir, stem):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(outdir / f"{stem}.{ext}", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {stem}.pdf and {stem}.png")


def make_figures(score_json=None, outdir=None):
    score_json = Path(score_json) if score_json else \
        DIR["runs"] / "scores" / "score_histograms.json"
    outdir = Path(outdir) if outdir else \
        score_json.parent.parent.parent / "figures" / "results"
    data = json.loads(score_json.read_text())
    if data.get("SYNTHETIC"):
        print("*** SYNTHETIC input: layout test only, not for the paper")
    print(f"Read {score_json}")
    for fn in (figure_a, figure_b, figure_c, figure_d):
        fn(data, outdir)
    print(f"\nFour figures in {outdir}")
    return outdir


print("Figure runtime ready. Run make_figures().")

"""Figures 6-8 for the paper. Palette is the dataviz reference categorical
set, validated with scripts/validate_palette.js --mode light:

  [PASS] lightness band, chroma floor, CVD separation (worst adjacent
         deutan dE 9.2), normal-vision floor (dE 27.6)
  [WARN] aqua #1baf7a sits below 3:1 on the light surface, so relief is
         required - discharged by direct labels on every arm plus the
         tables in the document.

Marker shape doubles the hue so the figures survive greyscale printing.
"""
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent

SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
CRITICAL = "#d03b3b"

ARMS = ["polyiom", "iom_only", "randproj_iom"]
LABEL = {"polyiom": "PolyIoM (ours)", "iom_only": "IoM only",
         "randproj_iom": "Random proj. + IoM"}
HUE = {"polyiom": "#2a78d6", "iom_only": "#eb6834", "randproj_iom": "#1baf7a"}
SHAPE = {"polyiom": "o", "iom_only": "s", "randproj_iom": "^"}

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.4, "ytick.labelsize": 7.8,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6,
    "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ----------------------------------------------------------------- data
ABL = {
 "voice": {"polyiom": {"EER": (1.9282, 1.1097, 2.9510), "Dsys": (0.088431, 0.069403, 0.220611)},
           "iom_only": {"EER": (0.2730, 0.0343, 0.5679), "Dsys": (0.072822, 0.058086, 0.191561)},
           "randproj_iom": {"EER": (0.7002, 0.3054, 1.3793), "Dsys": (0.113162, 0.083211, 0.220905)}},
 "face": {"polyiom": {"EER": (4.7995, 1.7368, 9.7375), "Dsys": (0.150803, 0.124976, 0.280611)},
          "iom_only": {"EER": (4.2471, 1.3369, 8.5927), "Dsys": (0.116965, 0.101223, 0.257562)},
          "randproj_iom": {"EER": (3.8610, 1.6890, 8.3750), "Dsys": (0.096140, 0.092291, 0.232726)}},
}
INV = {
 "voice": {"M": 128, "tau": 37, "chance_hits": 4.0, "chance_cos": 0.120,
           "hits": {"polyiom": 128.0, "iom_only": 128.0, "randproj_iom": 125.72},
           "cos": {"polyiom": (0.221948, 0.196092, 0.247856),
                   "iom_only": (0.912850, 0.909844, 0.915842),
                   "randproj_iom": (0.489618, 0.481551, 0.498266)}},
 "face": {"M": 256, "tau": 68, "chance_hits": 8.0, "chance_cos": 0.029,
          "hits": {"polyiom": 256.0, "iom_only": 256.0, "randproj_iom": 238.83},
          "cos": {"polyiom": (0.418434, 0.407547, 0.429552),
                  "iom_only": (0.875893, 0.873483, 0.878205),
                  "randproj_iom": (0.492278, 0.485223, 0.499347)}},
}
PK = {
 "voice": {
  "polyiom": [0,1.7241379,0,0,0,1.7241379,0,0,3.4482758,84.482759,0,1.7241379,0,
              27.586207,3.4482758,0,0,0,0,5.1724140,0,0,0,0,0,3.4482758,0,5.1724140,
              89.655173,6.8965517,43.103448,3.4482758,0,0,0,0,0,0,6.8965517,12.068965],
  "iom_only": [100.0] * 40,
  "randproj_iom": [6.8965517,5.1724140,3.4482758,8.6206898,6.8965517,5.1724140,
                   8.6206898,0,6.8965517,5.1724140,5.1724140,6.8965517,6.8965517,
                   1.7241379,5.1724140,6.8965517,1.7241379,1.7241379,6.8965517,
                   6.8965517,1.7241379,13.793103,1.7241379,6.8965517,8.6206898,
                   1.7241379,5.1724140,0,8.6206898,8.6206898,10.344828,6.8965517,
                   6.8965517,1.7241379,10.344828,1.7241379,10.344828,6.8965517,
                   3.4482758,6.8965517]},
 "face": {
  "polyiom": [1.7241379,0,100.0,0,8.6206898,0,5.1724140,0,0,25.862068,0,0,93.103451,
              100.0,0,0,0,0,0,0,100.0,0,100.0,0,0,3.4482758,0,0,0,100.0,0,0,
              86.206895,0,0,100.0,0,0,100.0,100.0],
  "iom_only": [100.0] * 40,
  "randproj_iom": [0,3.4482758,1.7241379,5.1724140,0,1.7241379,5.1724140,1.7241379,
                   8.6206898,1.7241379,0,0,3.4482758,5.1724140,3.4482758,3.4482758,
                   1.7241379,5.1724140,5.1724140,1.7241379,1.7241379,5.1724140,
                   6.8965517,6.8965517,8.6206898,5.1724140,1.7241379,3.4482758,0,
                   1.7241379,0,1.7241379,3.4482758,0,1.7241379,1.7241379,1.7241379,
                   0,3.4482758,1.7241379]},
}
TAU = {"voice": 37, "face": 68}


def dot_interval(ax, values, xmax=None, pct=False):
    for i, arm in enumerate(ARMS):
        point, lo, hi = values[arm]
        y = len(ARMS) - 1 - i
        ax.plot([lo, hi], [y, y], color=HUE[arm], lw=2.0,
                solid_capstyle="round", zorder=3)
        ax.plot([point], [y], marker=SHAPE[arm], ms=7.5, color=HUE[arm],
                mec=SURFACE, mew=1.4, zorder=4)
        txt = f"{point:.3f}" if not pct else f"{point:.2f}%"
        ax.annotate(txt, (hi, y), xytext=(5, 0), textcoords="offset points",
                    fontsize=7.2, color=INK2, va="center")
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([LABEL[a] for a in reversed(ARMS)])
    ax.set_ylim(-0.6, len(ARMS) - 0.4)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0, pad=3)
    if xmax:
        ax.set_xlim(0, xmax)


# =========================================== Figure 6 - ablation
fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                         gridspec_kw={"wspace": 0.78, "hspace": 0.70})
for r, mod in enumerate(("voice", "face")):
    dot_interval(axes[r, 0], {a: ABL[mod][a]["EER"] for a in ARMS},
                 xmax=11.5 if mod == "face" else 3.6, pct=True)
    dot_interval(axes[r, 1], {a: ABL[mod][a]["Dsys"] for a in ARMS},
                 xmax=0.33)
    axes[r, 0].set_title(f"{mod} — equal error rate (%)", loc="left",
                         color=INK, pad=6)
    axes[r, 1].set_title(f"{mod} — $D_{{sys}}$", loc="left", color=INK, pad=6)
    for c in (0, 1):
        axes[r, c].set_xlabel("lower is better")

# the decomposition, annotated where it is claimed
ax = axes[0, 0]
for (x0, x1, yy, col, txt) in (
        (0.2730, 0.7002, -0.50, MUTED,
         "+0.43 pp  from the size reduction"),
        (0.7002, 1.9282, -1.05, HUE["polyiom"],
         "+1.23 pp  from the polynomial itself")):
    ax.annotate("", xy=(x0, yy), xytext=(x1, yy),
                arrowprops=dict(arrowstyle="|-|,widthA=0.22,widthB=0.22",
                                color=col, lw=0.9))
    ax.annotate(txt, (x0, yy - 0.13), ha="left", va="top", fontsize=6.4,
                color=col)
ax.set_ylim(-1.80, len(ARMS) - 0.4)

fig.suptitle("Removing the keyed polynomial improves recognition and does "
             "not worsen unlinkability", fontsize=9, color=INK, x=0.008,
             ha="left", y=0.995)
fig.savefig(HERE / "fig6_ablation.pdf", bbox_inches="tight")
fig.savefig(HERE / "fig6_ablation.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# =========================================== Figure 7 - per-key revocation
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.45),
                         gridspec_kw={"wspace": 0.30})
rng = np.random.default_rng(2026)
for c, mod in enumerate(("voice", "face")):
    ax = axes[c]
    counts = []
    for i, arm in enumerate(ARMS):
        vals = np.asarray(PK[mod][arm], dtype=float)
        y = len(ARMS) - 1 - i
        jitter = rng.uniform(-0.17, 0.17, size=vals.size)
        ax.scatter(vals, y + jitter, s=15, marker=SHAPE[arm],
                   facecolor=HUE[arm], edgecolor=SURFACE, linewidth=0.5,
                   alpha=0.85, zorder=3)
        counts.append(int((vals >= 50).sum()))
    ax.axvline(50, color=CRITICAL, lw=0.9, ls=(0, (3, 2)), zorder=2)
    # Beside the line, inside the empty band between the first two rows.
    # Below it collides with the "50" tick; above it collides with the title.
    ax.annotate("fails outright", (50, len(ARMS) - 1.5), fontsize=6.6,
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
    ax.set_title(f"{mod}  (M = {INV[mod]['M']}, "
                 rf"$\tau^*$ = {TAU[mod]})", loc="left", color=INK, pad=6)
    ax.set_xlabel("acceptance rate after re-keying (%)")

    right = ax.twinx()
    right.set_ylim(ax.get_ylim())
    right.set_yticks(range(len(ARMS)))
    right.set_yticklabels([f"{n} of 40" for n in reversed(counts)])
    right.tick_params(length=0, pad=4, labelsize=6.8)
    for s_ in ("top", "right", "left", "bottom"):
        right.spines[s_].set_visible(False)
    for tick, n in zip(right.get_yticklabels(), reversed(counts)):
        tick.set_color(CRITICAL if n else MUTED)

fig.suptitle("Each dot is one fresh key. PolyIoM usually revokes perfectly, "
             "then fails completely", fontsize=9, color=INK, x=0.008,
             ha="left", y=1.02)
fig.savefig(HERE / "fig7_revocation_per_key.pdf", bbox_inches="tight")
fig.savefig(HERE / "fig7_revocation_per_key.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# =========================================== Figure 8 - inversion
fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                         gridspec_kw={"wspace": 0.78, "hspace": 0.70})
for r, mod in enumerate(("voice", "face")):
    M, tau = INV[mod]["M"], INV[mod]["tau"]
    ax = axes[r, 0]
    for i, arm in enumerate(ARMS):
        v = INV[mod]["hits"][arm]
        y = len(ARMS) - 1 - i
        ax.plot([0, v], [y, y], color=HUE[arm], lw=2.0,
                solid_capstyle="butt", zorder=3)
        ax.plot([v], [y], marker=SHAPE[arm], ms=7.5, color=HUE[arm],
                mec=SURFACE, mew=1.4, zorder=4)
        ax.annotate(f"{v:.1f}", (v, y), xytext=(5, 0),
                    textcoords="offset points", fontsize=7.2, color=INK2,
                    va="center")
    ax.axvline(tau, color=CRITICAL, lw=0.9, ls=(0, (3, 2)), zorder=2)
    ax.annotate(rf"$\tau^*$ = {tau}", (tau, -0.50), fontsize=6.6,
                color=CRITICAL, ha="left", va="center",
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
    ax.axvline(INV[mod]["chance_hits"], color=MUTED, lw=0.8, zorder=2)
    ax.annotate(f"chance {INV[mod]['chance_hits']:.0f}",
                (INV[mod]["chance_hits"], -0.50), fontsize=6.6, color=MUTED,
                ha="left", va="center",
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([LABEL[a] for a in reversed(ARMS)])
    ax.set_ylim(-0.75, len(ARMS) - 0.35)
    ax.set_xlim(0, M * 1.14)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0, pad=3)
    ax.set_title(f"{mod} — matching positions reached (of {M})", loc="left",
                 color=INK, pad=6)
    ax.set_xlabel("further right = attack succeeded more completely")

    ax = axes[r, 1]
    dot_interval(ax, INV[mod]["cos"], xmax=1.06)
    ax.axvline(INV[mod]["chance_cos"], color=MUTED, lw=0.8, zorder=2)
    ax.annotate(f"chance {INV[mod]['chance_cos']:.3f}",
                (INV[mod]["chance_cos"], -0.50), fontsize=6.6, color=MUTED,
                ha="left", va="center",
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2))
    ax.set_ylim(-0.75, len(ARMS) - 0.35)
    ax.set_title(f"{mod} — cosine to the true embedding", loc="left",
                 color=INK, pad=6)
    ax.set_xlabel("higher = more of the biometric recovered")

fig.suptitle("The attack clears the threshold in every arm; only the "
             "recovered embedding separates them", fontsize=9, color=INK,
             x=0.008, ha="left", y=0.995)
fig.savefig(HERE / "fig8_inversion.pdf", bbox_inches="tight")
fig.savefig(HERE / "fig8_inversion.png", dpi=300, bbox_inches="tight")
plt.close(fig)

for mod in ("voice", "face"):
    for arm in ARMS:
        v = np.asarray(PK[mod][arm], float)
        print(f"{mod:<6}{arm:<14} mean {v.mean():6.2f}%  median "
              f"{np.median(v):6.2f}%  max {v.max():6.2f}%  "
              f"fail {int((v >= 50).sum())}/40")
print("wrote fig6, fig7, fig8")

"""Result figures for AttackAware PolyIoM v1.1.4.

Palette: reference categorical slots 1 (blue, voice) and 2 (orange, face),
validated all-pairs on the light surface (#fcfcfb): CVD dE 24.7,
normal-vision dE 33.6, both >= 3:1 contrast. Gray is de-emphasis, never a
series. One measure per axis; no dual axis anywhere.

These are print figures, so there is no hover layer - the Results tables
are the table view, and direct labels are selective (floors and the
selected configuration only, never a value on every point).
"""
import csv
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

HERE = Path(__file__).parent

# ---------------------------------------------------------------- tokens
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
VOICE = "#2a78d6"      # categorical slot 1
FACE = "#eb6834"       # categorical slot 2
DEEMPH = "#c9c8c2"     # de-emphasis, not a categorical slot

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5,
    "axes.titlesize": 8.8,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.6,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.labelcolor": INK_2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "grid.linestyle": "-",          # never dashed
    "legend.frameon": False,
    "pdf.fonttype": 42,
})


def style(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(True)
    ax.tick_params(length=3, pad=3)


def load(path):
    rows = list(csv.DictReader(open(HERE / path)))
    for r in rows:
        for k in ("EER", "TAR_DEV", "Dsys_DEV"):
            r[k] = float(r[k])
        for k in ("M", "q", "o"):
            r[k] = int(r[k])
    return rows


face = load("sweep_80_face.csv")
voice = load("sweep_80_voice.csv")

SEL = {
    "face": dict(M=256, q=32, o=1, eer=0.028390672383143,
                 tar=0.8625954198473282, dsys=0.1331002909486603),
    "voice": dict(M=128, q=32, o=1, eer=0.00952380952380952,
                  tar=0.9523809523809524, dsys=0.05251857190074913),
}
FLOOR = {"voice": (0.01, 0.95), "face": (0.03, 0.85)}


def eligible(rows, modality):
    e, t = FLOOR[modality]
    return [r for r in rows if r["EER"] <= e and r["TAR_DEV"] >= t]


# ==================================================== Figure 1: selection
fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.2))

# --- (a) EER x TAR, with both floors drawn as regions
style(axa)
for mod, rows, col in (("face", face, FACE), ("voice", voice, VOICE)):
    axa.scatter([r["EER"] * 100 for r in rows],
                [r["TAR_DEV"] * 100 for r in rows],
                s=26, c=col, alpha=0.75, linewidths=0.7, edgecolors=SURFACE,
                zorder=3, label=f"{mod} (80 configs)")

for mod, col in (("face", FACE), ("voice", VOICE)):
    e, t = FLOOR[mod]
    axa.add_patch(Rectangle((0, t * 100), e * 100, 100 - t * 100,
                            facecolor=col, alpha=0.07, edgecolor=col,
                            linewidth=0.7, zorder=1))

axa.annotate("voice floor", xy=(1.18, 97.8), fontsize=7.2, color=INK_2,
             ha="left", va="center")
axa.annotate("face floor", xy=(3.18, 94.8), fontsize=7.2, color=INK_2,
             ha="left", va="center")

# Selected configurations: a larger mark with a 2px surface ring. The
# M/q/o values live in the caption rather than on the plot.
for mod, col, xytext in (("voice", VOICE, (0.18, 86.5)),
                         ("face", FACE, (4.30, 92.5))):
    sp = SEL[mod]
    axa.scatter([sp["eer"] * 100], [sp["tar"] * 100], s=124, c=col,
                linewidths=1.8, edgecolors=SURFACE, zorder=5)
    axa.annotate("selected", xy=(sp["eer"] * 100, sp["tar"] * 100),
                 xytext=xytext, fontsize=7.4, color=INK, ha="left",
                 va="center",
                 arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.7,
                                 shrinkA=3, shrinkB=7))

axa.set_xlabel("EER (%), development")
axa.set_ylabel("TAR (%), development")
axa.set_xlim(0, 7.2)
axa.set_ylim(35, 103)
axa.set_title("(a)  No face configuration meets the voice floor",
              loc="left", color=INK, pad=7)
axa.legend(loc="lower right", handletextpad=0.4, borderpad=0.2)

# --- (b) EER x Dsys, emphasis on each modality's eligible set
style(axb)
for mod, rows, col in (("face", face, FACE), ("voice", voice, VOICE)):
    elig = {id(r) for r in eligible(rows, mod)}
    ine = [r for r in rows if id(r) not in elig]
    el = [r for r in rows if id(r) in elig]
    axb.scatter([r["EER"] * 100 for r in ine], [r["Dsys_DEV"] for r in ine],
                s=20, c=DEEMPH, alpha=0.85, linewidths=0.6,
                edgecolors=SURFACE, zorder=2)
    axb.scatter([r["EER"] * 100 for r in el], [r["Dsys_DEV"] for r in el],
                s=26, c=col, alpha=0.85, linewidths=0.7, edgecolors=SURFACE,
                zorder=3, label=f"{mod}, meets floor ({len(el)})")

for mod, col in (("face", FACE), ("voice", VOICE)):
    sp = SEL[mod]
    axb.scatter([sp["eer"] * 100], [sp["dsys"]], s=124, c=col,
                linewidths=1.8, edgecolors=SURFACE, zorder=5)

axb.scatter([], [], s=20, c=DEEMPH, linewidths=0.6, edgecolors=SURFACE,
            label="below floor")
axb.annotate("large mark = selected", xy=(7.05, 0.012), fontsize=7.0,
             color=MUTED, ha="right", va="bottom")
axb.set_xlabel("EER (%), development")
axb.set_ylabel("$D_{sys}$, development  (lower is better)")
axb.set_xlim(0, 7.2)
axb.set_ylim(0, 0.41)
axb.set_title("(b)  Lowest $D_{sys}$ that clears each floor",
              loc="left", color=INK, pad=7)
axb.legend(loc="upper right", handletextpad=0.4, borderpad=0.2)

fig.tight_layout(pad=1.1)
fig.savefig(HERE / "fig1_operating_point_selection.pdf")
fig.savefig(HERE / "fig1_operating_point_selection.png", dpi=300)
plt.close(fig)

# ============================================== Figure 2: generalisation
ROWS = [
    ("face",  "development (42)",     "dev"),
    ("face",  "held-out (58)",        "ho"),
    ("voice", "development (42)",     "dev"),
    ("voice", "held-out (58)",        "ho"),
    ("voice", "external, VCTK (110)", "ext"),
]

D = {
    ("face", "dev"):  dict(eer=2.839, tar=86.260, fmr=0.093, dsys=0.133100),
    ("face", "ho"):   dict(eer=(4.799, 1.945, 10.345),
                           tar=(82.239, 72.767, 89.933),
                           fmr=(0.041, 0.000, 0.218),
                           dsys=(0.150803, 0.122519, 0.282221)),
    ("voice", "dev"): dict(eer=0.952, tar=95.238, fmr=0.081, dsys=0.052519),
    ("voice", "ho"):  dict(eer=(1.928, 1.092, 2.919),
                           tar=(93.966, 89.655, 97.414),
                           fmr=(0.185, 0.028, 0.480),
                           dsys=(0.088431, 0.070803, 0.218493)),
    ("voice", "ext"): dict(eer=(2.798, 1.992, 3.807),
                           tar=(89.000, 85.727, 91.727),
                           fmr=(0.377, 0.202, 0.622),
                           dsys=(0.080300, 0.060294, 0.155097)),
}

# Threshold annotations are short numerals; their meaning is in the caption.
PANELS = [
    ("eer",  "EER (%)",            [(1.0, "1%"), (3.0, "3%")], (0, 11)),
    ("tar",  "TAR (%)",            [],                         (65, 100)),
    ("fmr",  "FMR (%)",            [(0.1, "0.1%")],            (0, 0.68)),
    ("dsys", "$D_{sys}$",          [],                         (0, 0.30)),
]

fig, axes = plt.subplots(1, 4, figsize=(7.6, 3.05))
ypos = list(range(len(ROWS)))[::-1]

for ax, (key, xlabel, refs, xlim) in zip(axes, PANELS):
    style(ax)
    ax.grid(False, axis="y")
    for ref, lab in refs:
        ax.axvline(ref, color=MUTED, linewidth=0.7, zorder=1)
        ax.annotate(lab, xy=(ref, len(ROWS) - 0.38), fontsize=6.8,
                    color=MUTED, ha="center", va="bottom")
    for y, (mod, _, stage) in zip(ypos, ROWS):
        col = VOICE if mod == "voice" else FACE
        v = D[(mod, stage)][key]
        if isinstance(v, tuple):
            est, lo, hi = v
            ax.plot([lo, hi], [y, y], color=col, linewidth=1.8,
                    solid_capstyle="butt", zorder=3)
            for cap in (lo, hi):
                ax.plot([cap, cap], [y - 0.16, y + 0.16], color=col,
                        linewidth=1.8, solid_capstyle="butt", zorder=3)
            ax.scatter([est], [y], s=46, c=col, linewidths=1.5,
                       edgecolors=SURFACE, zorder=5)
        else:
            # Development: point estimate, no interval - drawn hollow.
            ax.scatter([v], [y], s=34, facecolors=SURFACE, linewidths=1.3,
                       edgecolors=col, zorder=5)
    ax.set_yticks(ypos)
    ax.set_ylim(-0.6, len(ROWS) - 0.15)
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    if ax is axes[0]:
        ax.set_yticklabels([f"{m} · {lab}" for m, lab, _ in ROWS],
                           fontsize=7.4, color=INK_2)
    else:
        ax.set_yticklabels([])

handles = [
    Line2D([], [], color=FACE, linewidth=1.8, marker="o", markersize=5,
           markeredgecolor=SURFACE, markeredgewidth=1.3, label="face"),
    Line2D([], [], color=VOICE, linewidth=1.8, marker="o", markersize=5,
           markeredgecolor=SURFACE, markeredgewidth=1.3, label="voice"),
    Line2D([], [], color=MUTED, linewidth=0, marker="o", markersize=5,
           markerfacecolor=SURFACE, markeredgecolor=MUTED,
           markeredgewidth=1.3, label="development (no interval)"),
]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, -0.005), handletextpad=0.4,
           columnspacing=1.8)
fig.suptitle("Point estimates with 95% identity-cluster bootstrap "
             "intervals (2,000 replicates)", fontsize=8.8, color=INK,
             x=0.008, ha="left", y=0.99)
fig.tight_layout(pad=1.0, rect=(0, 0.075, 1, 0.935))
fig.savefig(HERE / "fig2_generalisation.pdf")
fig.savefig(HERE / "fig2_generalisation.png", dpi=300)
plt.close(fig)

print("eligible: face %d | voice %d | face under the VOICE floor %d"
      % (len(eligible(face, "face")), len(eligible(voice, "voice")),
         len([r for r in face if r["EER"] <= 0.01 and r["TAR_DEV"] >= 0.95])))
print("face best EER %.2f%%  best TAR %.2f%%"
      % (min(r["EER"] for r in face) * 100,
         max(r["TAR_DEV"] for r in face) * 100))
print("wrote fig1_operating_point_selection.{pdf,png}")
print("wrote fig2_generalisation.{pdf,png}")

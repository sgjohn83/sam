"""Method and protocol schematic for AttackAware PolyIoM v1.1.4."""
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = Path(__file__).parent

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
FILL = "#f2f1ec"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "figure.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "pdf.fonttype": 42,
})


def box(ax, x0, x1, y0, y1, text, fc=FILL, ec=AXIS, fs=7.2, tc=INK, lw=0.7,
        weight="normal"):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0,rounding_size=1.2",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=3, linespacing=1.45,
            fontweight=weight)


def arrow(ax, x0, y0, x1, y1, color=MUTED, lw=0.9):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7,
        color=color, linewidth=lw, shrinkA=0, shrinkB=0, zorder=4))


fig, (axa, axb) = plt.subplots(2, 1, figsize=(7.4, 4.9),
                               gridspec_kw={"height_ratios": [1.25, 1.0]})
for ax in (axa, axb):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

# ============================================================== panel (a)
axa.text(0, 99, "(a)  Protected template construction", fontsize=8.8,
         color=INK, ha="left", va="top")

W, GAP, Y0, Y1 = 14.2, 3.0, 62, 80
xs = [1.0 + i * (W + GAP) for i in range(6)]
stages = [
    "biometric\nsample",
    "frozen encoder\nFaceNet · ECAPA",
    "embedding\n$x \\in \\mathbb{R}^{512}$",
    "polynomial\ntransform",
    "IoM hash\n$M$ windows, $q$ buckets",
    "protected code\n$z \\in \\{0..q\\!-\\!1\\}^{M}$",
]
for i, (x0, txt) in enumerate(zip(xs, stages)):
    hi = i in (3, 4, 5)
    box(axa, x0, x0 + W, Y0, Y1, txt,
        fc="#eaf2fd" if hi else FILL,
        ec=BLUE if hi else AXIS, lw=0.9 if hi else 0.7)
    if i:
        arrow(axa, x0 - GAP, (Y0 + Y1) / 2, x0, (Y0 + Y1) / 2)

# The key feeds the two keyed stages.
box(axa, xs[3] + 1.0, xs[4] + W - 1.0, 40, 51,
    "application key  $K$ = (coefficients $C$, exponents $E$, overlap $o$,"
    "  projection $R$)", fc=SURFACE, ec=BLUE, fs=7.0, tc=INK_2, lw=0.9)
for i in (3, 4):
    arrow(axa, xs[i] + W / 2, 51, xs[i] + W / 2, Y0, color=BLUE, lw=0.9)

# What is measured on the codes.
box(axa, 30.0, 63.0, 12, 30,
    "Recognition\ncollision count $c(z_{enrol}, z_{probe})$\n"
    "accept when $c \\geq \\tau$", fc=FILL, ec=AXIS, fs=7.0)
box(axa, 66.0, 99.0, 12, 30,
    "Unlinkability\n$D_{sys}$ between $z$ and $z'$\n"
    "from two independent keys", fc=FILL, ec=AXIS, fs=7.0)
arrow(axa, xs[5] + W / 2 - 4, Y0, 52, 30)
arrow(axa, xs[5] + W / 2, Y0, 82, 30)

# ============================================================== panel (b)
axb.text(0, 99, "(b)  Identity partitions and the order of access",
         fontsize=8.8, color=INK, ha="left", va="top")

BX0, BW = 3.0, 70.0
per = BW / 150.0
segs = [(50, "background\n50", "#e6e5df"),
        (42, "development\n42", "#eaf2fd"),
        (58, "evaluation\n58", "#fdeee7")]
x = BX0
seg_x = {}
for n, lab, fc in segs:
    w = n * per
    axb.add_patch(Rectangle((x, 46), w, 17, facecolor=fc, edgecolor=AXIS,
                            linewidth=0.7, zorder=2))
    axb.text(x + w / 2, 54.5, lab, ha="center", va="center", fontsize=7.2,
             color=INK, zorder=3, linespacing=1.4)
    seg_x[lab.split("\n")[0]] = (x, x + w)
    x += w

axb.text(BX0, 66.5, "150 identities per modality, split once from the "
                    "master seed", fontsize=7.0, color=MUTED, ha="left",
         va="bottom")

# What each partition was used for.
uses = [
    ("background", "polynomial key search\n10k $\\rightarrow$ 20k candidates"),
    ("development", "thresholds, 80-configuration\nsweep, operating point"),
    ("evaluation", "held-out evaluation\nread only after sealing"),
]
for key, txt in uses:
    x0, x1 = seg_x[key]
    axb.text((x0 + x1) / 2, 40, txt, ha="center", va="top", fontsize=6.9,
             color=INK_2, linespacing=1.45)
    axb.plot([(x0 + x1) / 2, (x0 + x1) / 2], [46, 42.5], color=AXIS,
             linewidth=0.7, zorder=1)

# The seal boundary.
sx = seg_x["evaluation"][0]
axb.plot([sx, sx], [20, 72], color=ORANGE, linewidth=1.3, zorder=5)
axb.text(sx - 1.2, 73.5, "operating points sealed here", fontsize=7.0,
         color=ORANGE, ha="right", va="bottom", fontweight="bold")
axb.annotate("", xy=(sx - 16, 70), xytext=(sx - 1.5, 70),
             arrowprops=dict(arrowstyle="-|>", color=ORANGE, linewidth=0.9,
                             mutation_scale=7))

box(axb, 77.0, 99.0, 44, 65,
    "external corpus\nVCTK, 110 speakers\n\nread last, after the\ninternal "
    "method was frozen", fc=SURFACE, ec=ORANGE, fs=6.9, tc=INK_2, lw=0.9)

axb.text(BX0, 14, "No stage to the left of the seal reads an evaluation "
                  "identity or the external corpus.", fontsize=7.0,
         color=INK, ha="left", va="center")

fig.tight_layout(pad=0.7)
fig.savefig(HERE / "fig_method_protocol.pdf")
fig.savefig(HERE / "fig_method_protocol.png", dpi=300)
plt.close(fig)
print("wrote fig_method_protocol.{pdf,png}")

"""Three treatments of Figure 7, so the choice can be made by pointing."""
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from make_paper_figures import PK, ARMS, TAU, INV

LAB = ["PolyIoM (ours)", "IoM only", "Random proj. + IoM"]

# ---------------------------------------------- B: journal, muted colour
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 7, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
    "text.color": "black", "axes.labelcolor": "black",
    "xtick.color": "black", "ytick.color": "black",
    "axes.edgecolor": "black", "axes.linewidth": 0.7,
    "pdf.fonttype": 42, "legend.frameon": False,
})
MUTED = {"polyiom": "#1f4e79", "iom_only": "#9c4a1a", "randproj_iom": "#2d6a4f"}
MONO = {"polyiom": "#111111", "iom_only": "#111111", "randproj_iom": "#111111"}
FACE = {"polyiom": "#111111", "iom_only": "white", "randproj_iom": "#8a8a8a"}
SH = {"polyiom": "o", "iom_only": "s", "randproj_iom": "^"}


def strip(name, hue, facecol=None, size=(6.5, 1.95)):
    fig, axes = plt.subplots(1, 2, figsize=size, sharey=True,
                             gridspec_kw={"wspace": 0.14})
    rng = np.random.default_rng(2026)
    for c, mod in enumerate(("voice", "face")):
        ax = axes[c]
        for i, arm in enumerate(ARMS):
            v = np.asarray(PK[mod][arm], float)
            y = len(ARMS) - 1 - i + rng.uniform(-0.15, 0.15, v.size)
            ax.scatter(v, y, s=11, marker=SH[arm],
                       facecolor=(facecol or hue)[arm], edgecolor=hue[arm],
                       linewidth=0.6, zorder=3, clip_on=False)
        ax.axvline(50, color="black", lw=0.6, ls=(0, (3, 2.5)), zorder=2)
        ax.set_xlim(-3, 103)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_ylim(-0.5, 2.5)
        ax.set_yticks(range(3))
        ax.set_yticklabels(list(reversed(LAB)))
        ax.tick_params(direction="out", length=2.5, width=0.7, pad=2.5)
        ax.set_xlabel(f"({'ab'[c]}) {mod}: acceptance after re-keying (%)")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for i, arm in enumerate(ARMS):
            n = int((np.asarray(PK[mod][arm], float) >= 50).sum())
            ax.annotate(f"{n}/40", (101.5, len(ARMS) - 1 - i), fontsize=6,
                        va="center", ha="left", clip_on=False)
    fig.savefig(name + ".pdf", bbox_inches="tight")
    fig.savefig(name + ".png", dpi=300, bbox_inches="tight")
    plt.close(fig)


strip("v_B_journal_colour", MUTED)
strip("v_C_journal_mono", MONO, FACE)

# ---------------------------------------------- D: a different form
fig, axes = plt.subplots(3, 2, figsize=(6.5, 2.9), sharex=True, sharey=True,
                         gridspec_kw={"wspace": 0.10, "hspace": 0.30})
bins = np.arange(0, 110, 10)
for r, arm in enumerate(ARMS):
    for c, mod in enumerate(("voice", "face")):
        ax = axes[r, c]
        v = np.asarray(PK[mod][arm], float)
        ax.hist(v, bins=bins, color=MUTED[arm], edgecolor="white", lw=0.5)
        ax.axvline(50, color="black", lw=0.6, ls=(0, (3, 2.5)))
        ax.set_ylim(0, 42)
        ax.set_yticks([0, 20, 40])
        ax.tick_params(direction="out", length=2.5, width=0.7, pad=2.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if c == 0:
            ax.set_ylabel(LAB[r].replace(" (ours)", "").replace(
                "Random proj. + IoM", "Rand. proj."), fontsize=6.5)
        if r == 0:
            ax.set_title(f"({'ab'[c]}) {mod}", fontsize=7, loc="left")
        if r == 2:
            ax.set_xlabel("acceptance after re-keying (%)")
fig.text(0.006, 0.5, "number of fresh keys (of 40)", rotation=90,
         va="center", fontsize=7)
fig.savefig("v_D_histogram.pdf", bbox_inches="tight")
fig.savefig("v_D_histogram.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("wrote v_B_journal_colour, v_C_journal_mono, v_D_histogram")

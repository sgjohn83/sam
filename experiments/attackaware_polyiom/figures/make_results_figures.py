"""Additional result figures: design-space sensitivity and the trade-off
frontier. Both read only the two sealed sweeps."""
import csv
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

HERE = Path(__file__).parent

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
VOICE = "#2a78d6"
FACE = "#eb6834"
DEEMPH = "#c9c8c2"

# Sequential: one hue, light -> dark (reference blue ramp, steps 100-700)
BLUES = LinearSegmentedColormap.from_list("blues", [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95",
    "#0d366b"])

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.2,
    "xtick.labelsize": 7.6,
    "ytick.labelsize": 7.6,
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
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "grid.linestyle": "-",
    "legend.frameon": False,
    "pdf.fonttype": 42,
})

MS = [32, 64, 128, 256]
QS = [4, 8, 16, 32]
OS = [0, 1, 2, 3, 4]


def load(path):
    rows = list(csv.DictReader(open(HERE / path)))
    for r in rows:
        for k in ("EER", "TAR_DEV", "Dsys_DEV"):
            r[k] = float(r[k])
        for k in ("M", "q", "o"):
            r[k] = int(r[k])
    return rows


face, voice = load("sweep_80_face.csv"), load("sweep_80_voice.csv")
SEL = {"face": (256, 32, 1), "voice": (128, 32, 1)}
FLOOR = {"voice": (0.01, 0.95), "face": (0.03, 0.85)}


def grid(rows, o, key):
    g = np.full((len(MS), len(QS)), np.nan)
    for r in rows:
        if r["o"] == o:
            g[MS.index(r["M"]), QS.index(r["q"])] = r[key]
    return g


# ============================== Figure A: design space over M, q and o
vals = [r["Dsys_DEV"] for r in face + voice]
norm = Normalize(vmin=min(vals), vmax=max(vals))

fig, axes = plt.subplots(2, 5, figsize=(7.5, 3.5),
                         gridspec_kw={"wspace": 0.16, "hspace": 0.13})
for row, (name, rows) in enumerate((("face", face), ("voice", voice))):
    for col, o in enumerate(OS):
        ax = axes[row, col]
        g = grid(rows, o, "Dsys_DEV")
        ax.imshow(g, cmap=BLUES, norm=norm, origin="upper", aspect="auto")
        for i in range(len(MS)):
            for j in range(len(QS)):
                v = g[i, j]
                if np.isnan(v):
                    continue
                dark = norm(v) > 0.55
                ax.text(j, i, f"{v:.2f}".lstrip("0"), ha="center",
                        va="center", fontsize=5.9,
                        color=SURFACE if dark else INK_2)
        # Ring the sealed configuration.
        m, q, so = SEL[name]
        if so == o:
            ax.add_patch(plt.Rectangle(
                (QS.index(q) - 0.5, MS.index(m) - 0.5), 1, 1, fill=False,
                edgecolor=FACE if name == "face" else "#0d366b",
                linewidth=1.9, zorder=5))
        ax.set_xticks(range(len(QS)))
        ax.set_yticks(range(len(MS)))
        ax.set_xticklabels(QS if row == 1 else [])
        ax.set_yticklabels(MS if col == 0 else [])
        ax.tick_params(length=0, pad=2)
        for s in ax.spines.values():
            s.set_visible(False)
        if row == 0:
            ax.set_title(f"$o$ = {o}", pad=4, color=INK_2)
        if col == 0:
            ax.set_ylabel(f"{name}\n\n$M$", color=INK, labelpad=2)
        if row == 1:
            ax.set_xlabel("$q$")

cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=BLUES),
                  ax=axes, fraction=0.022, pad=0.015)
cb.set_label("$D_{sys}$, development  (lower is better)", color=INK_2,
             fontsize=8)
cb.outline.set_visible(False)
cb.ax.tick_params(length=2, labelsize=7.4, color=AXIS)
fig.suptitle("Unlinkability across the 80-configuration design space; "
             "the ringed cell is the sealed configuration",
             fontsize=8.8, color=INK, x=0.008, ha="left", y=0.985)
fig.savefig(HERE / "fig3_design_space.pdf", bbox_inches="tight")
fig.savefig(HERE / "fig3_design_space.png", dpi=300, bbox_inches="tight")
plt.close(fig)


# ===================== Figure B: recognition / unlinkability frontier
def pareto(rows):
    """Non-dominated set minimising both EER and Dsys."""
    pts = sorted(rows, key=lambda r: (r["EER"], r["Dsys_DEV"]))
    out, best = [], float("inf")
    for r in pts:
        if r["Dsys_DEV"] < best:
            out.append(r)
            best = r["Dsys_DEV"]
    return out


fig, ax = plt.subplots(figsize=(4.9, 3.6))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_axisbelow(True)
ax.grid(True)
ax.tick_params(length=3, pad=3)

for name, rows, col in (("face", face, FACE), ("voice", voice, VOICE)):
    e, t = FLOOR[name]
    ok = [r for r in rows if r["EER"] <= e and r["TAR_DEV"] >= t]
    no = [r for r in rows if r not in ok]
    ax.scatter([r["EER"] * 100 for r in no], [r["Dsys_DEV"] for r in no],
               s=17, c=DEEMPH, linewidths=0.6, edgecolors=SURFACE, zorder=2)
    ax.scatter([r["EER"] * 100 for r in ok], [r["Dsys_DEV"] for r in ok],
               s=24, c=col, alpha=0.9, linewidths=0.7, edgecolors=SURFACE,
               zorder=3, label=f"{name}, meets floor ({len(ok)})")
    pf = pareto(rows)
    ax.step([r["EER"] * 100 for r in pf], [r["Dsys_DEV"] for r in pf],
            where="post", color=col, linewidth=1.3, alpha=0.9, zorder=4)

for name, rows, col in (("face", face, FACE), ("voice", voice, VOICE)):
    m, q, o = SEL[name]
    r = next(x for x in rows if (x["M"], x["q"], x["o"]) == (m, q, o))
    ax.scatter([r["EER"] * 100], [r["Dsys_DEV"]], s=120, c=col,
               linewidths=1.8, edgecolors=SURFACE, zorder=6)

ax.scatter([], [], s=17, c=DEEMPH, linewidths=0.6, edgecolors=SURFACE,
           label="below floor")
ax.plot([], [], color=MUTED, linewidth=1.3, label="frontier")
ax.annotate("large mark = sealed configuration", xy=(7.05, 0.015),
            fontsize=7.0, color=MUTED, ha="right", va="bottom")
ax.set_xlabel("EER (%), development")
ax.set_ylabel("$D_{sys}$, development  (lower is better)")
ax.set_xlim(0, 7.2)
ax.set_ylim(0, 0.40)
ax.set_title("Recognition and unlinkability trade off across the "
             "design space",
             loc="left", color=INK, pad=7, fontsize=8.6)
ax.legend(loc="upper right", handletextpad=0.5, borderpad=0.2)
fig.tight_layout(pad=0.9)
fig.savefig(HERE / "fig4_frontier.pdf")
fig.savefig(HERE / "fig4_frontier.png", dpi=300)
plt.close(fig)

for name, rows in (("face", face), ("voice", voice)):
    pf = pareto(rows)
    m, q, o = SEL[name]
    on = any((r["M"], r["q"], r["o"]) == (m, q, o) for r in pf)
    print(f"{name}: frontier has {len(pf)} configs; sealed config on "
          f"frontier = {on}")
print("Dsys range %.3f - %.3f" % (min(vals), max(vals)))
print("wrote fig3_design_space.{pdf,png}  fig4_frontier.{pdf,png}")

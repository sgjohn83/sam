"""Drawing code for the results figures of AttackAware PolyIoM v1.1.4.

One source for two callers:

  reproducibility/figures.py       draws from the stored result files
  ALL_FIGURES notebook (Colab)     draws from results it has just computed

Every function takes the data it draws as an argument and reads nothing
from disk, so the figures are only ever as good as their inputs. The data
layout is the one the study's own runtime writes (ablation, inversion and
revocation results), plus four small pieces described in draw_all().

Needs numpy and matplotlib only.
"""

from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

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

STYLE = {
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5, "axes.titlesize": 8.6, "axes.labelsize": 8.2,
    "xtick.labelsize": 7.6, "ytick.labelsize": 7.6, "legend.fontsize": 7.6,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "grid.color": GRID,
    "grid.linewidth": 0.6, "grid.linestyle": "-", "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
}

def _check(cond, what):
    if not cond:
        raise ValueError(f"figure input check failed: {what}")


def close(a, b, tol):
    return abs(a - b) <= tol


def eligible(rows, mod, floor):
    e, t = floor[mod]
    return [r for r in rows if r["EER"] <= e and r["TAR_DEV"] >= t]


def save(fig, out, stem):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # No timestamps in the files, so a rerun reproduces them byte for byte.
    fig.savefig(out / f"{stem}.pdf", bbox_inches="tight",
                metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {stem}.png and .pdf")
    return stem

def style(ax, grid_axis="both"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(True, axis=grid_axis)
    ax.tick_params(length=3, pad=3)




def figure_selection(D, out):
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.2))
    style(axa)
    for mod, col in (("face", FACE), ("voice", VOICE)):
        rows = D["sweep"][mod]
        axa.scatter([r["EER"] * 100 for r in rows], [r["TAR_DEV"] * 100 for r in rows],
                    s=26, c=col, alpha=0.75, linewidths=0.7, edgecolors=SURFACE,
                    zorder=3, label=f"{mod} (80 settings)")
        e, t = D["floor"][mod]
        axa.add_patch(Rectangle((0, t * 100), e * 100, 100 - t * 100, facecolor=col,
                                alpha=0.07, edgecolor=col, linewidth=0.7, zorder=1))
    axa.annotate("voice floor", xy=(1.18, 97.8), fontsize=7.2, color=INK2, va="center")
    axa.annotate("face floor", xy=(3.18, 94.8), fontsize=7.2, color=INK2, va="center")
    for mod, col, xytext in (("voice", VOICE, (0.18, 86.5)), ("face", FACE, (4.30, 92.5))):
        s = D["selected"][mod]
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
        el = eligible(D["sweep"][mod], mod, D["floor"])
        ine = [r for r in D["sweep"][mod] if r not in el]
        axb.scatter([r["EER"] * 100 for r in ine], [r["Dsys_DEV"] for r in ine], s=20,
                    c=DEEMPH, alpha=0.85, linewidths=0.6, edgecolors=SURFACE, zorder=2)
        axb.scatter([r["EER"] * 100 for r in el], [r["Dsys_DEV"] for r in el], s=26,
                    c=col, alpha=0.85, linewidths=0.7, edgecolors=SURFACE, zorder=3,
                    label=f"{mod}, meets floor ({len(el)})")
        s = D["selected"][mod]
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
    return save(fig, out, "FigureS2_OperatingPointSelection")


# ============================================== Figure 3: the design space
def figure_design_space(D, out, MS=(32, 64, 128, 256), QS=(4, 8, 16, 32), OS=(0, 1, 2, 3, 4)):
    vals = [r["Dsys_DEV"] for m in D["sweep"] for r in D["sweep"][m]]
    norm = Normalize(vmin=min(vals), vmax=max(vals))
    fig, axes = plt.subplots(2, 5, figsize=(7.5, 3.5),
                             gridspec_kw={"wspace": 0.16, "hspace": 0.13})
    for row, mod in enumerate(("face", "voice")):
        for col, o in enumerate(OS):
            ax = axes[row, col]
            g = np.full((len(MS), len(QS)), np.nan)
            for r in D["sweep"][mod]:
                if r["o"] == o:
                    g[MS.index(r["M"]), QS.index(r["q"])] = r["Dsys_DEV"]
            ax.imshow(g, cmap=BLUES, norm=norm, origin="upper", aspect="auto")
            for i in range(len(MS)):
                for j in range(len(QS)):
                    v = g[i, j]
                    ax.text(j, i, f"{v:.2f}".lstrip("0"), ha="center", va="center",
                            fontsize=5.9, color=SURFACE if norm(v) > 0.55 else INK2)
            s = D["selected"][mod]
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
    return save(fig, out, "Figure3_DesignSpace")


# ================================================== Figure 4: the frontier
def pareto(rows):
    out, best = [], float("inf")
    for r in sorted(rows, key=lambda r: (r["EER"], r["Dsys_DEV"])):
        if r["Dsys_DEV"] < best:
            out.append(r)
            best = r["Dsys_DEV"]
    return out


def figure_frontier(D, out):
    fig, ax = plt.subplots(figsize=(4.9, 3.6))
    style(ax)
    for mod, col in (("face", FACE), ("voice", VOICE)):
        ok = eligible(D["sweep"][mod], mod, D["floor"])
        no = [r for r in D["sweep"][mod] if r not in ok]
        ax.scatter([r["EER"] * 100 for r in no], [r["Dsys_DEV"] for r in no], s=17,
                   c=DEEMPH, linewidths=0.6, edgecolors=SURFACE, zorder=2)
        ax.scatter([r["EER"] * 100 for r in ok], [r["Dsys_DEV"] for r in ok], s=24,
                   c=col, alpha=0.9, linewidths=0.7, edgecolors=SURFACE, zorder=3,
                   label=f"{mod}, meets floor ({len(ok)})")
        pf = pareto(D["sweep"][mod])
        ax.step([r["EER"] * 100 for r in pf], [r["Dsys_DEV"] for r in pf], where="post",
                color=col, linewidth=1.3, alpha=0.9, zorder=4)
        s = D["selected"][mod]
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
    return save(fig, out, "Figure4_Frontier")


# ============================================ Figure 5: generalisation
def figure_generalisation(D, out):
    rows = [("face", "development (42)", None), ("face", "held-out (58)", "face/evaluation"),
            ("voice", "development (42)", None), ("voice", "held-out (58)", "voice/evaluation"),
            ("voice", "external, VCTK (110)", "voice/external")]
    dev = {m: {"EER": D["selected"][m]["EER"] * 100, "TAR": D["selected"][m]["TAR_DEV"] * 100,
               "FMR": D["selected"][m]["FMR_DEV"] * 100, "Dsys": D["selected"][m]["Dsys_DEV"]}
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
                est, lo, hi = D["intervals"][part][key]
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
    return save(fig, out, "Figure5_Generalisation")


# ============================================ Figure P: protection cost
def figure_protection_cost(D, out):
    order = [("voice", "development"), ("voice", "evaluation"), ("voice", "external"),
             ("face", "development"), ("face", "evaluation")]
    name = {"development": "development (42)", "evaluation": "held-out (58)",
            "external": "external, VCTK (110)"}
    parts = {(p["modality"], p["partition"]): p for p in D["baseline"]}
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    style(ax, "x")
    ypos = list(range(len(order)))[::-1]
    for y, key in zip(ypos, order):
        p = parts[key]
        ci = D["intervals"].get(f"{key[0]}/{key[1]}", {}).get("EER")
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
    return save(fig, out, "FigureP_ProtectionCost")


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


def figure_ablation(D, out):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                             gridspec_kw={"wspace": 0.78, "hspace": 0.70})
    for r, mod in enumerate(("voice", "face")):
        arms = D["ablation"][mod]["arms"]
        eer = {a: (arms[a]["EER"] * 100, arms[a]["EER_CI"][0] * 100,
                   arms[a]["EER_CI"][1] * 100) for a in ARMS}
        dsys = {a: (arms[a]["Dsys"], *arms[a]["Dsys_CI"]) for a in ARMS}
        dot_interval(axes[r, 0], eer, xmax=11.5 if mod == "face" else 3.6, pct=True)
        dot_interval(axes[r, 1], dsys, xmax=0.33)
        axes[r, 0].set_title(f"{mod} — equal error rate (%)", loc="left", pad=6)
        axes[r, 1].set_title(f"{mod} — $D_{{sys}}$", loc="left", pad=6)
        for c in (0, 1):
            axes[r, c].set_xlabel("lower is better")
    v = {a: D["ablation"]["voice"]["arms"][a]["EER"] * 100 for a in ARMS}
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
    return save(fig, out, "Figure6_Ablation")


# ============================================ Figure 7: revocation per key
def figure_revocation(D, out):
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.45), gridspec_kw={"wspace": 0.30})
    rng = np.random.default_rng(D["revocation"]["master_seed"])
    n_keys = D["revocation"]["n_fresh_keys"]
    for c, mod in enumerate(("voice", "face")):
        m = D["revocation"]["modalities"][mod]
        ax = axes[c]
        counts = []
        for i, arm in enumerate(ARMS):
            vals = np.asarray(m["arms"][arm]["per_key_PRAR"], float) * 100
            _check(vals.size == n_keys, f"{mod}/{arm}: {vals.size} keys, expected {n_keys}")
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
    return save(fig, out, "Figure7_RevocationPerKey")


# ================================================ Figure 8: the inversion
def figure_inversion(D, out):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 3.6),
                             gridspec_kw={"wspace": 0.78, "hspace": 0.70})
    for r, mod in enumerate(("voice", "face")):
        inv = D["inversion"][mod]
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
            ra = D["revocation"]["modalities"][mod]["arms"][arm]
            _check(close(ra["cos_to_true"], inv["arms"][arm]["cos_to_true"], 1e-9),
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
    return save(fig, out, "Figure8_Inversion")



FIGURES = (figure_selection, figure_design_space, figure_frontier,
           figure_generalisation, figure_protection_cost, figure_ablation,
           figure_revocation, figure_inversion)


def draw_all(D, out):
    """Draw the eight results figures into `out`; return their file stems.

    D["sweep"]       {modality: [row, ...]}, 80 rows each, with keys
                     M, q, o, EER, TAR_DEV, FMR_DEV, Dsys_DEV (fractions)
    D["floor"]       {modality: (max EER, min TAR)} of the selection rule
    D["selected"]    {modality: the sweep row that was sealed}
    D["intervals"]   {"voice/evaluation" | "face/evaluation" |
                      "voice/external": {"EER" | "TAR" | "FMR": (point,
                      low, high) in percent, "Dsys": (point, low, high)}}
    D["baseline"]    [{modality, partition, protected_eer, unprotected_eer,
                      cost_pp, baseline_resolved,
                      unprotected_upper_bound_95}, ...] in percent
    D["ablation"]    ablation_result["modalities"]
    D["revocation"]  revocation_result (the whole record)
    D["inversion"]   inversion_result["modalities"]
    """
    stems = []
    for draw in FIGURES:
        # Start from matplotlib's defaults every time, so a style set by
        # other plotting code in the same session cannot leak in.
        with mpl.rc_context():
            mpl.rcdefaults()
            mpl.rcParams.update(STYLE)
            stems.append(draw(D, out))
    return stems

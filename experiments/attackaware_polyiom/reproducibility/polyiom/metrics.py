"""Metrics, transcribed from the study's implementation.

All four are computed from score histograms rather than raw score lists. A
collision score is an integer in 0..M, so a count per score value is a
lossless record and every rate below is exact.
"""

import numpy as np


def rates(genuine, impostor):
    """FMR and FNMR at every threshold.

    A comparison is accepted at a score of at least the threshold, so FMR
    is the upper tail of the impostor histogram and FNMR the lower tail of
    the genuine one. Both arrays have one entry more than there are score
    values, the last being a threshold above every score.
    """
    g = np.asarray(genuine, dtype=float)
    i = np.asarray(impostor, dtype=float)
    if g.sum() <= 0 or i.sum() <= 0:
        raise ValueError("rates require non-empty distributions")
    fmr = np.r_[np.cumsum(i[::-1])[::-1], 0.0] / i.sum()
    fnmr = np.r_[0.0, np.cumsum(g)] / g.sum()
    return fmr, fnmr


def eer(genuine, impostor):
    """Equal error rate, and the threshold index where it occurs.

    The exact-zero branch is not optional. Where the two distributions are
    well separated there is a run of thresholds at which both rates are
    zero, so the difference never changes sign and a crossing-only search
    finds nothing.
    """
    fmr, fnmr = rates(genuine, impostor)
    d = fmr - fnmr
    c = int(np.flatnonzero(np.abs(d) == np.abs(d).min())[0])
    exact = np.flatnonzero(d == 0.0)
    if len(exact):
        return float(fmr[exact[0]]), c
    crossings = np.flatnonzero((d[:-1] > 0.0) & (d[1:] < 0.0))
    if not len(crossings):
        raise AssertionError("EER crossing not found")
    j = int(crossings[0])
    w = d[j] / (d[j] - d[j + 1])
    return float(fmr[j] + w * (fmr[j + 1] - fmr[j])), c


def dlink_curve(mated, nonmated):
    """Local linkability D_link(s): 0 reveals nothing, 1 identifies."""
    m = np.asarray(mated, dtype=float)
    n = np.asarray(nonmated, dtype=float)
    if m.sum() <= 0 or n.sum() <= 0:
        raise ValueError("D_link requires non-empty distributions")
    pm, pn = m / m.sum(), n / n.sum()
    local = np.zeros_like(pm)
    for s in range(len(pm)):
        if pm[s] == 0:
            local[s] = 0.0
        elif pn[s] == 0:
            local[s] = 1.0
        else:
            ratio = pm[s] / pn[s]
            local[s] = 0.0 if ratio <= 1 else 2 * ratio / (1 + ratio) - 1
    return local, pm


def dsys(mated, nonmated):
    """Global linkability: the local curve averaged under the mated mass."""
    local, pm = dlink_curve(mated, nonmated)
    return float(np.sum(pm * local))


def tar_at(genuine, threshold):
    """Share of genuine comparisons accepted at a threshold."""
    g = np.asarray(genuine, dtype=float)
    return float(g[threshold:].sum() / g.sum())


def fmr_at(impostor, threshold):
    i = np.asarray(impostor, dtype=float)
    return float(i[threshold:].sum() / i.sum())


def prar(pseudo_impostor_scores, threshold):
    """Post-revocation acceptance: old templates still getting in.

    The share of subjects whose reconstruction from a pre-revocation
    template still reaches the threshold after re-keying.
    """
    s = np.asarray(pseudo_impostor_scores)
    return float((s >= threshold).mean())

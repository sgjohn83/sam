"""
Identity-cluster bootstrap confidence intervals for the external result.

Companion to the held-out confidence analysis. Same method
(identity_cluster_percentile_v1), applied to runs/external/voice so the
external point estimates can be compared against the held-out intervals on
equal footing.

Load after the v1.1.4 notebook cells, external_eval_cells.py and
vctk_prepare_cells.py:

    exec(open("/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4/"
              "external_confidence_cells.py").read())
    external_confidence()
    external_vs_heldout()

Writes runs/external/voice/external_confidence.json. The sealed
external_result.json is never touched.

WHY THE WEIGHTS, NOT A PHYSICAL RESAMPLE
----------------------------------------
Identities are the independent unit: the 10 genuine trials of one speaker
are correlated, so resampling trials would give falsely narrow intervals.
But physically resampling identities with replacement creates a second
problem - a speaker drawn twice would be compared against itself and
counted as an impostor trial, which is not an impostor comparison at all.

So each replicate draws multinomial identity counts and applies them as
weights: a genuine trial of identity i carries w_i, an ordered impostor
pair (a, b) carries w_a * w_b, and same-identity pairs are never formed.
This is the same weighting the held-out analysis used, so the two sets of
intervals are directly comparable.

Everything is precomputed as per-identity score histograms, so a replicate
is a weighted sum rather than a rescoring pass. 2000 replicates take
seconds.

VALIDATION
----------
The weighted metrics must reduce exactly to the notebook's own metric
functions when every weight is 1. The cell checks this twice before
bootstrapping: against the notebook's eer_discrete_interpolated /
dsys_discrete / tar_at_threshold on the flat score lists, and against the
sealed external_result.json. If either disagrees it raises rather than
reporting an interval built on a different definition.
"""

import hashlib
import json
import math

import numpy as np
import torch

EXT_N_BOOTSTRAP = 2000
EXT_CONFIDENCE = 0.95
EXT_METHOD_ID = "identity_cluster_percentile_v1"
EXT_TOLERANCE = 1e-9


def _ext_seed(modality):
    """Deterministic 63-bit seed from the master seed and a fixed label."""
    label = f"{MASTER_SEED}|external_confidence|{modality}".encode()
    return int.from_bytes(hashlib.sha256(label).digest()[:8], "big") >> 1


# ------------------------------------------------------- weighted metrics

def _tar_w(gen_hist, tau):
    total = gen_hist.sum()
    return float(gen_hist[tau:].sum() / total) if total > 0 else float("nan")


def _fmr_w(imp_hist, tau):
    total = imp_hist.sum()
    return float(imp_hist[tau:].sum() / total) if total > 0 else float("nan")


def _eer_w(gen_hist, imp_hist, M):
    """Weighted discrete EER with linear interpolation at the crossing.

    Accept when score >= c, so FMR falls and FNMR rises with c. The
    crossing is bracketed by the first c where FNMR(c) >= FMR(c), then
    interpolated between c-1 and c.
    """
    g_total, i_total = gen_hist.sum(), imp_hist.sum()
    if g_total <= 0 or i_total <= 0:
        return float("nan"), -1

    # FMR(c) = P(impostor >= c), FNMR(c) = P(genuine < c), c = 0..M
    imp_tail = np.concatenate([imp_hist[::-1].cumsum()[::-1], [0.0]])
    gen_head = np.concatenate([[0.0], gen_hist.cumsum()])
    fmr = imp_tail / i_total
    fnmr = gen_head / g_total

    diff = fmr - fnmr
    cross = int(np.argmax(diff <= 0))
    if diff[cross] > 0:                     # never crosses
        return float(fmr[-1]), M
    if cross == 0:
        return float((fmr[0] + fnmr[0]) / 2.0), 0

    d1, d2 = diff[cross - 1], diff[cross]
    t = 0.0 if d1 == d2 else float(d1 / (d1 - d2))
    eer = float(fmr[cross - 1] + t * (fmr[cross] - fmr[cross - 1]))
    return eer, cross


def _dsys_w(mated_hist, nonmated_hist, M):
    """Weighted Gomez-Barrero D_sys with omega = 1."""
    m_total, n_total = mated_hist.sum(), nonmated_hist.sum()
    if m_total <= 0 or n_total <= 0:
        return float("nan")
    p_m = mated_hist / m_total
    p_n = nonmated_hist / n_total
    denom = p_m + p_n
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.where(denom > 0, 2.0 * p_m / denom - 1.0, 0.0)
    d = np.clip(d, 0.0, 1.0)
    return float(np.sum(p_m * d))


# ------------------------------------------------- score reconstruction

def _external_histograms(modality="voice"):
    """Per-identity score histograms for the external corpus.

    Mirrors evaluate_external() exactly: same key, same sealed operating
    point, same development threshold, same two unlinkability keys. Only
    the bookkeeping differs - scores are kept grouped by identity instead
    of being flattened.
    """
    if modality != "voice":
        raise NotImplementedError(
            f"No external corpus is prepared for '{modality}'."
        )

    chosen = select_operating_point(modality)
    M, q, o = chosen["M"], chosen["q"], chosen["o"]
    tau = int(chosen["development"]["c_tau_DEV"])

    Ck, Ek = selected_poly_key(modality)
    subjects, enroll, probes = vctk_external_data()
    n = len(subjects)
    if n < 2:
        raise RuntimeError("Too few external identities.")

    d = len(enroll[subjects[0]])
    R = iom_tensor(modality, o, d).to(MODEL_DEVICE)

    def hashed(vec, Rx=R):
        x = torch.tensor(vec, dtype=torch.float32,
                         device=MODEL_DEVICE).unsqueeze(0)
        return iom_hash(
            poly_transform(x, Ck, Ek, o), Rx, M, q
        ).squeeze(0).cpu()

    enroll_z = {u: hashed(enroll[u]) for u in subjects}
    probe_z = {u: [hashed(x) for x in probes[u]] for u in subjects}

    bins = M + 1
    Ghist = np.zeros((n, bins), dtype=np.float64)
    Ihist = np.zeros((n, n, bins), dtype=np.float64)
    flat_gen, flat_imp = [], []

    for bi, true_u in enumerate(subjects):
        for zp in probe_z[true_u]:
            for ai, claimed_u in enumerate(subjects):
                c = int(collision_count(enroll_z[claimed_u], zp))
                if ai == bi:
                    Ghist[bi, c] += 1.0
                    flat_gen.append(c)
                else:
                    Ihist[ai, bi, c] += 1.0
                    flat_imp.append(c)

    # Unlinkability: the same two independently seeded IoM keys as the
    # sweep and the sealed external evaluation.
    k = 1 + math.ceil((d - G) / (G - o))

    def unlink_R(key_index):
        gen = torch.Generator(device="cpu")
        gen.manual_seed(seed_unlink(modality, key_index))
        return torch.randn(
            (M, q, k), generator=gen, dtype=torch.float32
        ).to(MODEL_DEVICE)

    R1, R2 = unlink_R(1), unlink_R(2)
    z1 = {u: hashed(enroll[u], R1) for u in subjects}
    z2 = {u: hashed(enroll[u], R2) for u in subjects}

    Mhist = np.zeros((n, bins), dtype=np.float64)
    Nhist = np.zeros((n, n, bins), dtype=np.float64)
    flat_mated, flat_nonmated = [], []

    for ai, u in enumerate(subjects):
        cm = int(collision_count(z1[u], z2[u]))
        Mhist[ai, cm] += 1.0
        flat_mated.append(cm)
        for bi, v in enumerate(subjects):
            if ai == bi:
                continue
            cn = int(collision_count(z1[u], z2[v]))
            Nhist[ai, bi, cn] += 1.0
            flat_nonmated.append(cn)

    return {
        "subjects": subjects, "n": n, "M": M, "q": q, "o": o, "tau": tau,
        "Ghist": Ghist, "Ihist": Ihist, "Mhist": Mhist, "Nhist": Nhist,
        "flat": (flat_gen, flat_imp, flat_mated, flat_nonmated),
        "chosen": chosen,
    }


def _apply_weights(H, w):
    """Collapse per-identity histograms under identity weights."""
    Ghist, Ihist, Mhist, Nhist = H["Ghist"], H["Ihist"], H["Mhist"], H["Nhist"]
    g = w @ Ghist
    i = w @ np.tensordot(w, Ihist, axes=(0, 0))
    m = w @ Mhist
    nm = w @ np.tensordot(w, Nhist, axes=(0, 0))
    return g, i, m, nm


def _metrics(H, w):
    g, i, m, nm = _apply_weights(H, w)
    M, tau = H["M"], H["tau"]
    eer, c_eer = _eer_w(g, i, M)
    return {
        "EER_EXT": eer,
        "TAR_EXT_at_dev_threshold": _tar_w(g, tau),
        "FMR_EXT_at_dev_threshold": _fmr_w(i, tau),
        "Dsys_EXT": _dsys_w(m, nm, M),
        "c_EER_EXT": c_eer,
    }


# ---------------------------------------------------------------- driver

def external_confidence(modality="voice", n_bootstrap=EXT_N_BOOTSTRAP,
                        confidence=EXT_CONFIDENCE):
    out_dir = DIR["runs"] / "external" / modality
    result_path = out_dir / "external_result.json"
    if not result_path.exists():
        raise RuntimeError(
            f"{modality}: no sealed external result. Run "
            f"evaluate_external('{modality}') first."
        )
    sealed = json.loads(result_path.read_text())

    print(f"reconstructing external scores for {modality} ...", flush=True)
    H = _external_histograms(modality)
    n, M = H["n"], H["M"]
    flat_gen, flat_imp, flat_mated, flat_nonmated = H["flat"]

    if n != int(sealed["n_subjects"]):
        raise RuntimeError(
            f"{n} identities reconstructed, sealed result has "
            f"{sealed['n_subjects']}. The external inputs changed."
        )

    ones = np.ones(n, dtype=np.float64)
    point = _metrics(H, ones)

    # 1. weighted metrics at unit weights must equal the notebook's own
    #    metric functions on the flat score lists
    ref_eer, ref_c = eer_discrete_interpolated(flat_gen, flat_imp, M)
    ref = {
        "EER_EXT": float(ref_eer),
        "TAR_EXT_at_dev_threshold": float(
            tar_at_threshold(flat_gen, H["tau"])),
        "FMR_EXT_at_dev_threshold": float(
            np.mean(np.asarray(flat_imp) >= H["tau"])),
        "Dsys_EXT": float(dsys_discrete(flat_mated, flat_nonmated, M)),
        "c_EER_EXT": int(ref_c),
    }
    bad = {k: (point[k], ref[k]) for k in ref
           if not (isinstance(point[k], int) and point[k] == ref[k])
           and abs(float(point[k]) - float(ref[k])) > 1e-6}
    if bad:
        raise RuntimeError(
            "Weighted metrics do not reproduce the notebook's own metric "
            "functions at unit weights, so an interval built from them "
            "would not describe the sealed estimate:\n"
            + "\n".join(f"  {k}: weighted={a!r} notebook={b!r}"
                        for k, (a, b) in bad.items())
        )

    # 2. and they must equal the sealed result
    drift = {k: (point[k], sealed[k]) for k in
             ("EER_EXT", "TAR_EXT_at_dev_threshold",
              "FMR_EXT_at_dev_threshold", "Dsys_EXT")
             if abs(float(point[k]) - float(sealed[k])) > 1e-6}
    if drift:
        raise RuntimeError(
            "Reconstruction does not match the sealed external result:\n"
            + "\n".join(f"  {k}: rebuilt={a!r} sealed={b!r}"
                        for k, (a, b) in drift.items())
        )
    print("reconstruction validated against the sealed result")

    # ---- bootstrap -------------------------------------------------
    seed = _ext_seed(modality)
    rng = np.random.default_rng(seed)
    keys = ("EER_EXT", "TAR_EXT_at_dev_threshold",
            "FMR_EXT_at_dev_threshold", "Dsys_EXT")
    draws = {k: np.empty(n_bootstrap) for k in keys}

    print(f"bootstrapping {n_bootstrap} replicates over {n} identities ...",
          flush=True)
    for b in range(n_bootstrap):
        w = rng.multinomial(n, np.full(n, 1.0 / n)).astype(np.float64)
        mb = _metrics(H, w)
        for k in keys:
            draws[k][b] = mb[k]
        if (b + 1) % 500 == 0:
            print(f"  {b + 1}/{n_bootstrap}", flush=True)

    alpha = (1.0 - confidence) / 2.0
    metrics = {}
    for k in keys:
        d = draws[k][np.isfinite(draws[k])]
        metrics[k] = {
            "estimate": float(point[k]),
            "lower": float(np.percentile(d, 100 * alpha)),
            "upper": float(np.percentile(d, 100 * (1 - alpha))),
        }

    record = {
        "schema": 1,
        "method_id": EXT_METHOD_ID,
        "confidence": confidence,
        "n_bootstrap": n_bootstrap,
        "master_seed": MASTER_SEED,
        "method": {
            "resampling_unit": "identity",
            "identity_draws_per_replicate": n,
            "interval": "two-sided percentile",
            "threshold_policy": "development threshold carried unchanged",
            "recognition_weighting": (
                "all genuine trials of a sampled identity receive its "
                "multinomial weight; ordered impostor identity pairs "
                "receive the product of their weights"),
            "unlinkability_weighting": (
                "mated scores receive identity weights; ordered non-mated "
                "identity pairs receive product weights; same-identity "
                "pairs are excluded"),
            "seed_derivation": (
                "sha256('<master_seed>|external_confidence|<modality>')"
                "[:8] as big-endian uint64, shifted right by 1"),
        },
        "modalities": {
            modality: {
                "corpus": sealed.get("corpus"),
                "M": H["M"], "q": H["q"], "o": H["o"],
                "c_tau_carried_from_DEV": H["tau"],
                "n_subjects": n,
                "n_genuine": len(flat_gen),
                "n_impostor": len(flat_imp),
                "bootstrap_seed": seed,
                "metrics": metrics,
                "reconstructed_point": point,
                "score_reconstruction": "validated_against_sealed_result",
            }
        },
        "source_external_sha256": {modality: sha256_file(result_path)},
    }

    out_path = out_dir / "external_confidence.json"
    atomic_json(out_path, record)
    mark_stage(f"external_confidence_{modality}",
               {"sha256": sha256_file(out_path)})

    print(f"\n{modality.upper()} external, {n} identities, "
          f"{n_bootstrap} replicates")
    for k in keys:
        m = metrics[k]
        scale = 1.0 if k == "Dsys_EXT" else 100.0
        unit = "" if k == "Dsys_EXT" else "%"
        print(f"  {k:32s} {m['estimate']*scale:7.3f}{unit}  "
              f"[{m['lower']*scale:7.3f}, {m['upper']*scale:7.3f}]")
    print(f"\nWrote {out_path}")
    return record


def external_vs_heldout(modality="voice"):
    """Do the external and held-out intervals overlap?

    Non-overlap is conservative evidence that the two differ; overlap is
    inconclusive rather than evidence of equality. The two sets are
    independent samples, so this is a comparison of intervals, not a
    paired test.
    """
    ext_p = DIR["runs"] / "external" / modality / "external_confidence.json"
    hel_p = DIR["runs"] / "heldout" / "heldout_confidence.json"
    if not ext_p.exists():
        print("No external_confidence.json yet. Run external_confidence().")
        return None
    if not hel_p.exists():
        print("No heldout_confidence.json found; nothing to compare.")
        return None

    ext = json.loads(ext_p.read_text())["modalities"][modality]["metrics"]
    hel = json.loads(hel_p.read_text())["modalities"][modality]["metrics"]
    pairs = [
        ("EER", "EER_EXT", "EER_HOLDOUT", 100.0, "%"),
        ("TAR", "TAR_EXT_at_dev_threshold",
         "TAR_HOLDOUT_at_dev_threshold", 100.0, "%"),
        ("FMR", "FMR_EXT_at_dev_threshold",
         "FMR_HOLDOUT_at_dev_threshold", 100.0, "%"),
        ("Dsys", "Dsys_EXT", "Dsys_HOLDOUT", 1.0, ""),
    ]

    print(f"{modality}: external (VCTK) vs held-out, 95% intervals\n")
    print(f"  {'':5s} {'held-out':>26s}   {'external':>26s}   verdict")
    rows = []
    for label, ke, kh, s, u in pairs:
        if ke not in ext or kh not in hel:
            continue
        e, h = ext[ke], hel[kh]
        overlap = not (e["upper"] < h["lower"] or h["upper"] < e["lower"])
        verdict = ("overlap - inconclusive" if overlap
                   else "no overlap - difference is firm")
        print(f"  {label:5s} "
              f"{h['estimate']*s:7.3f}{u} [{h['lower']*s:6.3f},"
              f"{h['upper']*s:6.3f}]   "
              f"{e['estimate']*s:7.3f}{u} [{e['lower']*s:6.3f},"
              f"{e['upper']*s:6.3f}]   {verdict}")
        rows.append({"metric": label, "overlap": overlap})
    return rows


print("External confidence analysis ready.")
print(f"  external_confidence()   - {EXT_N_BOOTSTRAP} identity-cluster "
      f"replicates, writes external_confidence.json")
print("  external_vs_heldout()   - interval overlap against the held-out CIs")

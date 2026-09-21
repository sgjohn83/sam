#@title 30. Hardening ablation — what does the polynomial actually buy?
"""Ablation at the SEALED operating point. Read only; changes no seal.

Why this exists
---------------
The 80-configuration sweep varies M, q and o. All three are IoM-GRP
parameters (o is the hardening window overlap, which only sets the output
length). No condition in the study removes the polynomial, so nothing in
the reported results shows what P_{K*} contributes over IoM-GRP alone.
This cell adds that condition.

Requires cells 20 (held-out) and 25 (external confidence) to have been run
first: it reuses _eer_w, _dsys_w, _tar_w, _fmr_w, _apply_weights and
EXT_TOLERANCE from the external confidence cell. Expect a few minutes per
modality - the paired bootstrap collapses three arms per replicate.

Three arms, all at the sealed M*, q*:

  polyiom       z -> P_{K*}(z; o*) -> IoM-GRP          the proposed method
  iom_only      z ----------------> IoM-GRP            the practical baseline
  randproj_iom  z -> A z ----------> IoM-GRP           isolates the polynomial

The third arm matters. Hardening also changes dimensionality: with window
G and overlap o the hardened vector has k = 1 + ceil((d-G)/(G-o)) entries,
so for face d=512 -> k=128 and for voice d=192 -> k=48. Comparing polyiom
against iom_only therefore confounds "the polynomial helps" with "a lower
projection dimension helps". Arm 3 applies a fixed random linear map to the
same k, so polyiom vs randproj_iom isolates the polynomial itself.

Protocol discipline
-------------------
  * Runs at the already-sealed (M*, q*, o*). No selection, no re-tuning.
  * EER and D_sys are threshold-free, so all three arms are directly
    comparable with no threshold carried between them.
  * TAR is reported at MATCHED FMR, and is labelled descriptive: it is
    computed on held-out data and is not a sealed operating point.
  * The proposed arm rebuilds the sealed pipeline exactly and its EER
    is checked against the sealed held-out result before anything is
    reported. A mismatch raises rather than printing numbers.
  * Confidence intervals use the same identity-cluster bootstrap as the
    held-out and external analyses, PAIRED: one identity weight vector per
    replicate is applied to all three arms, so the interval on a difference
    accounts for the arms sharing identities.
"""

ABL_N_BOOTSTRAP = 2000
ABL_CONFIDENCE = 0.95
ABL_METHOD_ID = "identity_cluster_percentile_v1_paired"
ABL_ARMS = ("polyiom", "iom_only", "randproj_iom")


def _abl_seed(modality, label):
    """Deterministic 63-bit seed; distinct from every other seed stream."""
    raw = f"{MASTER_SEED}|ablation|{PROTOCOL_VERSION}|{modality}|{label}"
    return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big") >> 1


def _abl_randn(shape, modality, label):
    gen = torch.Generator(device="cpu")
    gen.manual_seed(_abl_seed(modality, label) % (2 ** 63 - 1))
    return torch.randn(shape, generator=gen, dtype=torch.float32)


def ablation_histograms(modality):
    """Per-identity score histograms for all three arms, one pass.

    Identity order is shared across arms, which is what makes the paired
    bootstrap valid.
    """
    assert_internal_frozen(modality)
    seal_path = DIR["seal"] / f"operating_point_{modality}.json"
    if not seal_path.exists():
        raise RuntimeError(
            f"{modality}: no sealed operating point. Seal one before "
            f"running the ablation."
        )
    chosen = json.loads(seal_path.read_text())
    M, q, o = chosen["M"], chosen["q"], chosen["o"]
    tau = int(chosen["development"]["c_tau_DEV"])

    Ck, Ek = selected_poly_key(modality)
    subjects, enroll, probes = heldout_data(modality)
    n = len(subjects)
    if n < 2:
        raise RuntimeError(f"{modality}: too few held-out identities.")

    d = len(enroll[subjects[0]])
    k = 1 + math.ceil((d - G) / (G - o))

    # Matching tensors. polyiom reuses the study's own tensor so the arm
    # reproduces evaluate_heldout() exactly.
    R_poly = iom_tensor(modality, o, d).to(MODEL_DEVICE)
    R_raw = _abl_randn((M, q, d), modality, "match|iom_only").to(MODEL_DEVICE)
    R_prj = _abl_randn((M, q, k), modality, "match|randproj").to(MODEL_DEVICE)
    A = _abl_randn((d, k), modality, "projmap").to(MODEL_DEVICE) / math.sqrt(d)

    # Unlinkability tensors: two independent keys per arm, as in the sweep.
    def unlink_poly(i):
        gen = torch.Generator(device="cpu")
        gen.manual_seed(seed_unlink(modality, i))
        return torch.randn((M, q, k), generator=gen,
                           dtype=torch.float32).to(MODEL_DEVICE)

    U = {
        "polyiom": (unlink_poly(1), unlink_poly(2)),
        "iom_only": tuple(_abl_randn((M, q, d), modality, f"unlink|raw|{i}")
                          .to(MODEL_DEVICE) for i in (1, 2)),
        "randproj_iom": tuple(_abl_randn((M, q, k), modality, f"unlink|prj|{i}")
                              .to(MODEL_DEVICE) for i in (1, 2)),
    }

    def embed(vec):
        return torch.tensor(vec, dtype=torch.float32,
                            device=MODEL_DEVICE).unsqueeze(0)

    def code(arm, vec, R):
        x = embed(vec)
        if arm == "polyiom":
            x = poly_transform(x, Ck, Ek, o)
        elif arm == "randproj_iom":
            x = x @ A
        return iom_hash(x, R, M, q).squeeze(0).cpu()

    R_match = {"polyiom": R_poly, "iom_only": R_raw, "randproj_iom": R_prj}
    H = {arm: {
        "Ghist": np.zeros((n, M + 1)), "Ihist": np.zeros((n, n, M + 1)),
        "Mhist": np.zeros((n, M + 1)), "Nhist": np.zeros((n, n, M + 1)),
        "M": M, "tau": tau,
    } for arm in ABL_ARMS}

    for arm in ABL_ARMS:
        enrolled = {u: code(arm, enroll[u], R_match[arm]) for u in subjects}
        for ti, true_uid in enumerate(subjects):
            for xnp in probes[true_uid]:
                zp = code(arm, xnp, R_match[arm])
                for ci, claimed in enumerate(subjects):
                    c = int(collision_count(enrolled[claimed], zp))
                    if ci == ti:
                        H[arm]["Ghist"][ti, c] += 1.0
                    else:
                        H[arm]["Ihist"][ti, ci, c] += 1.0

        R1, R2 = U[arm]
        z1 = {u: code(arm, enroll[u], R1) for u in subjects}
        z2 = {u: code(arm, enroll[u], R2) for u in subjects}
        for ui, u in enumerate(subjects):
            H[arm]["Mhist"][ui, int(collision_count(z1[u], z2[u]))] += 1.0
            for vi, v in enumerate(subjects):
                if ui != vi:
                    H[arm]["Nhist"][ui, vi,
                                    int(collision_count(z1[u], z2[v]))] += 1.0
        print(f"  {modality} {arm}: histograms built "
              f"(d={d}, k={k}, M={M}, q={q})")

    return H, {"M": M, "q": q, "o": o, "tau": tau, "d": d, "k": k,
               "n_subjects": n,
               "selection_rule_id": chosen["rule"]["rule_id"]}


def _tar_at_matched_fmr(gen_hist, imp_hist, target_fmr):
    """Largest threshold whose FMR still meets the target, and its TAR.

    Descriptive only - computed on held-out scores, not a sealed point.
    """
    i_total = imp_hist.sum()
    if i_total <= 0:
        return float("nan"), -1
    Mx = len(imp_hist) - 1
    best = None
    for c in range(Mx, -1, -1):
        if float(imp_hist[c:].sum() / i_total) <= target_fmr + EXT_TOLERANCE:
            best = c
        else:
            break
    if best is None:
        return float("nan"), -1
    return _tar_w(gen_hist, best), best


def ablation_heldout(modality, n_bootstrap=ABL_N_BOOTSTRAP,
                     confidence=ABL_CONFIDENCE):
    out_dir = DIR["runs"] / "ablation" / modality
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "ablation_result.json"
    if result_path.exists():
        r = json.loads(result_path.read_text())
        print(f"Already run: {modality}")
        return r

    print(f"\n{modality.upper()}  building histograms for "
          f"{len(ABL_ARMS)} arms")
    H, meta = ablation_histograms(modality)
    n, M = meta["n_subjects"], meta["M"]
    w_flat = np.full(n, 1.0 / n)

    def point(arm, w):
        g, i, m, nm = _apply_weights(H[arm], w)
        eer, c_eer = _eer_w(g, i, M)
        return {"EER": eer, "c_EER": c_eer, "Dsys": _dsys_w(m, nm, M),
                "_g": g, "_i": i}

    base = {arm: point(arm, w_flat) for arm in ABL_ARMS}

    # Self-check. The polyiom arm rebuilds exactly what evaluate_heldout()
    # did - same key, same tensors, same seeds - so its EER must reproduce
    # the sealed held-out figure. A mismatch means this cell has drifted
    # from the study and its numbers must not be reported.
    ref_path = DIR["runs"] / "heldout" / modality / "heldout_result.json"
    reproduced = None
    if ref_path.exists():
        ref = json.loads(ref_path.read_text())
        delta = abs(base["polyiom"]["EER"] - ref["EER_HOLDOUT"])
        reproduced = bool(delta <= 1e-9)
        flag = "matches" if reproduced else "DOES NOT MATCH"
        print(f"  self-check: polyiom EER {base['polyiom']['EER']*100:.4f}% "
              f"{flag} sealed held-out {ref['EER_HOLDOUT']*100:.4f}%")
        if not reproduced:
            raise RuntimeError(
                f"{modality}: ablation's polyiom arm does not reproduce the "
                f"sealed held-out EER (delta {delta:.3e}). Refusing to "
                f"report - the arm is not the study's pipeline."
            )
    else:
        print("  self-check skipped: no sealed held-out result to compare")

    # Matched-FMR TAR: the reference is the proposed arm at its sealed
    # threshold, and every arm is then read at that same FMR.
    ref_fmr = _fmr_w(base["polyiom"]["_i"], meta["tau"])
    for arm in ABL_ARMS:
        tar, c = _tar_at_matched_fmr(base[arm]["_g"], base[arm]["_i"], ref_fmr)
        base[arm]["TAR_at_matched_FMR"] = tar
        base[arm]["c_matched"] = c

    print(f"  paired bootstrap, {n_bootstrap} replicates over {n} identities")
    rng = np.random.default_rng(_abl_seed(modality, "bootstrap"))
    draws = {arm: {"EER": [], "Dsys": []} for arm in ABL_ARMS}
    diffs = {arm: {"dEER": [], "dDsys": []}
             for arm in ABL_ARMS if arm != "polyiom"}
    for _ in range(n_bootstrap):
        w = rng.multinomial(n, w_flat) / float(n)   # one draw, all arms
        rep = {}
        for arm in ABL_ARMS:
            g, i, m, nm = _apply_weights(H[arm], w)
            e, _ = _eer_w(g, i, M)
            dv = _dsys_w(m, nm, M)
            rep[arm] = (e, dv)
            draws[arm]["EER"].append(e)
            draws[arm]["Dsys"].append(dv)
        for arm in diffs:
            diffs[arm]["dEER"].append(rep[arm][0] - rep["polyiom"][0])
            diffs[arm]["dDsys"].append(rep[arm][1] - rep["polyiom"][1])

    lo_p, hi_p = (1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100

    def ci(v):
        a = np.asarray(v, dtype=float)
        a = a[np.isfinite(a)]
        if a.size == 0:
            return [float("nan"), float("nan")]
        return [float(np.percentile(a, lo_p)), float(np.percentile(a, hi_p))]

    result = {
        "modality": modality, "protocol": PROTOCOL_VERSION,
        "partition": "evaluation", "analysis": "hardening_ablation",
        "changes_any_seal": False,
        "polyiom_arm_reproduces_sealed_heldout": reproduced,
        "method_id": ABL_METHOD_ID, "n_bootstrap": n_bootstrap,
        "confidence": confidence,
        **{kk: meta[kk] for kk in ("M", "q", "o", "tau", "d", "k",
                                   "n_subjects", "selection_rule_id")},
        "reference_FMR_for_matched_TAR": float(ref_fmr),
        "arms": {arm: {
            "EER": float(base[arm]["EER"]),
            "EER_CI": ci(draws[arm]["EER"]),
            "Dsys": float(base[arm]["Dsys"]),
            "Dsys_CI": ci(draws[arm]["Dsys"]),
            "TAR_at_matched_FMR_descriptive":
                float(base[arm]["TAR_at_matched_FMR"]),
        } for arm in ABL_ARMS},
        "contrasts_vs_polyiom": {arm: {
            "delta_EER": float(base[arm]["EER"] - base["polyiom"]["EER"]),
            "delta_EER_CI": ci(diffs[arm]["dEER"]),
            "delta_Dsys": float(base[arm]["Dsys"] - base["polyiom"]["Dsys"]),
            "delta_Dsys_CI": ci(diffs[arm]["dDsys"]),
        } for arm in diffs},
    }
    atomic_json(result_path, result)
    print(f"  wrote {result_path}")
    return result


def ablation_report(modality):
    """The table to transcribe, plus the reading of each contrast."""
    p = DIR["runs"] / "ablation" / modality / "ablation_result.json"
    if not p.exists():
        print(f"{modality}: not run")
        return None
    r = json.loads(p.read_text())
    print(f"\n{modality.upper()}  M={r['M']} q={r['q']} o={r['o']}  "
          f"d={r['d']} -> k={r['k']}  n={r['n_subjects']} identities")
    print(f"{'arm':<14}{'EER %':>20}{'Dsys':>22}{'TAR@FMR %':>12}")
    for arm in ABL_ARMS:
        a = r["arms"][arm]
        print(f"{arm:<14}"
              f"{a['EER']*100:8.3f} [{a['EER_CI'][0]*100:5.3f},"
              f"{a['EER_CI'][1]*100:6.3f}]"
              f"{a['Dsys']:9.4f} [{a['Dsys_CI'][0]:6.4f},"
              f"{a['Dsys_CI'][1]:6.4f}]"
              f"{a['TAR_at_matched_FMR_descriptive']*100:11.2f}")
    print(f"\n  matched at FMR = "
          f"{r['reference_FMR_for_matched_TAR']*100:.3f}% "
          f"(proposed arm at its sealed threshold)")

    print("\n  contrasts (arm minus proposed; CI excluding 0 is firm)")
    for arm, c in r["contrasts_vs_polyiom"].items():
        for name, key in (("EER", "EER"), ("Dsys", "Dsys")):
            dv, lo, hi = (c[f"delta_{key}"], *c[f"delta_{key}_CI"])
            firm = "FIRM" if (lo > 0 or hi < 0) else "not distinguishable"
            scale = 100 if key == "EER" else 1
            unit = " %" if key == "EER" else ""
            print(f"    {arm:<14} d{name:<5} "
                  f"{dv*scale:+8.3f}{unit}  "
                  f"[{lo*scale:+7.3f},{hi*scale:+7.3f}]  {firm}")
    print("\n  Reading: a POSITIVE delta means that arm is worse than the")
    print("  proposed method on that metric (higher EER, higher Dsys).")
    print("  randproj_iom is the arm that isolates the polynomial, since")
    print("  it matches the proposed method's projection dimension k.")
    return r


def run_all_ablation():
    for modality in ("voice", "face"):
        try:
            ablation_heldout(modality)
            ablation_report(modality)
        except Exception as exc:
            print(f"{modality}: skipped - {type(exc).__name__}: {exc}")

"""Regenerate every results figure from code, for AttackAware PolyIoM v1.1.4.

Loaded by AttackAware_PolyIoM_v1_1_4_ALL_FIGURES.ipynb after the study's
own runtime (ablation_only.py, scoredump_only.py, inversion_only.py and
revocation_only.py). Those files compute the ablation, the score
histograms, the inversion attack and the revocation test exactly as the
study did. This file adds the three computations they do not cover, and
the checks:

  sweep        the 80-setting development sweep behind Figures 3, 4, S2
  intervals    the identity-cluster bootstrap intervals behind Figure 5
  baseline     protected against unprotected EER, behind Figure P

Inputs are read from RUNS_IN (the study's runs/ folder) and every output
is written to DIR["runs"], which the notebook points at a separate folder.
Nothing in runs/ or seal/ is ever written.

After each stage the regenerated result is compared with the study's
original output, where that output is on Drive, and the differences are
printed. A figure is therefore only drawn from numbers this notebook has
computed and then checked.
"""

# ------------------------------------------------------------ input paths
# The study's runtime reads its inputs through DIR["runs"]. The notebook
# redirects DIR["runs"] to a fresh output folder, so the two readers below
# are redefined to keep reading the sealed inputs from RUNS_IN.

def selected_poly_key(modality):
    path = RUNS_IN / "key_search" / modality / "selected_key.json"
    obj = json.loads(path.read_text())
    return np.asarray(obj["C"], np.float32), np.asarray(obj["E"], np.int64)


def load_iom_tensor(modality, overlap, d):
    k = 1 + math.ceil((d - G) / (G - overlap))
    path = RUNS_IN / "iom_tensors" / f"{modality}_o{overlap}_k{k}.pt"
    if not path.is_file():
        raise FileNotFoundError(f"Frozen IoM tensor is missing: {path}")
    try:
        tensor = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        tensor = torch.load(path, map_location="cpu")
    if (tensor.ndim != 3 or tensor.shape[0] < 256 or tensor.shape[1] < 32
            or tensor.shape[-1] != k):
        raise RuntimeError(f"Frozen IoM tensor has an invalid shape: {path}")
    return tensor


VCTK_EMB = DIR["embeddings"] / "vctk_external_embeddings.npz"


def vctk_external_data():
    """External VCTK identities, built as the sealed external evaluation
    built them: ranks 0-4 averaged for enrolment, ranks 5-14 as probes."""
    z = np.load(VCTK_EMB, allow_pickle=False)
    E = z["embedding"].astype(np.float32)
    table = pd.DataFrame({
        "speaker_id": z["speaker_id"].astype(str),
        "rank": z["rank"].astype(int),
        "embedding_index": z["embedding_index"].astype(int),
    })
    subjects, enroll, probes = [], {}, {}
    for uid, g in table.groupby("speaker_id"):
        g = g.sort_values("rank")
        if len(g) != 15:
            continue
        uid = str(uid)
        members = np.stack([E[int(r.embedding_index)]
                            for r in g[g["rank"] < 5].itertuples(index=False)])
        subjects.append(uid)
        enroll[uid] = l2_np(np.mean(members, axis=0))
        probes[uid] = [E[int(r.embedding_index)]
                       for r in g[g["rank"] >= 5].itertuples(index=False)]
    return sorted(subjects), enroll, probes


# ------------------------------------------- weighted metrics (unchanged)
# From external_confidence_cells.py, the study's identity_cluster_percentile_v1
# method. A genuine trial of identity i carries weight w_i; an ordered
# impostor pair (a, b) carries w_a * w_b; same-identity pairs never form.

def _tar_w(gen_hist, tau):
    total = gen_hist.sum()
    return float(gen_hist[tau:].sum() / total) if total > 0 else float("nan")


def _fmr_w(imp_hist, tau):
    total = imp_hist.sum()
    return float(imp_hist[tau:].sum() / total) if total > 0 else float("nan")


def _eer_w(gen_hist, imp_hist, M):
    g_total, i_total = gen_hist.sum(), imp_hist.sum()
    if g_total <= 0 or i_total <= 0:
        return float("nan"), -1
    imp_tail = np.concatenate([imp_hist[::-1].cumsum()[::-1], [0.0]])
    gen_head = np.concatenate([[0.0], gen_hist.cumsum()])
    fmr = imp_tail / i_total
    fnmr = gen_head / g_total
    diff = fmr - fnmr
    cross = int(np.argmax(diff <= 0))
    if diff[cross] > 0:
        return float(fmr[-1]), M
    if cross == 0:
        return float((fmr[0] + fnmr[0]) / 2.0), 0
    d1, d2 = diff[cross - 1], diff[cross]
    t = 0.0 if d1 == d2 else float(d1 / (d1 - d2))
    return float(fmr[cross - 1] + t * (fmr[cross] - fmr[cross - 1])), cross


def _dsys_w(mated_hist, nonmated_hist, M):
    m_total, n_total = mated_hist.sum(), nonmated_hist.sum()
    if m_total <= 0 or n_total <= 0:
        return float("nan")
    p_m = mated_hist / m_total
    p_n = nonmated_hist / n_total
    denom = p_m + p_n
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.where(denom > 0, 2.0 * p_m / denom - 1.0, 0.0)
    return float(np.sum(p_m * np.clip(d, 0.0, 1.0)))


def _apply_weights(H, w):
    g = w @ H["Ghist"]
    i = w @ np.tensordot(w, H["Ihist"], axes=(0, 0))
    m = w @ H["Mhist"]
    nm = w @ np.tensordot(w, H["Nhist"], axes=(0, 0))
    return g, i, m, nm


def _metrics(H, w):
    g, i, m, nm = _apply_weights(H, w)
    eer, c_eer = _eer_w(g, i, H["M"])
    return {"EER": eer, "c_EER": c_eer,
            "TAR": _tar_w(g, H["tau"]), "FMR": _fmr_w(i, H["tau"]),
            "Dsys": _dsys_w(m, nm, H["M"])}


# ------------------------------------- per-identity score histograms
def unlink_tensor(modality, index, M, q, k, variant="shape"):
    """One of the two independently seeded unlinkability keys.

    "shape" draws exactly (M, q, k), as the held-out evaluation and the
    ablation do. "slice" draws the largest grid (256, 32, k) and slices it;
    the sweep stage tries it only if "shape" fails to reproduce a row.
    """
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed_unlink(modality, index))
    if variant == "shape":
        return torch.randn((M, q, k), generator=generator, dtype=torch.float32)
    full = torch.randn((max(GRID["M"]), max(GRID["q"]), k),
                       generator=generator, dtype=torch.float32)
    return full[:M, :q].contiguous()


def identity_histograms(modality, subjects, enroll, probes, M, q, o, tau,
                        frozen=None, variant="shape"):
    """Genuine, impostor, mated and non-mated score histograms per identity,
    from the sealed pipeline (polynomial K*, frozen IoM tensor R)."""
    key = selected_poly_key(modality)
    n, d = len(subjects), len(enroll[subjects[0]])
    k = 1 + math.ceil((d - G) / (G - o))
    if frozen is None:
        frozen = load_iom_tensor(modality, o, d)
    recognition = frozen[:M, :q].to(DEVICE, torch.float32)

    enrolment = [enroll[u] for u in subjects]
    probe_vectors, owners = [], []
    for index, u in enumerate(subjects):
        probe_vectors.extend(probes[u])
        owners.extend([index] * len(probes[u]))
    owners = np.asarray(owners)
    enrolled = hash_arm(enrolment, "polyiom", key, o, recognition, M, q, None)
    hashed = hash_arm(probe_vectors, "polyiom", key, o, recognition, M, q, None)
    collision = (hashed[:, None, :] == enrolled[None, :, :]).sum(axis=-1)

    bins = M + 1
    Ghist = np.zeros((n, bins))
    Ihist = np.zeros((n, n, bins))           # [claimed, true, score]
    rows = np.arange(len(owners))
    np.add.at(Ghist, (owners, collision[rows, owners]), 1.0)
    for claimed in range(n):
        other = owners != claimed
        np.add.at(Ihist, (claimed, owners[other], collision[other, claimed]), 1.0)

    first = hash_arm(enrolment, "polyiom", key, o,
                     unlink_tensor(modality, 1, M, q, k, variant).to(DEVICE),
                     M, q, None)
    second = hash_arm(enrolment, "polyiom", key, o,
                      unlink_tensor(modality, 2, M, q, k, variant).to(DEVICE),
                      M, q, None)
    cross = (first[:, None, :] == second[None, :, :]).sum(axis=-1)
    Mhist = np.zeros((n, bins))
    Nhist = np.zeros((n, n, bins))
    Mhist[np.arange(n), np.diag(cross)] = 1.0
    for a in range(n):
        for b in range(n):
            if a != b:
                Nhist[a, b, cross[a, b]] = 1.0
    return {"subjects": subjects, "n": n, "M": M, "q": q, "o": o, "tau": tau,
            "Ghist": Ghist, "Ihist": Ihist, "Mhist": Mhist, "Nhist": Nhist}


# ----------------------------------------------------------------- sweep
def _config():
    path = DIR["seal"] / "config_v1_1_4.json"
    if path.is_file():
        return json.loads(path.read_text())
    print("  seal/config_v1_1_4.json not found; using the documented grid")
    return {"M_grid": [32, 64, 128, 256], "q_grid": [4, 8, 16, 32],
            "overlaps": [0, 1, 2, 3, 4], "target_fmr": 0.001}


CONFIG = _config()
GRID = {"M": CONFIG["M_grid"], "q": CONFIG["q_grid"], "o": CONFIG["overlaps"]}
SWEEP_FIELDS = ("EER", "c_EER", "c_tau_DEV", "TAR_DEV", "FMR_DEV",
                "FNMR_DEV", "Dsys_DEV")


def dev_threshold(imp_hist, target):
    """The lowest score at which the development FMR meets the target."""
    total = imp_hist.sum()
    for c in range(len(imp_hist) + 1):
        if imp_hist[c:].sum() / total <= target + 1e-12:
            return c
    return len(imp_hist)


def sweep_row(modality, H):
    ones = np.ones(H["n"])
    g, i, m, nm = _apply_weights(H, ones)
    eer, c_eer = _eer_w(g, i, H["M"])
    tau = dev_threshold(i, CONFIG["target_fmr"])
    tar = _tar_w(g, tau)
    return {"modality": modality, "M": H["M"], "q": H["q"], "o": H["o"],
            "n_subjects": H["n"], "n_genuine": int(g.sum()),
            "n_impostor": int(i.sum()), "c_tau_DEV": tau, "EER": eer,
            "c_EER": c_eer, "TAR_DEV": tar, "FMR_DEV": _fmr_w(i, tau),
            "FNMR_DEV": 1.0 - tar, "Dsys_DEV": _dsys_w(m, nm, H["M"])}


def _row_matches(new, old, tol=1e-9):
    return all(abs(float(new[f]) - float(old[f])) <= tol for f in SWEEP_FIELDS)


def run_sweep(modality):
    """Recompute the 80-setting development sweep and compare it, row by
    row, with the sealed runs/sweep/<modality>/sweep_80.csv."""
    out = DIR["runs"] / "sweep" / modality / "sweep_80.csv"
    if out.is_file():
        print(f"  {modality}: resume - regenerated sweep found")
        rows = pd.read_csv(out).to_dict("records")
    else:
        subjects, enroll, probes = partition_data(modality, "development")
        d = len(enroll[subjects[0]])
        sealed_path = RUNS_IN / "sweep" / modality / "sweep_80.csv"
        sealed = ({(r["M"], r["q"], r["o"]): r for r in
                   pd.read_csv(sealed_path).to_dict("records")}
                  if sealed_path.is_file() else {})
        rows = []
        for o in GRID["o"]:
            frozen = load_iom_tensor(modality, o, d)
            for M in GRID["M"]:
                for q in GRID["q"]:
                    H = identity_histograms(modality, subjects, enroll, probes,
                                            M, q, o, None, frozen=frozen)
                    row = sweep_row(modality, H)
                    old = sealed.get((M, q, o))
                    if old is not None and not _row_matches(row, old):
                        H2 = identity_histograms(modality, subjects, enroll,
                                                 probes, M, q, o, None,
                                                 frozen=frozen, variant="slice")
                        row2 = sweep_row(modality, H2)
                        if _row_matches(row2, old):
                            row = row2
                    rows.append(row)
            print(f"    {modality} o={o}: {len(rows)} of "
                  f"{len(GRID['o']) * len(GRID['M']) * len(GRID['q'])} settings")
        out.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out, index=False)
    compare_sweep(modality, rows)
    return rows


def compare_sweep(modality, rows):
    path = RUNS_IN / "sweep" / modality / "sweep_80.csv"
    if not path.is_file():
        print(f"  {modality}: no sealed sweep on Drive to compare against")
        return None
    sealed = {(r["M"], r["q"], r["o"]): r
              for r in pd.read_csv(path).to_dict("records")}
    same = [r for r in rows if (r["M"], r["q"], r["o"]) in sealed
            and _row_matches(r, sealed[(r["M"], r["q"], r["o"])])]
    print(f"  {modality}: {len(same)} of {len(rows)} regenerated settings equal "
          f"the sealed sweep on {', '.join(SWEEP_FIELDS)}")
    for r in rows:
        old = sealed.get((r["M"], r["q"], r["o"]))
        if old is not None and not _row_matches(r, old):
            diffs = {f: (round(float(r[f]), 6), round(float(old[f]), 6))
                     for f in SWEEP_FIELDS
                     if abs(float(r[f]) - float(old[f])) > 1e-9}
            print(f"    differs M={r['M']} q={r['q']} o={r['o']}: {diffs}")
    return len(same) == len(rows)


def floor_of(modality):
    path = DIR["seal"] / f"operating_point_{modality}.json"
    if path.is_file():
        rule = json.loads(path.read_text())["rule"]
        return float(rule["eer_max"]), float(rule["tar_min"])
    raise FileNotFoundError(f"sealed operating point not found: {path}")


def select(modality, rows, floor):
    """The study's rule: lowest Dsys among settings meeting the floor; ties
    by lower EER, then smaller M, q, o."""
    eer_max, tar_min = floor
    ok = [r for r in rows if r["EER"] <= eer_max and r["TAR_DEV"] >= tar_min]
    if not ok:
        raise RuntimeError(f"{modality}: no setting meets the floor {floor}")
    best = min(ok, key=lambda r: (r["Dsys_DEV"], r["EER"], r["M"], r["q"], r["o"]))
    sealed = json.loads(HELDOUT_RESULTS[modality].read_text())
    chosen = (best["M"], best["q"], best["o"])
    expected = (sealed["M"], sealed["q"], sealed["o"])
    tau_ok = int(best["c_tau_DEV"]) == int(sealed["c_tau_carried_from_DEV"])
    print(f"  {modality}: {len(ok)} settings meet the floor; the rule selects "
          f"M={chosen[0]} q={chosen[1]} o={chosen[2]} with tau={best['c_tau_DEV']}"
          f" - {'as sealed' if chosen == expected and tau_ok else '*** NOT the sealed setting'}")
    if chosen != expected or not tau_ok:
        raise RuntimeError(f"{modality}: regenerated selection {chosen} "
                           f"differs from the sealed {expected}")
    return best


# ------------------------------------------------------------- intervals
# Seeds of the study's held-out interval run, as recorded in
# RESULTS_SUMMARY.md; used only if runs/heldout/heldout_confidence.json
# does not record them itself. The external seed is derived by the
# study's own rule.
HELDOUT_SEEDS = {"face": 6353163838588607505, "voice": 4722292304065993655}


def external_seed(modality):
    label = f"{S0}|external_confidence|{modality}".encode()
    return int.from_bytes(hashlib.sha256(label).digest()[:8], "big") >> 1


def _original_interval_file(partition):
    path = (RUNS_IN / "heldout" / "heldout_confidence.json"
            if partition == "evaluation"
            else RUNS_IN / "external" / "voice" / "external_confidence.json")
    return json.loads(path.read_text()) if path.is_file() else None


def _seed_for(modality, partition):
    original = _original_interval_file(partition)
    if original:
        recorded = original.get("modalities", {}).get(modality, {}) \
            .get("bootstrap_seed")
        if recorded is not None:
            return int(recorded)
    return (HELDOUT_SEEDS[modality] if partition == "evaluation"
            else external_seed(modality))


def interval_for(modality, partition, n_bootstrap, confidence):
    if partition == "evaluation":
        sealed = json.loads(HELDOUT_RESULTS[modality].read_text())
        tag = "HOLDOUT"
        subjects, enroll, probes = (face_heldout_data() if modality == "face"
                                    else voice_heldout_data())
    else:
        sealed = json.loads((RUNS_IN / "external" / modality /
                             "external_result.json").read_text())
        tag = "EXT"
        subjects, enroll, probes = vctk_external_data()
    M, q, o = sealed["M"], sealed["q"], sealed["o"]
    tau = int(sealed["c_tau_carried_from_DEV"])
    H = identity_histograms(modality, subjects, enroll, probes, M, q, o, tau)

    point = _metrics(H, np.ones(H["n"]))
    sealed_point = {"EER": sealed[f"EER_{tag}"],
                    "TAR": sealed[f"TAR_{tag}_at_dev_threshold"],
                    "FMR": sealed[f"FMR_{tag}_at_dev_threshold"],
                    "Dsys": sealed[f"Dsys_{tag}"]}
    drift = {k: (point[k], v) for k, v in sealed_point.items()
             if abs(point[k] - v) > 1e-6}
    if drift:
        raise RuntimeError(f"{modality}/{partition}: rebuilt scores do not "
                           f"reproduce the sealed result: {drift}")

    seed = _seed_for(modality, partition)
    rng = np.random.default_rng(seed)
    keys = ("EER", "TAR", "FMR", "Dsys")
    draws = {k: np.empty(n_bootstrap) for k in keys}
    for b in range(n_bootstrap):
        w = rng.multinomial(H["n"], np.full(H["n"], 1.0 / H["n"])).astype(float)
        mb = _metrics(H, w)
        for k in keys:
            draws[k][b] = mb[k]
    alpha = (1.0 - confidence) / 2.0
    out = {}
    for k in keys:
        d = draws[k][np.isfinite(draws[k])]
        out[k] = {"estimate": float(point[k]),
                  "lower": float(np.percentile(d, 100 * alpha)),
                  "upper": float(np.percentile(d, 100 * (1 - alpha)))}
    print(f"  {modality}/{partition}: {H['n']} identities, seed {seed}; "
          f"point estimates reproduce the sealed result")
    return {"metrics": out, "bootstrap_seed": seed, "n_subjects": H["n"]}


def run_intervals(n_bootstrap=2000, confidence=0.95):
    path = DIR["runs"] / "intervals" / "confidence_intervals.json"
    if path.is_file():
        print("Resume: regenerated intervals found; returning them unchanged.")
        return json.loads(path.read_text())
    result = {"schema": 1, "method_id": "identity_cluster_percentile_v1",
              "n_bootstrap": n_bootstrap, "confidence": confidence,
              "partitions": {}}
    parts = [("voice", "evaluation"), ("face", "evaluation")]
    if VCTK_EMB.is_file() and (RUNS_IN / "external" / "voice" /
                               "external_result.json").is_file():
        parts.append(("voice", "external"))
    else:
        print("  voice/external: VCTK embeddings or sealed external result "
              "not found; skipped")
    for modality, partition in parts:
        result["partitions"][f"{modality}/{partition}"] = interval_for(
            modality, partition, n_bootstrap, confidence)
    atomic_json(path, result)
    compare_intervals(result)
    return result


def compare_intervals(result):
    names = {"EER": "EER_{}", "TAR": "TAR_{}_at_dev_threshold",
             "FMR": "FMR_{}_at_dev_threshold", "Dsys": "Dsys_{}"}
    for part, rec in result["partitions"].items():
        modality, partition = part.split("/")
        original = _original_interval_file(partition)
        if not original:
            print(f"  {part}: no original interval file on Drive to compare")
            continue
        tag = "HOLDOUT" if partition == "evaluation" else "EXT"
        old = original["modalities"][modality]["metrics"]
        worst = max(abs(rec["metrics"][k][side] - old[names[k].format(tag)][side])
                    for k in names for side in ("estimate", "lower", "upper"))
        print(f"  {part}: largest difference from the original intervals "
              f"{worst:.2e}" + ("  (identical)" if worst <= 1e-12 else ""))


def intervals_for_plots(result):
    """Percent for EER, TAR, FMR; fraction for Dsys; as (point, low, high)."""
    out = {}
    for part, rec in result["partitions"].items():
        m = rec["metrics"]
        out[part] = {k: tuple(m[k][s] * (1 if k == "Dsys" else 100)
                              for s in ("estimate", "lower", "upper"))
                     for k in ("EER", "TAR", "FMR", "Dsys")}
    return out


# -------------------------------------------------------------- baseline
def clopper_pearson_upper(k, n, confidence=0.95):
    from scipy.stats import beta
    return float(beta.ppf(confidence, k + 1, n - k))


def baseline_from_scores(scores):
    """Protected against unprotected EER, from the score histograms.

    Where the unprotected system makes fewer than one genuine error, its
    EER is not resolvable and only a one-sided 95% upper bound is given.
    """
    rows = []
    for modality in ("voice", "face"):
        entry = scores["modalities"][modality]
        for partition in ("development", "evaluation", "external"):
            h = entry["partitions"].get(partition)
            if h is None:
                continue
            protected = eer_check(h["genuine"], h["impostor"], entry["M"])
            raw = h["unprotected"]["EER"]
            n = h["n_genuine"]
            k = int(math.floor(raw * n + 1e-9))
            rows.append({
                "modality": modality, "partition": partition,
                "n_genuine": n,
                "protected_eer": protected * 100,
                "unprotected_eer": raw * 100,
                "cost_pp": (protected - raw) * 100,
                "one_genuine_error_pct": 100.0 / n,
                "baseline_resolved": bool(raw >= 1.0 / n),
                "unprotected_upper_bound_95": clopper_pearson_upper(k, n) * 100,
            })
    return rows


def add_external_scores(scores):
    """The study's score dump adds VCTK only through a helper file kept on
    Drive. If it did not, build the external partition here, the same way."""
    voice = scores["modalities"]["voice"]
    if "external" in voice["partitions"] or not VCTK_EMB.is_file():
        return scores
    subjects, enroll, probes = vctk_external_data()
    M, q, o = voice["M"], voice["q"], voice["o"]
    d = len(enroll[subjects[0]])
    k = 1 + math.ceil((d - G) / (G - o))
    recognition = load_iom_tensor("voice", o, d)[:M, :q].to(DEVICE, torch.float32)
    pair = [unlink_tensor("voice", i, M, q, k).to(DEVICE) for i in (1, 2)]
    h = histograms_for("voice", subjects, enroll, probes, M, q, o,
                       selected_poly_key("voice"), recognition, pair)
    h["dlink_curve"], h["dlink_global"] = unlinkability_curve(h["mated"],
                                                              h["nonmated"])
    h["unprotected"] = cosine_histograms(subjects, enroll, probes)
    h["unprotected"]["EER"] = eer_cosine(h["unprotected"]["genuine"],
                                         h["unprotected"]["impostor"])
    voice["partitions"]["external"] = h
    atomic_json(DIR["runs"] / "scores" / "score_histograms.json", scores)
    print(f"  external: {h['n_subjects']} speakers added to the score dump")
    return scores


# ------------------------------------------------------------ comparison
def _leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, f"{prefix}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _leaves(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def compare_with_original(name, regenerated, relative):
    """Every number in a regenerated result against the study's original."""
    path = RUNS_IN / relative
    if not path.is_file():
        print(f"  {name:<22} no original on Drive to compare against")
        return None
    old = dict(_leaves(json.loads(path.read_text())))
    new = dict(_leaves(regenerated))
    numeric = [k for k in old if isinstance(old[k], (int, float))
               and not isinstance(old[k], bool) and k in new]
    worst, where = 0.0, None
    for k in numeric:
        diff = abs(float(new[k]) - float(old[k]))
        if diff > worst:
            worst, where = diff, k
    missing = [k for k in old if k not in new]
    verdict = "identical" if worst == 0.0 and not missing else (
        f"largest difference {worst:.2e} at {where}")
    print(f"  {name:<22} {len(numeric):6d} numbers compared: {verdict}"
          + (f"; {len(missing)} fields absent" if missing else ""))
    return worst


# ---------------------------------------------------------------- figures
def draw_figures(out, sweeps, selected, floors, intervals, baseline,
                 ablation, inversion, revocation, score_json):
    data = {"sweep": sweeps, "floor": floors, "selected": selected,
            "intervals": intervals_for_plots(intervals), "baseline": baseline,
            "ablation": ablation["modalities"], "revocation": revocation,
            "inversion": inversion["modalities"]}
    stems = results_plots.draw_all(data, out)

    # Figures A-D: the study's own figure code, given the intervals this
    # notebook computed instead of the ones typed into it.
    figures_only.CARRIED_CI = {
        tuple(part.split("/")): data["intervals"][part]["EER"]
        for part in data["intervals"]}
    figures_only.make_figures(score_json, out)
    return stems + ["figA_det_preservation", "figB_score_separability",
                    "figC_unlinkability", "figD_revocability"]


print("All-figures runtime ready.")

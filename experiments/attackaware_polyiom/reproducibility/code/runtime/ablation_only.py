"""Self-contained ablation runtime for AttackAware PolyIoM v1.1.4.

Loaded by AttackAware_PolyIoM_v1_1_4_ABLATION.ipynb after its preflight cell
has defined PROJECT, DIR, S0, G, DEVICE, the embedding paths, HELDOUT_RESULTS
and ABLATION_OUTPUT.

Rebuilds the frozen score histograms from the stored embeddings and keys, so
it depends on no other notebook. Writes one file, runs/ablation/
ablation_result.json, and no seal.
"""

def sha256_file(path, chunk=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str))
    os.replace(temporary, path)


def H(*fields):
    payload = "|".join(str(field) for field in fields).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


def seed_unlink(modality, key_index):
    return H(S0, "UNLINK", modality, key_index)


def l2_np(vector, eps=1e-12):
    vector = np.asarray(vector, dtype=np.float32)
    norm = np.linalg.norm(vector)
    if norm <= eps:
        raise RuntimeError("Zero-norm embedding")
    return (vector / norm).astype(np.float32)


def selected_poly_key(modality):
    path = DIR["runs"] / "key_search" / modality / "selected_key.json"
    obj = json.loads(path.read_text())
    return np.asarray(obj["C"], np.float32), np.asarray(obj["E"], np.int64)


def face_heldout_data():
    trials = pd.read_csv(LFW_FACE_TRIALS, sep="\t")
    stored = np.load(LFW_EMB, allow_pickle=True)
    embeddings = stored["embedding"].astype(np.float32)
    held = trials[trials.partition == "evaluation"]
    subjects, enroll, probes = [], {}, {}
    for uid, group in held.groupby("subject_id"):
        erow = group[group.role == "enroll"]
        prows = group[group.role == "probe"]
        if len(erow) != 1 or len(prows) < 1:
            continue
        uid = str(uid)
        subjects.append(uid)
        enroll[uid] = embeddings[int(erow.iloc[0].embedding_index)]
        probes[uid] = [
            embeddings[int(row.embedding_index)] for row in prows.itertuples()
        ]
    return sorted(subjects), enroll, probes


def voice_heldout_data():
    manifest = pd.read_csv(LIBRI_MANIFEST, sep="\t", dtype={"speaker_id": str})
    stored = np.load(LIBRI_EMB, allow_pickle=True)
    embeddings = stored["embedding"].astype(np.float32)
    table = pd.DataFrame({
        "speaker_id": stored["speaker_id"].astype(str),
        "rank": stored["rank"].astype(int),
        "embedding_index": np.arange(len(embeddings), dtype=np.int64),
    })
    held = manifest.merge(
        table[["speaker_id", "rank", "embedding_index"]],
        on=["speaker_id", "rank"], how="inner",
    )
    held = held[held.partition == "evaluation"]
    subjects, enroll, probes = [], {}, {}
    for uid, group in held.groupby("speaker_id"):
        group = group.sort_values("rank")
        if len(group) != 15:
            continue
        uid = str(uid)
        members = np.stack([
            embeddings[int(row.embedding_index)]
            for row in group[group["rank"] < 5].itertuples()
        ])
        subjects.append(uid)
        enroll[uid] = l2_np(members.mean(axis=0))
        probes[uid] = [
            embeddings[int(row.embedding_index)]
            for row in group[group["rank"] >= 5].itertuples()
        ]
    return sorted(subjects), enroll, probes


def poly_indices(d, overlap, device):
    stride = G - overlap
    k = 1 + math.ceil((d - G) / stride)
    idx = torch.arange(k, device=device)[:, None] * stride + torch.arange(G, device=device)
    mask = idx < d
    return idx.clamp(max=d - 1).long(), mask


def poly_transform(vectors, coefficients, exponents, overlap):
    idx, mask = poly_indices(vectors.shape[-1], overlap, vectors.device)
    values = vectors[..., idx] * mask.to(vectors.dtype)
    coefficients = torch.as_tensor(coefficients, device=vectors.device, dtype=vectors.dtype)
    exponents = torch.as_tensor(exponents, device=vectors.device, dtype=torch.int64)
    return (torch.pow(values, exponents) * coefficients).sum(dim=-1)


def load_iom_tensor(modality, overlap, d):
    k = 1 + math.ceil((d - G) / (G - overlap))
    path = DIR["runs"] / "iom_tensors" / f"{modality}_o{overlap}_k{k}.pt"
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


print("Frozen-pipeline primitives ready.")


ARMS = ("polyiom", "iom_only", "randproj_iom")
ARM_NOTE = {
    "polyiom": "z -> P_K*(z; o*) -> IoM-GRP   (the proposed method)",
    "iom_only": "z ----------------> IoM-GRP   (the practical baseline)",
    "randproj_iom": "z -> A z ----------> IoM-GRP   (isolates the polynomial)",
}


def abl_seed(modality, label):
    """Deterministic seed, distinct from every seed stream in the study."""
    return H(S0, "ABLATION", modality, label)


def abl_randn(shape, modality, label):
    generator = torch.Generator(device="cpu")
    generator.manual_seed(abl_seed(modality, label))
    return torch.randn(shape, generator=generator, dtype=torch.float32)


def hash_arm(vectors, arm, key, overlap, tensor, M, q, A, batch_size=64):
    """One arm's protected codes. Only the pre-projection step differs."""
    coefficients, exponents = key
    tensor = tensor[:M, :q].to(DEVICE, torch.float32)
    outputs = []
    for start in range(0, len(vectors), batch_size):
        batch = torch.as_tensor(
            np.stack(vectors[start:start + batch_size]),
            dtype=torch.float32, device=DEVICE,
        )
        if arm == "polyiom":
            projected = poly_transform(batch, coefficients, exponents, overlap)
        elif arm == "randproj_iom":
            projected = batch @ A
        elif arm == "iom_only":
            projected = batch
        else:
            raise ValueError(arm)
        scores = torch.einsum("bk,mqk->bmq", projected, tensor)
        outputs.append(torch.argmax(scores, dim=-1).to(torch.int16).cpu().numpy())
    return np.concatenate(outputs, axis=0)


def check_gaussian(tensor, label, tolerance=0.05):
    """The generated tensors are standard normal. If the frozen recognition
    tensor is not, the arms are not drawn from the same family and the
    comparison is confounded, so say so loudly rather than quietly."""
    mean, std = float(tensor.mean()), float(tensor.std())
    ok = abs(mean) <= tolerance and abs(std - 1.0) <= tolerance
    print(f"    {label}: mean={mean:+.4f} std={std:.4f} "
          f"{'~N(0,1)' if ok else '*** NOT ~N(0,1) - comparison confounded'}")
    return ok


def build_arm_histograms(modality):
    """Per-identity histograms for all three arms, sharing identity order."""
    sealed = json.loads(HELDOUT_RESULTS[modality].read_text())
    M, q, overlap = sealed["M"], sealed["q"], sealed["o"]
    threshold = int(sealed["c_tau_carried_from_DEV"])
    subjects, enroll, probes = (
        face_heldout_data() if modality == "face" else voice_heldout_data()
    )
    if len(subjects) != sealed["n_subjects"]:
        raise RuntimeError(
            f"{modality}: reconstructed {len(subjects)} identities; "
            f"sealed result has {sealed['n_subjects']}"
        )

    key = selected_poly_key(modality)
    n = len(subjects)
    d = len(enroll[subjects[0]])
    k = 1 + math.ceil((d - G) / (G - overlap))
    print(f"  {modality}: n={n}  d={d}  k={k}  M={M} q={q} o={overlap}")

    frozen = load_iom_tensor(modality, overlap, d)
    print("  recognition tensors:")
    gaussian_ok = check_gaussian(frozen[:M, :q], "polyiom (frozen, from disk)")
    recognition = {
        "polyiom": frozen,
        "iom_only": abl_randn((M, q, d), modality, "match|iom_only"),
        "randproj_iom": abl_randn((M, q, k), modality, "match|randproj"),
    }
    A = abl_randn((d, k), modality, "projmap") / math.sqrt(d)

    unlink = {"polyiom": [], "iom_only": [], "randproj_iom": []}
    for key_index in (1, 2):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed_unlink(modality, key_index))
        unlink["polyiom"].append(
            torch.randn((M, q, k), generator=generator, dtype=torch.float32)
        )
        unlink["iom_only"].append(
            abl_randn((M, q, d), modality, f"unlink|raw|{key_index}")
        )
        unlink["randproj_iom"].append(
            abl_randn((M, q, k), modality, f"unlink|prj|{key_index}")
        )

    enrolment_vectors = [enroll[uid] for uid in subjects]
    probe_vectors, probe_owners = [], []
    for owner, uid in enumerate(subjects):
        probe_vectors.extend(probes[uid])
        probe_owners.extend([owner] * len(probes[uid]))

    bundles = {}
    for arm in ARMS:
        enrolment_hashes = hash_arm(
            enrolment_vectors, arm, key, overlap, recognition[arm], M, q, A)
        probe_hashes = hash_arm(
            probe_vectors, arm, key, overlap, recognition[arm], M, q, A)
        collision = (probe_hashes[:, None, :]
                     == enrolment_hashes[None, :, :]).sum(axis=-1)

        genuine_by_subject = np.zeros((n, M + 1), dtype=np.float64)
        impostor_by_pair = np.zeros((n, n, M + 1), dtype=np.float64)
        for probe_index, owner in enumerate(probe_owners):
            genuine_by_subject[owner, collision[probe_index, owner]] += 1
            for claimant in range(n):
                if claimant != owner:
                    impostor_by_pair[owner, claimant,
                                     collision[probe_index, claimant]] += 1

        first = hash_arm(enrolment_vectors, arm, key, overlap,
                         unlink[arm][0], M, q, A)
        second = hash_arm(enrolment_vectors, arm, key, overlap,
                          unlink[arm][1], M, q, A)
        unlink_collision = (first[:, None, :] == second[None, :, :]).sum(axis=-1)
        mated_by_subject = np.zeros((n, M + 1), dtype=np.float64)
        nonmated_by_pair = np.zeros((n, n, M + 1), dtype=np.float64)
        for left in range(n):
            mated_by_subject[left, unlink_collision[left, left]] = 1
            for right in range(n):
                if left != right:
                    nonmated_by_pair[left, right,
                                     unlink_collision[left, right]] = 1

        bundles[arm] = {
            "genuine_by_subject": genuine_by_subject,
            "impostor_by_pair": impostor_by_pair,
            "mated_by_subject": mated_by_subject,
            "nonmated_by_pair": nonmated_by_pair,
        }
        print(f"    {arm:<13} built   {ARM_NOTE[arm]}")

    return {
        "modality": modality, "sealed": sealed, "subjects": subjects,
        "M": M, "q": q, "o": overlap, "d": d, "k": k,
        "threshold": threshold, "arms": bundles,
        "frozen_tensor_is_gaussian": bool(gaussian_ok),
    }


print("Arm construction ready.")


def eer_from_histograms(genuine, impostor):
    genuine_total, impostor_total = genuine.sum(), impostor.sum()
    if genuine_total <= 0 or impostor_total <= 0:
        raise RuntimeError("EER requires non-empty distributions")
    far = np.r_[np.cumsum(impostor[::-1])[::-1], 0.0] / impostor_total
    frr = np.r_[0.0, np.cumsum(genuine)] / genuine_total
    difference = far - frr
    c_eer = int(np.flatnonzero(np.abs(difference) == np.abs(difference).min())[0])
    exact = np.flatnonzero(difference == 0.0)
    if len(exact):
        return float(far[exact[0]]), c_eer
    crossings = np.flatnonzero((difference[:-1] > 0.0) & (difference[1:] < 0.0))
    if not len(crossings):
        raise AssertionError("EER crossing not found")
    index = int(crossings[0])
    weight = difference[index] / (difference[index] - difference[index + 1])
    return float(far[index] + weight * (far[index + 1] - far[index])), c_eer


def dsys_from_histograms(mated, nonmated):
    if mated.sum() <= 0 or nonmated.sum() <= 0:
        raise RuntimeError("Dsys requires non-empty distributions")
    pm, pn = mated / mated.sum(), nonmated / nonmated.sum()
    local = np.zeros_like(pm)
    for score in range(len(pm)):
        if pm[score] == 0:
            local[score] = 0
        elif pn[score] == 0:
            local[score] = 1
        else:
            ratio = pm[score] / pn[score]
            local[score] = 0 if ratio <= 1 else 2 * ratio / (1 + ratio) - 1
    return float(np.sum(pm * local))


def collapse(bundle, identity_weights, n):
    pair_weights = np.outer(identity_weights, identity_weights)
    np.fill_diagonal(pair_weights, 0.0)
    flat = pair_weights.reshape(-1)
    return (
        identity_weights @ bundle["genuine_by_subject"],
        flat @ bundle["impostor_by_pair"].reshape(n * n, -1),
        identity_weights @ bundle["mated_by_subject"],
        flat @ bundle["nonmated_by_pair"].reshape(n * n, -1),
    )


def arm_metrics(bundle, identity_weights, n):
    genuine, impostor, mated, nonmated = collapse(bundle, identity_weights, n)
    eer, c_eer = eer_from_histograms(genuine, impostor)
    return {"EER": eer, "c_EER": c_eer,
            "Dsys": dsys_from_histograms(mated, nonmated)}, genuine, impostor


def tar_at_matched_fmr(genuine, impostor, target):
    """Lowest threshold whose FMR still meets the target; descriptive only."""
    total = impostor.sum()
    best = None
    for c in range(len(impostor) - 1, -1, -1):
        if float(impostor[c:].sum() / total) <= target + 1e-12:
            best = c
        else:
            break
    if best is None:
        return float("nan"), -1
    return float(genuine[best:].sum() / genuine.sum()), best


def verify_against_seal(record):
    """The polyiom arm rebuilds the sealed pipeline exactly, so its EER must
    reproduce the sealed held-out figure. Anything else means this notebook
    has drifted from the study and its numbers must not be reported."""
    sealed = record["sealed"]
    reproduced = record["point"]["polyiom"]["EER"]
    if not np.isclose(reproduced, sealed["EER_HOLDOUT"], rtol=0.0, atol=1e-12):
        raise RuntimeError(
            f"{record['modality']}: the polyiom arm reproduces "
            f"EER={reproduced}, but the sealed held-out result is "
            f"{sealed['EER_HOLDOUT']}. Refusing to report - the arm is not "
            f"the study's pipeline."
        )
    print(f"  self-check: polyiom EER {reproduced * 100:.4f}% reproduces the "
          f"sealed held-out result")


def paired_bootstrap(record, n_bootstrap, confidence, seed):
    """One identity weight vector per replicate, applied to all three arms,
    so an interval on a DIFFERENCE accounts for the arms sharing identities.
    An unpaired interval would be too wide."""
    n = len(record["subjects"])
    rng = np.random.default_rng(seed)
    parts, remaining = [], n_bootstrap
    while remaining:
        candidates = rng.multinomial(n, np.full(n, 1 / n), size=remaining)
        candidates = candidates[(candidates > 0).sum(axis=1) >= 2]
        parts.append(candidates[:remaining])
        remaining -= len(parts[-1])
    weights = np.concatenate(parts, axis=0).astype(np.float64)

    per_arm = {arm: {"EER": [], "Dsys": []} for arm in ARMS}
    contrasts = {arm: {"delta_EER": [], "delta_Dsys": []}
                 for arm in ARMS if arm != "polyiom"}
    for replicate in range(n_bootstrap):
        w = weights[replicate]
        values = {}
        for arm in ARMS:
            measured, _, _ = arm_metrics(record["arms"][arm], w, n)
            values[arm] = measured
            per_arm[arm]["EER"].append(measured["EER"])
            per_arm[arm]["Dsys"].append(measured["Dsys"])
        for arm in contrasts:
            contrasts[arm]["delta_EER"].append(
                values[arm]["EER"] - values["polyiom"]["EER"])
            contrasts[arm]["delta_Dsys"].append(
                values[arm]["Dsys"] - values["polyiom"]["Dsys"])
        if (replicate + 1) % 500 == 0:
            print(f"    {record['modality']}: {replicate + 1}/{n_bootstrap}")

    alpha = 1.0 - confidence

    def interval(values):
        lower, upper = np.quantile(values, [alpha / 2, 1 - alpha / 2])
        return [float(lower), float(upper)]

    return per_arm, contrasts, interval


def run_ablation(n_bootstrap=2000, confidence=0.95):
    if ABLATION_OUTPUT.is_file():
        stored = json.loads(ABLATION_OUTPUT.read_text())
        print("Resume: stored ablation result found; returning it unchanged.")
        return stored

    source_hashes = {m: sha256_file(p) for m, p in HELDOUT_RESULTS.items()}
    result = {
        "schema": 1,
        "analysis": "hardening_ablation",
        "method_id": "identity_cluster_percentile_v1_paired",
        "n_bootstrap": int(n_bootstrap),
        "confidence": float(confidence),
        "master_seed": S0,
        "changes_any_seal": False,
        "threshold_policy": "none fitted; EER and Dsys are threshold-free",
        "arms": {arm: ARM_NOTE[arm] for arm in ARMS},
        "source_heldout_sha256": source_hashes,
        "modalities": {},
    }

    for modality in ("voice", "face"):
        print(f"\n{modality.upper()}")
        record = build_arm_histograms(modality)
        n = len(record["subjects"])
        flat = np.ones(n, dtype=np.float64)

        record["point"] = {}
        matched = {}
        for arm in ARMS:
            measured, genuine, impostor = arm_metrics(record["arms"][arm], flat, n)
            record["point"][arm] = measured
            matched[arm] = (genuine, impostor)
        verify_against_seal(record)

        reference_fmr = float(
            matched["polyiom"][1][record["threshold"]:].sum()
            / matched["polyiom"][1].sum()
        )
        for arm in ARMS:
            tar, c = tar_at_matched_fmr(*matched[arm], reference_fmr)
            record["point"][arm]["TAR_at_matched_FMR_descriptive"] = tar
            record["point"][arm]["c_matched"] = int(c)

        print(f"  paired bootstrap over {n} identities")
        per_arm, contrasts, interval = paired_bootstrap(
            record, n_bootstrap, confidence,
            seed=abl_seed(modality, "bootstrap"),
        )

        result["modalities"][modality] = {
            "n_subjects": n, "M": record["M"], "q": record["q"],
            "o": record["o"], "d": record["d"], "k": record["k"],
            "c_tau_carried_from_DEV": record["threshold"],
            "frozen_tensor_is_gaussian": record["frozen_tensor_is_gaussian"],
            "polyiom_reproduces_sealed_heldout": True,
            "reference_FMR_for_matched_TAR": reference_fmr,
            "arms": {arm: {
                "EER": record["point"][arm]["EER"],
                "EER_CI": interval(per_arm[arm]["EER"]),
                "Dsys": record["point"][arm]["Dsys"],
                "Dsys_CI": interval(per_arm[arm]["Dsys"]),
                "TAR_at_matched_FMR_descriptive":
                    record["point"][arm]["TAR_at_matched_FMR_descriptive"],
            } for arm in ARMS},
            "contrasts_vs_polyiom": {arm: {
                "delta_EER": (record["point"][arm]["EER"]
                              - record["point"]["polyiom"]["EER"]),
                "delta_EER_CI": interval(contrasts[arm]["delta_EER"]),
                "delta_Dsys": (record["point"][arm]["Dsys"]
                               - record["point"]["polyiom"]["Dsys"]),
                "delta_Dsys_CI": interval(contrasts[arm]["delta_Dsys"]),
            } for arm in contrasts},
        }

    if {m: sha256_file(p) for m, p in HELDOUT_RESULTS.items()} != source_hashes:
        raise RuntimeError("A sealed held-out result changed during the ablation")
    atomic_json(ABLATION_OUTPUT, result)
    print("\nWrote", ABLATION_OUTPUT)
    return result


def ablation_table(result):
    rows = []
    for modality, data in result["modalities"].items():
        for arm, values in data["arms"].items():
            rows.append({
                "modality": modality, "arm": arm,
                "EER": values["EER"],
                "EER_lo": values["EER_CI"][0], "EER_hi": values["EER_CI"][1],
                "Dsys": values["Dsys"],
                "Dsys_lo": values["Dsys_CI"][0], "Dsys_hi": values["Dsys_CI"][1],
                "TAR_matched_FMR": values["TAR_at_matched_FMR_descriptive"],
            })
    return pd.DataFrame(rows)


def contrast_report(result):
    for modality, data in result["modalities"].items():
        print(f"\n{modality.upper()}  d={data['d']} -> k={data['k']}  "
              f"n={data['n_subjects']} identities")
        print("  arm minus proposed; an interval excluding 0 is firm")
        for arm, c in data["contrasts_vs_polyiom"].items():
            for name, scale, unit in (("EER", 100, " %"), ("Dsys", 1, "")):
                value = c[f"delta_{name}"]
                lower, upper = c[f"delta_{name}_CI"]
                firm = "FIRM" if (lower > 0 or upper < 0) else "not distinguishable"
                print(f"    {arm:<14} d{name:<5}{value * scale:+8.3f}{unit}"
                      f"  [{lower * scale:+7.3f},{upper * scale:+7.3f}]  {firm}")
    print("\n  A POSITIVE delta means that arm is WORSE than the proposed")
    print("  method (higher EER, higher Dsys). randproj_iom is the arm that")
    print("  isolates the polynomial: it matches the proposed method's")
    print("  projection dimension k, so a null contrast there means the gain")
    print("  came from the dimension change and not from P_K*.")


print("Metrics and paired bootstrap ready.")

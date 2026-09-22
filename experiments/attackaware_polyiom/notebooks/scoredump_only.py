"""Score-histogram dump for AttackAware PolyIoM v1.1.4.

Loaded after ablation_only.py, which supplies the frozen-pipeline
primitives. Read-only: writes one file and no seal.

Why histograms rather than raw score vectors
--------------------------------------------
A collision score is an integer in 0..M. A count per score value is
therefore a LOSSLESS record of the score distribution, and every results
figure a biometric paper needs can be derived from it exactly:

  * FMR and FNMR at every threshold, hence the full DET curve
  * EER, and the threshold at which it occurs
  * genuine and impostor distributions, with tau* marked
  * mated and non-mated distributions, which is what D_sys summarises

The file is a few kilobytes rather than a few megabytes, and nothing is
approximated. The evaluation already builds these histograms internally
and discards them; this cell keeps them.

Covers two systems, because the first criterion a cancelable-biometric
paper has to address is performance PRESERVATION, which is reported as the
protected system against the UNPROTECTED one:

  protected     the sealed pipeline, integer collision scores in 0..M
  unprotected   plain cosine similarity between the same embeddings

Cosine is continuous, so the unprotected side is binned finely over
[-1, 1] and the bin edges are stored with it. At 2000 bins the resolution
is 0.001, which is far finer than any DET curve needs.

Also stores the LOCAL unlinkability curve D_link(s) alongside the global
value. The global value is what the evaluation already reports; the local
curve is the part that is plottable, and it is the standard unlinkability
figure in this literature.

Note that the mated distribution serves two figures at once. Under the
unlinkability framework it is "same subject, two different keys"; under
revocability it is the pseudo-impostor distribution. They are the same
measurement, and a paper should not present them as independent evidence.

Partitions: development and evaluation for both modalities, plus external
VCTK for voice when its embeddings are present.
"""

COS_BINS = 2000

SCORE_OUTPUT = None          # set in run_score_dump


def partition_data(modality, partition):
    """Enrolment and probe embeddings for one partition of one modality.

    Same construction as the held-out loaders in ablation_only.py, with the
    partition as a parameter so development can be read the same way.
    """
    if modality == "face":
        trials = pd.read_csv(LFW_FACE_TRIALS, sep="\t")
        stored = np.load(LFW_EMB, allow_pickle=True)
        embeddings = stored["embedding"].astype(np.float32)
        rows = trials[trials.partition == partition]
        subjects, enroll, probes = [], {}, {}
        for uid, group in rows.groupby("subject_id"):
            erow = group[group.role == "enroll"]
            prows = group[group.role == "probe"]
            if len(erow) != 1 or len(prows) < 1:
                continue
            uid = str(uid)
            subjects.append(uid)
            enroll[uid] = embeddings[int(erow.iloc[0].embedding_index)]
            probes[uid] = [embeddings[int(r.embedding_index)]
                           for r in prows.itertuples()]
        return sorted(subjects), enroll, probes

    manifest = pd.read_csv(LIBRI_MANIFEST, sep="\t", dtype={"speaker_id": str})
    stored = np.load(LIBRI_EMB, allow_pickle=True)
    embeddings = stored["embedding"].astype(np.float32)
    table = pd.DataFrame({
        "speaker_id": stored["speaker_id"].astype(str),
        "rank": stored["rank"].astype(int),
        "embedding_index": np.arange(len(embeddings), dtype=np.int64),
    })
    rows = manifest.merge(table, on=["speaker_id", "rank"], how="inner")
    rows = rows[rows.partition == partition]
    subjects, enroll, probes = [], {}, {}
    for uid, group in rows.groupby("speaker_id"):
        group = group.sort_values("rank")
        if len(group) != 15:
            continue
        uid = str(uid)
        members = np.stack([embeddings[int(r.embedding_index)]
                            for r in group[group["rank"] < 5].itertuples()])
        subjects.append(uid)
        enroll[uid] = l2_np(members.mean(axis=0))
        probes[uid] = [embeddings[int(r.embedding_index)]
                       for r in group[group["rank"] >= 5].itertuples()]
    return sorted(subjects), enroll, probes


def histograms_for(modality, subjects, enroll, probes, M, q, overlap, key,
                   recognition, unlink_pair):
    """Flat genuine / impostor / mated / non-mated histograms over 0..M."""
    enrolment = [enroll[uid] for uid in subjects]
    enrolled = hash_arm(enrolment, "polyiom", key, overlap, recognition,
                        M, q, None)
    probe_vectors, owners = [], []
    for index, uid in enumerate(subjects):
        probe_vectors.extend(probes[uid])
        owners.extend([index] * len(probes[uid]))
    hashed = hash_arm(probe_vectors, "polyiom", key, overlap, recognition,
                      M, q, None)
    collision = (hashed[:, None, :] == enrolled[None, :, :]).sum(axis=-1)

    genuine = np.zeros(M + 1, dtype=np.int64)
    impostor = np.zeros(M + 1, dtype=np.int64)
    for row, owner in enumerate(owners):
        for claimant in range(len(subjects)):
            c = int(collision[row, claimant])
            if claimant == owner:
                genuine[c] += 1
            else:
                impostor[c] += 1

    first = hash_arm(enrolment, "polyiom", key, overlap, unlink_pair[0],
                     M, q, None)
    second = hash_arm(enrolment, "polyiom", key, overlap, unlink_pair[1],
                      M, q, None)
    cross = (first[:, None, :] == second[None, :, :]).sum(axis=-1)
    mated = np.zeros(M + 1, dtype=np.int64)
    nonmated = np.zeros(M + 1, dtype=np.int64)
    for a in range(len(subjects)):
        mated[int(cross[a, a])] += 1
        for b in range(len(subjects)):
            if a != b:
                nonmated[int(cross[a, b])] += 1

    return {"genuine": genuine.tolist(), "impostor": impostor.tolist(),
            "mated": mated.tolist(), "nonmated": nonmated.tolist(),
            "n_subjects": len(subjects),
            "n_genuine": int(genuine.sum()),
            "n_impostor": int(impostor.sum())}


def cosine_histograms(subjects, enroll, probes, nbins=COS_BINS):
    """Unprotected baseline: plain cosine between the same embeddings.

    This is the reference the protected system has to be compared against.
    Binned over [-1, 1] rather than stored raw: 2000 bins is 0.001
    resolution and a few kilobytes instead of megabytes.
    """
    def unit(a):
        a = np.asarray(a, dtype=np.float64)
        return a / max(np.linalg.norm(a), 1e-12)

    E = np.stack([unit(enroll[uid]) for uid in subjects])
    rows, owners = [], []
    for index, uid in enumerate(subjects):
        for v in probes[uid]:
            rows.append(unit(v))
            owners.append(index)
    P = np.stack(rows)
    scores = P @ E.T                                  # (probes, subjects)

    edges = np.linspace(-1.0, 1.0, nbins + 1)
    own = np.asarray(owners)
    mask = np.zeros_like(scores, dtype=bool)
    mask[np.arange(len(own)), own] = True
    gen, _ = np.histogram(scores[mask], bins=edges)
    imp, _ = np.histogram(scores[~mask], bins=edges)
    return {"genuine": gen.tolist(), "impostor": imp.tolist(),
            "bin_edges": [float(edges[0]), float(edges[-1])],
            "n_bins": int(nbins),
            "n_genuine": int(gen.sum()), "n_impostor": int(imp.sum())}


def unlinkability_curve(mated, nonmated):
    """Local D_link(s) and the global value, from the same histograms.

    The global value is what the evaluation already reports. The local
    curve is what a figure needs.
    """
    m = np.asarray(mated, float)
    n = np.asarray(nonmated, float)
    if m.sum() <= 0 or n.sum() <= 0:
        return [], float("nan")
    pm, pn = m / m.sum(), n / n.sum()
    local = np.zeros_like(pm)
    for s_ in range(len(pm)):
        if pm[s_] == 0:
            local[s_] = 0.0
        elif pn[s_] == 0:
            local[s_] = 1.0
        else:
            ratio = pm[s_] / pn[s_]
            local[s_] = 0.0 if ratio <= 1 else 2 * ratio / (1 + ratio) - 1
    return local.tolist(), float(np.sum(pm * local))


def eer_cosine(hist_gen, hist_imp):
    """EER from a binned continuous score, for the unprotected baseline.

    The exact-zero branch is not optional here. When the two distributions
    are well separated there is a run of thresholds at which FAR and FRR
    are both zero, so FAR - FRR never changes sign between adjacent bins
    and a crossing-only search returns nothing. The unprotected baseline
    is the case most likely to be well separated, which is exactly the
    number this function exists to produce.
    """
    g = np.asarray(hist_gen, float)
    i = np.asarray(hist_imp, float)
    if g.sum() <= 0 or i.sum() <= 0:
        return float("nan")
    far = np.r_[np.cumsum(i[::-1])[::-1], 0.0] / i.sum()
    frr = np.r_[0.0, np.cumsum(g)] / g.sum()
    d = far - frr
    exact = np.flatnonzero(d == 0.0)
    if len(exact):
        return float(far[exact[0]])
    cross = np.flatnonzero((d[:-1] > 0) & (d[1:] < 0))
    if len(cross):
        j = int(cross[0])
        w = d[j] / (d[j] - d[j + 1])
        return float(far[j] + w * (far[j + 1] - far[j]))
    j = int(np.argmin(np.maximum(far, frr)))      # never crosses
    return float((far[j] + frr[j]) / 2.0)


def eer_check(genuine, impostor, M):
    """Recompute EER from the histogram, to prove the dump is faithful."""
    g = np.asarray(genuine, float)
    i = np.asarray(impostor, float)
    far = np.r_[np.cumsum(i[::-1])[::-1], 0.0] / i.sum()
    frr = np.r_[0.0, np.cumsum(g)] / g.sum()
    d = far - frr
    exact = np.flatnonzero(d == 0.0)
    if len(exact):
        return float(far[exact[0]])
    cross = np.flatnonzero((d[:-1] > 0) & (d[1:] < 0))
    j = int(cross[0])
    w = d[j] / (d[j] - d[j + 1])
    return float(far[j] + w * (far[j + 1] - far[j]))


def run_score_dump():
    output = DIR["runs"] / "scores" / "score_histograms.json"
    if output.is_file():
        print("Resume: stored score histograms found; returning unchanged.")
        return json.loads(output.read_text())

    result = {"schema": 1, "analysis": "score_histograms",
              "systems": {
                  "protected": "polyiom, the sealed pipeline; integer "
                               "collision scores in 0..M",
                  "unprotected": "plain cosine between the same embeddings; "
                                 "binned over [-1,1], the performance-"
                                 "preservation reference"},
              "mated_note": "the mated distribution is both the "
                            "unlinkability mated set and the revocability "
                            "pseudo-impostor set; one measurement, not two",
              "lossless": "scores are integers in 0..M, so a count per "
                          "score value loses nothing",
              "master_seed": S0, "changes_any_seal": False, "modalities": {}}

    for modality in ("voice", "face"):
        sealed = json.loads(HELDOUT_RESULTS[modality].read_text())
        M, q, overlap = sealed["M"], sealed["q"], sealed["o"]
        tau = int(sealed["c_tau_carried_from_DEV"])
        key = selected_poly_key(modality)
        print(f"\n{modality.upper()}  M={M} q={q} o={overlap} tau={tau}")

        entry = {"M": M, "q": q, "o": overlap, "tau": tau,
                 "partitions": {}}
        for partition in ("development", "evaluation"):
            subjects, enroll, probes = partition_data(modality, partition)
            if len(subjects) < 2:
                print(f"  {partition}: too few identities, skipped")
                continue
            d = len(enroll[subjects[0]])
            k = 1 + math.ceil((d - G) / (G - overlap))
            recognition = load_iom_tensor(modality, overlap, d)[:M, :q] \
                .to(DEVICE, torch.float32)
            pair = []
            for index in (1, 2):
                gen = torch.Generator(device="cpu")
                gen.manual_seed(seed_unlink(modality, index))
                pair.append(torch.randn((M, q, k), generator=gen,
                                        dtype=torch.float32).to(DEVICE))
            h = histograms_for(modality, subjects, enroll, probes, M, q,
                               overlap, key, recognition, pair)
            h["dlink_curve"], h["dlink_global"] = unlinkability_curve(
                h["mated"], h["nonmated"])
            h["unprotected"] = cosine_histograms(subjects, enroll, probes)
            entry["partitions"][partition] = h
            recomputed = eer_check(h["genuine"], h["impostor"], M)
            raw = eer_cosine(h["unprotected"]["genuine"],
                             h["unprotected"]["impostor"])
            h["unprotected"]["EER"] = raw
            note = ""
            if partition == "evaluation":
                delta = abs(recomputed - sealed["EER_HOLDOUT"])
                note = (f"  reproduces sealed held-out EER "
                        f"({sealed['EER_HOLDOUT'] * 100:.4f}%)"
                        if delta <= 1e-9 else
                        f"  *** MISMATCH vs sealed "
                        f"{sealed['EER_HOLDOUT'] * 100:.4f}%")
            print(f"  {partition:<12} {h['n_subjects']} identities, "
                  f"{h['n_genuine']} genuine / {h['n_impostor']} impostor")
            print(f"    protected   EER {recomputed * 100:7.4f}%{note}")
            print(f"    unprotected EER {raw * 100:7.4f}%   "
                  f"-> protection costs "
                  f"{(recomputed - raw) * 100:+.4f} pp")
            print(f"    D_link global {h['dlink_global']:.6f}")
        result["modalities"][modality] = entry

    # External voice, if its embeddings are present
    ext = PROJECT / "external_voice_only.py"
    vctk = DIR["embeddings"] / "vctk_external_embeddings.npz"
    if ext.is_file() and vctk.is_file():
        try:
            scope = {"PROJECT": PROJECT, "DIR": DIR, "np": np, "pd": pd,
                     "torch": torch, "json": json, "math": math,
                     "hashlib": hashlib, "os": os, "Path": Path}
            exec(compile(ext.read_text(), str(ext), "exec"), scope)
            subjects, enroll, probes = scope["external_voice_data"]()
            sealed = json.loads(HELDOUT_RESULTS["voice"].read_text())
            M, q, overlap = sealed["M"], sealed["q"], sealed["o"]
            key = selected_poly_key("voice")
            d = len(enroll[subjects[0]])
            k = 1 + math.ceil((d - G) / (G - overlap))
            recognition = load_iom_tensor("voice", overlap, d)[:M, :q] \
                .to(DEVICE, torch.float32)
            pair = []
            for index in (1, 2):
                gen = torch.Generator(device="cpu")
                gen.manual_seed(seed_unlink("voice", index))
                pair.append(torch.randn((M, q, k), generator=gen,
                                        dtype=torch.float32).to(DEVICE))
            h = histograms_for("voice", subjects, enroll, probes, M, q,
                               overlap, key, recognition, pair)
            h["dlink_curve"], h["dlink_global"] = unlinkability_curve(
                h["mated"], h["nonmated"])
            h["unprotected"] = cosine_histograms(subjects, enroll, probes)
            h["unprotected"]["EER"] = eer_cosine(
                h["unprotected"]["genuine"], h["unprotected"]["impostor"])
            result["modalities"]["voice"]["partitions"]["external"] = h
            print(f"\n  external     {h['n_subjects']} speakers, "
                  f"{h['n_genuine']} genuine / {h['n_impostor']} impostor")
            print(f"    protected   EER "
                  f"{eer_check(h['genuine'], h['impostor'], M) * 100:7.4f}%")
            print(f"    unprotected EER "
                  f"{h['unprotected']['EER'] * 100:7.4f}%")
        except Exception as exc:
            print(f"\n  external: skipped - {type(exc).__name__}: {exc}")
    else:
        print("\n  external: skipped - VCTK embeddings or runtime not found")

    atomic_json(output, result)
    print("\nWrote", output)
    return result


print("Score dump ready. Run run_score_dump().")

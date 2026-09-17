
#@title 26. Pre-registered operating-point selection (run BEFORE touching VCTK)
# The whole point of the external lock is that the configuration is chosen
# from development data only. This cell writes the rule and the resulting
# choice to the seal, so the ordering is auditable after the fact. If it has
# already been sealed, the stored choice is reused and cannot be changed.

# Rule: among configurations meeting the recognition floor, take the one with
# the lowest Dsys (best unlinkability); ties broken by lower EER, then by the
# smaller M, q, o in that order. Rationale: recognition beyond the floor is
# not the contribution; unlinkability is.
#
# Applied to the sealed voice sweep (Sep 16) this selects M=128 q=32 o=1,
# EER 0.95%, TAR 95.2%, Dsys 0.053, from 30 eligible configurations.
# Set eer_max = 0.005 instead to select M=128 q=32 o=4 (EER 0.48%,
# Dsys 0.072) under the same rule.
SELECTION_RULE = {
    "rule_id": "min_dsys_subject_to_eer_floor_v1",
    "eer_max": 0.01,     # 1.0% EER ceiling
    "tar_min": 0.95,     # recognition floor
    "objective": "min Dsys_DEV",
    "tiebreak": ["EER", "M", "q", "o"],
}

# Per-modality overrides of SELECTION_RULE.
#
# Face cannot meet the voice floor: across all 80 face configurations the
# best EER is 2.29% and the best TAR is 90.08%, so the eligible set under
# eer_max=0.01 / tar_min=0.95 is empty. Rather than quietly relaxing the
# rule inside the selector, a modality that needs its own floor registers
# it here, and select_operating_point() seals the rule it actually applied.
# heldout_eval_cells.py registers the face floor; nothing else writes here.
MODALITY_RULES = {}


def rule_for(modality):
    """The rule that would be applied to this modality right now."""
    return MODALITY_RULES.get(modality, SELECTION_RULE)


def select_operating_point(modality):
    seal_path = DIR["seal"] / f"operating_point_{modality}.json"
    if seal_path.exists():
        chosen = json.loads(seal_path.read_text())
        active = MODALITY_RULES.get(modality, SELECTION_RULE)
        if chosen["rule"] != active:
            # A sealed per-modality deviation is re-adopted on resume: a
            # fresh runtime has an empty MODALITY_RULES, and the sealed
            # rule is the pre-registered one. Any other mismatch means the
            # rule was edited after sealing, which is not allowed.
            if (chosen["rule"].get("deviation_reason")
                    and modality not in MODALITY_RULES):
                MODALITY_RULES[modality] = chosen["rule"]
            else:
                raise RuntimeError(
                    f"{modality}: selection rule changed after sealing. "
                    "The pre-registered choice is immutable."
                )
        return chosen

    assert_internal_frozen(modality)

    rule = rule_for(modality)
    sweep_csv = DIR["runs"] / "sweep" / modality / "sweep_80.csv"
    df = pd.read_csv(sweep_csv)

    eligible = df[
        (df["EER"] <= rule["eer_max"])
        & (df["TAR_DEV"] >= rule["tar_min"])
    ]
    if eligible.empty:
        raise RuntimeError(
            f"{modality}: no configuration meets the floor "
            f"(EER <= {rule['eer_max']}, "
            f"TAR >= {rule['tar_min']}). "
            "Relax the rule and re-seal, or report the floor as unmet."
        )

    best = eligible.sort_values(
        ["Dsys_DEV", "EER", "M", "q", "o"]
    ).iloc[0]

    chosen = {
        "modality": modality,
        "rule": rule,
        "M": int(best["M"]),
        "q": int(best["q"]),
        "o": int(best["o"]),
        "development": {
            "EER": float(best["EER"]),
            "TAR_DEV": float(best["TAR_DEV"]),
            "Dsys_DEV": float(best["Dsys_DEV"]),
            "c_tau_DEV": int(best["c_tau_DEV"]),
        },
        "n_eligible": int(len(eligible)),
        "sweep_sha256": sha256_file(sweep_csv),
    }
    atomic_json(seal_path, chosen)
    return chosen


print("Selection rule defined. Nothing sealed until select_operating_point() runs.")


#@title 27. VCTK external embedding cache
# Built only after the internal method is frozen. VCTK is never used for key
# selection, thresholds, or configuration choice.
#
# NOTE: ecapa_embedding(), VCTK_MANIFEST and DIR["audio_vctk"] must match the
# names defined in cell 17. Rename here if they differ.
#
# The manifest and the 16 kHz audio it points at are produced by
# vctk_prepare_cells.py (prepare_vctk()), which works from the archive
# already in Drive; there is nothing left to download.

VCTK_EMB = DIR["embeddings"] / "vctk_external_embeddings.npz"


def extract_vctk_embeddings():
    if verified_stage("vctk_embeddings", [(VCTK_EMB, "sha256")]):
        print("RESUME: VCTK embeddings verified.")
        return np.load(VCTK_EMB, allow_pickle=False)

    manifest = pd.read_csv(VCTK_MANIFEST, sep="\t", dtype={"speaker_id": str})
    rows, embs = [], []

    for r in manifest.sort_values(["speaker_id", "rank"]).itertuples(index=False):
        path = DIR["audio_vctk"] / r.relative_path
        if not path.exists():
            raise RuntimeError(f"Missing sealed VCTK audio: {r.relative_path}")
        e = l2_np(ecapa_embedding(path))
        rows.append({
            "speaker_id": str(r.speaker_id),
            "rank": int(r.rank),
            "embedding_index": len(embs),
        })
        embs.append(e)

    table = pd.DataFrame(rows)
    npz_tmp = VCTK_EMB.with_name(VCTK_EMB.name + ".tmp")
    np.savez(
        npz_tmp,
        embedding=np.stack(embs).astype(np.float32),
        speaker_id=table["speaker_id"].to_numpy(),
        rank=table["rank"].to_numpy(),
        embedding_index=table["embedding_index"].to_numpy(),
    )
    os.replace(npz_tmp, VCTK_EMB)

    mark_stage("vctk_embeddings", {
        "n": len(embs),
        "sha256": sha256_file(VCTK_EMB),
    })
    print("VCTK embeddings:", len(embs))
    return np.load(VCTK_EMB, allow_pickle=False)


def vctk_external_data():
    z = extract_vctk_embeddings()
    E = z["embedding"]
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
        # Same enrolment construction as the voice development protocol:
        # ranks 0-4 averaged, ranks 5-14 as probes.
        e_members = np.stack([
            E[int(r.embedding_index)]
            for r in g[g["rank"] < 5].itertuples(index=False)
        ])
        uid = str(uid)
        subjects.append(uid)
        enroll[uid] = l2_np(np.mean(e_members, axis=0))
        probes[uid] = [
            E[int(r.embedding_index)]
            for r in g[g["rank"] >= 5].itertuples(index=False)
        ]
    return sorted(subjects), enroll, probes


print("VCTK external accessors ready.")


#@title 28. Locked external evaluation
# Applies the frozen key and the pre-registered configuration to VCTK.
# The development threshold c_tau_DEV is carried over unchanged: choosing a
# new threshold on external data would leak it.

def evaluate_external(modality="voice"):
    if modality != "voice":
        # The only external corpus prepared in this project is VCTK, which
        # is voice. CFP-FP is sealed as a name list for the LFW overlap
        # exclusion, not as an embedding corpus, so there is no external
        # face evaluation to run yet. Failing here beats silently scoring
        # face embeddings against VCTK.
        raise NotImplementedError(
            f"No external corpus is prepared for '{modality}'. "
            "Only the voice external evaluation (VCTK) exists."
        )

    out_dir = DIR["runs"] / "external" / modality
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "external_result.json"

    if result_path.exists():
        result = json.loads(result_path.read_text())
        print("Already evaluated:", result)
        return result

    assert_internal_frozen(modality)
    chosen = select_operating_point(modality)
    M, q, o = chosen["M"], chosen["q"], chosen["o"]
    tau = chosen["development"]["c_tau_DEV"]

    Ck, Ek = selected_poly_key(modality)
    subjects, enroll, probes = vctk_external_data()
    if len(subjects) < 2:
        raise RuntimeError("Too few external identities.")

    d = len(enroll[subjects[0]])
    R = iom_tensor(modality, o, d).to(MODEL_DEVICE)

    def hashed(vec):
        x = torch.tensor(vec, dtype=torch.float32,
                         device=MODEL_DEVICE).unsqueeze(0)
        return iom_hash(
            poly_transform(x, Ck, Ek, o), R, M, q
        ).squeeze(0).cpu()

    enroll_z = {uid: hashed(enroll[uid]) for uid in subjects}

    genuine, impostor = [], []
    for true_uid in subjects:
        for xnp in probes[true_uid]:
            zp = hashed(xnp)
            for claimed_uid in subjects:
                c = int(collision_count(enroll_z[claimed_uid], zp))
                (genuine if claimed_uid == true_uid else impostor).append(c)

    # Development threshold applied as-is. Also report the external EER,
    # which is threshold-free, so both a locked and a free number are on
    # record.
    tar_ext = tar_at_threshold(genuine, tau)
    fmr_ext = float(np.mean(np.asarray(impostor) >= tau))
    eer_ext, c_eer_ext = eer_discrete_interpolated(genuine, impostor, M)

    k = 1 + math.ceil((d - G) / (G - o))

    def unlink_R(key_index):
        gen = torch.Generator(device="cpu")
        gen.manual_seed(seed_unlink(modality, key_index))
        return torch.randn(
            (M, q, k), generator=gen, dtype=torch.float32
        ).to(MODEL_DEVICE)

    R1, R2 = unlink_R(1), unlink_R(2)

    def hashed_with(vec, Rx):
        x = torch.tensor(vec, dtype=torch.float32,
                         device=MODEL_DEVICE).unsqueeze(0)
        return iom_hash(
            poly_transform(x, Ck, Ek, o), Rx, M, q
        ).squeeze(0).cpu()

    z1 = {u: hashed_with(enroll[u], R1) for u in subjects}
    z2 = {u: hashed_with(enroll[u], R2) for u in subjects}
    mated = [int(collision_count(z1[u], z2[u])) for u in subjects]
    nonmated = [
        int(collision_count(z1[u], z2[v]))
        for u in subjects for v in subjects if u != v
    ]

    result = {
        "modality": modality,
        "corpus": "VCTK-Corpus-0.92",
        "protocol": PROTOCOL_VERSION,
        "M": M, "q": q, "o": o,
        "selection_rule_id": chosen["rule"]["rule_id"],
        "n_subjects": len(subjects),
        "n_genuine": len(genuine),
        "n_impostor": len(impostor),
        "c_tau_carried_from_DEV": int(tau),
        "TAR_EXT_at_dev_threshold": float(tar_ext),
        "FMR_EXT_at_dev_threshold": float(fmr_ext),
        "FNMR_EXT_at_dev_threshold": float(1.0 - tar_ext),
        "EER_EXT": float(eer_ext),
        "c_EER_EXT": int(c_eer_ext),
        "Dsys_EXT": float(dsys_discrete(mated, nonmated, M)),
        "development_reference": chosen["development"],
    }
    atomic_json(result_path, result)
    mark_stage(f"external_{modality}", {"sha256": sha256_file(result_path)})
    return result


print("External evaluation ready.")


#@title 29. Run the external evaluation (guarded)
RUN_EXTERNAL = False

if RUN_EXTERNAL:
    chosen = select_operating_point("voice")
    print("Pre-registered operating point:", json.dumps(chosen, indent=2), flush=True)
    result = evaluate_external("voice")
    print(json.dumps(result, indent=2), flush=True)

    dev, ext = result["development_reference"], result
    print("\nDevelopment -> External")
    print(f"  EER  {dev['EER']*100:6.2f}% -> {ext['EER_EXT']*100:6.2f}%")
    print(f"  TAR  {dev['TAR_DEV']*100:6.2f}% -> "
          f"{ext['TAR_EXT_at_dev_threshold']*100:6.2f}% (dev threshold)")
    print(f"  Dsys {dev['Dsys_DEV']:6.3f} -> {ext['Dsys_EXT']:6.3f}")
else:
    print("External evaluation not started. Set RUN_EXTERNAL = True to run.")

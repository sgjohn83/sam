"""
Phase 1 - held-out evaluation on the sealed 58-identity partition.

The 50/42/58 split reserved N_EVAL = 58 identities per modality that no
stage of the protocol has read: not key selection, not thresholds, not the
80-configuration sweep. They are the primary generalisation evidence and
require no downloads.

Load after the v1.1.4 notebook cells and external_eval_cells.py:

    exec(open("/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4/"
              "heldout_eval_cells.py").read())

Then, for the whole phase in one call:

    run_all_heldout()

or step by step:

    face_floor_report()              # what each floor admits for face
    seal_face_operating_point()      # decide the face floor first
    run_heldout("face")
    run_heldout("voice")
    heldout_summary()

Design notes:

* Accessors mirror face_development_data / voice_development_data exactly.
  Only the partition filter changes, so any difference in the result is a
  difference in the identities, not in how they were processed.
* c_tau_DEV is carried over unchanged. Re-fitting a threshold on held-out
  data would leak it and make the number meaningless.
* EER is reported alongside because it is threshold-free, so a threshold
  carried from a 42-subject development set cannot flatter or penalise it.
* Unlinkability uses the same two independently seeded IoM keys as the
  sweep, so Dsys_HOLDOUT is directly comparable to Dsys_DEV.

Expected trial counts at 58 identities: voice 580 genuine / 33,060 impostor
(10 probes each); face depends on images per identity (>= 2 probes each).
"""

import json
import math
import os

import numpy as np
import pandas as pd
import torch


if "rule_for" not in globals() or "MODALITY_RULES" not in globals():
    raise RuntimeError(
        "external_eval_cells.py looks out of date: rule_for() / "
        "MODALITY_RULES are missing. Load the current copy from Drive "
        "before this file, otherwise the face floor cannot be registered "
        "and the sealed face rule will be rejected on the next run."
    )


# ---------------------------------------------------------------- accessors

def face_heldout_data():
    """Mirror of face_development_data() on partition == "evaluation"."""
    trials = pd.read_csv(LFW_FACE_TRIALS, sep="\t")
    _, E = face_embedding_table()
    held = trials[trials["partition"] == "evaluation"]

    subjects, enroll, probes = [], {}, {}
    for uid, g in held.groupby("subject_id"):
        erow = g[g["role"] == "enroll"]
        prows = g[g["role"] == "probe"]
        if len(erow) != 1 or len(prows) < 1:
            continue
        uid = str(uid)
        subjects.append(uid)
        enroll[uid] = E[int(erow.iloc[0].embedding_index)]
        probes[uid] = [
            E[int(r.embedding_index)]
            for r in prows.itertuples(index=False)
        ]
    return subjects, enroll, probes


def voice_heldout_data():
    """Mirror of voice_development_data() on partition == "evaluation"."""
    manifest = pd.read_csv(
        LIBRI_MANIFEST, sep="\t", dtype={"speaker_id": str}
    )
    table, E = voice_embedding_table()
    merged = manifest.merge(
        table[["speaker_id", "rank", "embedding_index"]],
        on=["speaker_id", "rank"],
        how="inner",
    )
    held = merged[merged["partition"] == "evaluation"]

    subjects, enroll, probes = [], {}, {}
    for uid, g in held.groupby("speaker_id"):
        g = g.sort_values("rank")
        if len(g) != 15:
            continue
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
    return subjects, enroll, probes


_HELDOUT_CACHE = {}


def heldout_data(modality):
    if modality not in _HELDOUT_CACHE:
        _HELDOUT_CACHE[modality] = (
            face_heldout_data() if modality == "face"
            else voice_heldout_data()
        )
    return _HELDOUT_CACHE[modality]


# ------------------------------------------------- face operating point

# Face is single-sample enrolment, and it does not clear the voice floor of
# EER <= 1.0% with TAR >= 95%. Measured over the sealed 80-row face sweep
# (runs/sweep/face/sweep_80.csv, Sep 16):
#
#   best EER  2.29%   (voice rule needs <= 1.00%)
#   best TAR 90.08%   (voice rule needs >= 95.00%)
#
# so the eligible set under the voice rule is empty, and no eer_max <= 0.02
# admits anything either. What the attainable floors admit:
#
#   eer_max  tar_min  eligible  min Dsys  best config
#     0.03     0.90        1      0.166   M=256 q=8  o=3  EER 2.67% TAR 90.08%
#     0.03     0.85       13      0.133   M=256 q=32 o=1  EER 2.84% TAR 86.26%
#     0.05     0.85       20      0.101   M=256 q=16 o=4  EER 3.05% TAR 85.11%
#     0.05     0.80       35      0.044   M=64  q=32 o=4  EER 4.01% TAR 81.68%
#
# FACE_FLOOR is set to 3% / 85%: the tightest floor that still selects from
# a real pool rather than a single point. At 3% / 90% exactly one
# configuration survives, so the "choice" would be an artifact of the grid,
# and the resulting Dsys (0.166) is worse anyway. Looser floors buy
# unlinkability with an accuracy claim that is harder to defend.
#
# This is set from face's own development distribution, before any held-out
# identity is read, and it is sealed with its justification so the paper can
# state the deviation rather than imply the voice rule was met.
FACE_FLOOR = {"eer_max": 0.03, "tar_min": 0.85}

FACE_DEVIATION_REASON = (
    "Face uses single-sample enrolment (LFW provides as few as three "
    "images per identity); the voice floor is not attainable - over the "
    "sealed 80-configuration face sweep the best EER is 2.29% and the "
    "best TAR is 90.08%, so the eligible set under eer_max=0.01 / "
    "tar_min=0.95 is empty. Floor set on face's own development "
    "distribution, before any held-out data was read."
)


def face_floor_report():
    sweep_csv = DIR["runs"] / "sweep" / "face" / "sweep_80.csv"
    df = pd.read_csv(sweep_csv)

    print(f"face sweep: {len(df)} configurations")
    print(f"  best EER  {df['EER'].min()*100:6.2f}%")
    print(f"  best TAR  {df['TAR_DEV'].max()*100:6.2f}%")
    print(f"  best Dsys {df['Dsys_DEV'].min():6.3f}")
    print()

    voice_rule = SELECTION_RULE
    n_voice = len(df[
        (df["EER"] <= voice_rule["eer_max"])
        & (df["TAR_DEV"] >= voice_rule["tar_min"])
    ])
    print(f"  voice rule (EER <= {voice_rule['eer_max']}, "
          f"TAR >= {voice_rule['tar_min']}): {n_voice} eligible"
          + ("" if n_voice else "  <- not attainable for face"))
    print()

    print("  eer_max  tar_min  eligible  min Dsys among eligible")
    for eer_max in (0.005, 0.01, 0.02, 0.03, 0.05, 0.10):
        for tar_min in (0.95, 0.90, 0.85, 0.80):
            el = df[(df["EER"] <= eer_max) & (df["TAR_DEV"] >= tar_min)]
            if el.empty:
                continue
            mark = ("  <- FACE_FLOOR"
                    if (eer_max == FACE_FLOOR["eer_max"]
                        and tar_min == FACE_FLOOR["tar_min"]) else "")
            print(f"  {eer_max:7.3f}  {tar_min:7.2f}  {len(el):8d}"
                  f"  {el['Dsys_DEV'].min():.3f}{mark}")
    return df


def seal_face_operating_point(eer_max=None, tar_min=None):
    """Seal the face operating point.

    With no arguments this tries the voice rule unchanged, which is
    preferable when face can meet it, and falls back to FACE_FLOOR when the
    eligible set is empty. Pass an explicit floor to override FACE_FLOOR.
    Either way the rule actually applied is written into the seal, with its
    justification, so the paper can state it.
    """
    seal_path = DIR["seal"] / "operating_point_face.json"
    if seal_path.exists():
        # Already pre-registered; select_operating_point re-adopts the
        # sealed rule and refuses to change it.
        return select_operating_point("face")

    if eer_max is None and tar_min is None:
        df = pd.read_csv(DIR["runs"] / "sweep" / "face" / "sweep_80.csv")
        meets_voice_rule = not df[
            (df["EER"] <= SELECTION_RULE["eer_max"])
            & (df["TAR_DEV"] >= SELECTION_RULE["tar_min"])
        ].empty
        if meets_voice_rule:
            print("face meets the voice rule; sealing it unchanged.")
            return select_operating_point("face")
        eer_max = FACE_FLOOR["eer_max"]
        tar_min = FACE_FLOOR["tar_min"]
        print(f"face cannot meet the voice rule "
              f"(EER <= {SELECTION_RULE['eer_max']}, "
              f"TAR >= {SELECTION_RULE['tar_min']}); "
              f"applying FACE_FLOOR "
              f"(EER <= {eer_max}, TAR >= {tar_min}).")

    rule = dict(SELECTION_RULE)
    if eer_max is not None:
        rule["eer_max"] = float(eer_max)
    if tar_min is not None:
        rule["tar_min"] = float(tar_min)
    rule["rule_id"] = (
        f"min_dsys_subject_to_eer_floor_v1_face"
        f"_eer{rule['eer_max']}_tar{rule['tar_min']}"
    )
    rule["deviation_reason"] = FACE_DEVIATION_REASON

    # Registered rather than swapped in around the call: the sealed rule
    # has to stay readable afterwards, or select_operating_point("face")
    # and evaluate_external("face") would reject it as "changed after
    # sealing" on the very next call.
    MODALITY_RULES["face"] = rule
    return select_operating_point("face")


# ------------------------------------------------------------ evaluation

def evaluate_heldout(modality):
    """Apply the frozen key and sealed operating point to the 58 held-out
    identities. Metric computation mirrors sweep_one_config exactly."""
    out_dir = DIR["runs"] / "heldout" / modality
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "heldout_result.json"

    if result_path.exists():
        result = json.loads(result_path.read_text())
        print("Already evaluated:", modality)
        return result

    assert_internal_frozen(modality)

    seal_path = DIR["seal"] / f"operating_point_{modality}.json"
    if not seal_path.exists():
        raise RuntimeError(
            f"{modality}: no sealed operating point. Run "
            f"select_operating_point('{modality}') or "
            f"seal_face_operating_point(...) first."
        )
    chosen = json.loads(seal_path.read_text())
    M, q, o = chosen["M"], chosen["q"], chosen["o"]
    tau = chosen["development"]["c_tau_DEV"]

    Ck, Ek = selected_poly_key(modality)
    subjects, enroll, probes = heldout_data(modality)

    if len(subjects) != N_EVAL:
        print(f"WARNING {modality}: {len(subjects)} held-out identities, "
              f"expected {N_EVAL}. Reporting on what is present.")
    if len(subjects) < 2:
        raise RuntimeError(f"{modality}: too few held-out identities.")

    d = len(enroll[subjects[0]])
    R = iom_tensor(modality, o, d).to(MODEL_DEVICE)

    def hashed(vec, Rx=R):
        x = torch.tensor(vec, dtype=torch.float32,
                         device=MODEL_DEVICE).unsqueeze(0)
        return iom_hash(
            poly_transform(x, Ck, Ek, o), Rx, M, q
        ).squeeze(0).cpu()

    enroll_z = {uid: hashed(enroll[uid]) for uid in subjects}

    genuine, impostor = [], []
    for true_uid in subjects:
        for xnp in probes[true_uid]:
            zp = hashed(xnp)
            for claimed_uid in subjects:
                c = int(collision_count(enroll_z[claimed_uid], zp))
                (genuine if claimed_uid == true_uid else impostor).append(c)

    tar = tar_at_threshold(genuine, tau)
    fmr = float(np.mean(np.asarray(impostor) >= tau))
    eer, c_eer = eer_discrete_interpolated(genuine, impostor, M)

    # Same two independently seeded IoM keys as the sweep, so Dsys is
    # directly comparable to the development figure.
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
    mated = [int(collision_count(z1[u], z2[u])) for u in subjects]
    nonmated = [
        int(collision_count(z1[u], z2[v]))
        for u in subjects for v in subjects if u != v
    ]

    result = {
        "modality": modality,
        "partition": "evaluation",
        "protocol": PROTOCOL_VERSION,
        "M": M, "q": q, "o": o,
        "selection_rule_id": chosen["rule"]["rule_id"],
        "n_subjects": len(subjects),
        "n_genuine": len(genuine),
        "n_impostor": len(impostor),
        "c_tau_carried_from_DEV": int(tau),
        "TAR_HOLDOUT_at_dev_threshold": float(tar),
        "FMR_HOLDOUT_at_dev_threshold": float(fmr),
        "FNMR_HOLDOUT_at_dev_threshold": float(1.0 - tar),
        "EER_HOLDOUT": float(eer),
        "c_EER_HOLDOUT": int(c_eer),
        "Dsys_HOLDOUT": float(dsys_discrete(mated, nonmated, M)),
        "development_reference": chosen["development"],
    }
    atomic_json(result_path, result)
    mark_stage(f"heldout_{modality}", {"sha256": sha256_file(result_path)})
    return result


def run_heldout(modality):
    r = evaluate_heldout(modality)
    dev = r["development_reference"]
    print(f"\n{modality.upper()}  M={r['M']} q={r['q']} o={r['o']}  "
          f"n={r['n_subjects']}  tau={r['c_tau_carried_from_DEV']}")
    print(f"  EER  {dev['EER']*100:6.2f}% -> "
          f"{r['EER_HOLDOUT']*100:6.2f}%")
    print(f"  TAR  {dev['TAR_DEV']*100:6.2f}% -> "
          f"{r['TAR_HOLDOUT_at_dev_threshold']*100:6.2f}% (dev threshold)")
    print(f"  Dsys {dev['Dsys_DEV']:6.3f} -> {r['Dsys_HOLDOUT']:6.3f}")
    return r


def heldout_summary():
    """The generalisation table, ready to transcribe into the paper."""
    rows = []
    for modality in ("face", "voice"):
        p = DIR["runs"] / "heldout" / modality / "heldout_result.json"
        if not p.exists():
            print(f"{modality}: not evaluated")
            continue
        r = json.loads(p.read_text())
        dev = r["development_reference"]
        rows.append({
            "modality": modality,
            "M": r["M"], "q": r["q"], "o": r["o"],
            "n_dev": N_DEV, "n_heldout": r["n_subjects"],
            "EER_dev": dev["EER"], "EER_heldout": r["EER_HOLDOUT"],
            "TAR_dev": dev["TAR_DEV"],
            "TAR_heldout": r["TAR_HOLDOUT_at_dev_threshold"],
            "Dsys_dev": dev["Dsys_DEV"], "Dsys_heldout": r["Dsys_HOLDOUT"],
        })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    out = DIR["runs"] / "heldout" / "generalisation_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, out)
    print(df.to_string(index=False))
    print(f"\nWrote {out}")
    return df


def run_all_heldout():
    """Seal both operating points, evaluate both modalities, print the table.

    Safe to re-run: every step returns the sealed or stored result if it
    already exists, and nothing re-fits a threshold.
    """
    voice = select_operating_point("voice")
    print("voice operating point:", {k: voice[k] for k in ("M", "q", "o")},
          voice["rule"]["rule_id"])
    face = seal_face_operating_point()
    print("face  operating point:", {k: face[k] for k in ("M", "q", "o")},
          face["rule"]["rule_id"])
    for modality in ("face", "voice"):
        run_heldout(modality)
    print()
    return heldout_summary()


print("Held-out evaluation ready.")
print(f"  FACE_FLOOR = EER <= {FACE_FLOOR['eer_max']}, "
      f"TAR >= {FACE_FLOOR['tar_min']} (voice rule is unattainable for face)")
print("  run_all_heldout()           - seal both, evaluate both, print table")
print("  face_floor_report()         - what each floor admits for face")
print("  seal_face_operating_point() - seal it (optionally with a floor)")
print("  run_heldout('face' / 'voice')")
print("  heldout_summary()           - the generalisation table")

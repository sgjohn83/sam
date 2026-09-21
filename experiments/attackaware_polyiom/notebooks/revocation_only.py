"""Post-revocation acceptance for AttackAware PolyIoM v1.1.4.

Loaded after ablation_only.py and inversion_only.py. Answers the one
question the inversion run left open: does the attacker's reconstruction,
built from an OLD template, still get in after the subject re-enrols under
a FULLY re-keyed system?

The inversion run re-keyed the IoM projection R only. This re-keys
everything each arm has:

  polyiom       fresh polynomial key K** AND fresh projection R'
  randproj_iom  fresh random map A'      AND fresh projection R'
  iom_only      fresh projection R'      (it has nothing else)

The attacker never re-attacks. They hold one stolen template, reconstruct
once, and the subject then re-enrols. That is the real revocation
scenario.

Headline metric, fixed in advance: **PRAR**, post-revocation acceptance
rate - the fraction of subjects whose old-template reconstruction is
accepted at the sealed threshold after full re-keying. Revocation works
only if PRAR falls to the impostor floor.

K** is drawn to match K*'s structure by resampling its own coefficient and
exponent values, NOT by re-running Stage A's inversion gate. For this
question that is the right construction: we are asking whether z'
resembles z in the ways any polynomial of that family sees, not whether
K** is a good key. Three independent draws guard against a fluke.

Writes one file, runs/revocation/revocation_result.json, and no seal.
"""

REV_N_KEYS = 3
REV_N_BOOTSTRAP = 2000
REV_CONFIDENCE = 0.95


def fresh_poly_key(modality, key, index):
    """A new polynomial key matched to K*'s own value distribution."""
    C, E = key
    rng = np.random.default_rng(H(S0, "REVOCATION-KEY", modality, index))
    return (rng.choice(np.asarray(C).reshape(-1), size=np.asarray(C).shape,
                       replace=True).astype(np.float32),
            rng.choice(np.asarray(E).reshape(-1), size=np.asarray(E).shape,
                       replace=True).astype(np.int64))


def fresh_params(arm, modality, index, key, M, q, d, k):
    """Everything this arm would re-issue on revocation."""
    label = f"revocation|{index}"
    if arm == "polyiom":
        return (fresh_poly_key(modality, key, index),
                None,
                abl_randn((M, q, k), modality, f"{label}|R|poly").to(DEVICE))
    if arm == "randproj_iom":
        return (key,
                abl_randn((d, k), modality, f"{label}|A").to(DEVICE) / math.sqrt(d),
                abl_randn((M, q, k), modality, f"{label}|R|prj").to(DEVICE))
    if arm == "iom_only":
        return (key, None,
                abl_randn((M, q, d), modality, f"{label}|R|raw").to(DEVICE))
    raise ValueError(arm)


def revocation_for(modality):
    sealed = json.loads(HELDOUT_RESULTS[modality].read_text())
    M, q, overlap = sealed["M"], sealed["q"], sealed["o"]
    tau = int(sealed["c_tau_carried_from_DEV"])
    subjects, enroll, probes = (
        face_heldout_data() if modality == "face" else voice_heldout_data()
    )
    key = selected_poly_key(modality)
    n, d = len(subjects), len(enroll[subjects[0]])
    k = 1 + math.ceil((d - G) / (G - overlap))
    print(f"  {modality}: n={n} d={d} k={k} M={M} q={q} tau={tau}")
    assert_diff_matches(modality, key, overlap, d)

    frozen = load_iom_tensor(modality, overlap, d)[:M, :q].to(DEVICE, torch.float32)
    recognition = {
        "polyiom": frozen,
        "iom_only": abl_randn((M, q, d), modality, "match|iom_only").to(DEVICE),
        "randproj_iom": abl_randn((M, q, k), modality, "match|randproj").to(DEVICE),
    }
    A = abl_randn((d, k), modality, "projmap").to(DEVICE) / math.sqrt(d)
    truth = torch.as_tensor(np.stack([enroll[uid] for uid in subjects]),
                            dtype=torch.float32, device=DEVICE)

    out = {}
    for arm in ARMS:
        print(f"    --- {arm}")
        targets = codes_of(arm, truth, key, overlap, recognition[arm], A)
        # Same seeds as the inversion run, so z' is bit-identical to it.
        recovered, hits = invert_arm(
            arm, targets, key, overlap, recognition[arm], A, d,
            seed=H(S0, "INVERSION", modality, arm) % (2 ** 31))

        accepted_per_key, impostor_per_key = [], []
        for index in range(REV_N_KEYS):
            new_key, new_A, new_R = fresh_params(
                arm, modality, index, key, M, q, d, k)
            eff_A = new_A if new_A is not None else A
            true_codes = codes_of(arm, truth, new_key, overlap, new_R, eff_A)
            rec_codes = codes_of(arm, recovered, new_key, overlap, new_R, eff_A)
            agree = (true_codes == rec_codes).sum(dim=-1)
            accepted_per_key.append((agree >= tau).float().cpu().numpy())
            off = ~torch.eye(n, dtype=torch.bool, device=DEVICE)
            floor = float((true_codes[:, None, :] == true_codes[None, :, :])
                          .sum(-1)[off].float().mean())
            # A resampled key can pair a large exponent with a small
            # coefficient so hard that every power underflows, the projection
            # collapses to zero, and argmax returns bucket 0 for everyone.
            # That would read as PRAR 100% for entirely the wrong reason.
            # A healthy key puts different subjects near the M/q chance floor.
            if floor > M / 4:
                raise RuntimeError(
                    f"{modality}/{arm}: fresh key {index} is degenerate - "
                    f"different subjects collide {floor:.1f}/{M} times, "
                    f"against a chance floor of {M / q:.1f}. The re-keyed "
                    f"system is not discriminating, so no revocation "
                    f"conclusion can be drawn from it."
                )
            impostor_per_key.append(floor)
            print(f"      re-key {index + 1}/{REV_N_KEYS}: "
                  f"mean agreement {float(agree.float().mean()):6.1f}/{M}  "
                  f"accepted {float((agree >= tau).float().mean()) * 100:6.2f}%"
                  f"   impostor floor {impostor_per_key[-1]:5.1f}")

        out[arm] = {
            "prar": np.mean(np.stack(accepted_per_key), axis=0),   # per identity
            "cos": cosine_rows(recovered, truth).cpu().numpy(),
            "hits": hits.cpu().numpy(),
            "impostor_floor": float(np.mean(impostor_per_key)),
        }
        print(f"    {arm:<13} PRAR {out[arm]['prar'].mean() * 100:6.2f}%   "
              f"cos {out[arm]['cos'].mean():.3f}")

    return {"modality": modality, "M": M, "tau": tau, "d": d, "k": k,
            "n": n, "arms": out}


def run_revocation(n_bootstrap=REV_N_BOOTSTRAP, confidence=REV_CONFIDENCE):
    output = DIR["runs"] / "revocation" / "revocation_result.json"
    if output.is_file():
        print("Resume: stored revocation result found; returning it unchanged.")
        return json.loads(output.read_text())

    result = {
        "schema": 1, "analysis": "post_revocation_acceptance",
        "question": "does an old template's reconstruction still get in "
                    "after the subject re-enrols under a fully re-keyed system",
        "re_keys": {"polyiom": "fresh K** and fresh R",
                    "randproj_iom": "fresh A and fresh R",
                    "iom_only": "fresh R"},
        "n_fresh_keys": REV_N_KEYS,
        "fresh_key_construction": "resampled from K*'s own coefficient and "
                                  "exponent values; NOT passed through "
                                  "Stage A's inversion gate",
        "method_id": "identity_cluster_percentile_v1_paired",
        "n_bootstrap": int(n_bootstrap), "confidence": float(confidence),
        "master_seed": S0, "changes_any_seal": False, "modalities": {},
    }

    for modality in ("voice", "face"):
        print(f"\n{modality.upper()}")
        record = revocation_for(modality)
        n = record["n"]
        rng = np.random.default_rng(H(S0, "REVOCATION-BOOTSTRAP", modality))
        stats = {a: {"PRAR": [], "cos": []} for a in ARMS}
        contrasts = {a: {"delta_PRAR": [], "delta_cos": []}
                     for a in ARMS if a != "polyiom"}
        for _ in range(n_bootstrap):
            w = rng.multinomial(n, np.full(n, 1 / n)) / float(n)
            values = {a: (float(w @ record["arms"][a]["prar"]),
                          float(w @ record["arms"][a]["cos"])) for a in ARMS}
            for a in ARMS:
                stats[a]["PRAR"].append(values[a][0])
                stats[a]["cos"].append(values[a][1])
            for a in contrasts:
                contrasts[a]["delta_PRAR"].append(values[a][0] - values["polyiom"][0])
                contrasts[a]["delta_cos"].append(values[a][1] - values["polyiom"][1])

        alpha = 1.0 - confidence

        def interval(v):
            lo, hi = np.quantile(v, [alpha / 2, 1 - alpha / 2])
            return [float(lo), float(hi)]

        result["modalities"][modality] = {
            "n_subjects": n, "M": record["M"], "tau": record["tau"],
            "d": record["d"], "k": record["k"],
            "arms": {a: {
                "PRAR": float(record["arms"][a]["prar"].mean()),
                "PRAR_CI": interval(stats[a]["PRAR"]),
                "cos_to_true": float(record["arms"][a]["cos"].mean()),
                "cos_CI": interval(stats[a]["cos"]),
                "impostor_floor_collisions": record["arms"][a]["impostor_floor"],
                "attack_collisions": float(record["arms"][a]["hits"].mean()),
            } for a in ARMS},
            "contrasts_vs_polyiom": {a: {
                "delta_PRAR": float(record["arms"][a]["prar"].mean()
                                    - record["arms"]["polyiom"]["prar"].mean()),
                "delta_PRAR_CI": interval(contrasts[a]["delta_PRAR"]),
                "delta_cos": float(record["arms"][a]["cos"].mean()
                                   - record["arms"]["polyiom"]["cos"].mean()),
                "delta_cos_CI": interval(contrasts[a]["delta_cos"]),
            } for a in contrasts},
        }

    atomic_json(output, result)
    print("\nWrote", output)
    return result


def revocation_report(result):
    for modality, data in result["modalities"].items():
        print(f"\n{modality.upper()}  n={data['n_subjects']}  M={data['M']}  "
              f"tau={data['tau']}")
        print(f"  {'arm':<14}{'PRAR %':>22}{'cos to true':>26}"
              f"{'imp floor':>11}")
        for arm, v in data["arms"].items():
            print(f"  {arm:<14}"
                  f"{v['PRAR'] * 100:7.2f} [{v['PRAR_CI'][0] * 100:5.2f},"
                  f"{v['PRAR_CI'][1] * 100:6.2f}]"
                  f"{v['cos_to_true']:11.3f} [{v['cos_CI'][0]:6.3f},"
                  f"{v['cos_CI'][1]:6.3f}]"
                  f"{v['impostor_floor_collisions']:11.1f}")
        print("  contrasts (arm minus proposed; interval excluding 0 is firm)")
        for arm, c in data["contrasts_vs_polyiom"].items():
            for name, scale, unit in (("PRAR", 100, " %"), ("cos", 1, "")):
                value, (lo, hi) = c[f"delta_{name}"], c[f"delta_{name}_CI"]
                firm = "FIRM" if (lo > 0 or hi < 0) else "not distinguishable"
                print(f"    {arm:<14} d{name:<5}{value * scale:+8.3f}{unit}  "
                      f"[{lo * scale:+7.3f},{hi * scale:+7.3f}]  {firm}")
    print("\n  PRAR is the fraction of subjects whose OLD template's")
    print("  reconstruction is still accepted after full re-keying.")
    print("  Revocation WORKS only if PRAR falls to near zero. A PRAR near")
    print("  100% means a single stolen template is a permanent credential.")
    print("  'imp floor' is the mean collision count between different")
    print("  subjects under the new keys, for scale against tau.")


print("Revocation evaluation ready.")

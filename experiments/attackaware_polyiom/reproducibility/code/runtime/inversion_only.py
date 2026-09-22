"""Full-knowledge inversion evaluation for AttackAware PolyIoM v1.1.4.

Loaded by AttackAware_PolyIoM_v1_1_4_INVERSION.ipynb after its preflight
cell, and after ablation_only.py has supplied the frozen-pipeline
primitives. Pre-specification is in THREAT_MODEL.md; budget and success
criteria were fixed before this was run.

Writes one file, runs/inversion/inversion_result.json, and no seal.
"""

INV_RESTARTS = 5
INV_STEPS = 800
INV_LR = 0.05
INV_TEMP0, INV_TEMP1 = 1.0, 0.05
INV_N_BOOTSTRAP = 2000
INV_CONFIDENCE = 0.95


def poly_transform_diff(vectors, coefficients, exponents, overlap):
    """Differentiable polynomial, numerically identical to the study's.

    The study calls torch.pow(values, int64_tensor). Casting that exponent
    to float to get gradients would produce nan on negative bases, so the
    powers are built with Python integer exponents instead, which keeps
    integer-power semantics and a defined gradient.
    """
    idx, mask = poly_indices(vectors.shape[-1], overlap, vectors.device)
    values = vectors[..., idx] * mask.to(vectors.dtype)
    coefficients = torch.as_tensor(
        coefficients, device=vectors.device, dtype=vectors.dtype)
    powers = torch.stack(
        [values[..., i] ** int(exponents[i]) for i in range(values.shape[-1])],
        dim=-1,
    )
    return (powers * coefficients).sum(dim=-1)


def assert_diff_matches(modality, key, overlap, d, tolerance=1e-4):
    """Assertion 1 - the differentiable path is the study's path.

    Checked on RELATIVE error, and on the bucket indices it produces, not
    on absolute error. torch.pow(x, int64_tensor) and x ** int dispatch to
    different kernels, so they round differently; on a polynomial whose
    intermediate values can be large that shows as an absolute gap of a few
    1e-4 while the relative gap is ~1e-7. An earlier absolute threshold of
    1e-4 here was simply the wrong test.

    What actually matters is that no bucket index moves. This function
    checks that directly on the probes, and assertion 2 then confirms it
    end to end against the real stored templates.
    """
    generator = torch.Generator(device="cpu")
    generator.manual_seed(H(S0, "INVERSION-CHECK", modality))
    probe = torch.randn((64, d), generator=generator, dtype=torch.float32)
    probe = probe / probe.norm(dim=-1, keepdim=True)   # as real embeddings are
    reference = poly_transform(probe, key[0], key[1], overlap)
    candidate = poly_transform_diff(probe, key[0], key[1], overlap)

    absolute = float((reference - candidate).abs().max())
    scale = float(reference.abs().max())
    relative = absolute / max(scale, 1e-30)
    if not relative < tolerance:
        raise RuntimeError(
            f"{modality}: differentiable polynomial differs from the "
            f"study's by a relative {relative:.3e} (absolute {absolute:.3e} "
            f"at scale {scale:.3e}); the attack would not be attacking the "
            f"real scheme."
        )

    # The decisive check: same argmax, on a tensor of the right width.
    k = 1 + math.ceil((d - G) / (G - overlap))
    probe_generator = torch.Generator(device="cpu")
    probe_generator.manual_seed(H(S0, "INVERSION-CHECK-TENSOR", modality))
    probe_tensor = torch.randn((64, 32, k), generator=probe_generator,
                               dtype=torch.float32)
    left = torch.argmax(torch.einsum("bk,mqk->bmq", reference, probe_tensor), -1)
    right = torch.argmax(torch.einsum("bk,mqk->bmq", candidate, probe_tensor), -1)
    moved = int((left != right).sum())
    if moved:
        raise RuntimeError(
            f"{modality}: {moved} bucket indices move between the study's "
            f"polynomial and the differentiable one; the attack would not "
            f"be attacking the real scheme."
        )
    print(f"    assertion 1 OK: differentiable polynomial matches "
          f"(relative {relative:.2e}, absolute {absolute:.2e} at scale "
          f"{scale:.2e}) and moves no bucket index")


def project(arm, z, key, overlap, A):
    """Arm-specific pre-projection, rescaled to unit norm.

    argmax within a group is invariant to a positive per-sample rescale, so
    this changes no bucket index (assertion 2 checks that empirically). It
    exists so the annealed temperature means the same thing for every arm:
    the polynomial's output norm is not 1, and without this the three arms
    would be attacked at different effective temperatures, which would make
    the comparison unfair and could overflow the softmax.
    """
    if arm == "polyiom":
        x = poly_transform_diff(z, key[0], key[1], overlap)
    elif arm == "randproj_iom":
        x = z @ A
    elif arm == "iom_only":
        x = z
    else:
        raise ValueError(arm)
    return x / x.norm(dim=-1, keepdim=True).clamp_min(1e-12)


def codes_of(arm, z, key, overlap, tensor, A):
    """Hard bucket indices, no gradient."""
    with torch.no_grad():
        scores = torch.einsum(
            "bk,mqk->bmq", project(arm, z, key, overlap, A), tensor)
        return torch.argmax(scores, dim=-1)


def invert_arm(arm, targets, key, overlap, tensor, A, d, seed,
               restarts=INV_RESTARTS, steps=INV_STEPS, lr=INV_LR):
    """Attack every template at once. Identical budget for every arm."""
    n = targets.shape[0]
    best_z = torch.zeros((n, d), dtype=torch.float32, device=DEVICE)
    best_hits = torch.full((n,), -1, dtype=torch.int64, device=DEVICE)

    for restart in range(restarts):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed + restart)
        z = torch.randn((n, d), generator=generator, dtype=torch.float32)
        z = (z / z.norm(dim=-1, keepdim=True)).to(DEVICE).requires_grad_(True)
        optimiser = torch.optim.Adam([z], lr=lr)

        for step in range(steps):
            temperature = INV_TEMP0 * (INV_TEMP1 / INV_TEMP0) ** (step / max(steps - 1, 1))
            scores = torch.einsum(
                "bk,mqk->bmq", project(arm, z, key, overlap, A), tensor)
            loss = torch.nn.functional.cross_entropy(
                (scores / temperature).reshape(-1, scores.shape[-1]),
                targets.reshape(-1),
            )
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_([z], 5.0)
            optimiser.step()
            with torch.no_grad():
                z /= z.norm(dim=-1, keepdim=True).clamp_min(1e-12)

        hits = (codes_of(arm, z.detach(), key, overlap, tensor, A)
                == targets).sum(dim=-1)
        improved = hits > best_hits
        best_hits = torch.where(improved, hits, best_hits)
        best_z[improved] = z.detach()[improved]
        print(f"      {arm:<13} restart {restart + 1}/{restarts}  "
              f"loss {float(loss.detach()):7.4f}  best mean hits "
              f"{float(best_hits.float().mean()):7.2f}")

    return best_z, best_hits


def cosine_rows(a, b):
    a = a / a.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    b = b / b.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    return (a * b).sum(dim=-1)


def inversion_for(modality):
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
        "iom_only": abl_randn((M, q, d), modality, "match|iom_only")[:M, :q].to(DEVICE),
        "randproj_iom": abl_randn((M, q, k), modality, "match|randproj")[:M, :q].to(DEVICE),
    }
    A = abl_randn((d, k), modality, "projmap").to(DEVICE) / math.sqrt(d)

    cross_generator = torch.Generator(device="cpu")
    cross_generator.manual_seed(seed_unlink(modality, 1))
    cross = {
        "polyiom": torch.randn((M, q, k), generator=cross_generator,
                               dtype=torch.float32).to(DEVICE),
        "iom_only": abl_randn((M, q, d), modality, "unlink|raw|1").to(DEVICE),
        "randproj_iom": abl_randn((M, q, k), modality, "unlink|prj|1").to(DEVICE),
    }

    truth = torch.as_tensor(
        np.stack([enroll[uid] for uid in subjects]),
        dtype=torch.float32, device=DEVICE)

    out = {}
    for arm in ARMS:
        print(f"    --- {arm}")
        targets = codes_of(arm, truth, key, overlap, recognition[arm], A)

        if arm == "polyiom":                       # assertion 2
            stored = torch.as_tensor(
                hash_arm([enroll[uid] for uid in subjects], arm, key, overlap,
                         recognition[arm], M, q, A).astype(np.int64),
                device=DEVICE)
            if not bool((stored == targets).all()):
                raise RuntimeError(
                    f"{modality}: attack targets do not equal the stored "
                    f"template; the attack would be aiming at the wrong thing."
                )
            print("    assertion 2 OK: attack targets equal the stored "
                  "templates, so a perfect solution exists in the search space")

        guess_generator = torch.Generator(device="cpu")
        guess_generator.manual_seed(H(S0, "INVERSION-GUESS", modality, arm))
        guess = torch.randn((n, d), generator=guess_generator, dtype=torch.float32)
        guess = (guess / guess.norm(dim=-1, keepdim=True)).to(DEVICE)
        guess_hits = (codes_of(arm, guess, key, overlap, recognition[arm], A)
                      == targets).sum(dim=-1)

        recovered, hits = invert_arm(
            arm, targets, key, overlap, recognition[arm], A, d,
            seed=H(S0, "INVERSION", modality, arm) % (2 ** 31))

        cross_true = codes_of(arm, truth, key, overlap, cross[arm], A)
        cross_rec = codes_of(arm, recovered, key, overlap, cross[arm], A)
        cross_hits = (cross_true == cross_rec).sum(dim=-1)
        cross_impostor = float(
            (cross_true[:, None, :] == cross_true[None, :, :]).sum(-1)
            [~torch.eye(n, dtype=torch.bool, device=DEVICE)].float().mean())

        cos_true = cosine_rows(recovered, truth)
        chance = cosine_rows(truth[:, None, :].expand(n, n, d).reshape(-1, d),
                             truth[None, :, :].expand(n, n, d).reshape(-1, d))
        chance = chance.reshape(n, n)[~torch.eye(n, dtype=torch.bool,
                                                 device=DEVICE)]

        out[arm] = {
            "hits": hits.cpu().numpy(),
            "guess_hits": guess_hits.cpu().numpy(),
            "cos": cos_true.cpu().numpy(),
            "cross_hits": cross_hits.cpu().numpy(),
            "cross_impostor_mean": cross_impostor,
            "cos_chance_mean": float(chance.mean()),
        }
        accepted = float((hits >= tau).float().mean())
        print(f"    {arm:<13} SAR {accepted * 100:6.2f}%   "
              f"mean hits {float(hits.float().mean()):6.2f}/{M}   "
              f"random guess {float(guess_hits.float().mean()):5.2f}/{M} "
              f"(chance {M / q:.1f})")

    return {"modality": modality, "subjects": subjects, "M": M, "tau": tau,
            "d": d, "k": k, "n": n, "arms": out, "chance": M / q}


def run_inversion(n_bootstrap=INV_N_BOOTSTRAP, confidence=INV_CONFIDENCE):
    output = DIR["runs"] / "inversion" / "inversion_result.json"
    if output.is_file():
        print("Resume: stored inversion result found; returning it unchanged.")
        return json.loads(output.read_text())

    result = {
        "schema": 1, "analysis": "full_knowledge_inversion",
        "adversary": "level 3: holds K*, R, the algorithm and the template",
        "attack": "annealed-softmax gradient descent on the unit sphere, "
                  "identical budget for every arm",
        "budget": {"restarts": INV_RESTARTS, "steps": INV_STEPS,
                   "lr": INV_LR, "temperature": [INV_TEMP0, INV_TEMP1]},
        "measures": "practical inversion resistance under this budget; "
                    "NOT information-theoretic irreversibility",
        "method_id": "identity_cluster_percentile_v1_paired",
        "n_bootstrap": int(n_bootstrap), "confidence": float(confidence),
        "master_seed": S0, "changes_any_seal": False, "modalities": {},
    }

    for modality in ("voice", "face"):
        print(f"\n{modality.upper()}")
        record = inversion_for(modality)
        n, tau, M = record["n"], record["tau"], record["M"]
        rng = np.random.default_rng(H(S0, "INVERSION-BOOTSTRAP", modality))

        accepted = {a: (record["arms"][a]["hits"] >= tau).astype(float)
                    for a in ARMS}
        draws = {a: [] for a in ARMS}
        contrasts = {a: [] for a in ARMS if a != "polyiom"}
        for _ in range(n_bootstrap):
            w = rng.multinomial(n, np.full(n, 1 / n)) / float(n)
            values = {a: float(w @ accepted[a]) for a in ARMS}
            for a in ARMS:
                draws[a].append(values[a])
            for a in contrasts:
                contrasts[a].append(values[a] - values["polyiom"])

        alpha = 1.0 - confidence

        def interval(v):
            lo, hi = np.quantile(v, [alpha / 2, 1 - alpha / 2])
            return [float(lo), float(hi)]

        result["modalities"][modality] = {
            "n_subjects": n, "M": M, "tau": tau, "d": record["d"],
            "k": record["k"],
            "arms": {a: {
                "SAR": float(accepted[a].mean()),
                "SAR_CI": interval(draws[a]),
                "mean_collisions": float(record["arms"][a]["hits"].mean()),
                "random_guess_collisions":
                    float(record["arms"][a]["guess_hits"].mean()),
                "chance_collisions": record["chance"],
                "cos_to_true": float(record["arms"][a]["cos"].mean()),
                "cos_chance": record["arms"][a]["cos_chance_mean"],
                "cross_key_collisions":
                    float(record["arms"][a]["cross_hits"].mean()),
                "cross_key_impostor_mean":
                    record["arms"][a]["cross_impostor_mean"],
            } for a in ARMS},
            "contrasts_vs_polyiom": {a: {
                "delta_SAR": float(accepted[a].mean()
                                   - accepted["polyiom"].mean()),
                "delta_SAR_CI": interval(contrasts[a]),
            } for a in contrasts},
        }

    atomic_json(output, result)
    print("\nWrote", output)
    return result


def inversion_report(result):
    for modality, data in result["modalities"].items():
        print(f"\n{modality.upper()}  n={data['n_subjects']}  M={data['M']}  "
              f"tau={data['tau']}")
        print(f"  {'arm':<14}{'SAR %':>22}{'hits/M':>10}{'guess':>8}"
              f"{'cos':>8}{'chance':>8}{'xkey':>7}{'xkey imp':>10}")
        for arm, v in data["arms"].items():
            print(f"  {arm:<14}{v['SAR'] * 100:7.2f} "
                  f"[{v['SAR_CI'][0] * 100:5.2f},{v['SAR_CI'][1] * 100:6.2f}]"
                  f"{v['mean_collisions']:10.1f}"
                  f"{v['random_guess_collisions']:8.1f}"
                  f"{v['cos_to_true']:8.3f}{v['cos_chance']:8.3f}"
                  f"{v['cross_key_collisions']:7.1f}"
                  f"{v['cross_key_impostor_mean']:10.1f}")
        chance = list(data["arms"].values())[0].get("chance_collisions")
        if chance:
            print(f"  a random unit vector lands on {chance:.1f} of "
                  f"{data['M']} buckets by chance; 'guess' should sit near it")
        print("  contrasts (arm minus proposed; interval excluding 0 is firm)")
        for arm, c in data["contrasts_vs_polyiom"].items():
            lo, hi = c["delta_SAR_CI"]
            firm = "FIRM" if (lo > 0 or hi < 0) else "not distinguishable"
            print(f"    {arm:<14} dSAR {c['delta_SAR'] * 100:+7.2f} %  "
                  f"[{lo * 100:+7.2f},{hi * 100:+7.2f}]  {firm}")
    print("\n  A POSITIVE dSAR means that arm is EASIER to invert than the")
    print("  proposed method, i.e. the polynomial helped. 'cos' against")
    print("  'chance' says whether the biometric itself was recovered;")
    print("  'xkey' against 'xkey imp' says whether the attack found the")
    print("  subject or merely a preimage of this one hash.")


print("Inversion evaluation ready.")

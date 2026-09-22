"""Run the whole pipeline end to end on synthetic embeddings.

The real embeddings are derived from LFW, LibriSpeech and VCTK and are not
ours to redistribute, so without this nobody could execute the code at
all. This generates stand-in identities with the same shape as the voice
data (d=192), runs all three arms through hardening, hashing, matching and
the metrics, and prints a table.

THE NUMBERS THIS PRINTS ARE NOT THE PAPER'S NUMBERS. They come from
Gaussian clusters, not from people. Use it to confirm the code runs and to
read the pipeline, not as evidence of anything. The paper's numbers are in
results/ and are checked by `run.py verify`.

What it covers: hardening, hashing, matching, recognition and
unlinkability, for all three arms.

What it does NOT cover: revocability. The paper's result there rests on
the inversion attack, and the reason the arms differ is that the attack
recovers the true embedding well from an `iom_only` template (cosine
0.913) and poorly from a `polyiom` one (0.222). A recovered embedding
survives re-keying; a vector that merely collides under the old key does
not. Comparing templates across keys, which is what this demo can do
cheaply, does not show that. See code/runtime/inversion_only.py and
revocation_only.py for the real thing.
"""

import numpy as np

from . import core, metrics


def synthetic_identities(n_subjects=58, n_probes=10, d=192, spread=1.15,
                         seed=core.MASTER_SEED):
    """Identity clusters: a mean per subject, probes scattered around it.

    `spread` sets within-subject variation relative to between-subject,
    which is what decides how separable the population is.
    """
    rng = np.random.default_rng(seed)
    means = rng.standard_normal((n_subjects, d)).astype(np.float32)
    enrol = core.l2(means)
    probes, owners = [], []
    for s in range(n_subjects):
        noise = rng.standard_normal((n_probes, d)).astype(np.float32) * spread
        probes.append(core.l2(means[s] + noise))
        owners.extend([s] * n_probes)
    return enrol, np.concatenate(probes), np.asarray(owners)


def fresh_key(rng):
    return (rng.standard_normal(core.G).astype(np.float32),
            rng.integers(1, 4, core.G))


def run(n_subjects=58, n_probes=10, d=192, M=128, q=32, overlap=1,
        spread=1.15, seed=core.MASTER_SEED):
    print("SYNTHETIC DATA. These numbers are not the paper's; they come")
    print("from Gaussian clusters. Run `python3 run.py verify` for those.\n")

    rng = np.random.default_rng(seed)
    enrol, probes, owners = synthetic_identities(n_subjects, n_probes, d,
                                                 spread=spread, seed=seed)
    k = core.output_length(d, overlap)
    print(f"{n_subjects} identities, {len(probes)} probes, d={d}, "
          f"M={M}, q={q}, o={overlap} -> hardened length k={k}\n")

    key = fresh_key(rng)
    A = rng.standard_normal((d, k)).astype(np.float32)
    tensor_a = rng.standard_normal((M, q, k)).astype(np.float32)
    tensor_b = rng.standard_normal((M, q, k)).astype(np.float32)   # 2nd key
    tensor_iom = rng.standard_normal((M, q, d)).astype(np.float32)
    tensor_iom_b = rng.standard_normal((M, q, d)).astype(np.float32)

    print(f"{'arm':<14}{'EER':>9}{'tau*':>7}{'TAR':>9}{'FMR':>9}"
          f"{'D_sys':>9}{'cross-key':>11}")
    print("-" * 68)
    rows = {}
    for arm in core.ARMS:
        ta, tb = ((tensor_iom, tensor_iom_b) if arm == "iom_only"
                  else (tensor_a, tensor_b))
        e = core.hash_arm(enrol, arm, key, overlap, ta, M, q, A)
        p = core.hash_arm(probes, arm, key, overlap, ta, M, q, A)
        scores = core.collisions(p, e)

        mask = np.zeros_like(scores, dtype=bool)
        mask[np.arange(len(owners)), owners] = True
        gen = core.histogram(scores[mask], M)
        imp = core.histogram(scores[~mask], M)
        e_rate, tau = metrics.eer(gen, imp)

        # Re-key: the same people enrolled again under a different key.
        # A revoked template should now behave like a stranger's.
        e2 = core.hash_arm(enrol, arm, fresh_key(rng), overlap, tb, M, q, A)
        cross = core.collisions(e, e2)
        mated = core.histogram(cross.diagonal(), M)
        nonmated = core.histogram(cross[~np.eye(n_subjects, dtype=bool)], M)

        rows[arm] = dict(EER=e_rate, tau=tau,
                         TAR=metrics.tar_at(gen, tau),
                         FMR=metrics.fmr_at(imp, tau),
                         dsys=metrics.dsys(mated, nonmated),
                         still_in=metrics.prar(cross.diagonal(), tau))
        r = rows[arm]
        print(f"{arm:<14}{r['EER'] * 100:8.3f}%{r['tau']:7d}"
              f"{r['TAR'] * 100:8.2f}%{r['FMR'] * 100:8.3f}%"
              f"{r['dsys']:9.4f}{r['still_in'] * 100:10.1f}%")

    print("\n'cross-key' is the share of subjects whose old template still")
    print("reaches the threshold when compared against their re-keyed")
    print("enrolment. It should be near zero for every arm, and is.")
    print()
    print("This is NOT the paper's PRAR and does not reproduce the")
    print("revocability finding. There the attacker first reconstructs an")
    print("input from the old template, and the arms differ because that")
    print("reconstruction recovers the true embedding from an iom_only")
    print("template and not from a polyiom one. Running that needs the real")
    print("embeddings; see code/runtime/revocation_only.py.")
    return rows

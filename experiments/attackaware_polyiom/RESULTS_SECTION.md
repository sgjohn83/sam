# Results — draft section

Drafting note on the structure. The study has two classes of analysis and
the section is built so a reader can never confuse them:

- **Confirmatory.** The pre-registered pipeline: identity-disjoint
  50/42/58 split, operating points selected on development identities and
  sealed, then held-out and external evaluation. §5.1–5.3.
- **Secondary.** Three analyses added after the sealed results were read:
  the hardening ablation, the inversion evaluation, and the revocation
  test. §5.4–5.6. Each was itself specified before it was run, each ran at
  the already-sealed operating point, and none re-opened selection or
  altered a seal. They are nonetheless not part of the pre-registration and
  are labelled accordingly throughout.

Numbers in brackets are 95% confidence intervals from an identity-cluster
percentile bootstrap (2000 replicates). Where a contrast is reported, the
bootstrap is paired: one resampling is applied to every arm, so the
interval on a difference accounts for the arms sharing identities. The
revocation analysis resamples keys as well as identities.

---

## 5.1 Sealed operating points

Configurations were selected on the 42 development identities by the rule
*lowest D_sys subject to a recognition floor*, with ties broken by EER,
then M, then q, then o.

| | M* | q* | o* | τ* | EER | TAR | D_sys | eligible |
|---|---|---|---|---|---|---|---|---|
| Voice | 128 | 32 | 1 | 37 | 0.952% | 95.238% | 0.052519 | 30 / 80 |
| Face | 256 | 32 | 1 | 68 | 2.839% | 86.260% | 0.133100 | 13 / 80 |

The voice floor (EER ≤ 1%, TAR ≥ 95%) was unattainable for face: across all
80 face configurations the best achievable EER was 2.29% and the best
achievable TAR was 90.08%, so the eligible set was empty. A relaxed face
floor of EER ≤ 3%, TAR ≥ 85% was therefore fixed — the tightest floor that
still selects from a non-trivial pool — **before any held-out identity was
read**, and the deviation and its reason are recorded in the seal. At a
floor of 3% / 90% exactly one configuration survives, so that choice would
have been an artifact of the grid and its D_sys (0.166) is worse in any
case.

## 5.2 Generalisation to held-out identities

The sealed configuration and threshold were applied unchanged to the 58
evaluation identities.

| | EER | TAR at τ* | FMR at τ* | D_sys |
|---|---|---|---|---|
| Voice | 1.928% [1.092, 2.919] | 93.966% [89.655, 97.414] | 0.185% [0.028, 0.480] | 0.0884 [0.0708, 0.2185] |
| Face | 4.799% [1.945, 10.345] | 82.239% [72.767, 89.933] | 0.041% [0.000, 0.218] | 0.1508 [0.1225, 0.2822] |

Voice EER rose from 0.952% on development to 1.928% held out, and the
development value lies outside the held-out interval; the degradation is
firm and the system does not meet its own 1% floor on unseen identities.

No other development-to-held-out difference is supported. In particular the
face development EER (2.839%) lies inside the held-out interval, as does
the 3% floor, so **neither face degradation nor a face floor breach can be
claimed**. Face is reported descriptively throughout: 58 identities with
single-sample enrolment yield 259 genuine trials and an EER interval
spanning a five-fold range.

## 5.3 External validation (voice)

The sealed voice system was applied to 110 VCTK speakers, read after all
internal analysis was complete.

| | EER | TAR at τ* | FMR at τ* | D_sys |
|---|---|---|---|---|
| External | 2.798% [1.992, 3.807] | 89.000% [85.727, 91.727] | 0.377% [0.202, 0.622] | 0.0803 [0.0603, 0.1551] |

All four external intervals overlap their held-out counterparts, so **no
held-out-to-external difference is supported**. EER, TAR and FMR all moved
in the unfavourable direction, but they are three functions of the same two
score distributions and constitute one observation, not three.

One external finding is firm: the entire FMR interval lies above the 0.1%
design target, so the sealed threshold does not meet that target on the
external corpus. The threshold was selected to balance EER and TAR on
development identities; operating at a fixed FMR requires a different
threshold policy, which we do not fit here because doing so on evaluation
data is precisely what the sealed protocol exists to prevent.

Unlinkability transfers: the external D_sys interval is tighter than and
contained within the held-out interval.

## 5.4 What the hardening stage costs *(secondary)*

The sweep varies M, q and o, all of which are IoM-GRP parameters — o is the
hardening window overlap, which only sets the output length. No condition
in the pre-registered study removes the polynomial. We therefore added one
at the sealed (M*, q*, o*), with two baselines:

- `iom_only` — IoM-GRP applied to the embedding directly;
- `randproj_iom` — a fixed random linear map to the same output dimension
  k, then IoM-GRP.

The second baseline is necessary because hardening also reduces
dimensionality (face 512 → 128, voice 192 → 48); without it, *the
polynomial helps* and *a lower projection dimension helps* cannot be
separated.

**Voice, held-out:**

| arm | EER | D_sys | TAR at matched FMR |
|---|---|---|---|
| PolyIoM | 1.928% [1.110, 2.951] | 0.0884 [0.0694, 0.2206] | 93.97% |
| `iom_only` | **0.273%** [0.034, 0.568] | 0.0728 [0.0581, 0.1916] | **99.66%** |
| `randproj_iom` | 0.700% [0.305, 1.379] | 0.1132 [0.0832, 0.2209] | 98.97% |

Both EER contrasts are firm and both favour the baseline: −1.655 pp
[−2.563, −0.903] for `iom_only` and −1.228 pp [−2.187, −0.285] for
`randproj_iom`. Every D_sys contrast is not distinguishable.

The three arms decompose the cost. Removing the polynomial but keeping the
full embedding gives 0.273%; reducing to k = 48 with a random linear map
gives 0.700%, so the dimension change accounts for +0.427 pp; the keyed
polynomial accounts for a further +1.228 pp. **The polynomial costs
approximately 2.9 times more recognition accuracy than the dimensionality
reduction it performs**, and 5.7 pp of TAR at the sealed operating FMR.

No face contrast is distinguishable, though every face point estimate also
favours a baseline.

## 5.5 What the hardening stage does not buy *(secondary)*

We evaluated inversion under a level-3 adversary holding K*, R, the
algorithm and the stored template — the worst case, and the one an
irreversibility claim must survive, since an adversary who has breached the
database holds the template. The attack is annealed-softmax gradient
descent on the unit sphere against the stored bucket indices. The
polynomial is differentiable, so the identical attack at an identical
budget (5 restarts × 800 steps, fixed in advance) runs against all three
arms; no arm receives a surrogate the others do not.

**Every template, under every arm, on both modalities, was inverted to
acceptance: SAR = 100%, with contrasts of exactly zero.** The scheme is not
irreversible under full knowledge, and the polynomial confers no
acceptance-level protection.

SAR saturated — the attack reaches 128 of 128 buckets against a threshold
of 37 — so the pre-specified headline metric is null but uninformative. The
pre-specified secondary measures discriminate:

| arm | mean collisions | cosine to true embedding (chance) |
|---|---|---|
| PolyIoM | 128.0 / 128 | **0.222** [0.196, 0.248] (0.120) |
| `iom_only` | 128.0 / 128 | **0.913** [0.910, 0.916] (0.120) |
| `randproj_iom` | 125.7 / 128 | 0.490 [0.482, 0.498] (0.120) |

Against `iom_only` the attack recovers the embedding almost exactly.
Against PolyIoM it does not. The cosine contrasts are firm.

The two results are consistent because **the system matches on the hardened
vector, not on the embedding.** The attack recovers the hardened vector
exactly — that is what 128 of 128 collisions means — while recovering
comparatively little of the embedding. The keyed polynomial hides the
biometric but not the representation actually compared.

## 5.6 What enables revocability *(secondary)*

Since the reconstruction does not recover the embedding, we asked whether
it survives re-enrolment. Each subject is re-enrolled under fully re-issued
parameters — a fresh polynomial key and projection for PolyIoM, a fresh
linear map and projection for `randproj_iom`, a fresh projection for
`iom_only` — and the attacker's reconstruction, built from the *old*
template, is presented. The attacker does not re-attack.

We report **PRAR**, the post-revocation acceptance rate, over 40 fresh key
sets, with intervals resampling keys as well as identities.

| voice | PRAR | per-key median / max | keys failing for >=50% of subjects |
|---|---|---|---|
| PolyIoM | 7.50% [2.11, 14.44] | 0.00% / 89.66% | 2 of 40 |
| `iom_only` | **100.00%** [100, 100] | 100% / 100% | **40 of 40** |
| `randproj_iom` | 5.73% [4.01, 7.63] | 6.90% / 13.79% | **0 of 40** |

| face | PRAR | per-key median / max | keys failing for >=50% of subjects |
|---|---|---|---|
| PolyIoM | 25.60% [13.02, 38.58] | 0.00% / 100.00% | 10 of 40 |
| `iom_only` | **100.00%** [100, 100] | 100% / 100% | **40 of 40** |
| `randproj_iom` | 2.89% [1.77, 4.27] | 1.72% / 8.62% | **0 of 40** |

**Keyed compression is necessary for revocability.** Applied to the raw
embedding, IoM-GRP fails completely: every stolen template remains a valid
credential after re-keying, for all 40 key sets on both modalities
(contrasts +92.5 pp and +74.4 pp, both firm). This follows from §5.5 — the
attack recovers the embedding itself, so re-keying the projection cannot
help.

**That the polynomial is the right compression is not supported.** PolyIoM
is bimodal: its median per-key PRAR is 0.00% on both modalities, but it
fails catastrophically for a minority of fresh keys — 2 of 40 on voice, 10
of 40 on face, reaching 100%. `randproj_iom` never does: across all 80 key
sets none failed outright, and its worst case leaks 13.79%. The voice PRAR
contrast is not distinguishable (−1.767 pp [−8.793, +3.967]); the face
contrast is firm and favours the linear map (−22.716 pp [−35.864,
−9.996]).

Operationally, unpredictable total failure is worse than a small,
consistent leak.

## 5.7 Summary of evidence

| Property | Does keyed polynomial hardening help? |
|---|---|
| Recognition accuracy | No — costs 1.23 pp EER over a linear map of equal output dimension (firm) |
| Unlinkability (D_sys) | No — no contrast distinguishable |
| Inversion resistance | No — SAR 100% for every arm |
| Concealing the embedding | Yes — cosine 0.222 against 0.913 (firm) |
| Revocability | Keyed compression is necessary; the polynomial specifically is not better, and is worse on face (firm) |

Taken together: **keyed compression before IoM-GRP hashing is necessary for
revocability, a keyed random linear projection is sufficient, and on this
evidence the polynomial is not preferable to it.**

---

# 6 Limitations

1. **Statistical power.** All held-out inference rests on 58 identities.
   Face yields 259 genuine trials and an EER interval spanning a five-fold
   range; face results are descriptive and no face comparison in §5.2 is
   claimed.
2. **One external corpus, one modality.** VCTK validates voice. No external
   face corpus was available, so face has no external estimate.
3. **One attack family.** §5.5 measures practical inversion resistance
   under a stated budget, not information-theoretic irreversibility. A
   perfect solution provably exists in the search space, so failure to find
   it would be an optimisation-hardness result. A stronger attack can only
   increase attacker success, so the direction of the finding is safe; the
   magnitudes are lower bounds.
4. **Fresh-key construction.** K** is resampled from K*'s own coefficient
   and exponent values, not re-drawn through the Stage A selection that
   produced K*. This is appropriate for the question asked but means the
   fresh keys are not distributed exactly as deployed keys would be.
5. **Unexplained failure mode.** We cannot currently explain why 12 of 80
   fresh key sets produce catastrophic PRAR for PolyIoM. The failing keys
   are not degenerate — all passed a discrimination check — and the
   voice/face asymmetry (5% against 25%) is likewise unexplained.
6. **The preferred configuration was never sealed.** `randproj_iom` was
   introduced as an ablation arm. It has no operating point selected under
   the pre-registered rule and no external validation, so the
   recommendation in §5.7 rests on held-out comparison at PolyIoM's sealed
   configuration rather than on the full protocol.
7. **Asymmetric enrolment.** Face enrolment is a single embedding; voice
   enrolment is the L2-normalised mean of five. Deliberate, and a source of
   the modality difference in §5.2.
8. **Dataset provenance.** The CFP-FP exclusion list was obtained from a
   third-party mirror whose release metadata could not be verified against
   the original host; its scope is exact-name overlap exclusion, not alias
   resolution.

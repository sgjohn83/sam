# AttackAware PolyIoM v1.1.4 — results summary

Protocol **1.1.1**, master seed **2026**. Compiled 17 Sep 2026.
Every number below is transcribed from a sealed artifact in this project;
the artifact and its hash are listed in **Artifact inventory**.

Read **Firm findings** and **Do not claim** before writing anything.

---

## 1. What was run

| Stage | State |
|---|---|
| LFW prep, split, embeddings, face trials | sealed |
| LibriSpeech prep, speaker seal, embeddings | sealed |
| LFW ∩ CFP overlap exclusion | sealed |
| Self-tests v1.1.4 | passed |
| 80-configuration development sweep, face | sealed 16 Sep |
| 80-configuration development sweep, voice | sealed 16 Sep |
| Voice operating point | sealed |
| Face operating point | sealed 17 Sep |
| Held-out evaluation, 58 identities, both modalities | done 17 Sep |
| Held-out bootstrap CIs | done 17 Sep |
| VCTK preparation, 110 speakers | done 17 Sep |
| External voice evaluation | done 17 Sep |
| External bootstrap CIs | done 17 Sep |
| External face evaluation | **not run** — see §8 |

Identity budget per modality: **50 background / 42 development / 58 evaluation**.
The 58 evaluation identities were read for the first time on 17 Sep, after
both operating points were sealed.

---

## 2. Selection rule and operating points

Rule `min_dsys_subject_to_eer_floor_v1`: among configurations meeting the
recognition floor, take the lowest `Dsys_DEV`; ties broken by EER, then M,
then q, then o. Rationale: recognition beyond the floor is not the
contribution, unlinkability is.

### Voice — floor met unchanged

| | |
|---|---|
| Configuration | **M=128, q=32, o=1** |
| Floor applied | EER ≤ 0.01, TAR ≥ 0.95 |
| Eligible configurations | 30 of 80 |
| EER (dev) | 0.952% |
| TAR (dev) | 95.238% |
| Dsys (dev) | 0.052519 |
| Threshold `c_tau_DEV` | 37 |

### Face — floor relaxed, deviation sealed

The voice floor is **unattainable** for face. Across all 80 face
configurations the best EER is **2.29%** (floor needs ≤ 1.00%) and the best
TAR is **90.08%** (floor needs ≥ 95.00%), so the eligible set is empty. No
`eer_max ≤ 0.02` admits anything either.

What the attainable floors admit:

| eer_max | tar_min | eligible | min Dsys | best configuration |
|---|---|---|---|---|
| 0.03 | 0.90 | 1 | 0.166 | M=256 q=8 o=3 — EER 2.67%, TAR 90.08% |
| **0.03** | **0.85** | **13** | **0.133** | **M=256 q=32 o=1 — EER 2.84%, TAR 86.26%** |
| 0.05 | 0.85 | 20 | 0.101 | M=256 q=16 o=4 — EER 3.05%, TAR 85.11% |
| 0.05 | 0.80 | 35 | 0.044 | M=64 q=32 o=4 — EER 4.01%, TAR 81.68% |

0.03 / 0.85 was chosen as the tightest floor that still selects from a real
pool. At 0.03 / 0.90 exactly one configuration survives, so the choice
would be an artifact of the grid, and its Dsys (0.166) is worse anyway.

| | |
|---|---|
| Configuration | **M=256, q=32, o=1** |
| Floor applied | EER ≤ 0.03, TAR ≥ 0.85 |
| Rule id | `min_dsys_subject_to_eer_floor_v1_face_eer0.03_tar0.85` |
| Eligible configurations | 13 of 80 |
| EER (dev) | 2.839% |
| TAR (dev) | 86.260% |
| Dsys (dev) | 0.133100 |
| Threshold `c_tau_DEV` | 68 |

The floor was fixed from face's own development distribution **before any
held-out identity was read**, and the deviation reason is stored in the
seal. Quote the 2.29% / 90.08% figures in the paper — they are the evidence
that the voice floor was unattainable, and the sealed reason text omits them.

---

## 3. Development → held-out (58 unseen identities)

Threshold carried over unchanged. Re-fitting on held-out data would leak it.

### Face — M=256 q=32 o=1, τ=68, 259 genuine / 14,763 impostor

| Metric | Development | Held-out | 95% CI |
|---|---|---|---|
| EER | 2.839% | **4.799%** | [1.945, 10.345] |
| TAR @ τ | 86.260% | **82.239%** | [72.767, 89.933] |
| FMR @ τ | 0.093% | **0.041%** | [0.000, 0.218] |
| FNMR @ τ | — | 17.761% | — |
| Dsys | 0.133100 | **0.150803** | [0.122519, 0.282221] |
| `c_EER` | — | 31 | — |

### Voice — M=128 q=32 o=1, τ=37, 580 genuine / 33,060 impostor

| Metric | Development | Held-out | 95% CI |
|---|---|---|---|
| EER | 0.952% | **1.928%** | [1.092, 2.919] |
| TAR @ τ | 95.238% | **93.966%** | [89.655, 97.414] |
| FMR @ τ | 0.081% | **0.185%** | [0.028, 0.480] |
| FNMR @ τ | — | 6.034% | — |
| Dsys | 0.052519 | **0.088431** | [0.070803, 0.218493] |
| `c_EER` | — | 26 | — |

Trial counts match the protocol exactly for voice: 58 identities × 10
probes = 580 genuine, 58 × 57 × 10 = 33,060 impostor.

---

## 4. External evaluation — VCTK-Corpus-0.92

VCTK was read only after the internal method was frozen. It was never used
for key selection, thresholds, or configuration choice.

**Preparation:** 110 of 110 speakers kept, **0 skipped**, 1,650 utterances
(15 per speaker). mic1 only. 48 kHz → 16 kHz by `scipy.signal.resample_poly`
(exact anti-aliased 1/3 decimation), then the sealed validity gate
`post_resample_samples >= 24000` applied in that order. First 15 valid
utterances per speaker in sorted filename order — reproducible without
consuming a seed. Enrolment is the L2-normalised mean of ranks 0–4; ranks
5–14 are probes, identical to the voice development protocol.

### Voice — M=128 q=32 o=1, τ=37, 110 subjects, 1,100 genuine / 119,900 impostor

| Metric | Held-out (58) | External (110) | External 95% CI |
|---|---|---|---|
| EER | 1.928% | **2.798%** | [1.992, 3.807] |
| TAR @ τ | 93.966% | **89.000%** | [85.727, 91.727] |
| FMR @ τ | 0.185% | **0.377%** | [0.202, 0.622] |
| FNMR @ τ | 6.034% | 11.000% | — |
| Dsys | 0.088431 | **0.080300** | [0.060294, 0.155097] |
| `c_EER` | 26 | 28 | — |

**Every held-out ↔ external interval overlaps.** No difference between the
two is statistically firm. Overlap bands: EER 1.99–2.92, TAR 89.66–91.73,
FMR 0.202–0.480, Dsys 0.071–0.155.

The external Dsys interval is **materially tighter** than the held-out one
(width 0.095 vs 0.147), because 110 identities beat 58.

---

## 5. Confidence interval method

`identity_cluster_percentile_v1`, applied identically to the held-out and
external results so the two are directly comparable.

| | |
|---|---|
| Resampling unit | identity |
| Replicates | 2,000 |
| Interval | two-sided percentile, 95% |
| Threshold policy | development threshold carried unchanged |
| Recognition weighting | genuine trials of identity *i* carry *w_i*; ordered impostor pairs carry *w_a · w_b* |
| Unlinkability weighting | mated scores carry identity weights; ordered non-mated pairs carry product weights; same-identity pairs excluded |
| Validation | point estimates reconstructed and matched against the sealed results |

Identities are the independent unit — the 10 genuine trials of one speaker
are correlated, so trial-level resampling would give falsely narrow
intervals. Multinomial weights are used rather than a physical resample
because drawing one identity twice would compare a speaker against itself
and count it as an impostor trial.

**Methods caveat to state:** percentile bootstrap at 58–110 clusters can
run slightly anti-conservative.

---

## 6. Firm findings

Deterministic, from the sealed sweep:

1. **Face cannot meet the voice floor.** Best face EER 2.29% against a 1%
   ceiling; best face TAR 90.08% against a 95% floor; eligible set empty.

Statistical — the reference value lies outside the 95% interval:

2. **Voice EER degrades from development to unseen identities.** Dev 0.952%
   sits below the held-out lower bound of 1.092%.
3. **Voice unlinkability degrades from development to unseen identities.**
   Dev Dsys 0.052519 sits below the held-out lower bound of 0.070803.
4. **Voice breaches its 1% pre-registered EER floor on unseen identities.**
   Held-out CI [1.092, 2.919] lies entirely above 1%.
5. **Voice breaches the 1% floor on the external corpus too.** External CI
   [1.992, 3.807] lies entirely above 1%.
6. **The carried threshold breaches the FMR design target externally.**
   `target_fmr = 0.001`; external FMR CI [0.202%, 0.622%] lies entirely
   above 0.1%. The operating point does not hold its FMR target off the
   development corpus.
7. **Unlinkability transfers across identities and across corpora.**
   External Dsys 0.080300 [0.060294, 0.155097] on 110 unseen speakers from
   a different corpus — slightly better than held-out, overlapping it, and
   on a tighter interval.

Finding 7 is the headline: unlinkability is the contribution, and it holds.
Finding 6 is the crisp negative result.

---

## 7. Do not claim

Each of these has the reference value **inside** the interval, so the data
cannot distinguish it.

| Claim | Why not |
|---|---|
| Face EER degrades dev → held-out | Dev 2.839% is inside [1.945, 10.345] |
| Face unlinkability degrades dev → held-out | Dev 0.133100 is inside [0.122519, 0.282221] |
| Face breaches its 3% floor on held-out | 3% is inside [1.945, 10.345] |
| TAR is significantly lost dev → held-out, either modality | Face dev 86.260% inside [72.767, 89.933]; voice dev 95.238% inside [89.655, 97.414] |
| Voice breaches the FMR target on **held-out** | 0.1% is inside [0.028, 0.480] — firm externally only |
| Voice unlinkability beats face | Intervals overlap: voice to 0.218, face from 0.123 |
| Any held-out → external difference | All four intervals overlap (§4) |

**Face is under-powered.** 58 identities with single-sample enrolment yields
259 genuine trials and an EER interval spanning a 5× range. Report face
descriptively and state the limitation — it is a stronger position than
asserting a degradation the data does not support.

**A caution:** EER, TAR and FMR all shifted in the "worse" direction from
held-out to external. Do not treat that as three independent signals — all
three are functions of the same two score distributions, so it is one
observation.

---

## 8. Retracted during analysis

Both were stated earlier in this project and are **not supported**:

- **"The threshold transfers within corpus but degrades across corpus."**
  Based on comparing the external TAR point estimate (89.00%) against the
  held-out lower bound (89.66%). Once the external interval was computed,
  [85.727, 91.727] overlaps the held-out interval. Not supported.
- **"Voice exceeds its FMR target."** True of the held-out point estimate
  (1.85× target) but the held-out interval contains 0.1%. Firm on the
  external corpus only, as §6.6.

---

## 9. Disclosures for the paper

1. **Face floor deviation.** The voice rule was unattainable for face;
   quote best EER 2.29% and best TAR 90.08% as the evidence. Sealed in
   `operating_point_face.json` under `rule.deviation_reason`.
2. **CFP-FP provenance.** The 500-name list came from the Kaggle mirror
   `chinafax/cfpw-dataset` version 1; the original host was never reached.
   The seal records `release_metadata_from_mirror_original_host_not_verified`.
   Scope is exact-name overlap exclusion, not alias resolution.
3. **Asymmetric enrolment.** Face enrolment is a single embedding (LFW
   provides as few as three images per identity); voice enrolment is the
   L2-normalised mean of ranks 0–4. Deliberate; belongs in methods.
4. **No external face evaluation.** CFP-FP is sealed as a name list, not an
   embedding corpus. Voice-only external validation is the scope. If face
   is presented as a co-equal claim rather than a secondary demonstration,
   this gap needs closing.
5. **Bootstrap caveat.** Percentile intervals at 58–110 clusters can run
   slightly anti-conservative.
6. **Face statistical power.** 58 held-out identities, 259 genuine trials.
   Note that an external face corpus would add a better-powered external
   estimate but would not narrow the held-out interval, which is fixed by
   the sealed 50/42/58 split.

---

## 10. Artifact inventory

### Configuration and runtime

| Artifact | Key contents |
|---|---|
| `seal/config_v1_1_4.json` | protocol 1.1.1, seed 2026, splits 50/42/58, g=5, M∈{32,64,128,256}, q∈{4,8,16,32}, o∈{0..4}, reference M=128 q=16 o=2, `target_fmr` 0.001 |
| `seal/latest_runtime_environment.json` | Tesla T4, CUDA 12.8, cuDNN 91900, torch 2.11.0+cu128, torchaudio 2.11.0+cu128, torchvision 0.26.0+cu128, speechbrain 1.1.1, facenet-pytorch 2.6.0, av 18.1.0, numpy 2.1.3, pandas 2.2.3, Python 3.13.15 |

### Sweeps

| Artifact | sha256 |
|---|---|
| `runs/sweep/face/sweep_80.csv` | `89f28dc86a7844144afdb0be9ab7f2f2a4625ccc908d81993788083e07f079e2` |
| `runs/sweep/voice/sweep_80.csv` | `819232a6f9868cda2f4aea245a2da769400980e6141ca47e5c17eae3956abac1` |

### Results

| Artifact | Note |
|---|---|
| `seal/operating_point_voice.json` | M=128 q=32 o=1, τ=37, 30 eligible |
| `seal/operating_point_face.json` | M=256 q=32 o=1, τ=68, 13 eligible, deviation sealed |
| `runs/heldout/face/heldout_result.json` | sha256 `90b00186c204fc9f112a4d111717a22181ca0cefea027fdaf32db03782a88108` |
| `runs/heldout/voice/heldout_result.json` | sha256 `33dc476b920dabf5b9ee47951cb806b69fde87ee790875d7b95cca699e99ee15` |
| `runs/heldout/generalisation_table.csv` | both modalities, dev vs held-out |
| `runs/heldout/heldout_confidence.json` | 2,000 replicates; seeds — face 6353163838588607505, voice 4722292304065993655 |
| `runs/external/voice/external_result.json` | sha256 `bbafcd017e3546031d2253c40e568fb14955515f66e0a189d21b95b675a25b27` |
| `runs/external/voice/external_confidence.json` | 2,000 replicates; seed 7693023472975363427 |

### External input provenance

| Item | Value |
|---|---|
| VCTK archive | 11,747,302,977 bytes |
| VCTK manifest | sha256 `3025b1d448e318ccde93c3becab392c15f075b128c260bcd3dbc4c61742a9705` |
| VCTK embeddings | sha256 `5fd9c3b6e71282bbbe890e2c7dfb01b4de00c7e4acac5ec156995709e495007a` |
| Voice polynomial key | sha256 `e5b716fa56c5f7c800b1efb3fdfdda4be36ff8f3d1ba95329de4dfc359337678` |
| Operating point (as applied externally) | sha256 `027e18fa7fa5de062c4a3a538b1a2a36391f1626bbb72e577ee510c94bffab58` |
| CFP name list | 500 names, metadata sha256 `dcbcd60c4b60ad7498d5ef2f7d5889b41700feb3ef3a9a93b392b7a38cdc2a9e` |

### Not used in any reported result

`cfp_reserved_test_embeddings.npz` from the September V10 pilot — 1,250
embeddings, 250 subjects, 512-D, InceptionResnetV1/vggface2, state sha256
`4b9c85869c3de4faa93b93f1f75b38187ea03f04b3dd31f8fd7256dcfea146e7`. Its
metadata records `external_test_opened: true`, so it is not a sealed
holdout. Excluded from every number above.

---

## 11. Validity notes

- `librispeech_validity`: `decode_mono_16k_nonempty_finite_no_duration_gate`
- `vctk_validity`: `mic1_post_resample_samples>=24000`
- `lfw_cfp_overlap`: `exact_case_sensitive_subject_identifier`
- Determinism: candidate 1 recomputed on 13 Sep matched its 7 Sep shard to
  16 digits (`rho_max`, TAR, `c_tau_BG` all identical).
- ECAPA checkpoint lineage: `seal/ecapa_checkpoints.json` records
  `cd70225b…` for `mean_var_norm_emb.ckpt` at revision `3d2520d6`,
  independently reproduced by the v1.1.5 pilot's forced re-download.

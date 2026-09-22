# Frameworks, models, corpora and compute

Everything here is copied from the sealed project's own stage records,
vendored in `results/environment/`. Nothing is reconstructed from memory.
Where a file records a hash, the hash is the fact; the prose is a reading
of it.

## Encoders

| | Face | Voice |
|---|---|---|
| Architecture | Inception-ResNet-v1 (FaceNet) | ECAPA-TDNN |
| Pretraining | VGGFace2 | VoxCeleb |
| Package | facenet-pytorch 2.6.0 | SpeechBrain 1.1.1 |
| Pin | package version | `speechbrain/spkrec-ecapa-voxceleb` @ `3d2520d6a433ff8e42cb7e80f0d5f23b912ca189`; `embedding_model.ckpt` sha256 `0575cb64…`, `mean_var_norm_emb.ckpt` sha256 `cd70225b…` (full hashes in `ecapa_checkpoints.json`) |
| Detection / front end | MTCNN (facenet-pytorch); no-face images excluded | 16 kHz mono; VCTK resampled from 48 kHz with `scipy.signal.resample_poly` |
| Input | 160 x 160, package prewhitening, L2-normalised | waveform |
| Output | 512-d | 192-d |
| Fine-tuned | no | no |

## Corpora and what was taken

| Corpus | Record | Facts |
|---|---|---|
| LFW, original `lfw.tgz` | `stage_lfw_raw.done.json`, `stage_lfw_embeddings.done.json` | 13,233 raw images (archive sha256 `055f7d9c…`); 7,581 valid after MTCNN; 900 identities with >= 3 valid |
| CFP-W names, exclusion only | `cfp_authoritative_metadata.json`, `lfw_split.json` | 500 subject names from a Kaggle mirror (original host not verified); 100 LFW identities removed by exact case-sensitive name match; exact names only, no alias resolution |
| LibriSpeech `train-clean-100` | `stage_libri_local.done.json`, `stage_libri_internal.done.json`, `stage_libri_embeddings.done.json` | archive md5 `2a93770f6d5c6c964bc36631d331a522`; 150 speakers x 15 utterances = 2,250 embeddings; validity = decodes mono 16 kHz, non-empty, finite, no duration gate |
| VCTK 0.92, `mic1` | `stage_vctk_manifest.done.json`, `stage_vctk_embeddings.done.json` | 11.7 GB archive; 110 speakers x 15 = 1,650 utterances, 0 speakers skipped; first N valid in sorted filename order; >= 24,000 samples after resampling (1.5 s); manifest and embedding hashes match `results/external/voice_external_result.json` |

Partition: 50 background / 42 development / 58 evaluation per modality,
master seed 2026, protocol 1.1.1 (`config_v1_1_4.json`).

## Configuration grid and attack budgets (`config_v1_1_4.json`)

- M in {32, 64, 128, 256}; q in {4, 8, 16, 32}; o in {0, 1, 2, 3, 4}; G = 5;
  80 configurations per modality; reference (128, 16, 2); target FMR 1e-3.
- Stage A key-search gate: 5 restarts x 2,000 Adam iterations, lr 0.01,
  betas (0.9, 0.999), eps 1e-8, init std 0.1; candidate budget 10,000
  (max 20,000); stage-1 floor rho <= 0.9 & TAR >= 0.95, stage-2 rho <= 0.85
  & TAR >= 0.90.
- Section 5.5 full-knowledge attack (from `results/inversion/`):
  5 restarts x 800 steps, lr 0.05, temperature 1.0 -> 0.05. Same budget for
  every arm. This is a different run from the Stage A gate.

## Software and compute

| Stage | Record | Python | torch | GPU |
|---|---|---|---|---|
| Embedding extraction (Sep 7) | `environment_extraction_cpu.json` | 3.13.15 | 2.11.0+cpu | none |
| Sweep, sealed evaluation, secondary analyses (Sep 16-17) | `runtime_environment.json` | 3.13.15 | 2.11.0+cu128 | Tesla T4, CUDA 12.8, cuDNN 9.19 |

Both: numpy 2.1.3, pandas 2.2.3, torchaudio 2.11.0, torchvision 0.26.0,
speechbrain 1.1.1, facenet-pytorch 2.6.0, av 18.1.0, glibc 2.39.

Hashing runs on CPU in every analysis regardless of GPU, with
`torch.use_deterministic_algorithms(True)` and cuDNN benchmarking off.
Every random draw is seeded from `H(master_seed, analysis_name, ...)`
(see `polyiom/core.py::H`).

Implemented by the authors, not imported: the polynomial hardening,
IoM-GRP hashing, collision matching, both bootstraps, the unlinkability
measures, and the attack. `run.py parity` checks the NumPy rewrite of the
pipeline against the PyTorch original.

This package itself was verified on Python 3.11.15 with numpy 2.4.6;
`run.py parity` additionally ran with torch 2.14.0 (CPU).

## Not pinned, and worth knowing

- facenet-pytorch's own metadata pins old torch releases; it was installed
  with `--no-deps` to avoid a silent torch downgrade. `runtime_deps_cells.py`
  in `code/` documents the check.
- MTCNN's detection thresholds and margin were the package defaults; the
  exact values are in the acquisition notebook in the project, not in a
  seal record.
- The LFW identification as the original archive rests on the sealed raw
  stage (13,233 images) and the acquisition notebook naming `lfw.tgz`; the
  archive sha256 is recorded so it can be checked against a fresh download.

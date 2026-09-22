# Reproducibility package — AttackAware PolyIoM v1.1.4

Everything needed to check the paper's numbers, and to rerun the analyses
that produced them.

```
run.py               one entry point: verify | demo | parity | all
verify.py            recomputes every number the paper reports, from results/
polyiom/             the pipeline as plain NumPy, runnable anywhere
  core.py            hardening, hashing, matching
  metrics.py         EER, D_link, D_sys, TAR, FMR, PRAR
  demo.py            end to end on synthetic data
  parity.py          checks core.py against the study's PyTorch code
results/             the stored outputs of each analysis
code/runtime/        the analysis code as the study ran it (*_only.py)
code/notebooks/      the Colab notebooks that load and run it
code/figures/        figure builders and the figure explanation text
tests/               29 unit tests for the pipeline and the metrics
REVIEWER.md          the five-minute path, and what we would raise ourselves
RUNBOOK.md           running and verifying, with expected output
DATA.md              what is not included, why, and the paper's statements
LICENSE              MIT (author name needs filling in)
CITATION.cff         how to cite (placeholders need filling in)
requirements.txt     numpy; torch and matplotlib are optional
MANIFEST.sha256      hashes of every file here
```

**Reviewing this for a journal? Start with `REVIEWER.md`.**

## Quickest possible start

```
python3 run.py verify     # no dependencies at all
python3 run.py all        # add numpy, and torch if you have it
```

`code/` is the study as it ran, in Colab against Google Drive. `polyiom/`
is the same pipeline as ordinary Python that runs anywhere, checked
against the original by `run.py parity`.

## 1. Check the numbers without running anything

```
python3 verify.py
```

Standard library only. No data, no network, no GPU, runs in under a second.
It reads `results/` and re-derives each figure the paper quotes: the sealed
operating points, the held-out and external results, all three secondary
analyses, and the cross-file consistency the sealing discipline requires.
Any mismatch prints `FAIL` and the script exits non-zero.

74 checks pass on the files as shipped.

What this does and does not establish. It is written independently of the
code that produced the results, so it catches a number transcribed wrongly
into the manuscript, an interval quoted with the wrong sign, or a result
file edited after the fact. It cannot catch an error inside the pipeline
itself. For that, rerun the analyses (section 3).

Three of its checks are worth knowing about because they are the ones that
would break first if anything drifted:

- `ablation and held-out report the same sealed voice EER` — the ablation
  ran at the sealed operating point, so its `polyiom` arm must reproduce
  the held-out result bit for bit. It does, to 1e-12.
- `inversion and revocation report the same voice polyiom cosine` — both
  analyses measure the same reconstruction, so they must agree exactly.
- `changed no seal` on all three secondary analyses.

## 2. What is in results/

| File | Produced by | Backs |
|---|---|---|
| `heldout/{voice,face}_heldout_result.json` | sealed evaluation | Sections 5.1, 5.2 |
| `external/voice_external_result.json` | external validation | Section 5.3 |
| `ablation/ablation_result.json` | `ABLATION.ipynb` | Section 5.4 |
| `inversion/inversion_result.json` | `INVERSION.ipynb` | Section 5.5 |
| `revocation/revocation_result.json` | `REVOCATION.ipynb` | Section 5.6 |

Each carries its own provenance: the master seed (2026), the number of
bootstrap resamples (2000), the confidence level, the bootstrap method
identifier, and `changes_any_seal: false`.

**Not included here.** The face and speaker embeddings, the frozen IoM
projection tensors, and `runs/scores/score_histograms.json` (417 KB, the
input to the four results figures). The embeddings are derived from LFW,
LibriSpeech and VCTK and are not ours to redistribute; the tensors and the
histograms are regenerated deterministically from the master seed by the
notebooks. `external_result.json` records SHA-256 hashes of the VCTK
embeddings and manifest so a rerun can be checked against ours.

## 3. Rerunning the analyses

Each analysis is a small notebook plus a self-contained runtime file. The
notebook mounts Drive, checks its inputs exist, executes the runtime, and
calls one function. The split exists so the code is reviewable as a file
rather than buried in notebook cells.

| Notebook | Runtime | Writes |
|---|---|---|
| `ABLATION` | `ablation_only.py` | `runs/ablation/ablation_result.json` |
| `INVERSION` | `inversion_only.py` | `runs/inversion/inversion_result.json` |
| `REVOCATION` | `revocation_only.py` | `runs/revocation/revocation_result.json` |
| `SCOREDUMP` | `scoredump_only.py` | `runs/scores/score_histograms.json` |
| `FIGURES` | `figures_only.py`, `docx_only.py` | the four results figures, and the docx |

Order matters only in two places: every analysis needs the sealed held-out
results first, and `FIGURES` needs `SCOREDUMP`.

Every analysis is read-only with respect to the study. None fits a
threshold, none re-opens selection, and each records `changes_any_seal:
false`. Each also resumes: if its output file already exists it is returned
unchanged rather than recomputed, so a rerun cannot silently overwrite a
sealed result.

Determinism: master seed 2026, `torch.use_deterministic_algorithms(True)`,
cuDNN benchmarking off, and every random draw seeded from a documented
function of the master seed and the analysis name. The hashing runs on CPU
so results do not depend on the GPU allocated.

## 4. Two definitions that are easy to misread

**"Keys failing outright"** in `revocation_result.json` means a key set
that leaves **at least half** the subjects' old templates still accepted
after re-keying. It does not mean all of them. For `polyiom` that is 12 of
80 key sets, of which 8 leave every subject exposed. `verify.py` checks
both numbers separately, because the difference is easy to lose and the
paper states both.

**The mated distribution is one measurement, not two.** Under the
unlinkability framework it is "same subject, two different keys"; under
revocability it is the pseudo-impostor distribution. Figures C and D show
the same data answering different questions, and the paper must not count
them as independent evidence.

## 5. Known limits of this package

- The face arm is descriptive. Its encoder caps the attainable equal error
  rate near 3%, and with 259 genuine comparisons the held-out interval
  spans a five-fold range.
- The unprotected voice baselines fall below one genuine error, so they
  are reported as one-sided bounds rather than point estimates.
- `randproj_iom`, which the paper recommends over the polynomial, was
  never itself put through the sealed selection protocol. It was only ever
  evaluated at the polynomial's operating point.
- One interval was retracted during the study. The first revocation
  analysis used 3 keys and bootstrapped identities only; with 40 keys and
  a two-level bootstrap over keys and identities the contrast it reported
  is not distinguishable. `verify.py` checks the corrected result.

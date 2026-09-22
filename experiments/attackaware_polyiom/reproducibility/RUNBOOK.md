# Running and verifying

Two independent levels. Level 1 checks the paper against the stored
results and needs nothing but Python. Level 2 regenerates those results
from the embeddings and needs Colab and the Drive project.

Do level 1 first. It takes a second and tells you whether the manuscript
matches the artifact.

---

## Level 1 — verify the paper's numbers (offline, ~1 second)

Requires Python 3.8 or newer. No packages, no data, no network, no GPU.

```
unzip AttackAware_PolyIoM_v1_1_4_reproducibility.zip
cd reproducibility
python3 verify.py
```

### Expected output

Five sections of `ok` lines, then:

```
========================================================================
74 checks passed, 0 failed
Every number the paper reports is reproduced from results/.
```

Exit code 0. Any failure prints `FAIL` on the offending line, lists the
failures at the end, and exits 1.

### Also check the files were not altered

```
sha256sum -c MANIFEST.sha256
```

Every line should read `OK` (23 files). On macOS use `shasum -a 256 -c`.

### Confirm the check is not vacuous

A verifier that passes no matter what is worthless. Break one number and
watch it fail:

```
python3 - <<'EOF'
import json
p = "results/heldout/voice_heldout_result.json"
d = json.load(open(p)); d["EER_HOLDOUT"] = 0.0175
json.dump(d, open(p, "w"), indent=2)
EOF
python3 verify.py; echo "exit code: $?"
```

You should see **two** failures, not one:

```
  FAIL voice held-out EER %                              1.7500  paper says 1.9280
  FAIL ablation and held-out report the same sealed voice EER  False  paper says True
exit code: 1
```

The second is the useful one. The ablation ran at the sealed operating
point, so its `polyiom` arm must equal the held-out result exactly; the
two files cannot disagree unless something was edited. Restore with:

```
git checkout results/heldout/voice_heldout_result.json   # or re-unzip
```

### What level 1 does and does not establish

It establishes that every number printed in the paper is present in the
stored results, with the right sign and at the stated precision, and that
the files agree with each other where the sealing discipline requires it.

It does not establish that the pipeline is correct. `verify.py` reads the
outputs; it does not recompute a hash, a bootstrap or an attack. For that,
level 2.

---

## Level 2 — regenerate the results (Colab)

### Before you start

Mount Drive fresh. Files added since your last mount are invisible
otherwise, and the notebooks will report them missing:

```python
from google.colab import drive
drive.flush_and_unmount()
drive.mount("/content/drive")
```

**Every analysis resumes.** If its output file already exists it is
returned unchanged rather than recomputed. That protects a sealed result
from being silently overwritten, but it also means a rerun tells you
nothing unless you move the old file aside first:

```python
import shutil, pathlib
p = pathlib.Path("/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4/runs")
shutil.move(str(p / "ablation" / "ablation_result.json"),
            str(p / "ablation" / "ablation_result.PREVIOUS.json"))
```

Then rerun, and compare the new file against `.PREVIOUS`. They should be
identical: master seed 2026, deterministic algorithms on, hashing on CPU.

### Order

Each analysis needs the sealed held-out results, which are already in the
project. Beyond that only one ordering constraint: `FIGURES` needs
`SCOREDUMP`.

| Step | Notebook | Runtime | Writes |
|---|---|---|---|
| 1 | `ABLATION` | `ablation_only.py` | `runs/ablation/ablation_result.json` |
| 2 | `INVERSION` | `inversion_only.py` | `runs/inversion/inversion_result.json` |
| 3 | `REVOCATION` | `revocation_only.py` | `runs/revocation/revocation_result.json` |
| 4 | `SCOREDUMP` | `scoredump_only.py` | `runs/scores/score_histograms.json` |
| 5 | `FIGURES` | `figures_only.py`, `docx_only.py` | four figures, and the docx |

Every notebook is the same three or four cells: mount and preflight, load
the runtime, run. The preflight fails loudly with the missing path if an
input is absent, rather than half-running.

### What each run should print

**1. Ablation** — voice, then face:

```
voice   polyiom       1.9282   iom_only  0.2730   randproj_iom  0.7002
face    polyiom       4.7995   iom_only  4.2471   randproj_iom  3.8610
```

Both contrasts against `polyiom` on voice exclude zero; no `D_sys`
contrast does.

**2. Inversion** — the assertion at the top must pass before any result is
printed. It checks that the differentiable transform matches the study's
own transform on L2-normalised probes, by relative error, and that no
bucket index moves. Then:

```
SAR 100% for every arm, both modalities

cos to the true embedding     polyiom   iom_only   randproj_iom   chance
voice                          0.2219     0.9128         0.4896   0.1202
face                           0.4184     0.8759         0.4923   0.0287
```

Every arm is fully invertible to acceptance; what differs is how much of
the underlying biometric the reconstruction recovers. `polyiom` on voice
is the closest to chance.

**3. Revocation** — 40 fresh key sets per arm per modality:

```
voice  polyiom   7.50 [ 2.11, 14.44]   iom_only 100.00   randproj_iom  5.73 [4.01, 7.63]
face   polyiom  25.60 [13.02, 38.58]   iom_only 100.00   randproj_iom  2.89 [1.77, 4.27]
```

`polyiom` median is 0.00 on both. "Keys failing outright" is 5.0% on voice
and 25.0% on face — that is 12 of 80, and it means a key set that left at
least **half** the subjects exposed, not all of them.

**4. Score dump** — the line that matters is the faithfulness check:

```
evaluation   58 identities, 580 genuine / 33060 impostor
  protected   EER  1.9282%  reproduces sealed held-out EER (1.9282%)
  unprotected EER  0.0848%   -> protection costs +1.8434 pp
```

If it prints `*** MISMATCH` instead of `reproduces sealed held-out EER`,
stop. The dump is not faithful and no figure should be built on it.

**5. Figures** — four figures displayed inline, then the docx. Cell 4
installs `python-docx` first.

### After a rerun, re-verify

Copy the regenerated files over `results/` in this package and run
`verify.py` again. It should still report 74 passed. If a number moved,
the regenerated run disagrees with the paper and the difference needs
explaining before anything is published.

---

## Runtimes and requirements

| Step | Needs | Roughly |
|---|---|---|
| `verify.py` | Python 3.8 | 1 second |
| Ablation | Colab CPU | minutes |
| Inversion | Colab GPU helps | longest of the five; 800 steps x 5 restarts per template per arm |
| Revocation | Colab CPU | minutes; 40 key sets x 3 arms x 2 modalities |
| Score dump | Colab CPU | minutes |
| Figures | Colab CPU | under a minute |

Hashing is pinned to CPU deliberately, so results do not depend on which
GPU Colab allocates.

## If something fails

**Preflight says a file is missing.** Remount Drive. If it persists, the
file genuinely is not in the project; the message names the exact path.

**Inversion's assertion fires.** Read the printed relative error. This
assertion previously fired at 2.441e-04 on an absolute tolerance, which
turned out to be the float32 spacing rather than a real disagreement; it
now tests relative error and bucket-index invariance instead. A relative
error near 1e-8 with no index moved is correct behaviour.

**A number differs from this runbook.** Do not adjust the paper to match.
Check first whether the output file was already present and resumed, which
is the usual explanation, and whether Drive was remounted after the last
upload.

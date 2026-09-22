# For the reviewer

## Five minutes, no dependencies

```
python3 run.py verify
```

Python 3.8 or newer. No packages, no data, no network, no GPU. It reads
the stored results and re-derives every number the manuscript reports.
Expect `74 checks passed, 0 failed` and exit code 0.

To satisfy yourself the check is not vacuous, break one stored value and
run it again:

```
python3 - <<'PY'
import json
p = "results/heldout/voice_heldout_result.json"
d = json.load(open(p)); d["EER_HOLDOUT"] = 0.0175
json.dump(d, open(p, "w"), indent=2)
PY
python3 run.py verify        # expect two FAILs and exit 1
```

Two checks should fail, not one. The second is the informative one: the
ablation ran at the sealed operating point, so its `polyiom` arm must
equal the held-out result exactly, and the two files cannot disagree
unless one was edited. Re-extract the archive to restore.

## Fifteen minutes, with NumPy

```
pip install numpy
python3 run.py all
```

Four steps: `verify`, `test` (29 unit tests), `parity`, `demo`. Each exits
non-zero on failure.

`parity` needs PyTorch. Without it the step reports **SKIPPED** and states
that the NumPy pipeline is unverified against the study's implementation.
It never reports a pass it did not earn. With torch installed it prints
one float32 ulp of difference on the hardened vector and zero differing
template indices out of 32768.

## What each claim rests on

| Claim in the paper | Where to check it |
|---|---|
| Sealed operating points, held-out and external results | `results/`, checked by `verify.py` |
| The three secondary analyses | `results/{ablation,inversion,revocation}` |
| Nothing was refitted after sealing | `changes_any_seal: false` in every result file; asserted in tests |
| The ablation ran at the sealed point | `polyiom_reproduces_sealed_heldout: true`, and an exact-equality check against the held-out file |
| The maths is implemented as described | `polyiom/core.py`, with `run.py parity` against the original PyTorch |
| Metric definitions | `polyiom/metrics.py`, with edge-case tests |

## Points we would raise ourselves

These are in the paper's limitations, and are flagged here so no reviewer
has to find them:

1. **The face arm resolves nothing.** With 259 genuine comparisons the
   held-out interval is [1.945, 10.345]. The face encoder caps the
   attainable equal error rate near 3%, which is also why the sealed
   recognition floor was relaxed from 1% to 3% before any evaluation
   identity was read. Face is descriptive throughout.

2. **The unprotected voice baselines are below the protocol's
   resolution.** Fewer than one genuine error on every split, so they are
   reported as one-sided 95% bounds, never as point estimates, and no
   ratio is quoted.

3. **The recommended configuration was never sealed.** `randproj_iom` is
   recommended over the polynomial but was only ever evaluated at the
   polynomial's operating point, not put through the selection protocol
   itself.

4. **One interval was retracted mid-study.** The first revocation
   analysis used 3 keys and bootstrapped identities only. With 40 keys and
   a two-level bootstrap over keys and identities, the contrast it had
   reported is not distinguishable. The corrected result is what ships,
   and `verify.py` checks it.

5. **"Failing outright" means at least half the subjects, not all.** For
   `polyiom` that is 12 of 80 key sets, of which 8 leave every subject
   exposed. Both counts are in the paper and both are asserted in the
   tests, because conflating them overstates the failure.

6. **Unlinkability and revocability share one measurement.** The mated
   distribution serves both. They are not independent evidence and the
   paper does not treat them as such.

## What the package cannot establish

`verify.py` reads stored outputs. It does not recompute a hash, a
bootstrap or an attack, so it catches a number transcribed wrongly into
the manuscript or a result file altered afterwards, but not an error
inside the pipeline. For that the analyses must be rerun against the
embeddings; `RUNBOOK.md` section 2 gives the procedure, and `DATA.md`
explains why the embeddings are not redistributed.

## Before submission

`LICENSE` and `CITATION.cff` contain bracketed placeholders for author
name, affiliation, ORCID, journal and DOI. They must be filled in.

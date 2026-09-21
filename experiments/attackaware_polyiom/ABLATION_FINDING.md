# Hardening ablation — finding

Run 2026-09-21 at the sealed operating points. No seal was written, no
threshold fitted. Both arms' self-checks passed: the `polyiom` arm
reproduces the sealed held-out EER **and** D_sys exactly for both
modalities, and both frozen IoM tensors are ~N(0,1), so the three arms are
drawn from the same family and the comparison is not confounded by the
tensor distribution.

Confirmed in passing: **voice `d = 192`** (the one value never previously
verified against the code).

## The result

On voice, the polynomial hardening **costs recognition accuracy firmly and
buys no measurable unlinkability**.

| voice, n=58 | EER | 95% CI | D_sys | 95% CI | TAR @ sealed FMR |
|---|---|---|---|---|---|
| `polyiom` (proposed) | 1.928% | [1.110, 2.951] | 0.0884 | [0.0694, 0.2206] | 93.97% |
| `iom_only` | **0.273%** | [0.034, 0.568] | 0.0728 | [0.0581, 0.1916] | **99.66%** |
| `randproj_iom` | 0.700% | [0.305, 1.379] | 0.1132 | [0.0832, 0.2209] | 98.97% |

Contrasts (arm minus proposed; an interval excluding 0 is firm):

| contrast | ΔEER | ΔD_sys |
|---|---|---|
| `iom_only` − `polyiom` | −1.655% [−2.563, −0.903] **FIRM** | −0.016 [−0.125, +0.087] ns |
| `randproj_iom` − `polyiom` | −1.228% [−2.187, −0.285] **FIRM** | +0.025 [−0.092, +0.106] ns |

Negative ΔEER means the baseline is **better**.

## Decomposition

The three arms separate the two things hardening does at once:

| voice | EER | attributable to |
|---|---|---|
| no polynomial, full d=192 | 0.273% | — |
| linear map to k=48 | 0.700% | +0.427 pp, the dimension change |
| keyed polynomial to k=48 | 1.928% | +1.228 pp, **the polynomial itself** |

The polynomial costs about **2.9× more accuracy than the dimensionality
reduction it performs**, and 5.69 pp of TAR at the sealed operating FMR.

## Face

Every face contrast is not distinguishable, as expected at n=58 with 259
genuine trials. Every face **point estimate** also favours a baseline
(`polyiom` 4.800% vs `randproj_iom` 3.861% EER; D_sys 0.1508 vs 0.0961),
but the data cannot resolve it. Report face as descriptive only.

## What survives

Nothing on recognition or unlinkability. The one claim that could still
support the contribution is **irreversibility** — that the keyed polynomial
resists inversion better than IoM-GRP alone. That experiment does not
exist yet. Until it does, the paper has no measured benefit to set against
a firm, measured cost.

## Caveats, stated honestly

1. **The operating point favours the proposed method, and it still lost.**
   `M*`, `q*`, `o*` were selected on development identities to minimise
   `polyiom`'s D_sys subject to its EER floor. The baselines run at a
   configuration tuned for a different pipeline. This asymmetry works
   *against* the baselines, so the finding is conservative, not inflated.

2. **One tensor draw per arm.** `polyiom` uses the frozen tensor from disk;
   the other two use freshly seeded draws. The identity-cluster bootstrap
   resamples identities, not projection tensors, so tensor-draw variance is
   not inside these intervals. With M=128 groups the averaging should make
   it small, but it is untested. Cheap to check: re-run the non-frozen arms
   under several seeds and confirm the contrast is stable.

3. **The key was never evaluated for its recognition cost.** Stage A
   selected `K*` on background identities for inversion resistance behind a
   recognition gate. Nothing in the study asked whether the key that passed
   that gate was worth its accuracy cost. This result suggests it was not.

## Confidence-interval housekeeping

The ablation file re-derives the held-out intervals under a different
bootstrap seed, so they differ in the third decimal from
`heldout_confidence.json` (voice EER [1.110, 2.951] here vs
[1.092, 2.919] there; point estimates are identical). **Quote
`heldout_confidence.json` in the main results table and the ablation file
only for the contrasts** — a reviewer who sees two intervals for the same
quantity will ask why.

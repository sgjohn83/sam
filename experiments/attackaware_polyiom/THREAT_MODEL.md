# Threat model and inversion evaluation — pre-specification

Written **before** the experiment was run. Budget, metrics and success
criteria are fixed here so the result means something whichever way it
falls.

## Adversary scenarios

Standard three-level model for cancelable biometrics.

| Level | Adversary holds | Evaluated |
|---|---|---|
| 1. Naive | own biometric only | yes — this is FMR, already reported |
| 2. Stolen token | `K*`, `R`, algorithm; **not** the template | not applicable to inversion |
| 3. **Full knowledge** | `K*`, `R`, algorithm **and** the stored template `h` | **yes — this experiment** |

Level 3 is the worst case and the one the irreversibility claim must
survive. An adversary who has breached the database has the template; if
the scheme also assumes the key stays secret, it is a two-factor scheme,
not a cancelable biometric.

## The attack

Given `h` and full knowledge, recover an embedding `z'` that the system
accepts as the enrolled subject.

Gradient descent on `z'`, with the non-differentiable argmax relaxed to a
softmax over each group's `q` projections and the temperature annealed.
Cross-entropy against the stored bucket indices. `z'` is renormalised to
the unit sphere each step, because real embeddings are L2-normalised —
this constrains the search and makes the attack *stronger*, not weaker.

**The same attack, same budget, runs against all three arms.** A scheme can
always be made to look secure by attacking it weakly; the only defensible
comparison is an identical attack.

The polynomial is differentiable (integer powers of window values), so
gradients flow through it exactly as they do through the linear arms. No
arm gets a surrogate the others do not.

### Budget, fixed in advance

- 5 random restarts per template
- 800 Adam steps per restart, learning rate 0.05
- temperature annealed 1.0 → 0.05
- best restart by achieved collision count

## Metrics

1. **SAR@τ\*** — Success Attack Rate: fraction of templates whose
   reconstruction is *accepted* at the sealed threshold. The headline.
2. **Mean collisions / M** — how close the attack got, so a reader can see
   whether it was working at all.
3. **cos(z', z_true)** — did it recover the biometric, against the
   chance baseline of cosine between different identities' embeddings.
4. **Cross-key collisions** — hash `z'` under a *different* IoM tensor and
   compare with the true subject's template under that tensor. This
   separates *found a preimage of this hash* from *recovered the
   biometric*. Compared against the impostor mean under the same tensor.

Metric 4 is the one that decides what was actually broken.

## Success criteria, fixed in advance

- The polynomial **helps** if SAR is firmly lower for `polyiom` than for
  both baselines, under the paired identity-cluster bootstrap.
- The polynomial **does not help** if the SAR contrasts are not
  distinguishable, or favour a baseline.

## What this does and does not measure

It measures **practical inversion resistance under a stated attack budget**.
It is not a proof of information-theoretic irreversibility. A perfect
solution provably exists in the search space — `z_true` itself reproduces
`h` exactly — so any failure to find it is an optimisation-hardness
result, and must be reported in those words.

## Self-validation

Three assertions run before any number is reported:

1. The differentiable polynomial reproduces the study's `poly_transform`
   to within float tolerance.
2. Hashing the true enrolment embedding reproduces the stored template
   exactly, proving the attack target is achievable.
3. A random unit vector, with no attack, scores near the measured FMR —
   which anchors the SAR scale.

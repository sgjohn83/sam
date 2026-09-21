# Full-knowledge inversion — finding

Run 2026-09-21 against the sealed operating points. Both assertions
passed: the differentiable polynomial matches the study's to a relative
5.7e-08 and moves no bucket index, and the attack targets equal the stored
templates. The attack is attacking the real scheme.

## Headline: the pre-registered metric is null, and saturated

**SAR = 100% for every arm, both modalities.** Every template, under every
pipeline, is invertible to acceptance. Contrasts are exactly zero with
zero-width intervals.

SAR was the pre-registered headline and it did not discriminate, because
it saturated: the attack reaches 128/128 buckets against a threshold of
37, and 256/256 against 68. Any competent attack clears those thresholds.
The pre-registered *secondary* metrics are what carry the information, and
they were specified in `THREAT_MODEL.md` before the run — no metric was
introduced after seeing the result.

## What the secondary metrics show

| voice, M=128, τ=37 | hits/M | cos to true (chance 0.120) | cross-key vs impostor |
|---|---|---|---|
| `polyiom` | 128.0 | **0.222** (1.9× chance) | 109.4 vs 10.2 |
| `iom_only` | 128.0 | 0.913 (7.6× chance) | 73.8 vs 7.2 |
| `randproj_iom` | 125.7 | 0.490 (4.1× chance) | 107.1 vs 7.6 |

| face, M=256, τ=68 | hits/M | cos to true (chance 0.029) | cross-key vs impostor |
|---|---|---|---|
| `polyiom` | 256.0 | **0.418** | 208.0 vs 12.9 |
| `iom_only` | 256.0 | 0.876 | 129.9 vs 10.3 |
| `randproj_iom` | 238.8 | 0.492 | 198.2 vs 10.9 |

Two findings, pulling in opposite directions.

### 1. The polynomial does protect the raw embedding

Against `iom_only` the attack recovers the embedding almost exactly —
cosine 0.913 on voice, 0.876 on face. Against `polyiom` it recovers far
less: 0.222 and 0.418. This is the one place in the whole study where the
polynomial demonstrably does something.

It is a real effect and it is large. It is **not yet intervalled** — the
per-identity cosines were not bootstrapped in this run.

### 2. But revocation fails, and it fails *worse* with the polynomial

Hash the reconstruction under a **fresh IoM tensor** and compare with the
true subject:

- `polyiom`: 109.4 of 128 — **3.0× the threshold**. Accepted.
- `iom_only`: 73.8 — 2.0× threshold. Accepted.
- `randproj_iom`: 107.1 — 2.9× threshold. Accepted.

Impostor baselines are 7–13. So an attacker holding one stolen template
reconstructs something that is still accepted after the template is
revoked and re-issued under a new IoM key. **Revocation by re-keying the
projection does not work**, for any arm — and `polyiom` transfers *better*
than the baseline, i.e. it is the worst of the three on this axis.

### Why the two findings are consistent

The polynomial compresses `z` into `y`, and the system matches on `y`, not
on `z`. The attack recovers `y` essentially exactly — that is what 128/128
buckets means — while recovering little of `z`. So the polynomial
protects the embedding and exposes the hardened vector, and the hardened
vector is all an attacker needs.

**The one-sentence version: `P_{K*}` hides the biometric but not the
thing the system actually compares.**

## What this does and does not settle

**Settled.** Under a level-3 adversary the scheme is not irreversible, the
polynomial buys no acceptance-level protection, and revocation that
re-keys only the IoM projection is broken.

**Not settled.** Revocation that also re-issues the **polynomial key**
`K*`. This experiment changed `R` only. Because the attack's `z'` has low
cosine to `z` (0.222 on voice), it is genuinely unclear whether
`P_{K**}(z')` would still match `P_{K**}(z)` under a fresh `K**`. That is
the last open question, and it is the last place the contribution could
survive.

## Caveats

1. **SAR saturated**, so the headline contrast is uninformative rather
   than evidence of equivalence. Report mean collisions, not SAR alone.
2. **The cosine and cross-key contrasts have no confidence intervals.**
   The per-identity values were not retained. A re-run that bootstraps
   them would let these be stated as firm rather than as point estimates.
3. **One attack, one budget.** A stronger or differently-shaped attack
   could only make these numbers worse for the scheme, not better, so the
   direction of the finding is safe; the magnitudes are a lower bound on
   attacker success.

# Post-revocation acceptance — finding (40 keys, two-level bootstrap)

Supersedes the 3-key version. Assertions passed; the attack is the
inversion run's, re-run under the same seeds, so `z'` is identical.

## Retraction

The 3-key run reported `randproj_iom` as **firmly worse** than `polyiom` on
voice — +4.598 pp [+1.724, +8.046] — and that was used here to claim the
keyed polynomial specifically, rather than the dimensionality reduction,
was doing the work.

**That claim is withdrawn.** With 40 keys and a bootstrap over keys as well
as identities the same contrast is −1.767 pp [−8.793, +3.967], **not
distinguishable**. The earlier interval came from resampling the wrong
axis and was an artifact of three draws.

## What the 40 keys show

| voice, n=58, τ=37 | PRAR | 95% CI | per-key med / min / max | keys failing outright |
|---|---|---|---|---|
| `polyiom` | 7.50% | [2.11, 14.44] | 0.00 / 0.00 / **89.66** | **2 of 40** |
| `iom_only` | 100.00% | [100, 100] | 100 / 100 / 100 | 40 of 40 |
| `randproj_iom` | 5.73% | [4.01, 7.63] | 6.90 / 0.00 / 13.79 | **0 of 40** |

| face, n=58, τ=68 | PRAR | 95% CI | per-key med / min / max | keys failing outright |
|---|---|---|---|---|
| `polyiom` | 25.60% | [13.02, 38.58] | 0.00 / 0.00 / **100.00** | **10 of 40** |
| `iom_only` | 100.00% | [100, 100] | 100 / 100 / 100 | 40 of 40 |
| `randproj_iom` | 2.89% | [1.77, 4.27] | 1.72 / 0.00 / 8.62 | **0 of 40** |

### Firm and robust: keyed compression is necessary

`iom_only` — IoM-GRP on the raw embedding — fails **completely, for all 40
keys, on both modalities**. Every stolen template stays a valid credential
after re-keying. Contrasts +92.5 pp (voice) and +74.4 pp (face), both FIRM.

Whatever else is true, compressing the embedding under a key before
hashing is what makes revocation possible at all.

### Not firm: that the polynomial is the right compression

`polyiom` has a **bimodal failure mode**. Its median per-key PRAR is 0.00%
on both modalities — usually revocation is perfect — but it fails
catastrophically for a minority of fresh keys: 2 of 40 on voice (up to
89.66%) and 10 of 40 on face (up to 100%).

`randproj_iom` never does this. Its worst key leaks 13.79% (voice) and
8.62% (face), and **0 of 80 keys across both modalities failed outright**.

A scheme that revokes perfectly most of the time but fails completely one
re-key in four is worse operationally than one that leaks a few percent
every time, because the failure is unpredictable and total.

## randproj_iom dominates polyiom on the measured axes

| axis | `randproj_iom` | `polyiom` | verdict |
|---|---|---|---|
| EER, voice | 0.700% | 1.928% | randproj better, FIRM |
| D_sys, voice | 0.1132 | 0.0884 | not distinguishable |
| SAR (inversion) | 100% | 100% | identical |
| PRAR, voice | 5.73% | 7.50% | not distinguishable |
| PRAR, face | 2.89% | 25.60% | randproj better, FIRM |
| keys failing outright | 0 of 80 | 12 of 80 | randproj never fails |

Both are keyed compressions; one is linear, the other polynomial. On this
evidence the linear map is better on accuracy, no worse on revocation
where the data can tell, firmly better where it can, and free of the
catastrophic failure mode.

## Revised thesis for the paper

> Keyed compression before IoM-GRP hashing is **necessary** for
> revocability — without it every stolen template is a permanent
> credential. A keyed random linear projection is sufficient, and on this
> evidence preferable to the keyed polynomial: it costs 1.23 pp less EER,
> revokes at least as reliably, and never fails outright.

That is a design recommendation supported by an ablation, an attack and a
revocation test, with the negative results making the positive one
credible. It is not the paper that was planned, and it is a more useful
one.

## Open question

Why does `polyiom` fail for a minority of fresh keys? The failing keys are
not degenerate — all 40 passed the discrimination check on both
modalities. The likely explanation is that a resampled key occasionally
behaves like `K*` on the subspace the attack's `z'` occupies, but that is
untested. If the paper leans on the catastrophic-failure claim, this
deserves a look; if it leans on the dominance table, it does not.

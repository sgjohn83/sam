# Post-revocation acceptance — finding

Run 2026-09-21. Assertions passed; the attack is the inversion run's, re-run
under the same seeds, so `z'` is identical.

## The polynomial's job is revocation, and on voice it does it

**PRAR** — the fraction of subjects whose *old* template's reconstruction is
still accepted after they re-enrol under fully fresh keys.

| voice, n=58, τ=37 | PRAR | 95% CI | cos to true | 95% CI |
|---|---|---|---|---|
| `polyiom` | **0.57%** | [0.00, 1.72] | 0.222 | [0.196, 0.247] |
| `iom_only` | **100.00%** | [100, 100] | 0.913 | [0.910, 0.916] |
| `randproj_iom` | 5.17% | [2.30, 8.62] | 0.490 | [0.481, 0.498] |

Contrasts against `polyiom`, all **FIRM**: `iom_only` +99.4 pp, `randproj_iom`
+4.6 pp; cosine +0.691 and +0.268.

Read plainly: **without the polynomial, revocation does not work at all.**
Every stolen template remains a valid credential after re-keying. With it,
0.57%. And `randproj_iom` — same dimensionality reduction, no keyed
polynomial — is firmly worse, so this is not the dimension change doing the
work. It is the keyed polynomial specifically.

This is the contribution, demonstrated. It is also the *only* thing in the
study that the polynomial demonstrably buys.

The voice result is stable across fresh keys: 0.00%, 1.72%, 0.00%.

## The face number is not usable as reported

| face, n=58, τ=68 | per-key PRAR | mean |
|---|---|---|
| `polyiom` | 1.72%, 0.00%, **100.00%** | 33.91% |
| `iom_only` | 100%, 100%, 100% | 100.00% |
| `randproj_iom` | 0.00%, 3.45%, 1.72% | 1.72% |

`polyiom`'s 33.91% is **one fresh key out of three**, not a uniform
one-in-three failure. Two keys revoke cleanly; the third fails completely,
with a healthy impostor floor (10.4 against a chance 8.0), so it is a real
transfer, not a degenerate key.

**The confidence interval on that number is wrong.** [33.33, 35.06] comes
from bootstrapping over *identities*, and with one catastrophic key the
identity bootstrap concentrates tightly around 1/3. The dominant uncertainty
here is over **keys**, and there are three of them. The interval answers a
question nobody asked.

So the firm-looking face contrast — `randproj_iom` −32.2 pp — is contaminated
by the same single key and must not be reported.

## What is safe to say now

- **Voice:** revocation works with the polynomial and fails completely
  without it. Firm, stable across keys, and `randproj_iom` rules out the
  dimensionality explanation.
- **Face:** revocation usually works but sometimes fails outright depending
  on the re-issued key. Not characterised. Needs many more keys.

## The fix, and it is cheap

Re-run with 25–50 fresh keys and bootstrap over **keys as well as
identities**. The expensive part is the attack, which runs once per arm; each
additional key costs only a re-hash. The same run should report the *per-key
distribution*, not just a mean, because "fails for 1 key in 3" and "fails
34% of the time" are different claims and only one of them is true.

## Where this leaves the paper

Combined with the earlier runs, the arc is now complete and coherent:

| Property | Does the polynomial help? |
|---|---|
| Recognition accuracy | **No** — costs 1.23 pp EER on voice (firm) |
| Unlinkability (D_sys) | **No** — not distinguishable |
| Inversion resistance (SAR) | **No** — 100% for every arm |
| Protecting the raw embedding | **Yes** — cos 0.222 vs 0.913 (firm) |
| **Revocability** | **Yes** — PRAR 0.57% vs 100% (firm, voice) |

That is a publishable paper with an honest thesis: *keyed polynomial
hardening buys revocability, not accuracy and not unlinkability, and the
price is 1.23 pp of EER.* The ablation supplies the price tag, the inversion
run shows what is not bought, and this run shows what is.

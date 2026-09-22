# Performance preservation against the unprotected baseline

Secondary analysis. Read-only at the sealed operating points. Changes no
seal, fits no threshold. Source: `notebooks/scoredump_only.py`, output
`runs/scores/score_histograms.json`.

## Why this had to be measured

Performance preservation is the first of the four ISO/IEC 24745 criteria,
and in this literature it is always reported as the protected system
measured against the **unprotected** one. Every recognition number the study
had produced up to this point compared *protected* variants against each
other. Plain cosine matching on these same splits had never been run, so the
paper could not state its own headline claim in the form the field expects.

The dump reproduces both sealed held-out EERs exactly (voice 1.9282%, face
4.7995%), so the histograms are a faithful record of the sealed pipeline and
the baseline is computed from the identical enrolment and probe sets.

## Result

| Partition | Identities | Protected EER | Unprotected EER | Cost | Verdict |
|---|---|---|---|---|---|
| Voice, development | 42 | 0.9524% | 0.0000% | +0.9524 pp | baseline at the floor |
| Voice, evaluation | 58 | 1.9282% | 0.0848% | **+1.8434 pp** | **firm** |
| Voice, external (VCTK) | 110 | 2.7977% | 0.0033% | **+2.7944 pp** | **firm** |
| Face, development | 42 | 2.8391% | 2.6718% | +0.1673 pp | not resolvable |
| Face, evaluation | 58 | 4.7995% | 3.4749% | +1.3246 pp | not resolvable |

## Why two of these are firm and two are not

The unprotected EERs on voice sit **below the resolution of the protocol**.
One genuine error is 0.238% on voice development, 0.172% on evaluation and
0.091% on external. The measured baseline EERs are smaller than a single
genuine error, which means the equal-error crossing falls in a region
containing zero or at most one genuine mistake. Those point estimates are
therefore not usable as point estimates, and the ratios they imply (22.7x
held-out, 848x external) must not be reported.

What they do support is a one-sided bound. At 95% confidence the unprotected
genuine error rate is below 0.515% on evaluation and below 0.272% on
external. The protected intervals are 1.928% [1.092, 2.919] and 2.798%
[1.992, 3.807]. In both cases the lower bound of the protected interval lies
above the upper bound of the baseline, so the degradation is firm without
relying on the unresolved point estimate.

Face is the opposite case and gives nothing. The face evaluation has 259
genuine comparisons and a protected interval of 4.799% [1.945, 10.345]. The
baseline's own 95% upper bound, 5.504%, sits inside that interval. The
+1.32 pp point difference is therefore **not distinguishable from zero**, and
the face experiment cannot support a preservation claim in either direction.
This is a power limitation, not evidence of preservation, and must not be
presented as the latter.

## The diagnostic this produces

The face unprotected baseline is 3.475% EER on evaluation and 2.672% on
development. For LFW that is poor. It is also the explanation for a protocol
decision that was, until now, defensible only on its own terms: the voice
recognition floor of EER at most 1% was declared unattainable for face and
relaxed to 3%, with the deviation sealed before any evaluation identity was
read.

The baseline now shows *why* it was unattainable. The face embeddings
themselves cap the achievable EER at roughly 3%. No protected system built on
them could have reached 1%, whatever the protection did. The relaxation was
forced by the representation, not by the scheme, and not by a wish to make
the scheme look better.

The best protected face EER across all eighty configurations was 2.29%,
which is **better than the 2.672% unprotected baseline on the same
development identities**. On face, protection is not the binding constraint
at any configuration in the grid.

## What this means for the scheme

The cost of protection here scales inversely with the quality of the
underlying representation.

Where the embedding is strong, protection dominates the error budget. The
voice encoder is near-perfect on these splits, so essentially all of the
protected system's 1.93% held-out and 2.80% external error is introduced by
the protection itself.

Where the embedding is weak, protection is free, because the
representation's own error already exceeds what protection costs. That is
the face result, and it is why face cannot test this criterion.

The honest summary for the paper is therefore: **performance preservation is
not supported on voice, and is untested on face.** The voice degradation is
firm, is larger externally than internally, and is the same direction as the
external false-match-rate finding already reported.

## Non-claims

- We do not claim a degradation ratio. The voice baselines are unresolved.
- We do not claim preservation on face. The interval is too wide to resolve.
- We do not claim the face encoder is the best available, only that the one
  used caps this experiment at roughly 3% and that this explains the sealed
  floor relaxation.
- We do not claim the voice degradation generalises beyond LibriSpeech and
  VCTK, though it appears in both and is larger in the external corpus.
- The mated distribution used for unlinkability is the same measurement as
  the revocability pseudo-impostor distribution. They are one observation.

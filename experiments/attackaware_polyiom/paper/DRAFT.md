# Keyed compression, not keyed polynomials: what actually makes an IoM-based cancelable biometric revocable

*Working title. Alternatives: "What does the hardening step buy? An ablation
and attack study of polynomial-hardened IoM hashing"; "Revocability is the
binding property: a pre-registered study of a cancelable biometric scheme".*

**Draft status.** Complete first draft, written independently of any venue.
Citation slots are marked `[CITE: ...]` and state exactly what needs
supporting; no reference has been invented. Section 9 lists what a
literature pass must supply.

---

## Abstract

A biometric template cannot be changed. If it is stolen, the person cannot
be issued a new face or a new voice. Cancelable biometrics address this by
storing a transformed template that depends on a key, so that a compromised
template can be replaced by issuing a new key. A scheme of this kind must
satisfy four requirements at once: it must still recognise people, it must
not be reversible to the original biometric, templates from different
databases must not be linkable, and a stolen template must be replaceable.

We study a scheme that applies a keyed polynomial transform to a face or
speaker embedding before Index-of-Maximum (IoM) hashing. We evaluate it
under a pre-registered protocol: identities are split once into background,
development and evaluation sets; the key and the operating point are chosen
on development identities and then frozen; the evaluation identities and an
external corpus are read only afterwards. We then run three further
analyses that the original study did not contain: an ablation that removes
the polynomial, an inversion attack under a full-knowledge adversary, and a
test of whether a stolen template can still be used after the subject
re-enrols under a new key.

The results are largely negative for the polynomial, and they identify a
different property as the one that matters. The polynomial costs 1.23
percentage points of equal error rate on voice compared with a random
linear map of the same output size, and it does not improve unlinkability.
Under a full-knowledge adversary every arm is fully invertible: the attack
reconstructs an input that is accepted for every template we tested. The
polynomial does conceal the underlying embedding, reducing the cosine
similarity between the reconstruction and the true embedding from 0.913 to
0.222, but this does not prevent acceptance, because the system matches on
the hardened vector rather than on the embedding, and the attack recovers
the hardened vector exactly.

The property that separates the arms is revocability. Applied to the raw
embedding, IoM hashing fails completely: for all forty fresh key sets we
tested, on both modalities, the reconstruction built from an old template
was still accepted after re-keying. A stolen template is therefore a
permanent credential. Any keyed compression of the embedding before hashing
removes this failure. The polynomial is not the best choice of compression:
a keyed random linear projection is more accurate, revokes at least as
reliably, and never failed outright, whereas the polynomial failed
completely for 12 of 80 fresh key sets.

We conclude that keyed compression before IoM hashing is necessary for
revocability, that a random linear projection is sufficient, and that the
polynomial is not preferable to it on any property we were able to measure.

---

## 1. Introduction

### 1.1 The problem

Passwords can be changed. Biometrics cannot. If a database of face
embeddings is stolen, the people in it cannot be issued new faces. This is
the central difficulty in deploying biometric recognition at scale, and it
is the reason template protection is required by standards for biometric
information protection `[CITE: ISO/IEC 24745 biometric information
protection]`.

Cancelable biometrics are one response. Instead of storing the biometric
feature vector, the system stores a transformed version of it. The
transform depends on a key. If the stored template is compromised, the
operator issues a new key, the subject re-enrols, and the old template
becomes useless. The biometric itself never has to change.

A scheme of this kind is usually required to satisfy four properties at
once `[CITE: standard formulation of the four criteria]`:

1. **Recognition performance.** Protected templates must still tell people
   apart about as well as unprotected ones.
2. **Irreversibility.** An attacker who obtains a stored template must not
   be able to recover the underlying biometric.
3. **Unlinkability.** Templates of the same person held in two different
   databases, protected with different keys, must not be identifiable as
   belonging to the same person.
4. **Revocability.** A compromised template must be replaceable, and the
   old one must stop working.

These four are in tension. A transform that destroys enough information to
be irreversible usually also destroys the information needed for
recognition. Most of the literature in this area reports the first three
and treats the fourth as following automatically from the use of a key.

### 1.2 What we study

We study a scheme that combines two stages. First, a keyed polynomial is
applied to overlapping windows of the biometric embedding. We refer to this
as *hardening*. Second, the hardened vector is passed through
Index-of-Maximum (IoM) hashing, which projects it many times and stores
only which projection was largest in each group `[CITE: IoM hashing, Jin et
al.]`. The combination is intended to be harder to invert than IoM hashing
alone, because the polynomial stage is keyed and non-linear.

The scheme was evaluated under a pre-registered protocol. One hundred and
fifty identities per modality were split once, from a fixed random seed,
into three disjoint sets: fifty background identities used to search for
the polynomial key, forty-two development identities used to choose the
operating point, and fifty-eight evaluation identities that were not read
until the configuration was frozen. An external voice corpus was read last
of all. This is stricter than common practice in the area, where thresholds
are often chosen on the same data used to report results.

### 1.3 What was missing

The pre-registered study measured how well the complete scheme performs. It
did not measure what the polynomial stage contributes. The parameter sweep
varied the number of hash groups, the number of projections per group, and
the window overlap. All three are parameters of the hashing stage or of the
windowing; none of them removes the polynomial. There was therefore no
evidence in the study that the polynomial does anything at all.

The study also did not contain an attack. The scheme is described as
resisting inversion, and the polynomial key was selected using an inversion
stress test, but that test was a selection criterion applied to candidate
keys on background identities. It was never used to evaluate the final
system. Irreversibility was asserted rather than measured.

This paper adds the missing analyses.

### 1.4 Contributions

1. **An ablation that isolates the polynomial.** We compare the complete
   scheme against IoM hashing applied directly to the embedding, and
   against IoM hashing applied to a random linear projection of the same
   output size. The third arm is necessary because the polynomial also
   reduces dimensionality; without it, the effect of the polynomial cannot
   be separated from the effect of the size reduction.

2. **An inversion evaluation under a full-knowledge adversary.** The
   adversary holds the key, the projection, the algorithm and the stored
   template. The same attack, at the same budget, is applied to all three
   arms, because a scheme can always be made to look secure by attacking it
   weakly.

3. **A revocation test.** We ask whether a reconstruction built from an old
   template is still accepted after the subject re-enrols under completely
   new keys. To our knowledge this is not routinely measured, and we find
   it is the property that separates the designs.

4. **A negative result and a design recommendation.** The polynomial costs
   accuracy and does not improve irreversibility or unlinkability. Keyed
   compression of any kind is what makes revocation work. A random linear
   projection does that job better than the polynomial.

5. **A worked example of an evaluation protocol** that keeps confirmatory
   and exploratory analysis separate, states in advance what would count as
   evidence, and reports the claims the data cannot support alongside those
   it can.

### 1.5 Summary of findings

| Property | Does the keyed polynomial help? |
|---|---|
| Recognition accuracy | No. It costs 1.23 pp EER against a linear map of the same output size (firm). |
| Unlinkability | No. No contrast is distinguishable. |
| Irreversibility | No. Every template in every arm was inverted to acceptance. |
| Concealing the embedding | Yes. Cosine 0.222 against 0.913 (firm). |
| Revocability | Keyed compression is necessary. The polynomial specifically is not better, and is worse on face (firm). |

---

## 2. Background and related work

### 2.1 Cancelable biometrics

The idea of storing a revocable transform of a biometric rather than the
biometric itself goes back to early work on cancelable templates
`[CITE: Ratha et al., original cancelable biometrics proposal]`. A large
family of schemes followed, of which random-projection methods such as
BioHashing are the best known `[CITE: Teoh et al., BioHashing]`. In these
schemes a user-specific random matrix is applied to the feature vector and
the result is quantised. The key is the random matrix.

Two weaknesses of this family are well documented. When the key is stolen,
recognition performance can collapse, because the transform is essentially
a linear map that the attacker can undo `[CITE: stolen-token analyses of
BioHashing]`. And the quantisation step is often shallow enough that the
original feature vector can be approximated from the stored code
`[CITE: reconstruction attacks against random-projection schemes]`.

### 2.2 Index-of-Maximum hashing

IoM hashing avoids storing any magnitude information `[CITE: IoM hashing,
Jin et al.]`. The feature vector is projected using many random vectors,
which are divided into groups. Within each group the system records only
*which* projection was largest, as an index. The stored template is a list
of small integers, one per group. Two templates are compared by counting
how many positions hold the same index; this count is the similarity score.

Discarding magnitudes is what gives the scheme its security argument. Many
different inputs produce the same index in a group, so the map is
many-to-one, and the stored code carries less information than the feature
vector. It also makes the comparison cheap: the score is a count of equal
integers.

### 2.3 How these schemes are usually evaluated

The typical evaluation reports equal error rate before and after
protection, a measure of unlinkability, and sometimes a reconstruction
experiment. The most widely used unlinkability measure is the framework of
Gómez-Barrero and colleagues, which compares the score distribution of
mated pairs, meaning two protected templates of the same person under
different keys, against the distribution of non-mated pairs `[CITE:
Gómez-Barrero et al., unlinkability framework]`. It summarises the
comparison as a single number, often written $D_{\mathrm{sys}}$, where
lower values indicate better unlinkability.

Three habits are common in this literature and all three weaken the
conclusions.

First, the decision threshold is frequently chosen on the same data on
which results are reported. This makes the reported error rates optimistic
by an unknown amount.

Second, ablations are rare. Many published schemes combine two or three
transformation stages and report the performance of the combination without
showing what each stage contributes. A combination that performs well is
taken as evidence that each part is useful.

Third, irreversibility is often argued from the structure of the transform
rather than measured. When a reconstruction attack is run, it is usually
run only against the proposed scheme and not against the baselines, which
makes the comparison uninformative: a weak attack makes any scheme look
secure.

### 2.4 The gap this paper addresses

The scheme we study was developed with the first habit deliberately
avoided. The operating point was selected on development identities and
frozen before the evaluation identities were read. The second and third
habits, however, were present: there was no ablation and no attack. This
paper supplies both, and adds a fourth analysis, on revocability, that we
have not seen reported.

---

## 3. Method

### 3.1 Overview

A sample is turned into a protected template in three steps. A frozen
neural network produces an embedding. A keyed polynomial is applied to
overlapping windows of that embedding, producing a shorter hardened vector.
IoM hashing turns the hardened vector into a list of indices, which is what
is stored. Figure 1 shows the complete construction. Figure 2 shows how two
protected templates are compared.

### 3.2 Frozen encoders

For face we use a FaceNet encoder producing a 512-dimensional embedding
`[CITE: FaceNet, Schroff et al.]`. For voice we use an ECAPA-TDNN speaker
encoder producing a 192-dimensional embedding `[CITE: ECAPA-TDNN,
Desplanques et al.]`. Neither network is fine-tuned at any point. This is
deliberate. It means the recognition performance we start from is that of
the published model, and any loss we report is attributable to the
protection scheme rather than to training choices.

We write the embedding of sample $x_m$ in modality $m$ as
$z_m = f_m(x_m)$.

### 3.3 Keyed polynomial hardening

The embedding is not transformed as a whole. Instead, a polynomial is
applied to overlapping windows of five consecutive components. Consecutive
windows advance by $5 - o^{*}$ positions, so neighbouring windows share
$o^{*}$ components. The overlap $o^{*}$ is a design parameter.

Each window produces a single output value. For a window of values
$v_1, \dots, v_5$, the output is $\sum_{i} c_i v_i^{e_i}$, where the
coefficients $c_i$ and the integer exponents $e_i$ are the application key
$K^{*}$. Collecting the outputs of all windows gives the hardened vector
$y_m = P_{K^{*}}(z_m; o^{*})$.

Two consequences matter later. The transform is non-linear and keyed, which
is the intended security property. It also shortens the vector: with window
size five and overlap $o^{*}$, an embedding of length $d$ produces a
hardened vector of length $k = 1 + \lceil (d - 5)/(5 - o^{*}) \rceil$. At
the sealed overlap of one, face goes from 512 to 128 and voice from 192 to
48. This second consequence is not part of the intended design, but it
turns out to matter more than the first.

### 3.4 IoM-GRP hashing

The hardened vector is projected using $M^{*}$ groups of $q^{*}$ random
vectors. Within each group the system finds the largest projection and
stores its index. The protected template is therefore a list of $M^{*}$
integers, each between 1 and $q^{*}$:

$$h_{K,m} \in \{1, \dots, q^{*}\}^{M^{*}}.$$

The magnitudes of the projections are discarded.

### 3.5 Matching

Two templates are compared position by position. The collision score $s_m$
is the number of positions at which the two lists hold the same index. The
system accepts if $s_m \geq \tau^{*}_m$ and rejects otherwise. Nothing
outside the two index lists takes part in the comparison; the sample and
the embedding play no role once enrolment is complete.

### 3.6 Stage A: selecting the polynomial key

The polynomial key is selected on the fifty background identities only.
Between ten and twenty thousand candidate keys are generated
deterministically. Each is scored by an inversion stress test, and keys
that fail a recognition gate are discarded. The best surviving key is
selected and frozen as $K^{*}$.

Two features of this procedure are important for interpreting our results.
The selection objective is inversion resistance; recognition enters only as
a pass-or-fail gate. And the stress test is applied to candidate keys on
background identities, not to the final system on evaluation identities. No
part of the pre-registered study measured how well the selected key resists
inversion in the deployed configuration.

### 3.7 Stage B: selecting the operating point

With $K^{*}$ frozen, eighty configurations are evaluated on the forty-two
development identities, spanning four values of $M$, four of $q$ and five
of $o$. The selection rule is: *choose the configuration with the lowest
$D_{\mathrm{sys}}$ among those meeting a recognition floor*, with ties
broken by equal error rate, then $M$, then $q$, then $o$. The threshold
$\tau^{*}$ is set at the development equal error rate point.

The selected configuration, the threshold and the rule identifier are
written to a sealed record. Nothing downstream may modify them.

---

## 4. Experimental protocol

### 4.1 Identities and partitions

For each modality, 150 identities are drawn and split once, from a master
seed, into three disjoint sets:

| Partition | Identities | Used for |
|---|---|---|
| Background | 50 | Polynomial key search (Stage A) |
| Development | 42 | Operating point and threshold (Stage B) |
| Evaluation | 58 | Held-out reporting only |

Face identities come from LFW `[CITE: LFW, Huang et al.]`. Voice identities
come from LibriSpeech `[CITE: LibriSpeech, Panayotov et al.]`. An external
voice corpus, VCTK `[CITE: VCTK corpus]`, supplies 110 further speakers
that are read only after all internal analysis is complete.

Face enrolment uses a single embedding, because LFW provides as few as
three images for some identities. Voice enrolment uses the
$L_2$-normalised mean of five embeddings. This asymmetry is deliberate and
accounts for part of the difference in performance between the modalities.

### 4.2 Metrics

**Equal error rate (EER).** The error rate at the threshold where the false
match rate equals the false non-match rate. Lower is better. It requires no
threshold and is therefore directly comparable between systems.

**True accept rate (TAR) and false match rate (FMR) at $\tau^{*}$.** The
rates achieved by the sealed threshold, carried unchanged from development.

**Unlinkability, $D_{\mathrm{sys}}$.** The system-level measure of
Gómez-Barrero and colleagues with $\omega = 1$, computed between templates
of the same subject under two independently generated projection keys.
Lower is better.

**Success attack rate (SAR).** Introduced in Section 5.5. The fraction of
templates for which an inversion attack produces an input that the system
accepts.

**Post-revocation acceptance rate (PRAR).** Introduced in Section 5.6. The
fraction of subjects whose old template's reconstruction is still accepted
after they re-enrol under new keys.

### 4.3 Confidence intervals

All intervals are 95% percentile bootstrap intervals over 2000 replicates,
resampling **identities**, not individual comparisons. This matters. If
comparisons were resampled directly, a subject could be compared against
themselves, and the intervals would be too narrow. Each identity receives a
multinomial weight; genuine comparisons take the weight of their subject
and impostor comparisons take the product of the weights of the two
subjects involved.

Where two systems are compared, the bootstrap is **paired**: one resampling
is applied to both arms in each replicate, so the interval on the
difference accounts for the two arms sharing identities. An unpaired
interval would be substantially too wide.

The revocation analysis in Section 5.6 resamples **keys as well as
identities**, for reasons explained there.

We describe a difference as *firm* when its 95% interval excludes zero, and
as *not distinguishable* otherwise. We do not describe a non-distinguishable
difference as evidence of equivalence.

### 4.4 Sealing discipline

The selected key, configuration and threshold are written once and are
read-only thereafter. Every analysis reported in Section 5 verifies that it
reproduces the sealed results before reporting anything new. In the
ablation and attack analyses, the arm corresponding to the complete scheme
rebuilds the sealed pipeline exactly — same key, same projection tensors,
same seeds — and its equal error rate must match the sealed held-out figure
to floating-point precision. If it does not, the analysis stops rather than
reporting numbers.

### 4.5 Status of each analysis

We distinguish two classes throughout.

**Confirmatory.** Sections 5.1 to 5.3 report the pre-registered pipeline.
The operating point was frozen before the evaluation identities were read,
and the external corpus was read last.

**Secondary.** Sections 5.4 to 5.6 report three analyses that were added
after the sealed results had been seen. Each was specified before it was
run, each ran at the already-sealed operating point, and none re-opened
selection or altered a seal. They are nonetheless not part of the
pre-registration, and we label them as secondary wherever they appear. We
make this distinction explicitly because it is the distinction most often
blurred in this literature, and because the confirmatory results are more
trustworthy for being separated from the exploratory ones.

---

## 5. Results

### 5.1 Sealed operating points

| | $M^{*}$ | $q^{*}$ | $o^{*}$ | $\tau^{*}$ | EER | TAR | $D_{\mathrm{sys}}$ | Eligible |
|---|---|---|---|---|---|---|---|---|
| Voice | 128 | 32 | 1 | 37 | 0.952% | 95.238% | 0.052519 | 30 of 80 |
| Face | 256 | 32 | 1 | 68 | 2.839% | 86.260% | 0.133100 | 13 of 80 |

The recognition floor used for voice was EER at most 1% and TAR at least
95%. That floor is unattainable for face. Across all eighty face
configurations the best achievable EER is 2.29% and the best achievable TAR
is 90.08%, so no configuration qualifies. A relaxed face floor of EER at
most 3% and TAR at least 85% was therefore fixed, and the deviation and its
reason were written into the seal, **before any evaluation identity was
read**. We report the 2.29% and 90.08% figures because they are the
evidence that the original floor was impossible rather than merely
inconvenient.

We chose 3% and 85% as the tightest floor that still selects from a
non-trivial pool. At 3% and 90% exactly one configuration survives, so the
selection would have been an artifact of the grid, and that configuration's
$D_{\mathrm{sys}}$ of 0.166 is worse in any case.

Figure 3 shows the design space and where the sealed configurations sit
within it. Figure 4 shows the trade-off frontier between recognition and
unlinkability.

### 5.2 Generalisation to held-out identities

The sealed configuration and threshold were applied, unchanged, to the 58
evaluation identities. Voice yields 580 genuine and 33,060 impostor
comparisons; face yields 259 genuine and 14,763.

| | EER | TAR at $\tau^{*}$ | FMR at $\tau^{*}$ | $D_{\mathrm{sys}}$ |
|---|---|---|---|---|
| Voice | 1.928% [1.092, 2.919] | 93.966% [89.655, 97.414] | 0.185% [0.028, 0.480] | 0.0884 [0.0708, 0.2185] |
| Face | 4.799% [1.945, 10.345] | 82.239% [72.767, 89.933] | 0.041% [0.000, 0.218] | 0.1508 [0.1225, 0.2822] |

Voice equal error rate rose from 0.952% on development to 1.928% on
held-out identities. The development value lies outside the held-out
interval, so this degradation is firm. The system does not meet its own 1%
floor on identities it has not seen.

**No other development-to-held-out difference is supported.** The face
development EER of 2.839% lies inside the held-out interval, and so does
the 3% floor. We therefore cannot claim that face performance degrades, and
we cannot claim that face breaches its floor. Face is reported
descriptively throughout. Fifty-eight identities with single-sample
enrolment give 259 genuine trials and an equal error rate interval spanning
a five-fold range; this is not enough to resolve differences of the size we
are looking for.

Figure 5 shows development, held-out and external results side by side with
their intervals.

### 5.3 External validation on voice

The sealed voice system was applied without modification to 110 VCTK
speakers.

| | EER | TAR at $\tau^{*}$ | FMR at $\tau^{*}$ | $D_{\mathrm{sys}}$ |
|---|---|---|---|---|
| External | 2.798% [1.992, 3.807] | 89.000% [85.727, 91.727] | 0.377% [0.202, 0.622] | 0.0803 [0.0603, 0.1551] |

All four external intervals overlap their held-out counterparts, so **no
held-out-to-external difference is supported**. Equal error rate, true
accept rate and false match rate all moved in the unfavourable direction,
but these are three functions of the same two score distributions. They
constitute one observation, not three, and should not be read as
independent evidence of a drop.

One external finding is firm. The entire false match rate interval lies
above the 0.1% design target. The sealed threshold therefore does not meet
that target on the external corpus. This is a consequence of how the
threshold was chosen: it was set at the development equal error rate point,
which balances the two error types rather than fixing one of them.
Operating at a fixed false match rate would require a different threshold
policy. We deliberately do not fit one here, because fitting a threshold on
evaluation data is exactly what the sealed protocol exists to prevent.

Unlinkability transfers well. The external $D_{\mathrm{sys}}$ interval is
tighter than the held-out interval and contained within it.

### 5.4 What the hardening stage costs *(secondary)*

The pre-registered sweep varies $M$, $q$ and $o$. All three are parameters
of the hashing stage or of the windowing; none removes the polynomial. We
therefore added one condition at the sealed configuration, together with
two baselines.

| Arm | Pipeline |
|---|---|
| PolyIoM | $z \rightarrow P_{K^{*}}(z; o^{*}) \rightarrow$ IoM-GRP |
| `iom_only` | $z \rightarrow$ IoM-GRP |
| `randproj_iom` | $z \rightarrow Az \rightarrow$ IoM-GRP |

The third arm exists because the polynomial does two things at once. It
applies a keyed non-linearity, and it shortens the vector. Comparing
PolyIoM against `iom_only` alone would conflate the two. The third arm
applies a fixed random linear map to the same output length $k$, so the
comparison between PolyIoM and `randproj_iom` isolates the polynomial
itself.

**Voice, held-out identities:**

| Arm | EER | $D_{\mathrm{sys}}$ | TAR at matched FMR |
|---|---|---|---|
| PolyIoM | 1.928% [1.110, 2.951] | 0.0884 [0.0694, 0.2206] | 93.97% |
| `iom_only` | **0.273%** [0.034, 0.568] | 0.0728 [0.0581, 0.1916] | **99.66%** |
| `randproj_iom` | 0.700% [0.305, 1.379] | 0.1132 [0.0832, 0.2209] | 98.97% |

Both equal error rate contrasts are firm and both favour the baseline:
$-1.655$ pp [$-2.563$, $-0.903$] for `iom_only`, and $-1.228$ pp
[$-2.187$, $-0.285$] for `randproj_iom`. **Every unlinkability contrast is
not distinguishable.** The accuracy the polynomial costs is not buying
unlinkability.

The three arms decompose the cost cleanly:

| Configuration | Voice EER | Attributable to |
|---|---|---|
| No polynomial, full $d = 192$ | 0.273% | — |
| Linear map to $k = 48$ | 0.700% | $+0.427$ pp, the size reduction |
| Keyed polynomial to $k = 48$ | 1.928% | $+1.228$ pp, **the polynomial itself** |

The polynomial costs about 2.9 times more recognition accuracy than the
size reduction it performs, and 5.7 percentage points of true accept rate
at the sealed operating false match rate.

No face contrast is distinguishable, although every face point estimate
also favours a baseline. This is consistent with the power limitation noted
in Section 5.2.

One asymmetry works in the scheme's favour and should be noted. The
configuration $(M^{*}, q^{*}, o^{*})$ was selected to minimise *PolyIoM's*
unlinkability subject to *PolyIoM's* recognition floor. The baselines run
at a configuration tuned for a different pipeline. This makes the finding
conservative rather than inflated.

### 5.5 What the hardening stage does not buy *(secondary)*

#### 5.5.1 Threat model

We evaluate inversion under a full-knowledge adversary who holds the key
$K^{*}$, the projection tensors, the algorithm, **and** the stored
template. This is the worst case, and it is the case an irreversibility
claim has to survive: an attacker who has breached the database holds the
template by definition. If the scheme also requires the key to stay secret,
it is a two-factor system, not a cancelable biometric.

#### 5.5.2 The attack

The attack searches for an input whose protected template matches the
stored one. Because the index-of-maximum operation is not differentiable,
we relax it with a softmax over each group's projections and anneal the
temperature during the search. The objective is cross-entropy against the
stored indices. The candidate is kept on the unit sphere throughout,
because real embeddings are $L_2$-normalised; this constrains the search
and makes the attack stronger, not weaker.

The polynomial is differentiable, so gradients pass through it exactly as
they pass through the linear arms. **The same attack, at the same budget of
five restarts of eight hundred steps, fixed in advance, is applied to all
three arms.** This matters: a scheme can always be made to look secure by
attacking it weakly, and an attack applied only to the proposed method
produces a comparison that means nothing.

#### 5.5.3 Result

**Every template, in every arm, on both modalities, was inverted to
acceptance. The success attack rate is 100% throughout, and the contrasts
are exactly zero.** Under a full-knowledge adversary the scheme is not
irreversible, and the polynomial confers no protection at the level of
acceptance.

The pre-specified headline metric saturated. The attack reaches 128 of 128
matching positions against a threshold of 37, and 256 of 256 against 68.
Any competent attack clears those thresholds, so the success attack rate
cannot discriminate between the arms. The pre-specified secondary measures
can:

| Arm | Mean matching positions | Cosine to true embedding |
|---|---|---|
| PolyIoM | 128.0 of 128 | **0.222** [0.196, 0.248] |
| `iom_only` | 128.0 of 128 | **0.913** [0.910, 0.916] |
| `randproj_iom` | 125.7 of 128 | 0.490 [0.482, 0.498] |

The chance level for the cosine is 0.120, measured between embeddings of
different subjects. A random unit vector matches 9.3, 3.8 and 4.2 positions
respectively, against a chance level of 4.0, which confirms that the scale
is anchored.

Against `iom_only` the attack recovers the embedding almost exactly.
Against PolyIoM it recovers much less. The cosine contrasts are firm.

#### 5.5.4 Why both results are true at once

The two findings look contradictory and are not. **The system matches on
the hardened vector, not on the embedding.** The attack recovers the
hardened vector exactly, which is what 128 of 128 matching positions means,
while recovering comparatively little of the embedding.

The keyed polynomial therefore hides the biometric but not the
representation that is actually compared. This is the central observation
of the paper, and it has a general implication: evaluations that measure
only how well a reconstruction resembles the original feature vector will
miss the attack that matters, because acceptance does not require
resemblance to the feature vector.

### 5.6 What enables revocability *(secondary)*

#### 5.6.1 The question

Section 5.5 shows that the reconstruction does not recover the embedding
for PolyIoM. That raises the question the whole scheme exists to answer:
does the reconstruction still work after the template is revoked?

We re-enrol each subject under fully re-issued parameters. For PolyIoM this
means a fresh polynomial key and a fresh projection. For `randproj_iom` it
means a fresh linear map and a fresh projection. For `iom_only` it means a
fresh projection, which is all that arm has. We then present the attacker's
reconstruction, built from the **old** template. The attacker does not
re-attack; they hold one stolen template, reconstruct once, and the subject
then re-enrols. This is the real revocation scenario.

We report the **post-revocation acceptance rate**, the fraction of subjects
whose old template's reconstruction is still accepted at the sealed
threshold. Revocation works only if this rate falls to near zero. A rate
near 100% means a single stolen template is a permanent credential.

Fresh polynomial keys are drawn by resampling $K^{*}$'s own coefficient and
exponent values. They are not re-selected through Stage A. For this
question that is the right construction, because we are asking whether the
reconstruction resembles the true embedding in the ways any polynomial of
that family sees, not whether a particular new key is a good one.

We use forty fresh key sets. Intervals resample **keys as well as
identities**, because both vary and because an identity-only bootstrap
understates the spread badly when a minority of keys behave differently
from the rest.

#### 5.6.2 Result

| Voice | PRAR | Per-key median / maximum | Keys failing outright |
|---|---|---|---|
| PolyIoM | 7.50% [2.11, 14.44] | 0.00% / 89.66% | 2 of 40 |
| `iom_only` | **100.00%** [100, 100] | 100% / 100% | **40 of 40** |
| `randproj_iom` | 5.73% [4.01, 7.63] | 6.90% / 13.79% | **0 of 40** |

| Face | PRAR | Per-key median / maximum | Keys failing outright |
|---|---|---|---|
| PolyIoM | 25.60% [13.02, 38.58] | 0.00% / 100.00% | 10 of 40 |
| `iom_only` | **100.00%** [100, 100] | 100% / 100% | **40 of 40** |
| `randproj_iom` | 2.89% [1.77, 4.27] | 1.72% / 8.62% | **0 of 40** |

**Finding one: keyed compression is necessary for revocability.** Applied
directly to the raw embedding, IoM hashing fails completely. Every stolen
template remains a valid credential after re-keying, for all forty key sets
on both modalities. The contrasts are $+92.5$ pp on voice and $+74.4$ pp on
face, both firm.

This follows directly from Section 5.5. The attack recovers the embedding
itself at a cosine of 0.913, so re-keying the projection cannot help: the
attacker holds something close to the biometric, and the new projection is
applied to that just as it is applied to the real thing.

**Finding two: that the polynomial is the right compression is not
supported.** PolyIoM's behaviour is bimodal. Its median per-key acceptance
rate is 0.00% on both modalities, meaning revocation is usually perfect,
but it fails catastrophically for a minority of fresh keys: two of forty on
voice, reaching 89.66%, and ten of forty on face, reaching 100%.
`randproj_iom` never does this. Across all eighty key sets, none failed
outright, and its worst case leaks 13.79%.

The voice contrast between the two is not distinguishable ($-1.767$ pp
[$-8.793$, $+3.967$]). The face contrast is firm and favours the linear map
($-22.716$ pp [$-35.864$, $-9.996$]).

Operationally, unpredictable total failure is a worse property than a
small, consistent leak. An operator can budget for a system that lets
through a few per cent on every re-key. An operator cannot budget for a
system that works perfectly most of the time and then, for reasons not
visible at the time of re-keying, does not work at all.

#### 5.6.3 A correction we made during this analysis

An earlier version of this experiment used three fresh keys and
bootstrapped over identities only. It reported the voice contrast between
PolyIoM and `randproj_iom` as firm and in PolyIoM's favour, at $+4.598$ pp
[$+1.724$, $+8.046$]. With forty keys and a bootstrap over both axes the
same contrast is $-1.767$ pp [$-8.793$, $+3.967$], not distinguishable.

The earlier interval was an artifact of resampling the wrong axis. When one
key in three fails completely, an identity-only bootstrap concentrates
around one third and produces an interval of near-zero width. We report
this because it is a general hazard: when a system's behaviour varies
across keys, intervals that resample only subjects will be confidently
wrong.

### 5.7 Summary of evidence

| Property | Verdict |
|---|---|
| Recognition accuracy | The polynomial costs 1.23 pp EER over a linear map of equal output size (firm). |
| Unlinkability | No contrast distinguishable. |
| Irreversibility | 100% success attack rate for every arm. Not irreversible. |
| Concealing the embedding | The polynomial helps: cosine 0.222 against 0.913 (firm). |
| Revocability | Keyed compression is necessary. The polynomial is not better than a linear map, and is worse on face (firm). |

Taken together: **keyed compression before IoM hashing is necessary for
revocability; a keyed random linear projection is sufficient; and on this
evidence the polynomial is not preferable to it.**

---

## 6. Discussion

### 6.1 What the polynomial does, and what it does not

The polynomial was selected to resist inversion. Section 5.5 shows it
partly succeeds at a narrow version of that goal and fails at the one that
matters. It does make the reconstruction resemble the true embedding much
less: cosine 0.222 against 0.913. But it does not stop the reconstruction
being accepted, because acceptance depends on the hardened vector and the
attack recovers that exactly.

This is worth stating carefully, because it is the kind of result that is
easy to report in a misleadingly favourable way. A paper that measured only
reconstruction fidelity would conclude that the polynomial provides strong
protection. That conclusion would be wrong in the way that matters for a
deployed system.

### 6.2 Why revocability turns out to be the binding property

Of the four standard requirements, revocability receives the least
attention in evaluations, and it is the one that separates the designs
here. Recognition performance is similar across arms to within a couple of
percentage points. Unlinkability is not distinguishable at all.
Irreversibility fails uniformly. Revocability is the only property on which
the arms behave qualitatively differently: one of them fails completely and
the others do not.

We think this happens because revocability is the only one of the four that
is tested by a *sequence* of events rather than by a single measurement.
The other three are properties of one template at one moment. Revocability
asks what happens after the attacker acts and the operator responds. That
makes it harder to measure and easier to assume, which is presumably why it
is usually assumed.

### 6.3 Implications for how these schemes are evaluated

Three points generalise beyond the scheme studied here.

**Compare an attack against baselines, not only against the proposal.** Our
success attack rate is 100% for every arm. A paper reporting only the
proposed scheme could have reported a reconstruction cosine of 0.222 and
described it as strong protection. Only the presence of the `iom_only`
baseline, at 0.913, makes it possible to say what the polynomial
contributes, and only the acceptance-rate measurement shows that the
contribution does not matter.

**Ablate multi-stage transforms.** The original sweep varied three
parameters, none of which removed the polynomial. A combination that
performs acceptably is not evidence that each stage is useful. In this case
one stage was actively harmful to accuracy and did not compensate on any
other axis.

**Resample the right axis.** Section 5.6.3 describes an interval that was
confidently wrong because it resampled subjects when the variation was
across keys. Any scheme whose behaviour depends on a drawn key needs
intervals that account for the key.

### 6.4 Design recommendation

On the evidence here, a practitioner building a cancelable scheme on IoM
hashing should compress the embedding under a key before hashing, and
should use a random linear projection to do it. Compression is necessary:
without it, revocation does not work and a stolen template is permanent.
The polynomial is not required: it costs accuracy, adds a catastrophic
failure mode, and improves nothing we could measure other than
reconstruction fidelity, which does not translate into resistance to
acceptance.

We state this as a recommendation supported by held-out comparison, not as
a validated design. Section 7 records why.

---

## 7. Limitations

1. **Statistical power.** All held-out inference rests on 58 identities.
   Face gives 259 genuine trials and an equal error rate interval spanning
   a five-fold range. Face is reported descriptively, and no face
   comparison in Section 5.2 is claimed.

2. **One external corpus, one modality.** VCTK validates the voice system.
   No external face corpus was available, so the face results have no
   external estimate.

3. **One attack family.** Section 5.5 measures practical inversion
   resistance under a stated budget. It is not a proof of
   information-theoretic irreversibility. A perfect solution provably
   exists in the search space, since the true embedding reproduces the
   stored template exactly, so a failure to find one would be a statement
   about optimisation difficulty rather than about information. A stronger
   attack can only increase attacker success, so the direction of our
   finding is safe; the magnitudes are lower bounds on what an attacker can
   achieve.

4. **Construction of fresh keys.** Fresh polynomial keys are resampled from
   the selected key's own coefficient and exponent values rather than
   re-selected through Stage A. This is appropriate for the question asked
   in Section 5.6, but it means the fresh keys are not distributed exactly
   as deployed keys would be.

5. **An unexplained failure mode.** We cannot explain why twelve of eighty
   fresh key sets produce catastrophic post-revocation acceptance for
   PolyIoM. The failing keys are not degenerate; all forty passed a check
   that the re-keyed system still separates different subjects. The
   asymmetry between modalities, five per cent on voice against twenty-five
   on face, is likewise unexplained. This is the weakest point in the
   argument of Section 5.6.

6. **The preferred configuration was never sealed.** `randproj_iom` was
   introduced as an ablation arm. It has no operating point selected under
   the pre-registered rule, and no external validation. The recommendation
   in Section 6.4 therefore rests on a held-out comparison conducted at
   PolyIoM's sealed configuration, not on the full protocol.

7. **Asymmetric enrolment.** Face enrolment uses a single embedding; voice
   enrolment uses the mean of five. This is a deliberate consequence of the
   data available and contributes to the difference between modalities.

8. **Dataset provenance.** The exclusion list used to prevent overlap
   between face corpora was obtained from a third-party mirror whose
   release metadata could not be verified against the original host. Its
   scope is exact-name exclusion, not alias resolution.

---

## 8. Conclusion

We set out to measure what a keyed polynomial hardening stage contributes
to a cancelable biometric scheme built on index-of-maximum hashing. Under a
pre-registered protocol with sealed operating points, and three further
analyses conducted at that sealed configuration, the answer is mostly that
it does not contribute.

The polynomial costs 1.23 percentage points of equal error rate against a
random linear map of the same output size. It does not improve
unlinkability. It does not prevent inversion: under a full-knowledge
adversary, every template in every arm was reconstructed to acceptance. It
does conceal the underlying embedding, but that turns out not to matter,
because the system compares hardened vectors and the attack recovers those
exactly.

What does matter is compression under a key. Without it, index-of-maximum
hashing is not revocable at all: in our tests a stolen template remained a
valid credential after re-keying in every one of eighty trials. With it,
revocation works. A random linear projection performs that role more
accurately than the polynomial, at least as reliably, and without the
polynomial's catastrophic failure mode.

The broader lesson concerns evaluation rather than design. Three of the
four standard requirements for a cancelable scheme can be measured on a
single template at a single moment. The fourth cannot, and it is the one
that distinguished the designs we compared. Schemes of this kind should be
evaluated by attacking them and their baselines with the same attack, by
ablating their stages, and by testing what happens after a template is
revoked rather than assuming that using a key is sufficient.

---

## 9. What a literature pass must supply

No reference in this draft has been invented. The following claims need
citations, and the bibliographic details of each must be verified before
submission.

| Location | Claim needing support |
|---|---|
| §1.1 | Standards requirement for biometric template protection (ISO/IEC 24745) |
| §1.1 | The four-criteria formulation of cancelable biometrics |
| §2.1 | Original cancelable-biometrics proposal (Ratha and colleagues) |
| §2.1 | BioHashing and the random-projection family (Teoh and colleagues) |
| §2.1 | Stolen-token attacks on BioHashing |
| §2.1 | Reconstruction attacks on random-projection schemes |
| §2.2 | Index-of-maximum hashing (Jin and colleagues) |
| §2.3 | Unlinkability framework (Gómez-Barrero and colleagues) |
| §3.2 | FaceNet |
| §3.2 | ECAPA-TDNN |
| §4.1 | LFW, LibriSpeech, VCTK, CFP-FP |
| §2.3 | Evidence for the three evaluation habits described; if no survey supports these, soften to observations about the works cited |

A further section that this draft does not contain is a quantitative
comparison against published cancelable schemes on the same corpora.
Protocols differ enough that a table may be misleading, in which case a
discussion paragraph is the honest substitute. Either way its absence will
be noticed.

---

## Figures and tables

| Item | Content | Status |
|---|---|---|
| Figure 1 | How a protected template is built | Drawn |
| Figure 2 | How two protected templates are compared | Drawn |
| Figure 3 | Design space: $D_{\mathrm{sys}}$ over $M \times q$ for each overlap | Drawn |
| Figure 4 | Recognition–unlinkability trade-off frontier | Drawn |
| Figure 5 | Development, held-out and external results with intervals | Drawn |
| Figure 6 | Ablation: the three arms on EER and $D_{\mathrm{sys}}$ | To draw |
| Figure 7 | Per-key post-revocation acceptance, showing the bimodal failure | To draw |
| Table 1 | Sealed operating points | §5.1 |
| Table 2 | Held-out results | §5.2 |
| Table 3 | External results | §5.3 |
| Table 4 | Ablation | §5.4 |
| Table 5 | Inversion | §5.5 |
| Table 6 | Revocation | §5.6 |

Figures 6 and 7 do not yet exist. Figure 7 matters most: the bimodal
failure in Section 5.6 is the hardest part of the argument to convey in a
table, and a strip plot of per-key acceptance rates would make it
immediate.

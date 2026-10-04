# Presentation Guide: AttackAware PolyIoM

A slide-by-slide guide to AttackAware_PolyIoM_paper.pptx (24 slides).

## Key terms

- Template: the data a biometric system stores about a person instead of the photo or voice recording.
- Cancelable biometric: a template scrambled with a secret key, so a stolen copy can be cancelled by issuing a new key.
- EER (equal error rate): the error rate at the point where real users are wrongly rejected as often as strangers are wrongly accepted. Lower is better.
- pp (percentage points): the plain difference between two percentages. From 1% to 3% is 2 pp.
- Dsys (linkability): how easily two templates of the same person, made with different keys, can be linked. 0 means not at all, 1 means fully.
- Firm: a difference whose 95% confidence interval does not include zero.

## Part 1: The question

### Slide 1: Title

The title states the main finding: compressing the data under a secret key is what allows a stolen template to be cancelled. Pre-registered means the test rules were fixed before the test data were examined.

Say: This talk is about protecting stored face and voice data, and about which part of the protection lets you cancel a stolen copy.

### Slide 2: Abstract

The paper in four points:

1. The scheme: a secret polynomial transforms a face or voice embedding, and Index-of-Maximum (IoM) hashing follows.
2. It works: voice error is 1.93% on 58 unseen speakers and 2.80% on 110 speakers from an independent dataset. Linkability is low: 0.088 and 0.080.
3. It has a price and hides the biometric: protection costs 1.84 pp of accuracy on unseen speakers and 2.79 pp on the independent set. An attacker who knows everything recovers only a weak copy of the embedding (cosine 0.222, against 0.913 without the polynomial).
4. Revocation needs keyed compression: plain IoM hashing could not be revoked in any of 80 new key sets.

Say: The system recognises people well, keeps templates unlinkable, hides the biometric and can be revoked. Each of these has a measured cost or limit.

### Slide 3: The problem (Section 1.1)

Passwords can be changed; faces and voices cannot. The ISO/IEC 24745 standard sets four requirements for a protected template:

1. Recognition performance: it still tells people apart well.
2. Irreversibility: a stolen template does not give back the face or voice.
3. Unlinkability: templates of one person under two keys cannot be matched.
4. Revocability: after a theft, a new key makes the old template useless.

The first three can be checked on one template. Revocability needs a before-and-after test, so it is rarely measured. This paper measures it.

Say: Most studies check the first three requirements. We also test the fourth.

### Slide 4: The scheme, and what this paper asks (Sections 1.2 to 1.3)

The pipeline has four steps: embedding, keyed polynomial, IoM hashing under a second key, stored template. The paper asks three questions:

1. Is IoM hashing alone revocable? No. An attacker rebuilds the original embedding almost exactly (cosine 0.913). It does not depend on any key, so it still works after a key change: 80 of 80 key sets.
2. What makes it revocable? Compressing under a key before hashing. The polynomial and a simple keyed linear map both do this.
3. What does the polynomial add? It hides the biometric better: cosine 0.222, against 0.490 for the linear map and 0.120 at chance. It costs 1.23 pp of voice accuracy.

Say: Revocation comes from keyed compression. The polynomial adds concealment, at a price.

### Slide 5: Contributions and summary of findings (Sections 1.4 to 1.5)

The study adds six things to the usual evaluation:

- an ablation, which removes one part at a time;
- the same inversion attack on every version;
- a revocation test;
- a comparison with the unprotected system;
- an explanation of what each stage does;
- a pre-registered protocol.

The four headline numbers are 1.93% voice error, 0.088 linkability, 0.222 recovered similarity and 80 of 80 raw-IoM failures to revoke.

Say: Our contribution is a fairer way of testing such schemes, applied to this one.

### Slide 6: Background and related work (Section 2)

Cancelable biometrics store a transformed version of the data. Simple random projections are well known, but can be undone with a stolen key. IoM hashing keeps only which projection was largest in each group, so no values are stored.

The field often has three weaknesses:

- the threshold is chosen on the reported data;
- multi-step designs are not tested step by step;
- irreversibility is argued rather than measured.

This study addresses all three and adds a revocation test.

Say: We test the parts the field usually takes on trust.

## Part 2: The method

### Slide 7: Overview and frozen encoders (Sections 3.1 to 3.2)

Public, standard models turn data into numbers: FaceNet turns a photo into 512 numbers, and ECAPA-TDNN turns a voice clip into 192 numbers. They are frozen, which means they are used as published and never retrained. So any difference comes from the protection scheme, not the model.

Say: We used standard models unchanged, so the results reflect the protection itself.

### Slide 8: Hardening, IoM-GRP and matching (Sections 3.3 to 3.5)

Three steps:

1. Hardening: a secret polynomial is applied to small overlapping windows of the embedding. For voice, this reduces 192 numbers to 48.
2. Hashing: the 48 numbers are projected many times under a second key. Only the position of the largest value in each group is stored.
3. Matching: two templates are compared by counting how many groups agree. Above a fixed threshold, the person is accepted.

Say: The stored template is a list of positions, and matching means counting how many agree.

### Slide 9: Selecting the key, then the operating point (Sections 3.6 to 3.7)

Stage A screened thousands of candidate keys using 50 background identities, then locked in the best one. Stage B tried 80 settings on 42 development identities. It chose the one with the lowest linkability that met the accuracy target, and locked that in too.

The screening in Stage A only helped choose a key. The real attack test is in Section 5.5.

Say: Every choice was made on separate data and locked before the test data were opened.

### Slide 10: Identities, partitions and sealing (Sections 4.1 and 4.4)

People were split once, at random, into four groups:

- 50 background identities, for choosing the key;
- 42 development identities, for choosing the settings;
- 58 evaluation identities, for the main test, opened only after locking;
- 110 external speakers from the VCTK dataset, opened last.

The key, settings and threshold were sealed in a record that no later analysis could change.

Say: No one in the test group was seen while the system was being tuned.

### Slide 11: Metrics and confidence intervals (Sections 4.2 to 4.3)

- EER: overall error rate.
- TAR and FMR: at the locked threshold, how often real users are accepted (TAR) and how often strangers are wrongly accepted (FMR).
- Dsys: linkability.
- SAR: how often the attack produces an input the system accepts.
- PRAR: how often an old stolen template still works after a key change. Lower is better.

Intervals come from resampling the people 2,000 times. For revocation, the keys are resampled as well.

Say: We call a difference real only when its uncertainty range excludes zero.

### Slide 12: Implementation, frameworks and provenance (Section 4.6)

The software is PyTorch, facenet-pytorch, SpeechBrain, NumPy, pandas and SciPy, each with a pinned version. The datasets are LFW for faces, and LibriSpeech and VCTK for voices. All random choices start from one seed, 2026, so the study can be repeated exactly.

Say: Every tool and dataset is recorded so others can repeat the work.

## Part 3: The results

### Slide 13: Sealed operating points (Section 5.1, confirmatory)

The locked voice setting reached 0.952% error on the development group. No face setting met the voice target of 1% error and 95% acceptance: the best reached 2.29% and 90.08%.

The face target was therefore relaxed to 3% and 85%, before any test data were opened. The face model alone, with no protection, already has 3.475% error.

Say: We relaxed the face target openly, before testing, because the face model alone could not meet the stricter one.

### Slide 14: Generalisation to held-out identities (Section 5.2, confirmatory)

On unseen people:

- Voice error is 1.93% (range 1.09% to 2.92%).
- Face error is 4.80%, with a wider range.
- Protection costs 1.84 pp on unseen voice and 2.79 pp on the external voice set. Both costs are firm.
- The face cost (1.32 pp) cannot be resolved.

No ratio is given, because the unprotected voice system made almost no errors.

Say: Protection costs about two percentage points on voice, and we are sure of that cost. On face we cannot yet tell.

### Slide 15: External validation on voice (Section 5.3, confirmatory)

The system was locked on one voice dataset and applied unchanged to another (110 VCTK speakers). Results:

- error 2.80%;
- acceptance 89.00%;
- linkability 0.080.

There is no reliable sign of a drop. The one target missed is false acceptance: 0.377%, above the 0.1% aim.

Say: Tested on new data without changes, the system held up. The one miss is reported as it is.

### Slide 16: What the hardening stage costs (Section 5.4, secondary)

Three versions were compared: PolyIoM, a keyed linear map, and IoM hashing alone. On voice, the 1.928% error splits into three parts:

- 0.273% from hashing alone;
- 0.427 pp from reducing 192 numbers to 48;
- 1.228 pp from the polynomial itself, which is a firm cost.

Linkability does not differ reliably between the versions.

Say: The polynomial accounts for most of the accuracy cost. The next slide shows what it buys.

### Slide 17: What the hardening stage does not buy (Section 5.5, secondary)

The strongest attacker was simulated: one who holds the keys, the algorithm and the stored template. Two findings:

1. The attacker always gets in (100%). In every version, they found an input the system accepts, because the system compares transformed vectors and the attacker only needs to reproduce one.
2. The polynomial hides the person. The rebuilt vector resembles the real voice embedding only weakly with the polynomial (0.222, near chance at 0.120). It is closer with the linear map (0.490) and very close with no protection (0.913).

Say: The attacker can open the lock, but cannot recover the person's real biometric. That is why revocation matters.

### Slide 18: What enables revocability (Section 5.6, secondary)

The keys were changed 40 times for each modality, 80 in total. How often did the old stolen template still work?

- Raw IoM: every time, in 80 of 80 key sets. Revocation fails.
- PolyIoM: 7.5% on average for voice and 25.6% for face. For most keys, none worked. In 12 of 80 key sets, half or more still worked; the cause is not yet known.
- Linear map: low and steady. No key set left half exposed.

An earlier analysis with 3 keys suggested that PolyIoM was clearly worse than the linear map. With 40 keys that difference disappeared, and the claim was withdrawn.

Say: Without keyed compression, revocation does not work. With it, revocation works in most cases.

### Slide 19: Summary of evidence (Section 5.7)

One table brings together all four requirements and the strength of the evidence for each. Confirmatory results were planned in advance and tested once; secondary results were added afterwards.

The bottom line: keyed compression gives revocability, the polynomial gives concealment, and choosing between them is a trade.

Say: All four requirements in one place, each marked by how strong its evidence is.

## Part 4: Meaning and limits

### Slide 20: Discussion (Sections 6.1 to 6.3)

1. The polynomial hides the biometric but does not stop a forged match. Judging protection only by how well the face can be rebuilt would overstate safety.
2. Revocability is the property that separates the designs: they differ little in accuracy, not at all in linkability, and all fail the forged-match test.
3. For the field: attack the baselines with the same attack, test each stage separately, and resample keys as well as people.

Say: The property that truly separates the designs is the one usually left untested.

### Slide 21: Design recommendation (Section 6.4)

Keyed polynomial:

- voice error 1.928%;
- hides the biometric better (0.222 voice, 0.418 face);
- 12 of 80 key sets revoke poorly.

Choose it when losing the face or voice itself is the main risk.

Keyed linear map:

- voice error 0.700%, which is 1.23 pp better;
- hides the biometric less (0.490 voice, 0.492 face);
- revokes reliably (0 of 80 key sets fail).

Choose it when a stolen credential is the main risk.

Either way, always compress under a key before hashing.

Say: Pick the polynomial when protecting the biometric matters most, and the linear map when accuracy and reliable revocation matter most.

### Slide 22: Limitations (Section 7)

1. The test group is modest (58 people); face results are descriptive only.
2. Only one external dataset was used, and only for voice.
3. Only one attack type was tried.
4. Fresh keys were not re-screened through Stage A.
5. Why 12 of 80 PolyIoM key sets fail is not yet known.
6. The linear map was not tuned separately.
7. Face enrolment uses one photo; voice uses five clips.
8. Unprotected voice made almost no errors, so only bounds are given.
9. The face model limits face error to about 3%.
10. One exclusion list came from an unverified copy.

Say: These set the right level of confidence. None reverses the main findings.

### Slide 23: Conclusion (Section 8)

Keyed compression gives revocability, and the polynomial gives concealment. The choice between them is a trade. The headline numbers:

- 1.93% voice error on unseen speakers;
- 80 of 80 raw-IoM key sets fail to revoke;
- 0.222 against 0.490 recovered similarity.

One command (python3 run.py verify) re-checks every number. It runs 74 checks and 29 unit tests.

Say: Compress under a key to make templates cancellable. Add the polynomial if hiding the biometric is worth a little accuracy.

### Slide 24: Declarations

- AI use: an AI assistant helped with secondary analysis code, figures, the reproducibility package and the writing. The core design and the main locked results came first.
- Data and code: code, results and tests are released. Embeddings are not shared, because they still count as biometric data.
- Ethics: only public datasets were used, and only the authors' own templates were attacked.

Say: We state openly how AI was used, what we share, and why there are no ethical concerns.

## Three points to remember

1. Keyed compression makes revocation possible. Without it, a stolen template works forever.
2. The polynomial hides the biometric: 0.222 against 0.490 for a linear map.
3. It is a trade. The polynomial costs about 1.2 pp of voice accuracy and gives less uniform revocation.

## Likely questions

Why not just use the linear map? It reveals more of the biometric, and a leaked face or voice can never be replaced.

How do we know the results were not tuned? Settings were chosen on separate people and locked before testing, and an independent dataset was tested last.

Can others reproduce this? Yes. Versions are pinned, one seed is used, and one command re-derives every number.

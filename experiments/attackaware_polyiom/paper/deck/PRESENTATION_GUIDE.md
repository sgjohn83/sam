# Presentation Guide: AttackAware PolyIoM

*A slide-by-slide companion to `AttackAware_PolyIoM_paper.pptx`*

This guide explains each of the 24 slides in plain language. For every slide it gives:

- **What the slide shows**: what is on the screen.
- **What it means**: the idea behind it, in plain words.
- **Suggested wording**: one or two sentences the presenter can say aloud.

Some slides also have **If asked**: a short answer to a question the audience is likely to raise.

The slides follow the paper's own sections in order, so the guide doubles as a short reading guide to the paper itself. Every number here comes from the stored results. None was typed in by hand.

---

## Before you start: six terms in plain language

| Term | Plain meaning |
|---|---|
| **Template** | What a biometric system stores about a person instead of the photo or recording. Here it starts as a list of numbers called an *embedding*. |
| **Cancelable biometric** | A template that is scrambled with a secret key, so that a stolen copy can be cancelled by issuing a new key. A password can be reset this way; a face or voice cannot, so the key does the job. |
| **EER (equal error rate)** | How often the system makes mistakes, measured at the point where it wrongly rejects real users exactly as often as it wrongly accepts strangers. Lower is better. |
| **pp (percentage points)** | The plain difference between two percentages. Going from 1% to 3% is a rise of 2 pp. |
| **D<sub>sys</sub> (linkability)** | How easily two templates of the same person, made with different keys, can be recognised as belonging together. 0 means impossible; 1 means trivial. |
| **Confidence interval [a, b]** | The range in which the true value very likely lies (95% confidence). When the interval for a difference does not include zero, we call the difference **firm**. |

---

## Part 1: The question

### Slide 1: Title

**What the slide shows.** The paper's title, *"Keyed compression is what makes an IoM-based cancelable biometric revocable"*, the subtitle *"A pre-registered evaluation on face and voice"*, and a picture of how a protected template is built.

**What it means.** The title states the main finding. One specific step in the design, compressing the data under a secret key, is the step that lets a stolen template be cancelled. "Pre-registered" means the rules of the test were fixed before the test data were examined.

**Suggested wording.** *"This talk is about protecting stored face and voice data, and about which part of the protection actually lets you cancel a stolen copy."*

### Slide 2: Abstract

**What the slide shows.** Four numbered cards: the scheme, recognition and unlinkability, cost and concealment, and revocability.

**What it means.** This slide is the whole paper in four sentences:

1. **The scheme.** A face or voice embedding is first transformed by a secret polynomial. It is then hashed by a method called Index-of-Maximum (IoM).
2. **It works.** On 58 speakers the system had never seen, the voice error rate is 1.93%. On a second, independent set of 110 speakers it is 2.80%, with no reliable sign of a drop. Linkability is low (0.088 and 0.080).
3. **It has a price, and it hides the biometric.** Protection costs about 1.84 pp of accuracy on unseen speakers and 2.79 pp on the independent set. An attacker who knows everything can rebuild only a rough copy of the original embedding: a similarity score (cosine) of 0.222, compared with 0.913 when the polynomial step is removed.
4. **Revocation needs keyed compression.** Hashing the raw embedding cannot be revoked: old templates still worked in all 80 of 80 new key sets. Adding keyed compression fixes this.

**Suggested wording.** *"The system recognises people well, keeps templates unlinkable, hides the original biometric, and can be revoked. Each of these has a measured cost or limit, and we report them all."*

### Slide 3: The problem (§1.1)

**What the slide shows.** The phrase *"Passwords can be changed. Biometrics cannot."* and the four requirements a protected template must meet. These come from the international standard ISO/IEC 24745.

**What it means.** A protected template has to pass four tests:

1. **Recognition performance**: it still tells people apart well.
2. **Irreversibility**: a stolen template does not give back the face or voice.
3. **Unlinkability**: two templates of the same person, made with different keys, cannot be matched to each other.
4. **Revocability**: after a theft, a new key makes the old template useless.

The first three can be checked on a single template. The fourth needs a "before and after" test, which is why it is rarely measured. This paper measures it.

**Suggested wording.** *"Most studies check the first three. Revocability needs a before-and-after test, and that is the one we focus on."*

### Slide 4: The scheme, and what this paper asks (§1.2–1.3)

**What the slide shows.** A four-step pipeline: embedding → keyed polynomial → IoM hashing under a second key → stored template. Below it are three questions with short answers.

**What it means.** The design has two secret-key stages. The paper asks three questions about them:

1. **Is IoM hashing on its own revocable?** No. An attacker can rebuild the original embedding almost exactly (cosine 0.913). The embedding does not depend on any key, so it keeps working after a key change: in 80 of 80 key sets.
2. **What makes the system revocable?** Compressing the embedding under a key *before* hashing. The attacker then rebuilds only a key-specific vector, which stops working when the key changes. Either a polynomial or a simple keyed linear map does this.
3. **What does the polynomial add on top?** It hides the biometric better: cosine 0.222, against 0.490 for the linear map and 0.120 for pure chance. The cost is 1.23 pp of voice accuracy.

**Suggested wording.** *"Revocation comes from compressing under a key. The polynomial's extra contribution is hiding the biometric, and that has a price."*

### Slide 5: Contributions and summary of findings (§1.4–1.5)

**What the slide shows.** Six contributions on the left. Four headline numbers on the right: 1.93%, 0.088, 0.222 and 80/80.

**What it means.** The contributions are the methods this study added to the usual evaluation:

- An **ablation**, which removes one part at a time to see what each part does.
- An **inversion attack**, applied equally to every version of the system.
- A **revocation test**.
- A comparison of every result against the **unprotected system**.
- An explanation of **why** each stage behaves as it does.
- A **pre-registered protocol**.

The four numbers summarise what the final system achieves.

**Suggested wording.** *"Our contribution is not only a scheme. It is a fairer way of testing such schemes, and we apply it."*

### Slide 6: Background and related work (§2)

**What the slide shows.** Three cards (cancelable biometrics, Index-of-Maximum hashing, how schemes are usually evaluated) and a highlighted box titled "The gap".

**What it means.**

- **Cancelable biometrics** store a transformed version of the data, not the data itself. Simple random-projection methods are well known, but can be undone if the key is stolen.
- **IoM hashing** projects the data many times and keeps only *which* projection was largest in each group. No sizes are kept, so many inputs give the same code.
- **The usual weaknesses in the field** are threefold. The decision threshold is chosen on the same data that is reported. Multi-step designs are not tested one step at a time. Irreversibility is argued in words rather than measured with an attack.
- **The gap.** This study fixes all three, and adds a revocation test the authors have not seen reported elsewhere.

**Suggested wording.** *"We follow the field's own standards, but we test the parts it usually takes on trust."*

---

## Part 2: The method

### Slide 7: Overview and frozen encoders (§3.1–3.2)

**What the slide shows.** Two columns. Face (in blue) uses FaceNet, which gives a 512-number embedding. Voice (in green) uses ECAPA-TDNN, which gives a 192-number embedding.

**What it means.** The study uses well-known, publicly available models that turn a photo or a voice clip into a list of numbers. These models are **frozen**: they are used exactly as published, never retrained. This keeps the test about the protection scheme, not about a better model. Exact versions are pinned so that anyone can reproduce the results.

**Suggested wording.** *"We did not train any recognition model. We used standard ones unchanged, so that any difference we see comes from the protection itself."*

### Slide 8: Hardening, IoM-GRP and matching (§3.3–3.5)

**What the slide shows.** Two diagrams: how a protected template is built, and how two templates are compared. Three short explanations sit beside them.

**What it means.**

- **Hardening.** A secret polynomial is applied to small overlapping windows of the embedding. For voice, this shrinks 192 numbers to 48 numbers.
- **IoM-GRP hashing.** The 48 numbers are projected many times under a second key, R. Only the position of the largest value in each group is stored.
- **Matching.** Two templates are compared by counting how many groups show the same position. If the count reaches a fixed threshold, τ\*, the person is accepted.

**Suggested wording.** *"The stored template is just a list of positions, such as 3, 1, 4. Matching means counting how many positions agree."*

### Slide 9: Selecting the key, then the operating point (§3.6–3.7)

**What the slide shows.** Stage A (choosing the polynomial key) and Stage B (choosing the settings), plus a warning box.

**What it means.**

- **Stage A.** Thousands of candidate keys were screened, using only 50 "background" identities. The best key that kept recognition working was locked in. Its name is K\*.
- **Stage B.** Eighty combinations of settings were tried on a separate group of 42 "development" identities. The combination with the lowest linkability that still met the accuracy target was chosen and locked.
- **Warning box.** The screening test in Stage A helped *choose* a key. It is not evidence that the key resists attack. That evidence comes later, in §5.5.

**Suggested wording.** *"Every choice was made on data kept separate from the final test, and then locked before the test data were opened."*

### Slide 10: Identities, partitions and sealing (§4.1, 4.4)

**What the slide shows.** A diagram of how people were split into groups. Four number tiles: 50, 42, 58 and 110.

**What it means.** People were divided once, at random, into separate groups, each used for one purpose only:

| Group | Size | Purpose |
|---|---|---|
| Background | 50 | Choosing the key |
| Development | 42 | Choosing the settings |
| Evaluation | 58 | The main test, opened only after everything was locked |
| External | 110 | A second, independent voice dataset (VCTK), opened last |

**Sealing** means the key, settings and threshold were written into a locked record, and every later analysis checks that it changed nothing.

**Suggested wording.** *"No one in the test group was ever seen while the system was being tuned. This is what makes the results honest."*

### Slide 11: Metrics and confidence intervals (§4.2–4.3)

**What the slide shows.** Definitions of the measures used, and how the confidence intervals were computed.

**What it means.**

- **EER**: the overall error rate (see the glossary above).
- **TAR and FMR**: at the locked threshold, how often real users are accepted (TAR) and how often strangers are wrongly accepted (FMR).
- **D<sub>sys</sub>**: linkability, from 0 (none) to 1 (full).
- **SAR**: how often the attack produces an input the system accepts.
- **PRAR**: after a key change, how often the *old* stolen template is still accepted. Lower is better.
- **Firm**: a difference whose confidence interval does not include zero.

The intervals come from **bootstrapping**: re-drawing the people at random 2,000 times and recomputing each result. For revocation, the keys are re-drawn too, because results vary from key to key.

**Suggested wording.** *"We only call a difference real when its uncertainty range excludes zero, and we resample whatever actually varies: people, and keys where relevant."*

### Slide 12: Implementation, frameworks and provenance (§4.6)

**What the slide shows.** Two tables. The first lists the software (PyTorch, facenet-pytorch, SpeechBrain, NumPy, pandas, SciPy) with exact versions. The second lists the datasets (LFW for faces, LibriSpeech and VCTK for voices) and how much of each was used.

**What it means.** This slide records exactly *what* was used, so that others can repeat the work. All random choices start from one fixed seed (2026). The hashing runs in a fixed, repeatable mode.

**Suggested wording.** *"Every tool and dataset is named with its version, so the study can be repeated exactly."*

---

## Part 3: The results

### Slide 13: Sealed operating points (§5.1, confirmatory)

**What the slide shows.** A table of the locked settings for voice and face, a chart of how they were chosen, and a note that the face target was relaxed.

**What it means.** For voice, the chosen setting reached 0.952% error on the development group. Face is harder. No face setting met the voice target (EER ≤ 1% and TAR ≥ 95%): the best of 80 settings reached 2.29% EER and 90.08% TAR. The face target was therefore relaxed to 3% and 85%. This was decided *before* any test data were opened. The face model itself, with no protection at all, already has a 3.475% error rate, so the strict target was not realistic for face.

**Suggested wording.** *"We relaxed the face target openly, and before testing, because the face model alone could not meet the stricter one."*

### Slide 14: Generalisation to held-out identities (§5.2, confirmatory)

**What the slide shows.** A results table for the test group, a bar chart comparing protected and unprotected error rates, and three labelled findings.

**What it means.**

- On unseen speakers, voice gives **1.93% error**, with a range of 1.09% to 2.92%. Face gives 4.80%, with a much wider range because face has fewer reliable samples.
- **Cost of protection**: +1.84 pp on unseen voice and +2.79 pp on the external voice set. Both are **firm**.
- For face, the cost (+1.32 pp) **cannot be resolved**: the uncertainty is too large to tell.
- No "times worse" ratio is quoted. The unprotected voice system made fewer than one mistake on real users, so any ratio would be misleading.

**Suggested wording.** *"Protection costs about two percentage points on voice. We are sure of that cost. On face we cannot yet tell."*

### Slide 15: External validation on voice (§5.3, confirmatory)

**What the slide shows.** Four number tiles (2.80%, 89.00%, 0.080 and 0.377%) and a chart comparing the main test with the external test.

**What it means.** The system was locked using one voice dataset (LibriSpeech) and then applied, unchanged, to a completely different one (VCTK, 110 speakers). The error rate was 2.80%. There is no reliable evidence that it got worse when moving to new data. Linkability was even lower (0.080). The one target not met is the false-acceptance rate: 0.377%, above the 0.1% aim. The paper reports this openly.

**Suggested wording.** *"Locked on one dataset and tested on another, the system held up. The one miss, the false-acceptance rate, is reported as it is."*

### Slide 16: What the hardening stage costs (§5.4, secondary)

**What the slide shows.** Three versions of the system:

- **PolyIoM**: polynomial, then hashing.
- **Linear map**: a simple keyed linear map, then hashing.
- **Raw IoM**: hashing only.

A stacked bar chart splits the error into parts.

**What it means.** This is the ablation: remove one step at a time and see what changes. On voice:

| Part | Error added |
|---|---|
| Hashing alone (the starting point) | 0.273% |
| Shrinking from 192 to 48 numbers | +0.427 pp |
| The polynomial itself | +1.228 pp |
| **Total** | **1.928%** |

So the polynomial is the largest single cost, and that cost is firm. Linkability does not differ in any reliable way between the versions.

**Suggested wording.** *"Breaking the cost into parts shows that the polynomial is responsible for most of it. The next slide shows what that cost pays for."*

### Slide 17: What the hardening stage does not buy (§5.5, secondary)

**What the slide shows.**

- A threat-model box: the attacker knows everything except the person's real biometric.
- A large "100%".
- A chart of how close each attack gets to the true embedding.

**What it means.** The strongest possible attacker was simulated: they hold the keys, the algorithm and the stored template. Two findings follow:

1. **The attacker always gets in (100%).** In every version, the attacker found *some* input the system accepted. This happens because the system compares transformed vectors, and the attacker only needs to reproduce one of those.
2. **The polynomial hides who the person is.** The rebuilt vector resembles the real voice embedding only weakly with the polynomial (cosine 0.222, near chance at 0.120). It is closer with the linear map (0.490) and very close with no protection (0.913).

Put simply, the attacker can open the lock, but cannot recover the person's actual voice or face.

**Suggested wording.** *"An all-knowing attacker can always forge a match. With the polynomial, though, they learn very little about the real person's biometric."*

**If asked: "Isn't 100% attack success a failure?"** It reflects the strongest attacker, one who already holds every key. It shows why revocation matters: once a theft is known, the keys are changed. The next slide tests whether that works.

### Slide 18: What enables revocability (§5.6, secondary)

**What the slide shows.** A chart of PRAR (how often an old stolen template still works after a key change), three tiles (80/80, 12/80 and 0/80), a per-key plot, and a box titled "A correction we made".

**What it means.** After each of 40 fresh key changes per modality (80 in total):

- **Raw IoM**: the old template still worked every time (100%, 80 of 80 key sets). Revocation fails completely.
- **PolyIoM**: on average, only 7.5% of old voice templates still worked (25.6% for face). For most keys, none did. In 12 of the 80 key sets, though, half or more still worked; in 8 of those, all of them did. The cause is not yet known.
- **Linear map**: low and steady. No key set left half or more exposed (0 of 80).

**The correction.** An earlier, smaller analysis (3 keys) suggested that PolyIoM was clearly worse than the linear map. With 40 keys and a more careful method, the difference disappeared. The earlier claim was withdrawn, and the paper says so.

**Suggested wording.** *"Without keyed compression, revocation simply does not work. With it, revocation works in most cases. We also report a claim we had to withdraw when we tested more keys."*

### Slide 19: Summary of evidence (§5.7)

**What the slide shows.** One table: each of the four requirements, what the system does, and whether the evidence is *confirmatory* or *secondary*.

**What it means.** "Confirmatory" results were planned in advance and tested once. "Secondary" results were added afterwards and are reported as supporting evidence. The bottom line reads: *keyed compression gives revocability; the polynomial gives concealment; choosing between them is a trade.*

**Suggested wording.** *"Here are all four requirements in one place, each marked with how strong its evidence is."*

---

## Part 4: Meaning and limits

### Slide 20: Discussion (§6.1–6.3)

**What the slide shows.** Three cards.

**What it means.**

1. **What the polynomial does and does not do.** It hides the biometric, but it does not stop a forged match. Judging protection by "how well can the face be rebuilt" alone would overstate how safe the system is.
2. **Why revocability is the deciding property.** The three versions differ only a little in accuracy, not at all in linkability, and all fail the forged-match test. Revocation is the one property that clearly separates them.
3. **Lessons for the field.** Attack the simple baselines with the same attack as the proposed scheme. Test each stage separately. When results depend on keys, resample the keys as well as the people.

**Suggested wording.** *"The property that truly separates the designs is the one that is usually left untested."*

### Slide 21: Design recommendation (§6.4)

**What the slide shows.** A side-by-side comparison of the keyed polynomial and the keyed linear map, joined by a vertical bar labelled "TRADE".

**What it means.** Neither option is better in every way.

| | Keyed polynomial | Keyed linear map |
|---|---|---|
| Accuracy (voice EER) | 1.928% | 0.700% (better by 1.23 pp, firm) |
| Hides the biometric (cosine; lower is better) | 0.222 voice, 0.418 face | 0.490 voice, 0.492 face |
| Revocation | 12 of 80 key sets leave half or more exposed | 0 of 80 |
| Choose it when | the main risk is someone recovering a face or voice, which can never be replaced | the main risk is a stolen credential, which a new key repairs |

Whichever is chosen, **always compress under a key before hashing**. Without that step, a stolen template can never be cancelled.

**Suggested wording.** *"Pick the polynomial if losing the biometric itself is the worst outcome. Pick the linear map if accuracy and dependable revocation matter more. Never skip the keyed compression."*

### Slide 22: Limitations (§7)

**What the slide shows.** Ten numbered limitations, one line each.

**What it means.** These are the honest boundaries of the study, in plain terms:

1. The test group (58 people) is modest. Face results are descriptive only.
2. Only one external dataset was used, and only for voice.
3. Only one type of attack was tried, so attacker success may be higher with other attacks.
4. The fresh keys were drawn from K\*'s family; they were not re-screened through Stage A.
5. Why 12 of the 80 PolyIoM key sets fail is not yet explained.
6. The linear-map version was tested at PolyIoM's settings, not tuned on its own.
7. Face enrolment uses one photo; voice uses the average of five clips.
8. The unprotected voice system made almost no errors, so only bounds are given, not ratios.
9. The face model itself limits how low the face error can go (about 3%).
10. One list used to exclude overlapping people came from an unverified copy and matched names exactly.

**Suggested wording.** *"We list these so the results are read with the right amount of confidence. None of them reverses the main findings."*

### Slide 23: Conclusion (§8)

**What the slide shows.** The two-sentence takeaway, three headline numbers, a recommendation for how such schemes should be evaluated, and a reproducibility line.

**What it means.** The takeaway is: *keyed compression gives revocability; the polynomial gives concealment; the choice between them is a trade.* The headline numbers are:

- 1.93% voice error on unseen speakers;
- 80 of 80 raw-IoM key sets that fail to revoke;
- 0.222 versus 0.490 for how much of the biometric an attacker recovers, polynomial against linear map.

Anyone can re-check every number with one command (`python3 run.py verify`). It runs 74 checks and 29 unit tests, and confirms that two independent implementations agree on all 32,768 template values.

**Suggested wording.** *"Compress under a key to make templates cancellable. Add the polynomial if hiding the biometric is worth a little accuracy. Every number in this talk can be re-checked with one command."*

### Slide 24: Declarations

**What the slide shows.** Three short statements: use of AI, data and code availability, and ethics.

**What it means.**

- **AI use.** An AI assistant helped with the secondary-analysis code, the figures, the reproducibility package and the writing. The core design, the data splits and the main locked results came first and were not changed.
- **Data and code.** Code, stored results and tests are released. The embeddings are not shared, because an embedding still counts as biometric data.
- **Ethics.** Only public datasets were used. The attack targeted only templates the authors made themselves, never a real deployed system.

**Suggested wording.** *"We state openly how AI was used, what we share, and why the attack experiments raise no ethical concerns."*

---

## Three points to remember

1. **Keyed compression makes revocation possible.** Without it, a stolen template works forever: 80 of 80 key sets.
2. **The polynomial hides the biometric.** An attacker recovers far less of the real face or voice: cosine 0.222 versus 0.490 for a linear map.
3. **It is a trade.** The polynomial costs about 1.2 pp of voice accuracy and gives less uniform revocation. The right choice depends on which harm matters most.

## Likely audience questions

**"Why not simply use the linear map, since it is more accurate?"**
Because it reveals more of the original biometric. A leaked face or voice can never be replaced, so in some applications concealment is worth the accuracy cost. The paper presents this as a choice, not a single answer.

**"How do we know the results were not tuned to look good?"**
The protocol was pre-registered. Settings were chosen on separate groups of people and locked before the test data were opened. A second, independent dataset was tested last, without changes.

**"Can someone else reproduce this?"**
Yes. All versions are pinned, all random choices use one seed, and one command re-derives every number from the stored results.

**"What remains open?"**
Mainly two things: why a minority of polynomial keys fail to revoke, and whether the findings hold for face on a larger, independent dataset.

---

*To rebuild the slides after adding figures A–D to `figures/results/`, run this in `paper/deck/`:*
`NODE_PATH=$PWD/node_modules node build_deck.js`

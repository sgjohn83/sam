# Figure captions and in-text explanation

Drop-in text for Figures 1 and 2. Numbers are the sealed operating points
from the pre-registered protocol (v1.1.1, master seed 2026).

---

## Figure 1 — caption (long form, for a figure that must stand alone)

**Figure 1: Building a protected template.** A frozen encoder maps the
biometric sample to an embedding $z$ (512 values for face, 192 for voice);
the encoder is never retrained. The keyed polynomial $P_{K^{*}}$ is then
applied to overlapping windows of five consecutive values of $z$.
Consecutive windows are shifted by $5-o^{*}$ positions, so neighbouring
windows share $o^{*}$ values; each window contributes one value to the
hardened vector $y$. Cells outside the window currently being transformed
are shown ghosted. This step is one-way: $y$ cannot be inverted to recover
$z$, so the embedding is not recoverable from anything that is stored.
IoM--GRP hashing then takes $M^{*}$ groups of $q^{*}$ random projections of
$y$ and keeps, for each group, only the *index* of the largest projection;
the projection magnitudes are discarded. The resulting index list
$h_{K,m}\in\{1,\dots,q^{*}\}^{M^{*}}$ is the stored template. Sealed
configurations: face $M^{*}=256$, $q^{*}=32$, $o^{*}=1$; voice
$M^{*}=128$, $q^{*}=32$, $o^{*}=1$.

## Figure 1 — caption (short form, if the body text carries the detail)

**Figure 1: Building a protected template.** The embedding $z$ is hardened
by applying the keyed polynomial $P_{K^{*}}$ to overlapping windows of five
values, shifted by $5-o^{*}$; the resulting vector $y$ cannot be inverted
back to $z$. IoM--GRP hashing keeps only the index of the largest of
$q^{*}$ projections in each of $M^{*}$ groups, giving the stored template
$h_{K,m}\in\{1,\dots,q^{*}\}^{M^{*}}$.

---

## Figure 2 — caption (long form)

**Figure 2: Comparing two protected templates.** Comparison is carried out
entirely on index lists; neither the original image or recording nor the
embedding is used again after enrolment. The enrolled template and the
probe template are aligned position by position, and the collision score
$s_m$ is the number of positions at which the two indices agree (shaded
columns). The decision compares $s_m$ with the threshold $\tau_m^{*}$,
shown as a position on the score scale: scores at or above $\tau_m^{*}$
accept, scores below reject. The padlock marks $\tau_m^{*}$ as frozen --
it was selected on development identities and was not adjusted after any
evaluation identity or the external corpus was read. The worked example
shows 5 agreements over 7 positions against $\tau^{*}=4$. Sealed
thresholds: face $\tau^{*}=68$ of $M^{*}=256$; voice $\tau^{*}=37$ of
$M^{*}=128$.

## Figure 2 — caption (short form)

**Figure 2: Comparing two protected templates.** The collision score
$s_m$ counts the positions at which the enrolled and probe index lists
agree. It is compared with the frozen threshold $\tau_m^{*}$, drawn as a
position on the score scale; at or above accepts, below rejects.

---

## In-text explanation

### Template construction (refer to Figure 1)

Figure 1 shows how a protected template is produced. A sample $x_m$ of
modality $m$ is passed through a frozen encoder $f_m$ to obtain an
embedding $z_m = f_m(x_m)$. We do not fine-tune the encoder, so the
recognition ability we start from is that of the published model and any
loss we report is attributable to the protection scheme rather than to
training choices.

The embedding is then hardened. Rather than transforming the whole vector
at once, $P_{K^{*}}$ is evaluated on overlapping windows of five
consecutive components. Consecutive windows advance by $5-o^{*}$
positions, so adjacent windows share $o^{*}$ components; the overlap
$o^{*}$ is a design parameter selected together with the rest of the
operating point. Each window produces a single output, giving the hardened
vector $y_m = P_{K^{*}}(z_m; o_m^{*})$. The polynomial coefficients are
the application key $K^{*}$, and the map is not invertible: recovering
$z_m$ from $y_m$ is not possible, which is what prevents an attacker
holding a stored template from reconstructing the face or the voice.

Protection is completed by IoM--GRP hashing. The hardened vector is
projected $q_m^{*}$ ways within each of $M_m^{*}$ groups, and only the
index of the largest projection in each group is retained. Because the
magnitudes are discarded and only an ordinal index survives, the stored
template is a short list of small integers,
$h_{K,m}\in\{1,\dots,q_m^{*}\}^{M_m^{*}}$, rather than anything resembling
the original measurement. Revocation follows directly: issuing a fresh key
$K^{*}$ and re-enrolling the same subject yields an unrelated template, so
a compromised template can be replaced without changing the biometric.

### Matching (refer to Figure 2)

Figure 2 shows the comparison stage. Two templates are compared position by
position, and the collision score $s_m$ is the number of positions holding
the same index. The decision rule is a single comparison,
$s_m \geq \tau_m^{*}$, and nothing outside the index lists takes part: the
raw sample and the embedding play no role once enrolment is complete.

The threshold is treated as part of the sealed operating point rather than
as a free parameter. $\tau_m^{*}$, along with $K^{*}$, $o_m^{*}$,
$M_m^{*}$ and $q_m^{*}$, is selected on the development identities and
frozen before any held-out identity or the external corpus is read. The
evaluation therefore reports the performance of a system that was fixed in
advance, not one tuned to the data it is measured on.

---

## Sealed operating points (for the table, if you want one)

| | $M^{*}$ | $q^{*}$ | $o^{*}$ | $\tau^{*}$ | dev EER | dev TAR | dev $D_{\mathrm{sys}}$ |
|---|---|---|---|---|---|---|---|
| Face  | 256 | 32 | 1 | 68 | 2.839 % | 86.260 % | 0.133100 |
| Voice | 128 | 32 | 1 | 37 | 0.952 % | 95.238 % | 0.052519 |

Selection rule: lowest $D_{\mathrm{sys}}$ subject to the modality
recognition floor (voice 1 % EER / 95 % TAR; face 3 % EER / 85 % TAR),
ties broken by EER, then $M$, then $q$, then $o$. 30 of 80 configurations
were eligible for voice, 13 of 80 for face.

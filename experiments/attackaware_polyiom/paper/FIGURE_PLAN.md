# Research figure plan

## The thing to decide first

The paper's thesis changed. The existing results figures were built when the
claim was *"this scheme works, here are its numbers."* The claim is now
*"the hardening stage does not earn its place, and here is what actually
does."* Figures that served the old argument do not automatically serve the
new one, and one of them now raises a question the study cannot answer.

So this plan has two halves: what to build, and what to demote.

---

## Part 1 — Figures to build

Three new figures, in priority order. Each is listed with the claim it
carries, the chart form and why that form, and what it needs.

### Figure 7 (build first) — Per-key post-revocation acceptance

**Claim it carries.** PolyIoM's revocation failure is *bimodal*: usually
perfect, occasionally total. The random linear map is never total. This is
the hardest point in §5.6 to convey and the weakest link in the argument,
so it is the figure that most needs to exist.

**Form: strip plot.** One row per arm, one dot per fresh key, 40 dots per
row, faceted by modality (voice, face).

**Why not a box plot.** A box plot would actively mislead here. PolyIoM's
median is 0.00% and its maximum is 100%, so a box plot draws a flat box at
zero with one long whisker, and a reader concludes *"fine, with an
outlier."* The truth is *"ten of forty keys fail completely."* Hiding
bimodality is exactly what box plots do, and it is the anti-pattern this
figure exists to avoid. Forty visible dots make the two clusters immediate.

**Annotation.** A reference line at 50% labelled *fails outright*, with the
count beside each row (2 of 40, 40 of 40, 0 of 40).

**Needs.** The forty per-key values per arm per modality. I have only the
summary statistics from the run output. These are stored as
`per_key_PRAR` in `runs/revocation/revocation_result.json` — I can pull it
from Drive, or you can paste it.

### Figure 6 — What the hardening stage costs

**Claim.** The polynomial costs recognition accuracy and buys no
unlinkability. The dimension change and the polynomial are separable.

**Form: dot-and-interval, small multiples.** Point estimate as a dot, 95%
interval as a line. Two columns (EER, $D_{\mathrm{sys}}$) by two rows
(voice, face). Arms on the vertical axis.

**Why not bars with error bars.** Bars assert that zero is a meaningful
baseline, which is true for EER and not for $D_{\mathrm{sys}}$, and they
spend a lot of ink to position one number. Dot-and-interval is the standard
form for effect estimates and lets the reader compare interval widths
directly, which is the point on the face row.

**Annotation.** On the voice EER panel, a bracket showing the
decomposition: $+0.427$ pp attributable to the size reduction, $+1.228$ pp
to the polynomial. That bracket is the single most quotable thing in the
section and it belongs in the figure, not only in the prose.

**Needs.** Nothing — all values and intervals are in hand.

### Figure 8 — Inversion: two findings at once

**Claim.** The attack succeeds completely against every arm, *and* the
polynomial nonetheless conceals the embedding. These look contradictory;
the figure has to make them coexist.

**Form: two panels, one axis each.** This is where a dual-axis chart would
be tempting and wrong.

- Panel (a), *matching positions achieved*: how far past the decision
  threshold the attack gets. Reference lines at the sealed threshold (37
  voice, 68 face) and at the chance level (4.0, 8.0). The attack reaching
  128 of 128 against a threshold of 37 is the visual statement that SAR
  saturated.
- Panel (b), *cosine to the true embedding*: dot-and-interval, with the
  chance level (0.120 voice, 0.029 face) marked. This is where the arms
  separate.

**Why SAR itself is not plotted.** Three identical bars at 100% is not a
chart. It is a sentence, and it is already in the text. Panel (a) carries
the same information and is informative.

**Needs.** Nothing — all values in hand.

---

## Part 2 — Existing figures to re-scope

| Figure | Current role | Recommendation |
|---|---|---|
| Fig 1, template construction (TikZ) | Method | **Keep as is.** |
| Fig 2, matching (TikZ) | Method | **Keep as is.** |
| Operating-point selection | §5.1 | **Keep.** Still carries the floor and the selection. |
| Generalisation | §5.2–5.3 | **Keep, minor rework** — see below. |
| Design space heatmaps | §5.1 | **Move to appendix.** It documents the sweep honestly, but the sweep is no longer the contribution. |
| Trade-off frontier | §5.1 | **Cut, or appendix with a caveat.** See below. |

**Generalisation figure.** Built with five rows for the old narrative.
Re-lay it out as two blocks — voice (development, held-out, external) and
face (development, held-out) — so the missing external face estimate is
visible as an absence rather than hidden by the row order. That absence is
a limitation we declare; the figure should not paper over it.

**The frontier figure is now a liability.** It argued *"we selected a good
point on the recognition–unlinkability frontier."* The paper now argues
that the frontier is beside the point, because a simpler arm dominates the
whole family. Any reader who sees that plot will ask why `randproj_iom` is
not on it — and the honest answer is that it was never swept, which is
Limitation 6. Better to state the limitation in prose than to raise the
question with a picture we cannot answer. If it stays, it goes in the
appendix with that caveat in the caption.

---

## Part 3 — Conventions across all figures

These are decided once and applied everywhere, so the reader learns the
encoding a single time.

**Arm identity is categorical, in fixed order.** PolyIoM, `iom_only`,
`randproj_iom` — same three hues, same order, in every figure. Colour
follows the arm, never its rank in a given panel.

**Marker shape as secondary encoding.** A distinct shape per arm as well as
a distinct hue. The paper will be printed, and some of it in greyscale;
hue alone would not survive that. This also satisfies the requirement that
identity is never carried by colour alone.

**One axis per panel. No dual-axis chart anywhere.** Where two measures of
different scale must be shown, they get two panels (Figures 6 and 8 both
do this).

**Sequential where magnitude, categorical where identity.** The design-space
heatmap is the only sequential figure: one hue, light to dark. The three
arms are categorical.

**Palette validated by script, not by eye.** I will run the validator on
the three-hue categorical set before drawing anything, and fix any failure
on the lightness band, chroma floor, or colour-vision separation. I will
not reason about whether the hues are distinguishable.

**No hover layer.** These are print figures, so the interaction layer that
an on-screen chart would carry does not apply. Every value a reader needs
is either directly labelled or in the corresponding table.

**Direct labels, selectively.** Three arms is few enough to label directly
rather than by legend lookup. No number on every mark.

---

## Part 4 — Order of work

1. **Figure 7**, per-key revocation. Highest value: it carries the weakest
   section. *Blocked on the per-key arrays.*
2. **Figure 6**, ablation. Unblocked.
3. **Figure 8**, inversion. Unblocked.
4. Re-lay the generalisation figure into two blocks.
5. Demote the design-space and frontier figures to the appendix, or cut the
   frontier.

I can start on 2 and 3 immediately. For 1, I need
`runs/revocation/revocation_result.json`.

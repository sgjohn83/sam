const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun,
        AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType,
        BorderStyle, PageOrientation } = require("docx");

const FIG = "/home/user/sam/experiments/attackaware_polyiom/figures";
const INK = "0B0B0B", INK2 = "52514E", MUTED = "898781";
const BLUE = "2A78D6", ORANGE = "EB6834", AQUA = "1BAF7A", RED = "D03B3B";

// Letter, landscape: the figures are 7in wide and need room beside a caption
const PAGE = { size: { width: 12240, height: 15840,
                       orientation: PageOrientation.PORTRAIT },
               margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } };
const CONTENT = 12240 - 2160;               // 10080 dxa = 7.0in

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, color: INK, size: 30, bold: true })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, color: INK, size: 24, bold: true })] });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: opts.after ?? 140, line: 300 },
    alignment: opts.align,
    children: [new TextRun({ text, color: opts.color ?? INK2,
      size: opts.size ?? 21, italics: opts.italics, bold: opts.bold })] });
}
function runs(parts, opts = {}) {
  return new Paragraph({ spacing: { after: opts.after ?? 140, line: 300 },
    children: parts.map(x => typeof x === "string"
      ? new TextRun({ text: x, color: INK2, size: 21 })
      : new TextRun({ text: x.t, color: x.c ?? INK2, size: x.s ?? 21,
                      bold: x.b, italics: x.i })) });
}
function bullet(text, opts = {}) {
  return new Paragraph({ bullet: { level: opts.level ?? 0 },
    spacing: { after: 90, line: 300 },
    children: [new TextRun({ text, color: INK2, size: 21 })] });
}
function rule() {
  return new Paragraph({ spacing: { before: 120, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "E1E0D9" } },
    children: [new TextRun({ text: "" })] });
}
function figure(file, widthIn, label) {
  const buf = fs.readFileSync(file);
  const png = require("child_process")
    .execSync(`python3 -c "from PIL import Image;im=Image.open('${file}');print(im.size[0],im.size[1])"`)
    .toString().trim().split(" ").map(Number);
  const w = widthIn * 96, h = w * png[1] / png[0];
  return new Paragraph({ alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 100 },
    children: [new ImageRun({ type: "png", data: buf,
      transformation: { width: Math.round(w), height: Math.round(h) } })] });
}
function caption(n, title, body) {
  return new Paragraph({ spacing: { after: 260, line: 280 },
    children: [
      new TextRun({ text: `Figure ${n}. `, bold: true, color: INK, size: 19 }),
      new TextRun({ text: title + " ", bold: true, color: INK, size: 19 }),
      new TextRun({ text: body, color: INK2, size: 19 })] });
}
function table(headers, rows, widths) {
  const cell = (text, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill,
                           color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: opts.align,
      spacing: { after: 0, line: 260 },
      children: [new TextRun({ text, bold: opts.b, size: 18,
        color: opts.c ?? INK2 })] })] });
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((t, i) =>
        cell(t, { w: widths[i], b: true, fill: "F2F1EC", c: INK,
                  align: i ? AlignmentType.RIGHT : undefined })) }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) =>
        cell(String(t), { w: widths[i], b: i === 0,
          align: i ? AlignmentType.RIGHT : undefined })) })),
    ],
  });
}

const doc = new Document({
  creator: "AttackAware PolyIoM v1.1.4",
  title: "Figure package",
  styles: { default: { document: { run: { font: "Calibri" } } } },
  sections: [{ properties: { page: PAGE }, children: [

// ============================================================ front matter
new Paragraph({ spacing: { after: 80 },
  children: [new TextRun({ text: "AttackAware PolyIoM v1.1.4", size: 22,
    color: MUTED })] }),
new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: "Figure package", size: 44, bold: true,
    color: INK })] }),
p("Every figure prepared for the paper, with what each one claims, how to "
  + "read it, and the decision behind its chart form. Numbers in this "
  + "document are transcribed from the sealed run outputs and were checked "
  + "against them.", { color: INK2, size: 22, after: 200 }),
rule(),

h1("How to use this document"),
p("Five figures are ready to place. Three are new and carry the paper's "
  + "central argument; two are existing method diagrams. Two further "
  + "figures from the original study are recommended for the appendix, and "
  + "one is recommended for removal — the reasoning is in the last section, "
  + "because it is a judgement about the argument rather than about the "
  + "picture."),
runs([{ t: "A convention runs through all of them: ", b: true, c: INK },
  "the three compared systems always take the same colour and the same "
  + "marker shape, in the same order. A reader learns the encoding once. "
  + "Marker shape doubles the colour so the figures still work when printed "
  + "in greyscale, and the colour set was checked with a colour-vision "
  + "simulator rather than by eye."]),

table(["System", "Colour", "Marker", "What it is"],
  [["PolyIoM (ours)", "blue", "circle", "keyed polynomial, then IoM hashing"],
   ["IoM only", "orange", "square", "IoM hashing on the raw embedding"],
   ["Random proj. + IoM", "aqua", "triangle", "random linear map, then IoM hashing"]],
  [2200, 1100, 1100, 5680]),
p("", { after: 240 }),

// ============================================================ Figure 6
h1("Figure 6 — What the hardening stage costs"),
runs([{ t: "The claim. ", b: true, c: INK },
  "Removing the keyed polynomial improves recognition, and does not make "
  + "unlinkability worse. The accuracy the polynomial costs is not buying "
  + "anything on the measure it was expected to buy."]),
figure(`${FIG}/paper/fig6_ablation.png`, 6.9),
caption("6", "What the hardening stage costs.",
  "Equal error rate and unlinkability for the three systems on the 58 "
  + "held-out identities, at the sealed operating point. Dots are point "
  + "estimates; lines are 95% confidence intervals from a paired "
  + "identity-cluster bootstrap. Lower is better on both measures. On voice, "
  + "both comparisons against PolyIoM are firm and both favour the baseline: "
  + "−1.655 pp for IoM only and −1.228 pp for random projection. No "
  + "unlinkability comparison is distinguishable. The two rungs below the "
  + "voice panel separate the two things the polynomial does at once: "
  + "shortening the vector accounts for +0.43 pp of error, and the "
  + "polynomial itself for a further +1.23 pp. No face comparison is "
  + "distinguishable, which is consistent with 259 genuine trials."),
h2("How to read it"),
bullet("The dot is the estimate; the line is the range the data supports. "
  + "Where two lines overlap heavily, the data cannot separate those systems."),
bullet("The face intervals are much wider than the voice intervals. That is "
  + "the power limitation, visible rather than stated."),
bullet("The two rungs are the sentence most likely to be quoted: the "
  + "polynomial costs about 2.9 times more accuracy than the size reduction "
  + "it performs."),
h2("Why this chart form"),
p("Dots with intervals, not bars with error bars. A bar asserts that zero is "
  + "a meaningful baseline, which is true for error rate and not for "
  + "unlinkability, and a bar spends a great deal of ink to place a single "
  + "number. The dot-and-interval form also lets a reader compare interval "
  + "widths directly, which is the whole point of the face row."),
new Paragraph({ children: [new TextRun({ break: 1 })] }),

// ============================================================ Figure 7
h1("Figure 7 — Revocation, key by key"),
runs([{ t: "The claim. ", b: true, c: INK },
  "Without keyed compression, revocation does not work at all. With it, it "
  + "usually works — but the polynomial fails completely for a minority of "
  + "new keys, and the random linear map never does."]),
figure(`${FIG}/paper/fig7_revocation_per_key.png`, 6.9),
caption("7", "Revocation, key by key.",
  "Each dot is one of 40 freshly issued key sets. The horizontal position is "
  + "the fraction of the 58 subjects whose old template's reconstruction is "
  + "still accepted after they re-enrol under that new key. Revocation works "
  + "only when the dots sit at the left edge. IoM hashing on the raw "
  + "embedding sits at 100% for all 40 keys on both modalities: a stolen "
  + "template stays a valid credential permanently. PolyIoM usually revokes "
  + "perfectly — its median is 0.00% — but fails outright for 2 of 40 voice "
  + "keys and 10 of 40 face keys. The random projection never fails "
  + "outright, with a worst case of 13.79%. Counts on the right give the "
  + "number of keys past the 50% line."),
h2("How to read it"),
bullet("Left edge is good. A dot at 100% means the attacker's reconstruction "
  + "was accepted for every subject, so re-keying achieved nothing."),
bullet("The orange row is the finding that is beyond doubt: 80 out of 80 "
  + "keys, both modalities, complete failure."),
bullet("The blue row is the finding that is not: two clusters, one at zero "
  + "and one at the far right, with nothing in between. That gap is the "
  + "shape of the problem."),
h2("Why this chart form"),
runs([{ t: "A strip plot with every key visible, and deliberately not a box "
  + "plot. ", b: true, c: INK },
  "PolyIoM's median is 0.00% and its maximum is 100%. A box plot would draw "
  + "a flat box at zero with one long whisker, and a reader would conclude "
  + "“fine, with an outlier.” The truth is that ten of forty keys "
  + "fail completely. Concealing that split is exactly what a box plot does "
  + "to this data, and it is the reason this figure exists."]),
p("Vertical scatter within each row carries no meaning; it only stops dots "
  + "at the same value hiding one another.", { italics: true }),
new Paragraph({ children: [new TextRun({ break: 1 })] }),

// ============================================================ Figure 8
h1("Figure 8 — Inversion under a full-knowledge attacker"),
runs([{ t: "The claim. ", b: true, c: INK },
  "The attack succeeds completely against every system. The polynomial "
  + "nevertheless hides the underlying biometric. Both statements are true, "
  + "and the figure has to let them sit together."]),
figure(`${FIG}/paper/fig8_inversion.png`, 6.9),
caption("8", "Inversion under a full-knowledge attacker.",
  "The attacker holds the key, the projections, the algorithm and the stored "
  + "template. Left: how many template positions the reconstruction matches, "
  + "against the sealed decision threshold and against the level a random "
  + "input reaches. Every system is driven far past its threshold, which is "
  + "why the success attack rate is 100% everywhere and cannot distinguish "
  + "them. Right: how much of the true embedding the reconstruction "
  + "recovers, as cosine similarity, against the level for two different "
  + "people. Here the systems separate firmly: IoM hashing on the raw "
  + "embedding leaks it almost completely at 0.913, while PolyIoM leaks far "
  + "less at 0.222. Confidence intervals are present but narrower than the "
  + "markers."),
h2("How to read it"),
bullet("Left panels: the dashed red line is the threshold for acceptance. "
  + "Everything to its right is an accepted forgery. All three systems are "
  + "hundreds of positions past it."),
bullet("Right panels: the grey line is what a stranger's embedding scores. "
  + "Distance above it is how much of the person was recovered."),
runs([{ t: "The two panels together are the paper's central observation: ",
  b: true, c: INK },
  "the system compares hardened vectors, not embeddings. The attack recovers "
  + "the hardened vector exactly while recovering little of the embedding, "
  + "so hiding the biometric does not prevent acceptance. An evaluation that "
  + "measured only the right-hand panel would report strong protection and "
  + "would be wrong."]),
h2("Why this chart form"),
p("Two panels, one measure each. Matching positions and cosine similarity "
  + "are on completely different scales, and putting them on one pair of "
  + "axes would be a two-scale chart — the most common way a chart misleads. "
  + "The success attack rate itself is not plotted: three identical bars at "
  + "100% is a sentence, not a chart, and the left-hand panel carries the "
  + "same information while remaining informative."),
new Paragraph({ children: [new TextRun({ break: 1 })] }),

// ============================================================ Figures 1-2
h1("Figures 1 and 2 — Method diagrams"),
p("These two were drawn earlier and need no change. They are included so "
  + "the package is complete."),
figure(`${FIG}/tikz/Figure1_TemplateGeneration.png`, 6.9),
caption("1", "Building a protected template.",
  "A frozen encoder turns the sample into an embedding. The keyed "
  + "polynomial is applied to overlapping windows of five values, shifted by "
  + "5 − o* so neighbouring windows share values; each window contributes "
  + "one value to the hardened vector. Cells outside the current window are "
  + "greyed. The step is one-way: the hardened vector cannot be turned back "
  + "into the embedding. IoM hashing then keeps only the index of the "
  + "largest of q* projections in each of M* groups, discarding the "
  + "magnitudes. That list of indices is the stored template."),
figure(`${FIG}/tikz/Figure2_ProtectedMatching.png`, 6.9),
caption("2", "Comparing two protected templates.",
  "Comparison uses the index lists alone; neither the original sample nor "
  + "the embedding is used again after enrolment. The two templates are "
  + "aligned position by position and the agreeing positions are counted. "
  + "That count is compared with the frozen threshold τ*, drawn as a "
  + "position on the score scale so that accept and reject are regions "
  + "rather than words. The padlock marks τ* as fixed on development "
  + "identities before any evaluation identity was read."),
new Paragraph({ children: [new TextRun({ break: 1 })] }),

// ============================================================ existing
h1("Existing figures: what to keep, move, and cut"),
p("The paper's argument changed. These figures were made when the claim was "
  + "that the scheme works. The claim is now that the hardening stage does "
  + "not earn its place, and that keyed compression is what matters. A "
  + "figure that served the first argument does not automatically serve the "
  + "second."),
table(["Figure", "Recommendation", "Reason"],
  [["Operating-point selection", "Keep",
    "Still carries the recognition floor and the selection rule."],
   ["Generalisation", "Keep, re-lay out",
    "Split into a voice block and a face block so the missing external face "
    + "estimate shows as an absence rather than being hidden by row order."],
   ["Design-space heat maps", "Appendix",
    "Documents the 80-configuration sweep honestly, but the sweep is no "
    + "longer the contribution."],
   ["Trade-off frontier", "Cut, or appendix with a caveat",
    "See below — it now raises a question the study cannot answer."]],
  [2600, 2300, 5180]),
p("", { after: 200 }),
h2("Why the frontier figure has become a liability"),
runs(["That figure argued that a good point was chosen on the "
  + "recognition–unlinkability frontier. The paper now argues that the "
  + "frontier is beside the point, because a simpler system dominates the "
  + "whole family. ",
  { t: "Any reader who sees the plot will ask why the random projection is "
    + "not on it", b: true, c: INK },
  ", and the honest answer is that it was never swept — which is a stated "
  + "limitation. It is better to declare that limitation in prose than to "
  + "invite the question with a picture that cannot answer it. If the figure "
  + "stays, it belongs in the appendix with that caveat in its caption."]),

// ============================================================ provenance
rule(),
h1("Provenance and checks"),
bullet("Every number in Figures 6 to 8 is transcribed from the sealed run "
  + "outputs, and the transcription was verified by recomputing the summary "
  + "statistics from the per-key values and matching them against the run "
  + "log."),
bullet("The colour set was checked with a colour-vision validator, not by "
  + "eye. It passes the lightness band, the chroma floor, colour-blind "
  + "separation and the normal-vision floor. One colour sits below the "
  + "contrast guideline against the page, which is why every system is "
  + "labelled directly and every figure has a table beside it."),
bullet("Marker shape duplicates colour throughout, so the figures survive "
  + "greyscale printing and do not rely on colour alone to convey identity."),
bullet("Figures are 6.9 inches wide and were drawn at final size, so type "
  + "prints at the size shown. PDF versions with embedded editable text are "
  + "in figures/paper/ alongside the PNGs used here."),
bullet("Confidence intervals resample identities, never individual "
  + "comparisons. Figure 7 resamples keys as well, because its variation is "
  + "across keys and an identity-only interval on that data was "
  + "confidently wrong in an earlier version of the analysis."),
  ]}],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync("Figure_Package.docx", b);
  console.log("wrote Figure_Package.docx", b.length, "bytes");
});

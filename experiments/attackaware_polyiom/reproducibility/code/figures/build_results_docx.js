// Results-figures package. Reads results_figures_text.json so this builder and
// the Colab one (notebooks/docx_only.py) cannot drift apart.
//
//   node build_results_docx.js <figure-dir> <out.docx> [--preview]
//
// --preview stamps the document as a layout proof. Pass it whenever the
// figures came from anything other than the real sealed run.
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun,
        AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType,
        BorderStyle, PageBreak } = require("docx");

const FIGDIR = process.argv[2];
const OUT = process.argv[3];
const PREVIEW = process.argv.includes("--preview");
const T = JSON.parse(fs.readFileSync(path.join(__dirname,
                     "results_figures_text.json"), "utf8"));

const INK = "121212", BODY = "3B3A38", MUTED = "7A7873";
const RULE = "D9DDE3", WARN = "9A3412", BAND = "F3F4F6";
const CONTENT = 12240 - 2160;               // 7.0 in of text
const IMG_W = 648;                          // 6.75 in, inside the margins

function h1(t) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 140 },
    children: [new TextRun({ text: t, color: INK, size: 30, bold: true })] });
}
function h2(t) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    spacing: { before: 260, after: 100 },
    children: [new TextRun({ text: t, color: INK, size: 23, bold: true })] });
}
function h3(t) {
  return new Paragraph({ spacing: { before: 200, after: 70 },
    children: [new TextRun({ text: t, color: INK, size: 20, bold: true })] });
}
function p(text, o = {}) {
  return new Paragraph({ spacing: { after: o.after ?? 130, line: 300 },
    alignment: o.align,
    children: [new TextRun({ text, color: o.color ?? BODY, size: o.size ?? 21,
                             italics: o.italics, bold: o.bold })] });
}
function rule() {
  return new Paragraph({ spacing: { before: 130, after: 130 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE } } });
}
function banner(text, colour) {
  return new Table({ width: { size: CONTENT, type: WidthType.DXA },
    borders: ["top", "bottom", "left", "right"].reduce((a, k) =>
      (a[k] = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, a), {}),
    rows: [new TableRow({ children: [new TableCell({
      shading: { type: ShadingType.CLEAR, fill: BAND },
      margins: { top: 130, bottom: 130, left: 170, right: 170 },
      children: [p(text, { color: colour, size: 19, after: 0 })] })] })] });
}
function figure(stem) {
  const file = path.join(FIGDIR, stem);
  if (!fs.existsSync(file)) throw new Error("missing figure: " + file);
  // The renderer writes every panel 7.16in wide; heights differ per figure,
  // so the aspect ratio is read from the PNG header rather than assumed.
  const b = fs.readFileSync(file);
  const w = b.readUInt32BE(16), hgt = b.readUInt32BE(20);
  return new Paragraph({ spacing: { before: 60, after: 110 },
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: b, transformation: {
      width: IMG_W, height: Math.round(IMG_W * hgt / w) } })] });
}
function table(rows) {
  const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const line = { style: BorderStyle.SINGLE, size: 4, color: RULE };
  return new Table({ width: { size: CONTENT, type: WidthType.DXA },
    borders: { top: line, bottom: line, left: noBorder, right: noBorder,
               insideHorizontal: line, insideVertical: noBorder },
    rows: rows.map((cells, r) => new TableRow({
      tableHeader: r === 0,
      children: cells.map(c => new TableCell({
        margins: { top: 90, bottom: 90, left: 110, right: 110 },
        shading: r === 0 ? { type: ShadingType.CLEAR, fill: BAND } : undefined,
        children: [p(c, { size: 18, bold: r === 0,
                          color: r === 0 ? INK : BODY, after: 0 })] })) })) });
}

const kids = [];
kids.push(new Paragraph({ spacing: { after: 40 },
  children: [new TextRun({ text: T.title, color: INK, size: 38, bold: true })] }));
kids.push(p(T.subtitle, { color: MUTED, size: 22, after: 200 }));
if (PREVIEW) {
  kids.push(banner("LAYOUT PROOF. The four images in this document were drawn "
    + "from synthetic histograms matched to the real statistics, so their "
    + "shapes are representative but they are not the real figures. Every "
    + "number in the text is from the sealed run. Run the FIGURES notebook in "
    + "Colab to regenerate this document with the real figures.", WARN));
  kids.push(p("", { after: 120 }));
}
kids.push(banner(T.note, BODY));
kids.push(h1(T.intro_h));
T.intro.forEach(t => kids.push(p(t)));
kids.push(h1(T.op_h));
kids.push(p(T.op_intro));
kids.push(table(T.op_table));
kids.push(p("", { after: 60 }));
kids.push(p(T.op_after, { size: 19, color: MUTED }));

T.figures.forEach((f, i) => {
  kids.push(new Paragraph({ children: [new PageBreak()] }));
  kids.push(h1(f.label + ". " + f.title));
  kids.push(figure(f.file));
  kids.push(p(f.caption, { size: 18, color: MUTED }));
  kids.push(rule());
  kids.push(h3(f.read_h));
  f.read.forEach(t => kids.push(p(t)));
  kids.push(h3(f.says_h));
  f.says.forEach(t => kids.push(p(t)));
  kids.push(h3(f.careful_h));
  f.careful.forEach(t => kids.push(p(t, { color: WARN })));
});

kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(h1(T.close_h));
T.close.forEach(t => kids.push(p(t)));

const doc = new Document({ styles: { default: {
    document: { run: { font: "Calibri", size: 21, color: BODY } } } },
  sections: [{ properties: { page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: kids }] });

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(OUT, b);
  console.log("wrote " + OUT + "  " + b.length + " bytes");
});

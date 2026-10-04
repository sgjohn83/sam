// AttackAware PolyIoM — the paper as a deck.
// Structure: the paper's own sections, in order, with its own headings.
// Style:     the SlideTeam "Research Methodology" look (white ground,
//            periwinkle/mint two-tone, numbered circle badges, rounded pill
//            spines, label-over-rule rows, soft corner circles). Nothing of
//            the template's slide structure is used.
// Numbers:   every number comes from data.js (result JSONs) or paper.js
//            (the paper's own tables); none is typed here.
const path = require("path");
const pptxgen = require("pptxgenjs");
const D = require("./data.js");
const P = require("./paper.js");
const FIG = require("./figures.js");
const SKILL = "/root/.claude/skills/synced/721d7864-ced3-40cc-829a-7b0f821df0d8_de93726b-f0f9-42f5-a0bc-23de2b7a1f61/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));

const OUT = path.join(__dirname, "AttackAware_PolyIoM_paper.pptx");
const THEME = {
  name: "AttackAware Periwinkle",
  headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: {
    dk1: "2B2B2B", lt1: "FFFFFF", dk2: "23295C", lt2: "F3F4F8",
    accent1: "5B6FD6",   // periwinkle, primary
    accent2: "3DBE8B",   // mint, secondary
    accent3: "F5C94C",   // soft yellow, single accent
    accent4: "6B7280",   // muted text
    accent5: "D5D9E2",   // rules and borders
    accent6: "238A60",   // deep mint, for mint-coloured text
    hlink: "5B6FD6", folHlink: "3D4FB8",
  },
};
const HEX = THEME.colors;

// ---------------------------------------------------------------- checks
// The paper's 5.2/5.3 tables carry intervals from the held-out confidence
// run; their point estimates must equal the stored result files.
const T51 = P.table("5.1 Sealed"), T52 = P.table("5.2 Generalisation"), T53 = P.table("5.3 External");
const T57 = P.table("5.7 Summary");
function must(cond, msg) { if (!cond) throw new Error("consistency: " + msg); }
must(T52[1][1].startsWith(D.heldout.voice.EER + "%"), "5.2 voice EER vs JSON");
must(T52[2][1].startsWith(D.heldout.face.EER + "%"), "5.2 face EER vs JSON");
must(T53[1][1].startsWith(D.external.EER + "%"), "5.3 EER vs JSON");
must(T51[1][4] === String(D.op.voice.tau) && T51[2][4] === String(D.op.face.tau), "5.1 tau vs JSON");
const ci2 = cell => { const m = cell.match(/\[([\d.]+), ([\d.]+)\]/); return `[${(+m[1]).toFixed(2)}, ${(+m[2]).toFixed(2)}]`; };
const n2 = s => (+s).toFixed(2);

// ---------------------------------------------------------------- deck
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Keyed compression is what makes an IoM-based cancelable biometric revocable";
pres.subject = "AttackAware PolyIoM v1.1.4";
const C = pres.SchemeColor;
const SH = pres.shapes;
const W = 13.333, L = 0.6, R = W - 0.6, CW = R - L, TOP = 1.5;

const shadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 90, color: "1A1F3D", opacity: 0.10 });

function corner(objs, dark) {
  // soft circles in the top-right corner: the template's only ornament
  const a = dark ? 55 : 20, b = dark ? 60 : 35, c = dark ? 50 : 25;
  objs.push({ text: { text: "", options: { shape: SH.OVAL, x: 12.35, y: -0.42, w: 1.15, h: 1.15, fill: { color: C.accent3, transparency: a }, line: { type: "none" } } } });
  objs.push({ text: { text: "", options: { shape: SH.OVAL, x: 12.72, y: 0.52, w: 0.5, h: 0.5, fill: { color: C.accent2, transparency: b }, line: { type: "none" } } } });
  objs.push({ text: { text: "", options: { shape: SH.OVAL, x: 12.02, y: 0.62, w: 0.3, h: 0.3, fill: { color: C.accent1, transparency: c }, line: { type: "none" } } } });
}

const content = [];
corner(content, false);
content.push({ placeholder: { options: { name: "kicker", type: "body", x: L, y: 0.3, w: 9, h: 0.3, fontSize: 12, bold: true, color: C.accent6, charSpacing: 2, margin: 0, valign: "middle" }, text: "" } });
content.push({ placeholder: { options: { name: "title", type: "title", x: L, y: 0.62, w: 11.1, h: 0.72, fontSize: 30, bold: true, color: C.accent1, margin: 0, valign: "middle", align: "left" }, text: "" } });
content.push({ text: { text: "AttackAware PolyIoM  ·  a pre-registered evaluation on face and voice", options: { x: L, y: 7.02, w: 8, h: 0.28, fontSize: 10, color: C.accent4, margin: 0 } } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: C.background1 }, objects: content,
  slideNumber: { x: R - 0.6, y: 7.02, w: 0.6, h: 0.28, fontSize: 10, color: C.accent4, align: "right" } });

const dark = [];
corner(dark, true);
dark.push({ text: { text: "", options: { shape: SH.OVAL, x: -0.55, y: 6.35, w: 1.5, h: 1.5, fill: { color: C.accent1, transparency: 55 }, line: { type: "none" } } } });
dark.push({ placeholder: { options: { name: "kicker", type: "body", x: 0.8, y: 0.62, w: 10, h: 0.32, fontSize: 13, bold: true, color: C.accent2, charSpacing: 2, margin: 0, valign: "middle" }, text: "" } });
dark.push({ placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.05, w: 11.0, h: 1.75, fontSize: 34, bold: true, color: C.background1, margin: 0, valign: "top", align: "left" }, text: "" } });
pres.defineSlideMaster({ title: "TITLE_DARK", background: { color: C.text2 }, objects: dark });

// ---------------------------------------------------------------- helpers
const TB = (o) => Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top" }, o);
function rich(text, o = {}) {
  const SUB = { "D_sys": ["D", "sys"], "P_K*": ["P", "K*"] };
  return String(text).split(/(D_sys|P_K\*)/).filter(Boolean).map(t => SUB[t]
    ? [{ text: SUB[t][0], options: Object.assign({}, o) }, { text: SUB[t][1], options: Object.assign({}, o, { subscript: true }) }]
    : [{ text: t, options: Object.assign({}, o) }]).flat();
}
function tx(s, text, o) { s.addText(rich(text), TB(o)); }
function paras(s, items, o) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const po = { paraSpaceAfter: o.gap ?? 6 };
    const seg = [];
    if (it.lead) seg.push({ text: it.lead + "  ", options: Object.assign({}, po, { bold: true, color: it.leadColor || o.leadColor || C.text1 }) });
    seg.push(...rich(it.text, Object.assign({}, po, it.color ? { color: it.color } : {})));
    if (!last) seg[seg.length - 1].options.breakLine = true;
    runs.push(...seg);
  });
  const box = Object.assign({}, o); delete box.gap; delete box.leadColor;
  s.addText(runs, TB(box));
}
function card(s, x, y, w, h, fill, o = {}) {
  s.addShape(SH.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, fill: { color: fill || C.background2 }, line: { type: "none" }, rectRadius: 0.07, shadow: shadow() }, o));
}
function badge(s, x, y, d, label, color, fs) {
  s.addText(label, TB({ shape: SH.OVAL, x, y, w: d, h: d, fill: { color }, line: { type: "none" }, color: C.background1, bold: true,
    fontSize: fs || Math.round(d * 26), align: "center", valign: "middle" }));
}
function rule(s, x1, x2, y, color) { s.addShape(SH.LINE, { x: x1, y, w: x2 - x1, h: 0, line: { color: color || C.accent5, width: 1 } }); }
function arrow(s, x1, x2, y) { s.addShape(SH.LINE, { x: x1, y, w: x2 - x1, h: 0, line: { color: C.accent4, width: 1.5, endArrowType: "triangle" } }); }
function pill(s, x, y, w, h, color, text, o = {}) {
  s.addText(rich(text), TB(Object.assign({ shape: SH.ROUNDED_RECTANGLE, rectRadius: 0.5, x, y, w, h, fill: { color }, line: { type: "none" },
    color: C.background1, bold: true, fontSize: 18, align: "center", valign: "middle" }, o)));
}
// The template's row: bold label above a thin rule, description below, badge at the outer end.
function row(s, { x, y, w, side = "left", n, color, label, desc, descH = 0.62, labelColor }) {
  const d = 0.5;
  if (side === "right") {
    tx(s, label, { x, y, w: w - 0.7, h: 0.34, bold: true, fontSize: 16, color: labelColor || C.text1, valign: "bottom" });
    rule(s, x, x + w - d / 2, y + 0.42);
    s.addShape(SH.OVAL, { x: x + w - d, y: y + 0.17, w: d, h: d, fill: { color: C.background1 }, line: { type: "none" } });
    badge(s, x + w - d, y + 0.17, d, n, color, 13);
    tx(s, desc, { x, y: y + 0.52, w: w - 0.7, h: descH });
  } else {
    const align = side === "left" ? "right" : "left";
    rule(s, x + d / 2, x + w, y + 0.42);
    badge(s, x, y + 0.17, d, n, color, 13);
    tx(s, label, { x: x + 0.7, y, w: w - 0.7, h: 0.34, bold: true, fontSize: 16, color: labelColor || C.text1, align, valign: "bottom" });
    tx(s, desc, { x: x + 0.7, y: y + 0.52, w: w - 0.7, h: descH, align });
  }
}
function stat(s, x, y, w, h, big, label, color, o = {}) {
  card(s, x, y, w, h, o.fill);
  tx(s, big, { x: x + 0.2, y: y + 0.16, w: w - 0.4, h: h * 0.48, fontSize: o.bigSize || 30, bold: true, color, valign: "middle" });
  tx(s, label, { x: x + 0.2, y: y + 0.18 + h * 0.48, w: w - 0.4, h: h * 0.52 - 0.3, fontSize: o.labelSize || 13, color: o.labelColor || C.accent4 });
}
function figure(s, key, box) {
  const r = FIG.resolve(key);
  if (!r.ok) return false;
  const f = FIG.fit(r, { x: box.x + 0.1, y: box.y + 0.1, w: box.w - 0.2, h: box.h - 0.2 });
  s.addShape(SH.ROUNDED_RECTANGLE, { x: f.x - 0.1, y: f.y - 0.1, w: f.w + 0.2, h: f.h + 0.2, fill: { color: C.background1 },
    line: { color: C.accent5, width: 0.75 }, rectRadius: 0.04 });
  s.addImage({ path: r.path, x: f.x, y: f.y, w: f.w, h: f.h, altText: key });
  return true;
}
function chart(s, data, box, o = {}) {
  s.addChart(o.type || pres.charts.BAR, data, Object.assign({
    x: box.x, y: box.y, w: box.w, h: box.h, barDir: "col", barGrouping: o.grouping || "clustered", barGapWidthPct: 55,
    chartColors: o.colors || [HEX.accent1, HEX.accent2],
    showValue: true, dataLabelPosition: o.labelPos || "outEnd", dataLabelFormatCode: o.fmt || "0.00",
    dataLabelFontSize: 12, dataLabelColor: "2B2B2B", dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelColor: "2B2B2B", catAxisLabelFontFace: "+mn-lt", catAxisLineShow: true,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: o.max, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: data.length > 1, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: "2B2B2B",
    showTitle: !!o.title, title: o.title, titleFontSize: 14, titleColor: "2B2B2B", titleFontFace: "+mn-lt",
  }, o.extra || {}));
}
function table(s, rows, o) {
  const head = rows[0].map(c => ({ text: rich(c, { bold: true, color: C.background1 }), options: { fill: { color: C.accent1 }, valign: "middle" } }));
  const body = rows.slice(1).map((r, i) => r.map((c, j) => ({
    text: rich(c, Object.assign({ color: C.text1 }, j === 0 ? { bold: true } : {}, (o.cellColor && o.cellColor(i, j, c)) || {})),
    options: { fill: { color: i % 2 ? C.background1 : C.background2 }, valign: "middle" } })));
  s.addTable([head, ...body], { x: o.x, y: o.y, w: o.w, colW: o.colW, fontSize: o.fontSize || 14, rowH: o.rowH,
    border: { type: "solid", pt: 0.75, color: HEX.accent5 }, margin: [0.05, 0.1, 0.05, 0.1] });
}
function slide(section, kicker, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
let curSection = null;
function section(title) { pres.addSection({ title }); curSection = title; }

const pc = x => `${x}%`;
const V = D.heldout.voice, F_ = D.heldout.face, X = D.external;
const ablV = Object.fromEntries(D.ablation.voice.map(a => [a.arm, a]));
const invV = Object.fromEntries(D.inversion.voice.map(a => [a.arm, a]));
const invF = Object.fromEntries(D.inversion.face.map(a => [a.arm, a]));
const revV = Object.fromEntries(D.revocation.voice.map(a => [a.arm, a]));
const revF = Object.fromEntries(D.revocation.face.map(a => [a.arm, a]));
const pres52 = Object.fromEntries(D.preservation.map(p => [p.modality + "/" + p.partition, p]));
const ARMLABEL = { polyiom: "PolyIoM", iom_only: "iom_only", randproj_iom: "randproj_iom" };

// ============================================================== 1 Title
section("Title");
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Title" });
  s.addText(`AttackAware PolyIoM v1.1.4  ·  protocol ${D.protocol.version}`, { placeholder: "kicker" });
  s.addText("Keyed compression is what makes an IoM-based cancelable biometric revocable", { placeholder: "title" });
  tx(s, "A pre-registered evaluation on face and voice", { x: 0.8, y: 2.95, w: 10, h: 0.5, fontSize: 20, color: C.accent2, bold: true });
  const r = FIG.resolve("method1");
  const f = FIG.fit(r, { x: 0.8, y: 3.95, w: 11.73, h: 2.6 });
  card(s, f.x - 0.25, f.y - 0.2, f.w + 0.5, f.h + 0.4, C.background1);
  s.addImage({ path: r.path, x: f.x, y: f.y, w: f.w, h: f.h, altText: "Template generation" });
  s.addNotes(P.notes("Abstract"));
}

// ============================================================== 2 Abstract
section("Abstract");
{
  const s = slide("Abstract", "ABSTRACT", "Abstract", P.notes("Abstract"));
  const cw = (CW - 0.3) / 2, ch = 2.45, ys = [TOP + 0.05, TOP + 0.05 + ch + 0.3];
  const items = [
    ["01", C.accent1, "The scheme", "A keyed polynomial transform of a face or speaker embedding, then Index-of-Maximum hashing. All four requirements at one sealed operating point, under one pre-registered protocol."],
    ["02", C.accent2, "Recognition and unlinkability", `Voice ${n2(V.EER)}% EER ${ci2(T52[1][1])} on ${V.nSub} unseen speakers; ${n2(X.EER)}% on ${X.nSub} external speakers, with no supported drop. D_sys ${(+V.D).toFixed(3)} held-out, ${(+X.D).toFixed(3)} external.`],
    ["03", C.accent1, "Cost and concealment", `Protection costs ${pres52["voice/evaluation"].cost} pp of EER on held-out voice and ${pres52["voice/external"].cost} pp externally, both firm. A full-knowledge attacker recovers the embedding at cosine ${invV.polyiom.cos}, against ${invV.iom_only.cos} without the polynomial.`],
    ["04", C.accent3, "Revocability", `IoM hashing on a raw embedding is not revocable: old templates are still accepted in ${D.revocation.everySubject.iom_only} of ${D.revocation.totalKeySets} fresh key sets. Keyed compression removes this; polynomial versus linear map is a trade.`],
  ];
  items.forEach(([n, col, head, body], i) => {
    const x = L + (i % 2) * (cw + 0.3), y = ys[Math.floor(i / 2)];
    card(s, x, y, cw, ch);
    badge(s, x + 0.3, y + 0.3, 0.6, n, col, 15);
    tx(s, head, { x: x + 1.1, y: y + 0.3, w: cw - 1.4, h: 0.6, fontSize: 18, bold: true, valign: "middle" });
    tx(s, body, { x: x + 0.3, y: y + 1.08, w: cw - 0.6, h: ch - 1.3 });
  });
}

// ============================================================== 3 Introduction
section("1 Introduction");
{
  const s = slide(curSection, "1.1", "The problem", P.notes("1.1 The problem"));
  tx(s, "Passwords can be changed. Biometrics cannot.", { x: L, y: TOP + 0.05, w: 4.7, h: 1.5, fontSize: 28, bold: true, color: C.accent1 });
  tx(s, "Cancelable biometrics store a keyed transform of the template. If it is stolen, issue a new key, re-enrol, and the old template should stop working.",
    { x: L, y: TOP + 1.75, w: 4.7, h: 1.45, fontSize: 15 });
  card(s, L, 5.05, 4.7, 1.7, C.background2);
  tx(s, "The first three can be measured on one template at one moment. The fourth needs a second enrolment under a fresh key, and is rarely measured.",
    { x: L + 0.25, y: 5.22, w: 4.2, h: 1.4, fontSize: 14, color: C.accent6, bold: true });
  const rx = 5.85, rw = R - rx;
  [["01", C.accent1, "Recognition performance", "Protected templates still tell people apart about as well as unprotected ones."],
   ["02", C.accent1, "Irreversibility", "A stolen template does not give back the underlying biometric."],
   ["03", C.accent1, "Unlinkability", "Templates of one person under two keys cannot be tied together."],
   ["04", C.accent3, "Revocability", "A compromised template is replaced, and the old one stops working."]]
    .forEach(([n, col, lab, desc], i) => row(s, { x: rx, y: TOP + 0.05 + i * 1.32, w: rw, side: "plain", n, color: col, label: lab, desc }));
}
{
  const s = slide(curSection, "1.2 – 1.3", "The scheme, and what this paper asks", P.notes("1.3 What this paper asks"));
  const chips = [["Embedding z", C.background2, C.text1], ["Keyed polynomial P_K*", C.accent1, C.background1],
    ["IoM-GRP under key R", C.accent2, C.background1], ["Template: argmax index per group", C.background2, C.text1]];
  const cwid = 2.62, gap = (CW - 4 * cwid) / 3;
  chips.forEach(([t, f, c], i) => {
    const x = L + i * (cwid + gap);
    s.addText(rich(t), TB({ shape: SH.ROUNDED_RECTANGLE, rectRadius: 0.5, x, y: TOP, w: cwid, h: 0.7, fill: { color: f }, line: { type: "none" }, color: c, bold: true, fontSize: 14, align: "center", valign: "middle" }));
    if (i < 3) arrow(s, x + cwid + 0.08, x + cwid + gap - 0.08, TOP + 0.35);
  });
  const qs = [
    ["01", C.accent1, "Is IoM hashing on a raw embedding revocable?", `No. The attack recovers the embedding itself (cosine ${invV.iom_only.cos}), which depends on no key: every old template survived re-keying, ${D.revocation.everySubject.iom_only} of ${D.revocation.totalKeySets} key sets.`],
    ["02", C.accent2, "What makes it revocable?", "Keyed compression before the hash. The attack then finds only a vector that collides under the old key. The polynomial and a keyed linear map both work."],
    ["03", C.accent3, "What does the polynomial itself buy?", `Concealment of the biometric: cosine ${invV.polyiom.cos} against ${invV.randproj_iom.cos} for a linear map and ${D.inversion.chanceVoice} at chance. It costs ${n2(D.ablation.costVsRandproj)} pp of voice EER.`],
  ];
  qs.forEach(([n, col, q, a], i) => row(s, { x: L, y: 2.55 + i * 1.42, w: CW, side: "plain", n, color: col, label: q, desc: a, descH: 0.7 }));
}
{
  const s = slide(curSection, "1.4 – 1.5", "Contributions and summary of findings", P.notes("1.4 Contributions"));
  tx(s, "Contributions", { x: L, y: TOP, w: 6.2, h: 0.4, fontSize: 18, bold: true });
  ["An ablation that isolates the polynomial, with a linear-map arm of equal output size",
   "An inversion attack under a full-knowledge adversary, applied identically to all three arms",
   "A revocation test: does an old template still get in after re-keying?",
   "All four criteria reported against the unprotected baseline",
   "A separation of what each keyed stage does, with the mechanism behind each",
   "A worked pre-registered protocol that keeps confirmatory and exploratory apart"]
    .forEach((t, i) => {
      const y = TOP + 0.6 + i * 0.78;
      badge(s, L, y + 0.04, 0.42, "0" + (i + 1), i % 2 ? C.accent2 : C.accent1, 11);
      tx(s, t, { x: L + 0.62, y, w: 5.6, h: 0.72, valign: "middle" });
    });
  const rx = 7.25, tw = (R - rx - 0.25) / 2, th = 2.3;
  tx(s, "What the sealed system achieves", { x: rx, y: TOP, w: R - rx, h: 0.4, fontSize: 18, bold: true });
  stat(s, rx, TOP + 0.6, tw, th, pc(n2(V.EER)), `voice EER on ${V.nSub} unseen speakers`, C.accent1);
  stat(s, rx + tw + 0.25, TOP + 0.6, tw, th, (+V.D).toFixed(3), "D_sys held-out; 0 is fully unlinkable", C.accent6);
  stat(s, rx, TOP + 0.85 + th, tw, th, invV.polyiom.cos, `cosine of the recovered embedding; chance ${D.inversion.chanceVoice}`, C.accent1);
  stat(s, rx + tw + 0.25, TOP + 0.85 + th, tw, th, `${D.revocation.everySubject.iom_only} / ${D.revocation.totalKeySets}`, "raw-IoM key sets in which old templates survive re-keying", "B8860B");
}

// ============================================================== 2 Background
section("2 Background and related work");
{
  const s = slide(curSection, "2", "Background and related work", P.notes("2.3 How these schemes"));
  const w = (CW - 0.6) / 3, h = 3.3;
  [["2.1", C.accent1, "Cancelable biometrics", "Store a revocable transform, not the biometric. Random-projection schemes such as BioHashing are the best known; with a stolen key the linear map can be undone."],
   ["2.2", C.accent2, "Index-of-Maximum hashing", "Project many times; keep only which projection was largest in each group. No magnitudes are stored, many inputs map to one code, and the score is a count of equal indices."],
   ["2.3", C.accent1, "How schemes are usually evaluated", "Three habits weaken the conclusions: a threshold chosen on the reported data; no ablation of multi-stage transforms; irreversibility argued rather than measured."]]
    .forEach(([n, col, head, body], i) => {
      const x = L + i * (w + 0.3);
      card(s, x, TOP, w, h);
      badge(s, x + 0.28, TOP + 0.28, 0.6, n, col, 13);
      tx(s, head, { x: x + 0.28, y: TOP + 1.05, w: w - 0.56, h: 0.7, fontSize: 17, bold: true });
      tx(s, body, { x: x + 0.28, y: TOP + 1.8, w: w - 0.56, h: h - 2.0 });
    });
  card(s, L, 5.1, CW, 1.65, C.background1, { line: { color: C.accent2, width: 1.5 } });
  badge(s, L + 0.3, 5.42, 0.6, "2.4", C.accent3, 13);
  tx(s, "The gap", { x: L + 1.15, y: 5.3, w: 3, h: 0.4, fontSize: 17, bold: true });
  tx(s, "This study already avoided the first habit: the operating point was sealed on development identities. It supplies the missing ablation and attack, and adds a revocation analysis we have not seen reported.",
    { x: L + 1.15, y: 5.72, w: CW - 1.45, h: 0.95 });
}

// ============================================================== 3 Method
section("3 Method");
{
  const s = slide(curSection, "3.1 – 3.2", "Overview and frozen encoders", P.notes("3.2 Frozen encoders"));
  const mid = W / 2, pw = 0.55, ph = 4.95, py = TOP + 0.05;
  pill(s, mid - 0.95 - pw / 2, py, pw, ph, C.accent1, "Face", { vert: "vert270" });
  pill(s, mid + 0.95 - pw / 2, py, pw, ph, C.accent2, "Voice", { vert: "vert270" });
  tx(s, "ENCODERS".split("").join("\n"), { x: mid - 0.3, y: py + 0.1, w: 0.6, h: ph - 0.2, fontSize: 19, bold: true, align: "center", valign: "middle", color: C.text1, lineSpacingMultiple: 0.95 });
  const lw = mid - 1.4 - L, rx = mid + 1.4;
  const face = [["Architecture", `Inception-ResNet-v1 (FaceNet), facenet-pytorch ${D.protocol.facenet}`],
    ["Weights", "Pretrained on VGGFace2; not fine-tuned"],
    ["Front end", "MTCNN detect and align, 160 × 160; no-face images excluded"],
    ["Output", "512-d embedding, L2-normalised"]];
  const voice = [["Architecture", `ECAPA-TDNN, SpeechBrain ${D.protocol.speechbrain}`],
    ["Weights", `VoxCeleb; revision ${D.protocol.ecapaRev} pinned, checkpoints hashed`],
    ["Front end", `16 kHz mono; VCTK resampled from 48 kHz`],
    ["Output", "192-d embedding; not fine-tuned"]];
  face.forEach(([a, b], i) => row(s, { x: L, y: py + 0.05 + i * 1.22, w: lw, side: "left", n: "0" + (i + 1), color: C.accent1, label: a, desc: b }));
  voice.forEach(([a, b], i) => row(s, { x: rx, y: py + 0.05 + i * 1.22, w: R - rx, side: "right", n: "0" + (i + 1), color: C.accent2, label: a, desc: b }));
}
{
  const s = slide(curSection, "3.3 – 3.5", "Hardening, IoM-GRP and matching", P.notes("3.3 Keyed polynomial"));
  figure(s, "method1", { x: L, y: TOP - 0.05, w: 8.4, h: 2.75 });
  figure(s, "method2", { x: L, y: 4.25, w: 8.4, h: 2.55 });
  const rx = 9.4, rw = R - rx;
  [["3.3", C.accent1, "Hardening", `Keyed polynomial over overlapping windows of G = ${D.protocol.G}, shift G − o. Voice d = ${D.ablation.d} → k = ${D.ablation.k}.`],
   ["3.4", C.accent2, "IoM-GRP", "M groups × q projections under key R; only the argmax index of each group is stored."],
   ["3.5", C.accent3, "Matching", "Score = number of groups with equal index; accept if the score reaches τ*."]]
    .forEach(([n, col, lab, desc], i) => {
      const y = TOP + i * 1.78;
      badge(s, rx, y, 0.55, n, col, 12);
      tx(s, lab, { x: rx + 0.7, y, w: rw - 0.7, h: 0.55, fontSize: 17, bold: true, valign: "middle" });
      tx(s, desc, { x: rx, y: y + 0.68, w: rw, h: 1.0 });
    });
}
{
  const s = slide(curSection, "3.6 – 3.7", "Selecting the key, then the operating point", P.notes("3.6 Stage A"));
  const cw = 5.55, ch = 3.6, xb = R - cw;
  const A = D.protocol.stageA;
  card(s, L, TOP, cw, ch);
  badge(s, L + 0.3, TOP + 0.3, 0.7, "A", C.accent1, 20);
  tx(s, "Stage A: the polynomial key", { x: L + 1.2, y: TOP + 0.3, w: cw - 1.4, h: 0.7, fontSize: 18, bold: true, valign: "middle" });
  paras(s, [
    { lead: "Data", text: `${D.protocol.split.background} background identities only` },
    { lead: "Candidates", text: `${D.protocol.budget.stage1.toLocaleString("en-US")} to ${D.protocol.budget.maximum.toLocaleString("en-US")} keys, generated deterministically` },
    { lead: "Score", text: `inversion stress test, ${A.restarts} restarts × ${A.iterations.toLocaleString("en-US")} Adam iterations, lr ${A.lr}` },
    { lead: "Gate", text: "recognition is pass-or-fail; the best survivor is sealed as K*" },
  ], { x: L + 0.3, y: TOP + 1.2, w: cw - 0.6, h: ch - 1.4, leadColor: C.accent1, gap: 8 });
  arrow(s, L + cw + 0.12, xb - 0.12, TOP + ch / 2);
  card(s, xb, TOP, cw, ch);
  badge(s, xb + 0.3, TOP + 0.3, 0.7, "B", C.accent2, 20);
  tx(s, "Stage B: the operating point", { x: xb + 1.2, y: TOP + 0.3, w: cw - 1.4, h: 0.7, fontSize: 18, bold: true, valign: "middle" });
  paras(s, [
    { lead: "Data", text: `${D.protocol.split.development} development identities` },
    { lead: "Grid", text: `M ∈ {${D.protocol.Mgrid.join(", ")}}, q ∈ {${D.protocol.qgrid.join(", ")}}, o ∈ {${D.protocol.ogrid[0]}…${D.protocol.ogrid.at(-1)}}: ${D.protocol.nConfigs} configurations` },
    { lead: "Rule", text: "lowest D_sys among configurations meeting the recognition floor" },
    { lead: "Threshold", text: "τ* at the development EER point; sealed" },
  ], { x: xb + 0.3, y: TOP + 1.2, w: cw - 0.6, h: ch - 1.4, leadColor: C.accent6, gap: 8 });
  card(s, L, 5.4, CW, 1.35, C.background2);
  badge(s, L + 0.3, 5.72, 0.6, "!", C.accent3, 18);
  tx(s, "The Stage A stress test selects keys; it is not the evaluation. No part of the pre-registered study measured the selected key's inversion resistance in the deployed configuration. Section 5.5 does.",
    { x: L + 1.15, y: 5.55, w: CW - 1.45, h: 1.05, valign: "middle" });
}

// ============================================================== 4 Protocol
section("4 Experimental protocol");
{
  const s = slide(curSection, "4.1 · 4.4", "Identities, partitions and sealing", P.notes("4.4 Sealing"));
  figure(s, "protocol", { x: L, y: TOP - 0.05, w: 7.7, h: 5.35 });
  const rx = 8.55, tw = (R - rx - 0.2) / 2, th = 1.4;
  stat(s, rx, TOP, tw, th, String(D.protocol.split.background), "background: key search only", C.accent4);
  stat(s, rx + tw + 0.2, TOP, tw, th, String(D.protocol.split.development), "development: operating point", C.accent1);
  stat(s, rx, TOP + th + 0.2, tw, th, String(D.protocol.split.evaluation), "evaluation: read after sealing", C.accent6);
  stat(s, rx + tw + 0.2, TOP + th + 0.2, tw, th, String(D.protocol.vctk.speakers), "external VCTK speakers, read last", "B8860B");
  card(s, rx, TOP + 2 * th + 0.45, R - rx, 6.75 - (TOP + 2 * th + 0.45), C.background1, { line: { color: C.accent1, width: 1.25 } });
  paras(s, [
    { lead: "Split once", text: `master seed ${D.protocol.seed}, protocol ${D.protocol.version}` },
    { lead: "Seal", text: "key, configuration and threshold are written to a sealed record; nothing downstream may change them" },
    { lead: "Check", text: "every later analysis records that it changed no seal" },
  ], { x: rx + 0.25, y: TOP + 2 * th + 0.62, w: R - rx - 0.5, h: 2.0, leadColor: C.accent1, gap: 6 });
}
{
  const s = slide(curSection, "4.2 – 4.3", "Metrics and confidence intervals", P.notes("4.3 Confidence"));
  const gw = 7.4, tw = (gw - 0.4) / 3, th = 2.45;
  [["EER", C.accent1, "Error rate where false match and false non-match are equal; threshold-free."],
   ["TAR and FMR", C.accent1, "Rates at the sealed threshold τ*, carried unchanged from development."],
   ["D_sys", C.accent6, "Global linkability of templates under two keys; 0 is fully unlinkable."],
   ["SAR", C.accent6, "Share of templates for which the inversion attack produces an accepted input."],
   ["PRAR", "B8860B", "Share of subjects whose old template's reconstruction is accepted after re-keying."],
   ["Firm", "B8860B", "A difference whose 95% interval excludes zero. Otherwise: not distinguishable."]]
    .forEach(([h, col, d], i) => {
      const x = L + (i % 3) * (tw + 0.2), y = TOP + Math.floor(i / 3) * (th + 0.25);
      card(s, x, y, tw, th);
      tx(s, h, { x: x + 0.22, y: y + 0.22, w: tw - 0.44, h: 0.5, fontSize: 18, bold: true, color: col });
      tx(s, d, { x: x + 0.22, y: y + 0.82, w: tw - 0.44, h: th - 1.0 });
    });
  const rx = L + gw + 0.35, rw = R - rx, rh = 2 * th + 0.25;
  card(s, rx, TOP, rw, rh, C.background1, { line: { color: C.accent1, width: 1.25 } });
  tx(s, "Bootstrap", { x: rx + 0.28, y: TOP + 0.22, w: rw - 0.56, h: 0.5, fontSize: 18, bold: true, color: C.accent1 });
  paras(s, [
    { lead: "95% percentile", text: `${D.protocol.nBootstrap.toLocaleString("en-US")} replicates` },
    { lead: "Identities", text: "are resampled, not comparisons, so a subject is never compared with itself" },
    { lead: "Paired", text: "one resampling serves every arm in a replicate" },
    { lead: "Two-level", text: "for revocation, keys are resampled as well as identities" },
  ], { x: rx + 0.28, y: TOP + 0.85, w: rw - 0.56, h: rh - 1.05, leadColor: C.accent1, gap: 10 });
}
{
  const s = slide(curSection, "4.6", "Implementation, frameworks and provenance", P.notes("4.6 Implementation"));
  table(s, [["Component", "What it does here", "Version / pin"],
    ["PyTorch", "encoder inference, hashing, the attack's gradients", D.protocol.torch.split("+")[0]],
    ["facenet-pytorch", "MTCNN detection and alignment; Inception-ResNet-v1 (VGGFace2)", D.protocol.facenet],
    ["SpeechBrain", "ECAPA-TDNN speaker encoder", `${D.protocol.speechbrain}; revision ${D.protocol.ecapaRev}`],
    ["NumPy · pandas · SciPy", "histograms, bootstrap, manifests, resampling", `${D.protocol.numpy} · ${D.protocol.pandas}`]],
    { x: L, y: TOP - 0.05, w: CW, colW: [2.6, 6.5, 3.033], rowH: 0.4, fontSize: 14 });
  table(s, [["Corpus", "Use", "What was taken"],
    ["LFW", "face, internal", `${D.protocol.lfw.raw.toLocaleString("en-US")} images → ${D.protocol.lfw.valid.toLocaleString("en-US")} pass MTCNN → ${D.protocol.lfw.eligible} identities with ≥ 3; ${D.protocol.lfw.excluded} removed by CFP-W name match`],
    ["LibriSpeech train-clean-100", "voice, internal", `${D.protocol.libri.speakers} speakers × 15 utterances`],
    [`VCTK 0.92, ${D.protocol.vctk.mic}`, "voice, external", `${D.protocol.vctk.speakers} speakers, ${D.protocol.vctk.utt.toLocaleString("en-US")} utterances, resampled to 16 kHz`]],
    { x: L, y: 3.75, w: CW, colW: [2.9, 1.9, 7.333], rowH: 0.42, fontSize: 14 });
  card(s, L, 5.95, CW, 0.8, C.background2);
  tx(s, `Embeddings on CPU; everything after on one ${D.protocol.gpu}, CUDA ${D.protocol.cuda}. Hashing pinned to CPU with deterministic algorithms; every draw seeded from master seed ${D.protocol.seed}.`,
    { x: L + 0.25, y: 6.05, w: CW - 0.5, h: 0.6, valign: "middle" });
}

// ============================================================== 5 Results
section("5 Results");
{
  const s = slide(curSection, "5.1 · CONFIRMATORY", "Sealed operating points", P.notes("5.1 Sealed"));
  table(s, T51, { x: L, y: TOP - 0.05, w: CW, colW: [1.3, 0.95, 0.95, 0.95, 0.95, 1.55, 1.7, 1.7, 2.083], rowH: 0.42, fontSize: 14 });
  figure(s, "fig1", { x: L, y: 2.95, w: 7.8, h: 3.85 });
  const rx = 8.7, rw = R - rx;
  card(s, rx, 3.05, rw, 3.7, C.background1, { line: { color: C.accent3, width: 1.5 } });
  tx(s, "The face floor was relaxed", { x: rx + 0.25, y: 3.25, w: rw - 0.5, h: 0.45, fontSize: 17, bold: true });
  tx(s, "No face configuration reaches the voice floor of EER ≤ 1% and TAR ≥ 95%: the best of 80 reaches 2.29% and 90.08%. The floor was relaxed to 3% and 85% and sealed before any evaluation identity was read.",
    { x: rx + 0.25, y: 3.78, w: rw - 0.5, h: 2.0 });
  tx(s, `The face encoder's own unprotected EER is ${(+pres52["face/evaluation"].unprotected).toFixed(3)}%.`, { x: rx + 0.25, y: 5.95, w: rw - 0.5, h: 0.6, color: C.accent6, bold: true });
}
{
  const s = slide(curSection, "5.2 · CONFIRMATORY", "Generalisation to held-out identities", P.notes("5.2 Generalisation"));
  table(s, T52, { x: L, y: TOP - 0.05, w: CW, colW: [1.3, 2.75, 2.85, 2.55, 2.683], rowH: 0.42, fontSize: 14 });
  const cats = ["Voice dev", "Voice held-out", "Voice external", "Face dev", "Face held-out"];
  const keys = ["voice/development", "voice/evaluation", "voice/external", "face/development", "face/evaluation"];
  chart(s, [{ name: "Protected", labels: cats, values: keys.map(k => pres52[k].protectedNum) },
            { name: "Unprotected cosine", labels: cats, values: keys.map(k => pres52[k].unprotectedNum) }],
    { x: L, y: 2.95, w: 7.6, h: 3.8 }, { title: "EER (%), protected against unprotected matching", max: 5.6 });
  const rx = 8.55, rw = R - rx;
  const ver = [["firm", C.accent2, `Voice held-out: +${pres52["voice/evaluation"].cost} pp. Baseline below ${pres52["voice/evaluation"].ub}% at 95%; the protected interval starts at ${T52[1][1].match(/\[([\d.]+)/)[1]}%.`],
               ["firm", C.accent2, `Voice external: +${pres52["voice/external"].cost} pp. Baseline below ${pres52["voice/external"].ub}%; the protected interval starts at ${T53[1][1].match(/\[([\d.]+)/)[1]}%.`],
               ["not resolvable", C.accent4, `Face held-out: +${pres52["face/evaluation"].cost} pp. The baseline's own bound, ${pres52["face/evaluation"].ub}%, lies inside the protected interval.`]];
  ver.forEach(([tag, col, t], i) => {
    const y = 3.0 + i * 1.12;
    pill(s, rx, y, tag === "firm" ? 0.85 : 1.7, 0.34, col, tag, { fontSize: 12 });
    tx(s, t, { x: rx, y: y + 0.42, w: rw, h: 0.68 });
  });
  tx(s, "No ratio is quoted: the unprotected voice system makes fewer than one genuine error on every split.", { x: rx, y: 6.33, w: rw, h: 0.45, fontSize: 12, color: C.accent4 });
}
{
  const figA = FIG.resolve("figA");
  const s = slide(curSection, "5.3 · CONFIRMATORY", "External validation on voice",
    P.notes("5.3 External") + "\n\n" + P.figNotes("Figure A") + (figA.ok ? "" : "\n\n[Author note] " + figA.note));
  const tw = 2.75, th = 1.9, g = 0.25;
  stat(s, L, TOP, tw, th, pc(n2(X.EER)), `EER ${ci2(T53[1][1])}`, C.accent1);
  stat(s, L + tw + g, TOP, tw, th, pc(n2(X.TAR)), "TAR at the sealed τ*", C.accent1);
  stat(s, L, TOP + th + g, tw, th, (+X.D).toFixed(3), "D_sys; tighter than held-out", C.accent6);
  stat(s, L + tw + g, TOP + th + g, tw, th, pc(X.FMR), "FMR, above the 0.1% target: firm", "B8860B", { fill: "FDF3D6" });
  tx(s, `${X.nSub} VCTK speakers, ${X.nGen.toLocaleString("en-US")} genuine and ${X.nImp.toLocaleString("en-US")} impostor comparisons. Configuration and threshold sealed on LibriSpeech, applied unchanged. No held-out-to-external difference is supported.`,
    { x: L, y: TOP + 2 * th + 2 * g, w: 2 * tw + g, h: 1.25 });
  const box = { x: 6.6, y: TOP - 0.05, w: R - 6.6, h: 5.3 };
  if (!figure(s, "figA", box)) {
    chart(s, [{ name: `Held-out (${V.nSub})`, labels: ["EER", "FMR at τ*"], values: [+V.EER, +V.FMR] },
              { name: `External (${X.nSub})`, labels: ["EER", "FMR at τ*"], values: [+X.EER, +X.FMR] }],
      box, { title: "Voice, held-out against external (%)", max: 3.4, fmt: "0.000" });
  }
}
{
  const s = slide(curSection, "5.4 · SECONDARY", "What the hardening stage costs", P.notes("5.4 What the hardening"));
  const arms = [["polyiom", C.accent1, "z → P_K*(z) → IoM-GRP"], ["randproj_iom", C.accent2, "z → Az → IoM-GRP"], ["iom_only", C.accent3, "z → IoM-GRP"]];
  arms.forEach(([a, col, pipe], i) => {
    const y = TOP + i * 1.3;
    badge(s, L, y + 0.05, 0.55, "0" + (i + 1), col, 13);
    tx(s, ARMLABEL[a], { x: L + 0.75, y, w: 4.6, h: 0.38, fontSize: 17, bold: true });
    tx(s, pipe, { x: L + 0.75, y: y + 0.4, w: 4.6, h: 0.32, color: C.accent4 });
    tx(s, `voice EER ${ablV[a].EER}%  ·  D_sys ${ablV[a].D}`, { x: L + 0.75, y: y + 0.74, w: 4.6, h: 0.34 });
  });
  const cats = [`No polynomial, d = ${D.ablation.d}`, `Linear map, k = ${D.ablation.k}`, `Polynomial, k = ${D.ablation.k}`];
  const b = +ablV.iom_only.EERnum.toFixed(3), sz = +D.ablation.dimensionCost, pl = +D.ablation.polynomialCost;
  chart(s, [{ name: "No-polynomial baseline", labels: cats, values: [b, b, b] },
            { name: "Size reduction", labels: cats, values: [0, sz, sz] },
            { name: "The polynomial itself", labels: cats, values: [0, 0, pl] }],
    { x: 6.0, y: TOP - 0.1, w: R - 6.0, h: 4.25 },
    { grouping: "stacked", labelPos: "ctr", fmt: "0.000;;;", colors: ["C9CEDA", HEX.accent2, HEX.accent1], title: "Voice EER (%), decomposed", max: 2.1,
      extra: { barGapWidthPct: 70 } });
  card(s, L, 5.6, CW, 1.15, C.background2);
  paras(s, [
    { lead: "Polynomial against linear map", text: `+${D.ablation.costVsRandproj} pp EER ${D.ablation.costVsRandprojCI}, firm. No D_sys difference is distinguishable. Face: no contrast resolved.` },
  ], { x: L + 0.25, y: 5.72, w: CW - 0.5, h: 0.9, leadColor: C.accent1, valign: "middle" });
}
{
  const s = slide(curSection, "5.5 · SECONDARY", "What the hardening stage does not buy", P.notes("5.5.3 Result"));
  const B = D.inversion.budget;
  card(s, L, TOP, 3.9, 5.25, C.background1, { line: { color: C.accent1, width: 1.25 } });
  tx(s, "Threat model", { x: L + 0.25, y: TOP + 0.2, w: 3.4, h: 0.45, fontSize: 18, bold: true, color: C.accent1 });
  paras(s, [
    { lead: "Adversary", text: "holds K*, the projection R, the algorithm and the stored template" },
    { lead: "Attack", text: "annealed-softmax gradient descent on the unit sphere" },
    { lead: "Budget", text: `${B.restarts} restarts × ${B.steps} steps, lr ${B.lr}, temperature ${B.temperature[0].toFixed(1)} → ${B.temperature[1]}; identical for every arm` },
  ], { x: L + 0.25, y: TOP + 0.8, w: 3.4, h: 4.3, leadColor: C.accent1, gap: 10 });
  const mx = 4.85;
  tx(s, `${invV.polyiom.SAR}%`, { x: mx, y: TOP + 0.3, w: 2.9, h: 1.3, fontSize: 60, bold: true, color: "B8860B", valign: "middle" });
  tx(s, "attack success rate: every arm, both modalities", { x: mx, y: TOP + 1.7, w: 2.75, h: 0.9, fontSize: 15 });
  tx(s, "Every template was inverted to an accepted input.", { x: mx, y: TOP + 2.75, w: 2.75, h: 0.9, color: C.accent4 });
  const order = ["polyiom", "randproj_iom", "iom_only"];
  const cats = ["PolyIoM", "Linear map", "Raw IoM", "Chance"];
  chart(s, [{ name: "Voice", labels: cats, values: [...order.map(a => invV[a].cosNum), D.inversion.chanceVoiceNum] },
            { name: "Face", labels: cats, values: [...order.map(a => invF[a].cosNum), D.inversion.chanceFaceNum] }],
    { x: 7.85, y: TOP - 0.1, w: R - 7.85, h: 4.0 }, { title: "Cosine to the true embedding", max: 1.05, fmt: "0.000" });
  card(s, mx, 5.55, R - mx, 1.2, C.background2);
  tx(s, "Both are true at once: the system matches on the hardened vector, not the embedding. The attack recovers a vector that collides, not the person.",
    { x: mx + 0.25, y: 5.62, w: R - mx - 0.5, h: 1.06, valign: "middle", bold: true, color: C.accent6 });
}
{
  const s = slide(curSection, "5.6 · SECONDARY", "What enables revocability", P.notes("5.6.2 Result"));
  const cats = ["PolyIoM", "Raw IoM", "Linear map"], order = ["polyiom", "iom_only", "randproj_iom"];
  chart(s, [{ name: "Voice", labels: cats, values: order.map(a => revV[a].PRARnum) },
            { name: "Face", labels: cats, values: order.map(a => revF[a].PRARnum) }],
    { x: L, y: TOP - 0.1, w: 6.0, h: 3.45 }, { title: `PRAR (%) across ${D.revocation.nKeys} fresh key sets`, max: 118, fmt: "0.0" });
  const tw = (6.0 - 0.4) / 3, ty = 4.95, th = 1.8;
  stat(s, L, ty, tw, th, `${D.revocation.everySubject.iom_only}/${D.revocation.totalKeySets}`, "raw-IoM key sets: every old template still accepted", "B8860B", { bigSize: 26, labelSize: 12 });
  stat(s, L + tw + 0.2, ty, tw, th, `${D.revocation.halfOrMore.polyiom}/${D.revocation.totalKeySets}`, `PolyIoM key sets: half or more exposed; ${D.revocation.everySubject.polyiom} expose all`, C.accent1, { bigSize: 26, labelSize: 12 });
  stat(s, L + 2 * (tw + 0.2), ty, tw, th, `${D.revocation.halfOrMore.randproj_iom}/${D.revocation.totalKeySets}`, "linear-map key sets: half or more exposed", C.accent6, { bigSize: 26, labelSize: 12 });
  figure(s, "fig7", { x: 6.95, y: TOP - 0.05, w: R - 6.95, h: 2.55 });
  const cx = 6.95, cy = 4.15, cwid = R - cx;
  card(s, cx, cy, cwid, 2.6, C.background1, { line: { color: C.accent3, width: 1.5 } });
  tx(s, "5.6.3  A correction we made", { x: cx + 0.25, y: cy + 0.18, w: cwid - 0.5, h: 0.42, fontSize: 16, bold: true });
  tx(s, `With 3 keys and an identity-only bootstrap, PolyIoM against the linear map looked firm on voice: +4.598 pp [+1.724, +8.046]. With ${D.revocation.nKeys} keys and a two-level bootstrap it is ${D.revocation.deltaVsRandprojVoice} pp ${D.revocation.deltaVsRandprojVoiceCI}: not distinguishable. The claim was retracted.`,
    { x: cx + 0.25, y: cy + 0.68, w: cwid - 0.5, h: 1.8 });
}
{
  const s = slide(curSection, "5.7", "Summary of evidence", P.notes("5.7 Summary"));
  table(s, T57, { x: L, y: TOP - 0.05, w: CW, colW: [2.55, 8.0, 1.583], fontSize: 14,
    cellColor: (i, j, c) => j === 2 ? { bold: true, color: c === "confirmatory" ? C.accent6 : C.accent1 } : null });
  card(s, L, 5.95, CW, 0.8, C.background2);
  tx(s, "Keyed compression gives revocability. The polynomial gives concealment of the biometric. The choice between them is a trade.",
    { x: L + 0.25, y: 6.02, w: CW - 0.5, h: 0.66, valign: "middle", bold: true, color: C.accent6 });
}

// ============================================================== 6 Discussion
section("6 Discussion");
{
  const s = slide(curSection, "6.1 – 6.3", "Discussion", P.notes("6.2 Why revocability"));
  const w = (CW - 0.6) / 3, h = 5.2;
  [["6.1", C.accent1, "What the polynomial does, and what it does not", `It conceals the embedding: cosine ${invV.polyiom.cos} against ${invV.iom_only.cos}. It does not stop acceptance, because the system compares hardened vectors and the attack recovers those. Measuring fidelity alone would overstate protection.`],
   ["6.2", C.accent2, "Why revocability is the binding property", "Recognition differs by a few points across arms; unlinkability not at all; irreversibility fails uniformly. Only revocability splits them, and it is the one property tested by a sequence of events rather than a single measurement."],
   ["6.3", C.accent3, "Implications for evaluation", "Attack the baselines with the same attack as the proposal. Ablate multi-stage transforms. Resample the axis that actually varies: keys as well as identities."]]
    .forEach(([n, col, head, body], i) => {
      const x = L + i * (w + 0.3);
      card(s, x, TOP, w, h);
      badge(s, x + 0.28, TOP + 0.28, 0.65, n, col, 14);
      tx(s, head, { x: x + 0.28, y: TOP + 1.1, w: w - 0.56, h: 0.95, fontSize: 18, bold: true });
      tx(s, body, { x: x + 0.28, y: TOP + 2.15, w: w - 0.56, h: h - 2.35 });
    });
}
{
  const s = slide(curSection, "6.4", "Design recommendation", P.notes("6.4 Design"));
  const mid = W / 2, pw = 0.55, ph = 4.5, py = TOP + 0.05;
  pill(s, mid - 0.95 - pw / 2, py, pw, ph, C.accent1, "Keyed polynomial", { vert: "vert270", fontSize: 16 });
  pill(s, mid + 0.95 - pw / 2, py, pw, ph, C.accent2, "Keyed linear map", { vert: "vert270", fontSize: 16 });
  tx(s, "TRADE".split("").join("\n"), { x: mid - 0.3, y: py + 0.4, w: 0.6, h: ph - 0.8, fontSize: 22, bold: true, align: "center", valign: "middle", lineSpacingMultiple: 1.0 });
  const lw = mid - 1.4 - L, rx = mid + 1.4;
  const left = [["Accuracy", `Voice EER ${ablV.polyiom.EER}%`],
    ["Concealment", `Recovered embedding: cosine ${invV.polyiom.cos} voice, ${invF.polyiom.cos} face`],
    ["Revocation", `${D.revocation.halfOrMore.polyiom} of ${D.revocation.totalKeySets} key sets leave half or more exposed`],
    ["Choose when", "the harm is a recovered face or voice, which nothing repairs"]];
  const right = [["Accuracy", `Voice EER ${ablV.randproj_iom.EER}%, better by ${n2(D.ablation.costVsRandproj)} pp (firm)`],
    ["Concealment", `Cosine ${invV.randproj_iom.cos} voice, ${invF.randproj_iom.cos} face`],
    ["Revocation", `${D.revocation.halfOrMore.randproj_iom} of ${D.revocation.totalKeySets} key sets leave half exposed`],
    ["Choose when", "the harm is a compromised credential, which re-keying repairs"]];
  left.forEach(([a, b], i) => row(s, { x: L, y: py + i * 1.1, w: lw, side: "left", n: "0" + (i + 1), color: C.accent1, label: a, desc: b, descH: 0.5 }));
  right.forEach(([a, b], i) => row(s, { x: rx, y: py + i * 1.1, w: R - rx, side: "right", n: "0" + (i + 1), color: C.accent2, label: a, desc: b, descH: 0.5 }));
  card(s, L, 6.2, CW, 0.58, C.background2);
  tx(s, "Either way: compress under a key before the hash. Without it, revocation does not work and a stolen template is permanent.",
    { x: L + 0.25, y: 6.24, w: CW - 0.5, h: 0.5, valign: "middle", bold: true, color: C.accent6 });
}

// ============================================================== 7 Limitations
section("7 Limitations");
{
  const s = slide(curSection, "7", "Limitations", P.notes("7. Limitations", 1800));
  const items = [
    ["Statistical power", `${V.nSub} held-out identities; face is descriptive only`],
    ["One external corpus", "VCTK validates voice; face has no external estimate"],
    ["One attack family", "Magnitudes are lower bounds on attacker success"],
    ["Fresh keys", "Resampled from K*, not re-selected through Stage A"],
    ["Unexplained failures", `${D.revocation.halfOrMore.polyiom} of ${D.revocation.totalKeySets} PolyIoM key sets; cause unknown`],
    ["Linear arm unsealed", "Evaluated only at PolyIoM's operating point"],
    ["Asymmetric enrolment", "Face uses one sample; voice the mean of five"],
    ["Voice baselines", "Below one genuine error: bounds, never ratios"],
    ["Face encoder", "Caps attainable EER near 3%"],
    ["Provenance", "Exclusion list from an unverified mirror; exact names only"],
  ];
  const cw = (CW - 0.5) / 2;
  items.forEach(([lab, d], i) => {
    const x = L + (i < 5 ? 0 : cw + 0.5), y = TOP + (i % 5) * 1.05;
    badge(s, x, y + 0.08, 0.48, String(i + 1).padStart(2, "0"), i % 2 ? C.accent2 : C.accent1, 12);
    tx(s, lab, { x: x + 0.68, y, w: cw - 0.68, h: 0.36, bold: true, fontSize: 16 });
    tx(s, d, { x: x + 0.68, y: y + 0.4, w: cw - 0.68, h: 0.55 });
  });
}

// ============================================================== 8 Conclusion
section("8 Conclusion");
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: curSection });
  s.addText("8 · CONCLUSION", { placeholder: "kicker" });
  s.addText("Keyed compression gives revocability. The polynomial gives concealment.", { placeholder: "title" });
  s.addNotes(P.notes("8. Conclusion", 1800));
  tx(s, "The choice between them is a trade, and we state it as one.", { x: 0.8, y: 2.55, w: 11, h: 0.45, fontSize: 18, color: C.accent2, bold: true });
  const tw = 3.6, th = 1.55, ty = 3.3;
  [[pc(n2(V.EER)), `voice EER on ${V.nSub} unseen speakers`],
   [`${D.revocation.everySubject.iom_only} / ${D.revocation.totalKeySets}`, "raw-IoM key sets that fail to revoke"],
   [`${invV.polyiom.cos} vs ${invV.randproj_iom.cos}`, "embedding recovered: polynomial against linear map"]]
    .forEach(([b, l], i) => {
      const x = 0.8 + i * (tw + 0.32);
      s.addShape(SH.ROUNDED_RECTANGLE, { x, y: ty, w: tw, h: th, fill: { color: C.accent1, transparency: 72 }, line: { type: "none" }, rectRadius: 0.07 });
      tx(s, b, { x: x + 0.22, y: ty + 0.15, w: tw - 0.44, h: 0.72, fontSize: 28, bold: true, color: C.background1, valign: "middle" });
      tx(s, l, { x: x + 0.22, y: ty + 0.88, w: tw - 0.44, h: 0.55, fontSize: 13, color: C.background1 });
    });
  tx(s, "Evaluate such schemes by attacking their baselines with the same attack, ablating their stages, reporting against the unprotected system, and testing what happens after a template is revoked.",
    { x: 0.8, y: 5.15, w: 11.4, h: 0.85, fontSize: 15, color: C.background1 });
  tx(s, "python3 run.py verify  →  74 checks  ·  29 unit tests  ·  NumPy and PyTorch agree on all 32,768 template indices",
    { x: 0.8, y: 6.2, w: 11.4, h: 0.4, fontSize: 13, color: C.accent2, bold: true });
}

// ============================================================== Declarations
section("Declarations");
{
  const s = slide(curSection, "DECLARATIONS", "Declarations", P.notes("Declarations"));
  const w = (CW - 0.6) / 3, h = 4.6;
  [["AI", C.accent1, "Generative AI use", "An AI assistant helped write the secondary-analysis code, the figures, the reproducibility package and the manuscript text. Protocol, partitions, key search, sealed operating points and confirmatory results predate it. Every number re-derives from stored results."],
   ["D", C.accent2, "Data and code availability", "Code, stored results, 29 unit tests and a verification script are released. Embeddings are not redistributed: an embedding is a derived representation of a biometric sample, not an anonymisation of it."],
   ["E", C.accent3, "Ethics", "No new human-subject data. Public corpora only. The inversion analysis attacks templates generated by the authors; no deployed system and no third party's template was attacked."]]
    .forEach(([n, col, head, body], i) => {
      const x = L + i * (w + 0.3);
      card(s, x, TOP, w, h);
      badge(s, x + 0.28, TOP + 0.28, 0.65, n, col, 16);
      tx(s, head, { x: x + 0.28, y: TOP + 1.1, w: w - 0.56, h: 0.5, fontSize: 18, bold: true });
      tx(s, body, { x: x + 0.28, y: TOP + 1.7, w: w - 0.56, h: h - 1.9 });
    });
  tx(s, "References follow the literature pass; citation slots are listed in Section 9 of the paper.", { x: L, y: 6.35, w: CW, h: 0.4, fontSize: 12, color: C.accent4 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  const miss = ["figA", "figB", "figC", "figD"].filter(k => !FIG.resolve(k).ok);
  console.log(`wrote ${OUT}`);
  if (miss.length) console.log(`  not yet built, native chart used instead: ${miss.join(", ")}`);
})().catch(e => { console.error(e); process.exit(1); });

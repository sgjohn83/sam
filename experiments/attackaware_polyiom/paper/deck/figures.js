// Resolves figure files. Figures A-D exist only after the FIGURES notebook
// has run; until then the slide gets an empty frame with a one-line note,
// and a rerun of build_deck.js completes it.
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..", "..");
const F = (...p) => path.join(ROOT, "figures", ...p);

const CATALOGUE = {
  method1: F("tikz", "Figure1_TemplateGeneration.png"),
  method2: F("tikz", "Figure2_ProtectedMatching.png"),
  protocol: F("fig_method_protocol.png"),
  fig1: F("fig1_operating_point_selection.png"),
  fig2: F("fig2_generalisation.png"),
  fig3: F("fig3_design_space.png"),
  fig4: F("fig4_frontier.png"),
  fig6: F("paper", "fig6_ablation.png"),
  fig7: F("paper", "fig7_revocation_per_key.png"),
  fig8: F("paper", "fig8_inversion.png"),
  figA: F("results", "figA_det_preservation.png"),
  figB: F("results", "figB_score_separability.png"),
  figC: F("results", "figC_unlinkability.png"),
  figD: F("results", "figD_revocability.png"),
};

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function resolve(key) {
  const file = CATALOGUE[key];
  if (fs.existsSync(file)) return { ok: true, path: file, ...pngSize(file) };
  return { ok: false, path: file,
    note: `${path.basename(file)} not built yet: run the FIGURES notebook, copy it to figures/results/, rerun build_deck.js` };
}

// Fit an image into a box, preserving aspect ratio, centred.
function fit(img, box) {
  const r = Math.min(box.w / img.w, box.h / img.h);
  const w = img.w * r, h = img.h * r;
  return { x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h };
}

module.exports = { resolve, fit, CATALOGUE };

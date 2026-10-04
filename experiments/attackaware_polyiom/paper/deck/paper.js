// Reads the paper itself: section prose for speaker notes, and the tables
// whose intervals come from runs not vendored as JSON (sections 5.1-5.3).
const fs = require("fs");
const path = require("path");
const DRAFT = fs.readFileSync(path.resolve(__dirname, "..", "DRAFT.md"), "utf8");
const FIGTEXT = JSON.parse(fs.readFileSync(path.resolve(__dirname, "..", "results_figures_text.json"), "utf8"));

function tex2txt(s) {
  return s
    .replace(/\$D_\{\\mathrm\{sys\}\}\$/g, "D_sys")
    .replace(/\$D\^\{\\mathrm\{sys\}\}_\{\\leftrightarrow\}\$/g, "D_sys")
    .replace(/\$\\tau\^\{\*\}\$/g, "τ*")
    .replace(/\$([MqoK])\^\{\*\}\$/g, "$1*")
    .replace(/\$k = (\d+)\$/g, "k = $1").replace(/\$d = (\d+)\$/g, "d = $1")
    .replace(/\$\+?([\d.]+)\$/g, "+$1")
    .replace(/\$[^$]*\$/g, m => m.slice(1, -1))
    .replace(/\*\*/g, "").replace(/`/g, "");
}

// Body of a heading (any level) up to the next heading of the same or higher level.
function section(prefix) {
  const lines = DRAFT.split("\n");
  const i = lines.findIndex(l => /^#{2,4} /.test(l) && l.replace(/^#+ /, "").startsWith(prefix));
  if (i < 0) throw new Error("no section: " + prefix);
  const level = lines[i].match(/^#+/)[0].length;
  const out = [];
  for (let j = i + 1; j < lines.length; j++) {
    const m = lines[j].match(/^(#+) /);
    if (m && m[1].length <= level) break;
    if (/^---\s*$/.test(lines[j])) break;
    out.push(lines[j]);
  }
  return out.join("\n");
}

function table(prefix, n = 0) {
  const body = section(prefix).split("\n");
  const blocks = []; let cur = [];
  for (const l of body) {
    if (l.startsWith("|")) cur.push(l); else if (cur.length) { blocks.push(cur); cur = []; }
  }
  if (cur.length) blocks.push(cur);
  const t = blocks[n];
  if (!t) throw new Error(`no table ${n} in ${prefix}`);
  return t.filter(l => !/^\|[\s|:-]+\|$/.test(l))
    .map(l => l.split("|").slice(1, -1).map(c => tex2txt(c.trim())));
}

// Plain prose for speaker notes: drop tables, headings, citation markers.
function notes(prefix, max = 1400) {
  let t = section(prefix).split("\n").filter(l => !l.startsWith("|") && !/^#/.test(l)).join("\n");
  t = tex2txt(t).replace(/\[CITE:[^\]]*\]/g, "").replace(/[ \t]*\n(?!\n)/g, " ")
    .replace(/\n{2,}/g, "\n\n").replace(/ {2,}/g, " ").trim();
  if (t.length <= max) return t;
  const cut = t.lastIndexOf(". ", max);
  return t.slice(0, cut > 200 ? cut + 1 : max).trim();
}

function figNotes(label) {
  const f = FIGTEXT.figures.find(x => x.label === label);
  return [f.caption, "What it says: " + f.says.join(" "), "What not to conclude: " + f.careful.join(" ")].join("\n\n");
}

module.exports = { section, table, notes, figNotes, tex2txt, DRAFT };

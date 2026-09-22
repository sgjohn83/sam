"""Builds the results-figures package as a .docx, from the real figures.

Reads the same results_figures_text.json that the local builder
(paper/build_results_docx.js) reads, so the two cannot drift apart. Runs
after figures_only.py has written the four PNGs.

Read-only with respect to the study: it touches no seal and computes no
score. It only lays out figures that already exist and text that is fixed.

Needs python-docx, which Colab does not ship:  pip -q install python-docx
"""

import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Inches, Pt, RGBColor

INK = RGBColor(0x12, 0x12, 0x12)
BODY = RGBColor(0x3B, 0x3A, 0x38)
MUTED = RGBColor(0x7A, 0x78, 0x73)
WARN = RGBColor(0x9A, 0x34, 0x12)

IMG_W = Inches(6.75)


def _run(par, text, size=10.5, colour=BODY, bold=False, italic=False):
    r = par.add_run(text)
    r.font.size = Pt(size)
    r.font.color.rgb = colour
    r.font.bold = bold
    r.font.italic = italic
    return r


def _para(doc, text, size=10.5, colour=BODY, bold=False, italic=False,
          after=7, align=None):
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(after)
    par.paragraph_format.line_spacing = 1.25
    if align is not None:
        par.alignment = align
    if text:
        _run(par, text, size, colour, bold, italic)
    return par


def _heading(doc, text, size, before, after):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(before)
    par.paragraph_format.space_after = Pt(after)
    _run(par, text, size, INK, bold=True)
    return par


def _banner(doc, text, colour):
    """A one-cell shaded table, which is how docx does a callout box."""
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    cell.width = IMG_W
    par = cell.paragraphs[0]
    par.paragraph_format.line_spacing = 1.2
    _run(par, text, 9.5, colour)
    return t


def _table(doc, rows):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Light Grid Accent 1"
    for r, cells in enumerate(rows):
        for c, text in enumerate(cells):
            par = t.cell(r, c).paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            _run(par, text, 9, INK if r == 0 else BODY, bold=(r == 0))
    return t


def build_results_docx(figdir=None, text_json=None, out=None):
    figdir = Path(figdir) if figdir else \
        PROJECT / "figures" / "results"
    text_json = Path(text_json) if text_json else \
        PROJECT / "results_figures_text.json"
    out = Path(out) if out else \
        PROJECT / "figures" / "Results_Figures_Package.docx"

    T = json.loads(text_json.read_text())
    missing = [f["file"] for f in T["figures"]
               if not (figdir / f["file"]).is_file()]
    if missing:
        raise FileNotFoundError(
            "Run make_figures() first; these are not on disk yet:\n- "
            + "\n- ".join(missing))

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    for side in ("top", "bottom", "left", "right"):
        setattr(section, f"{side}_margin", Inches(0.75))
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    _para(doc, T["title"], size=19, colour=INK, bold=True, after=2)
    _para(doc, T["subtitle"], size=11, colour=MUTED, after=10)
    _banner(doc, T["note"], BODY)

    _heading(doc, T["intro_h"], 15, 20, 7)
    for t in T["intro"]:
        _para(doc, t)

    _heading(doc, T["op_h"], 15, 20, 7)
    _para(doc, T["op_intro"])
    _table(doc, T["op_table"])
    _para(doc, "", after=3)
    _para(doc, T["op_after"], size=9.5, colour=MUTED)

    for fig in T["figures"]:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        _heading(doc, f"{fig['label']}. {fig['title']}", 15, 0, 7)
        doc.add_picture(str(figdir / fig["file"]), width=IMG_W)
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _para(doc, fig["caption"], size=9, colour=MUTED, after=10)
        for key_h, key_b, colour in (("read_h", "read", BODY),
                                     ("says_h", "says", BODY),
                                     ("careful_h", "careful", WARN)):
            _heading(doc, fig[key_h], 11, 11, 4)
            for t in fig[key_b]:
                _para(doc, t, colour=colour)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    _heading(doc, T["close_h"], 15, 0, 7)
    for t in T["close"]:
        _para(doc, t)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    size = out.stat().st_size
    print(f"Wrote {out}")
    print(f"  {size:,} bytes, 4 figures at 6.75 in, real sealed-run figures")
    return out


print("Docx runtime ready. Run build_results_docx().")

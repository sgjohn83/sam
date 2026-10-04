"""Check that every number printed on a slide comes from the paper or the results.

Reads the built deck, pulls each decimal number out of the slide text, tables
and chart labels, and looks for it in paper/DRAFT.md, the result JSONs and the
reproducibility docs. Small whole numbers (counts, list badges, section
numbers) are skipped. Exit code 1 if any number has no source.

    python check_numbers.py
"""
import json
import pathlib
import re
import sys

from pptx import Presentation

HERE = pathlib.Path(__file__).resolve().parent
EXP = HERE.parent.parent
DECK = HERE / "AttackAware_PolyIoM_paper.pptx"
NUM = re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,])[-+]?\d+(?:\.\d+)?(?![\w])")


def corpus():
    texts = [(EXP / "paper" / "DRAFT.md").read_text()]
    for p in (EXP / "reproducibility").rglob("*"):
        if p.suffix in {".md", ".json", ".txt", ".cff"} and p.is_file():
            texts.append(p.read_text(errors="ignore"))
    texts.append((EXP / "paper" / "results_figures_text.json").read_text())
    return "\n".join(texts)


def known_values(text):
    """Every number in the sources, plus its 1-3 decimal roundings."""
    vals = set()
    for m in NUM.finditer(text):
        s = m.group().lstrip("+").replace(",", "")
        vals.add(s)
        try:
            v = float(s)
        except ValueError:
            continue
        for d in (0, 1, 2, 3):
            vals.add(f"{v:.{d}f}")
            vals.add(f"{v * 100:.{d}f}")  # fractions shown as percentages
    return vals


def slide_numbers():
    prs = Presentation(DECK)
    for i, slide in enumerate(prs.slides, 1):
        chunks = []
        for sh in slide.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip() != str(i):  # skip page number
                chunks.append(sh.text_frame.text)
            if sh.has_table:
                chunks += [c.text for r in sh.table.rows for c in r.cells]
            if sh.has_chart:
                for plot in sh.chart.plots:
                    for ser in plot.series:
                        chunks += [str(v) for v in ser.values if v is not None]
        for m in NUM.finditer("\n".join(chunks)):
            yield i, m.group().lstrip("+").replace(",", "")


def main():
    known = known_values(corpus())
    missing = []
    checked = 0
    for i, s in slide_numbers():
        v = float(s)
        if "." not in s and abs(v) <= 12:
            continue  # badges, section numbers, small counts
        checked += 1
        forms = {s, s.lstrip("-")} | {f"{v:.{d}f}" for d in (0, 1, 2, 3)}
        if not forms & known:
            missing.append((i, s))
    for i, s in missing:
        print(f"slide {i}: {s} not found in paper or results")
    print(f"{checked} numbers checked, {len(missing)} without a source")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build RUN_CHECKS.ipynb: run.py (verify, test, demo, parity, figures) as a
notebook, for Colab, Kaggle or Jupyter. No terminal needed.

    python3 code/build_run_checks_notebook.py
"""

import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
OUT = PACKAGE / "RUN_CHECKS.ipynb"

INTRO = """# AttackAware PolyIoM v1.1.4: check the paper and redraw its figures

This notebook runs the reproducibility package without a terminal. It does
what `python run.py all` does, one step per cell, and shows the figures here.

| Step | What it does | Needs |
|---|---|---|
| 2 | **verify**: recomputes every number the paper reports from the stored results | nothing |
| 3 | **test**: 29 unit tests of the pipeline and the metrics | numpy |
| 4 | **demo**: runs the pipeline end to end on synthetic data | numpy |
| 5 | **parity**: checks the NumPy pipeline against the study's PyTorch code | torch (optional) |
| 6 | **figures**: draws the 8 results figures and shows them | matplotlib |
| 7 | **Figures A to D**, only if you have `score_histograms.json` | scipy |
| 8 | a zip of the figures to download | |

**How to use it**
- **Colab:** File → Upload notebook → this file. Run the first cell; it asks
  you to upload `AttackAware_PolyIoM_code.zip`.
- **Kaggle:** File → Import Notebook → this file. Add the zip as an input
  (Add Input → Upload), then Run All. Internet is not needed.
- **Jupyter on your computer:** open this file from inside the unzipped
  `reproducibility` folder and Run All.

Every step prints PASS or FAIL. None of them needs a GPU or the datasets.
"""

FIND = r'''#@title 1. Find the package (or upload the zip)
import os, subprocess, sys, zipfile
from pathlib import Path

ZIP_NAME = "AttackAware_PolyIoM_code.zip"


def find_package():
    """The folder holding run.py: here, above here, or inside an unzipped copy."""
    for base in [Path.cwd(), *Path.cwd().parents]:
        if (base / "run.py").is_file() and (base / "verify.py").is_file():
            return base
    for base in [Path.cwd(), Path("/content"), Path("/kaggle/working")]:
        for hit in sorted(base.glob("**/reproducibility/run.py"))[:1]:
            return hit.parent
    return None


def find_zip():
    for base in [Path.cwd(), Path("/content"), Path("/kaggle/input")]:
        if base.exists():
            for hit in sorted(base.glob(f"**/{ZIP_NAME}"))[:1]:
                return hit
            for hit in sorted(base.glob("**/*.zip")):
                try:
                    if any(n.endswith("reproducibility/run.py")
                           for n in zipfile.ZipFile(hit).namelist()):
                        return hit
                except zipfile.BadZipFile:
                    continue
    return None


REPRO = find_package()
if REPRO is None:
    archive = find_zip()
    if archive is None:
        try:
            from google.colab import files            # Colab only
            print(f"Choose {ZIP_NAME} to upload.")
            archive = Path(next(iter(files.upload())))
        except ImportError:
            raise SystemExit(f"{ZIP_NAME} not found. Put it next to this notebook "
                             "(or add it as a Kaggle input) and run this cell again.")
    target = Path("/kaggle/working" if Path("/kaggle/working").exists() else ".") \
        / "AttackAware_PolyIoM_code"
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target)
    print(f"unzipped {archive.name} into {target}")
    REPRO = find_package() or next(target.glob("**/reproducibility"))
REPRO = Path(REPRO).resolve()
print("package:", REPRO)

RESULTS = {}


def step(name, *args):
    """Run one step as run.py would, show its output, record PASS/FAIL."""
    proc = subprocess.run([sys.executable, *args], cwd=REPRO, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout)
    RESULTS[name] = "PASS" if proc.returncode == 0 else "FAIL"
    print(f"==> {name}: {RESULTS[name]}")
'''

INSTALL = '''#@title Libraries (numpy, matplotlib, scipy; most notebooks have them already)
import importlib.util
missing = [p for p in ("numpy", "matplotlib", "scipy") if importlib.util.find_spec(p) is None]
if missing:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])
print("torch:", "present, so parity runs" if importlib.util.find_spec("torch")
      else "absent, so parity reports SKIPPED (that is fine)")
'''

STEPS = [
    '''#@title 2. verify: does the paper match the stored results?
step("verify", "run.py", "verify")
''',
    '''#@title 3. test: unit tests of the pipeline and the metrics
step("test", "run.py", "test")
''',
    '''#@title 4. demo: the pipeline end to end on synthetic data
step("demo", "run.py", "demo")
''',
    '''#@title 5. parity: the NumPy pipeline against the study's PyTorch code
step("parity", "run.py", "parity")
''',
    '''#@title 6. figures: the 8 results figures, drawn from results/
step("figures", "run.py", "figures")
from IPython.display import Image, display
for png in sorted((REPRO / "figures").glob("*.png")):
    print(png.name)
    display(Image(filename=str(png), width=760))
''',
    '''#@title 7. Figures A to D (only if you have score_histograms.json)
# score_histograms.json is in the study's Drive folder (runs/scores/), or in
# the results zip of the Kaggle run (runs/scores/). Put it next to this
# notebook, or add it as an input, and run this cell.
hits = [p for base in (Path.cwd(), REPRO, Path("/content"), Path("/kaggle/input"))
        if base.exists() for p in sorted(base.glob("**/score_histograms.json"))[:1]]
if hits:
    step("figures A-D", "figures_from_scores.py", str(hits[0]))
    for png in sorted((REPRO / "figures").glob("fig[A-D]_*.png")):
        print(png.name)
        display(Image(filename=str(png), width=760))
else:
    print("score_histograms.json not found; Figures A to D skipped (not a failure).")
''',
    '''#@title 8. Summary, and a zip of the figures to download
import shutil
for name, verdict in RESULTS.items():
    print(f"{verdict:5}  {name}")
print("\\nall steps passed" if all(v == "PASS" for v in RESULTS.values())
      else "\\nSOME STEPS FAILED: read the output of those cells")
out = Path("/kaggle/working" if Path("/kaggle/working").exists() else ".").resolve()
archive = shutil.make_archive(str(out / "AttackAware_PolyIoM_figures"), "zip", REPRO / "figures")
print("figures zip:", archive)
try:
    from google.colab import files
    files.download(archive)
except ImportError:
    pass
''',
]


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source.splitlines(keepends=True)}


def build():
    cells = [{"cell_type": "markdown", "metadata": {},
              "source": INTRO.splitlines(keepends=True)},
             code(FIND), code(INSTALL)] + [code(s) for s in STEPS]
    nb = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 4}
    OUT.write_text(json.dumps(nb, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(PACKAGE)}  ({len(cells)} cells)")


if __name__ == "__main__":
    build()

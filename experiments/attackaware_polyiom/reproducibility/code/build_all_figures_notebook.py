#!/usr/bin/env python3
"""Build notebooks/AttackAware_PolyIoM_v1_1_4_ALL_FIGURES.ipynb.

The notebook carries its own copy of every runtime file it needs, written
out with %%writefile, so it runs in Colab with nothing but the study's data
on Drive. This script assembles it from code/runtime/, so the notebook is
never edited by hand and cannot drift from the code in this package.

    python3 code/build_all_figures_notebook.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = HERE / "runtime"
OUT = HERE / "notebooks" / "AttackAware_PolyIoM_v1_1_4_ALL_FIGURES.ipynb"

# Written to the Colab runtime, in this order.
FILES = [
    ("ablation_only.py", "The study's pipeline primitives and the ablation"),
    ("scoredump_only.py", "The study's score histograms"),
    ("inversion_only.py", "The study's full-knowledge inversion attack"),
    ("revocation_only.py", "The study's revocation test"),
    ("figures_only.py", "The study's code for Figures A to D"),
    ("results_plots.py", "Drawing code for Figures 3 to 8, S2 and P"),
    ("allfigures_only.py", "Sweep, intervals, baseline and checks"),
]

INTRO = """# AttackAware PolyIoM v1.1.4: every results figure, generated from code

This notebook recomputes the study's results from the stored embeddings and
the sealed keys, and then draws every results figure from what it has just
computed. No number is typed in, and nothing is read from an earlier result
file except to compare against it.

| Stage | Computes | Figures |
|---|---|---|
| 1 | the 80-setting development sweep, and the selection rule re-run on it | 3, 4, S2 |
| 2 | the protected and unprotected score histograms | A, B, C, D |
| 3 | identity-cluster bootstrap intervals; protection cost against the unprotected system | 5, P |
| 4 | the ablation of the polynomial | 6 |
| 5 | the full-knowledge inversion attack | 8 |
| 6 | the revocation test over 40 fresh keys | 7 |
| 7 | a comparison of every regenerated number with the study's original output | |
| 8 | all twelve figures, as PNG and PDF, and a zip to download | |

**What it needs on Drive** (under `MyDrive/AttackAware_PolyIoM_v1_1_4/`, as the
study left it): `embeddings/`, `protocol/`, `seal/`, and from `runs/` the
selected keys, the frozen IoM tensors, the sealed held-out and external
results and the two sealed sweeps.

**What it writes.** Everything it computes goes to `runs_regenerated/`, and the
figures to `figures_regenerated/`. It never writes to `runs/` or `seal/`.

**Checks.** Each stage stops if it cannot reproduce the sealed result it
depends on: the selection rule must choose the sealed setting, the rebuilt
scores must give the sealed held-out and external point estimates, and the
ablation must reproduce the sealed held-out EER. Stage 7 then compares every
regenerated number with the study's original output where that is on Drive.

**Run time.** Stages 5 and 6 run the inversion attack on the CPU, as the study
did, and take most of the time. Every stage saves its result, so after a
disconnect, run all cells again and finished stages are skipped.

**Use:** Runtime, then Run all.
"""

SETUP = '''#@title 1. Settings, Drive and input check
import hashlib, importlib.util, json, math, os, shutil
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from IPython.display import display

try:
    from google.colab import drive, files
    drive.mount("/content/drive")
    IN_COLAB = True
except ImportError:                      # outside Colab, e.g. a local check
    IN_COLAB = False

PROJECT = Path(os.environ.get(
    "POLYIOM_PROJECT", "/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4"))
RUNS_IN = PROJECT / "runs"               # the study's outputs: read only
WORK = PROJECT / "runs_regenerated"      # everything this notebook computes
FIGURES_OUT = PROJECT / "figures_regenerated"
RUNTIME = Path(os.environ.get("POLYIOM_RUNTIME", "/content/polyiom_runtime"))

DIR = {"protocol": PROJECT / "protocol", "embeddings": PROJECT / "embeddings",
       "runs": WORK, "seal": PROJECT / "seal"}
S0, G = 2026, 5
DEVICE = torch.device("cpu")
N_BOOTSTRAP, CONFIDENCE = 2000, 0.95

LFW_FACE_TRIALS = DIR["protocol"] / "lfw_face_trials.tsv"
LFW_EMB = DIR["embeddings"] / "lfw_all_valid_embeddings.npz"
LIBRI_MANIFEST = DIR["protocol"] / "librispeech_internal.tsv"
LIBRI_EMB = DIR["embeddings"] / "librispeech_internal_embeddings.npz"
HELDOUT_RESULTS = {m: RUNS_IN / "heldout" / m / "heldout_result.json"
                   for m in ("face", "voice")}
ABLATION_OUTPUT = WORK / "ablation" / "ablation_result.json"

DIMENSION = {"face": 512, "voice": 192}
REQUIRED = [LFW_FACE_TRIALS, LFW_EMB, LIBRI_MANIFEST, LIBRI_EMB,
            DIR["seal"] / "operating_point_face.json",
            DIR["seal"] / "operating_point_voice.json"]
for m, d in DIMENSION.items():
    REQUIRED += [RUNS_IN / "key_search" / m / "selected_key.json",
                 HELDOUT_RESULTS[m]]
    REQUIRED += [RUNS_IN / "iom_tensors" /
                 f"{m}_o{o}_k{1 + math.ceil((d - G) / (G - o))}.pt"
                 for o in range(5)]
missing = [str(p) for p in REQUIRED if not p.is_file()]
if missing:
    raise FileNotFoundError("These inputs are missing:\\n- " + "\\n- ".join(missing))

OPTIONAL = {
    "external VCTK embeddings": DIR["embeddings"] / "vctk_external_embeddings.npz",
    "sealed external result": RUNS_IN / "external/voice/external_result.json",
    "sealed sweeps (to compare)": RUNS_IN / "sweep/voice/sweep_80.csv",
}
for label, path in OPTIONAL.items():
    print(f"  {label:<28} {'found' if path.is_file() else 'not found - skipped'}")

torch.use_deterministic_algorithms(True, warn_only=True)
WORK.mkdir(parents=True, exist_ok=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
print(f"\\nInputs from {RUNS_IN}\\nOutputs to  {WORK}\\nFigures to  {FIGURES_OUT}")
'''

LOADER = '''#@title 9. Load the runtime
for name in ("ablation_only.py", "scoredump_only.py", "inversion_only.py",
             "revocation_only.py", "allfigures_only.py"):
    exec(compile((RUNTIME / name).read_text(), str(RUNTIME / name), "exec"),
         globals())


def _module(name):
    spec = importlib.util.spec_from_file_location(name, RUNTIME / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Imported as modules so their names cannot collide with the study's.
results_plots = _module("results_plots")
figures_only = _module("figures_only")
print("Runtime loaded.")
'''

STAGES = [
    ('''#@title 10. Stage 1 - the development sweep (Figures 3, 4, S2)
SWEEPS, SELECTED, FLOORS = {}, {}, {}
for modality in ("voice", "face"):
    SWEEPS[modality] = run_sweep(modality)
    FLOORS[modality] = floor_of(modality)
    SELECTED[modality] = select(modality, SWEEPS[modality], FLOORS[modality])
'''),
    ('''#@title 11. Stage 2 - score histograms, protected and unprotected (Figures A-D)
SCORES = add_external_scores(run_score_dump())
'''),
    ('''#@title 12. Stage 3 - intervals and protection cost (Figures 5, P)
INTERVALS = run_intervals(N_BOOTSTRAP, CONFIDENCE)
BASELINE = baseline_from_scores(SCORES)
display(pd.DataFrame(BASELINE).round(4))
'''),
    ('''#@title 13. Stage 4 - ablation (Figure 6)
ABLATION = run_ablation(N_BOOTSTRAP, CONFIDENCE)
contrast_report(ABLATION)
'''),
    ('''#@title 14. Stage 5 - full-knowledge inversion attack (Figure 8)
INVERSION = run_inversion(N_BOOTSTRAP, CONFIDENCE)
inversion_report(INVERSION)
'''),
    ('''#@title 15. Stage 6 - revocation over fresh keys (Figure 7)
REVOCATION = run_revocation(N_BOOTSTRAP, CONFIDENCE)
revocation_report(REVOCATION)
'''),
    ('''#@title 16. Stage 7 - compare with the study's original outputs
compare_with_original("score histograms", SCORES, "scores/score_histograms.json")
compare_with_original("ablation", ABLATION, "ablation/ablation_result.json")
compare_with_original("inversion", INVERSION, "inversion/inversion_result.json")
compare_with_original("revocation", REVOCATION, "revocation/revocation_result.json")
'''),
    ('''#@title 17. Stage 8 - draw every figure, then download them
STEMS = draw_figures(FIGURES_OUT, SWEEPS, SELECTED, FLOORS, INTERVALS,
                     BASELINE, ABLATION, INVERSION, REVOCATION,
                     WORK / "scores" / "score_histograms.json")
archive = shutil.make_archive(str(PROJECT / "AttackAware_PolyIoM_figures_regenerated"),
                              "zip", FIGURES_OUT)
print(f"\\n{len(STEMS)} figures, PNG and PDF, in {FIGURES_OUT}")
print(f"zip: {archive}")
if IN_COLAB:
    files.download(archive)
'''),
]


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source.splitlines(keepends=True)}


def markdown(source):
    return {"cell_type": "markdown", "metadata": {},
            "source": source.splitlines(keepends=True)}


def build():
    cells = [markdown(INTRO), code(SETUP)]
    for number, (name, what) in enumerate(FILES, start=2):
        body = (RUNTIME / name).read_text()
        cells.append(code(f"%%writefile {{RUNTIME}}/{name}\n"
                          f"# {number}. {what}\n" + body))
    cells.append(code(LOADER))
    cells += [code(s) for s in STAGES]
    notebook = {"cells": cells, "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"}},
        "nbformat": 4, "nbformat_minor": 4}
    OUT.write_text(json.dumps(notebook, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(HERE.parent)}  ({len(cells)} cells)")


if __name__ == "__main__":
    build()

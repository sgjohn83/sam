#!/usr/bin/env python3
"""Build kaggle/AttackAware_PolyIoM_KAGGLE_FRESH.ipynb.

The notebook carries every runtime file it needs (written out with
%%writefile) and a bundle of the study's recorded results, so on Kaggle it
needs nothing but Internet access and one attached dataset (the CFP name
list). It is assembled from code/runtime/ and kaggle/, never edited by hand.

    python3 kaggle/build_kaggle_notebook.py
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
RUNTIME = PACKAGE / "code" / "runtime"
RESULTS = PACKAGE / "results"
OUT = HERE / "AttackAware_PolyIoM_KAGGLE_FRESH.ipynb"

FILES = [
    (RUNTIME / "ablation_only.py", "The study's pipeline primitives and the ablation"),
    (RUNTIME / "scoredump_only.py", "The study's score histograms"),
    (RUNTIME / "inversion_only.py", "The study's full-knowledge inversion attack"),
    (RUNTIME / "revocation_only.py", "The study's revocation test"),
    (RUNTIME / "figures_only.py", "The study's code for Figures A to D"),
    (RUNTIME / "results_plots.py", "Drawing code for Figures 3 to 8, S2 and P"),
    (RUNTIME / "allfigures_only.py", "Sweep, intervals, baseline and figure driver"),
    (RUNTIME / "vctk_prepare_cells.py", "The study's VCTK preparation"),
    (HERE / "fresh_pipeline_only.py", "Acquisition to evaluation, and the comparison with the paper"),
]


def paper_reference():
    """What the study recorded: results, settings and provenance."""
    j = lambda rel: json.loads((RESULTS / rel).read_text())
    env = "environment/"
    return {
        "heldout": {m: j(f"heldout/{m}_heldout_result.json") for m in ("face", "voice")},
        "external": j("external/voice_external_result.json"),
        "ablation": j("ablation/ablation_result.json"),
        "inversion": j("inversion/inversion_result.json"),
        "revocation": j("revocation/revocation_result.json"),
        "intervals": j("heldout/confidence_intervals.json"),
        "baseline": j("scores/unprotected_baseline.json"),
        "config": j(env + "config_v1_1_4.json"),
        "ecapa": j(env + "ecapa_checkpoints.json"),
        "cfp": j(env + "cfp_authoritative_metadata.json"),
        "lfw_split": j(env + "lfw_split.json"),
        "sweeps": {m: [{k: (v if k == "modality" else float(v) if "." in v or "e" in v
                            else int(v)) for k, v in row.items()}
                       for row in csv.DictReader(open(RESULTS / f"sweep/{m}_sweep_80.csv"))]
                   for m in ("face", "voice")},
        "stages": {name: j(f"{env}stage_{name}.done.json") for name in (
            "lfw_raw", "lfw_embeddings", "libri_local", "libri_internal",
            "libri_embeddings", "vctk_manifest", "vctk_embeddings")},
    }


INTRO = """# AttackAware PolyIoM v1.1.4: the whole experiment, run freshly on Kaggle

This notebook reruns the study from the public datasets: it downloads LFW,
LibriSpeech and VCTK, extracts face and voice embeddings, splits the people,
searches for the polynomial key, selects the operating point, evaluates, runs
the ablation, the attack and the revocation test, draws every figure, and
compares every result with the paper.

**Before you start (Kaggle settings, right-hand panel)**
1. **Internet: On.** This needs a phone-verified Kaggle account.
2. **Accelerator: GPU T4 x2 or P100.** Used only for the key search.
3. **Add Input → Datasets → `chinafax/cfpw-dataset`.** This is the CFP name
   list the study used to exclude overlapping people.

**How to run.** Click **Save Version → Save & Run All (Commit)**. One Kaggle
session lasts at most 12 hours, and the whole experiment needs about three:

| Session | What it does |
|---|---|
| 1 | downloads, face and voice embeddings, the split, the tensors; starts the key search |
| 2 | finishes the key search |
| 3 | selection, evaluation, the external corpus, the analyses, the figures and the report |

**To continue after a session:** open the notebook, choose **Add Input →
Your Work → this notebook's output** (the latest version), and Save & Run All
again. The first cell restores the earlier work, and every finished stage is
skipped. When nothing is left to do, `REPLICATION_REPORT.md`, the figures and
a zip appear in the output.

**What "reproduce" means here.** The notebook runs the study's own code
(ported from its Colab notebook): the same downloads, face and voice models,
seeds, split, key search, tensors and selection rule. After every stage it
compares its output with the study's record and prints **identical** or
**DIFFERENT**. If every stage is identical, the paper is reproduced exactly.
If a stage differs (for example, a newer library moves a float), the run
continues, and the final report sets each result beside the paper's with
the fresh 95% interval.
"""

SETUP = '''#@title 1. Settings, earlier work and checklist
import hashlib, importlib.util, json, math, os, shutil, sys
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")   # deterministic GPU maths
import numpy as np
import pandas as pd
import torch
from IPython.display import display

PROJECT = Path(os.environ.get("POLYIOM_PROJECT", "/kaggle/working/AttackAware_PolyIoM_fresh"))
INPUT_ROOT = Path(os.environ.get("POLYIOM_INPUT", "/kaggle/input"))
RAW = Path(os.environ.get("POLYIOM_RAW", "/kaggle/tmp/attackaware_raw"))
RUNTIME = Path(os.environ.get("POLYIOM_RUNTIME", "/kaggle/tmp/polyiom_runtime"))

# Earlier sessions: copy their saved work back before anything is written.
MARKER = "ATTACKAWARE_FRESH_PROJECT.txt"     # visible: Kaggle may drop hidden files
if not (PROJECT / MARKER).is_file() and INPUT_ROOT.exists():
    for found in sorted(INPUT_ROOT.glob(f"**/{MARKER}")):
        shutil.copytree(found.parent, PROJECT, dirs_exist_ok=True)
        print(f"Restored earlier work from {found.parent}")
        break
PROJECT.mkdir(parents=True, exist_ok=True)
(PROJECT / MARKER).write_text("AttackAware PolyIoM fresh Kaggle run\\n")

DIR = {"protocol": PROJECT / "protocol", "embeddings": PROJECT / "embeddings",
       "runs": PROJECT / "runs", "seal": PROJECT / "seal",
       "datasets": RAW / "datasets", "preprocessed": PROJECT / "preprocessed"}
for path in list(DIR.values()) + [RAW, RUNTIME]:
    path.mkdir(parents=True, exist_ok=True)
RUNS_IN = DIR["runs"]
S0, G, PROTOCOL_VERSION = 2026, 5, "1.1.1"
DEVICE = torch.device("cpu")                 # hashing on CPU, as the study
DIMENSION = {"face": 512, "voice": 192}
N_BOOTSTRAP, CONFIDENCE = 2000, 0.95
LFW_FACE_TRIALS = DIR["protocol"] / "lfw_face_trials.tsv"
LFW_EMB = DIR["embeddings"] / "lfw_all_valid_embeddings.npz"
LIBRI_MANIFEST = DIR["protocol"] / "librispeech_internal.tsv"
LIBRI_EMB = DIR["embeddings"] / "librispeech_internal_embeddings.npz"
HELDOUT_RESULTS = {m: RUNS_IN / "heldout" / m / "heldout_result.json"
                   for m in ("face", "voice")}
ABLATION_OUTPUT = RUNS_IN / "ablation" / "ablation_result.json"
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
torch.backends.cudnn.benchmark = False
torch.use_deterministic_algorithms(True, warn_only=True)

free = shutil.disk_usage(RAW).free / 1e9
print(f"GPU      {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none - the key search will be slow'}")
print(f"disk     {free:.0f} GB free for downloads (about 25 GB needed)")
print(f"project  {PROJECT}")
'''

LOADER = '''#@title 12. Load the runtime
config_path = DIR["seal"] / "config_v1_1_4.json"
if not config_path.is_file():
    config_path.write_text(json.dumps(
        json.loads((RUNTIME / "paper_reference.json").read_text())["config"], indent=2))
for name in ("ablation_only.py", "scoredump_only.py", "inversion_only.py",
             "revocation_only.py", "allfigures_only.py", "vctk_prepare_cells.py",
             "fresh_pipeline_only.py"):
    exec(compile((RUNTIME / name).read_text(), str(RUNTIME / name), "exec"), globals())


def _module(name):
    spec = importlib.util.spec_from_file_location(name, RUNTIME / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


results_plots = _module("results_plots")
figures_only = _module("figures_only")
print("\\nWhere this run stands:")
status()
'''

STAGES = [
    '''#@title 13. Stage 0 - libraries and environment record
install_dependencies()
display(environment_record())
''',
    '''#@title 14. Stage 1 - LFW: download, MTCNN, FaceNet embeddings
stage_face()
''',
    '''#@title 15. Stage 2 - CFP exclusion, the 50/42/58 face split and trials
stage_face_split()
''',
    '''#@title 16. Stage 3 - LibriSpeech: download, 150 speakers, ECAPA embeddings
stage_voice()
''',
    '''#@title 17. Stage 4 - frozen IoM tensors
stage_tensors()
''',
    '''#@title 18. Stage 5 - Stage A key search (GPU; may span sessions)
KEYS_READY = stage_a("voice") and stage_a("face")    # face waits for voice
print("keys ready" if KEYS_READY else "key search continues in the next session")
''',
    '''#@title 19. Stage 6 - Stage B sweep, selection, held-out evaluation
INTERNAL_READY = False
if KEYS_READY:
    for m in ("voice", "face"):
        stage_b(m)
    for m in ("voice", "face"):
        stage_heldout(m)
    INTERNAL_READY = True
else:
    print("waiting for the key search")
''',
    '''#@title 20. Stage 7 - external corpus VCTK (read only now)
EXTERNAL_READY = False
if INTERNAL_READY:
    stage_external()
    EXTERNAL_READY = True
else:
    print("waiting for the internal evaluation")
''',
    '''#@title 21. Stage 8 - score dump, intervals, ablation, attack, revocation
ANALYSES_READY = False
if EXTERNAL_READY:
    SCORES = add_external_scores(run_score_dump())
    INTERVALS = run_intervals(N_BOOTSTRAP, CONFIDENCE)
    BASELINE = baseline_from_scores(SCORES)
    ABLATION = run_ablation(N_BOOTSTRAP, CONFIDENCE)
    INVERSION = run_inversion(N_BOOTSTRAP, CONFIDENCE)
    REVOCATION = run_revocation(N_BOOTSTRAP, CONFIDENCE)
    ANALYSES_READY = True
else:
    print("waiting for the external evaluation")
''',
    '''#@title 22. Stage 9 - every figure, the comparison with the paper, and a zip
if ANALYSES_READY:
    SWEEPS, SELECTED, FLOORS = {}, {}, {}
    for m in ("voice", "face"):
        SWEEPS[m] = pd.read_csv(RUNS_IN / "sweep" / m / "sweep_80.csv").to_dict("records")
        op = json.loads((DIR["seal"] / f"operating_point_{m}.json").read_text())
        SELECTED[m] = next(r for r in SWEEPS[m]
                           if (r["M"], r["q"], r["o"]) == (op["M"], op["q"], op["o"]))
        FLOORS[m] = (op["rule"]["eer_max"], op["rule"]["tar_min"])
    figures = PROJECT / "figures"
    draw_figures(figures, SWEEPS, SELECTED, FLOORS, INTERVALS, BASELINE,
                 ABLATION, INVERSION, REVOCATION, RUNS_IN / "scores" / "score_histograms.json")
    rows, claims = compare_with_paper(INTERVALS, ABLATION, INVERSION, REVOCATION)
    write_report(rows, claims)
    bundle = RAW / "bundle"
    shutil.rmtree(bundle, ignore_errors=True)
    shutil.copytree(figures, bundle / "figures")
    shutil.copytree(DIR["seal"], bundle / "seal")
    for f in RUNS_IN.glob("**/*.json"):
        (bundle / "runs" / f.relative_to(RUNS_IN)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, bundle / "runs" / f.relative_to(RUNS_IN))
    for name in ("REPLICATION_REPORT.md", "replication_report.json"):
        shutil.copy(PROJECT / name, bundle / name)
    print("zip:", shutil.make_archive(str(PROJECT / "AttackAware_PolyIoM_fresh_results"),
                                      "zip", bundle))
else:
    print("not finished yet; Save & Run All again in the next session")
    status()
''',
]


def code(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source.splitlines(keepends=True)}


def markdown(source):
    return {"cell_type": "markdown", "metadata": {},
            "source": source.splitlines(keepends=True)}


def build():
    cells = [markdown(INTRO), code(SETUP)]
    for number, (path, what) in enumerate(FILES, start=2):
        cells.append(code(f"%%writefile {{RUNTIME}}/{path.name}\n# {number}. {what}\n"
                          + path.read_text()))
    cells.append(code("%%writefile {RUNTIME}/paper_reference.json\n"
                      + json.dumps(paper_reference(), indent=1) + "\n"))
    cells.append(code(LOADER))
    cells += [code(s) for s in STAGES]
    notebook = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}, "kaggle": {"accelerator": "gpu",
                                                         "isInternetEnabled": True}},
        "nbformat": 4, "nbformat_minor": 4}
    OUT.write_text(json.dumps(notebook, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(PACKAGE)}  ({len(cells)} cells)")


if __name__ == "__main__":
    build()

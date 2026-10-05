#!/usr/bin/env python3
"""Draw paper Figures A to D from score_histograms.json, on any computer.

    python3 figures_from_scores.py path/to/score_histograms.json [outdir]

score_histograms.json is written by the study's SCOREDUMP notebook (or by
the ALL_FIGURES notebook) into runs/scores/ on Drive. Copy it anywhere and
point this script at it. Figures go to figures/ unless outdir is given.

  A  protected DET curves, and protection cost against unprotected matching
  B  genuine and impostor scores, with the sealed threshold
  C  mated and non-mated scores, with local unlinkability D_link(s)
  D  genuine, impostor and pseudo-impostor (revoked key) scores

The drawing is the study's own code, code/runtime/figures_only.py. Before
drawing, the script checks the file against the sealed results: the
protected EER rebuilt from each histogram must equal the sealed held-out
and external EER. The EER intervals drawn in Figure A are read from
results/heldout/confidence_intervals.json, not typed in.

Needs numpy, scipy and matplotlib.
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"


def load_figure_code():
    spec = importlib.util.spec_from_file_location(
        "figures_only", HERE / "code" / "runtime" / "figures_only.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_against_sealed(scores, eer_from):
    """Each protected histogram must give back the sealed EER."""
    sealed = {
        ("voice", "evaluation"): RES / "heldout" / "voice_heldout_result.json",
        ("face", "evaluation"): RES / "heldout" / "face_heldout_result.json",
        ("voice", "external"): RES / "external" / "voice_external_result.json",
    }
    for (modality, partition), path in sealed.items():
        h = scores["modalities"].get(modality, {}).get("partitions", {}).get(partition)
        if h is None:
            print(f"  {modality}/{partition}: not in this file, skipped")
            continue
        record = json.loads(path.read_text())
        expected = record.get("EER_HOLDOUT", record.get("EER_EXT"))
        rebuilt, _ = eer_from(h["genuine"], h["impostor"])
        if abs(rebuilt - expected) > 1e-9:
            raise SystemExit(f"{modality}/{partition}: this file gives EER "
                             f"{rebuilt * 100:.4f}%, the sealed result is "
                             f"{expected * 100:.4f}%. It is not the study's "
                             f"score dump; stopping.")
        print(f"  {modality}/{partition}: EER {rebuilt * 100:.4f}% matches "
              f"the sealed result")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(argv) == 2 else 2
    score_json = Path(argv[1]).expanduser().resolve()
    outdir = Path(argv[2]) if len(argv) > 2 else HERE / "figures"
    if not score_json.is_file():
        print(f"not found: {score_json}")
        return 1

    figures = load_figure_code()
    scores = json.loads(score_json.read_text())
    if scores.get("SYNTHETIC"):
        print("*** SYNTHETIC input: layout test only, not for the paper")
    else:
        print("checking the file against the sealed results")
        check_against_sealed(scores, figures.eer_from)

    # Figure A's EER intervals, from the stored interval file.
    intervals = json.loads((RES / "heldout" / "confidence_intervals.json")
                           .read_text())["partitions"]
    figures.CARRIED_CI = {tuple(part.split("/")): tuple(values["EER"])
                          for part, values in intervals.items()}

    figures.make_figures(score_json, outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""Run the ALL_FIGURES notebook end to end on a synthetic stand-in project.

The real notebook needs the study's embeddings and keys, which are on the
authors' Google Drive. This check builds a small project with the same
layout from random data, seals it with the study's own code, and then
executes the real notebook against it twice:

  run 1  computes everything and draws every figure;
  run 2  starts from nothing again, with run 1's outputs placed where the
         study's originals would be, so stage 7 must report every
         regenerated number as identical.

It proves the notebook runs and is deterministic. It cannot prove the
real figures, which only the real data can produce.

    pip install nbformat nbclient ipykernel torch pandas scipy matplotlib
    python3 code/check_all_figures_notebook.py [workdir]
"""

import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "notebooks" / "AttackAware_PolyIoM_v1_1_4_ALL_FIGURES.ipynb"
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
PROJECT, RUNTIME = ROOT / "project", ROOT / "runtime"
G, S0 = 5, 2026
DIMS = {"face": 512, "voice": 192}
N = {"development": 10, "evaluation": 12}
N_EXTERNAL = 12

results = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (f"   {detail}" if detail else ""))
    results.append(bool(ok))


def unit(v):
    return (v / np.linalg.norm(v)).astype(np.float32)


# ------------------------------------------------------ synthetic project
def build_project():
    rng = np.random.default_rng(7)
    for sub in ("protocol", "embeddings", "seal", "runs"):
        (PROJECT / sub).mkdir(parents=True, exist_ok=True)

    # Face: one enrolment and three probes per identity.
    rows, embs = [], []
    for partition, n in N.items():
        for s in range(n):
            centre = rng.standard_normal(DIMS["face"])
            for j in range(4):
                rows.append({"subject_id": f"{partition[:3]}{s:03d}",
                             "role": "enroll" if j == 0 else "probe",
                             "partition": partition, "embedding_index": len(embs)})
                embs.append(unit(centre + 0.9 * rng.standard_normal(DIMS["face"])))
    pd.DataFrame(rows).to_csv(PROJECT / "protocol" / "lfw_face_trials.tsv",
                              sep="\t", index=False)
    np.savez(PROJECT / "embeddings" / "lfw_all_valid_embeddings.npz",
             embedding=np.stack(embs))

    # Voice: fifteen ranked utterances per speaker, internal and external.
    def speakers(prefix, n, partition=None):
        out_rows, out_embs = [], []
        for s in range(n):
            centre = rng.standard_normal(DIMS["voice"])
            for rank in range(15):
                out_rows.append({"speaker_id": f"{prefix}{s:03d}", "rank": rank,
                                 **({"partition": partition} if partition else {})})
                out_embs.append(unit(centre + 0.9 * rng.standard_normal(DIMS["voice"])))
        return out_rows, out_embs

    manifest, vembs = [], []
    for partition, n in N.items():
        r, e = speakers(partition[:3], n, partition)
        manifest += r
        vembs += e
    pd.DataFrame(manifest).to_csv(PROJECT / "protocol" / "librispeech_internal.tsv",
                                  sep="\t", index=False)
    np.savez(PROJECT / "embeddings" / "librispeech_internal_embeddings.npz",
             embedding=np.stack(vembs),
             speaker_id=np.array([r["speaker_id"] for r in manifest]),
             rank=np.array([r["rank"] for r in manifest]))
    r, e = speakers("p", N_EXTERNAL)
    np.savez(PROJECT / "embeddings" / "vctk_external_embeddings.npz",
             embedding=np.stack(e), speaker_id=np.array([x["speaker_id"] for x in r]),
             rank=np.array([x["rank"] for x in r]),
             embedding_index=np.arange(len(e)))

    # Keys and frozen IoM tensors.
    for modality, d in DIMS.items():
        key_dir = PROJECT / "runs" / "key_search" / modality
        key_dir.mkdir(parents=True, exist_ok=True)
        # A well-conditioned stand-in key: mostly linear terms, so that the
        # revocation test's resampled keys rarely collapse.
        (key_dir / "selected_key.json").write_text(json.dumps({
            "C": [1.0, -0.8, 0.6, 1.2, -1.1], "E": [1, 1, 2, 1, 3]}))
        tensor_dir = PROJECT / "runs" / "iom_tensors"
        tensor_dir.mkdir(parents=True, exist_ok=True)
        for o in range(5):
            k = 1 + math.ceil((d - G) / (G - o))
            gen = torch.Generator().manual_seed(1000 * o + d)
            torch.save(torch.randn((256, 32, k), generator=gen),
                       tensor_dir / f"{modality}_o{o}_k{k}.pt")
    (PROJECT / "seal" / "config_v1_1_4.json").write_text(json.dumps({
        "M_grid": [32, 64, 128, 256], "q_grid": [4, 8, 16, 32],
        "overlaps": [0, 1, 2, 3, 4], "target_fmr": 0.001}))


def runtime_namespace(runs_out):
    """The notebook's globals, with the runtime files loaded, for sealing."""
    g = {"__name__": "seal"}
    exec("import hashlib, importlib.util, json, math, os\n"
         "from pathlib import Path\nimport numpy as np, pandas as pd, torch", g)
    g.update(PROJECT=PROJECT, RUNS_IN=PROJECT / "runs", S0=S0, G=G,
             DEVICE=torch.device("cpu"),
             DIR={"protocol": PROJECT / "protocol",
                  "embeddings": PROJECT / "embeddings",
                  "runs": runs_out, "seal": PROJECT / "seal"},
             LFW_FACE_TRIALS=PROJECT / "protocol" / "lfw_face_trials.tsv",
             LFW_EMB=PROJECT / "embeddings" / "lfw_all_valid_embeddings.npz",
             LIBRI_MANIFEST=PROJECT / "protocol" / "librispeech_internal.tsv",
             LIBRI_EMB=PROJECT / "embeddings" / "librispeech_internal_embeddings.npz",
             HELDOUT_RESULTS={m: PROJECT / "runs" / "heldout" / m / "heldout_result.json"
                              for m in DIMS})
    for name in ("ablation_only.py", "scoredump_only.py", "inversion_only.py",
                 "revocation_only.py", "allfigures_only.py"):
        path = HERE / "runtime" / name
        exec(compile(path.read_text(), str(path), "exec"), g)
    return g


def seal_project():
    """Seal the synthetic study with the study's own code, as the real one was."""
    g = runtime_namespace(PROJECT / "runs")
    for modality in DIMS:
        rows = g["run_sweep"](modality)                 # writes runs/sweep/
        eers = sorted(r["EER"] for r in rows)
        rule = {"eer_max": float(eers[len(eers) // 2]), "tar_min": 0.0}
        ok = [r for r in rows if r["EER"] <= rule["eer_max"]]
        best = min(ok, key=lambda r: (r["Dsys_DEV"], r["EER"], r["M"], r["q"], r["o"]))
        (PROJECT / "seal" / f"operating_point_{modality}.json").write_text(
            json.dumps({"rule": rule, "M": best["M"], "q": best["q"], "o": best["o"]}))
        M, q, o, tau = best["M"], best["q"], best["o"], int(best["c_tau_DEV"])

        subjects, enroll, probes = (g["face_heldout_data"]() if modality == "face"
                                    else g["voice_heldout_data"]())
        H = g["identity_histograms"](modality, subjects, enroll, probes, M, q, o, tau)
        gen, imp, mat, non = g["_apply_weights"](H, np.ones(H["n"]))
        point = g["_metrics"](H, np.ones(H["n"]))
        eer, _ = g["eer_from_histograms"](gen, imp)     # the ablation's definition
        sealed = {"M": M, "q": q, "o": o, "c_tau_carried_from_DEV": tau,
                  "n_subjects": H["n"], "EER_HOLDOUT": eer,
                  "TAR_HOLDOUT_at_dev_threshold": point["TAR"],
                  "FMR_HOLDOUT_at_dev_threshold": point["FMR"],
                  "Dsys_HOLDOUT": point["Dsys"],
                  "development_reference": {"EER": best["EER"],
                                            "Dsys_DEV": best["Dsys_DEV"]}}
        path = g["HELDOUT_RESULTS"][modality]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sealed))
        if modality == "voice":
            subjects, enroll, probes = g["vctk_external_data"]()
            H = g["identity_histograms"]("voice", subjects, enroll, probes, M, q, o, tau)
            p = g["_metrics"](H, np.ones(H["n"]))
            ext = PROJECT / "runs" / "external" / "voice" / "external_result.json"
            ext.parent.mkdir(parents=True, exist_ok=True)
            ext.write_text(json.dumps({
                "M": M, "q": q, "o": o, "c_tau_carried_from_DEV": tau,
                "n_subjects": H["n"], "EER_EXT": p["EER"],
                "TAR_EXT_at_dev_threshold": p["TAR"],
                "FMR_EXT_at_dev_threshold": p["FMR"], "Dsys_EXT": p["Dsys"]}))
        print(f"  sealed {modality}: M={M} q={q} o={o} tau={tau}")


# ------------------------------------------------------------- execution
FAST = """# test only: a small attack budget and few replicates
invert_arm.__defaults__ = (1, 30, INV_LR)
REV_N_KEYS = 6
N_BOOTSTRAP = 60
"""


def run_notebook(label):
    import nbclient
    import nbformat
    nb = nbformat.read(NOTEBOOK, as_version=4)
    at = next(i for i, c in enumerate(nb.cells)
              if c.cell_type == "code" and "Load the runtime" in c.source)
    nb.cells.insert(at + 1, nbformat.v4.new_code_cell(FAST))
    os.environ.update(POLYIOM_PROJECT=str(PROJECT), POLYIOM_RUNTIME=str(RUNTIME),
                      MPLBACKEND="Agg")
    client = nbclient.NotebookClient(nb, timeout=3600, kernel_name="python3",
                                     resources={"metadata": {"path": str(ROOT)}})
    try:
        client.execute()
        ok, detail = True, ""
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {str(exc)[-600:]}"
    nbformat.write(nb, ROOT / f"executed_{label}.ipynb")
    text = "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code"
                     for o in c.get("outputs", []))
    return ok, detail, text


def promote_run_one_to_originals():
    """Put run 1's outputs where the study's originals live, in their formats."""
    work, runs = PROJECT / "runs_regenerated", PROJECT / "runs"
    for rel in ("scores/score_histograms.json", "ablation/ablation_result.json",
                "inversion/inversion_result.json", "revocation/revocation_result.json"):
        (runs / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(work / rel, runs / rel)
    regenerated = json.loads((work / "intervals" / "confidence_intervals.json").read_text())
    names = {"EER": "EER_{}", "TAR": "TAR_{}_at_dev_threshold",
             "FMR": "FMR_{}_at_dev_threshold", "Dsys": "Dsys_{}"}
    held = {"modalities": {}}
    for part, rec in regenerated["partitions"].items():
        modality, partition = part.split("/")
        tag = "HOLDOUT" if partition == "evaluation" else "EXT"
        entry = {"bootstrap_seed": rec["bootstrap_seed"],
                 "metrics": {names[k].format(tag): v for k, v in rec["metrics"].items()}}
        if partition == "evaluation":
            held["modalities"][modality] = entry
        else:
            (runs / "external" / "voice" / "external_confidence.json").write_text(
                json.dumps({"modalities": {"voice": entry}}))
    (runs / "heldout" / "heldout_confidence.json").write_text(json.dumps(held))
    shutil.rmtree(work)
    shutil.rmtree(PROJECT / "figures_regenerated")


def main():
    subprocess_build = HERE / "build_all_figures_notebook.py"
    exec(compile(subprocess_build.read_text(), str(subprocess_build), "exec"),
         {"__name__": "__main__", "__file__": str(subprocess_build)})
    print(f"\nworking in {ROOT}\n\n[1] synthetic project, sealed with the study's code")
    build_project()
    seal_project()

    print("\n[2] run 1: compute everything and draw every figure")
    ok, detail, text = run_notebook("run1")
    check("the notebook runs from start to finish", ok, detail)
    figs = PROJECT / "figures_regenerated"
    stems = ["FigureS2_OperatingPointSelection", "Figure3_DesignSpace",
             "Figure4_Frontier", "Figure5_Generalisation", "FigureP_ProtectionCost",
             "Figure6_Ablation", "Figure7_RevocationPerKey", "Figure8_Inversion",
             "figA_det_preservation", "figB_score_separability",
             "figC_unlinkability", "figD_revocability"]
    have = [s for s in stems if (figs / f"{s}.png").is_file() and (figs / f"{s}.pdf").is_file()]
    check("all twelve figures written as PNG and PDF", len(have) == 12,
          f"{len(have)}/12; missing {sorted(set(stems) - set(have))}")
    check("a zip of the figures is written",
          (PROJECT / "AttackAware_PolyIoM_figures_regenerated.zip").is_file())
    check("the regenerated sweep equals the sealed one, 80 of 80 per modality",
          text.count("80 of 80 regenerated settings equal the sealed sweep") == 2)
    check("the selection rule picks the sealed setting for both modalities",
          text.count("- as sealed") == 2)
    check("rebuilt scores reproduce every sealed point estimate",
          text.count("point estimates reproduce the sealed result") == 3)
    check("nothing is written into runs/ or seal/",
          not (PROJECT / "runs" / "ablation").exists()
          and not (PROJECT / "runs" / "scores").exists())

    print("\n[3] run 2: from nothing again, against run 1 as the originals")
    promote_run_one_to_originals()
    ok, detail, text = run_notebook("run2")
    check("the notebook runs again from start to finish", ok, detail)
    for name in ("score histograms", "ablation", "inversion", "revocation"):
        line = next((l for l in text.splitlines() if l.strip().startswith(name)), "")
        check(f"{name}: every regenerated number identical", "identical" in line,
              line.strip())
    check("all three interval sets identical to the originals",
          text.count("(identical)") == 3)

    print(f"\n{sum(results)}/{len(results)} checks passed"
          + ("" if all(results) else "   <- FAILURES ABOVE"))
    print(f"executed notebooks: {ROOT}/executed_run1.ipynb, executed_run2.ipynb")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

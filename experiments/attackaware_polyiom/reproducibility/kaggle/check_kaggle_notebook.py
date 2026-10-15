#!/usr/bin/env python3
"""Run the Kaggle notebook end to end on miniature stand-in datasets.

The real run needs the public datasets, the face and voice models and a
GPU, none of which this check has. So it builds tiny archives with the same
layout as LFW, LibriSpeech, VCTK and the CFP list, replaces MTCNN, FaceNet
and ECAPA with deterministic stand-ins, shrinks the counts and budgets, and
executes the real notebook four times:

  1  a first session that runs out of time at the key search, and must stop
     cleanly with every later stage waiting;
  2  a second session that restores the first one's saved output from
     "/kaggle/input" and finishes everything;
  3  a rerun of the finished project, which must skip every stage and change
     no result;
  4  a run from nothing in a new folder, whose results must be identical to
     run 2's.

It proves the notebook's plumbing, resumption and determinism. It cannot
prove the real results, which only Kaggle with the real data can produce.

    pip install nbformat nbclient ipykernel soundfile pillow scipy matplotlib
    python3 kaggle/check_kaggle_notebook.py [workdir]
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "AttackAware_PolyIoM_KAGGLE_FRESH.ipynb"
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
SRC = ROOT / "sources"
SPLIT = {"background": 8, "development": 8, "evaluation": 10}
N_ID = sum(SPLIT.values())
results = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (f"   {detail}" if detail else ""))
    results.append(bool(ok))


def sha(path, algo="sha256"):
    return hashlib.new(algo, Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------- stand-in datasets
def build_sources():
    import soundfile as sf
    from PIL import Image
    rng = np.random.default_rng(11)
    SRC.mkdir(parents=True, exist_ok=True)

    # LFW: 32 eligible people, 3 of them on the CFP list, 2 with too few
    # images, and some images with no face (black) that MTCNN must reject.
    faces, valid, eligible = [], 0, 0
    with tarfile.open(SRC / "lfw.tgz", "w:gz") as tar:
        for p in range(N_ID + 6 + 2):
            name = f"Synth_Person{p:02d}"
            base = rng.uniform(0.2, 1.0, (8, 8, 3))
            n_img = 2 if p >= N_ID + 6 else 4 + p % 3
            good = 0
            for i in range(n_img + 1):
                if i == n_img:                       # one no-face image each
                    arr = np.zeros((64, 64, 3))
                else:
                    arr = np.kron(base, np.ones((8, 8, 1))) + 0.08 * rng.standard_normal((64, 64, 3))
                    good += 1
                buf = io.BytesIO()
                Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).save(buf, "JPEG", quality=95)
                info = tarfile.TarInfo(f"lfw/{name}/{name}_{i + 1:04d}.jpg")
                info.size = buf.tell()
                buf.seek(0)
                tar.addfile(info, buf)
                faces.append(name)
            valid += good
            eligible += good >= 3
    cfp = SRC / "input" / "cfpw-dataset" / "cfp-dataset" / "Data"
    cfp.mkdir(parents=True, exist_ok=True)
    (cfp / "list_name.txt").write_text(
        "\n".join([f"Synth Person{p:02d}" for p in (1, 5, 9)] + ["Someone Else"]) + "\n")

    def tone(f0, seconds, sr):
        t = np.arange(int(seconds * sr)) / sr
        x = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in (1, 2, 3))
        return (0.2 * x + 0.02 * rng.standard_normal(t.size)).astype(np.float32)

    # LibriSpeech: 30 speakers, 16 utterances each, 16 kHz FLAC.
    with tarfile.open(SRC / "train-clean-100.tar.gz", "w:gz") as tar:
        for s in range(N_ID + 4):
            spk = str(100 + s)
            for u in range(16):
                buf = io.BytesIO()
                sf.write(buf, tone(90 + 9 * s, 1.0 + 0.1 * (u % 4), 16000), 16000, format="FLAC")
                data = buf.getvalue()           # FLAC rewinds to patch its header
                info = tarfile.TarInfo(
                    f"LibriSpeech/train-clean-100/{spk}/77/{spk}-77-{u:04d}.flac")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

    # VCTK: 12 speakers at 48 kHz, every fourth utterance too short, so 15
    # of the 20 pass the validity gate.
    with zipfile.ZipFile(SRC / "VCTK-Corpus-0.92.zip", "w") as zf:
        for s in range(12):
            spk = f"p{225 + s}"
            for u in range(20):
                buf = io.BytesIO()
                sf.write(buf, tone(110 + 11 * s, 0.9 if u % 4 == 3 else 2.0, 48000),
                         48000, format="FLAC")
                zf.writestr(f"VCTK-Corpus-0.92/wav48_silence_trimmed/{spk}/"
                            f"{spk}_{u + 1:03d}_mic1.flac", buf.getvalue())
                zf.writestr(f"VCTK-Corpus-0.92/wav48_silence_trimmed/{spk}/"
                            f"{spk}_{u + 1:03d}_mic2.flac", b"ignored")
    return {"lfw_raw_images": len(faces), "lfw_valid": valid, "lfw_eligible": eligible}


TEST_CELL = """# ---- test only: stand-in sources, models and a small budget ----
import numpy as _np
SRC = Path({src!r})
URLS.update({{"lfw": [(SRC / "lfw.tgz").as_uri()],
             "libri": [(SRC / "train-clean-100.tar.gz").as_uri()],
             "vctk": [(SRC / "VCTK-Corpus-0.92.zip").as_uri()]}})
REF.update({ref!r})
SPLIT.clear(); SPLIT.update({split!r})
SELECTION_RULE_VOICE.update({{"eer_max": 1.0, "tar_min": 0.0}})
N_INIT, N_MAX, KEYSEARCH_CANDIDATE_BATCH = 6, 8, 4
ATTACK_RESTARTS, ATTACK_ITERS = 2, 15
STAGE1_RHO_MAX, STAGE1_TAR_MIN = -2.0, 0.0      # nobody passes gate 1 ...
STAGE2_RHO_MAX, STAGE2_TAR_MIN = 2.0, 0.0       # ... so gate 2 is exercised
invert_arm.__defaults__ = (1, 25, INV_LR)
REV_N_KEYS = 6
N_BOOTSTRAP = 60


class _MTCNN:
    def __call__(self, image, return_prob=False):
        a = _np.asarray(image, dtype=_np.float32) / 255
        if a.mean() < 0.05:
            return None, None
        small = _np.asarray(image.resize((16, 16)), dtype=_np.float32) / 255
        return torch.as_tensor(small).permute(2, 0, 1).contiguous(), 0.999


class _FaceNet:
    P = torch.as_tensor(_np.random.default_rng(1).standard_normal((768, 512)).astype(_np.float32))

    def __call__(self, x):
        return (x.reshape(x.shape[0], -1) - 0.5) @ self.P


class _Ecapa:
    P = torch.as_tensor(_np.random.default_rng(2).standard_normal((400, 192)).astype(_np.float32))

    def encode_batch(self, wav, wav_lens=None, normalize=False):
        # One direction per speaker (set by the tone's pitch), plus a little
        # utterance-to-utterance variation from the rest of the spectrum.
        spec = torch.fft.rfft(wav[0, :16000]).abs()[:400]
        f0 = int(torch.argmax(spec[20:])) + 20
        base = torch.as_tensor(_np.random.default_rng(f0).standard_normal(192).astype(_np.float32))
        feat = torch.log1p(spec)
        feat = (feat - feat.mean()) / (feat.std() + 1e-6)
        return (base + 0.3 * (feat @ self.P) / 20).reshape(1, 1, -1)


load_face_models = lambda: (_MTCNN(), _FaceNet())
load_ecapa = lambda: _Ecapa()
install_dependencies = lambda: print("  (test: no installs)")

try:
    download("lfw", RAW / "corrupt.tgz", sha256="0" * 64)
    print("CORRUPT-NOT-CAUGHT")
except RuntimeError:
    print("CORRUPT-CAUGHT", not (RAW / "corrupt.tgz").exists())
"""


def run(label, project, input_root, raw, hours, ref):
    import nbclient
    import nbformat
    nb = nbformat.read(NOTEBOOK, as_version=4)
    at = next(i for i, c in enumerate(nb.cells)
              if c.cell_type == "code" and "Load the runtime" in c.source)
    nb.cells.insert(at + 1, nbformat.v4.new_code_cell(
        TEST_CELL.format(src=str(SRC), ref=ref, split=SPLIT)))
    os.environ.update(POLYIOM_PROJECT=str(project), POLYIOM_INPUT=str(input_root),
                      POLYIOM_RAW=str(raw), POLYIOM_RUNTIME=str(ROOT / f"runtime_{label}"),
                      POLYIOM_SESSION_HOURS=str(hours), MPLBACKEND="Agg")
    client = nbclient.NotebookClient(nb, timeout=3600, kernel_name="python3",
                                     resources={"metadata": {"path": str(ROOT)}})
    try:
        client.execute()
        ok, detail = True, ""
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {str(exc)[-800:]}"
    nbformat.write(nb, ROOT / f"executed_{label}.ipynb")
    text = "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code"
                     for o in c.get("outputs", []))
    return ok, detail, text


OUTPUTS = ["runs/key_search/voice/selected_key.json", "runs/key_search/face/selected_key.json",
           "runs/key_search/voice/candidates.jsonl", "runs/key_search/face/candidates.jsonl",
           "runs/sweep/voice/sweep_80.csv", "runs/sweep/face/sweep_80.csv",
           "protocol/lfw_internal_split.tsv", "protocol/lfw_face_trials.tsv",
           "protocol/librispeech_internal.tsv", "protocol/vctk_manifest.tsv",
           "embeddings/lfw_all_valid_embeddings.npz",
           "embeddings/librispeech_internal_embeddings.npz",
           "embeddings/vctk_external_embeddings.npz",
           "seal/operating_point_voice.json", "seal/operating_point_face.json",
           "runs/heldout/voice/heldout_result.json", "runs/heldout/face/heldout_result.json",
           "runs/external/voice/external_result.json", "runs/intervals/confidence_intervals.json",
           "runs/ablation/ablation_result.json", "runs/inversion/inversion_result.json",
           "runs/revocation/revocation_result.json", "runs/scores/score_histograms.json",
           "REPLICATION_REPORT.md"]


def fingerprint(project):
    return {rel: sha(project / rel) for rel in OUTPUTS if (project / rel).is_file()}


def main():
    build = HERE / "build_kaggle_notebook.py"
    exec(compile(build.read_text(), str(build), "exec"),
         {"__name__": "__main__", "__file__": str(build)})
    print(f"\nworking in {ROOT}\n\n[0] stand-in datasets")
    truth = build_sources()
    ref = {**truth, "lfw_sha256": sha(SRC / "lfw.tgz"),
           "libri_md5": sha(SRC / "train-clean-100.tar.gz", "md5"),
           "vctk_md5": sha(SRC / "VCTK-Corpus-0.92.zip", "md5"),
           "libri_embeddings": N_ID * 15, "cfp_overlap": 3,
           "cfp_source_sha256": sha(SRC / "input/cfpw-dataset/cfp-dataset/Data/list_name.txt"),
           "vctk_speakers": 12, "vctk_utterances": 180}
    input_1 = SRC / "input"

    print("\n[1] session 1 runs out of time at the key search")
    p1 = ROOT / "session1" / "AttackAware_PolyIoM_fresh"
    ok, detail, text = run("s1", p1, input_1, ROOT / "raw1", 0.2, ref)
    check("the notebook finishes without an error", ok, detail)
    check("a corrupted download is caught and deleted", "CORRUPT-CAUGHT True" in text)
    check("the exact checks are reported",
          text.count("identical ") >= 6, f"{text.count('identical ')} identical lines")
    check("the key search stops cleanly for the next session",
          "session time nearly used" in text and "waiting for the key search" in text)
    check("embeddings, protocol and tensors are saved",
          (p1 / "seal/stage_lfw_face_trials.done.json").is_file()
          and (p1 / "seal/stage_libri_embeddings.done.json").is_file()
          and len(list((p1 / "runs/iom_tensors").glob("*.pt"))) == 10)

    print("\n[2] session 2 restores session 1 and finishes")
    input_2 = ROOT / "input2"
    shutil.copytree(input_1, input_2, dirs_exist_ok=True)
    shutil.copytree(p1, input_2 / "previous-version" / "AttackAware_PolyIoM_fresh")
    p2 = ROOT / "session2" / "AttackAware_PolyIoM_fresh"
    ok, detail, text = run("s2", p2, input_2, ROOT / "raw2", 11, ref)
    check("the notebook finishes without an error", ok, detail)
    check("earlier work is restored, not recomputed",
          "Restored earlier work" in text and "RESUME: LFW embeddings present." in text
          and "RESUME: face split and trials present." in text
          and "RESUME: LibriSpeech embeddings present." in text)
    check("gate 1 fails, so the search goes on to gate 2 and picks a key",
          all((p2 / f"runs/key_search/{m}/selected_key.json").is_file() and
              json.loads((p2 / f"runs/key_search/{m}/selected_key.json").read_text())
              ["selected_stage"] == 2 for m in ("voice", "face")))
    figs = p2 / "figures"
    n_png = len(list(figs.glob("*.png"))) if figs.is_dir() else 0
    check("all twelve figures are drawn", n_png == 12, f"{n_png} PNG")
    check("the replication report and the zip are written",
          (p2 / "REPLICATION_REPORT.md").is_file()
          and (p2 / "AttackAware_PolyIoM_fresh_results.zip").is_file())
    report = (p2 / "REPLICATION_REPORT.md").read_text() if (p2 / "REPLICATION_REPORT.md").is_file() else ""
    check("the report has exact checks, results and findings",
          all(h in report for h in ("Stage by stage", "Results against the paper",
                                    "paper's findings")))
    check("stand-in data is reported as DIFFERENT from the study, not hidden",
          "DIFFERENT" in report and "| LFW raw images |" in report)
    exact = {r["check"]: r["verdict"] for r in json.loads(
        (p2 / "seal/exact_checks.json").read_text())} if (p2 / "seal/exact_checks.json").is_file() else {}
    known = ["lfw archive sha256", "libri archive md5", "vctk archive md5", "LFW raw images",
             "LFW valid embeddings", "LFW identities with at least 3 valid images",
             "CFP list_name.txt sha256", "LFW identities excluded by the CFP overlap",
             "LibriSpeech embeddings", "VCTK speakers kept", "VCTK utterances kept"]
    check("every value set to the stand-in truth is reported identical",
          all(exact.get(k) == "identical" for k in known),
          str({k: exact.get(k) for k in known if exact.get(k) != "identical"}))
    check("values only the real data can give are reported DIFFERENT",
          exact.get("LFW 50/42/58 split sha256") == "DIFFERENT"
          and exact.get("voice sealed operating point (M, q, o, tau)") == "DIFFERENT")
    first = fingerprint(p2)

    print("\n[3] rerunning a finished project changes nothing")
    ok, detail, text = run("s3", p2, input_2, ROOT / "raw2", 11, ref)
    check("the notebook finishes without an error", ok, detail)
    check("every result file is unchanged", fingerprint(p2) == first)

    print("\n[4] a run from nothing gives identical results")
    p3 = ROOT / "fresh" / "AttackAware_PolyIoM_fresh"
    ok, detail, text = run("s4", p3, input_1, ROOT / "raw3", 11, ref)
    check("the notebook finishes without an error", ok, detail)
    second = fingerprint(p3)
    differing = [k for k in first if first[k] != second.get(k)]
    check(f"all {len(first)} result files identical to run 2", not differing and
          len(first) == len(OUTPUTS), f"differ: {differing}")

    print(f"\n{sum(results)}/{len(results)} checks passed"
          + ("" if all(results) else "   <- FAILURES ABOVE"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

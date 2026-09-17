"""Local test harness: stubs the v1.1.4 notebook globals and exercises the
parts of the updated Drive cells that do not need embeddings or a GPU."""
import hashlib
import io
import json
import math
import os
import sys
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/polyiom_test")
SRC = Path(__file__).parent

# ------------------------------------------------------------------ torch stub
torch = types.ModuleType("torch")
torch.__version__ = "2.11.0+cu128"
torch.Tensor = type("Tensor", (), {})      # scipy's array-api probe reads this
torch.version = types.SimpleNamespace(cuda="12.8")
torch.cuda = types.SimpleNamespace(
    is_available=lambda: True, get_device_name=lambda i: "Tesla T4")
torch.backends = types.SimpleNamespace(
    cudnn=types.SimpleNamespace(version=lambda: 91900))
sys.modules["torch"] = torch


def make_env():
    """A fresh notebook-like namespace with the sealed project on disk."""
    for sub in ("seal", "runs", "embeddings", "datasets", "preprocessed",
                "protocol", "models"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    DIR = {k: ROOT / k for k in
           ("seal", "runs", "embeddings", "datasets", "preprocessed",
            "protocol", "models")}

    def sha256_file(path):
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()

    def atomic_json(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(obj, indent=2, sort_keys=True))
        os.replace(tmp, path)

    def mark_stage(stage, payload):
        atomic_json(DIR["seal"] / f"stage_{stage}.done.json",
                    {"stage": stage, **payload})

    def verified_stage(stage, artifacts):
        marker = DIR["seal"] / f"stage_{stage}.done.json"
        if not marker.exists():
            return False
        rec = json.loads(marker.read_text())
        for path, key in artifacts:
            if not Path(path).exists() or rec.get(key) != sha256_file(path):
                return False
        return True

    g = {
        "__name__": "nb", "DIR": DIR,
        "json": json, "math": math, "os": os, "np": np, "pd": pd,
        "Path": Path, "torch": torch,
        "sha256_file": sha256_file, "atomic_json": atomic_json,
        "mark_stage": mark_stage, "verified_stage": verified_stage,
        "assert_internal_frozen": lambda m: None,
        "l2_np": lambda v: v / (np.linalg.norm(v) + 1e-12),
        "PROTOCOL_VERSION": "1.1.1", "N_EVAL": 58, "N_DEV": 42, "G": 5,
        "MODEL_DEVICE": "cpu",
    }
    return g


def load(g, name):
    exec(compile((SRC / name).read_text(), name, "exec"), g)
    return g


def install_sweeps():
    """Real face sweep_80.csv; a small synthetic voice one for rule tests."""
    face_src = SRC / "sweep_80_face.csv"
    (ROOT / "runs" / "sweep" / "face").mkdir(parents=True, exist_ok=True)
    (ROOT / "runs" / "sweep" / "voice").mkdir(parents=True, exist_ok=True)
    (ROOT / "runs" / "sweep" / "face" / "sweep_80.csv").write_text(
        face_src.read_text())

    # Two rows that both clear the voice floor; the lower-Dsys one must win.
    pd.DataFrame([
        dict(modality="voice", M=128, q=32, o=1, n_subjects=42, n_genuine=420,
             n_impostor=17220, c_tau_DEV=37, EER=0.00952380952380952, c_EER=29,
             TAR_DEV=0.9523809523809523, FMR_DEV=0.000813, FNMR_DEV=0.047619,
             Dsys_DEV=0.05251857190074913),
        dict(modality="voice", M=256, q=32, o=1, n_subjects=42, n_genuine=420,
             n_impostor=17220, c_tau_DEV=67, EER=0.007142857142857143, c_EER=55,
             TAR_DEV=0.9761904761904762, FMR_DEV=0.000871, FNMR_DEV=0.023809,
             Dsys_DEV=0.10726455286119560),
    ]).to_csv(ROOT / "runs" / "sweep" / "voice" / "sweep_80.csv", index=False)


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label
          + (f"   {detail}" if detail else ""))
    return bool(cond)


results = []

# ---------------------------------------------------------------- selection
print("\n[1] operating-point selection")
install_sweeps()
g = make_env()
load(g, "external_eval_cells.py")
load(g, "heldout_eval_cells.py")

voice = g["select_operating_point"]("voice")
results.append(check(
    "voice reproduces the sealed choice M=128 q=32 o=1",
    (voice["M"], voice["q"], voice["o"]) == (128, 32, 1),
    f"got M={voice['M']} q={voice['q']} o={voice['o']} "
    f"rule={voice['rule']['rule_id']}"))
results.append(check(
    "voice rule is the unmodified default",
    voice["rule"]["rule_id"] == "min_dsys_subject_to_eer_floor_v1"))

print("\n  face_floor_report():")
g["face_floor_report"]()

face = g["seal_face_operating_point"]()
results.append(check(
    "face falls back to FACE_FLOOR and selects M=256 q=32 o=1",
    (face["M"], face["q"], face["o"]) == (256, 32, 1),
    f"got M={face['M']} q={face['q']} o={face['o']} "
    f"n_eligible={face['n_eligible']}"))
results.append(check(
    "face seal records eer_max=0.03 / tar_min=0.85",
    (face["rule"]["eer_max"], face["rule"]["tar_min"]) == (0.03, 0.85)))
results.append(check(
    "face seal carries a deviation_reason for the paper",
    bool(face["rule"].get("deviation_reason"))))
results.append(check(
    "face eligible pool is 13 configurations",
    face["n_eligible"] == 13, f"got {face['n_eligible']}"))

# Re-seal in the same session must be a no-op, not an error.
again = g["seal_face_operating_point"]()
results.append(check("re-sealing face is idempotent", again == face))

# ------------------------------------------------- fresh runtime, same seal
print("\n[2] resume in a fresh runtime (the bug this fixes)")
g2 = make_env()
load(g2, "external_eval_cells.py")
load(g2, "heldout_eval_cells.py")
try:
    reloaded = g2["select_operating_point"]("face")
    ok = reloaded == face
    err = ""
except Exception as exc:
    ok, err = False, f"{type(exc).__name__}: {exc}"
results.append(check(
    "sealed face rule is re-adopted, not rejected", ok, err))

try:
    g2["evaluate_external"]("face")
    ok, err = False, "no error raised"
except NotImplementedError as exc:
    ok, err = True, str(exc)[:60]
except Exception as exc:
    ok, err = False, f"{type(exc).__name__}: {exc}"
results.append(check(
    "external face is refused explicitly, not scored against VCTK",
    ok, err))

# ------------------------------------------------------ immutability intact
print("\n[3] immutability of a sealed choice")
g3 = make_env()
load(g3, "external_eval_cells.py")
g3["SELECTION_RULE"]["eer_max"] = 0.005      # tamper after sealing
try:
    g3["select_operating_point"]("voice")
    ok, err = False, "no error raised"
except RuntimeError as exc:
    ok, err = "immutable" in str(exc), str(exc)[:60]
results.append(check(
    "editing the rule after sealing still raises", ok, err))

# ------------------------------------------------------------- vctk helpers
print("\n[4] VCTK preparation")
g4 = make_env()
load(g4, "external_eval_cells.py")
load(g4, "vctk_prepare_cells.py")

rng = np.random.default_rng(0)
x48 = rng.standard_normal(48000 * 2).astype(np.float32) * 0.1
y = g4["_to_16k"](x48, 48000)
results.append(check("48 kHz -> 16 kHz is exact 1/3 decimation",
                     abs(len(y) - 32000) <= 1, f"{len(y)} samples"))

wav = ROOT / "preprocessed" / "t.wav"
n = g4["_write_wav_16k"](wav, y)
results.append(check("wav round-trips its frame count",
                     g4["_wav_frames"](wav) == n, f"{n} frames"))

# A miniature VCTK: 3 speakers, one of them short of 15 valid utterances,
# plus mic2 members that must be ignored.
try:
    import soundfile as sf
    have_sf = True
except ImportError:
    have_sf = False

zip_path = ROOT / "datasets" / "VCTK-Corpus-0.92" / "VCTK-Corpus-0.92.zip"
zip_path.parent.mkdir(parents=True, exist_ok=True)
# Every third utterance is too short, so p225 has 16 valid and p226 18,
# while p227 can only supply 6 and must be dropped.
plan = {"p225": 24, "p226": 27, "p227": 9}


def flac_bytes(seconds):
    x = (rng.standard_normal(int(48000 * seconds)) * 0.05).astype(np.float32)
    if have_sf:
        buf = io.BytesIO()
        sf.write(buf, x, 48000, format="FLAC")
        return buf.getvalue()
    return x.tobytes()          # decoder is monkeypatched below


with zipfile.ZipFile(zip_path, "w") as zf:
    for spk, count in plan.items():
        for i in range(count):
            # Every third utterance is too short to survive the gate.
            secs = 0.9 if i % 3 == 2 else 2.5
            zf.writestr(
                f"wav48_silence_trimmed/{spk}/{spk}_{i+1:03d}_mic1.flac",
                flac_bytes(secs))
            zf.writestr(
                f"wav48_silence_trimmed/{spk}/{spk}_{i+1:03d}_mic2.flac",
                b"not-a-flac-and-must-be-ignored")

if not have_sf:
    g4["_decode_flac"] = lambda raw: (
        np.frombuffer(raw, dtype=np.float32), 48000)

manifest = g4["prepare_vctk"](progress_every=0)
counts = manifest.groupby("speaker_id").size().to_dict()
results.append(check(
    "only speakers with 15 valid utterances are kept",
    sorted(counts) == ["p225", "p226"] and set(counts.values()) == {15},
    str(counts)))
results.append(check(
    "ranks are 0..14 per speaker",
    all(sorted(gp["rank"]) == list(range(15))
        for _, gp in manifest.groupby("speaker_id"))))
results.append(check(
    "mic2 members are excluded",
    not manifest["source_member"].str.contains("mic2").any()))
results.append(check(
    "ranks follow sorted filename order (reproducible without a seed)",
    all(list(gp.sort_values("rank")["source_member"])
        == sorted(gp["source_member"])
        for _, gp in manifest.groupby("speaker_id"))))
results.append(check(
    "every kept utterance clears the 24000-sample gate",
    bool((manifest["n_samples"] >= 24000).all()),
    f"min {int(manifest['n_samples'].min())}"))
results.append(check(
    "all manifest audio exists on disk",
    all((g4["DIR"]["audio_vctk"] / r).exists()
        for r in manifest["relative_path"])))

again = g4["prepare_vctk"](progress_every=0)
results.append(check("prepare_vctk resumes from the verified stage",
                     len(again) == len(manifest)))

g4["vctk_manifest_report"]()

# ------------------------------------------------------------ runtime deps
print("\n[5] runtime dependency record")
g5 = make_env()
load(g5, "runtime_deps_cells.py")
env = g5["ensure_runtime_deps"](install=False, verbose=False)
sealed = json.loads(
    (ROOT / "seal" / "latest_runtime_environment.json").read_text())
results.append(check(
    "environment record keeps the sealed key schema",
    set(sealed) == {"av", "cuda_available", "cuda_version", "cudnn_version",
                    "facenet-pytorch", "gpu", "numpy", "pandas", "platform",
                    "python", "speechbrain", "torch", "torchaudio",
                    "torchvision"},
    str(sorted(set(sealed)))))
results.append(check("install=False installs nothing",
                     sealed["torch"] == "2.11.0+cu128"))

print(f"\n{sum(results)}/{len(results)} checks passed"
      + ("" if all(results) else "   <- FAILURES ABOVE"))
sys.exit(0 if all(results) else 1)

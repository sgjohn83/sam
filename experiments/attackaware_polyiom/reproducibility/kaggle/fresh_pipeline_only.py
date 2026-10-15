"""The whole AttackAware PolyIoM v1.1.4 study, rerun from the public data.

Loaded by AttackAware_PolyIoM_KAGGLE_FRESH.ipynb after the study's analysis
runtime (ablation_only, scoredump_only, inversion_only, revocation_only,
allfigures_only, vctk_prepare_cells).

Stages 1 to 5 are ported from the study's own Colab notebook,
AttackAware_PolyIoM_v1_1_4_PublicData_15GB_Resumable_CHECKPOINT_FIX.ipynb
(cells 5 to 22): the downloads, MTCNN and FaceNet, the CFP gate, the LFW
and LibriSpeech splits, ECAPA, the polynomial key generator, the IoM
tensors and the Stage A key search, with the same seed labels and rules.
Only the plumbing changes: Kaggle paths instead of Google Drive, soundfile
for audio input and output (FLAC is lossless, so the samples are the same),
and the ECAPA normalisation checkpoint hash taken from the study's sealed
record (cd70225b...), which the notebook's constant (0eb77a0b...) does not
match.

Every stage compares what it produces with what the study recorded and
prints "identical" or "DIFFERENT". If every stage is identical, this is an
exact reproduction. Where a stage differs (a newer library can move a
float), the run carries on, and the final report sets each result beside
the paper's with the fresh 95% interval.

Every stage writes a marker under seal/, so a rerun skips it and a new
Kaggle session continues where the last one stopped.
"""

import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import torch

# ------------------------------------------------------------- the record
PAPER = json.loads((RUNTIME / "paper_reference.json").read_text())

# The study's frozen constants (its notebook, cell 2).
SPLIT = {"background": 50, "development": 42, "evaluation": 58}
M_REF, Q_REF, O_REF = 128, 16, 2
TARGET_FMR = 1e-3
N_INIT, N_MAX = 10_000, 20_000
STAGE1_RHO_MAX, STAGE1_TAR_MIN = 0.90, 0.95
STAGE2_RHO_MAX, STAGE2_TAR_MIN = 0.85, 0.90
ATTACK_RESTARTS, ATTACK_ITERS, ATTACK_LR = 5, 2000, 0.01
ATTACK_BETAS, ATTACK_EPS, ATTACK_INIT_STD = (0.9, 0.999), 1e-8, 0.1
KEYSEARCH_CANDIDATE_BATCH = 32
FACE_VALID_PROB = 0.95
SELECTION_RULE_VOICE = {"eer_max": 0.01, "tar_min": 0.95}
FACE_FLOOR = {"eer_max": 0.03, "tar_min": 0.85}
NONZERO_COEFFS = np.array(list(range(-50, 0)) + list(range(1, 51)), dtype=np.int64)

URLS = {
    "lfw": ["https://ndownloader.figshare.com/files/5976018",
            "http://vis-www.cs.umass.edu/lfw/lfw.tgz"],
    "libri": ["https://www.openslr.org/resources/12/train-clean-100.tar.gz",
              "https://us.openslr.org/resources/12/train-clean-100.tar.gz",
              "https://openslr.elda.org/resources/12/train-clean-100.tar.gz"],
    "vctk": ["https://datashare.ed.ac.uk/bitstreams/"
             "535f4286-e54c-4038-838c-a02285e32cb2/download",
             "https://datashare.ed.ac.uk/bitstream/handle/10283/3443/"
             "VCTK-Corpus-0.92.zip"],
}
REF = {
    "lfw_sha256": "055f7d9c632d7370e6fb4afc7468d40f970c34a80d4c6f50ffec63f5a8d536c0",
    "libri_md5": "2a93770f6d5c6c964bc36631d331a522",
    "vctk_md5": "8a6ba2946b36fcbef0212cad601f4bfa",
    "lfw_raw_images": PAPER["stages"]["lfw_raw"]["raw_images"],
    "lfw_valid": PAPER["stages"]["lfw_embeddings"]["valid_embeddings"],
    "lfw_eligible": PAPER["stages"]["lfw_embeddings"]["identities_with_at_least_3_valid"],
    "lfw_embeddings_sha256": PAPER["stages"]["lfw_embeddings"]["embeddings_sha256"],
    "cfp_source_sha256": PAPER["cfp"]["source_sha256"],
    "cfp_metadata_sha256": PAPER["cfp"]["metadata_sha256"],
    "cfp_overlap": PAPER["lfw_split"]["excluded_exact_overlap_count"],
    "lfw_split_sha256": PAPER["lfw_split"]["split_sha256"],
    "lfw_excluded_sha256": PAPER["lfw_split"]["excluded_sha256"],
    "libri_manifest_sha256": PAPER["stages"]["libri_internal"]["manifest_sha256"],
    "libri_embeddings": PAPER["stages"]["libri_embeddings"]["embeddings"],
    "libri_embeddings_sha256": PAPER["stages"]["libri_embeddings"]["sha256"],
    "vctk_manifest_sha256": PAPER["stages"]["vctk_manifest"]["manifest_sha256"],
    "vctk_speakers": PAPER["stages"]["vctk_manifest"]["n_speakers"],
    "vctk_utterances": PAPER["stages"]["vctk_manifest"]["n_utterances"],
    "vctk_embeddings_sha256": PAPER["stages"]["vctk_embeddings"]["sha256"],
    "ecapa_repo": PAPER["ecapa"]["repo_id"],
    "ecapa_revision": PAPER["ecapa"]["revision"],
    "ecapa_embedding_sha256": PAPER["ecapa"]["embedding_model_ckpt"]["sha256"],
    "ecapa_norm_sha256": PAPER["ecapa"]["mean_var_norm_emb_ckpt"]["sha256"],
    "voice_key_sha256": PAPER["external"].get("voice_key_sha256"),
}
CFP_KAGGLE = "chinafax/cfpw-dataset"

EXTRACT_DEVICE = torch.device(os.environ.get("POLYIOM_EXTRACT_DEVICE", "cpu"))
ATTACK_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SESSION_START = time.time()
SESSION_BUDGET_H = float(os.environ.get("POLYIOM_SESSION_HOURS", "11.0"))

MODELS = PROJECT / "models"
LFW_LOCAL_ROOT = RAW / "lfw_extract"
LIBRI_LOCAL_ROOT = RAW / "LibriSpeech_extract"
LIBRI_SELECTED_ROOT = PROJECT / "datasets" / "LibriSpeech_selected"
VCTK_ARCHIVE = RAW / "VCTK-Corpus-0.92.zip"
LFW_VALIDITY = DIR["protocol"] / "lfw_validity.tsv"
LFW_SPLIT = DIR["protocol"] / "lfw_internal_split.tsv"
LFW_EXCLUDED = DIR["protocol"] / "lfw_excluded_cfp_overlap.txt"
CFP_METADATA_DIR = DIR["protocol"] / "cfp_authoritative_metadata"
CFP_METADATA = CFP_METADATA_DIR / "cfp_subject_names.tsv"


# --------------------------------------------------------------- markers
def stage_file(name):
    return DIR["seal"] / f"stage_{name}.done.json"


def stage_done(name):
    return stage_file(name).exists()


def mark_stage(name, payload=None):
    payload = dict(payload or {})
    payload.update({"stage": name, "protocol_version": PROTOCOL_VERSION,
                    "completed_unix": time.time()})
    atomic_json(stage_file(name), payload)


def verified_stage(stage, artifacts):
    if not stage_done(stage):
        return False
    record = json.loads(stage_file(stage).read_text())
    return all(Path(p).is_file() and record.get(k) == sha256_file(p)
               for p, k in artifacts)


def time_left_h():
    return SESSION_BUDGET_H - (time.time() - SESSION_START) / 3600


def exact(label, got, expected, tol=None):
    """One line of the reproduction record: does the fresh run give the
    study's value?"""
    if tol is not None and isinstance(got, (int, float)) and isinstance(expected, (int, float)):
        same = abs(float(got) - float(expected)) <= tol
    else:
        same = got == expected
    path = DIR["seal"] / "exact_checks.json"
    rows = json.loads(path.read_text()) if path.is_file() else []
    rows = [r for r in rows if r["check"] != label] + [{
        "check": label, "fresh": got, "study": expected,
        "verdict": "identical" if same else "DIFFERENT"}]
    atomic_json(path, rows)
    print(f"  {'identical' if same else 'DIFFERENT':<10} {label}"
          + ("" if same else f": fresh {got}, study {expected}"))
    return same


# ------------------------------------------------------------- downloads
def md5_file(path, chunk=8 * 1024 * 1024):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def download(name, dest, sha256=None, md5=None):
    """Fetch from the first working source, resuming a partial file, and
    verify it. A file that fails its hash is deleted and the error raised."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = Path(str(dest) + ".part")
    if not dest.is_file():
        last = None
        for url in URLS[name]:
            try:
                offset = part.stat().st_size if part.is_file() else 0
                request = urllib.request.Request(url)
                if offset and url.startswith("http"):
                    request.add_header("Range", f"bytes={offset}-")
                with urllib.request.urlopen(request, timeout=120) as response:
                    resumed = getattr(response, "status", 200) == 206
                    print(f"  {name}: downloading from {url}"
                          + (" (resuming)" if resumed else ""), flush=True)
                    with open(part, "ab" if resumed else "wb") as out:
                        shutil.copyfileobj(response, out, length=1 << 24)
                os.replace(part, dest)
                break
            except Exception as exc:
                last = exc
                print(f"  {name}: {url} failed - {type(exc).__name__}: {exc}")
        else:
            raise RuntimeError(f"{name}: every source failed (last error: {last}). "
                               "Is Internet switched on in the notebook settings?")
    for label, expected, fn in (("sha256", sha256, sha256_file), ("md5", md5, md5_file)):
        if expected:
            got = fn(dest)
            if got != expected:
                dest.unlink()
                raise RuntimeError(f"{name}: {label} {got} is not the study's "
                                   f"{expected}; the file was deleted.")
            exact(f"{name} archive {label}", got, expected)
    return dest


# ---------------------------------------------- stage 0: libraries, models
def install_dependencies():
    """As the study's cell 1, except facenet-pytorch goes in without its
    dependency pins, which would downgrade torch (runtime_deps_cells.py)."""
    before = torch.__version__
    for spec, nodeps in (("facenet-pytorch==2.6.0", True), ("speechbrain==1.1.1", False)):
        try:
            __import__(spec.split("==")[0].replace("-", "_"))
            continue
        except ImportError:
            pass
        cmd = [sys.executable, "-m", "pip", "install", "-q", spec]
        print("  pip install", spec, "(no dependencies)" if nodeps else "")
        subprocess.check_call(cmd + (["--no-deps"] if nodeps else []))
    print(f"  torch {before} before, {torch.__version__} after")


def environment_record():
    from importlib import metadata

    def version(name):
        try:
            return metadata.version(name)
        except Exception:
            return None
    env = {"python": sys.version, "platform": platform.platform(),
           "torch": torch.__version__, "cuda_available": torch.cuda.is_available(),
           "cuda_version": torch.version.cuda,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "extract_device": str(EXTRACT_DEVICE), "attack_device": str(ATTACK_DEVICE)}
    for name in ("numpy", "pandas", "scipy", "torchaudio", "torchvision",
                 "facenet-pytorch", "speechbrain", "soundfile", "huggingface-hub"):
        env[name] = version(name)
    atomic_json(DIR["seal"] / "environment.json", env)
    return env


def load_face_models():
    """The study's MTCNN and FaceNet (its notebook, cell 5)."""
    from facenet_pytorch import MTCNN, InceptionResnetV1
    os.environ["TORCH_HOME"] = str(MODELS / "torch")
    mtcnn = MTCNN(image_size=160, margin=0, min_face_size=20,
                  thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True,
                  select_largest=True, keep_all=False, device=EXTRACT_DEVICE)
    resnet = InceptionResnetV1(pretrained="vggface2").eval().to(EXTRACT_DEVICE)
    return mtcnn, resnet


def load_ecapa():
    """ECAPA at the study's pinned revision, both checkpoints hash-checked."""
    from huggingface_hub import hf_hub_download, snapshot_download
    try:
        from speechbrain.inference.speaker import EncoderClassifier
    except Exception:
        from speechbrain.inference.classifiers import EncoderClassifier
    ecapa_dir = MODELS / f"ecapa_{REF['ecapa_revision']}"
    ecapa_dir.mkdir(parents=True, exist_ok=True)
    if not (ecapa_dir / "hyperparams.yaml").exists():
        snapshot_download(repo_id=REF["ecapa_repo"], revision=REF["ecapa_revision"],
                          local_dir=str(ecapa_dir))
    for filename, expected in (("embedding_model.ckpt", REF["ecapa_embedding_sha256"]),
                               ("mean_var_norm_emb.ckpt", REF["ecapa_norm_sha256"])):
        path = ecapa_dir / filename
        if not path.is_file() or sha256_file(path) != expected:
            fresh = hf_hub_download(repo_id=REF["ecapa_repo"], filename=filename,
                                    revision=REF["ecapa_revision"], force_download=True)
            shutil.copy2(fresh, path)
        exact(f"ECAPA {filename} sha256", sha256_file(path), expected)
    return EncoderClassifier.from_hparams(source=str(ecapa_dir),
                                          savedir=str(MODELS / "ecapa_loaded"),
                                          run_opts={"device": str(EXTRACT_DEVICE)})


def ecapa_embed_waveform(model, wav_16k_mono):
    """The study's embedding call (its notebook, cell 5)."""
    wav = torch.as_tensor(wav_16k_mono, dtype=torch.float32,
                          device=EXTRACT_DEVICE).reshape(1, -1)
    with torch.no_grad():
        e = model.encode_batch(wav, wav_lens=torch.ones(1, device=EXTRACT_DEVICE),
                               normalize=False)
    e = l2_np(e.reshape(-1).detach().cpu().numpy())
    if e.shape != (192,):
        raise RuntimeError(f"Unexpected ECAPA embedding shape: {e.shape}")
    return e


def load_audio(path):
    """Decode, mono, 16 kHz; and whether it is non-empty and finite."""
    import soundfile as sf
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    wav = torch.as_tensor(x.T.copy())
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if sr != 16000:
        import torchaudio
        wav = torchaudio.functional.resample(wav, sr, 16000)
    wav = wav.squeeze(0).contiguous()
    return wav, bool(wav.numel() > 0 and torch.isfinite(wav).all())


def save_flac_16k(path, wav):
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), wav.numpy(), 16000, format="FLAC", subtype="PCM_16")


def pack_folder(folder):
    """Keep a finished audio folder as one uncompressed tar. Kaggle saves a
    session's output file by file, and the audio is never read again once
    it is embedded; the tar keeps it for audit."""
    folder = Path(folder)
    if not folder.is_dir():
        return
    tar_path = folder.parent / f"{folder.name}.tar"
    tmp = folder.parent / f"{folder.name}.tar.tmp"
    with tarfile.open(tmp, "w") as tf:
        tf.add(folder, arcname=folder.name)
    os.replace(tmp, tar_path)
    shutil.rmtree(folder)
    print(f"  packed {folder.name} into {tar_path.name}")


# ------------------------------------------------------------ stage 1: LFW
def prepare_lfw_raw():
    root = LFW_LOCAL_ROOT / "lfw"
    if (LFW_LOCAL_ROOT / ".extracted").is_file():
        return root
    archive = download("lfw", RAW / "lfw.tgz", sha256=REF["lfw_sha256"])
    LFW_LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(LFW_LOCAL_ROOT)
    if not root.exists():
        root = [p for p in LFW_LOCAL_ROOT.iterdir() if p.is_dir()][0]
    n_img = len(list(root.rglob("*.jpg")))
    exact("LFW raw images", n_img, REF["lfw_raw_images"])
    mark_stage("lfw_raw", {"archive_sha256": sha256_file(archive), "raw_images": n_img})
    (LFW_LOCAL_ROOT / ".extracted").write_text("ok")
    return root


def stage_face():
    """MTCNN validity and 512-D FaceNet embeddings (cell 7)."""
    if stage_done("lfw_embeddings") and LFW_EMB.exists() and LFW_VALIDITY.exists():
        print("RESUME: LFW embeddings present.")
        return
    from PIL import Image
    root = prepare_lfw_raw()
    mtcnn, resnet = load_face_models()
    identity_files = {}
    for subject_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(subject_dir.glob("*.jpg"))
        if len(files) >= 3:
            identity_files[subject_dir.name] = files
    rows, emb_subject, emb_relpath, embs = [], [], [], []
    for n, subject in enumerate(sorted(identity_files), 1):
        for img_path in identity_files[subject]:
            rec = {"subject_id": subject, "relative_path": str(img_path.relative_to(root)),
                   "sha256": sha256_file(img_path), "valid": False,
                   "mtcnn_prob": np.nan, "error": ""}
            try:
                face, prob = mtcnn(Image.open(img_path).convert("RGB"), return_prob=True)
                prob = float(prob) if prob is not None else float("nan")
                rec["mtcnn_prob"] = prob
                if face is None or not np.isfinite(prob) or prob < FACE_VALID_PROB:
                    rec["error"] = "mtcnn_validity_gate"
                    rows.append(rec)
                    continue
                with torch.no_grad():
                    e = resnet(face.unsqueeze(0).to(EXTRACT_DEVICE)).squeeze(0).cpu().numpy()
                e = l2_np(e)
                rec["valid"] = True
                rec["embedding_norm"] = float(np.linalg.norm(e))
                emb_subject.append(subject)
                emb_relpath.append(rec["relative_path"])
                embs.append(e)
            except Exception as exc:
                rec["error"] = repr(exc)
            rows.append(rec)
        if n % 100 == 0:
            print(f"    {n}/{len(identity_files)} identities, {len(embs):,} valid faces",
                  flush=True)
    validity = pd.DataFrame(rows).sort_values(["subject_id", "relative_path"])
    validity.to_csv(LFW_VALIDITY, sep="\t", index=False)
    np.savez_compressed(LFW_EMB, subject_id=np.array(emb_subject, dtype=object),
                        relative_path=np.array(emb_relpath, dtype=object),
                        embedding=np.stack(embs).astype(np.float32))
    counts = validity[validity["valid"] == True].groupby("subject_id").size()  # noqa: E712
    eligible = int((counts >= 3).sum())
    exact("LFW valid embeddings", len(embs), REF["lfw_valid"])
    exact("LFW identities with at least 3 valid images", eligible, REF["lfw_eligible"])
    exact("LFW embeddings file sha256", sha256_file(LFW_EMB), REF["lfw_embeddings_sha256"])
    mark_stage("lfw_embeddings", {"valid_embeddings": len(embs),
                                  "identities_with_at_least_3_valid": eligible,
                                  "validity_sha256": sha256_file(LFW_VALIDITY),
                                  "embeddings_sha256": sha256_file(LFW_EMB)})


# --------------------------------------------------- stage 2: CFP and split
def find_cfp_list():
    for root in (INPUT_ROOT, RAW):
        if Path(root).exists():
            hits = sorted(Path(root).glob("**/list_name.txt"))
            if hits:
                return hits[0]
    try:
        import kagglehub
        hits = sorted(Path(kagglehub.dataset_download(CFP_KAGGLE)).glob("**/list_name.txt"))
        if hits:
            return hits[0]
    except Exception as exc:
        print(f"  kagglehub could not fetch {CFP_KAGGLE}: {exc}")
    raise FileNotFoundError(f"CFP name list not found. Use 'Add Input' and add the Kaggle "
                            f"dataset {CFP_KAGGLE}, which is the source the study used.")


def cfp_subject_names():
    """The sealed CFP metadata: the release's 500 names in order, with the
    rule case_sensitive_space_to_underscore_v1."""
    source = find_cfp_list()
    exact("CFP list_name.txt sha256", sha256_file(source), REF["cfp_source_sha256"])
    names = [line.strip() for line in source.read_text(errors="replace").splitlines()
             if line.strip()]
    table = pd.DataFrame({"cfp_subject_id": [f"{i:03d}" for i in range(1, len(names) + 1)],
                          "subject_name": [n.replace(" ", "_") for n in names]})
    CFP_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(CFP_METADATA, sep="\t", index=False)
    exact("CFP metadata table sha256", sha256_file(CFP_METADATA), REF["cfp_metadata_sha256"])
    return sorted(set(table["subject_name"]))


def lfw_embedding_records():
    z = np.load(LFW_EMB, allow_pickle=True)
    return pd.DataFrame({"subject_id": z["subject_id"].astype(str),
                         "relative_path": z["relative_path"].astype(str),
                         "embedding_index": np.arange(len(z["embedding"]), dtype=np.int64)})


def stage_face_split():
    """Exact CFP overlap removal, the 50/42/58 split and the trials (cells 9-10)."""
    if stage_done("lfw_face_trials") and LFW_FACE_TRIALS.exists():
        print("RESUME: face split and trials present.")
        return
    n_bg, n_dev = SPLIT["background"], SPLIT["development"]
    cfp_set = set(cfp_subject_names())
    rec = lfw_embedding_records()
    counts = rec.groupby("subject_id").size()
    eligible = sorted(counts[counts >= 3].index.astype(str))
    excluded = sorted(u for u in eligible if u in cfp_set)
    remaining = [u for u in eligible if u not in cfp_set]
    ranked = sorted(remaining, key=lambda u: (H(S0, "LFW-SPLIT", str(u)), u))
    if len(ranked) < sum(SPLIT.values()):
        raise RuntimeError(f"only {len(ranked)} eligible LFW identities remain")
    rows = []
    for idx, u in enumerate(ranked[:sum(SPLIT.values())]):
        part = ("background" if idx < n_bg else
                "development" if idx < n_bg + n_dev else "evaluation")
        rows.append({"subject_id": u, "split_rank_hash": H(S0, "LFW-SPLIT", str(u)),
                     "partition": part})
    pd.DataFrame(rows).to_csv(LFW_SPLIT, sep="\t", index=False)
    LFW_EXCLUDED.write_text("\n".join(excluded) + ("\n" if excluded else ""))
    exact("LFW identities excluded by the CFP overlap", len(excluded), REF["cfp_overlap"])
    exact("LFW excluded list sha256", sha256_file(LFW_EXCLUDED), REF["lfw_excluded_sha256"])
    exact("LFW 50/42/58 split sha256", sha256_file(LFW_SPLIT), REF["lfw_split_sha256"])
    atomic_json(DIR["seal"] / "lfw_split.json", {
        "eligible_before_overlap_removal": len(eligible),
        "excluded_exact_overlap_count": len(excluded),
        "split_sha256": sha256_file(LFW_SPLIT),
        "excluded_sha256": sha256_file(LFW_EXCLUDED)})
    mark_stage("lfw_split")

    trials = []
    for s in pd.read_csv(LFW_SPLIT, sep="\t").itertuples(index=False):
        g = rec[rec["subject_id"] == s.subject_id].sort_values("relative_path") \
            .reset_index(drop=True)
        if s.partition == "background":
            for rank, role in enumerate(["attack", "enroll", "probe"]):
                r = g.iloc[rank]
                trials.append({"subject_id": s.subject_id, "partition": s.partition,
                               "role": role, "rank": rank,
                               "relative_path": r.relative_path,
                               "embedding_index": int(r.embedding_index)})
        else:
            for rank in range(len(g)):
                r = g.iloc[rank]
                trials.append({"subject_id": s.subject_id, "partition": s.partition,
                               "role": "enroll" if rank == 0 else "probe", "rank": rank,
                               "relative_path": r.relative_path,
                               "embedding_index": int(r.embedding_index)})
    pd.DataFrame(trials).sort_values(["partition", "subject_id", "role", "rank"]) \
        .to_csv(LFW_FACE_TRIALS, sep="\t", index=False)
    mark_stage("lfw_face_trials", {"manifest_sha256": sha256_file(LFW_FACE_TRIALS),
                                   "rows": len(trials)})


# ------------------------------------------------------ stage 3: LibriSpeech
def stage_voice():
    """Speaker selection, 15 valid utterances each, ECAPA (cells 11-13)."""
    if stage_done("libri_embeddings") and LIBRI_EMB.exists():
        print("RESUME: LibriSpeech embeddings present.")
        return
    n_bg, n_dev, n_total = SPLIT["background"], SPLIT["development"], sum(SPLIT.values())
    if not (stage_done("libri_internal") and LIBRI_MANIFEST.exists()):
        archive = download("libri", RAW / "train-clean-100.tar.gz", md5=REF["libri_md5"])
        LIBRI_LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(LIBRI_LOCAL_ROOT)
        root = next(LIBRI_LOCAL_ROOT.rglob("train-clean-100"))
        mark_stage("libri_local", {"archive_md5": md5_file(archive)})
        candidates = []
        for spk in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
            files = sorted(spk.rglob("*.flac"), key=lambda p: p.relative_to(root).as_posix())
            if len(files) >= 15:
                candidates.append((spk.name, files))
        candidates.sort(key=lambda it: (H(S0, "LIBRISPEECH-SPLIT", str(it[0])), it[0]))
        rows, selected = [], []
        for speaker_id, files in candidates:
            valid_items = []
            for src in files:
                try:
                    wav, valid = load_audio(src)
                    if valid:
                        valid_items.append((src, wav))
                    if len(valid_items) == 15:
                        break
                except Exception:
                    continue
            if len(valid_items) < 15:
                continue
            index = len(selected)
            if index >= n_total:
                break
            partition = ("background" if index < n_bg else
                         "development" if index < n_bg + n_dev else "evaluation")
            selected.append(speaker_id)
            for rank, (src, wav) in enumerate(valid_items):
                dest = LIBRI_SELECTED_ROOT / speaker_id / f"{rank:02d}_{src.stem}.flac"
                if not dest.exists():
                    save_flac_16k(dest, wav)
                if partition == "background":
                    role = ["attack", "enroll", "probe"][rank] if rank < 3 else "reserve"
                else:
                    role = "enroll_member" if rank < 5 else "probe"
                rows.append({"speaker_id": speaker_id,
                             "split_rank_hash": H(S0, "LIBRISPEECH-SPLIT", str(speaker_id)),
                             "partition": partition, "rank": rank, "role": role,
                             "source_relative_path": src.relative_to(root).as_posix(),
                             "stored_relative_path": dest.relative_to(PROJECT).as_posix(),
                             "n_samples_16k": int(wav.numel()), "sha256": sha256_file(dest)})
        if len(selected) != n_total:
            raise RuntimeError(f"only {len(selected)} LibriSpeech speakers qualify")
        pd.DataFrame(rows).sort_values(["partition", "speaker_id", "rank"]) \
            .to_csv(LIBRI_MANIFEST, sep="\t", index=False)
        exact("LibriSpeech manifest sha256", sha256_file(LIBRI_MANIFEST),
              REF["libri_manifest_sha256"])
        mark_stage("libri_internal", {"selected_speakers": len(selected),
                                      "manifest_sha256": sha256_file(LIBRI_MANIFEST)})
        shutil.rmtree(LIBRI_LOCAL_ROOT, ignore_errors=True)
        archive.unlink(missing_ok=True)

    model = load_ecapa()
    manifest = pd.read_csv(LIBRI_MANIFEST, sep="\t", dtype={"speaker_id": str})
    ids, ranks, paths, embs = [], [], [], []
    for n, r in enumerate(manifest.itertuples(index=False), 1):
        wav, valid = load_audio(PROJECT / r.stored_relative_path)
        if not valid:
            raise RuntimeError(f"Persisted invalid waveform: {r.stored_relative_path}")
        embs.append(ecapa_embed_waveform(model, wav.numpy()))
        ids.append(str(r.speaker_id))
        ranks.append(int(r.rank))
        paths.append(str(r.stored_relative_path))
        if n % 250 == 0:
            print(f"    {n:,}/{len(manifest):,} utterances embedded", flush=True)
    np.savez_compressed(LIBRI_EMB, speaker_id=np.array(ids, dtype=object),
                        rank=np.array(ranks, dtype=np.int64),
                        relative_path=np.array(paths, dtype=object),
                        embedding=np.stack(embs).astype(np.float32))
    exact("LibriSpeech embeddings", len(embs), REF["libri_embeddings"])
    exact("LibriSpeech embeddings file sha256", sha256_file(LIBRI_EMB),
          REF["libri_embeddings_sha256"])
    mark_stage("libri_embeddings", {"embeddings": len(embs), "sha256": sha256_file(LIBRI_EMB)})
    pack_folder(LIBRI_SELECTED_ROOT)


# ------------------------------------------------------- stage 4: tensors
def stage_tensors():
    """The frozen IoM tensors, seeded H(2026, 'IOM', modality, overlap) (cell 15)."""
    for modality, d in DIMENSION.items():
        for o in CONFIG["overlaps"]:
            k = 1 + math.ceil((d - G) / (G - o))
            path = RUNS_IN / "iom_tensors" / f"{modality}_o{o}_k{k}.pt"
            if path.is_file():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            gen = torch.Generator(device="cpu")
            gen.manual_seed(H(S0, "IOM", modality, o))
            torch.save(torch.randn((256, 32, k), generator=gen, dtype=torch.float32), path)
    print("  frozen IoM tensors present for both modalities and every overlap")


# ------------------------------------------------------ stage 5: Stage A
def generate_candidate(modality, candidate_id):
    gen = torch.Generator(device="cpu")
    gen.manual_seed(H(S0, "POLY", modality, candidate_id))
    perm = torch.randperm(len(NONZERO_COEFFS), generator=gen)[:G].numpy()
    Cc = NONZERO_COEFFS[perm].astype(np.float32)
    Ee = (torch.randperm(G, generator=gen) + 1).numpy().astype(np.int64)
    return Cc, Ee


def poly_transform_candidates(x, Cs, Es, o):
    """P(x) for a batch of candidate keys; vals is [B, N, k, G] or
    [B, N, R, k, G]. The study's notebook shaped the keys as [B, 1, G], which
    lines B up against N and fails unless the batch has one candidate (its
    sealed search ran on 7 Sep with earlier, sharded code). Here the keys are
    [B, 1, ..., 1, G], so candidate b uses its own key, as intended. Each
    candidate's attack is independent of the others in the batch."""
    if x.ndim == 2:
        x = x.unsqueeze(0).expand(Cs.shape[0], -1, -1)
    idx, mask = poly_indices(x.shape[-1], o, x.device)
    vals = x[..., idx]
    coeff_shape = [Cs.shape[0]] + [1] * (vals.ndim - 2) + [G]
    coeff = Cs.to(x.device, x.dtype).view(*coeff_shape)
    exp = Es.to(x.device, torch.int64).view(*coeff_shape)
    vals = vals * mask.to(vals.dtype).view(*([1] * (vals.ndim - 2) + list(mask.shape)))
    return (torch.pow(vals, exp) * coeff).sum(dim=-1)


def iom_hash(P, R, M, q):
    scores = torch.einsum("...k,mqk->...mq", P, R[:M, :q, :].to(P.device, P.dtype))
    return torch.argmax(scores, dim=-1).to(torch.int16)


def integer_threshold(impostor_counts, M, alpha=TARGET_FMR):
    imp = np.asarray(impostor_counts, dtype=np.int64)
    for c in range(0, M + 2):
        if np.mean(imp >= c) <= alpha:
            return int(c)
    raise AssertionError("Threshold sentinel logic failed.")


def background_tensors(modality):
    """Attack, enrolment and probe embeddings of the background people (cell 20)."""
    if modality == "face":
        trials = pd.read_csv(LFW_FACE_TRIALS, sep="\t")
        E = np.load(LFW_EMB, allow_pickle=True)["embedding"].astype(np.float32)
        bg = trials[trials["partition"] == "background"]
        ids, A, B, C = [], [], [], []
        for uid, g in bg.groupby("subject_id"):
            byrole = {r.role: r for r in g.itertuples(index=False)}
            ids.append(str(uid))
            A.append(E[int(byrole["attack"].embedding_index)])
            B.append(E[int(byrole["enroll"].embedding_index)])
            C.append(E[int(byrole["probe"].embedding_index)])
    else:
        manifest = pd.read_csv(LIBRI_MANIFEST, sep="\t", dtype={"speaker_id": str})
        z = np.load(LIBRI_EMB, allow_pickle=True)
        E = z["embedding"].astype(np.float32)
        table = pd.DataFrame({"speaker_id": z["speaker_id"].astype(str),
                              "rank": z["rank"].astype(int),
                              "embedding_index": np.arange(len(E))})
        merged = manifest.merge(table, on=["speaker_id", "rank"], how="inner")
        bg = merged[merged["partition"] == "background"]
        ids, A, B, C = [], [], [], []
        for uid, g in bg.groupby("speaker_id"):
            byrank = {int(r.rank): r for r in g.itertuples(index=False)}
            ids.append(str(uid))
            A.append(E[int(byrank[0].embedding_index)])
            B.append(E[int(byrank[1].embedding_index)])
            C.append(E[int(byrank[2].embedding_index)])
    t = lambda xs: torch.tensor(np.stack(xs), dtype=torch.float32)
    return ids, t(A), t(B), t(C)


def attack_initial_batch(modality, candidate_ids, subject_ids, d):
    out = []
    for cid in candidate_ids:
        per_subject = []
        for uid in subject_ids:
            restarts = []
            for restart in range(ATTACK_RESTARTS):
                gen = torch.Generator(device="cpu")
                gen.manual_seed(H(S0, "ATTACK", modality, int(cid), uid, restart))
                v = torch.randn((d,), generator=gen, dtype=torch.float32) * ATTACK_INIT_STD
                restarts.append(v / torch.linalg.vector_norm(v))
            per_subject.append(torch.stack(restarts))
        out.append(torch.stack(per_subject))
    return torch.stack(out)


def evaluate_candidate_batch(modality, candidate_ids, background):
    """The study's white-box candidate evaluation (cell 18), unchanged."""
    dev = ATTACK_DEVICE
    subject_ids, A_cpu, B_cpu, C_cpu = background
    A, B, Cprobe = A_cpu.to(dev), B_cpu.to(dev), C_cpu.to(dev)
    d = A.shape[-1]
    generated = [generate_candidate(modality, int(c)) for c in candidate_ids]
    Cs = torch.tensor(np.stack([x[0] for x in generated]), dtype=torch.float32, device=dev)
    Es = torch.tensor(np.stack([x[1] for x in generated]), dtype=torch.int64, device=dev)
    with torch.no_grad():
        targetP = poly_transform_candidates(A, Cs, Es, O_REF)
    xprime = torch.nn.Parameter(attack_initial_batch(modality, candidate_ids,
                                                     subject_ids, d).to(dev))
    opt = torch.optim.Adam([xprime], lr=ATTACK_LR, betas=ATTACK_BETAS, eps=ATTACK_EPS,
                           weight_decay=0.0, amsgrad=False)
    for _ in range(ATTACK_ITERS):
        opt.zero_grad(set_to_none=True)
        diff = poly_transform_candidates(xprime, Cs, Es, O_REF) - targetP.unsqueeze(2)
        (diff * diff).sum(dim=-1).sum().backward()
        opt.step()
        with torch.no_grad():
            xprime.data /= torch.linalg.vector_norm(xprime.data, dim=-1,
                                                    keepdim=True).clamp_min(1e-12)
    with torch.no_grad():
        rho = (xprime * A.unsqueeze(0).unsqueeze(2)).sum(dim=-1)
        rho_max = rho.max(dim=-1).values.max(dim=-1).values.cpu().numpy()
        PB = poly_transform_candidates(B, Cs, Es, O_REF)
        PC = poly_transform_candidates(Cprobe, Cs, Es, O_REF)
        R = load_iom_tensor(modality, O_REF, d).to(dev)
        zB, zC = iom_hash(PB, R, M_REF, Q_REF), iom_hash(PC, R, M_REF, Q_REF)
        results, N = [], zB.shape[1]
        for bi, cid in enumerate(candidate_ids):
            cc = (zB[bi, :, None, :] == zC[bi, None, :, :]).sum(dim=-1).cpu().numpy()
            genuine, impostor = np.diag(cc), cc[~np.eye(N, dtype=bool)]
            tau_bg = integer_threshold(impostor, M_REF, TARGET_FMR)
            Cc, Ee = generated[bi]
            results.append({"candidate_id": int(cid), "C": Cc.astype(int).tolist(),
                            "E": Ee.astype(int).tolist(), "rho_max": float(rho_max[bi]),
                            "TAR_background": float(np.mean(genuine >= tau_bg)),
                            "FMR_background": float(np.mean(impostor >= tau_bg)),
                            "c_tau_BG": int(tau_bg)})
    del xprime, opt
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return results


def stage_a(modality):
    """The resumable 10k -> 20k key search (cell 19). Returns True when the
    key is selected, False when this session ran out of time."""
    out_dir = RUNS_IN / "key_search" / modality
    selected = out_dir / "selected_key.json"
    if selected.exists():
        print(f"  {modality}: key already selected")
        return True
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "candidates.jsonl"
    existing = {}
    if log.exists():
        for line in log.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing[int(r["candidate_id"])] = r
    background = background_tensors(modality)
    if len(background[0]) != SPLIT["background"]:
        raise RuntimeError(f"{modality}: {len(background[0])} background identities")

    def run(first, last, stage):
        pending = [c for c in range(first, last + 1) if c not in existing]
        started = time.time()
        for start in range(0, len(pending), KEYSEARCH_CANDIDATE_BATCH):
            if time_left_h() < 0.3:
                print(f"  {modality}: session time nearly used; {len(existing):,} "
                      f"candidates saved. Save this version and run it again.")
                return False
            batch = pending[start:start + KEYSEARCH_CANDIDATE_BATCH]
            rows = evaluate_candidate_batch(modality, batch, background)
            with open(log, "a") as f:
                for r in rows:
                    r["stage_generated"] = stage
                    f.write(json.dumps(r, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
            existing.update({r["candidate_id"]: r for r in rows})
            done = start + len(batch)
            rate = done / max(time.time() - started, 1e-9)
            print(f"    {modality} stage {stage}: {len(existing):,} candidates "
                  f"({rate * 60:.0f}/min, about "
                  f"{(len(pending) - done) / max(rate, 1e-9) / 3600:.1f} h left)", flush=True)
        return True

    def passing(rows, rho_max, tar_min):
        return [r for r in rows if r["rho_max"] <= rho_max and r["TAR_background"] >= tar_min]

    def rank(rows):
        return min(rows, key=lambda r: (r["rho_max"], -r["TAR_background"], r["candidate_id"]))

    torch.use_deterministic_algorithms(True, warn_only=False)    # as the study
    try:
        if not run(1, N_INIT, 1):
            return False
        p1 = passing([existing[c] for c in range(1, N_INIT + 1)],
                     STAGE1_RHO_MAX, STAGE1_TAR_MIN)
        if p1:
            winner = dict(rank(p1), selected_stage=1)
        else:
            if not run(N_INIT + 1, N_MAX, 2):
                return False
            p2 = passing([existing[c] for c in range(1, N_MAX + 1)],
                         STAGE2_RHO_MAX, STAGE2_TAR_MIN)
            if not p2:
                atomic_json(out_dir / "FAILED.json", {"modality": modality, "status": "FAIL"})
                raise RuntimeError(f"{modality}: no candidate passed the Stage-2 gates")
            winner = dict(rank(p2), selected_stage=2)
        atomic_json(selected, winner)
    finally:
        torch.use_deterministic_algorithms(True, warn_only=True)
    print(f"  {modality}: candidate {winner['candidate_id']} selected "
          f"(rho_max {winner['rho_max']:.4f}, TAR {winner['TAR_background']:.4f})")
    if modality == "voice" and REF["voice_key_sha256"]:
        exact("voice selected_key.json sha256", sha256_file(selected), REF["voice_key_sha256"])
    return True


# ------------------------------------------------------- stage 6: Stage B
def stage_b(modality):
    """The 80-setting development sweep, then the sealed selection rule."""
    seal_path = DIR["seal"] / f"operating_point_{modality}.json"
    if seal_path.is_file():
        print(f"  {modality}: operating point already sealed")
        return json.loads(seal_path.read_text())
    sweep_path = RUNS_IN / "sweep" / modality / "sweep_80.csv"
    if not sweep_path.is_file():
        subjects, enroll, probes = partition_data(modality, "development")
        d = len(enroll[subjects[0]])
        rows = []
        for o in GRID["o"]:
            frozen = load_iom_tensor(modality, o, d)
            for M in GRID["M"]:
                for q in GRID["q"]:
                    H_ = identity_histograms(modality, subjects, enroll, probes,
                                             M, q, o, None, frozen=frozen)
                    rows.append(sweep_row(modality, H_))
            print(f"    {modality} o={o}: {len(rows)} settings", flush=True)
        sweep_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).sort_values(["o", "M", "q"]).to_csv(sweep_path, index=False)
    rows = pd.read_csv(sweep_path).to_dict("records")
    sealed = {(r["M"], r["q"], r["o"]): r for r in PAPER["sweeps"][modality]}
    fields = ("EER", "c_EER", "c_tau_DEV", "TAR_DEV", "FMR_DEV", "Dsys_DEV")
    same = sum(1 for r in rows if (r["M"], r["q"], r["o"]) in sealed
               and all(abs(float(r[f]) - float(sealed[(r["M"], r["q"], r["o"])][f])) <= 1e-9
                       for f in fields))
    exact(f"{modality} sweep rows equal to the sealed sweep", same, len(sealed))

    def eligible(rule):
        return [r for r in rows if r["EER"] <= rule["eer_max"] and r["TAR_DEV"] >= rule["tar_min"]]

    rule = dict(SELECTION_RULE_VOICE, rule_id="min_dsys_subject_to_eer_floor_v1")
    ok = eligible(rule)
    if not ok and modality == "face":
        rule = dict(FACE_FLOOR, rule_id="min_dsys_subject_to_eer_floor_v1_face",
                    deviation_reason="face cannot meet the voice floor; the study's "
                                     "registered face floor is applied")
        ok = eligible(rule)
    if not ok:
        raise RuntimeError(f"{modality}: no setting meets the floor {rule}")
    best = min(ok, key=lambda r: (r["Dsys_DEV"], r["EER"], r["M"], r["q"], r["o"]))
    chosen = {"modality": modality, "rule": rule, "M": int(best["M"]),
              "q": int(best["q"]), "o": int(best["o"]),
              "development": {"EER": float(best["EER"]), "TAR_DEV": float(best["TAR_DEV"]),
                              "Dsys_DEV": float(best["Dsys_DEV"]),
                              "c_tau_DEV": int(best["c_tau_DEV"])},
              "n_eligible": len(ok), "sweep_sha256": sha256_file(sweep_path)}
    atomic_json(seal_path, chosen)
    paper = PAPER["heldout"][modality]
    exact(f"{modality} sealed operating point (M, q, o, tau)",
          [chosen["M"], chosen["q"], chosen["o"], chosen["development"]["c_tau_DEV"]],
          [paper["M"], paper["q"], paper["o"], paper["c_tau_carried_from_DEV"]])
    return chosen


# --------------------------------------------------- stage 7: evaluation
def evaluate_partition(modality, subjects, enroll, probes, chosen, tag):
    M, q, o = chosen["M"], chosen["q"], chosen["o"]
    tau = chosen["development"]["c_tau_DEV"]
    H_ = identity_histograms(modality, subjects, enroll, probes, M, q, o, tau)
    gen, imp, _, _ = _apply_weights(H_, np.ones(H_["n"]))
    point = _metrics(H_, np.ones(H_["n"]))
    eer, c_eer = eer_from_histograms(gen, imp)      # the ablation checks against this
    return {"modality": modality, "M": M, "q": q, "o": o, "protocol": PROTOCOL_VERSION,
            "c_tau_carried_from_DEV": tau, "n_subjects": H_["n"],
            "n_genuine": int(gen.sum()), "n_impostor": int(imp.sum()),
            f"EER_{tag}": eer, f"c_EER_{tag}": int(c_eer),
            f"TAR_{tag}_at_dev_threshold": point["TAR"],
            f"FMR_{tag}_at_dev_threshold": point["FMR"],
            f"FNMR_{tag}_at_dev_threshold": 1.0 - point["TAR"],
            f"Dsys_{tag}": point["Dsys"],
            "development_reference": {**chosen["development"]},
            "selection_rule_id": chosen["rule"]["rule_id"]}


def _exact_metrics(label, result, paper, tag):
    for key in (f"EER_{tag}", f"TAR_{tag}_at_dev_threshold",
                f"FMR_{tag}_at_dev_threshold", f"Dsys_{tag}"):
        exact(f"{label} {key}", round(result[key], 12), round(paper[key], 12), tol=1e-9)


def stage_heldout(modality):
    path = HELDOUT_RESULTS[modality]
    if path.is_file():
        print(f"  {modality}: held-out result already written")
        return
    chosen = json.loads((DIR["seal"] / f"operating_point_{modality}.json").read_text())
    data = face_heldout_data() if modality == "face" else voice_heldout_data()
    result = dict(evaluate_partition(modality, *data, chosen, "HOLDOUT"), partition="evaluation")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, result)
    _exact_metrics(f"{modality} held-out", result, PAPER["heldout"][modality], "HOLDOUT")


def extract_vctk_embeddings():
    if verified_stage("vctk_embeddings", [(VCTK_EMB, "sha256")]):
        return
    manifest = pd.read_csv(VCTK_MANIFEST, sep="\t", dtype={"speaker_id": str}) \
        .sort_values(["speaker_id", "rank"]).reset_index(drop=True)
    model = load_ecapa()
    embs = []
    for r in manifest.itertuples(index=False):
        wav, _ = load_audio(DIR["audio_vctk"] / r.relative_path)
        embs.append(ecapa_embed_waveform(model, wav.numpy()))
    np.savez(VCTK_EMB, embedding=np.stack(embs).astype(np.float32),
             speaker_id=manifest.speaker_id.to_numpy().astype(str),
             rank=manifest["rank"].to_numpy(),
             embedding_index=np.arange(len(embs)))
    exact("VCTK embeddings file sha256", sha256_file(VCTK_EMB), REF["vctk_embeddings_sha256"])
    mark_stage("vctk_embeddings", {"n": len(embs), "sha256": sha256_file(VCTK_EMB),
                                   "manifest_sha256": sha256_file(VCTK_MANIFEST)})


def stage_external():
    """VCTK, read only after both internal evaluations are written."""
    path = RUNS_IN / "external" / "voice" / "external_result.json"
    if path.is_file():
        print("  voice: external result already written")
        return
    if not all(HELDOUT_RESULTS[m].is_file() for m in ("voice", "face")):
        raise RuntimeError("the internal evaluation must finish before VCTK is read")
    if not stage_done("vctk_manifest"):
        download("vctk", VCTK_ARCHIVE, md5=REF["vctk_md5"])
    manifest = prepare_vctk()
    exact("VCTK speakers kept", int(manifest.speaker_id.nunique()), REF["vctk_speakers"])
    exact("VCTK utterances kept", int(len(manifest)), REF["vctk_utterances"])
    exact("VCTK manifest sha256", sha256_file(VCTK_MANIFEST), REF["vctk_manifest_sha256"])
    extract_vctk_embeddings()
    VCTK_ARCHIVE.unlink(missing_ok=True)
    pack_folder(DIR["audio_vctk"])
    chosen = json.loads((DIR["seal"] / "operating_point_voice.json").read_text())
    result = dict(evaluate_partition("voice", *vctk_external_data(), chosen, "EXT"),
                  corpus="VCTK-Corpus-0.92")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, result)
    _exact_metrics("voice external", result, PAPER["external"], "EXT")


# ----------------------------------------- stage 9: against the paper
def _ci_row(label, paper_point, fresh, scale=100.0, unit="%"):
    p, lo, hi = fresh
    return {"quantity": label, "paper": round(paper_point * scale, 4),
            "fresh": round(p * scale, 4),
            "fresh_95ci": [round(lo * scale, 4), round(hi * scale, 4)], "unit": unit,
            "verdict": ("paper inside fresh interval" if lo <= paper_point <= hi
                        else "paper OUTSIDE fresh interval")}


def compare_with_paper(intervals, ablation, inversion, revocation):
    rows, claims = [], []
    names = {"EER": "EER_{}", "TAR": "TAR_{}_at_dev_threshold",
             "FMR": "FMR_{}_at_dev_threshold", "Dsys": "Dsys_{}"}
    for part, paper_res in (("voice/evaluation", PAPER["heldout"]["voice"]),
                            ("face/evaluation", PAPER["heldout"]["face"]),
                            ("voice/external", PAPER["external"])):
        if part not in intervals["partitions"]:
            continue
        tag = "HOLDOUT" if part.endswith("evaluation") else "EXT"
        for k, name in names.items():
            m = intervals["partitions"][part]["metrics"][k]
            scale, unit = (1.0, "") if k == "Dsys" else (100.0, "%")
            rows.append(_ci_row(f"{part} {k}", paper_res[name.format(tag)],
                                (m["estimate"], m["lower"], m["upper"]), scale, unit))
    for mod in ("voice", "face"):
        for arm in ARMS:
            a = ablation["modalities"][mod]["arms"][arm]
            pa = PAPER["ablation"]["modalities"][mod]["arms"][arm]
            r = revocation["modalities"][mod]["arms"][arm]
            pr = PAPER["revocation"]["modalities"][mod]["arms"][arm]
            rows += [_ci_row(f"ablation {mod} {arm} EER", pa["EER"], (a["EER"], *a["EER_CI"])),
                     _ci_row(f"ablation {mod} {arm} Dsys", pa["Dsys"],
                             (a["Dsys"], *a["Dsys_CI"]), 1.0, ""),
                     _ci_row(f"revocation {mod} {arm} PRAR", pr["PRAR"],
                             (r["PRAR"], *r["PRAR_CI"])),
                     _ci_row(f"inversion {mod} {arm} cosine", pr["cos_to_true"],
                             (r["cos_to_true"], *r["cos_CI"]), 1.0, "")]
        rv, iv = revocation["modalities"][mod]["arms"], inversion["modalities"][mod]["arms"]
        lo, hi = ablation["modalities"][mod]["contrasts_vs_polyiom"]["randproj_iom"]["delta_EER_CI"]
        claims += [
            (f"{mod}: hashing alone never revokes (PRAR 100%)", rv["iom_only"]["PRAR"] == 1.0),
            (f"{mod}: keyed compression revokes for the median key",
             rv["polyiom"]["per_key_median"] < 0.5 and rv["randproj_iom"]["per_key_median"] < 0.5),
            (f"{mod}: cosine polynomial < linear map < hashing alone",
             iv["polyiom"]["cos_to_true"] < iv["randproj_iom"]["cos_to_true"]
             < iv["iom_only"]["cos_to_true"]),
            (f"{mod}: the attack reaches the threshold in every arm (SAR 100%)",
             all(iv[a]["SAR"] == 1.0 for a in ARMS)),
            (f"{mod}: the polynomial costs EER against the linear map (firm)", hi < 0)]
    return rows, claims


def write_report(rows, claims):
    exact_rows = json.loads((DIR["seal"] / "exact_checks.json").read_text()) \
        if (DIR["seal"] / "exact_checks.json").is_file() else []
    n_same = sum(r["verdict"] == "identical" for r in exact_rows)
    lines = ["# AttackAware PolyIoM v1.1.4 - fresh run on Kaggle", "",
             "## 1. Stage by stage: does the fresh run give the study's output?", "",
             f"{n_same} of {len(exact_rows)} checks are identical.", "",
             "| Check | Fresh | Study | Verdict |", "|---|---|---|---|"]
    lines += [f"| {r['check']} | {r['fresh']} | {r['study']} | {r['verdict']} |"
              for r in exact_rows]
    inside = sum(r["verdict"].startswith("paper inside") for r in rows)
    lines += ["", "## 2. Results against the paper", "",
              f"{inside} of {len(rows)} paper values lie inside the fresh 95% interval.", "",
              "| Quantity | Paper | Fresh | Fresh 95% interval | Verdict |",
              "|---|---|---|---|---|"]
    lines += [f"| {r['quantity']} | {r['paper']}{r['unit']} | {r['fresh']}{r['unit']} | "
              f"[{r['fresh_95ci'][0]}, {r['fresh_95ci'][1]}] | {r['verdict']} |" for r in rows]
    lines += ["", "## 3. The paper's findings", "", "| Finding | Holds in the fresh run |",
              "|---|---|"] + [f"| {c} | {'yes' if ok else 'NO'} |" for c, ok in claims]
    text = "\n".join(lines) + "\n"
    (PROJECT / "REPLICATION_REPORT.md").write_text(text)
    atomic_json(PROJECT / "replication_report.json",
                {"exact": exact_rows, "results": rows,
                 "findings": [{"finding": c, "holds": bool(ok)} for c, ok in claims]})
    print(text)
    return text


# ---------------------------------------------------------------- status
def status():
    names = [("environment", DIR["seal"] / "environment.json"),
             ("face embeddings", stage_file("lfw_embeddings")),
             ("face split and trials", stage_file("lfw_face_trials")),
             ("voice embeddings", stage_file("libri_embeddings")),
             ("Stage A voice key", RUNS_IN / "key_search/voice/selected_key.json"),
             ("Stage A face key", RUNS_IN / "key_search/face/selected_key.json"),
             ("Stage B voice", DIR["seal"] / "operating_point_voice.json"),
             ("Stage B face", DIR["seal"] / "operating_point_face.json"),
             ("held-out", HELDOUT_RESULTS["face"]),
             ("external", RUNS_IN / "external/voice/external_result.json"),
             ("revocation", RUNS_IN / "revocation/revocation_result.json"),
             ("report", PROJECT / "REPLICATION_REPORT.md")]
    for label, path in names:
        print(f"  {'done' if Path(path).is_file() else '....'}  {label}")


print("Fresh pipeline ready.")

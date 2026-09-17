"""
VCTK external corpus preparation - works from the archive already in Drive.

VCTK-Corpus-0.92.zip (11,747,302,977 bytes) finished downloading on Sep 17
into datasets/VCTK-Corpus-0.92/. Nothing else has happened to it: the
folder holds only the zip, so there is no manifest and no 16 kHz audio for
extract_vctk_embeddings() to read. vctk_download_retry.py has done its job
and is no longer needed.

Load after the v1.1.4 notebook cells and external_eval_cells.py:

    exec(open("/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4/"
              "vctk_prepare_cells.py").read())
    prepare_vctk()

Then the existing external path runs unchanged:

    ensure_runtime_deps()        # ECAPA needs speechbrain present
    evaluate_external("voice")

WHAT IT DOES, AND WHY THIS WAY
------------------------------
* Streams the members it needs straight out of the zip. Extracting the
  whole archive would write 11.7 GB to a Colab disk that does not reliably
  have it, to use a few hundred MB of it. Only the utterances that end up
  in the manifest are ever decoded or written.
* mic1 only, as config_v1_1_4.json records
  ("vctk_validity": "mic1_post_resample_samples>=24000"). mic2 is a
  different microphone and p280's mic2 is missing from the release.
* Resamples 48 kHz -> 16 kHz with an exact 1/3 polyphase decimation
  (scipy.signal.resample_poly), which is anti-aliased and deterministic,
  then applies the >= 24000 sample gate AFTER resampling, in that order,
  because that is what the sealed validity rule says.
* Takes the first 15 valid utterances per speaker in sorted filename
  order, and drops any speaker that cannot supply 15. Fifteen is what the
  voice protocol requires: vctk_external_data() skips any speaker without
  exactly 15, enrolling ranks 0-4 and probing with ranks 5-14. Sorted
  order rather than a random sample keeps this reproducible without
  spending a seed, and VCTK filename order is not correlated with
  anything the evaluation measures.
* Resumable and idempotent: a verified stage returns immediately, and an
  already-written wav of the right length is not decoded again.

VCTK is external. It is read only after the internal method is frozen, and
it is never used for key selection, thresholds, or configuration choice.
"""

import io
import json
import os
import re
import zipfile
from fractions import Fraction

import numpy as np
import pandas as pd

VCTK_TARGET_SR = 16000
VCTK_MIN_SAMPLES = 24000          # sealed validity gate, post-resample
VCTK_UTTS_PER_SPEAKER = 15        # ranks 0-4 enroll, 5-14 probe
VCTK_ZIP_BYTES = 11747302977      # the copy in Drive, as downloaded Sep 17

_MIC1 = re.compile(r"(?:^|/)(p\d{3}|s5)_(\d+)_mic1\.flac$")

# Cell 17 defines these when it runs the download itself. It has not, so
# fall back to the conventional locations and register them, because
# extract_vctk_embeddings() reads both.
if "VCTK_MANIFEST" not in globals():
    VCTK_MANIFEST = DIR["protocol"] / "vctk_manifest.tsv"
if "audio_vctk" not in DIR:
    DIR["audio_vctk"] = DIR["preprocessed"] / "vctk_16k"


def locate_vctk_archive():
    """Find the downloaded archive. Returns a Path."""
    candidates = []
    if "VCTK_ARCHIVE" in globals():
        candidates.append(VCTK_ARCHIVE)
    candidates.append(
        DIR["datasets"] / "VCTK-Corpus-0.92" / "VCTK-Corpus-0.92.zip"
    )
    candidates.extend(sorted(DIR["datasets"].glob("**/VCTK-Corpus-0.92.zip")))

    for path in candidates:
        if path and path.exists() and path.stat().st_size > 0:
            size = path.stat().st_size
            if size != VCTK_ZIP_BYTES:
                print(f"NOTE: {path.name} is {size} bytes, expected "
                      f"{VCTK_ZIP_BYTES}. Continuing; the zip directory "
                      f"check below will catch a truncated file.")
            return path

    raise RuntimeError(
        "VCTK-Corpus-0.92.zip not found under "
        f"{DIR['datasets']}. Expected the copy downloaded on Sep 17."
    )


def verify_vctk_archive_md5(path=None):
    """Optional integrity check. Reads all 11.7 GB, so it is slow over
    Drive; the zip central directory check in prepare_vctk() is usually
    enough."""
    path = path or locate_vctk_archive()
    if "VCTK_MD5" not in globals():
        print("VCTK_MD5 is not defined; nothing to compare against.")
        return None
    import hashlib

    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    got = h.hexdigest()
    print(f"md5 {got} {'OK' if got == VCTK_MD5 else 'MISMATCH'}")
    return got


# ------------------------------------------------------------- audio I/O

def _decode_flac(raw):
    """FLAC bytes -> (float32 mono ndarray, sample_rate)."""
    try:
        import soundfile as sf

        x, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
        return x.mean(axis=1).astype(np.float32), int(sr)
    except ImportError:
        pass

    try:
        import torchaudio

        wav, sr = torchaudio.load(io.BytesIO(raw), format="flac")
        return wav.mean(dim=0).numpy().astype(np.float32), int(sr)
    except Exception as exc:
        raise RuntimeError(
            "No working FLAC decoder. Install one with "
            "`pip install soundfile` (or run ensure_runtime_deps(), which "
            f"installs av). Last error: {exc}"
        )


def _to_16k(x, sr):
    """Anti-aliased resample to 16 kHz. Exact 1/3 decimation for VCTK."""
    if sr == VCTK_TARGET_SR:
        return x
    from scipy.signal import resample_poly

    ratio = Fraction(VCTK_TARGET_SR, sr).limit_denominator(1000)
    return resample_poly(x, ratio.numerator, ratio.denominator).astype(
        np.float32
    )


def _wav_frames(path):
    """Frame count of an existing wav, or None if it cannot be read.

    Read from the header rather than inferred from the file size: the
    44-byte canonical header is not guaranteed, and a partially written
    file must not be mistaken for a valid one.
    """
    import wave

    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes()
    except Exception:
        return None


def _write_wav_16k(path, x):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    clipped = np.clip(x, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    try:
        import soundfile as sf

        sf.write(tmp, pcm, VCTK_TARGET_SR, subtype="PCM_16")
    except ImportError:
        import wave

        with wave.open(str(tmp), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(VCTK_TARGET_SR)
            wf.writeframes(pcm.tobytes())
    os.replace(tmp, path)
    return len(pcm)


# ------------------------------------------------------------- preparation

def prepare_vctk(force=False, progress_every=10):
    """Build DIR["audio_vctk"] and VCTK_MANIFEST from the archive in Drive.

    Returns the manifest DataFrame.
    """
    if not force and verified_stage(
        "vctk_manifest", [(VCTK_MANIFEST, "manifest_sha256")]
    ):
        print("RESUME: VCTK manifest verified.")
        return pd.read_csv(
            VCTK_MANIFEST, sep="\t", dtype={"speaker_id": str}
        )

    archive = locate_vctk_archive()
    print(f"archive {archive}")
    print(f"        {archive.stat().st_size} bytes")

    with zipfile.ZipFile(archive) as zf:
        members = [n for n in zf.namelist() if _MIC1.search(n)]
        if not members:
            raise RuntimeError(
                "No *_mic1.flac members found. The archive is not the "
                "VCTK-Corpus-0.92 release, or it is truncated."
            )

        by_speaker = {}
        for name in members:
            speaker = _MIC1.search(name).group(1)
            by_speaker.setdefault(speaker, []).append(name)
        for names in by_speaker.values():
            names.sort()

        print(f"mic1 members {len(members)} across "
              f"{len(by_speaker)} speakers")
        print(f"gate: post-resample samples >= {VCTK_MIN_SAMPLES} "
              f"({VCTK_MIN_SAMPLES / VCTK_TARGET_SR:.2f} s), keeping the "
              f"first {VCTK_UTTS_PER_SPEAKER} valid per speaker")

        rows, skipped, done = [], {}, 0
        for speaker in sorted(by_speaker):
            kept, tried = [], 0
            for name in by_speaker[speaker]:
                if len(kept) >= VCTK_UTTS_PER_SPEAKER:
                    break
                tried += 1
                stem = name.rsplit("/", 1)[-1][:-len(".flac")]
                rel = f"{speaker}/{stem}.wav"
                out_path = DIR["audio_vctk"] / rel

                if out_path.exists():
                    n = _wav_frames(out_path)
                    if n is not None and n >= VCTK_MIN_SAMPLES:
                        kept.append((rel, int(n), name, None))
                        continue
                    # Truncated, unreadable, or below the gate: rewrite it
                    # rather than carry a bad file into the manifest.
                    out_path.unlink()

                x, sr = _decode_flac(zf.read(name))
                if x.size == 0 or not np.isfinite(x).all():
                    continue
                y = _to_16k(x, sr)
                if y.size < VCTK_MIN_SAMPLES:
                    continue
                n = _write_wav_16k(out_path, y)
                kept.append((rel, int(n), name, int(sr)))

            if len(kept) < VCTK_UTTS_PER_SPEAKER:
                skipped[speaker] = len(kept)
                # Leave the partial wavs on disk; they cost little and make
                # a re-run cheap if the gate is ever revisited. They are not
                # in the manifest, so nothing reads them.
                continue

            for rank, (rel, n, member, src_sr) in enumerate(kept):
                rows.append({
                    "speaker_id": speaker,
                    "rank": rank,
                    "relative_path": rel,
                    "n_samples": n,
                    "sample_rate": VCTK_TARGET_SR,
                    "source_sample_rate": src_sr,
                    "source_member": member,
                })

            done += 1
            if progress_every and done % progress_every == 0:
                print(f"  {done} speakers prepared "
                      f"({len(rows)} utterances)", flush=True)

    if not rows:
        raise RuntimeError(
            "No speaker supplied 15 valid utterances. Check the gate and "
            "the decoder before changing the protocol."
        )

    manifest = pd.DataFrame(rows).sort_values(
        ["speaker_id", "rank"]
    ).reset_index(drop=True)

    VCTK_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = VCTK_MANIFEST.with_name(VCTK_MANIFEST.name + ".tmp")
    manifest.to_csv(tmp, sep="\t", index=False)
    os.replace(tmp, VCTK_MANIFEST)

    mark_stage("vctk_manifest", {
        "corpus": "VCTK-Corpus-0.92",
        "archive_bytes": archive.stat().st_size,
        "mic": "mic1",
        "target_sample_rate": VCTK_TARGET_SR,
        "validity_rule": "mic1_post_resample_samples>=24000",
        "utterances_per_speaker": VCTK_UTTS_PER_SPEAKER,
        "selection": "first N valid in sorted filename order",
        "resampler": "scipy.signal.resample_poly",
        "n_speakers": int(manifest["speaker_id"].nunique()),
        "n_utterances": int(len(manifest)),
        "n_speakers_skipped": len(skipped),
        "manifest_sha256": sha256_file(VCTK_MANIFEST),
    })

    print(f"\nspeakers kept    {manifest['speaker_id'].nunique()}")
    print(f"utterances       {len(manifest)}")
    print(f"speakers skipped {len(skipped)} (fewer than "
          f"{VCTK_UTTS_PER_SPEAKER} valid utterances)")
    if skipped:
        shown = sorted(skipped.items())[:10]
        print("  " + ", ".join(f"{s}:{n}" for s, n in shown)
              + (" ..." if len(skipped) > 10 else ""))
    print(f"\nWrote {VCTK_MANIFEST}")
    print(f"Audio  {DIR['audio_vctk']}")
    return manifest


def vctk_manifest_report():
    if not VCTK_MANIFEST.exists():
        print("No VCTK manifest yet. Run prepare_vctk().")
        return None
    m = pd.read_csv(VCTK_MANIFEST, sep="\t", dtype={"speaker_id": str})
    dur = m["n_samples"] / VCTK_TARGET_SR
    print(f"speakers   {m['speaker_id'].nunique()}")
    print(f"utterances {len(m)}")
    print(f"duration   min {dur.min():.2f}s  median {dur.median():.2f}s  "
          f"max {dur.max():.2f}s  total {dur.sum()/60:.1f} min")
    counts = m.groupby("speaker_id").size()
    bad = counts[counts != VCTK_UTTS_PER_SPEAKER]
    if len(bad):
        print(f"WARNING: {len(bad)} speakers do not have exactly "
              f"{VCTK_UTTS_PER_SPEAKER} utterances; "
              "vctk_external_data() will skip them.")
    missing = [
        r.relative_path for r in m.itertuples(index=False)
        if not (DIR["audio_vctk"] / r.relative_path).exists()
    ]
    if missing:
        print(f"WARNING: {len(missing)} manifest files are missing on "
              f"disk, first: {missing[0]}")
    else:
        print("all manifest files present on disk")
    return m


print("VCTK preparation ready.")
print("  locate_vctk_archive()     - find the zip already in Drive")
print("  prepare_vctk()            - stream mic1, resample, build manifest")
print("  vctk_manifest_report()    - check what was built")
print("  verify_vctk_archive_md5() - optional, reads all 11.7 GB")

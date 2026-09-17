"""Harness for external_confidence_cells.py.

Stubs the notebook globals with a synthetic but similarity-preserving
IoM pipeline, and provides REFERENCE metric implementations written in a
deliberately different style (explicit loops) so that agreement with the
vectorised weighted versions is a real check, not a tautology.
"""
import json
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ext_test")
SRC = Path(__file__).parent

# ----------------------------------------------------------- torch stub
class _T:
    def __init__(self, a): self.a = np.asarray(a)
    def unsqueeze(self, _): return self
    def squeeze(self, _): return self
    def cpu(self): return self
    def to(self, _): return self


torch = types.ModuleType("torch")
torch.float32 = np.float32
torch.Tensor = _T
torch.tensor = lambda v, dtype=None, device=None: _T(v)


class _Gen:
    def __init__(self, device="cpu"): self.seed = 0
    def manual_seed(self, s): self.seed = int(s); return self


torch.Generator = _Gen
torch.randn = lambda shape, generator=None, dtype=None: _T(
    np.full(3, getattr(generator, "seed", 0) % 9973))
sys.modules["torch"] = torch

# --------------------------------------------------- synthetic pipeline
M_REF, Q_REF, D_REF, N_ID, N_PROBE = 128, 32, 64, 40, 10
rng = np.random.default_rng(7)
_identity = {f"p{i:03d}": rng.standard_normal(D_REF) for i in range(N_ID)}


def _vec(uid, noise):
    return _identity[uid] + noise * rng.standard_normal(D_REF)


def _proj(key):
    """Index set + offsets for one IoM key, deterministic in the key."""
    r = np.random.default_rng(abs(hash(key)) % (2**32))
    return r.integers(0, D_REF, M_REF), r.random(M_REF)


_PROJ = {}


def iom_hash(x, Rx, M, q):
    key = float(np.asarray(Rx.a).ravel()[0])
    if key not in _PROJ:
        _PROJ[key] = _proj(key)
    idx, off = _PROJ[key]
    v = np.asarray(x.a).ravel()
    z = (v[idx] * 1.6 + off) % 1.0
    return _T((z * q).astype(np.int64))


def collision_count(a, b):
    return int(np.sum(np.asarray(a.a) == np.asarray(b.a)))


# ------------------------------------------------- REFERENCE metrics
def tar_at_threshold(genuine, tau):
    g = np.asarray(genuine)
    return float(np.sum(g >= tau) / len(g))


def eer_discrete_interpolated(genuine, imposter, M):
    """Reference: explicit per-threshold loop."""
    g, i = np.asarray(genuine), np.asarray(imposter)
    prev_c, prev_d, prev_fmr = None, None, None
    for c in range(M + 2):
        fmr = float(np.sum(i >= c) / len(i))
        fnmr = float(np.sum(g < c) / len(g))
        d = fmr - fnmr
        if d <= 0:
            if prev_c is None:
                return (fmr + fnmr) / 2.0, c
            t = 0.0 if prev_d == d else prev_d / (prev_d - d)
            return prev_fmr + t * (fmr - prev_fmr), c
        prev_c, prev_d, prev_fmr = c, d, fmr
    return float(np.sum(i >= M) / len(i)), M


def dsys_discrete(mated, nonmated, M):
    """Reference: explicit per-bin loop, omega = 1."""
    m, n = np.asarray(mated), np.asarray(nonmated)
    total = 0.0
    for s in range(M + 1):
        pm = float(np.sum(m == s) / len(m))
        pn = float(np.sum(n == s) / len(n))
        if pm + pn <= 0:
            continue
        d = 2.0 * pm / (pm + pn) - 1.0
        total += pm * min(max(d, 0.0), 1.0)
    return total


# --------------------------------------------------------- environment
def make_env():
    import hashlib
    import os

    for sub in ("seal", "runs", "protocol"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    DIR = {k: ROOT / k for k in ("seal", "runs", "protocol")}

    def sha256_file(p):
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()

    def atomic_json(p, obj):
        p.parent.mkdir(parents=True, exist_ok=True)
        t = p.with_name(p.name + ".tmp")
        t.write_text(json.dumps(obj, indent=2, sort_keys=True))
        os.replace(t, p)

    # Heterogeneous probe quality, so genuine scores have a left tail that
    # reaches into the impostor range. Without it the two distributions are
    # cleanly separated and the TAR / FMR checks below are vacuous.
    noises = [0.012, 0.015, 0.018, 0.020, 0.022,
              0.025, 0.030, 0.050, 0.070, 0.090]
    subjects = sorted(_identity)
    enroll = {u: _vec(u, 0.005) for u in subjects}
    probes = {u: [_vec(u, noises[k]) for k in range(N_PROBE)]
              for u in subjects}

    chosen = {
        "modality": "voice", "M": M_REF, "q": Q_REF, "o": 1,
        "development": {"EER": 0.0095, "TAR_DEV": 0.952,
                        "Dsys_DEV": 0.0525, "c_tau_DEV": 14},
        "rule": {"rule_id": "min_dsys_subject_to_eer_floor_v1"},
    }

    return {
        "__name__": "nb", "DIR": DIR, "json": json, "np": np, "torch": torch,
        "sha256_file": sha256_file, "atomic_json": atomic_json,
        "mark_stage": lambda s, p: atomic_json(
            DIR["seal"] / f"stage_{s}.done.json", {"stage": s, **p}),
        "select_operating_point": lambda m: chosen,
        "selected_poly_key": lambda m: (None, None),
        "poly_transform": lambda x, Ck, Ek, o: x,
        "iom_hash": iom_hash, "iom_tensor": lambda m, o, d: _T([1.0]),
        "collision_count": collision_count,
        "tar_at_threshold": tar_at_threshold,
        "eer_discrete_interpolated": eer_discrete_interpolated,
        "dsys_discrete": dsys_discrete,
        "seed_unlink": lambda m, k: 1000 + k,
        "vctk_external_data": lambda: (subjects, enroll, probes),
        "MODEL_DEVICE": "cpu", "MASTER_SEED": 2026, "G": 5,
        "PROTOCOL_VERSION": "1.1.1",
    }


results = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label
          + (f"   {detail}" if detail else ""))
    results.append(bool(cond))
    return bool(cond)


g = make_env()

# Build the sealed external_result.json from the reference implementations,
# exactly as evaluate_external() would have.
exec(compile((SRC / "external_confidence_cells.py").read_text(),
             "external_confidence_cells.py", "exec"), g)

H = g["_external_histograms"]("voice")
fg, fi, fm, fn = H["flat"]
ref_eer, ref_c = eer_discrete_interpolated(fg, fi, H["M"])
sealed = {
    "modality": "voice", "corpus": "SYNTH", "M": H["M"], "q": H["q"],
    "o": H["o"], "n_subjects": H["n"], "n_genuine": len(fg),
    "n_impostor": len(fi), "c_tau_carried_from_DEV": H["tau"],
    "EER_EXT": float(ref_eer), "c_EER_EXT": int(ref_c),
    "TAR_EXT_at_dev_threshold": tar_at_threshold(fg, H["tau"]),
    "FMR_EXT_at_dev_threshold": float(np.mean(np.asarray(fi) >= H["tau"])),
    "Dsys_EXT": dsys_discrete(fm, fn, H["M"]),
}
out_dir = g["DIR"]["runs"] / "external" / "voice"
out_dir.mkdir(parents=True, exist_ok=True)
g["atomic_json"](out_dir / "external_result.json", sealed)

print(f"\nsynthetic corpus: {H['n']} identities, {len(fg)} genuine, "
      f"{len(fi)} impostor, tau={H['tau']}")
print(f"  sealed EER {ref_eer*100:.3f}%  TAR "
      f"{sealed['TAR_EXT_at_dev_threshold']*100:.2f}%  "
      f"Dsys {sealed['Dsys_EXT']:.4f}")

print("\n[1] weighted metrics at unit weights vs reference implementations")
ones = np.ones(H["n"])
pt = g["_metrics"](H, ones)
for k, refv in (("EER_EXT", ref_eer),
                ("TAR_EXT_at_dev_threshold",
                 sealed["TAR_EXT_at_dev_threshold"]),
                ("FMR_EXT_at_dev_threshold",
                 sealed["FMR_EXT_at_dev_threshold"]),
                ("Dsys_EXT", sealed["Dsys_EXT"])):
    check(f"{k} matches reference", abs(pt[k] - refv) < 1e-9,
          f"{pt[k]!r} vs {refv!r}")
check("c_EER matches reference", pt["c_EER_EXT"] == ref_c,
      f"{pt['c_EER_EXT']} vs {ref_c}")

print("\n[2] weighting behaves like a real resample")
w = np.zeros(H["n"]); w[:H["n"] // 2] = 2.0     # half the identities, doubled
sub = g["_metrics"](H, w)
subj = H["subjects"][:H["n"] // 2]
keep_g = [c for u in subj for c in []]  # rebuilt below from histograms
idx = [H["subjects"].index(u) for u in subj]
man_g = H["Ghist"][idx].sum(axis=0)
man_i = H["Ihist"][np.ix_(idx, idx)].sum(axis=(0, 1))
check("subset weighting equals summing that subset's histograms",
      abs(sub["TAR_EXT_at_dev_threshold"]
          - float(man_g[H["tau"]:].sum() / man_g.sum())) < 1e-12)
check("impostor product weights exclude same-identity pairs",
      abs(float(np.trace(H["Ihist"].sum(axis=2))) - 0.0) < 1e-12)

print("\n[3] full run")
rec = g["external_confidence"]("voice", n_bootstrap=200)
m = rec["modalities"]["voice"]["metrics"]
check("interval brackets the point estimate for every metric",
      all(v["lower"] <= v["estimate"] <= v["upper"] for v in m.values()),
      str({k: round(v["lower"], 4) for k, v in m.items()}))
check("external_confidence.json written",
      (out_dir / "external_confidence.json").exists())
check("sealed external_result.json untouched",
      json.loads((out_dir / "external_result.json").read_text()) == sealed)
check("seed is recorded and deterministic",
      rec["modalities"]["voice"]["bootstrap_seed"] == g["_ext_seed"]("voice"))

print("\n[4] validation actually catches a mismatch")
bad = dict(sealed); bad["EER_EXT"] = sealed["EER_EXT"] + 0.01
g["atomic_json"](out_dir / "external_result.json", bad)
(out_dir / "external_confidence.json").unlink()
try:
    g["external_confidence"]("voice", n_bootstrap=10)
    ok, detail = False, "no error raised"
except RuntimeError as exc:
    ok, detail = "does not match the sealed" in str(exc), str(exc)[:54]
check("drift against the sealed result raises", ok, detail)
g["atomic_json"](out_dir / "external_result.json", sealed)

print("\n[5] overlap comparison")
hel = {"modalities": {"voice": {"metrics": {
    "EER_HOLDOUT": {"estimate": 0.0193, "lower": 0.0109, "upper": 0.0292},
    "TAR_HOLDOUT_at_dev_threshold": {"estimate": 0.9397, "lower": 0.8966,
                                     "upper": 0.9741},
    "FMR_HOLDOUT_at_dev_threshold": {"estimate": 0.00185, "lower": 0.00028,
                                     "upper": 0.0048},
    "Dsys_HOLDOUT": {"estimate": 0.0884, "lower": 0.0708, "upper": 0.2185},
}}}}
g["atomic_json"](g["DIR"]["runs"] / "heldout" / "heldout_confidence.json", hel)
g["external_confidence"]("voice", n_bootstrap=200)
rows = g["external_vs_heldout"]("voice")
check("comparison returns a verdict per metric", rows is not None and len(rows) == 4)

print(f"\n{sum(results)}/{len(results)} checks passed"
      + ("" if all(results) else "   <- FAILURES ABOVE"))
sys.exit(0 if all(results) else 1)

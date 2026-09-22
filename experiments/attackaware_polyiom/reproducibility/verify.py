#!/usr/bin/env python3
"""Recompute every number the paper reports, from results/ alone.

    python3 verify.py

No dependencies beyond the standard library, no network, no data, no GPU.
It reads the stored result files, derives each figure the paper quotes, and
checks it. Any mismatch is a failure and the script exits non-zero.

This is deliberately separate from the code that produced the results. It
re-derives the paper's claims from the stored outputs, so it catches a
number that was transcribed wrongly into the manuscript. It cannot catch a
mistake inside the pipeline itself; for that, rerun the notebooks.
"""

import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent / "results"
PASS, FAIL = [], []


def load(*parts):
    return json.loads((R.joinpath(*parts)).read_text())


def check(label, got, want, tol=5e-4):
    """Compare to the value printed in the paper, at the paper's precision."""
    ok = abs(got - want) <= tol
    (PASS if ok else FAIL).append(label)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} "
          f"{got:>12.4f}  paper says {want:.4f}")
    return ok


def check_eq(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} "
          f"{str(got):>12}  paper says {want}")
    return ok


def excludes_zero(ci):
    return ci[0] > 0 or ci[1] < 0


def section(title):
    print(f"\n{title}\n{'-' * len(title)}")


voice = load("heldout", "voice_heldout_result.json")
face = load("heldout", "face_heldout_result.json")
ext = load("external", "voice_external_result.json")
abl = load("ablation", "ablation_result.json")
inv = load("inversion", "inversion_result.json")
rev = load("revocation", "revocation_result.json")

section("Section 5.1  Sealed operating points")
for name, r, M, q, o, tau in (("voice", voice, 128, 32, 1, 37),
                              ("face", face, 256, 32, 1, 68)):
    check_eq(f"{name} M", r["M"], M)
    check_eq(f"{name} q", r["q"], q)
    check_eq(f"{name} o", r["o"], o)
    check_eq(f"{name} tau* carried from development",
             r["c_tau_carried_from_DEV"], tau)
check("voice development EER %",
      voice["development_reference"]["EER"] * 100, 0.952)
check("voice development TAR %",
      voice["development_reference"]["TAR_DEV"] * 100, 95.238)
check("voice development D_sys",
      voice["development_reference"]["Dsys_DEV"], 0.052519)
check("face development EER %",
      face["development_reference"]["EER"] * 100, 2.839)
check("face development TAR %",
      face["development_reference"]["TAR_DEV"] * 100, 86.260)
check("face development D_sys",
      face["development_reference"]["Dsys_DEV"], 0.133100)

section("Section 5.2  Held-out identities")
check("voice held-out EER %", voice["EER_HOLDOUT"] * 100, 1.928)
check("voice held-out TAR %",
      voice["TAR_HOLDOUT_at_dev_threshold"] * 100, 93.966)
check("voice held-out FMR %",
      voice["FMR_HOLDOUT_at_dev_threshold"] * 100, 0.185)
check("voice held-out D_sys", voice["Dsys_HOLDOUT"], 0.0884, tol=5e-5)
check_eq("voice genuine comparisons", voice["n_genuine"], 580)
check_eq("voice impostor comparisons", voice["n_impostor"], 33060)
check("face held-out EER %", face["EER_HOLDOUT"] * 100, 4.799)
check("face held-out TAR %",
      face["TAR_HOLDOUT_at_dev_threshold"] * 100, 82.239)
check("face held-out D_sys", face["Dsys_HOLDOUT"], 0.1508, tol=5e-5)
check_eq("face genuine comparisons", face["n_genuine"], 259)
check_eq("face impostor comparisons", face["n_impostor"], 14763)

section("Section 5.3  External validation (VCTK)")
check("external EER %", ext["EER_EXT"] * 100, 2.798)
check("external TAR %", ext["TAR_EXT_at_dev_threshold"] * 100, 89.000)
check("external FMR %", ext["FMR_EXT_at_dev_threshold"] * 100, 0.377)
check("external D_sys", ext["Dsys_EXT"], 0.0803, tol=5e-5)
check_eq("external speakers", ext["n_subjects"], 110)
check_eq("threshold unchanged from development",
         ext["c_tau_carried_from_DEV"], 37)
check_eq("external FMR exceeds the 0.1% design target",
         ext["FMR_EXT_at_dev_threshold"] > 0.001, True)

section("Section 5.4  Ablation (secondary)")
av = abl["modalities"]["voice"]["arms"]
check("voice polyiom EER %", av["polyiom"]["EER"] * 100, 1.928)
check("voice iom_only EER %", av["iom_only"]["EER"] * 100, 0.273)
check("voice randproj_iom EER %", av["randproj_iom"]["EER"] * 100, 0.700)
check_eq("ablation reproduces the sealed held-out EER",
         abl["modalities"]["voice"]["polyiom_reproduces_sealed_heldout"], True)
cv = abl["modalities"]["voice"]["contrasts_vs_polyiom"]
check("polyiom costs vs randproj_iom, pp",
      -cv["randproj_iom"]["delta_EER"] * 100, 1.228)
check_eq("that contrast is firm (interval excludes zero)",
         excludes_zero(cv["randproj_iom"]["delta_EER_CI"]), True)
check_eq("iom_only contrast is firm (interval excludes zero)",
         excludes_zero(cv["iom_only"]["delta_EER_CI"]), True)
for arm in ("iom_only", "randproj_iom"):
    check_eq(f"no D_sys difference vs {arm} (interval spans zero)",
             excludes_zero(cv[arm]["delta_Dsys_CI"]), False)

section("Section 5.5  Inversion (secondary)")
for mod in ("voice", "face"):
    for arm in ("polyiom", "iom_only", "randproj_iom"):
        check(f"{mod} {arm} attack success rate",
              inv["modalities"][mod]["arms"][arm]["SAR"], 1.0)
iv = inv["modalities"]["voice"]["arms"]
check("voice polyiom cosine to true embedding",
      iv["polyiom"]["cos_to_true"], 0.222, tol=5e-4)
check("voice iom_only cosine to true embedding",
      iv["iom_only"]["cos_to_true"], 0.913, tol=5e-4)
check("voice chance cosine", iv["polyiom"]["cos_chance"], 0.120, tol=5e-4)

section("Section 5.6  Revocation (secondary)")
check_eq("fresh key sets per arm per modality", rev["n_fresh_keys"], 40)
check_eq("bootstrap resamples keys and identities",
         rev["modalities"]["voice"]["bootstrap_axes"], "keys and identities")
for mod, want in (("voice", (7.50, 100.0, 5.73)),
                  ("face", (25.60, 100.0, 2.89))):
    arms = rev["modalities"][mod]["arms"]
    for arm, w in zip(("polyiom", "iom_only", "randproj_iom"), want):
        check(f"{mod} {arm} PRAR %", arms[arm]["PRAR"] * 100, w, tol=5e-3)
    check(f"{mod} polyiom per-key median PRAR %",
          arms["polyiom"]["per_key_median"] * 100, 0.0)

# "Failing outright" means a key set that leaves at least half the subjects
# exposed. It is NOT the same as every subject, and the paper must not say
# so: 12 key sets clear the half mark, 8 of them leave everyone exposed.
half, whole = {}, {}
for arm in ("polyiom", "iom_only", "randproj_iom"):
    half[arm] = sum(sum(1 for x in rev["modalities"][m]["arms"][arm]
                        ["per_key_PRAR"] if x >= 0.5)
                    for m in ("voice", "face"))
    whole[arm] = sum(sum(1 for x in rev["modalities"][m]["arms"][arm]
                         ["per_key_PRAR"] if x == 1.0)
                     for m in ("voice", "face"))
check_eq("polyiom key sets leaving >=50% of subjects exposed (of 80)",
         half["polyiom"], 12)
check_eq("polyiom key sets leaving every subject exposed (of 80)",
         whole["polyiom"], 8)
check_eq("randproj_iom key sets leaving >=50% exposed (of 80)",
         half["randproj_iom"], 0)
check_eq("iom_only key sets leaving every subject exposed (of 80)",
         whole["iom_only"], 80)
rc = rev["modalities"]["voice"]["contrasts_vs_polyiom"]["randproj_iom"]
check_eq("voice polyiom vs randproj_iom is NOT distinguishable",
         excludes_zero(rc["delta_PRAR_CI"]), False)

section("Cross-file consistency")
check_eq("ablation and held-out report the same sealed voice EER",
         abs(av["polyiom"]["EER"] - voice["EER_HOLDOUT"]) < 1e-12, True)
check_eq("ablation and held-out report the same sealed voice D_sys",
         abs(av["polyiom"]["Dsys"] - voice["Dsys_HOLDOUT"]) < 1e-12, True)
check_eq("inversion and revocation report the same voice polyiom cosine",
         abs(iv["polyiom"]["cos_to_true"]
             - rev["modalities"]["voice"]["arms"]["polyiom"]["cos_to_true"])
         < 1e-12, True)
for name, r in (("ablation", abl), ("inversion", inv), ("revocation", rev)):
    check_eq(f"{name} changed no seal", r["changes_any_seal"], False)
    check_eq(f"{name} master seed", r["master_seed"], 2026)

print(f"\n{'=' * 72}")
print(f"{len(PASS)} checks passed, {len(FAIL)} failed")
if FAIL:
    print("\nFAILED:")
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("Every number the paper reports is reproduced from results/.")

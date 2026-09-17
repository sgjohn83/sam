"""
Runtime dependency check and repair.

seal/latest_runtime_environment.json (Sep 16) recorded:

    "av": null, "facenet-pytorch": null, "speechbrain": null

on an otherwise healthy runtime (Tesla T4, torch 2.11.0+cu128, Python
3.13.15). Those three nulls are the embedding stack: speechbrain supplies
the ECAPA encoder behind ecapa_embedding(), facenet-pytorch the face
encoder, and av is the audio decoder torchaudio falls back to. Nothing that
only reads cached embeddings notices, which is why the sweep completed - but
the VCTK external evaluation has to run ECAPA over new audio, so it cannot
start on a runtime in that state.

Load before any stage that extracts embeddings:

    exec(open("/content/drive/MyDrive/AttackAware_PolyIoM_v1_1_4/"
              "runtime_deps_cells.py").read())
    ensure_runtime_deps()

WHY THIS INSTALLS THE WAY IT DOES
---------------------------------
facenet-pytorch pins old torch/torchvision releases in its metadata. A
plain `pip install facenet-pytorch` on this runtime resolves those pins and
downgrades torch off the cu128 build, which silently removes GPU support
and invalidates the recorded environment. It is installed with --no-deps;
its real requirements (numpy, pillow, requests, torchvision) are already
present.

torch is recorded before and after the install and the result is compared,
so a downgrade is reported loudly instead of being discovered three stages
later.

The pinned ECAPA checkpoint revision in seal/ecapa_checkpoints.json is not
touched here. This file installs libraries; it never changes model
provenance.
"""

import json
import platform
import subprocess
import sys

# Import name -> pip requirement, plus whether to suppress dependency
# resolution for that package.
RUNTIME_DEPS = [
    ("speechbrain", "speechbrain", False),
    ("facenet_pytorch", "facenet-pytorch", True),
    ("av", "av", False),
]


def _version(import_name):
    """Installed version of a package, or None if it is not importable."""
    from importlib import metadata

    dist = {
        "speechbrain": "speechbrain",
        "facenet_pytorch": "facenet-pytorch",
        "av": "av",
    }.get(import_name, import_name)
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _pip_install(requirement, no_deps):
    cmd = [sys.executable, "-m", "pip", "install", "-q", requirement]
    if no_deps:
        cmd.insert(4, "--no-deps")
    print("  $", " ".join(cmd[2:]), flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-6:]
        raise RuntimeError(
            f"pip install {requirement} failed:\n" + "\n".join(tail)
        )


def runtime_environment():
    """The environment record, in the same shape as the sealed file."""
    import torch

    def v(import_name):
        return _version(import_name)

    gpu = None
    if torch.cuda.is_available():
        try:
            gpu = torch.cuda.get_device_name(0)
        except Exception:
            gpu = "unavailable"

    env = {
        "av": v("av"),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": torch.version.cuda,
        "cudnn_version": (
            torch.backends.cudnn.version()
            if torch.cuda.is_available() else None
        ),
        "facenet-pytorch": v("facenet_pytorch"),
        "gpu": gpu,
        "numpy": v("numpy"),
        "pandas": v("pandas"),
        "platform": platform.platform(),
        "python": sys.version,
        "speechbrain": v("speechbrain"),
        "torch": torch.__version__,
        "torchaudio": v("torchaudio"),
        "torchvision": v("torchvision"),
    }
    return env


def record_runtime_environment():
    """Overwrite seal/latest_runtime_environment.json with the live state.

    This file is a record of the runtime a stage ran on, not a pinned
    input, so it is expected to change between sessions. environment.json
    (the original sealed record) is never touched.
    """
    env = runtime_environment()
    path = DIR["seal"] / "latest_runtime_environment.json"
    atomic_json(path, env)
    return env


def ensure_runtime_deps(install=True, verbose=True):
    """Make speechbrain / facenet-pytorch / av importable, then re-record.

    Returns the environment dict that was written. With install=False this
    only reports, which is the safe way to check a runtime before deciding
    to spend an install on it.
    """
    import torch

    torch_before = torch.__version__
    missing = [
        (imp, req, no_deps)
        for imp, req, no_deps in RUNTIME_DEPS
        if _version(imp) is None
    ]

    if verbose:
        print("runtime dependencies")
        for imp, _, _ in RUNTIME_DEPS:
            got = _version(imp)
            print(f"  {imp:16s} {got or 'MISSING'}")

    if missing and not install:
        print("\ninstall=False; nothing installed.")
    elif missing:
        print("\ninstalling:", ", ".join(r for _, r, _ in missing))
        for _, req, no_deps in missing:
            _pip_install(req, no_deps)

        still = [imp for imp, _, _ in missing if _version(imp) is None]
        if still:
            raise RuntimeError(
                "Installed but not importable: " + ", ".join(still)
                + ". Restart the runtime and re-run ensure_runtime_deps()."
            )
    elif verbose:
        print("\nAll three present; nothing to install.")

    # A changed torch means the resolver moved it, which is the failure
    # this whole file exists to avoid. Read the version from the installed
    # distribution metadata rather than the imported module: the already
    # imported torch keeps reporting the old version until the runtime is
    # restarted, which is exactly what would hide the problem.
    torch_on_disk = _version("torch")
    if torch_on_disk and torch_on_disk != torch_before:
        print(f"\nWARNING: torch changed {torch_before} -> "
              f"{torch_on_disk} on disk during install.")
        print("The cu128 build may have been replaced. Restart the "
              "runtime, then check torch.cuda.is_available() before any "
              "stage, and reinstall the pinned build if it is False.")

    env = record_runtime_environment()
    if verbose:
        print("\nsealed seal/latest_runtime_environment.json:")
        print(json.dumps(env, indent=2))
        if not env["cuda_available"]:
            print("\nWARNING: CUDA is not available on this runtime. "
                  "Embedding extraction will run on CPU.")
    return env


print("Runtime dependency helper loaded.")
print("  ensure_runtime_deps(install=False) - report only")
print("  ensure_runtime_deps()              - install what is missing")
print("  record_runtime_environment()       - re-seal the runtime record")

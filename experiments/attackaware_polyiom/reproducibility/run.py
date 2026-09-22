#!/usr/bin/env python3
"""AttackAware PolyIoM v1.1.4 — one entry point.

    python3 run.py verify     check the paper against results/   (no deps)
    python3 run.py demo       run the pipeline on synthetic data (numpy)
    python3 run.py parity     check NumPy against PyTorch        (torch)
    python3 run.py all        all three

Run `verify` first. It needs nothing but Python and tells you whether the
manuscript matches the stored results.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def banner(title):
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def need(module, what):
    try:
        __import__(module)
        return True
    except ImportError:
        print(f"\n{what} needs `{module}`, which is not installed.")
        print(f"    pip install {module}")
        return False


def cmd_verify():
    banner("verify — every number in the paper, from results/")
    return subprocess.call([sys.executable, str(HERE / "verify.py")])


def cmd_demo():
    banner("demo — the pipeline end to end on synthetic data")
    if not need("numpy", "The demo"):
        return 1
    from polyiom import demo
    demo.run()
    return 0


def cmd_parity():
    banner("parity — NumPy pipeline against the study's PyTorch one")
    if not need("numpy", "The parity check"):
        return 1
    from polyiom import parity
    ok = parity.run()
    if ok is None:          # torch absent: skipped, not failed
        return 0
    return 0 if ok else 1


COMMANDS = {"verify": cmd_verify, "demo": cmd_demo, "parity": cmd_parity}


def main(argv):
    if len(argv) != 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if len(argv) == 2 else 2
    name = argv[1]
    if name == "all":
        codes = [COMMANDS[c]() for c in ("verify", "parity", "demo")]
        banner("done")
        print("all steps exited cleanly" if not any(codes)
              else f"a step failed: exit codes {codes}")
        return max(codes)
    if name not in COMMANDS:
        print(f"unknown command: {name}\n")
        print(__doc__)
        return 2
    return COMMANDS[name]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))

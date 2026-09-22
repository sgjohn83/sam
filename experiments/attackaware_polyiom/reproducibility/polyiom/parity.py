"""Check the NumPy pipeline against the study's PyTorch pipeline.

The study ran on PyTorch. polyiom/core.py is a NumPy rewrite of the same
maths, so it is only trustworthy if it agrees. This runs both on the same
random inputs and compares.

What agreement means here. The hardened vectors are floating point, so
they are compared to float32 precision, not for equality. The error is
measured against the scale of the data, not per element: a per-element
relative error is meaningless where a hardened value happens to sit near
zero, and reports a large number for a difference of one bit.

The templates are argmax indices, and those must match exactly. A single
index that differs is a different template, and every downstream number is
built from index comparisons. That is the check that actually decides.

Skipped, not passed, when torch is absent.
"""

import math

import numpy as np

from . import core


def torch_reference(z, key, overlap, tensor, M, q):
    """The study's implementation, transcribed from ablation_only.py."""
    import torch

    def poly_indices(d, ov, device):
        stride = core.G - ov
        k = 1 + math.ceil((d - core.G) / stride)
        idx = (torch.arange(k, device=device)[:, None] * stride
               + torch.arange(core.G, device=device))
        return idx.clamp(max=d - 1).long(), idx < d

    def poly_transform(vectors, coefficients, exponents, ov):
        idx, mask = poly_indices(vectors.shape[-1], ov, vectors.device)
        values = vectors[..., idx] * mask.to(vectors.dtype)
        coefficients = torch.as_tensor(coefficients, dtype=vectors.dtype)
        exponents = torch.as_tensor(exponents, dtype=torch.int64)
        return (torch.pow(values, exponents) * coefficients).sum(dim=-1)

    batch = torch.as_tensor(np.asarray(z), dtype=torch.float32)
    projected = poly_transform(batch, key[0], key[1], overlap)
    frozen = torch.as_tensor(np.asarray(tensor), dtype=torch.float32)[:M, :q]
    scores = torch.einsum("bk,mqk->bmq", projected, frozen)
    codes = torch.argmax(scores, dim=-1).to(torch.int16).numpy()
    return projected.numpy(), codes


def run(n=256, d=192, M=128, q=32, overlap=1, seed=core.MASTER_SEED):
    try:
        import torch  # noqa: F401
    except ImportError:
        print("torch is not installed, so the parity check is SKIPPED.")
        print("The NumPy pipeline is unverified against the study's own "
              "implementation until this runs.")
        return None

    rng = np.random.default_rng(seed)
    z = core.l2(rng.standard_normal((n, d)).astype(np.float32))
    key = (rng.standard_normal(core.G).astype(np.float32),
           rng.integers(1, 4, core.G))
    k = core.output_length(d, overlap)
    tensor = rng.standard_normal((M, q, k)).astype(np.float32)

    np_proj = core.poly_transform(z, key[0], key[1], overlap)
    np_codes = core.hash_arm(z, "polyiom", key, overlap, tensor, M, q)
    pt_proj, pt_codes = torch_reference(z, key, overlap, tensor, M, q)

    eps = float(np.finfo(np.float32).eps)
    absolute = float(np.max(np.abs(np_proj - pt_proj)))
    scale = float(np.max(np.abs(pt_proj)))
    relative = absolute / scale
    moved = int((np_codes != pt_codes).sum())
    total = np_codes.size

    print(f"  {n} vectors, d={d}, M={M}, q={q}, o={overlap}, k={k}")
    print(f"  hardened vector, max absolute difference  {absolute:.3e}")
    print(f"  as a fraction of the data's scale         {relative:.3e}"
          f"  ({relative / eps:.1f} x float32 eps)")
    print(f"  template indices differing                {moved} of {total}")

    # A few ulps is agreement; the index check is what decides.
    ok = relative < 8 * eps and moved == 0
    print("  PARITY OK" if ok else "  *** PARITY FAILED")
    return ok

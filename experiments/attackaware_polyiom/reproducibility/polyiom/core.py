"""The AttackAware PolyIoM pipeline, in plain NumPy.

The study runs on PyTorch inside Colab. This is the same pipeline written
against NumPy so it runs anywhere with no GPU and no heavy install. The
two are checked against each other by `run.py parity`, which is skipped
when torch is absent rather than silently assumed.

Three stages:

    z  ->  P_K*(z; o*)  ->  IoM-GRP  ->  argmax index per group

and matching counts how many group indices two templates share.
"""

import hashlib
import math

import numpy as np

G = 5              # polynomial window length
MASTER_SEED = 2026

ARMS = ("polyiom", "iom_only", "randproj_iom")
ARM_NOTE = {
    "polyiom": "z -> P_K*(z; o*) -> IoM-GRP   (the proposed method)",
    "iom_only": "z ----------------> IoM-GRP   (the practical baseline)",
    "randproj_iom": "z -> A z ----------> IoM-GRP   (isolates the polynomial)",
}


def H(*fields):
    """The study's seed derivation: SHA-256 of the joined fields."""
    payload = "|".join(str(f) for f in fields).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") \
        & ((1 << 63) - 1)


def l2(vectors, eps=1e-12):
    v = np.asarray(vectors, dtype=np.float32)
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    if np.any(norm <= eps):
        raise ValueError("zero-norm embedding")
    return v / norm


def output_length(d, overlap):
    """k, the length of the hardened vector. Window G, shift G - overlap."""
    return 1 + math.ceil((d - G) / (G - overlap))


def poly_indices(d, overlap):
    """Window start positions, and the mask for the final short window."""
    stride = G - overlap
    k = output_length(d, overlap)
    idx = np.arange(k)[:, None] * stride + np.arange(G)
    mask = idx < d
    return np.clip(idx, None, d - 1).astype(np.int64), mask


def poly_transform(vectors, coefficients, exponents, overlap):
    """Keyed polynomial hardening over overlapping windows of G values.

    Exponents are applied as Python integers. Casting them to float to use
    a vectorised power would produce nan on negative bases, and embeddings
    are signed.
    """
    vectors = np.asarray(vectors, dtype=np.float32)
    idx, mask = poly_indices(vectors.shape[-1], overlap)
    values = vectors[..., idx] * mask.astype(np.float32)
    coefficients = np.asarray(coefficients, dtype=np.float32)
    powers = np.stack([values[..., i] ** int(exponents[i])
                       for i in range(values.shape[-1])], axis=-1)
    return (powers * coefficients).sum(axis=-1, dtype=np.float32)


def iom_hash(projected, tensor, M, q):
    """IoM-GRP: M groups of q random projections, keep the argmax index.

    Returns one int16 index per group, which is the stored template.
    """
    projected = np.asarray(projected, dtype=np.float32)
    tensor = np.asarray(tensor[:M, :q], dtype=np.float32)
    scores = np.einsum("bk,mqk->bmq", projected, tensor, optimize=True)
    return np.argmax(scores, axis=-1).astype(np.int16)


def hash_arm(vectors, arm, key, overlap, tensor, M, q, A=None):
    """One arm's protected templates. Only the pre-projection differs."""
    vectors = np.asarray(vectors, dtype=np.float32)
    if arm == "polyiom":
        coefficients, exponents = key
        projected = poly_transform(vectors, coefficients, exponents, overlap)
    elif arm == "randproj_iom":
        projected = vectors @ np.asarray(A, dtype=np.float32)
    elif arm == "iom_only":
        projected = vectors
    else:
        raise ValueError(f"unknown arm: {arm}")
    return iom_hash(projected, tensor, M, q)


def collisions(a, b):
    """Collision score: how many group indices two template sets share.

    Returns an (len(a), len(b)) integer matrix. A comparison is accepted
    when its score reaches the threshold.
    """
    return (np.asarray(a)[:, None, :] == np.asarray(b)[None, :, :]).sum(axis=-1)


def histogram(counts, M):
    """Score counts over 0..M. Lossless: scores are integers in that range."""
    return np.bincount(np.asarray(counts).ravel(), minlength=M + 1)[:M + 1]

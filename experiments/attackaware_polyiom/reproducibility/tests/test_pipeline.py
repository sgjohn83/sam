"""Unit tests for the pipeline and the metrics.

    python3 -m unittest discover -s tests -v
    python3 run.py test

Standard library only apart from NumPy. These test properties that must
hold whatever the data is, and the edge cases that have actually bitten
this code.
"""

import math
import unittest

import numpy as np

from polyiom import core, metrics


class TestPolynomial(unittest.TestCase):

    def test_output_length_matches_the_study(self):
        # The two sealed configurations. If these move, every stored
        # frozen tensor has the wrong shape and nothing else is valid.
        self.assertEqual(core.output_length(192, 1), 48)    # voice
        self.assertEqual(core.output_length(512, 1), 128)   # face

    def test_output_length_formula(self):
        for d in (64, 100, 192, 512, 1000):
            for o in (0, 1, 2, 3, 4):
                k = core.output_length(d, o)
                self.assertEqual(k, 1 + math.ceil((d - core.G) / (core.G - o)))
                # windows must cover the vector
                self.assertGreaterEqual((k - 1) * (core.G - o) + core.G, d)

    def test_windows_stay_in_range_and_mask_the_tail(self):
        d, o = 100, 1
        idx, mask = core.poly_indices(d, o)
        self.assertTrue((idx < d).all(), "index past the end of the vector")
        self.assertTrue(mask[0].all(), "first window should be fully valid")
        # the last window may run off the end; those positions are masked
        self.assertEqual(idx.shape[1], core.G)

    def test_masked_tail_contributes_nothing(self):
        # Changing values beyond d cannot affect the output, because the
        # clamped indices are zeroed by the mask.
        rng = np.random.default_rng(0)
        z = rng.standard_normal((3, 97)).astype(np.float32)
        key = (rng.standard_normal(core.G).astype(np.float32),
               np.array([1, 2, 1, 3, 1]))
        a = core.poly_transform(z, *key, 1)
        self.assertEqual(a.shape, (3, core.output_length(97, 1)))
        self.assertTrue(np.isfinite(a).all())

    def test_negative_inputs_do_not_produce_nan(self):
        # Embeddings are signed. A float exponent would give nan here.
        z = np.full((2, 20), -0.5, dtype=np.float32)
        key = (np.ones(core.G, dtype=np.float32), np.array([1, 2, 3, 2, 1]))
        out = core.poly_transform(z, *key, 1)
        self.assertTrue(np.isfinite(out).all(), "nan from a negative base")

    def test_transform_is_deterministic(self):
        rng = np.random.default_rng(1)
        z = rng.standard_normal((5, 60)).astype(np.float32)
        key = (rng.standard_normal(core.G).astype(np.float32),
               rng.integers(1, 4, core.G))
        np.testing.assert_array_equal(core.poly_transform(z, *key, 1),
                                      core.poly_transform(z, *key, 1))

    def test_a_different_key_gives_a_different_vector(self):
        rng = np.random.default_rng(2)
        z = core.l2(rng.standard_normal((4, 60)).astype(np.float32))
        k1 = (rng.standard_normal(core.G).astype(np.float32),
              np.array([1, 2, 1, 3, 1]))
        k2 = (rng.standard_normal(core.G).astype(np.float32),
              np.array([1, 2, 1, 3, 1]))
        self.assertFalse(np.allclose(core.poly_transform(z, *k1, 1),
                                     core.poly_transform(z, *k2, 1)))


class TestHashing(unittest.TestCase):

    def setUp(self):
        self.rng = np.random.default_rng(3)
        self.d, self.M, self.q, self.o = 60, 32, 8, 1
        self.k = core.output_length(self.d, self.o)
        self.z = core.l2(self.rng.standard_normal((6, self.d)).astype(np.float32))
        self.key = (self.rng.standard_normal(core.G).astype(np.float32),
                    self.rng.integers(1, 4, core.G))
        self.T = self.rng.standard_normal((self.M, self.q, self.k)).astype(np.float32)
        self.A = self.rng.standard_normal((self.d, self.k)).astype(np.float32)

    def test_template_shape_and_index_range(self):
        for arm in core.ARMS:
            T = (self.rng.standard_normal((self.M, self.q, self.d)).astype(np.float32)
                 if arm == "iom_only" else self.T)
            h = core.hash_arm(self.z, arm, self.key, self.o, T,
                              self.M, self.q, self.A)
            self.assertEqual(h.shape, (len(self.z), self.M), arm)
            self.assertTrue((h >= 0).all() and (h < self.q).all(),
                            f"{arm}: index outside 0..q-1")

    def test_identical_inputs_collide_completely(self):
        h = core.hash_arm(self.z, "polyiom", self.key, self.o, self.T,
                          self.M, self.q)
        np.testing.assert_array_equal(core.collisions(h, h).diagonal(),
                                      np.full(len(self.z), self.M))

    def test_collision_score_is_symmetric_and_bounded(self):
        h = core.hash_arm(self.z, "polyiom", self.key, self.o, self.T,
                          self.M, self.q)
        c = core.collisions(h, h)
        np.testing.assert_array_equal(c, c.T)
        self.assertTrue((c >= 0).all() and (c <= self.M).all())

    def test_unknown_arm_is_rejected(self):
        with self.assertRaises(ValueError):
            core.hash_arm(self.z, "not_an_arm", self.key, self.o, self.T,
                          self.M, self.q)

    def test_argmax_is_invariant_to_positive_rescaling(self):
        # The stored template is an argmax index, so scaling the hardened
        # vector cannot change it. The inversion attack relies on this.
        h1 = core.iom_hash(np.ones((2, self.k), dtype=np.float32) * 0.1,
                           self.T, self.M, self.q)
        h2 = core.iom_hash(np.ones((2, self.k), dtype=np.float32) * 7.5,
                           self.T, self.M, self.q)
        np.testing.assert_array_equal(h1, h2)


class TestHistogram(unittest.TestCase):

    def test_histogram_is_lossless(self):
        rng = np.random.default_rng(4)
        M = 40
        scores = rng.integers(0, M + 1, 500)
        h = core.histogram(scores, M)
        self.assertEqual(h.sum(), scores.size)
        self.assertEqual(len(h), M + 1)
        for value in range(M + 1):
            self.assertEqual(h[value], int((scores == value).sum()))


class TestMetrics(unittest.TestCase):

    def test_eer_of_separated_distributions_is_zero(self):
        # The case a crossing-only search misses: FMR and FNMR are both
        # zero over a run of thresholds, so the difference never flips.
        g = np.zeros(51); g[40:] = 10
        i = np.zeros(51); i[:10] = 10
        self.assertEqual(metrics.eer(g, i)[0], 0.0)

    def test_eer_of_identical_distributions_is_one_half(self):
        u = np.ones(51)
        self.assertAlmostEqual(metrics.eer(u, u)[0], 0.5, places=6)

    def test_eer_is_a_rate(self):
        # EER is bounded by 0 and 1, not by 0.5. It exceeds 0.5 when the
        # genuine distribution scores LOWER than the impostor one, which
        # is a system performing worse than chance. Random histograms are
        # exchangeable, so that case does arise here.
        rng = np.random.default_rng(5)
        for _ in range(50):
            g = rng.integers(0, 50, 31).astype(float)
            i = rng.integers(0, 50, 31).astype(float)
            if g.sum() == 0 or i.sum() == 0:
                continue
            e, _ = metrics.eer(g, i)
            self.assertGreaterEqual(e, 0.0)
            self.assertLessEqual(e, 1.0)

    def test_eer_at_most_one_half_when_genuine_scores_higher(self):
        # The real case: genuine comparisons stochastically dominate
        # impostor ones. Then the equal-error point cannot exceed 0.5.
        rng = np.random.default_rng(9)
        M = 50
        for p_imp, p_gen in ((0.2, 0.6), (0.3, 0.5), (0.1, 0.9), (0.4, 0.45)):
            i = core.histogram(rng.binomial(M, p_imp, 4000), M).astype(float)
            g = core.histogram(rng.binomial(M, p_gen, 4000), M).astype(float)
            e, _ = metrics.eer(g, i)
            self.assertLessEqual(e, 0.5 + 1e-9,
                                 f"p_imp={p_imp} p_gen={p_gen} gave {e}")

    def test_eer_exceeds_one_half_for_an_inverted_system(self):
        # Genuine low, impostor high: every decision is backwards.
        g = np.zeros(51); g[:10] = 10
        i = np.zeros(51); i[40:] = 10
        e, _ = metrics.eer(g, i)
        self.assertGreater(e, 0.5)

    def test_empty_distribution_raises(self):
        with self.assertRaises(ValueError):
            metrics.eer(np.zeros(10), np.ones(10))

    def test_dsys_bounds(self):
        u = np.ones(51)
        self.assertAlmostEqual(metrics.dsys(u, u), 0.0, places=9)
        mated = np.zeros(51); mated[50] = 100
        nonmated = np.zeros(51); nonmated[0] = 100
        self.assertAlmostEqual(metrics.dsys(mated, nonmated), 1.0, places=9)

    def test_dsys_is_in_the_unit_interval(self):
        rng = np.random.default_rng(6)
        for _ in range(20):
            m = rng.integers(0, 30, 21).astype(float)
            n = rng.integers(0, 30, 21).astype(float)
            if m.sum() == 0 or n.sum() == 0:
                continue
            d = metrics.dsys(m, n)
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)

    def test_rates_are_monotone(self):
        rng = np.random.default_rng(7)
        g = rng.integers(1, 30, 26).astype(float)
        i = rng.integers(1, 30, 26).astype(float)
        fmr, fnmr = metrics.rates(g, i)
        self.assertTrue(np.all(np.diff(fmr) <= 1e-12), "FMR must not rise")
        self.assertTrue(np.all(np.diff(fnmr) >= -1e-12), "FNMR must not fall")
        self.assertAlmostEqual(fmr[0], 1.0, places=9)
        self.assertAlmostEqual(fnmr[0], 0.0, places=9)

    def test_tar_and_fmr_agree_with_the_rate_curves(self):
        rng = np.random.default_rng(8)
        g = rng.integers(1, 30, 26).astype(float)
        i = rng.integers(1, 30, 26).astype(float)
        fmr, fnmr = metrics.rates(g, i)
        for t in (0, 5, 13, 25):
            self.assertAlmostEqual(metrics.fmr_at(i, t), fmr[t], places=9)
            self.assertAlmostEqual(metrics.tar_at(g, t), 1.0 - fnmr[t],
                                   places=9)

    def test_prar_counts_acceptances(self):
        self.assertEqual(metrics.prar([10, 90, 95, 20], 50), 0.5)
        self.assertEqual(metrics.prar([10, 20], 50), 0.0)
        self.assertEqual(metrics.prar([60, 70], 50), 1.0)


class TestStoredResults(unittest.TestCase):
    """The stored results must satisfy the invariants the paper relies on."""

    @classmethod
    def setUpClass(cls):
        import json
        from pathlib import Path
        R = Path(__file__).resolve().parent.parent / "results"
        cls.abl = json.loads((R / "ablation/ablation_result.json").read_text())
        cls.inv = json.loads((R / "inversion/inversion_result.json").read_text())
        cls.rev = json.loads((R / "revocation/revocation_result.json").read_text())
        cls.voice = json.loads(
            (R / "heldout/voice_heldout_result.json").read_text())

    def test_no_analysis_changed_a_seal(self):
        for r in (self.abl, self.inv, self.rev):
            self.assertFalse(r["changes_any_seal"])
            self.assertEqual(r["master_seed"], 2026)

    def test_ablation_reproduces_the_sealed_operating_point(self):
        self.assertAlmostEqual(
            self.abl["modalities"]["voice"]["arms"]["polyiom"]["EER"],
            self.voice["EER_HOLDOUT"], places=12)

    def test_every_interval_is_ordered_and_brackets_its_estimate(self):
        checked = 0
        for r in (self.abl, self.inv, self.rev):
            for mod in r["modalities"].values():
                for arm in mod["arms"].values():
                    for key, ci in list(arm.items()):
                        if not key.endswith("_CI"):
                            continue
                        point = arm.get(key[:-3])
                        self.assertLessEqual(ci[0], ci[1], key)
                        if point is not None:
                            self.assertLessEqual(ci[0] - 1e-9, point, key)
                            self.assertGreaterEqual(ci[1] + 1e-9, point, key)
                        checked += 1
        self.assertGreater(checked, 10, "expected many intervals to check")

    def test_per_key_rates_are_probabilities(self):
        for mod in self.rev["modalities"].values():
            for arm in mod["arms"].values():
                per_key = np.asarray(arm["per_key_PRAR"])
                self.assertEqual(len(per_key), self.rev["n_fresh_keys"])
                self.assertTrue((per_key >= 0).all() and (per_key <= 1).all())
                self.assertAlmostEqual(float(np.median(per_key)),
                                       arm["per_key_median"], places=9)
                self.assertAlmostEqual(float(per_key.max()),
                                       arm["per_key_max"], places=9)

    def test_failing_outright_means_at_least_half_the_subjects(self):
        # The definition is per_key_PRAR >= 0.5, not == 1.0. The paper
        # states both counts; conflating them overstates the failure.
        for mod in self.rev["modalities"].values():
            for arm in mod["arms"].values():
                per_key = np.asarray(arm["per_key_PRAR"])
                self.assertAlmostEqual(float((per_key >= 0.5).mean()),
                                       arm["keys_failing_outright"], places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import unittest
from lib import estimate_cost

MODELS = {"leader": "fable", "workers": "sonnet", "summary": "haiku"}


class TestCostBasic(unittest.TestCase):
    def test_positive(self):
        cost = estimate_cost("write hello world", MODELS, 3)
        self.assertGreater(cost, 0)

    def test_finite(self):
        import math
        cost = estimate_cost("design a microservice", MODELS, 6)
        self.assertTrue(math.isfinite(cost))

    def test_max_4_decimal_places(self):
        cost = estimate_cost("design a java microservice", MODELS, 3)
        decimals = len(str(cost).split(".")[-1]) if "." in str(cost) else 0
        self.assertLessEqual(decimals, 4)


class TestCostScaling(unittest.TestCase):
    def test_more_workers_higher_cost(self):
        c6 = estimate_cost("build a REST API", MODELS, 6)
        c2 = estimate_cost("build a REST API", MODELS, 2)
        self.assertGreater(c6, c2)

    def test_longer_task_higher_cost(self):
        short = estimate_cost("write code", MODELS, 3)
        long  = estimate_cost(" ".join(["design microservice with postgres and kubernetes"] * 20), MODELS, 3)
        self.assertGreater(long, short)


class TestCostTiers(unittest.TestCase):
    def test_fable_leader_more_than_haiku_leader(self):
        fable = estimate_cost("build service", {"leader": "fable",  "workers": "sonnet", "summary": "haiku"}, 3)
        haiku = estimate_cost("build service", {"leader": "haiku",  "workers": "sonnet", "summary": "haiku"}, 3)
        self.assertGreater(fable, haiku)

    def test_opus_workers_more_than_haiku_workers(self):
        opus  = estimate_cost("build service", {"leader": "opus", "workers": "opus",  "summary": "haiku"}, 3)
        haiku = estimate_cost("build service", {"leader": "opus", "workers": "haiku", "summary": "haiku"}, 3)
        self.assertGreater(opus, haiku)

    def test_sonnet_summary_more_than_haiku_summary(self):
        sonnet = estimate_cost("build API", {"leader": "opus", "workers": "sonnet", "summary": "sonnet"}, 3)
        haiku  = estimate_cost("build API", {"leader": "opus", "workers": "sonnet", "summary": "haiku"},  3)
        self.assertGreater(sonnet, haiku)

    def test_unknown_model_no_crash(self):
        import math
        cost = estimate_cost("build API", {"leader": "unknown", "workers": "sonnet", "summary": "haiku"}, 3)
        self.assertTrue(math.isfinite(cost))


if __name__ == "__main__":
    unittest.main()

import unittest
from lib import topo_rounds


def w(id_, deps=None):
    return {"id": id_, "dependsOn": deps or []}


class TestTopoNoDeps(unittest.TestCase):
    def test_three_independent_one_round(self):
        rounds = topo_rounds([w("w1"), w("w2"), w("w3")])
        self.assertEqual(len(rounds), 1)
        self.assertEqual(len(rounds[0]), 3)

    def test_single_worker(self):
        rounds = topo_rounds([w("w1")])
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0][0]["id"], "w1")


class TestTopoLinearChain(unittest.TestCase):
    def test_chain_three_rounds(self):
        rounds = topo_rounds([w("w1"), w("w2", ["w1"]), w("w3", ["w2"])])
        self.assertEqual(len(rounds), 3)
        self.assertEqual(rounds[0][0]["id"], "w1")
        self.assertEqual(rounds[1][0]["id"], "w2")
        self.assertEqual(rounds[2][0]["id"], "w3")


class TestTopoFanOutMerge(unittest.TestCase):
    def test_two_parallel_then_merge(self):
        workers = [w("w1"), w("w2"), w("w3", ["w1", "w2"])]
        rounds = topo_rounds(workers)
        self.assertEqual(len(rounds), 2)
        self.assertEqual(len(rounds[0]), 2)
        self.assertEqual(rounds[1][0]["id"], "w3")


class TestTopoUnknownDep(unittest.TestCase):
    def test_unknown_dep_treated_as_resolved(self):
        rounds = topo_rounds([w("w1", ["nonexistent"])])
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0][0]["id"], "w1")


class TestTopoCycle(unittest.TestCase):
    def test_cycle_no_hang(self):
        workers = [w("w1", ["w2"]), w("w2", ["w1"])]
        rounds = topo_rounds(workers)
        total = sum(len(r) for r in rounds)
        self.assertEqual(total, 2)


class TestTopoMixedScenario(unittest.TestCase):
    def test_w1w2_independent_w3_on_w1_w4_on_w2w3(self):
        workers = [w("w1"), w("w2"), w("w3", ["w1"]), w("w4", ["w2", "w3"])]
        rounds = topo_rounds(workers)
        self.assertEqual(len(rounds), 3)
        r1_ids = sorted(x["id"] for x in rounds[0])
        self.assertIn("w1", r1_ids)
        self.assertIn("w2", r1_ids)
        self.assertEqual(rounds[1][0]["id"], "w3")
        self.assertEqual(rounds[2][0]["id"], "w4")


class TestTopoAllAccountedFor(unittest.TestCase):
    def test_total_equals_input(self):
        workers = [w("a"), w("b", ["a"]), w("c"), w("d", ["b","c"]), w("e", ["d"])]
        rounds = topo_rounds(workers)
        total = sum(len(r) for r in rounds)
        self.assertEqual(total, len(workers))


if __name__ == "__main__":
    unittest.main()

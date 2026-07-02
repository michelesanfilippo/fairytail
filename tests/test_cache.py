import time
import unittest
from lib import build_fingerprint, jaccard_similarity, find_cache_hit, prune_cache

NOW_MS = int(time.time() * 1000)
DAY_MS = 24 * 60 * 60 * 1000


class TestBuildFingerprint(unittest.TestCase):
    def test_contains_word_count(self):
        fp = build_fingerprint("write a java service", [])
        self.assertRegex(fp, r"\d+w")

    def test_contains_persona_keys(self):
        fp = build_fingerprint("build java postgres service", ["java", "dba"])
        self.assertIn("java", fp)
        self.assertIn("dba",  fp)

    def test_persona_order_irrelevant(self):
        fp1 = build_fingerprint("task", ["dba", "java"])
        fp2 = build_fingerprint("task", ["java", "dba"])
        self.assertEqual(fp1, fp2)

    def test_different_tasks_differ(self):
        fp1 = build_fingerprint("write a java service", [])
        fp2 = build_fingerprint("write a python script", [])
        self.assertNotEqual(fp1, fp2)

    def test_normalizes_punctuation_case(self):
        fp1 = build_fingerprint("Java Spring!!!", [])
        fp2 = build_fingerprint("java spring", [])
        self.assertEqual(fp1, fp2)


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical_strings(self):
        self.assertAlmostEqual(jaccard_similarity("java spring postgres", "java spring postgres"), 1.0)

    def test_completely_different(self):
        self.assertAlmostEqual(jaccard_similarity("alpha beta gamma", "delta epsilon zeta"), 0.0)

    def test_half_overlap(self):
        # intersection={java}=1, union={java,spring,postgres}=3 → 1/3
        s = jaccard_similarity("java spring", "java postgres")
        self.assertAlmostEqual(s, 1/3, places=2)

    def test_empty_strings(self):
        self.assertEqual(jaccard_similarity("", ""), 0.0)

    def test_case_insensitive(self):
        self.assertAlmostEqual(jaccard_similarity("JAVA SPRING", "java spring"), 1.0)


class TestFindCacheHit(unittest.TestCase):
    def _entry(self, fp, plan=None, age_ms=1000):
        return {"fingerprint": fp, "plan": plan or {}, "timestamp": NOW_MS - age_ms}

    def test_exact_hit(self):
        entries = [self._entry("java spring postgres 8w java,dba", {"rationale": "A"})]
        hit = find_cache_hit("java spring postgres 8w java,dba", entries, 0.75, 30)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["plan"]["rationale"], "A")

    def test_similar_hit(self):
        # "java spring postgres 8w java,dba" vs "java spring mysql 8w java,dba"
        # tokens: java,spring,postgres,8w,javadba vs java,spring,mysql,8w,javadba
        # intersection=4, union=6 → Jaccard≈0.67 — use 0.60 threshold
        entries = [self._entry("java spring postgres 8w java,dba")]
        hit = find_cache_hit("java spring mysql 8w java,dba", entries, 0.60, 30)
        self.assertIsNotNone(hit)

    def test_different_task_miss(self):
        entries = [self._entry("java spring postgres 8w java,dba")]
        hit = find_cache_hit("python flask redis 5w python", entries, 0.75, 30)
        self.assertIsNone(hit)

    def test_expired_entry_miss(self):
        entries = [self._entry("java spring postgres 8w java,dba", age_ms=31 * DAY_MS)]
        hit = find_cache_hit("java spring postgres 8w java,dba", entries, 0.75, 30)
        self.assertIsNone(hit)

    def test_empty_cache_null(self):
        self.assertIsNone(find_cache_hit("anything", [], 0.75, 30))

    def test_returns_first_match(self):
        entries = [
            self._entry("unrelated task 3w", {"rationale": "wrong"}),
            self._entry("java spring postgres 8w java,dba", {"rationale": "correct"}),
        ]
        hit = find_cache_hit("java spring postgres 8w java,dba", entries, 0.75, 30)
        self.assertEqual(hit["plan"]["rationale"], "correct")


class TestPruneCache(unittest.TestCase):
    def test_under_limit_unchanged(self):
        entries = [{"timestamp": NOW_MS}, {"timestamp": NOW_MS - 1}]
        result = prune_cache(entries, 5)
        self.assertEqual(len(result), 2)

    def test_over_limit_truncated(self):
        entries = [{"id": i, "timestamp": NOW_MS - i * 1000} for i in range(10)]
        result = prune_cache(entries, 3)
        self.assertEqual(len(result), 3)

    def test_keeps_newest(self):
        entries = [
            {"id": "old",    "timestamp": NOW_MS - 5000},
            {"id": "newer",  "timestamp": NOW_MS - 1000},
            {"id": "newest", "timestamp": NOW_MS},
        ]
        result = prune_cache(entries, 2)
        ids = [e["id"] for e in result]
        self.assertIn("newest", ids)
        self.assertIn("newer",  ids)
        self.assertNotIn("old", ids)

    def test_does_not_mutate_original(self):
        entries = [{"timestamp": i} for i in range(5)]
        original_len = len(entries)
        prune_cache(entries, 3)
        self.assertEqual(len(entries), original_len)


if __name__ == "__main__":
    unittest.main()

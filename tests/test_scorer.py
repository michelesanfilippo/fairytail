import unittest
from lib import compute_complexity_score, score_to_leader, DEFAULT_CONFIG


class TestSignal1Domains(unittest.TestCase):
    def test_no_domain_keywords(self):
        score = compute_complexity_score("write a hello world program")
        self.assertLess(score, 15)

    def test_one_domain_java(self):
        with_domain = compute_complexity_score("implement a java class")
        without = compute_complexity_score("implement a class")
        self.assertGreater(with_domain, without)

    def test_two_domains_java_sql(self):
        s2 = compute_complexity_score("java spring with postgres sql queries")
        s1 = compute_complexity_score("java spring class")
        self.assertGreater(s2, s1)

    def test_three_domains_max_30(self):
        score = compute_complexity_score("java spring with postgres and kubernetes deploy")
        self.assertGreaterEqual(score, 30)


class TestSignal2ArchMarkers(unittest.TestCase):
    def test_one_arch_marker_microservice(self):
        base = compute_complexity_score("build a service")
        arch = compute_complexity_score("build a microservice")
        self.assertGreater(arch, base)

    def test_three_arch_markers(self):
        score = compute_complexity_score("refactor distributed microservice architecture from scratch")
        self.assertGreaterEqual(score, 25)

    def test_migration_keyword(self):
        score = compute_complexity_score("database migration script")
        self.assertGreaterEqual(score, 10)

    def test_greenfield_keyword(self):
        score = compute_complexity_score("greenfield project setup")
        self.assertGreaterEqual(score, 10)


class TestSignal3ScopeMarkers(unittest.TestCase):
    def test_one_scope_entire(self):
        score = compute_complexity_score("refactor the entire module")
        self.assertGreaterEqual(score, 8)

    def test_two_scope_markers(self):
        score = compute_complexity_score("complete end-to-end production-ready system")
        self.assertGreaterEqual(score, 20)

    def test_all_keyword(self):
        with_all = compute_complexity_score("rewrite all services")
        without  = compute_complexity_score("rewrite the service")
        self.assertGreaterEqual(with_all, without)


class TestSignal4TechDepth(unittest.TestCase):
    def test_one_stack_keyword(self):
        score = compute_complexity_score("write a react component")
        self.assertGreaterEqual(score, 5)

    def test_six_plus_stack_keywords(self):
        score = compute_complexity_score(
            "java spring hibernate maven postgres sql schema table index query"
        )
        self.assertGreaterEqual(score, 15)


class TestSignal5WordCount(unittest.TestCase):
    def test_very_short_task_no_word_pts(self):
        score = compute_complexity_score("write code")
        self.assertLess(score, 4)

    def test_medium_task_gets_word_pts(self):
        task = " ".join(["word"] * 20)
        score = compute_complexity_score(task)
        self.assertGreaterEqual(score, 4)

    def test_long_task_gets_max_word_pts(self):
        task = " ".join(["word"] * 90)
        score = compute_complexity_score(task)
        self.assertGreaterEqual(score, 10)


class TestScoreCap(unittest.TestCase):
    def test_score_never_exceeds_100(self):
        task = (
            "java spring hibernate maven postgres sql schema table index query kubernetes docker "
            "microservice distributed architecture refactor migrate entire complete all comprehensive "
            "production-ready end-to-end greenfield rewrite from scratch system integration security auth"
        )
        score = compute_complexity_score(task)
        self.assertLessEqual(score, 100)


class TestScoreToLeader(unittest.TestCase):
    def test_score_0_trivial_sonnet(self):
        r = score_to_leader(0)
        self.assertEqual(r["model"], "sonnet")
        self.assertEqual(r["band"],  "trivial")

    def test_score_30_boundary_trivial(self):
        r = score_to_leader(30)
        self.assertEqual(r["model"], "sonnet")

    def test_score_31_standard_opus(self):
        r = score_to_leader(31)
        self.assertEqual(r["model"], "opus")
        self.assertEqual(r["band"],  "standard")

    def test_score_65_boundary_standard(self):
        r = score_to_leader(65)
        self.assertEqual(r["model"], "opus")

    def test_score_66_complex_fable(self):
        r = score_to_leader(66)
        self.assertEqual(r["model"], "fable")
        self.assertEqual(r["band"],  "complex")

    def test_score_100_complex_fable(self):
        r = score_to_leader(100)
        self.assertEqual(r["model"], "fable")

    def test_custom_mapping_trivial_haiku(self):
        import copy
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        cfg["autoSelect"]["mapping"]["trivial"] = "haiku"
        r = score_to_leader(10, cfg)
        self.assertEqual(r["model"], "haiku")


if __name__ == "__main__":
    unittest.main()

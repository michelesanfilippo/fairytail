"""
Integration test — medio-alta complessità

Task: "Migrate a monolithic Java Spring Boot application to microservices
       with separate postgres schemas per service, kubernetes deployment pipeline,
       and JWT security layer. Full production-ready architecture."

Exercises scorer → personas → cost → cache → topo → persona injection → validation.
"""
import time
import unittest
from lib import (
    compute_complexity_score, score_to_leader,
    detect_personas,
    estimate_cost,
    build_fingerprint, jaccard_similarity, find_cache_hit, prune_cache,
    topo_rounds,
    extract_persona_key, build_worker_persona_block,
    validate_workflow_args, validate_model_tier,
)

TASK = (
    "Migrate a monolithic Java Spring Boot application to microservices "
    "with separate postgres schemas per service, kubernetes deployment pipeline, "
    "and JWT security layer. Full production-ready architecture."
)

TASK_VARIANT = (
    "Migrate a legacy Java Spring Boot monolith to microservices "
    "with postgres schemas, kubernetes and JWT auth. Production-ready."
)

NOW_MS = int(time.time() * 1000)
DAY_MS = 24 * 60 * 60 * 1000


class TestComplexityForJavaDbDevopsTask(unittest.TestCase):
    def test_scores_complex_band(self):
        score = compute_complexity_score(TASK)
        self.assertGreaterEqual(score, 66, f"expected complex band (≥66), got {score}")

    def test_picks_fable_leader(self):
        score = compute_complexity_score(TASK)
        result = score_to_leader(score)
        self.assertEqual(result["model"], "fable", f"score={score}")
        self.assertEqual(result["band"],  "complex")

    def test_detects_four_domains(self):
        p = detect_personas(TASK)
        for domain in ["java", "dba", "devops", "security"]:
            self.assertIn(domain, p, f"{domain} not detected")

    def test_architect_domain_detected(self):
        p = detect_personas(TASK)
        self.assertIn("architect", p)

    def test_minimum_score_given_signal_density(self):
        score = compute_complexity_score(TASK)
        self.assertGreaterEqual(score, 70, f"got {score}")


class TestCostForComplexTask(unittest.TestCase):
    MODELS = {"leader": "fable", "workers": "sonnet", "summary": "haiku"}

    def test_cost_positive(self):
        cost = estimate_cost(TASK, self.MODELS, 6)
        self.assertGreater(cost, 0)

    def test_six_workers_more_than_three(self):
        c6 = estimate_cost(TASK, self.MODELS, 6)
        c3 = estimate_cost(TASK, self.MODELS, 3)
        self.assertGreater(c6, c3)

    def test_all_fable_more_than_2x_default(self):
        all_fable = estimate_cost(TASK, {"leader": "fable", "workers": "fable", "summary": "fable"}, 5)
        default   = estimate_cost(TASK, self.MODELS, 5)
        self.assertGreater(all_fable, default * 2, f"all_fable={all_fable} default={default}")

    def test_plausible_range(self):
        cost = estimate_cost(TASK, self.MODELS, 5)
        self.assertGreater(cost, 0.01, f"too low: {cost}")
        self.assertLess(cost, 5.00,    f"suspiciously high: {cost}")


class TestCacheRoundTrip(unittest.TestCase):
    def setUp(self):
        self.personas = detect_personas(TASK)
        self.persona_keys = list(self.personas.keys())
        self.fp = build_fingerprint(TASK, self.persona_keys)
        self.fp_variant = build_fingerprint(TASK_VARIANT, self.persona_keys)

    def test_fingerprint_non_empty(self):
        self.assertIsInstance(self.fp, str)
        self.assertGreater(len(self.fp), 0)

    def test_fingerprint_contains_personas(self):
        self.assertIn("java", self.fp)
        self.assertIn("dba",  self.fp)

    def test_variant_similarity_above_0_5(self):
        sim = jaccard_similarity(self.fp, self.fp_variant)
        self.assertGreaterEqual(sim, 0.5, f"sim={sim}")

    def test_cache_hit_or_correct_miss_on_variant(self):
        entries = [{"fingerprint": self.fp, "plan": {"rationale": "cached"}, "timestamp": NOW_MS - 1000}]
        sim = jaccard_similarity(self.fp, self.fp_variant)
        hit = find_cache_hit(self.fp_variant, entries, 0.75, 30)
        if sim >= 0.75:
            self.assertIsNotNone(hit, f"sim={sim} should hit cache")
        else:
            self.assertIsNone(hit, f"sim={sim} should miss cache")

    def test_unrelated_task_misses(self):
        entries = [{"fingerprint": self.fp, "plan": {}, "timestamp": NOW_MS - 1000}]
        unrelated = build_fingerprint("write a poem about cats", [])
        self.assertIsNone(find_cache_hit(unrelated, entries, 0.75, 30))

    def test_prune_keeps_3_of_10(self):
        entries = [{"id": i, "timestamp": NOW_MS - i * 1000} for i in range(10)]
        pruned = prune_cache(entries, 3)
        self.assertEqual(len(pruned), 3)
        for e in pruned:
            self.assertLess(e["id"], 3)


class TestWorkerPlanTopo(unittest.TestCase):
    WORKERS = [
        {"id": "java",      "dependsOn": []},
        {"id": "dba",       "dependsOn": []},
        {"id": "devops",    "dependsOn": ["java", "dba"]},
        {"id": "security",  "dependsOn": ["java"]},
        {"id": "architect", "dependsOn": ["java", "dba", "security"]},
    ]

    def test_three_rounds(self):
        rounds = topo_rounds(self.WORKERS)
        self.assertEqual(len(rounds), 3, f"got {len(rounds)} rounds")

    def test_round_1_java_dba(self):
        rounds = topo_rounds(self.WORKERS)
        ids = sorted(w["id"] for w in rounds[0])
        self.assertIn("java", ids)
        self.assertIn("dba",  ids)
        self.assertEqual(len(ids), 2)

    def test_round_2_devops_security(self):
        rounds = topo_rounds(self.WORKERS)
        ids = sorted(w["id"] for w in rounds[1])
        self.assertIn("devops",   ids)
        self.assertIn("security", ids)
        self.assertEqual(len(ids), 2)

    def test_round_3_architect(self):
        rounds = topo_rounds(self.WORKERS)
        self.assertEqual(len(rounds[2]), 1)
        self.assertEqual(rounds[2][0]["id"], "architect")

    def test_total_workers_5(self):
        rounds = topo_rounds(self.WORKERS)
        total = sum(len(r) for r in rounds)
        self.assertEqual(total, 5)


class TestPersonaInjection(unittest.TestCase):
    def setUp(self):
        self.personas = detect_personas(TASK)
        self.worker_roles = [
            {"id": "java",     "role": "java: design Spring Boot microservice structure"},
            {"id": "dba",      "role": "dba: design postgres schema per service"},
            {"id": "devops",   "role": "devops: kubernetes deployment pipeline"},
            {"id": "security", "role": "security: JWT layer and API gateway auth"},
        ]

    def test_all_roles_have_persona_prefix(self):
        for w in self.worker_roles:
            key = extract_persona_key(w["role"])
            self.assertIsNotNone(key, f"role '{w['role']}' should have prefix")
            self.assertIn(key, self.personas, f"key '{key}' not in detected personas")

    def test_java_block_contains_spring_boot(self):
        block = build_worker_persona_block("java: design microservice structure", self.personas)
        self.assertIn("Spring Boot", block)

    def test_dba_block_contains_schema(self):
        block = build_worker_persona_block("dba: schema design", self.personas)
        self.assertTrue("schema" in block.lower() or "DBA" in block)

    def test_devops_block_contains_kubernetes(self):
        block = build_worker_persona_block("devops: k8s pipeline", self.personas)
        self.assertIn("Kubernetes", block)

    def test_security_block_contains_owasp_or_appsec(self):
        block = build_worker_persona_block("security: JWT auth layer", self.personas)
        self.assertTrue(
            any(kw in block for kw in ["OWASP", "AppSec", "security", "threat"]),
            f"security block: {block}"
        )


class TestEndToEndArgsValidation(unittest.TestCase):
    def test_valid_args_pass(self):
        args = {
            "task": TASK,
            "models": {"leader": "fable", "workers": "sonnet", "summary": "haiku"},
            "context": "",
            "personas": detect_personas(TASK),
            "cachedPlan": None,
        }
        self.assertTrue(validate_workflow_args(args))

    def test_all_models_valid_for_their_tiers(self):
        self.assertTrue(validate_model_tier("leader",  "fable"))
        self.assertTrue(validate_model_tier("workers", "sonnet"))
        self.assertTrue(validate_model_tier("summary", "haiku"))


if __name__ == "__main__":
    unittest.main()

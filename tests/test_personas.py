import unittest
import copy
from lib import detect_personas, extract_persona_key, build_worker_persona_block, DEFAULT_CONFIG


class TestDetectPersonas(unittest.TestCase):
    def test_java_keyword(self):
        p = detect_personas("implement a java spring boot service")
        self.assertIn("java", p)

    def test_sql_keyword_dba(self):
        p = detect_personas("design a postgres database schema")
        self.assertIn("dba", p)

    def test_kubernetes_devops(self):
        p = detect_personas("deploy with kubernetes and docker")
        self.assertIn("devops", p)

    def test_no_keywords_empty(self):
        p = detect_personas("write hello world")
        self.assertEqual(p, {})

    def test_multiple_domains(self):
        p = detect_personas("java spring microservice with postgres and kubernetes")
        self.assertIn("java",   p)
        self.assertIn("dba",    p)
        self.assertIn("devops", p)

    def test_case_insensitive(self):
        p = detect_personas("JAVA SPRING APPLICATION with SQL database")
        self.assertIn("java", p)
        self.assertIn("dba",  p)

    def test_springboot_keyword_maps_to_java(self):
        p = detect_personas("springboot service")
        self.assertIn("java", p)

    def test_jwt_auth_security(self):
        p = detect_personas("add jwt auth and oauth2 security")
        self.assertIn("security", p)

    def test_returns_description_strings(self):
        p = detect_personas("react frontend component")
        self.assertIn("frontend", p)
        self.assertIsInstance(p["frontend"], str)
        self.assertGreater(len(p["frontend"]), 0)

    def test_disabled_returns_empty(self):
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        cfg["personas"]["enabled"] = False
        p = detect_personas("java spring postgres kubernetes", cfg)
        self.assertEqual(p, {})

    def test_python_keywords(self):
        p = detect_personas("build a fastapi python service")
        self.assertIn("python", p)

    def test_react_native_mobile(self):
        p = detect_personas("react native mobile app")
        self.assertIn("mobile", p)


class TestExtractPersonaKey(unittest.TestCase):
    def test_java_prefix(self):
        self.assertEqual(extract_persona_key("java: design REST endpoint"), "java")

    def test_dba_prefix(self):
        self.assertEqual(extract_persona_key("dba: schema migration"), "dba")

    def test_no_prefix_returns_none(self):
        self.assertIsNone(extract_persona_key("design REST endpoint"))

    def test_case_insensitive(self):
        self.assertEqual(extract_persona_key("Java: build service"), "java")

    def test_architect_prefix(self):
        self.assertEqual(extract_persona_key("architect: system design"), "architect")

    def test_devops_prefix(self):
        self.assertEqual(extract_persona_key("devops: k8s pipeline"), "devops")


class TestBuildWorkerPersonaBlock(unittest.TestCase):
    def test_matched_persona_contains_description(self):
        personas = {"java": "Senior Java developer, Spring Boot expert"}
        block = build_worker_persona_block("java: build REST API", personas)
        self.assertIn("Senior Java developer", block)
        self.assertIn("YOUR PERSONA:", block)

    def test_no_matching_persona_empty(self):
        personas = {"dba": "Senior DBA"}
        block = build_worker_persona_block("java: build REST API", personas)
        self.assertEqual(block, "")

    def test_no_prefix_empty(self):
        personas = {"java": "Senior Java developer"}
        block = build_worker_persona_block("build REST API", personas)
        self.assertEqual(block, "")

    def test_empty_personas_map(self):
        block = build_worker_persona_block("java: build service", {})
        self.assertEqual(block, "")

    def test_mindset_instruction_present(self):
        personas = {"devops": "DevOps engineer with K8s expertise"}
        block = build_worker_persona_block("devops: deploy pipeline", personas)
        self.assertIn("expertise and mindset", block)


if __name__ == "__main__":
    unittest.main()

"""
Pure logic extracted from SKILL.md and fairytail.js for testing.
No I/O, no Claude primitives — deterministic functions only.
"""
import re
import math

# ── DEFAULT CONFIG ────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "models": {
        "leader":  {"default": "fable",  "allowed": ["fable", "opus", "sonnet"]},
        "workers": {"default": "sonnet", "allowed": ["sonnet", "haiku", "opus", "fable"]},
        "summary": {"default": "haiku",  "allowed": ["haiku", "sonnet"]},
    },
    "autoSelect": {
        "enabled": True,
        "scoring": {
            "architectureKeywords": [
                "migrate","migration","microservice","distributed","scalab","design",
                "architecture","from scratch","refactor","system","integrate","integration",
                "rewrite","overhaul","greenfield",
            ],
            "scopeKeywords": [
                "best way","should i","entire","whole","complete","full",
                "end-to-end","everything","all","comprehensive","production-ready","production ready",
            ],
        },
        "bands": {
            "trivial":  {"min": 0,  "max": 30,  "model": "sonnet"},
            "standard": {"min": 31, "max": 65,  "model": "opus"},
            "complex":  {"min": 66, "max": 100, "model": "fable"},
        },
        "mapping": {"trivial": "sonnet", "standard": "opus", "complex": "fable"},
    },
    "personas": {
        "enabled": True,
        "catalog": {
            "java":      "Senior Java developer, 10y Spring Boot, microservices, design patterns, OOP",
            "dba":       "Senior DBA, Oracle/Postgres, query optimization, indexing, schema design, migrations",
            "devops":    "Senior DevOps engineer, Kubernetes, Docker, CI/CD, infrastructure-as-code",
            "security":  "AppSec engineer, OWASP Top 10, threat modeling, secure coding, dependency CVEs",
            "frontend":  "Senior frontend developer, React/Vue/Angular, UX-aware, accessibility",
            "architect": "Solutions architect, distributed systems, scalability, trade-off analysis",
            "python":    "Senior Python developer, clean code, async, packaging, testing",
            "mobile":    "Senior mobile developer, iOS/Android, React Native, Flutter",
            "qa":        "Senior QA engineer, test strategy, automation, edge cases, regression",
            "data":      "Senior data engineer, pipelines, SQL/NoSQL, analytics, data modeling",
        },
        "stackKeywords": {
            "java":      ["java", "spring", "springboot", "jvm", "maven", "gradle", "hibernate"],
            "dba":       ["sql", "database", "db", "oracle", "postgres", "mysql", "schema", "query", "table"],
            "devops":    ["kubernetes", "k8s", "docker", "ci/cd", "jenkins", "pipeline", "deploy", "infra"],
            "security":  ["security", "auth", "oauth", "jwt", "vuln", "pentest", "owasp", "xss", "injection"],
            "frontend":  ["react", "vue", "angular", "html", "css", "ui", "frontend", "component", "web"],
            "architect": ["architecture", "microservice", "distributed", "scalab", "design", "system"],
            "python":    ["python", "django", "flask", "fastapi", "pip", "pandas", "numpy"],
            "mobile":    ["ios", "android", "mobile", "swift", "kotlin", "flutter", "react native"],
            "qa":        ["test", "qa", "quality", "coverage", "regression", "e2e", "unit test"],
            "data":      ["data", "etl", "pipeline", "analytics", "warehouse", "spark", "kafka"],
        },
    },
    "costEstimate": {
        "enabled": True,
        "tokensPerWord": 1.5,
        "avgWorkerOutputTokens": 800,
        "pricesPer1kTokens": {
            "fable":  {"input": 0.015,   "output": 0.075},
            "opus":   {"input": 0.015,   "output": 0.075},
            "sonnet": {"input": 0.003,   "output": 0.015},
            "haiku":  {"input": 0.00025, "output": 0.00125},
        },
    },
    "planCache": {
        "enabled": True,
        "similarityThreshold": 0.75,
        "maxEntries": 50,
        "ttlDays": 30,
    },
}


# ── COMPLEXITY SCORER ─────────────────────────────────────────────────────────

def compute_complexity_score(task: str, config: dict = None) -> int:
    if config is None:
        config = DEFAULT_CONFIG
    t = task.lower()
    scoring = config["autoSelect"]["scoring"]
    stack_kws = config["personas"]["stackKeywords"]
    score = 0

    # Signal 1 — distinct technical domains (max 30)
    domains_hit = sum(1 for kws in stack_kws.values() if any(k in t for k in kws))
    if   domains_hit >= 3: score += 30
    elif domains_hit == 2: score += 20
    elif domains_hit == 1: score += 10

    # Signal 2 — architectural complexity markers (max 25)
    arch_hits = sum(1 for k in scoring["architectureKeywords"] if k in t)
    if   arch_hits >= 3: score += 25
    elif arch_hits == 2: score += 18
    elif arch_hits == 1: score += 10

    # Signal 3 — scope/ambiguity markers (max 20)
    scope_hits = sum(1 for k in scoring["scopeKeywords"] if k in t)
    if   scope_hits >= 2: score += 20
    elif scope_hits == 1: score += 8

    # Signal 4 — technical depth: total keyword hits across all domains (max 15)
    depth_hits = sum(1 for kws in stack_kws.values() for k in kws if k in t)
    if   depth_hits >= 6: score += 15
    elif depth_hits >= 3: score += 10
    elif depth_hits >= 1: score += 5

    # Signal 5 — word count (max 10, weak)
    words = len(task.strip().split())
    if   words > 80:  score += 10
    elif words >= 41: score += 7
    elif words >= 15: score += 4

    return min(score, 100)


def score_to_leader(score: int, config: dict = None) -> dict:
    if config is None:
        config = DEFAULT_CONFIG
    bands = config["autoSelect"]["bands"]
    mapping = config["autoSelect"]["mapping"]
    if score <= bands["trivial"]["max"]:
        return {"band": "trivial",  "model": mapping["trivial"]}
    if score <= bands["standard"]["max"]:
        return {"band": "standard", "model": mapping["standard"]}
    return     {"band": "complex",  "model": mapping["complex"]}


# ── PERSONA DETECTOR ──────────────────────────────────────────────────────────

def detect_personas(task: str, config: dict = None) -> dict:
    if config is None:
        config = DEFAULT_CONFIG
    if not config["personas"]["enabled"]:
        return {}
    t = task.lower()
    detected = {}
    for key, kws in config["personas"]["stackKeywords"].items():
        if any(k in t for k in kws):
            detected[key] = config["personas"]["catalog"][key]
    return detected


# ── COST ESTIMATOR ────────────────────────────────────────────────────────────

def estimate_cost(task: str, models: dict, max_workers: int, config: dict = None) -> float:
    if config is None:
        config = DEFAULT_CONFIG
    ce = config["costEstimate"]
    prices = ce["pricesPer1kTokens"]
    task_words = len(task.strip().split())

    leader_in   = task_words * ce["tokensPerWord"] + 500
    leader_out  = 400
    worker_in   = (task_words * ce["tokensPerWord"] + 300) * max_workers
    worker_out  = ce["avgWorkerOutputTokens"] * max_workers
    summary_in  = worker_out + 200
    summary_out = 300

    lp = prices.get(models["leader"],  prices["opus"])
    wp = prices.get(models["workers"], prices["sonnet"])
    sp = prices.get(models["summary"], prices["haiku"])

    input_cost  = (leader_in  * lp["input"]  + worker_in  * wp["input"]  + summary_in  * sp["input"])  / 1000
    output_cost = (leader_out * lp["output"] + worker_out * wp["output"] + summary_out * sp["output"]) / 1000
    return round(input_cost + output_cost, 4)


# ── PLAN CACHE ────────────────────────────────────────────────────────────────

def build_fingerprint(task: str, persona_keys: list) -> str:
    clean = re.sub(r"[^a-z0-9\s]", "", task.lower()).strip()
    words = clean.split()
    word_count = len(words)
    prefix = " ".join(words[:12])
    personas_str = ",".join(sorted(persona_keys)) if persona_keys else ""
    return f"{prefix} {word_count}w{' ' + personas_str if personas_str else ''}"


def jaccard_similarity(a: str, b: str) -> float:
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def find_cache_hit(fingerprint: str, entries: list, threshold: float, ttl_days: int):
    import time
    now_ms = time.time() * 1000
    ttl_ms = ttl_days * 24 * 60 * 60 * 1000
    for entry in entries:
        if now_ms - entry["timestamp"] > ttl_ms:
            continue
        sim = jaccard_similarity(fingerprint, entry["fingerprint"])
        if sim >= threshold:
            return entry
    return None


def prune_cache(entries: list, max_entries: int) -> list:
    if len(entries) <= max_entries:
        return list(entries)
    return sorted(entries, key=lambda e: e["timestamp"], reverse=True)[:max_entries]


# ── TOPO SORT ─────────────────────────────────────────────────────────────────

def topo_rounds(workers: list) -> list:
    by_id = {w["id"]: w for w in workers}
    done = set()
    rounds = []
    pending = set(w["id"] for w in workers)
    safety = len(workers) + 2
    while pending and safety > 0:
        safety -= 1
        round_ = []
        for id_ in list(pending):
            w = by_id[id_]
            deps = w.get("dependsOn") or []
            if all(d in done or d not in by_id for d in deps):
                round_.append(w)
        if not round_:
            round_ = [by_id[id_] for id_ in pending]
        rounds.append(round_)
        for w in round_:
            done.add(w["id"])
            pending.discard(w["id"])
    return rounds


# ── PERSONA PROMPT INJECTION ──────────────────────────────────────────────────

def extract_persona_key(role: str):
    m = re.match(r"^([a-z]+):\s*", role, re.IGNORECASE)
    return m.group(1).lower() if m else None


def build_worker_persona_block(role: str, personas: dict) -> str:
    key = extract_persona_key(role)
    if not key or key not in personas:
        return ""
    return f"\nYOUR PERSONA: {personas[key]}\nOperate with the expertise and mindset of this role.\n"


# ── ARGS VALIDATION ───────────────────────────────────────────────────────────

def validate_workflow_args(args) -> bool:
    if not isinstance(args, dict):
        raise ValueError("args must be a dict")
    task = args.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("args.task is required (non-empty string)")
    return True


def validate_model_tier(tier: str, model_id: str, config: dict = None) -> bool:
    if config is None:
        config = DEFAULT_CONFIG
    return model_id in config["models"][tier]["allowed"]

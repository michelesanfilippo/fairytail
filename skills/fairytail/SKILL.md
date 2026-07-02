---
name: fairytail
description: Orchestrated multi-agent pipeline for CLI tasks. Team Leader (reasoning tier) plans, N workers (execution tier) run in parallel with peer context, Summary (cheap tier) produces caveman report. Trigger for prompts like "/fairytail <task>", "fairytail run X", "orchestrate this multi-agent", or when the user explicitly asks for the fairytail system.
---

# Fairytail — Orchestrated Multi-Agent Pipeline

## What it does

Runs a 3-tier agent pipeline:
1. **Team Leader** (reasoning model — fable/opus/sonnet) — analyzes task, decomposes into N sub-agents, returns structured plan.
2. **Workers** (execution model — sonnet default) — run concurrently with peer-context injection when `dependsOn` is set.
3. **Summary** (cheap model — haiku default) — aggregates worker outputs into caveman report.

Caveman style enforced across all agents: no emoji, no filler, keywords + lists + symbols, terse but complete.

## When to trigger

- User types `/fairytail <task>` or "fairytail <task>"
- User asks for orchestrated multi-agent execution
- User explicitly invokes this skill by name

Do NOT trigger for single-shot questions, trivial edits, or when user has not asked for orchestration.

## How to execute

### Step 1 — Show banner (first run only)

Check for the marker file `~/.claude/fairytail/.banner_shown` (or `./.claude/fairytail/.banner_shown` for project scope) using the Read tool.

**If the marker file does NOT exist (first run):**
- Read `~/.claude/fairytail/fairytail-ascii.txt` and output its contents inside a fenced code block.
- STRICT: zero text before the banner, zero text after. No preamble, no commentary.
- If banner file is missing: output exactly `fairytail: banner not found` and continue.
- After printing the banner, create the marker file by writing a single character `1` to `~/.claude/fairytail/.banner_shown` using the Write tool. This marks all future runs as non-first.

**If the marker file EXISTS (subsequent runs):**
- Skip the banner entirely. Do not print it, do not mention it.
- Proceed directly to Step 2.

The workflow does NOT print the banner under any circumstances.

### Step 2 — Load config

Read config from (in priority order):
1. `./.claude/fairytail.config.json` (project override)
2. `~/.claude/fairytail.config.json` (user global)
3. Fallback embedded defaults (see bottom of this file)

Use the Read tool. If both files are absent, use embedded defaults silently.

### Step 3 — Parse args

The user prompt after `/fairytail` may contain flags:
- `--leader=<fable|opus|sonnet>` — override leader model
- `--workers=<sonnet|haiku|opus|fable>` — override workers model
- `--summary=<haiku|sonnet>` — override summary model
- `--max-workers=<N>` — cap parallelism (respects config.orchestration.maxWorkers ceiling)

Strip these flags from the task string. Everything else IS the task. Also strip leading `/fairytail` or `fairytail` from the message if present.

If the cleaned task is empty, print caveman error `fairytail: empty task. usage: /fairytail <task>` and stop.

### Step 4 — Auto-pick model tiers

For each tier NOT overridden by CLI flag:

**Workers auto-pick:** `config.models.workers.default`.

**Summary auto-pick:** `config.models.summary.default`.

**Leader auto-pick — multi-signal scoring:**

Compute a `complexityScore` (0–100) by summing weighted signals on the task string (case-insensitive):

**Signal 1 — distinct technical domains (weight: 30 pts)**
Count how many distinct domain groups from `config.personas.stackKeywords` have at least one keyword match in the task.
- 1 domain → +10
- 2 domains → +20
- 3+ domains → +30

**Signal 2 — architectural complexity markers (weight: 25 pts)**
Keywords: `migrate`, `migration`, `microservice`, `distributed`, `scalab`, `design`, `architecture`, `from scratch`, `refactor`, `system`, `integrate`, `integration`, `rewrite`, `overhaul`, `greenfield`
- 1 match → +10
- 2 matches → +18
- 3+ matches → +25

**Signal 3 — scope/ambiguity markers (weight: 20 pts)**
Keywords: `best way`, `should i`, `entire`, `whole`, `complete`, `full`, `end-to-end`, `everything`, `all`, `comprehensive`, `production-ready`, `production ready`
- 1 match → +8
- 2+ matches → +20

**Signal 4 — technical depth (weight: 15 pts)**
Count total distinct stack keyword hits across all domains (not just which domains, but how many keywords matched).
- 1–2 hits → +5
- 3–5 hits → +10
- 6+ hits → +15

**Signal 5 — word count (weight: 10 pts, weak signal)**
- < 15 words → +0
- 15–40 words → +4
- 41–80 words → +7
- > 80 words → +10

**Band mapping:**
- score 0–30 → `config.autoSelect.mapping.trivial` (default: `sonnet`)
- score 31–65 → `config.autoSelect.mapping.standard` (default: `opus`)
- score 66–100 → `config.autoSelect.mapping.complex` (default: `fable`)

Include the score and band in the auto-pick line: `leader=opus (score=48, band=standard)`.

### Step 4.5 — Persona detection

If `config.personas.enabled` is true, scan the task string for stack keywords from `config.personas.stackKeywords`. For each persona whose keywords appear in the task, add it to a `detectedPersonas` map. Pass this map to the workflow as `args.personas` — the leader will assign them to workers.

Print detected personas in the auto-pick line (see Step 5).

### Step 4.6 — Cost estimate

If `config.costEstimate.enabled` is true, compute a rough pre-run cost estimate using `config.costEstimate`:

```
taskWords = word_count(task)
leaderInputTokens  = taskWords * tokensPerWord + 500  (system overhead)
leaderOutputTokens = 400
workerInputTokens  = (taskWords * tokensPerWord + 300) * maxWorkers
workerOutputTokens = avgWorkerOutputTokens * maxWorkers
summaryInputTokens = workerOutputTokens + 200
summaryOutputTokens = 300

totalInputCost  = leaderIn * price[leader].input/1000
                + workerIn * price[workers].input/1000
                + summaryIn * price[summary].input/1000
totalOutputCost = leaderOut * price[leader].output/1000
                + workerOut * price[workers].output/1000
                + summaryOut * price[summary].output/1000
estimatedUSD = totalInputCost + totalOutputCost
```

Include this in the auto-pick line as `~$X.XXX`.

### Step 5 — Show pick + REQUIRE confirmation

Print ONE caveman line summarizing the auto-picks, task word count, detected personas, and cost estimate. Example:

```
auto-pick | leader=opus (task=64 words, band=standard) | workers=sonnet | summary=haiku | maxWorkers=6 | personas=java,dba | ~$0.043
```

Then call `AskUserQuestion` with a single question:

- question: `Proceed with these models?`
- header: `Confirm`
- multiSelect: false
- options:
  1. `Yes, run as picked` (Recommended) — proceed as-is
  2. `Change leader only`
  3. `Change workers only`
  4. `Change all tiers`

Follow-up asks (chain sequentially based on the answer):

- If user selected **Change leader only**: single ask
  - question: `Which leader?`
  - header: `Leader`
  - options built from `config.models.leader.allowed`. Order: Fable first (Recommended), then Opus, then any others. Each option label is the plain model id.
- If user selected **Change workers only**: single ask
  - question: `Which workers?`
  - header: `Workers`
  - options from `config.models.workers.allowed`, `sonnet` first (Recommended).
- If user selected **Change all tiers**: three sequential asks (leader, workers, summary) with the same option-building rules.

The user's "Other" custom input goes through the same validation as Step 6.

### Step 6 — Final validation

After user confirmation, ensure each chosen model id is in its tier's `allowed` list. If not (e.g. user typed a bad "Other" value), fall back to that tier's `default` and print `warn | invalid <tier>=<id>, fallback -> <default>`.

### Step 6.5 — Knowledge assessment (grill-me)

Before launching the workflow, perform a Socratic self-assessment of the task.

**Self-assess internally (no output).** Evaluate the task along these axes:
- Domain specificity: how niche/technical is this? Do I know the stack, context, constraints?
- Completeness: are there missing requirements, acceptance criteria, edge cases?
- Ambiguity: are key terms undefined or open to multiple interpretations?
- Risk: would a wrong assumption here cause all workers to produce useless output?

Assign an internal `confidence` score 0–100. Use `config.grillMe.confidenceThreshold` (default: 75) as the pass bar.

**If `confidence >= threshold`:** skip directly to Step 7. Print nothing about confidence.

**If `confidence < threshold`:** activate grill-me.

Print ONE line: `grill-me | confidence=<N>% — need more context before planning`

Then enter the grill-me interview loop (max `config.grillMe.maxRounds` rounds, default: 3):

**Each round:**
1. Output 1–3 sharp, targeted questions in plain text. Questions must be:
   - Specific to the actual gap (not generic "tell me more")
   - Ordered by impact: most critical gap first
   - Caveman style: no filler, direct
   - Numbered: `1.`, `2.`, `3.`
2. Wait for the user to answer (the user replies in the next turn).
3. Incorporate the answers. Re-assess confidence internally.
4. If `confidence >= threshold`: stop the loop. Print: `grill-me complete | confidence=<N>%`
5. If still below threshold and rounds remain: continue to next round.
6. If max rounds exhausted: print `grill-me | max rounds reached | proceeding with confidence=<N>%` and continue.

**Context accumulation:** maintain a `grillContext` string that concatenates all Q&A pairs in order. Format:
```
Q: <question>
A: <user answer>
```

This string is passed to the workflow as `args.context` in Step 7. If grill-me was skipped, `args.context` = `""`.

**Grill-me must never:**
- Ask the same question twice
- Ask more than 3 questions per round
- Be verbose or explain why it is asking
- Pretend to be a different persona

### Step 6.6 — Plan cache lookup

If `config.planCache.enabled` is true:

1. Compute a `taskFingerprint`: lowercase the task, strip punctuation, take the first 60 chars + word count + detected persona keys joined. Example: `"write rest api java spring 12w java,dba"`.
2. Read `config.planCache.dir/cache.json` (use Read tool; if missing, treat as empty `{}`).
3. Scan entries for similarity: an entry is a hit if its stored fingerprint shares ≥ `config.planCache.similarityThreshold` of tokens with the current fingerprint (simple Jaccard on word sets is sufficient).
4. Filter out entries older than `config.planCache.ttlDays`.
5. If hit found: print `cache hit | fingerprint match — reusing leader plan (saved ~$X leader cost)`. Pass the cached plan as `args.cachedPlan` in Step 7 (the workflow skips the leader agent).
6. If no hit: pass `args.cachedPlan = null`. After the workflow completes (Step 8), write the new plan to cache: append `{ fingerprint, plan: result.plan, timestamp, models }` to `cache.json`. Prune entries > `config.planCache.maxEntries` (remove oldest).

Cache write uses the Write tool. Read with Read tool. Never expose cache internals to the user.

### Step 7 — Invoke Workflow

Call the `Workflow` tool with:
- `name: "fairytail-run"` (or `scriptPath` if you know the local install path)
- `args`:
  ```json
  {
    "task": "<cleaned task string>",
    "context": "<grillContext string, or empty string if grill-me skipped>",
    "banner": "",
    "models": { "leader": "...", "workers": "...", "summary": "..." },
    "orchestration": { "maxWorkers": N, "allowPeerContext": true, "workerEffort": "...", "leaderEffort": "...", "summaryEffort": "..." },
    "style": { "caveman": true, "rules": [...] },
    "personas": { "<key>": "<description>", ... },
    "cachedPlan": null
  }
  ```

Pass `args` as an actual JSON object, NOT a stringified value.

**IMPORTANT**: `args.banner` MUST be an empty string `""`. The banner was shown in Step 1. The workflow's Phase 0 will skip banner render when banner is empty.

### Step 8 — Await workflow completion

The workflow returns `{ banner, models, plan, workers, report }`. Render for the user:

1. Print `report.title` as an H2.
2. Print `report.tldr` verbatim.
3. Print each `report.sections[i]`: heading as H3, bullets as `-` list.
4. If `report.nextSteps` present: H3 "Next Steps" + bulleted list.
5. If `report.warnings` present: H3 "Warnings" + bulleted list.
6. Append a one-line footer: `models: leader=X workers=Y summary=Z | workers-executed=N`.

Keep the render itself caveman: no preamble like "Here is the report." Just render. Do NOT reprint the ASCII banner at the end — it was shown once at Step 1.

### Step 9 — Handle errors

- If Leader returns 0 workers → workflow throws, report error to user + ask to refine task.
- If Workflow permission denied by user → suggest they retype with keyword "ultracode" or install fairytail as trusted skill.
- If Workflow tool not available in the session → print caveman error `fairytail requires Workflow tool. Not available this session.` and stop.

## Notes

- Banner shows ONCE per invocation, only in Step 1.
- Confirmation step is MANDATORY. Never skip AskUserQuestion in Step 5, even if all tiers came from CLI flags (in that case present the overrides instead of auto-picks — user still confirms).
- Never expose worker prompts or intermediate reasoning to the user unless they ask. Report only.

## Embedded default config (used if no config file found)

```json
{
  "models": {
    "leader":  { "default": "fable",  "allowed": ["fable", "opus", "sonnet"] },
    "workers": { "default": "sonnet", "allowed": ["sonnet", "haiku", "opus", "fable"] },
    "summary": { "default": "haiku",  "allowed": ["haiku", "sonnet"] }
  },
  "autoSelect": {
    "enabled": true,
    "trivialWordThreshold": 30,
    "complexWordThreshold": 120,
    "mapping": { "trivial": "sonnet", "standard": "opus", "complex": "fable" }
  },
  "orchestration": {
    "maxWorkers": 6,
    "allowPeerContext": true,
    "workerEffort": "medium",
    "leaderEffort": "high",
    "summaryEffort": "low"
  },
  "style": {
    "caveman": true,
    "rules": [
      "No emoji",
      "No filler words (sure, great, certainly)",
      "Skip unnecessary articles/verbs",
      "Keywords + lists + symbols",
      "Preserve semantic completeness",
      "Terse but complete"
    ]
  }
}
```

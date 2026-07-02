# Fairytail — Architecture

## Overview

Fairytail is a **skill + workflow** system for Claude Code:

- **Skill** (`skills/fairytail/SKILL.md`) is the user-facing trigger. Parses `/fairytail <task>` and CLI-style flags, loads config, picks the leader model, invokes the workflow.
- **Workflow** (`workflows/fairytail.js`) is a deterministic JavaScript orchestration script executed by Claude Code's built-in `Workflow` tool. It runs the three-tier pipeline.

The skill exists so the user has a slash-command entry point; the workflow exists so orchestration is deterministic (no LLM in the driver seat for fan-out logic).

---

## Why this shape

Alternatives considered:

| Approach | Why not |
|---|---|
| Pure slash-command with prompt template | No fan-out, no per-agent model override, no cheap-tier summary |
| Multi-agent via nested `Agent` calls from a prompt | LLM decides fan-out — non-deterministic, no concurrency cap, no journal |
| Single agent with role-switching | Loses cost tiering; expensive tier does everything |

The workflow tool gives us: per-`agent()` model + effort overrides, `pipeline()` / `parallel()` primitives with automatic concurrency cap, JSON-Schema-validated structured outputs, journal/resume, shared token budget.

---

## Phases

```
+--------+   +------+   +--------------+   +-----------+
| Banner |-->| Plan |-->| Execute      |-->| Summarize |
+--------+   +------+   |  (N rounds)  |   +-----------+
                        +--------------+
```

### Phase 0 — Banner

`log()` prints the ASCII banner (fenced in a code block) plus a one-line config summary. Zero cost, purely presentational.

### Phase 1 — Plan (Leader)

Single `agent()` call at the reasoning tier. Uses `PLAN_SCHEMA`:

```json
{
  "rationale": "why this decomposition",
  "workers": [
    { "id": "w1", "role": "...", "prompt": "...", "dependsOn": [], "expectedArtifact": "..." }
  ],
  "expectedOutcome": "..."
}
```

Constraints:
- `maxItems` = `config.orchestration.maxWorkers`
- Each worker prompt must be **self-contained** (workers don't see other worker prompts, only their declared peers' outputs)

### Phase 2 — Execute (Workers)

The workflow builds **topological rounds** from `dependsOn` edges. Each round is a `parallel(...)` call. Workers in the same round run concurrently, capped by the runtime's concurrency limit.

For a worker with `dependsOn: [w1, w2]`:
- The prompt is injected with peer outputs (`summary`, `output`, `handoffNotes`) from `w1` and `w2`
- Only peers that have completed and returned non-null results are injected
- If a cycle is detected, the remaining pending workers are flushed in a single warning round

Each worker returns `WORKER_SCHEMA`:

```json
{
  "workerId": "w1",
  "summary": "1-3 line caveman",
  "output": "full artifact",
  "warnings": [],
  "handoffNotes": "for downstream / summarizer"
}
```

### Phase 3 — Summarize

Single `agent()` call at the cheap tier. Receives:
- Original task
- Leader rationale + expected outcome
- Every worker's summary + full output + warnings

Returns `REPORT_SCHEMA`:

```json
{
  "title": "...",
  "tldr": "2-4 line caveman",
  "sections": [{ "heading": "...", "bullets": ["..."] }],
  "artifacts": [{ "workerId": "...", "summary": "..." }],
  "nextSteps": [],
  "warnings": []
}
```

The skill renders this into the user's terminal — no post-processing by the calling agent beyond markdown formatting.

---

## Coordination model

Sub-agents in Claude Code cannot chat directly. Fairytail models coordination as:

1. **Leader defines the shape**: which workers exist and what they depend on
2. **Workflow enforces order**: topological rounds
3. **Peer context injection**: dependent workers see upstream artifacts as prompt context
4. **Shared workspace**: the workflow's `results` object is the single source of truth read across rounds

This is deliberate — it makes the system deterministic, replayable (workflow journal), and cheap. Agent-to-agent live chat would require a different substrate (e.g. an MCP message bus) and add non-determinism.

---

## Model tiering

| Tier | Purpose | Cost bias | Default |
|---|---|---|---|
| Leader | Reasoning, decomposition | High | `opus` |
| Workers | Parallel execution | Medium | `sonnet` |
| Summary | Aggregation | Low | `haiku` |

Model IDs are the harness-resolved short names (`opus`, `sonnet`, `haiku`, `fable`). The harness maps them to whatever version is current at session time. Fairytail does not pin exact versions — new capable models flow through automatically.

Effort tiers per phase come from `config.orchestration.{leaderEffort, workerEffort, summaryEffort}`.

---

## Auto-select algorithm

Runs only if user did NOT pass `--leader=` flag:

```
words = word_count(task)
if words < trivialThreshold:  leader = autoSelect.mapping.trivial   # sonnet
elif words <= complexThreshold: leader = autoSelect.mapping.standard # opus
else:                          leader = autoSelect.mapping.complex  # fable
```

The skill announces the pick in one line before invoking the workflow, so the user can `Ctrl+C` and retry with an explicit `--leader=`.

---

## Streaming (caveman)

The workflow calls `log()` at each phase transition and for round boundaries. No verbose intermediate outputs. Users see:

```
fairytail | leader=opus workers=sonnet summary=haiku maxWorkers=6
plan | workers=3 | api:backend REST endpoint | db:schema migration | tests:contract
execute | 2 round(s)
round 1/2 | api, db
round 2/2 | tests
done
```

Full artifacts and report land at the end.

---

## Failure modes

| Failure | Handling |
|---|---|
| Leader returns 0 workers | Workflow throws, skill reports error, asks for task refinement |
| Worker returns null (dead agent) | Result recorded as `FAILED` placeholder; downstream peers still get non-null peers |
| Cycle in dependsOn | Logged warning; remaining workers flushed in one round |
| Workflow tool unavailable | Skill prints one-line error, stops |
| Model id not in `allowed` | Skill refuses, prints allowed list |

---

## Extensibility

- **Add a phase**: append `phase('X')` blocks in `fairytail.js` and update `meta.phases`
- **Change tier defaults**: edit `fairytail.config.json` — no code change
- **Custom style rules**: edit `config.style.rules` — appended verbatim to every agent's prompt
- **Add a new tier** (e.g. "critic"): add another `agent()` call between Execute and Summarize; wire config

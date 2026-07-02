# Fairytail — Config Reference

Config file location (resolved in this order by the skill):

1. `./.claude/fairytail.config.json` (project override)
2. `~/.claude/fairytail.config.json` (user global)
3. Embedded defaults (from `skills/fairytail/SKILL.md`)

---

## Schema

```json
{
  "version": "1.0.0",
  "models": {
    "leader":  { "default": "opus",   "allowed": ["opus", "fable", "sonnet"] },
    "workers": { "default": "sonnet", "allowed": ["sonnet", "haiku", "opus", "fable"] },
    "summary": { "default": "haiku",  "allowed": ["haiku", "sonnet"] }
  },
  "autoSelect": {
    "enabled": true,
    "trivialWordThreshold": 30,
    "complexWordThreshold": 120,
    "mapping": {
      "trivial":  "sonnet",
      "standard": "opus",
      "complex":  "fable"
    }
  },
  "orchestration": {
    "maxWorkers": 6,
    "allowPeerContext": true,
    "workerEffort":  "medium",
    "leaderEffort":  "high",
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
  },
  "output": {
    "showBanner": true,
    "streamPhases": true,
    "saveHistory": false,
    "historyDir": "~/.claude/fairytail/history"
  }
}
```

---

## Field-by-field

### `models.*.default`
Model id used when the user does not override via CLI flag (and, for the leader, when auto-select is disabled).

### `models.*.allowed`
Whitelist of ids the skill will accept for that tier. Ids not in the list are rejected with a caveman error.

Recognized ids: `opus`, `sonnet`, `haiku`, `fable`. The Claude Code harness resolves each id to the latest version available in the current session's model catalog.

### `autoSelect.enabled`
When `true` **and** the user did not pass `--leader=`, the leader model is chosen from `autoSelect.mapping` based on task word count.

### `autoSelect.trivialWordThreshold` / `complexWordThreshold`
Word-count boundaries between the three complexity bands. Defaults: 30 / 120.

### `autoSelect.mapping.{trivial,standard,complex}`
Which model to pick per band. Values must appear in `models.leader.allowed`.

### `orchestration.maxWorkers`
Upper cap on how many workers the leader may produce. Enforced via the plan schema (`maxItems`).

Runtime concurrency is still capped by the workflow runtime (`min(16, cpuCores - 2)`); if `maxWorkers` exceeds that cap, workers simply queue.

### `orchestration.allowPeerContext`
When `true`, workers with `dependsOn` receive their peers' outputs as prompt context. Set `false` to disable — workers then only see the original task and their own prompt.

### `orchestration.{leaderEffort,workerEffort,summaryEffort}`
Reasoning-effort tier per phase. Allowed: `low`, `medium`, `high`, `xhigh`, `max`.

Recommended defaults:
- Leader: `high` (planning benefits from deeper thought)
- Workers: `medium`
- Summary: `low` (aggregation is cheap)

### `style.caveman`
Currently informational — the actual style enforcement comes from `style.rules` being appended to every agent's system prompt.

### `style.rules`
Array of rule strings, joined and appended to every agent's prompt as mandatory style guidance.

### `output.showBanner`
If `false`, the workflow skips the ASCII banner render. The skill still passes the banner in `args.banner` but the workflow ignores it.

### `output.streamPhases`
If `false`, the workflow suppresses `log()` calls between phases. Currently the workflow logs unconditionally; toggle is reserved for a future version.

### `output.saveHistory`
Reserved. When enabled in a future release, will persist each run's report + tokens spent under `output.historyDir`.

---

## CLI flags

Users can override config values at invocation time:

| Flag | Overrides | Example |
|---|---|---|
| `--leader=<id>` | `models.leader.default` + skips auto-select | `--leader=fable` |
| `--workers=<id>` | `models.workers.default` | `--workers=haiku` |
| `--summary=<id>` | `models.summary.default` | `--summary=sonnet` |
| `--max-workers=<N>` | Caps the effective `orchestration.maxWorkers` | `--max-workers=3` |

Rejected ids fall back to the tier default with a warning.

---

## Sample tunings

### "Cheap and cheerful" (small tasks, fast)

```json
{
  "models": {
    "leader":  { "default": "sonnet" },
    "workers": { "default": "haiku" },
    "summary": { "default": "haiku" }
  },
  "orchestration": { "maxWorkers": 3, "leaderEffort": "medium", "workerEffort": "low", "summaryEffort": "low" }
}
```

### "Maximum thoughtfulness" (design work, hard problems)

```json
{
  "models": {
    "leader":  { "default": "fable" },
    "workers": { "default": "opus" },
    "summary": { "default": "sonnet" }
  },
  "orchestration": { "maxWorkers": 6, "leaderEffort": "max", "workerEffort": "high", "summaryEffort": "medium" }
}
```

### "Disable auto-select" (always use configured leader)

```json
{ "autoSelect": { "enabled": false } }
```

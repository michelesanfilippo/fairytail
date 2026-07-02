export const meta = {
  name: 'fairytail-run',
  description: 'Internal orchestrator invoked by the fairytail skill. Do not run directly.',
  phases: [
    { title: 'Plan', detail: 'Leader generates structured action plan + worker specs' },
    { title: 'Execute', detail: 'Workers run in topo-ordered rounds with peer context' },
    { title: 'Summarize', detail: 'Summary agent produces caveman report' }
  ]
}

// ---------- args validation ----------
if (!args || typeof args !== 'object') {
  throw new Error('fairytail workflow requires args object: {task, models, orchestration, style, banner?}')
}
const task = args.task
if (!task || typeof task !== 'string' || task.trim().length === 0) {
  throw new Error('fairytail: args.task is required (non-empty string)')
}
const models = args.models || { leader: 'opus', workers: 'sonnet', summary: 'haiku' }
const orch = args.orchestration || { maxWorkers: 6, allowPeerContext: true, workerEffort: 'medium', leaderEffort: 'high', summaryEffort: 'low' }
const styleRules = (args.style && args.style.rules) || [
  'No emoji', 'No filler', 'Skip unnecessary articles/verbs', 'Keywords + lists + symbols', 'Terse but complete'
]
const banner = args.banner || ''
const grillContext = (args.context && args.context.trim()) ? args.context.trim() : ''
const personas = args.personas || {}
const cachedPlan = args.cachedPlan || null

const STYLE_APPEND = `\n\n---\nSTYLE (MANDATORY):\n${styleRules.map(r => `- ${r}`).join('\n')}\n`

// ---------- Phase 1: Leader plan ----------
phase('Plan')
log(`fairytail | leader=${models.leader} workers=${models.workers} summary=${models.summary} maxWorkers=${orch.maxWorkers}`)

// persona catalog string for leader prompt
const personaCatalogStr = (personas && Object.keys(personas).length > 0)
  ? '\n\nAVAILABLE WORKER PERSONAS (assign by matching concern to stack):\n' +
    Object.entries(personas).map(([k, v]) => `- ${k}: ${v}`).join('\n') +
    '\nAssign persona to each worker via the "role" field prefix, e.g. "java: design REST endpoint".\n'
  : ''

const PLAN_SCHEMA = {
  type: 'object',
  required: ['rationale', 'workers', 'expectedOutcome'],
  properties: {
    rationale: { type: 'string', description: 'Terse reasoning for chosen decomposition' },
    workers: {
      type: 'array',
      minItems: 1,
      maxItems: orch.maxWorkers,
      items: {
        type: 'object',
        required: ['id', 'role', 'prompt', 'expectedArtifact'],
        properties: {
          id: { type: 'string', description: 'Unique short id, e.g. w1, backend, db' },
          role: { type: 'string', description: 'One-line role, e.g. "backend API endpoint design"' },
          prompt: { type: 'string', description: 'Full instructions for this worker. Self-contained.' },
          dependsOn: {
            type: 'array',
            items: { type: 'string' },
            description: 'Worker ids that must complete first; their outputs are injected as peer context.'
          },
          expectedArtifact: { type: 'string', description: 'What the worker must produce (code, spec, plan, analysis, etc.)' }
        }
      }
    },
    expectedOutcome: { type: 'string', description: 'Terse description of aggregated deliverable' }
  }
}

// use cached plan if provided (plan cache hit from skill)
let plan
if (cachedPlan) {
  log('plan | cache hit — skipping leader agent')
  plan = cachedPlan
} else {
  const leaderPrompt = `You are TEAM LEADER for a multi-agent execution pipeline.
TASK:
${task}
${grillContext ? `\nUSER CONTEXT (collected via pre-flight interview — treat as authoritative requirements):\n${grillContext}\n` : ''}${personaCatalogStr}
DECOMPOSE into <=${orch.maxWorkers} concurrent workers. Each worker owns a distinct concern (e.g. backend, frontend, db, tests, docs, infra). Use dependsOn ONLY when a worker genuinely needs another's output. Prefer independent workers for parallelism.

When personas are provided: assign the most fitting persona to each worker by prefixing the role with the persona key, e.g. "java: design REST endpoint", "dba: schema migration". A worker may have no persona if no match is appropriate.

Return structured plan. Prompts must be self-contained: each worker sees only the ORIGINAL task, its own prompt, and outputs of its declared dependencies.
${STYLE_APPEND}`

  plan = await agent(leaderPrompt, {
    label: `leader:${models.leader}`,
    phase: 'Plan',
    model: models.leader,
    effort: orch.leaderEffort,
    schema: PLAN_SCHEMA
  })
}

if (!plan || !plan.workers || plan.workers.length === 0) {
  throw new Error('Leader returned no workers. Aborting.')
}

log(`plan | workers=${plan.workers.length} | ${plan.workers.map(w => w.id + ':' + w.role.slice(0, 30)).join(' | ')}`)

// ---------- Phase 2: Execute workers in topo rounds ----------
phase('Execute')

const WORKER_SCHEMA = {
  type: 'object',
  required: ['workerId', 'summary', 'output'],
  properties: {
    workerId: { type: 'string' },
    summary: { type: 'string', description: '1-3 line caveman summary of what was produced' },
    output: { type: 'string', description: 'Full artifact content (code, spec, analysis, plan). Markdown ok.' },
    warnings: { type: 'array', items: { type: 'string' }, description: 'Issues encountered, assumptions made' },
    handoffNotes: { type: 'string', description: 'Terse notes for downstream workers or summarizer' }
  }
}

function topoRounds(workers) {
  const byId = new Map(workers.map(w => [w.id, w]))
  const done = new Set()
  const rounds = []
  const pending = new Set(workers.map(w => w.id))
  let safety = workers.length + 2
  while (pending.size > 0 && safety-- > 0) {
    const round = []
    for (const id of pending) {
      const w = byId.get(id)
      const deps = w.dependsOn || []
      if (deps.every(d => done.has(d) || !byId.has(d))) round.push(w)
    }
    if (round.length === 0) {
      log(`warn | cycle detected in dependsOn; flushing remaining ${pending.size} workers in one round`)
      for (const id of pending) round.push(byId.get(id))
    }
    rounds.push(round)
    for (const w of round) { done.add(w.id); pending.delete(w.id) }
  }
  return rounds
}

const rounds = topoRounds(plan.workers)
log(`execute | ${rounds.length} round(s)`)

const results = {}
for (let r = 0; r < rounds.length; r++) {
  const round = rounds[r]
  log(`round ${r + 1}/${rounds.length} | ${round.map(w => w.id).join(', ')}`)
  const roundResults = await parallel(round.map(w => () => {
    const peerCtx = (w.dependsOn && w.dependsOn.length > 0 && orch.allowPeerContext)
      ? '\n\nPEER CONTEXT (outputs of your dependencies):\n' + w.dependsOn
          .filter(d => results[d])
          .map(d => `--- peer:${d} ---\n${results[d].summary}\n\n${results[d].output}${results[d].handoffNotes ? '\n\nHANDOFF:\n' + results[d].handoffNotes : ''}`)
          .join('\n\n')
      : ''
    // extract persona key from role prefix e.g. "java: design REST endpoint" -> "java"
    const personaMatch = w.role.match(/^([a-z]+):\s*/i)
    const personaKey = personaMatch ? personaMatch[1].toLowerCase() : null
    const personaDesc = personaKey && personas[personaKey] ? personas[personaKey] : null
    const personaBlock = personaDesc
      ? `\nYOUR PERSONA: ${personaDesc}\nOperate with the expertise and mindset of this role.\n`
      : ''

    const wPrompt = `You are WORKER "${w.id}" (role: ${w.role}).
${personaBlock}
ORIGINAL TASK:
${task}

YOUR SPECIFIC INSTRUCTIONS:
${w.prompt}

EXPECTED ARTIFACT:
${w.expectedArtifact}
${peerCtx}

Produce artifact + terse summary + handoff notes.
${STYLE_APPEND}`
    return agent(wPrompt, {
      label: `worker:${w.id}`,
      phase: 'Execute',
      model: models.workers,
      effort: orch.workerEffort,
      schema: WORKER_SCHEMA
    })
  }))
  for (let i = 0; i < round.length; i++) {
    const w = round[i]
    const res = roundResults[i]
    if (!res) {
      log(`worker ${w.id} | FAILED (null result)`)
      results[w.id] = { workerId: w.id, summary: 'FAILED', output: '(worker returned no output)', warnings: ['agent returned null'] }
    } else {
      results[w.id] = res
    }
  }
}

// ---------- Phase 3: Summary ----------
phase('Summarize')

const REPORT_SCHEMA = {
  type: 'object',
  required: ['title', 'tldr', 'sections'],
  properties: {
    title: { type: 'string' },
    tldr: { type: 'string', description: '2-4 line caveman tl;dr' },
    sections: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        required: ['heading', 'bullets'],
        properties: {
          heading: { type: 'string' },
          bullets: { type: 'array', minItems: 1, items: { type: 'string' } }
        }
      }
    },
    artifacts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['workerId', 'summary'],
        properties: {
          workerId: { type: 'string' },
          summary: { type: 'string' }
        }
      }
    },
    nextSteps: { type: 'array', items: { type: 'string' } },
    warnings: { type: 'array', items: { type: 'string' } }
  }
}

const workerDump = plan.workers.map(w => {
  const r = results[w.id]
  return `### ${w.id} (${w.role})\nSummary: ${r.summary}\n\nOutput:\n${r.output}${r.warnings && r.warnings.length ? '\n\nWarnings: ' + r.warnings.join('; ') : ''}`
}).join('\n\n')

const summaryPrompt = `You are SUMMARY agent. Produce final report for user.

ORIGINAL TASK:
${task}

LEADER RATIONALE:
${plan.rationale}

EXPECTED OUTCOME:
${plan.expectedOutcome}

WORKER OUTPUTS:
${workerDump}

Aggregate into caveman report. Sections should cover deliverables per concern + integration notes. Include artifacts list mapping each worker to its output summary. Flag warnings.
${STYLE_APPEND}`

const report = await agent(summaryPrompt, {
  label: `summary:${models.summary}`,
  phase: 'Summarize',
  model: models.summary,
  effort: orch.summaryEffort,
  schema: REPORT_SCHEMA
})

log('done')

return {
  banner,
  models,
  plan: { rationale: plan.rationale, workerCount: plan.workers.length, expectedOutcome: plan.expectedOutcome, workers: plan.workers },
  workers: Object.fromEntries(Object.entries(results).map(([id, r]) => [id, { summary: r.summary, output: r.output, warnings: r.warnings || [] }])),
  report
}

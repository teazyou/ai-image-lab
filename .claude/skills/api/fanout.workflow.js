export const meta = {
  name: 'api-fanout',
  description: 'fal.ai gen/edit — one Sonnet/high worker per (image × model) cell',
  phases: [{ title: 'Generate', detail: 'one worker per image × model, on Sonnet/high' }],
}

// Launched by the /api skill (SKILL.md), once per /api request, in the background.
// args: [{ argline: string, label?: string, skipFallback?: string[], fallbackRule?: string }, ...]
//   One cell per (image × selected model).
//   `argline` — a single-cell /api argument string: <one model flag> <option flags> <one image PATH> <prompt>
//   `skipFallback` — the OTHER models selected for this same image (selected set minus this cell's own model).
//                    Those already have their own cells, so this worker must not fall back onto them (avoids a
//                    duplicate). Fallback order is google ↔ openai then grok last; see agent.md.
//   `fallbackRule` — optional free-text override of agent.md's default fallback order for THIS cell only
//                    (e.g. "if openai fails or is content-policy-rejected, retry on google, then on grok").
//                    Passed to the worker as its own instruction line — NEVER concatenated into the prompt,
//                    so it can't leak into the image the model draws.
// args normally arrives as a real array, but some launch paths deliver it as a JSON string —
// accept both so the fan-out is robust to how the orchestrator passed it.
let cells = []
if (Array.isArray(args)) cells = args
else if (typeof args === 'string') { try { const p = JSON.parse(args); if (Array.isArray(p)) cells = p } catch (e) {} }
if (cells.length === 0) return { error: 'no cells in args', argsType: typeof args }

phase('Generate')
log('fanning out ' + cells.length + ' cell(s) on Sonnet/high')

// Each cell → one worker sub-agent, pinned to model: sonnet at effort: high (the whole point of the
// workflow: the plain Agent tool can't set effort, agent() can). The worker reads agent.md and does the job.
const results = await parallel(cells.map((c, i) => () => {
  const skip = Array.isArray(c.skipFallback) ? c.skipFallback : []
  const noFb = skip.length ? '\nDo not fall back to these models for this image: ' + skip.join(', ') + '.' : ''
  const fbRule = (typeof c.fallbackRule === 'string' && c.fallbackRule.trim())
    ? '\nFallback exceptional rule (OVERRIDES agent.md\'s default fallback order for this image): ' + c.fallbackRule.trim()
    : ''
  const prompt =
    'Read the worker spec at `.claude/skills/api/agent.md` and follow it EXACTLY to process this `/api` ' +
    'argument string:\n' + c.argline + '\n' +
    'You handle exactly this ONE model on this ONE image. Working dir is the repo root; resolve paths ' +
    'relative to it. Execute every step yourself.' + noFb + fbRule + '\n' +
    'Never edit any pre-existing repo file and never install or change anything on the system ' +
    '(parallel workers share the repo) — if a script or tool is broken, do NOT fix it yourself; ' +
    'report the blocker in your final result for the orchestrator (the main agent) to handle.\n' +
    'Report only your final result, once you are done.'
  return agent(prompt, {
    model: 'sonnet',
    effort: 'high',
    agentType: 'claude',
    label: c.label || ('cell ' + (i + 1)),
    phase: 'Generate',
  })
}))

return results

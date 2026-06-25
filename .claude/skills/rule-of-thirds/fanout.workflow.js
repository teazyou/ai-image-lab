export const meta = {
  name: 'rule-of-thirds-fanout',
  description: 'rule-of-thirds off-center shift — one Sonnet/high vision worker per image',
  phases: [{ title: 'Shift', detail: 'one worker per image, on Sonnet/high' }],
}

// Launched by the /rule-of-thirds skill (SKILL.md), once per request, in the background.
// args: [{ argline: string, label?: string }, ...] — one cell per input image.
//   `argline` — a single-cell /rule-of-thirds argument string: <-pct (optional)> <one image PATH>
// args normally arrives as a real array, but some launch paths deliver it as a JSON string —
// accept both so the fan-out is robust to how the orchestrator passed it.
let cells = []
if (Array.isArray(args)) cells = args
else if (typeof args === 'string') { try { const p = JSON.parse(args); if (Array.isArray(p)) cells = p } catch (e) {} }
if (cells.length === 0) return { error: 'no cells in args', argsType: typeof args }

phase('Shift')
log('fanning out ' + cells.length + ' image(s) on Sonnet/high')

// Each cell → one worker sub-agent, pinned to model: sonnet at effort: high (the whole point of the
// workflow: the plain Agent tool can't set effort, agent() can). The worker reads agent.md, uses vision
// to decide the facing direction, runs the mechanical shift, QAs, and reports.
const results = await parallel(cells.map((c, i) => () => {
  const prompt =
    'Read the worker spec at `.claude/skills/rule-of-thirds/agent.md` and follow it EXACTLY to process ' +
    'this `/rule-of-thirds` argument string:\n' + c.argline + '\n' +
    'You handle exactly this ONE image. Working dir is the repo root; resolve paths relative to it. ' +
    'Execute every step yourself.\n' +
    'Never edit any pre-existing repo file and never install or change anything on the system ' +
    '(parallel workers share the repo) — if a script or tool is broken, do NOT fix it yourself; ' +
    'report the blocker in your final result for the orchestrator (the main agent) to handle.\n' +
    'Report only your final result, once you are done.'
  return agent(prompt, {
    model: 'sonnet',
    effort: 'high',
    agentType: 'claude',
    label: c.label || ('image ' + (i + 1)),
    phase: 'Shift',
  })
}))

return results

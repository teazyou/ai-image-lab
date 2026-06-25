export const meta = {
  name: 'sharpen-definition-fanout',
  description: 'set 1080p + boost definition — one Sonnet/low mechanical worker per image',
  phases: [{ title: 'Sharpen', detail: 'one worker per image, on Sonnet/low' }],
}

// Launched by the /sharpen-definition skill (SKILL.md), once per request, in the background.
// args: [{ argline: string, label?: string }, ...] — one cell per input image.
//   `argline` — a single-cell /sharpen-definition argument string: <one image PATH>
// args normally arrives as a real array, but some launch paths deliver it as a JSON string —
// accept both so the fan-out is robust to how the orchestrator passed it.
let cells = []
if (Array.isArray(args)) cells = args
else if (typeof args === 'string') { try { const p = JSON.parse(args); if (Array.isArray(p)) cells = p } catch (e) {} }
if (cells.length === 0) return { error: 'no cells in args', argsType: typeof args }

phase('Sharpen')
log('fanning out ' + cells.length + ' image(s) on Sonnet/low')

// Each cell → one worker sub-agent, pinned to model: sonnet at effort: low. The job is purely
// mechanical (run the sibling script — no vision, no QA), so low effort is plenty; we still fan out
// one worker per image for isolation and parallelism. The worker reads agent.md and runs the pipeline.
const results = await parallel(cells.map((c, i) => () => {
  const prompt =
    'Read the worker spec at `.claude/skills/sharpen-definition/agent.md` and follow it EXACTLY to process ' +
    'this `/sharpen-definition` argument string:\n' + c.argline + '\n' +
    'You handle exactly this ONE image. Working dir is the repo root; resolve paths relative to it. ' +
    'It is purely mechanical — run the sibling script, do NOT view or QA any image.\n' +
    'Report only your final result, once you are done.'
  return agent(prompt, {
    model: 'sonnet',
    effort: 'low',
    agentType: 'claude',
    label: c.label || ('image ' + (i + 1)),
    phase: 'Sharpen',
  })
}))

return results

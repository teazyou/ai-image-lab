export const meta = {
  name: 'sharpen-definition-fanout',
  description: 'set 1080p + boost definition — split images across ≤N sequential workers (≤N generations at once)',
  phases: [{ title: 'Sharpen', detail: '≤N workers in parallel, each its group sequentially, on Sonnet/low' }],
}

// ─────────────────────────────────────────────────────────────────────────────
// TWEAK ME — the only knob. `total_sub_agents` = how many worker sub-agents run
// in parallel = how many groups the images are split into = the MAX number of
// generations in flight at once. Each worker processes its group one image at a
// time (sequentially), so concurrent Real-ESRGAN runs never exceed this number.
// Raise it only if this machine's RAM can take more at once; lower it if even
// this many is too heavy. Change just this one line.
const total_sub_agents = 3
// ─────────────────────────────────────────────────────────────────────────────

// Launched by the /sharpen-definition skill (SKILL.md), once per request, in the background.
// args: [{ argline: string, label?: string }, ...] — one cell per input image (a FLAT list).
//   `argline` — a single-cell /sharpen-definition argument string: <one image PATH>.
// args normally arrives as a real array, but some launch paths deliver it as a JSON string —
// accept both so the fan-out is robust to how the orchestrator passed it.
let cells = []
if (Array.isArray(args)) cells = args
else if (typeof args === 'string') { try { const p = JSON.parse(args); if (Array.isArray(p)) cells = p } catch (e) {} }
if (cells.length === 0) return { error: 'no cells in args', argsType: typeof args }

// RAM safety: more than `total_sub_agents` Real-ESRGAN runs at once can exhaust this machine. So
// instead of one worker per image (which `parallel()` would run up to ~CPU-count at a time), we
// split the images into at most `total_sub_agents` balanced groups and run ONE worker per group.
// The ≤N workers run in parallel (parallel() over ≤N thunks → ≤N concurrent), and each worker
// processes its group one image at a time — so at most `total_sub_agents` generations are ever live.
const k = Math.max(1, Math.min(total_sub_agents, cells.length))

// Balanced contiguous split into k groups (e.g. with k=3: 51 → 17/17/17, 50 → 17/17/16, 5 → 2/2/1).
const groups = []
const base = Math.floor(cells.length / k)
let rem = cells.length % k
let idx = 0
for (let g = 0; g < k; g++) {
  const size = base + (rem > 0 ? 1 : 0)
  if (rem > 0) rem--
  groups.push(cells.slice(idx, idx + size))
  idx += size
}

phase('Sharpen')
log('splitting ' + cells.length + ' image(s) across ' + k + ' sequential worker(s) on Sonnet/low (cap total_sub_agents=' + total_sub_agents + ')')

// One worker per group → at most `total_sub_agents` run concurrently; each loops its group
// sequentially. The job is purely mechanical (run the sibling script — no vision, no QA), so low
// effort is plenty. The worker reads agent.md and runs the pipeline on each path it is handed.
const results = await parallel(groups.map((group, gi) => () => {
  const paths = group.map((c) => c.argline).join('\n')
  const prompt =
    'Read the worker spec at `.claude/skills/sharpen-definition/agent.md` and follow it EXACTLY to ' +
    'process this GROUP of `/sharpen-definition` image paths — one per line:\n' + paths + '\n' +
    'Process them STRICTLY ONE AT A TIME, sequentially: run the sibling script on one image, wait for ' +
    'it to finish, THEN move to the next. NEVER run two at once / never batch multiple commands in one ' +
    'step / never background them — running more than one Real-ESRGAN at once is what this split exists ' +
    'to prevent (it exhausts RAM). Working dir is the repo root; resolve paths relative to it. It is ' +
    'purely mechanical — run the sibling script, do NOT view or QA any image. Report only your final ' +
    'aggregated result (one line per image), once every image in your group is done.'
  return agent(prompt, {
    model: 'sonnet',
    effort: 'low',
    agentType: 'claude',
    label: 'group ' + (gi + 1) + '/' + k + ' (' + group.length + ' img)',
    phase: 'Sharpen',
  })
}))

return results

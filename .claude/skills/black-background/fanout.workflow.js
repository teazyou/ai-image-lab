export const meta = {
  name: 'black-background-fanout',
  description: 'subject → solid black — chop images into groups of ≤max_images_per_groups, run them through a pool of ≤max_parallels_agents sequential vision+QA workers',
  phases: [{ title: 'Cutout', detail: 'pool of ≤max_parallels_agents workers, each its group one image at a time, on Sonnet/high' }],
}

// ─────────────────────────────────────────────────────────────────────────────
// TWEAK ME — two knobs.
//
//   max_parallels_agents — how many worker sub-agents run AT ONCE (the concurrency
//   cap). Each running worker does ONE rembg cutout at a time. Measured peak RSS
//   (one rembg at a time, M4 Max): u2net_human_seg ≈ 2.1 GB, isnet-anime ≈ 4.5 GB,
//   birefnet-general ≈ 14.2 GB (worst case, resolution-independent). So worst-case
//   peak RAM ≈ max_parallels_agents × ~14 GB — default 2 ⇒ ~28 GB, safe on this
//   48 GB Mac (lighter models use far less). Raise only if RAM allows. The
//   `-parallels=N` argument overrides this per run (1 = strictly one agent at a time).
//
//   max_images_per_groups — how many images ONE sub-agent is handed (it processes
//   them sequentially, one at a time). Bounds a single worker's workload so its
//   context window doesn't get bloated. Images are chopped into groups of this size;
//   number of groups = ceil(total images / max_images_per_groups).
const max_parallels_agents = 3
const max_images_per_groups = 10
// ─────────────────────────────────────────────────────────────────────────────

// Launched by the /black-background skill (SKILL.md), once per request, in the background.
// args: { cells: [{ argline, label? }, ...], parallels?: number }
//   cells     — one cell per input image (a FLAT list); `argline` = a single image PATH.
//   parallels — optional override for max_parallels_agents (from the `-parallels=N` arg).
// Be robust to a few shapes: the object above, a bare cells array, or a JSON string of either.
let cells = [], parallelsOverride = null
if (Array.isArray(args)) {
  cells = args
} else if (args && typeof args === 'object') {
  if (Array.isArray(args.cells)) cells = args.cells
  if (typeof args.parallels === 'number') parallelsOverride = args.parallels
} else if (typeof args === 'string') {
  try {
    const p = JSON.parse(args)
    if (Array.isArray(p)) cells = p
    else if (p && typeof p === 'object') {
      if (Array.isArray(p.cells)) cells = p.cells
      if (typeof p.parallels === 'number') parallelsOverride = p.parallels
    }
  } catch (e) {}
}
if (cells.length === 0) return { error: 'no cells in args', argsType: typeof args }

// Concurrency = the per-run override if given, else the default knob; never below 1.
const concurrency = Math.max(1, Math.floor(parallelsOverride || max_parallels_agents))

// Chop the flat image list into contiguous groups of at most `max_images_per_groups`
// (e.g. 53 images, cap 10 → six groups: 10, 10, 10, 10, 10, 3).
const groupSize = Math.max(1, max_images_per_groups)
const groups = []
for (let i = 0; i < cells.length; i += groupSize) groups.push(cells.slice(i, i + groupSize))

// Pool size: at most `concurrency` workers run at once (and never more than there are groups).
const poolSize = Math.max(1, Math.min(concurrency, groups.length))

phase('Cutout')
log(cells.length + ' image(s) → ' + groups.length + ' group(s) of ≤' + groupSize +
    ' → pool of ' + poolSize + ' worker(s) (max_parallels_agents=' + max_parallels_agents +
    (parallelsOverride ? ', -parallels=' + parallelsOverride : '') + '; up to ~14 GB RAM each, ~' +
    (poolSize * 14) + ' GB worst-case peak)')

// One sub-agent per group, pinned to model: sonnet / effort: high — each image needs vision (pick the
// rembg model) + QA. Each worker processes its group strictly one image at a time.
function runGroup(group, gi) {
  const paths = group.map((c) => c.argline).join('\n')
  const prompt =
    'Read the worker spec at `.claude/skills/black-background/agent.md` and follow it EXACTLY to ' +
    'process this GROUP of `/black-background` image paths — one per line:\n' + paths + '\n' +
    'Process them STRICTLY ONE AT A TIME, sequentially: pick the rembg model (vision), run the sibling ' +
    'cutout-onto-black script on one image, QA it, clean up, THEN move to the next. NEVER run two ' +
    'cutouts at once / never batch multiple bg_to_color.sh calls in one step / never background them — ' +
    'rembg birefnet can use ~14 GB RAM, so two in flight inside one worker would blow the budget. ' +
    'Working dir is the repo root; resolve paths relative to it. Each image DOES need vision (model ' +
    'pick) + QA per agent.md. Creating NEW files is fine (the `outputs/` result, the `.cache/` cutout, ' +
    'and temp peek copies). Never edit any pre-existing repo file and never install or change anything ' +
    'on the system (parallel workers share the repo) — if the script or a tool is broken, do NOT fix it ' +
    'yourself; mark the affected image(s) FAILURE and report the blocker in your final result for the ' +
    'orchestrator (the main agent) to handle. Report only your final aggregated result (one line per ' +
    'image), once every image in your group is done.'
  return agent(prompt, {
    model: 'sonnet',
    effort: 'high',
    agentType: 'claude',
    label: 'group ' + (gi + 1) + '/' + groups.length + ' (' + group.length + ' img)',
    phase: 'Cutout',
  })
}

// Fixed-size worker pool: `poolSize` loops share a cursor; each takes the next waiting group, runs
// it to completion, then grabs the next — so at most `poolSize` groups are ever in flight, and as
// soon as a worker finishes its group it starts the next queued one. (Single-threaded JS: the
// synchronous `nextIdx++` hands each group to exactly one worker — no race.)
const results = new Array(groups.length)
let nextIdx = 0
async function poolWorker() {
  while (true) {
    const gi = nextIdx++
    if (gi >= groups.length) return
    results[gi] = await runGroup(groups[gi], gi)
  }
}
const pool = []
for (let w = 0; w < poolSize; w++) pool.push(poolWorker())
await Promise.all(pool)

return results

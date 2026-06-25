---
name: sharpen-definition
description: Set an image to 1080p (if not already) and increase/sharpen its definition. Works on one image or a whole folder. Chops the images into groups of ≤`max_images_per_groups` (default 10) and runs them through a pool of ≤`max_parallels_agents` (default 2) background workers — at most that many run at once; when one finishes its group it picks up the next waiting group. Each worker processes its group sequentially, one image at a time. One worker ≈ ~8 GB RAM, so the default holds peak ≈ 16 GB. Optional `-parallels=N` overrides the pool size for a run (1 = one at a time). Each worker is a Sonnet sub-agent running the mechanical pipeline (Real-ESRGAN 4× → downscale to 1080p → unsharp). Local-only, no vision.
argument-hint: "<image-or-folder-path> [-parallels=N]"
---

# /sharpen-definition — orchestrate "set 1080p + sharpen definition" through a bounded worker pool

You are the **orchestrator** for `/sharpen-definition`. Your only job: fan the request out into a
**background dynamic Workflow** that **chops the images into groups and runs them through a bounded
pool of worker sub-agents** — on Sonnet at **high** effort, each following the bundled `agent.md` —
then relay their results. **You never view, edit, or QA any image, and you never read `agent.md`
yourself** — the workers own that. (This skill authorizes the Workflow tool; see step 3.)

**How the Workflow splits & schedules the work (two knobs):**
- It chops the flat image list into **groups of at most `max_images_per_groups` images** (default
  **10**) — so #groups = ceil(#images / 10). Bounding a group keeps any one worker's context window
  from getting bloated.
- It runs those groups through a **pool of at most `max_parallels_agents` workers** (default **2**) —
  at most that many run **at once**; **when a worker finishes its group it immediately picks up the
  next waiting group**, until all groups are done. Each worker processes its own group **strictly one
  image at a time (sequentially)**.
- **RAM:** one running worker does one Real-ESRGAN 4× job at a time ≈ **~8 GB RAM** (measured). So peak
  ≈ `max_parallels_agents × ~8 GB` — default 2 ⇒ **~16 GB**, safe on this 48 GB Mac. This is exactly
  why the pool is bounded: an unbounded fan-out would run ~a dozen at once (~100 GB) and crash.

> **Tweakable knobs** — both are single constants at the **top of
> `.claude/skills/sharpen-definition/fanout.workflow.js`**: `max_parallels_agents` (default 2, the
> concurrency/RAM cap) and `max_images_per_groups` (default 10, the per-worker workload cap). Change a
> **one line** there to retune; nothing else needs editing. The **`-parallels=N`** argument overrides
> `max_parallels_agents` for a single run.

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. **Do NOT read `agent.md` or
`fanout.workflow.js`** — both are complete; you only ever pass their *path* (and the `args`), never their
contents, so opening them just burns tokens. Likewise don't read `lab/docs/`, `lab/wikis/`, or
`CLAUDE.md`. Open any of these **only if** launching the Workflow throws an error you must diagnose.

1. **Parse args (cheap text only).**
   - **`-parallels=N`** (optional) — if a token matches `-parallels=<integer ≥1>` (also accept
     `--parallels=N`), pull it out as the pool-size override `N`; if absent, there is no override (the
     Workflow uses its `max_parallels_agents` default). `-parallels=1` = strictly one worker at a time.
   - **Input** = the remaining bare positional (strip surrounding quotes; keep a trailing `/`). No other
     flags — every input gets the same fixed 1080p + sharpen pipeline.
2. **Build the image list → the cells.**
   - Input resolves (`test -e`) to a **file** → list is `[that file]`; to a **directory** → list is
     **every image in it** (`*.png *.jpg *.jpeg *.webp`, non-recursive — actually list them). Empty
     folder, unresolved path, or no input token → tell the user (ask for an image or folder path), STOP
     (no worker).
   - **One cell per image**, an object `{ argline, label }` — build the **flat** per-image list; the
     Workflow itself chops it into groups and schedules the pool (you do **not** group or schedule):
     - `argline` — a single-cell `/sharpen-definition` argument string: `"<that ONE image PATH>"`.
     - `label` — the image stem (shown in the progress display).
3. **Launch a background dynamic Workflow** — this skill **authorizes the Workflow tool**. Call
   `Workflow({ scriptPath: ".claude/skills/sharpen-definition/fanout.workflow.js", args: { cells: <the
   cell array>, parallels: <N or omit> } })` — **pass the path as-is; do NOT open/read the script** (it's
   complete). Pass `cells` as a real JSON array; include `parallels` **only if** `-parallels=N` was given.
   The bundled script chops the cells into groups of ≤`max_images_per_groups` and runs them through a
   pool of ≤(`parallels` or `max_parallels_agents`) sub-agents on `model: sonnet` at `effort: high` (the
   job is mechanical — no vision); each reads `agent.md` and runs the pipeline on **each image in its
   group sequentially**, then reports. The Workflow runs in the **background** and returns immediately:
   **one Workflow per `/sharpen-definition` request**, so you stay free to chain.
4. **Acknowledge in one line**, e.g. `▶ launched workflow — 53 images → 6 groups of ≤10, pool of 2
   workers (~16 GB peak), set 1080p + sharpen`. State the image count and, if you can, the group/pool
   numbers (groups = ceil(images/10); pool = the override N if given, else 2 capped to #groups). The live
   counts also show in the workflow progress. Write nothing else.
5. **Stay ready & chain.** Treat any follow-up that names an input as another job — re-run steps 1–4 for
   each; each fires its own background Workflow (they run concurrently — note that two concurrent jobs
   each at the pool cap can double the live RAM). Plain non-job messages you just answer normally.
6. **Relay, don't QA.** When a Workflow finishes, the harness notifies you with its aggregated results
   (one report per group, each covering the images in that group) — relay them **compactly** (one small
   row per image — image · output path · saved dimensions). Add no QA, previews, or commentary of your
   own. (`outputs/` is git-ignored ⇒ nothing to commit unless the script/skill itself changed.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.
Inputs are never modified in place; results land in `outputs/<stem>_1080p-sharp.png`.

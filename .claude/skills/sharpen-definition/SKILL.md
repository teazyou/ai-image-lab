---
name: sharpen-definition
description: Set an image to 1080p (if not already) and increase/sharpen its definition. Works on one image or a whole folder. Splits the images across at most `total_sub_agents` (default 3) background workers running in parallel; each worker processes its share sequentially, one image at a time, so at most that many generations ever run at once (RAM-safe). Each worker is a Sonnet sub-agent running the mechanical pipeline (Real-ESRGAN 4× → downscale to 1080p → unsharp). Local-only, no vision.
argument-hint: "<image-or-folder-path>"
---

# /sharpen-definition — orchestrate "set 1080p + sharpen definition" across ≤`total_sub_agents` sequential workers

You are the **orchestrator** for `/sharpen-definition`. Your only job: fan the request out into a
**background dynamic Workflow** that **splits the images into at most `total_sub_agents` groups and
spawns one worker sub-agent per group** — on Sonnet at **low** effort, each following the bundled
`agent.md` — then relay their results. The ≤`total_sub_agents` workers run in parallel, but **each
worker processes its group strictly one image at a time (sequentially)**, so **at most
`total_sub_agents` generations ever run at once** — that cap is the whole point (more concurrent
Real-ESRGAN runs exhaust this machine's RAM). Each worker runs the **purely mechanical** pipeline
itself (set 1080p → boost definition). **You never view, edit, or QA any image, and you never read
`agent.md` yourself** — the workers own that. (This skill authorizes the Workflow tool; see step 3.)

> **Tweakable knob — `total_sub_agents`:** a single constant at the **top of
> `.claude/skills/sharpen-definition/fanout.workflow.js`** (default **3**). It sets the number of
> parallel workers = number of image groups = the hard cap on simultaneous generations. To run
> more/fewer at once, change that **one line** — nothing else needs editing.

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. **Do NOT read `agent.md` or
`fanout.workflow.js`** — both are complete; you only ever pass their *path* (and the `args`), never their
contents, so opening them just burns tokens. Likewise don't read `lab/docs/`, `lab/wikis/`, or
`CLAUDE.md`. Open any of these **only if** launching the Workflow throws an error you must diagnose.

1. **Parse args (cheap text only).**
   - **Input** = the bare positional (strip surrounding quotes; keep a trailing `/`). There are no other
     flags — every input gets the same fixed 1080p + sharpen pipeline.
2. **Build the image list → the cells.**
   - Input resolves (`test -e`) to a **file** → list is `[that file]`; to a **directory** → list is
     **every image in it** (`*.png *.jpg *.jpeg *.webp`, non-recursive — actually list them). Empty
     folder, unresolved path, or no input token → tell the user (ask for an image or folder path), STOP
     (no worker).
   - **One cell per image**, an object `{ argline, label }` — build the **flat** per-image list; the
     Workflow itself splits it into ≤`total_sub_agents` balanced groups (you do **not** group them):
     - `argline` — a single-cell `/sharpen-definition` argument string: `"<that ONE image PATH>"`.
     - `label` — the image stem (shown in the progress display).
3. **Launch a background dynamic Workflow** — this skill **authorizes the Workflow tool**. Call
   `Workflow({ scriptPath: ".claude/skills/sharpen-definition/fanout.workflow.js", args: <the cell list as
   a real JSON array> })` — **pass the path as-is; do NOT open/read the script** (it's complete). The
   bundled script **splits the cells into at most `total_sub_agents` balanced groups and fans out one
   sub-agent per group on `model: sonnet` at `effort: low`** (the job is mechanical — no vision); each
   reads `agent.md` and runs the pipeline on **each image in its group sequentially**, then reports. So
   no matter how many images you pass, **at most `total_sub_agents` run at once**. The Workflow runs in
   the **background** and returns immediately: **one Workflow per `/sharpen-definition` request**, so you
   stay free to chain.
4. **Acknowledge in one line**, e.g. `▶ launched workflow — 51 images across ≤3 sequential workers
   (cap = total_sub_agents), set 1080p + sharpen`. State the image count; describe the pool as
   ≤`total_sub_agents` sequential workers (the live worker count shows in the workflow progress). Write
   nothing else.
5. **Stay ready & chain.** Treat any follow-up that names an input as another job — re-run steps 1–4 for
   each; each fires its own background Workflow (they run concurrently). Plain non-job messages you just
   answer normally.
6. **Relay, don't QA.** When a Workflow finishes, the harness notifies you with its aggregated results
   (the ≤`total_sub_agents` group workers each report the images in their group) — relay them
   **compactly** (one small row per image — image · output path · saved dimensions). Add no QA, previews,
   or commentary of your own. (`outputs/` is git-ignored ⇒ nothing to commit unless the script/skill
   itself changed.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.
Inputs are never modified in place; results land in `outputs/<stem>_1080p-sharp.png`.

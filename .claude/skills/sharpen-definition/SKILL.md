---
name: sharpen-definition
description: Set an image to 1080p (if not already) and increase/sharpen its definition. Works on one image or a whole folder. Fans out one background worker per image — each a Sonnet sub-agent that runs the mechanical pipeline (Real-ESRGAN 4× → downscale to 1080p → unsharp). Local-only, no vision.
argument-hint: "<image-or-folder-path>"
---

# /sharpen-definition — orchestrate "set 1080p + sharpen definition", one worker per image

You are the **orchestrator** for `/sharpen-definition`. Your only job: fan the request out into a
**background dynamic Workflow** that spawns **one worker sub-agent per input image** — on Sonnet at
**low** effort, each following the bundled `agent.md` — then relay their results. Each worker runs the
**purely mechanical** pipeline itself (set 1080p → boost definition). **You never view, edit, or QA any
image, and you never read `agent.md` yourself** — the workers own that. (This skill authorizes the
Workflow tool; see step 3.)

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
   - **One cell per image**, an object `{ argline, label }`:
     - `argline` — a single-cell `/sharpen-definition` argument string: `"<that ONE image PATH>"`.
     - `label` — the image stem (shown in the progress display).
3. **Launch a background dynamic Workflow** — this skill **authorizes the Workflow tool**. Call
   `Workflow({ scriptPath: ".claude/skills/sharpen-definition/fanout.workflow.js", args: <the cell list as
   a real JSON array> })` — **pass the path as-is; do NOT open/read the script** (it's complete). The
   bundled script fans out **one sub-agent per image on `model: sonnet` at `effort: low`** (the job is
   mechanical — no vision); each reads `agent.md`, runs the pipeline on its `argline`, and reports. The
   Workflow runs in the **background** and returns immediately: **one Workflow per `/sharpen-definition`
   request**, so you stay free to chain.
4. **Acknowledge in one line**, e.g. `▶ launched workflow — 5 workers (one per image), set 1080p + sharpen`.
   Write nothing else.
5. **Stay ready & chain.** Treat any follow-up that names an input as another job — re-run steps 1–4 for
   each; each fires its own background Workflow (they run concurrently). Plain non-job messages you just
   answer normally.
6. **Relay, don't QA.** When a Workflow finishes, the harness notifies you with its aggregated results —
   relay them **compactly** (one small row per image — image · output path · saved dimensions). Add no QA,
   previews, or commentary of your own. (`outputs/` is git-ignored ⇒ nothing to commit unless the
   script/skill itself changed.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.
Inputs are never modified in place; results land in `outputs/<stem>_1080p-sharp.png`.

---
name: rule-of-thirds
description: Shift a subject off-center so it looks into the open space (rule-of-thirds / lead-room look). Fans out one background worker per image — each a Sonnet/xhigh vision sub-agent that decides left|right from the subject's facing, then shifts it that % of the image width. Local-only (ImageMagick).
argument-hint: "[-20|-30] <image-or-folder-path>"
---

# /rule-of-thirds — orchestrate a face-aware off-center shift, one worker per image

You are the **orchestrator** for `/rule-of-thirds`. Your only job: fan the request out into a
**background dynamic Workflow** that spawns **one worker sub-agent per input image** — on Sonnet at
**xhigh** effort, each following the bundled `agent.md` — then relay their results. Each worker does the
vision (which way the subject faces → which way to shift), the mechanical shift, and the QA itself.
**You never view, shift, or QA any image, and you never read `agent.md` yourself** — the workers own
that. (This skill authorizes the Workflow tool; see step 3.)

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. **Do NOT read `agent.md` or
`fanout.workflow.js`** — both are complete; you only ever pass their *path* (and the `args`), never their
contents, so opening them just burns tokens. Likewise don't read `lab/docs/`, `lab/wikis/`, or
`CLAUDE.md`. Open any of these **only if** launching the Workflow throws an error you must diagnose.

1. **Parse args (cheap text only).**
   - **Percent** = `20` unless a `-N` token (any `-<number>`, e.g. `-20`, `-30`) is present → use that N.
   - **Input** = the remaining bare positional (strip surrounding quotes; keep a trailing `/`).
2. **Build the image list → the cells.**
   - Input resolves (`test -e`) to a **file** → list is `[that file]`; to a **directory** → list is
     **every image in it** (`*.png *.jpg *.jpeg *.webp`, non-recursive — actually list them). Empty
     folder, unresolved path, or no input token → tell the user (ask for an image or folder path), STOP
     (no worker).
   - **One cell per image**, an object `{ argline, label }`:
     - `argline` — a single-cell `/rule-of-thirds` argument string: `-<pct> "<that ONE image PATH>"`.
     - `label` — the image stem (shown in the progress display).
3. **Launch a background dynamic Workflow** — this skill **authorizes the Workflow tool**. Call
   `Workflow({ scriptPath: ".claude/skills/rule-of-thirds/fanout.workflow.js", args: <the cell list as a
   real JSON array> })` — **pass the path as-is; do NOT open/read the script** (it's complete). The
   bundled script fans out **one sub-agent per image on `model: sonnet` at `effort: xhigh`** (vision to
   read the facing, then the mechanical shift); each reads `agent.md`, processes its `argline`, and
   reports. The Workflow runs in the **background** and returns immediately: **one Workflow per
   `/rule-of-thirds` request**, so you stay free to chain.
4. **Acknowledge in one line**, e.g. `▶ launched workflow — 5 workers (one per image), shift 20%`.
   Write nothing else.
5. **Stay ready & chain.** Treat any follow-up that names an input as another job — re-run steps 1–4 for
   each; each fires its own background Workflow (they run concurrently). Plain non-job messages you just
   answer normally.
6. **Relay, don't QA.** When a Workflow finishes, the harness notifies you with its aggregated results —
   relay them **compactly** (one small row per image — image · direction chosen · output path, plus any
   `clamped` note; batch them rather than narrating each). Add no QA, previews, or commentary of your
   own. (`outputs/` is git-ignored ⇒ nothing to commit unless the script/skill itself changed.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.
Inputs are never modified in place; results land in `outputs/<stem>_thirds-<dir><pct>.png`.

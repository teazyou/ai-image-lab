# /sharpen-definition worker — set a GROUP of images to 1080p + boost definition (sequentially), then report

You were handed a **GROUP of image PATHS** — they appear in your task prompt, **one per line**. Process
the whole group yourself; it is **purely mechanical, no visual judgment needed**. (The orchestrator
splits the request into at most a few groups and runs one worker per group in parallel — you own ONE
group, and you process it **strictly one image at a time**.)

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here. Working dir = repo root; resolve paths relative to it.

**Parallel-safe hard limits (other workers run at the same time — never touch anything shared).**
- **Never modify, overwrite, move, or delete any pre-existing file** — scripts (incl. the sibling
  sharpen script), skills, docs, configs, the tool/lab setup — **even to fix a bug or a broken script.**
  (Creating NEW files is fine: the script's own `outputs/` results and `.cache/` scratch.)
- **Never install or upgrade tools/packages/models, and never change the system or environment.**
- Blocked by something you can't clear within these limits (broken/missing script, missing dependency,
  a tool needing reinstall)? **Don't fix it yourself** — record those images as FAILURE and **report it
  to the orchestrator in your final report**, describing the problem precisely so the main agent (the
  one who launched this workflow) can fix it. (A per-image failure you still skip past per step 2.)

**What it does (per image):** sets the image to **1080p** (1080px tall, aspect ratio preserved — a
16:9 input → 1920×1080) and **sharpens its definition** via a Real-ESRGAN 4× upscale → Lanczos
downscale to 1080p → light unsharp. The whole pipeline is the sibling script; you just run it, once
per image.

## 1 — parse your group
Your task prompt contains a **list of image PATHS, one per line** (strip any surrounding quotes). That
list is your group; keep its order.

## 2 — run the pipeline ONE IMAGE AT A TIME (strictly sequential — this is the whole point)
For each path in your group, in order:
`.claude/skills/sharpen-definition/sharpen_definition.sh -i "<img>"`

- **Exactly one generation in flight at a time.** Issue the command for the next image **only after the
  previous one has fully finished**. **Never** put more than one sharpen command in a single step,
  **never** use `&` / background them, **never** run them in parallel. Each Real-ESRGAN run uses **~8 GB
  RAM**, so two in flight inside one worker would blow the memory budget — running one at a time is the
  whole reason the work is split this way. One image → wait → next image.
- Each invocation Real-ESRGAN 4×-upscales on MPS (~8s for a 1080p input), downscales to 1080p with
  Lanczos, applies a light unsharp, writes `outputs/<stem>_1080p-sharp.png`, and cleans its own
  `.cache/` scratch. It never modifies the input in place. **The script is the entire job** for that
  image — no extra ImageMagick steps.
- **Continue on failure.** If a path doesn't resolve or the script exits non-zero, record that image as
  a FAILURE (keep its stderr tail) and **move on to the next** — one bad image must not stop the rest of
  your group.
- **Process every image in your group before you report.** Don't stop early or summarize partway.

## 3 — do NOT review the results
This task needs **no vision and no QA**. **Do not open, view, or inspect** any input or output — the
pipeline is deterministic and already validated. For each image just confirm the script exited 0 and
printed its `saved: …` line. Spend zero vision tokens.

## Report
Work silently through your whole group, then **report only once — your final message, after every image
in your group is done** — with **one line per image**:
- `SUCCESS <final output path>` plus the saved dimensions the script printed, **or**
- `FAILURE <error>` for that image (path didn't resolve, or the script exited non-zero — include its
  stderr tail).

(The orchestrator aggregates across all groups; `outputs/` is git-ignored, nothing to commit.)

---
name: api
description: orchestrate fal.ai image gen/edit (best Grok/Google/OpenAI) → exact size+ratio; fans out one background worker per image×model so you can chain more while they run
argument-hint: [-help] [-grok] [-google] [-openai] [-reprompt] [-preview] [-size=1080p] [-ratio=169] <input-path|folder|(attached)> <prompt...>
disable-model-invocation: true
---

# /api — orchestrate fal.ai image gen/edit, one background worker per (image × model)

You are the **orchestrator** for `/api`. Your only job: fan a request out into a **background dynamic
Workflow** that spawns **one worker sub-agent per (image × selected model)** — on Sonnet at high effort,
each following the bundled `agent.md` — then stay free so the user can fire more requests while it runs.
**You never call the API, view/resize/QA any image, finalize prompts, or read `agent.md` yourself** — the
workers own that. (This skill authorizes the Workflow tool; see step 4.)

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. **Do NOT read `agent.md` or
`fanout.workflow.js`** — both are already prepared and complete; you only ever pass their *path* (and the
`args`), never their contents, so opening them just burns tokens. Likewise don't read `lab/docs/`,
`lab/wikis/`, or `CLAUDE.md`. Open any of these **only if** launching the Workflow throws an error you must diagnose.

1. **`-help`, `--help`, or empty `$ARGUMENTS`** → print the HELP block (bottom) verbatim and STOP. No worker.
2. **Pre-flight — cheap text/FS checks only (the *sole* validation you do; ask the user only when a job
   is genuinely impossible to start):**
   - **Models:** need ≥1 of `-grok` / `-google` / `-openai`. None → ask which; don't spawn yet.
   - **Input → a concrete LIST of image files.** Take the first bare positional (strip surrounding quotes;
     keep `./` and a trailing `/`). If it resolves (`test -e`) to a **file** → the list is `[that file]`;
     to a **directory** → the list is **every image file in it** (`*.jpg *.jpeg *.png *.webp …` — actually
     list them). If it does NOT resolve → no input token: if the user **attached/dropped** an image,
     persist it to a path (save under `inputs/` or `.cache/`, **without viewing the pixels**) → list is
     `[that file]`; else ask for a path (or to drop one in `inputs/`); don't spawn yet.
   - **Prompt** = the tokens after the input (or **ALL** positionals if the input came from an attachment).
     Must be non-empty → else ask; don't spawn yet.
3. **Build the cell list — one cell per (image × selected model).** Total cells = **images × models** (1
   model × 5 images = 5; 2 models × 5 images = 10). Each cell is an object `{ argline, label, skipFallback, fallbackRule? }`:
   - `argline` — a single-cell `/api` argument string: `<that ONE model flag> <-reprompt/-preview/-size/-ratio
     as given> <that ONE image PATH> <prompt>`.
   - `label` — `"<model>·<image-stem>"` (shown in the progress display).
   - `skipFallback` — the **other** models selected for this same image (the selected-model set minus this cell's
     own model). Those already have their own cells, so the worker must not fall back onto them (avoids a
     duplicate). E.g. `-google -openai` on one image → the google cell's `skipFallback` is `["openai"]`, the
     openai cell's is `["google"]`. Usually `[]` (only one model selected).
   - `fallbackRule` — **omit unless** the request says something about fallback for this image. Then set it to
     plain text capturing the user's intent; it OVERRIDES agent.md's default order (google↔openai then grok)
     for that cell. Common phrasings → value:
       • "no fallback" / "don't retry on another model" → `"if the chosen model fails or is content-policy-rejected, do NOT retry on any other model — just report the failure"`
       • "fallback to grok only" → `"if the chosen model fails or is content-policy-rejected, retry only on grok; never use any other model"`
       • "fallback to gemini then grok" → `"if the chosen model fails or is content-policy-rejected, retry on google, then on grok"`
     The script passes it to the worker as a **separate instruction line** — **never** put it in `argline`/the
     prompt (it would get drawn into the image).
   Remember this call's **flag set** (models, `-reprompt`, `-preview`, `-size`, `-ratio`) for later "same
   params" follow-ups.
4. **Launch a background dynamic Workflow** to run the cells — this skill **authorizes the Workflow tool**.
   Call `Workflow({ scriptPath: ".claude/skills/api/fanout.workflow.js", args: <the cell list as a real JSON
   array> })` — **pass the path as-is; do NOT open/read the script** (it's complete). The bundled script
   fans out **one sub-agent per cell on `model: sonnet` at `effort: high`** (set
   in the script — Sonnet/high is plenty for this gen/edit + resize work); each sub-agent reads `agent.md`,
   processes its `argline`, and — when the cell's `skipFallback` is non-empty — is told `Do not fall back to
   these models for this image: <list>.`, plus (when set) the cell's `fallbackRule` as a `Fallback exceptional
   rule:` line. The Workflow runs in the **background** and returns immediately: **one Workflow per
   `/api` request**, so you stay free to chain.
5. **Acknowledge in one line**, e.g. `▶ launched workflow — 10 workers ({google,openai} × 5 images): "Make the background black"`.
   Write nothing else.
6. **Stay ready & chain.** Treat any follow-up that names an input + prompt as another job — including
   `same params: <input> <prompt>` / `same param: …`, which **reuses the previous call's flag set** (a
   follow-up may still override individual flags). Re-run steps 2–5 for each — each fires its own background
   Workflow; they run **concurrently**. Plain non-job messages you just answer normally.
7. **Relay, don't QA.** When a Workflow finishes, the harness notifies you with its aggregated results —
   relay them **compactly** (one small row per cell — image · model · saved path · dims · cost, plus any
   fallback noted; batch them rather than narrating each). Add no QA, previews, or commentary of your own.
   (`outputs/` is git-ignored ⇒ nothing to commit.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.

---

```
/api — fal.ai image gen/edit with the best Grok/Google/OpenAI model, normalized to an exact size+ratio

USAGE
  /api [flags] <input> <prompt...>
  Flags first, then the input location, then the prompt. One output per (selected model × input image).
  Fans out to one BACKGROUND worker per (model × image) — so 2 models × 5 images = 10 workers — and you
  can fire more /api calls (or "same params: <input> <prompt>") while earlier ones run; all concurrent.

MODELS (pick ≥1)
  -grok      xAI Grok Imagine     — fast; fal's edit is standard-tier, may distort identity/pose
  -google    Nano Banana Pro      — most faithful editor (best for keeping the subject)
  -openai    GPT Image 2          — clean, but native ~1 MP so it's upscaled to target (softer)

OPTIONS
  -reprompt        Clarify/clean the prompt before sending. Omit = sent VERBATIM (typos kept).
  -preview         Allow the worker to view the input & results. Omit = never looks at any pixels.
  -size=VALUE      Short side in px: 720p | 1080p | 1440p | 2160p (4k=2160p).  Default: 1080p
  -ratio=VALUE     Aspect, colon removed: 169 916 11 43 34 32 23 219.         Default: 169 (16:9)
  -help            Show this help and exit.

POSITIONALS (always this order, after the flags — the input has NO flag/tag)
  <input>          A file path → that image · a folder path → every image in it · or omit it to use
                   an attached/dropped image. If no path and nothing attached, you'll be asked.
  <prompt...>      Everything after the input = the instruction sent to the model.

EXAMPLES
  /api -grok -google "./inputs/image.jpg" Make the background black   # 2 models, that one image
  /api -grok -google "./inputs/" Make the background black            # 2 models × every image in inputs/
  /api -grok -google Make the background black                        # uses the attached image (else asks)
  /api -google -reprompt -size=1440p -ratio=916 inputs/hero.jpg phone wallpaper, keep the character
  /api -openai -preview <drop an image> turn this into a watercolor
  …then while it runs:  same params: inputs/other.jpg make a red background   # new worker, reuses -openai etc.

NOTES
  • fal.ai is a PAID API (key already in .env); each run prints an est cost.
  • Every result is resized to the exact target W×H with ImageMagick. Saved to outputs/ (git-ignored).
  • Fans out to one background worker per (model × image); chain more anytime — "same params: …" reuses
    the last call's flags. The orchestrator only launches workers and relays reports — it never views,
    edits, or QAs any image itself.
  • If google/openai rejects an image on content policy, it auto-retries on the other of the two, then on grok
    (most permissive) as a last resort.
```

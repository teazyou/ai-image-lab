---
name: api
description: orchestrate fal.ai image gen/edit (best Grok/Google/OpenAI) → exact size+ratio; fans out one background worker per image×model so you can chain more while they run
argument-hint: [-help] [-grok] [-google] [-openai] [-reprompt] [-preview] [-size=1080p] [-ratio=169] <input-path|folder|(attached)> <prompt...>
disable-model-invocation: true
---

# /api — orchestrate fal.ai image gen/edit, one background worker per (image × model)

You are the **orchestrator** for `/api`. Your only job: fan a request out into **background worker**
sub-agents — **one per (image × selected model)** — that do the real work (each follows the bundled
`agent.md`), then stay free so the user can fire more requests while workers run. **You never call the
API, view/resize/QA any image, finalize prompts, or read `agent.md` yourself** — the workers own that.

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. Don't read `agent.md`,
`lab/docs/`, `lab/wikis/`, or `CLAUDE.md`.

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
3. **Fan out — one worker per (image × selected model).** Total workers = **images × models** (1 model ×
   5 images = 5; 2 models × 5 images = 10). For each (file, model) cell build a single-cell `/api` argument
   string `ARGS` = `<that ONE model flag> <-reprompt/-preview/-size/-ratio as given> <that ONE image PATH>
   <prompt>`. Remember this call's **flag set** (models, `-reprompt`, `-preview`, `-size`, `-ratio`) for
   later "same params" follow-ups.
4. **Spawn every cell as a background worker** (fire them in parallel) — Agent tool, `subagent_type: claude`,
   **same model as you**, `run_in_background: true`. For each cell, hand the worker its **parameters** (the
   single-cell `ARGS`: one model flag + the option flags + the one image PATH + the prompt) and the **path
   to the spec**, with this prompt:
   > Read the worker spec at `.claude/skills/api/agent.md` (repo-root relative; absolute equivalent
   > `${CLAUDE_SKILL_DIR}/agent.md`) and follow it exactly to process this `/api` argument string:
   > `ARGS`. You handle exactly this ONE model on this ONE image. Working dir is the repo root. Execute
   > every step yourself, and **report only your final result, once you're done**.

   That's all you pass each worker — params + spec path. Everything else (incl. the grok content-policy
   fallback) lives in `agent.md`; you neither know nor manage it.
5. **Acknowledge in one line** with the count, e.g. `▶ launched 10 workers — {google,openai} × 5 images: "Make the background black"`.
   Write nothing else.
6. **Stay ready & chain.** Treat any follow-up that names an input + prompt as another job — including
   `same params: <input> <prompt>` / `same param: …`, which **reuses the previous call's flag set** (a
   follow-up may still override individual flags). Re-run steps 2–5 for each; all workers run **concurrently**.
   Plain non-job messages you just answer normally.
7. **Relay, don't QA.** Each worker reports **once, when it's done**; as those results land, relay them
   **compactly** (one small row per cell — image · model · saved path · dims · cost, plus any fallback the
   worker noted; batch them rather than narrating each). Add no QA, previews, or commentary of your own.
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
  • If google/openai rejects an image on content policy, that image auto-retries on grok (permissive tier).
```

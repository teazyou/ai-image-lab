---
name: api
description: orchestrate fal.ai image gen/edit (best Grok/Google/OpenAI) → exact size+ratio; each request runs as a background worker so you can chain more while they run
argument-hint: [-help] [-grok] [-google] [-openai] [-reprompt] [-preview] [-size=1080p] [-ratio=169] <input-path|folder|(attached)> <prompt...>
disable-model-invocation: true
---

# /api — orchestrate fal.ai image gen/edit, one background worker per request

You are the **orchestrator** for `/api`. Your only job: launch a **background worker** sub-agent that
does the real work (the worker follows the bundled `agent.md`), then stay free so the user can fire
more requests while workers run. **You never call the API, view/resize/QA any image, finalize prompts,
or read `agent.md` yourself** — the worker owns all of that.

Raw arguments: `$ARGUMENTS`

## What the orchestrator does (ONLY this)

Keep your own output to one terse line per action. Never view any pixels. Don't read `agent.md`,
`lab/docs/`, `lab/wikis/`, or `CLAUDE.md`.

1. **`-help`, `--help`, or empty `$ARGUMENTS`** → print the HELP block (bottom) verbatim and STOP. No worker.
2. **Pre-flight — cheap text/FS checks only (the *sole* validation you do; ask the user only when a job
   is genuinely impossible to start):**
   - **Model:** need ≥1 of `-grok` / `-google` / `-openai`. None → ask which; don't spawn yet.
   - **Input:** the first bare positional token (strip surrounding quotes; keep `./` and a trailing `/`).
     If it resolves to an existing **file/dir** (`test -e`), that's the input path and the **prompt is the
     tokens after it**. If it does NOT resolve → there's no input token: if the user **attached/dropped**
     an image, persist it to a path (save under `inputs/` or `.cache/`, **without viewing the pixels**)
     and use that path (then **all** positionals are the prompt); if nothing is attached → ask for a path
     (or to drop one in `inputs/`); don't spawn yet.
   - **Prompt:** must be non-empty → else ask; don't spawn yet.
3. **Build the canonical `ARGS` string** = `<model flags> <other flags> <input-path> <prompt>` (flags
   first, then the resolved input PATH, then the prompt). Remember this call's **flag set** (models,
   `-reprompt`, `-preview`, `-size`, `-ratio`) for later "same params" follow-ups.
4. **Spawn a background worker** — Agent tool, `subagent_type: claude`, **same model as you**,
   `run_in_background: true`, with exactly this prompt (substitute the real `ARGS`):
   > Read the worker spec at `.claude/skills/api/agent.md` (repo-root relative; absolute equivalent
   > `${CLAUDE_SKILL_DIR}/agent.md`) and follow it exactly to process this `/api` argument string:
   > `ARGS`. Working dir is the repo root; resolve input paths relative to it. Execute every step
   > yourself. Your final message is the complete report.
5. **Acknowledge in one line**, e.g. `▶ launched: -openai inputs/x.jpg "Make the background black"`.
   Write nothing else.
6. **Stay ready & chain.** Treat any follow-up that names an input + prompt as another job — including
   `same params: <input> <prompt>` / `same param: …`, which **reuses the previous call's flag set** (a
   follow-up may still override individual flags). Re-run steps 2–5 for each; workers run **concurrently**.
   Plain non-job messages you just answer normally.
7. **Relay, don't QA.** When a background worker finishes, the harness notifies you — relay its report to
   the user (terse, faithful). Add no QA, previews, or commentary of your own. (`outputs/` is git-ignored
   ⇒ nothing to commit.)

That is the entire orchestrator job. The worker's full pipeline lives in `agent.md` — do not inline it.

---

```
/api — fal.ai image gen/edit with the best Grok/Google/OpenAI model, normalized to an exact size+ratio

USAGE
  /api [flags] <input> <prompt...>
  Flags first, then the input location, then the prompt. One output per (selected model × input image).
  Each call runs in a BACKGROUND worker — fire more /api calls (or "same params: <input> <prompt>")
  while earlier ones are still running; they run concurrently.

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
  • Each request runs in its own background worker so you can chain more; "same params: …" reuses the
    last call's flags. The orchestrator only launches workers and relays their reports — it never
    views, edits, or QAs any image itself.
```

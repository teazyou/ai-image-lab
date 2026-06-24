# /api worker — generate/edit image(s) via fal.ai, then normalize to an exact size+ratio

You were handed a `/api`-style **argument string** (it appears in your task prompt): flags first, then
an input PATH, then a prompt. Run the whole job yourself: parse the arguments, call the selected
model(s), save to `outputs/`, resize each result to the exact target, optionally QA, then report.

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here and verified. Open another doc only if a step here fails in a
way these instructions don't explain. Execute every step directly. Working dir = repo root; resolve
paths relative to it.

**What it does:** sends the input image(s) + a prompt to the best image model of each selected brand on
fal.ai (a **PAID** API — `FAL_KEY` is already in repo-root `.env`), saves results to `outputs/`, then
resizes each to the exact target pixel size. One output per **(selected model × input image)**.

## Facts you need (installed + verified — do not re-check)
- Run the client with: `lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py …`
- Each brand = ONE separate run of the script (the `--model` flag is singular):
  - `-grok` → `--model grok` · xAI Grok Imagine. Knobs: `--aspect 16:9` `--resolution 1k|2k` (no 4k).
    ⚠ fal's Grok edit is standard-tier and may **distort identity/pose** — expected, not a bug.
  - `-google` → `--model google` · Nano Banana Pro. Knobs: `--aspect 16:9` `--resolution 1k|2k|4k`
    (4k = 2× price). Most faithful editor of the three.
  - `-openai` → `--model openai` · GPT Image 2. Knobs: `--size <enum>` `--quality high|medium|low`
    (it does **NOT** accept aspect/resolution; native output ≈1 MP, so it is usually **upscaled** to
    the target — expect softer detail).
- Input flags: `--image PATH` (a single file) **or** `--images-dir DIR` (a folder → edits every image).
- Prompt flag: `--prompt "TEXT"`. **Mode auto-detects to edit** when an image is supplied.
- The script silently drops any knob a model doesn't support, validates inputs, and runs each job
  independently (one failure doesn't kill the batch). It saves to `outputs/` as
  `<brand>__<imgstem>__<prompt-slug>__<HHMMSS>.<ext>` and never overwrites. Ext: google/openai→`png`, grok→`jpeg`.
- `magick` (ImageMagick) is installed for the resize step.

## 1 — parse the argument string
Tokens beginning with `-` are flags; everything else is positional, in order.
- `-grok` / `-google` / `-openai` — model(s) to call (≥1 will be present).
- `-reprompt` — clarify the prompt before sending (step 3). If **absent**, send the prompt **verbatim —
  exact literal copy/paste, change nothing** (keep typos, casing, punctuation).
- `-preview` — you ARE allowed to view images this run (steps 4 & 7). If **absent**, you are **forbidden
  to open/view input or output pixels at all** — pass paths straight to the tool. Sole exception: the
  prompt text itself tells you to look at / match the image.
- `-size=VALUE` — short-side pixels. Accept `720p|1080p|1440p|2160p` (and `4k`=2160p). **Default `1080p`.**
  Value = the digits before `p`.
- `-ratio=VALUE` — aspect, colon removed. **Default `169`.** Decode: `169`=16:9 · `916`=9:16 · `11`=1:1 ·
  `43`=4:3 · `34`=3:4 · `32`=3:2 · `23`=2:3 · `219`=21:9. If unlisted, split into the intended `W:H`.
- **Input** = the first bare positional. A **file** → `--image <path>`; a **dir** → `--images-dir <path>`.
  **Prompt** = the tokens after it, joined into one string. (If the first positional doesn't resolve to a
  real path, treat all positionals as the prompt and report that no input was found.)

## 2 — compute the target W×H and per-brand knobs
From short-side `s` (e.g. 1080) and ratio `rW:rH`:
- landscape/square (`rW ≥ rH`): **H = s**, **W = round(s·rW/rH)**
- portrait (`rW < rH`): **W = s**, **H = round(s·rH/rW)**
- round both to even numbers. (1080p+16:9 → 1920×1080 · 1080p+1:1 → 1080×1080 · 1080p+9:16 → 1080×1920.)

For the API call:
- **google/grok** `--aspect` = `rW:rH` (e.g. `16:9`). `--resolution`: `s≤768`→`1k` · `769–1536`→`2k` ·
  `>1536`→ google `4k` (note 2× price) / grok `2k` (grok has no 4k). Requesting ≥ target then
  downscaling in step 6 keeps quality.
- **openai** `--size` enum by ratio: 16:9→`landscape_16_9` · 9:16→`portrait_16_9` · 1:1→`square_hd` ·
  4:3→`landscape_4_3` · 3:4→`portrait_4_3`. For any **other** ratio, **omit** `--size` (fix geometry in
  step 6). Always add `--quality high`.

## 3 — finalize the prompt → write it to a unique scratch file
- **No `-reprompt`:** use the prompt EXACTLY (do not "fix" obvious typos).
- **`-reprompt`:** rewrite for clarity — fix grammar/typos, make the instruction explicit and unambiguous
  for an image-edit model, **preserve the original intent and scope** (add nothing creative), stay concise.
  If `-preview` is set you may view a downscaled input copy (step 4) to ground the rewrite. Note the exact
  prompt you'll send in your final report.

Write the final prompt to a **per-job unique** scratch file (concurrent jobs must not collide) — e.g.
`PF=$(mktemp /tmp/api_prompt.XXXXXX.txt)`, write the text into `$PF`. Runs use `--prompt "$(cat "$PF")"`
so the shell never has to escape quotes/newlines.

## 4 — preview the input (ONLY if `-preview`, or the prompt asks you to look)
`magick "INPUT" -resize 640x "$(mktemp /tmp/api_in.XXXXXX.png)"` then read that once to understand the
subject. **Otherwise skip — never view the input.**

## 5 — run the API calls (capture all logs)
Run each selected model (edit mode is automatic), substituting the step-1/2 values:
- google: `lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py --model google {INPUT_FLAG} --prompt "$(cat "$PF")" --aspect <rW:rH> --resolution <1k|2k|4k>`
- grok:   `… --model grok   {INPUT_FLAG} --prompt "$(cat "$PF")" --aspect <rW:rH> --resolution <1k|2k>`
- openai: `… --model openai {INPUT_FLAG} --prompt "$(cat "$PF")" --size <enum> --quality high`  (drop `--size` for a nonstandard ratio)

where `{INPUT_FLAG}` is `--image <path>` or `--images-dir <dir>`. Run **every** selected model even if one
fails; capture each saved file path, the script's printed **est cost** line, and any error (e.g. a 422
content-policy block).

## 6 — exact size normalization (for every saved output file F)
- `magick identify -format '%wx%h' "F"` → if it already equals the target `W×H`, leave it.
- Otherwise resize to exactly the target (handles up- **and** down-scale; center-crops aspect overflow):
  `magick "F" -resize "WxH^" -gravity center -extent "WxH" "F"`
  (in-place is safe — ImageMagick reads the whole file before writing). Use literal numbers, e.g.
  `-resize "1920x1080^" -gravity center -extent "1920x1080"`.

## 7 — QA (ONLY if `-preview`)
- **`-preview`:** view a 640px-wide downscaled copy of each final output and judge it against the prompt;
  if one is poor, you may re-run that single model once with a clarified prompt, then re-normalize (step 6).
- **Not `-preview`:** never view outputs.

## Report
Your final message is the complete report:
- per model → `SUCCESS <final path> <final W×H>` **or** `FAILURE <error>`;
- the exact prompt that was sent;
- the **total est cost**;
- a final `ls -la outputs/`.
Then clean up your scratch files (`$PF`, any `/tmp/api_in.*`).

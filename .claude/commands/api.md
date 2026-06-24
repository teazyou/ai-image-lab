---
description: fal.ai image gen/edit with the best Grok/Google/OpenAI model, normalized to an exact size+ratio
argument-hint: [-grok] [-google] [-openai] [-reprompt] [-preview] [-size=1080p] [-ratio=169] <input-path|folder|(attached)> <prompt...>
---

# /api — generate image(s) via fal.ai, one per selected brand, normalized to size+ratio

You are running the `/api` command. **Do everything below from THESE INSTRUCTIONS ALONE.**
**DO NOT read any other file** — not `lab/docs/`, `lab/wikis/`, `lab/scripts/`, the script source, or
`CLAUDE.md`. Every fact you need is embedded here and is verified. Open a doc **only if** a step
here fails in a way these instructions do not explain.

Raw arguments: `$ARGUMENTS`

**What it does:** sends the input image(s) + a prompt to the best image model of each selected brand
on fal.ai (a **PAID** API — the `FAL_KEY` is already in repo-root `.env`), saves results to
`outputs/`, then resizes each result to the exact target pixel size. You get **one output per
(selected model × input image)**.

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
- `outputs/` is git-ignored ⇒ **nothing to commit** after a run.

## Step 1 — parse `$ARGUMENTS`
Tokens beginning with `-` are flags; everything else is positional, in order.

Flags:
- `-grok` / `-google` / `-openai` — model(s) to call; any combination, **≥1 required**. If none → **ask** which.
- `-reprompt` — clarify the prompt before sending (Step 3). If **absent**, send the prompt
  **verbatim — exact literal copy/paste, change nothing** (keep typos, casing, punctuation).
- `-preview` — you ARE allowed to view images this run (Steps 4 & 7). If **absent**, you are
  **forbidden to open/view the input or output pixels at all** — pass paths straight to the tool.
  Sole exception: the user's prompt text itself tells you to look at / match the image.
- `-size=VALUE` — short-side pixels. Accept `720p|1080p|1440p|2160p` (and `4k`=2160p). **Default `1080p`.**
  The value is the digits before `p`.
- `-ratio=VALUE` — aspect with the colon removed. **Default `169`.** Decode:
  `169`=16:9 · `916`=9:16 · `11`=1:1 · `43`=4:3 · `34`=3:4 · `32`=3:2 · `23`=2:3 · `219`=21:9.
  If unlisted, split into the intended `W:H` integers.

Positionals (always this order, AFTER the flags):
1. **Input location** (first positional): an existing **file** → use `--image`; an existing
   **directory** → use `--images-dir`. If the first positional is **not** an existing path **and** an
   image is attached to the message → there is no location token, the attachment is the input. If
   neither a path nor an attachment exists → **ask the user for the input.**
2. **Prompt**: everything after the location (or, when the input is an attached image with no
   location token, everything after the flags). Join into one string. If empty → **ask.**

Attached-image handling: if the user dropped/attached an image (no path), first save it to a file
under `inputs/` (or `.cache/<job>/`) and use that path as `--image`. If you can't get a file for it,
ask the user to give a path or drop it in `inputs/`.

## Step 2 — compute the target W×H and the per-brand knobs
From short-side `s` (e.g. 1080) and ratio `rW:rH`:
- landscape/square (`rW ≥ rH`): **H = s**, **W = round(s·rW/rH)**
- portrait (`rW < rH`): **W = s**, **H = round(s·rH/rW)**
- round both to even numbers. (1080p+16:9 → 1920×1080 · 1080p+1:1 → 1080×1080 · 1080p+9:16 → 1080×1920.)

For the API call:
- **google/grok** `--aspect` = `rW:rH` (e.g. `16:9`). `--resolution`: `s≤768`→`1k` · `769–1536`→`2k` ·
  `>1536`→ google `4k` (note 2× price) / grok `2k` (grok has no 4k). Requesting ≥ target and then
  downscaling in Step 6 keeps quality.
- **openai** `--size` enum by ratio: 16:9→`landscape_16_9` · 9:16→`portrait_16_9` · 1:1→`square_hd` ·
  4:3→`landscape_4_3` · 3:4→`portrait_4_3`. For any **other** ratio, **omit** `--size` (it defaults;
  you'll fix the geometry in Step 6). Always add `--quality high`.

## Step 3 — finalize the prompt → write it to a scratch file
- **No `-reprompt`:** use the user's prompt EXACTLY (do not "fix" obvious typos).
- **`-reprompt`:** rewrite for clarity — fix grammar/typos, make the instruction explicit and
  unambiguous for an image-edit model, **preserve the original intent and scope** (add nothing
  creative the user didn't ask for), stay concise. If `-preview` is also set you may view a
  downscaled input copy (Step 4) to ground the rewrite. Tell the user the exact prompt you'll send.

Write the final prompt text (verbatim or reprompted) to a scratch file, e.g.
`<scratchpad>/api_prompt.txt`, so the shell never has to escape quotes/newlines. The runs use
`--prompt "$(cat <scratchpad>/api_prompt.txt)"`.

## Step 4 — preview the input (ONLY if -preview, or the prompt asks you to look)
`magick "INPUT" -resize 640x <scratchpad>/api_in.png` then read that once to understand the subject.
**Otherwise skip entirely — never view the input.**

## Step 5 — run the API calls in a SUB-AGENT
Spawn ONE sub-agent (Agent tool, `subagent_type: claude`, **same model as you**) so its upload/queue
log spew stays out of your context. Hand it the exact, ready-to-run commands and tell it to:

1. Run each selected model (edit mode is automatic), substituting the Step-1/2 values, e.g.:
   - google: `lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py --model google {INPUT_FLAG} --prompt "$(cat <scratchpad>/api_prompt.txt)" --aspect <rW:rH> --resolution <1k|2k|4k>`
   - grok:   `… --model grok   {INPUT_FLAG} --prompt "$(cat …)" --aspect <rW:rH> --resolution <1k|2k>`
   - openai: `… --model openai {INPUT_FLAG} --prompt "$(cat …)" --size <enum> --quality high`  (drop `--size` for a nonstandard ratio)
   where `{INPUT_FLAG}` is `--image <path>` or `--images-dir <dir>`.
2. Run **every** selected model even if one fails; capture each saved file path, the script's printed
   **est cost** line, and any error (e.g. a 422 content-policy block).
3. **Normalize each saved file to exactly W×H** (Step 6) with magick. The sub-agent must **never
   open/view any image** — only `magick identify` / `magick` transforms.
4. Report back: per model → SUCCESS + final path + final `W×H` (or FAILURE + the error); the **total
   est cost**; and a final `ls -la outputs/`.

## Step 6 — exact size normalization (the sub-agent does this for every output file F)
- `magick identify -format '%wx%h' "F"` → if it already equals the target `W×H`, leave it.
- Otherwise resize to exactly the target (covers up- **and** down-scale; center-crops any aspect
  overflow, e.g. when openai returned a slightly different shape):
  `magick "F" -resize "WxH^" -gravity center -extent "WxH" "F"`
  (in-place is safe — ImageMagick reads the whole file before writing). Use the literal numbers, e.g.
  `-resize "1920x1080^" -gravity center -extent "1920x1080"`.

## Step 7 — QA + report (you, the main session)
- **If `-preview`:** view a 640px-wide downscaled copy of each final output and judge it against the
  prompt; if one is poor, say so — you may re-run that single model once with a clarified prompt.
  **If not `-preview`:** do **not** view outputs; just relay the sub-agent's paths + dims.
- Report to the user: each model's final file (as a clickable path), its final dimensions, the exact
  prompt that was sent, and the **total est cost**. Note that `outputs/` is git-ignored, so there's
  nothing to commit.

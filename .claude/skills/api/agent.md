# /api worker — generate/edit ONE image with ONE model via fal.ai, then normalize to an exact size+ratio

You were handed a `/api`-style **argument string** (it appears in your task prompt): exactly **one model
flag**, then a single input image **PATH**, then a prompt. Run that one job yourself: parse the arguments,
call that one model on that one image, save to `outputs/`, resize the result to the exact target, optionally
QA, then report. (The orchestrator fans a request out into one worker per image × model — you are one cell.)

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here and verified. Open another doc only if a step here fails in a
way these instructions don't explain. Execute every step directly. Working dir = repo root; resolve
paths relative to it.

**What it does:** sends the input image + a prompt to the selected model on fal.ai (a **PAID** API —
`FAL_KEY` is already in repo-root `.env`), saves the result to `outputs/`, then resizes it to the exact
target pixel size.

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
- Input flag: `--image PATH` (a single file — you always edit exactly one).
- Prompt flag: `--prompt "TEXT"`. **Mode auto-detects to edit** when an image is supplied.
- The script silently drops any knob a model doesn't support and validates inputs. It saves to `outputs/`
  as `<brand>__<imgstem>__<prompt-slug>__<HHMMSS>.<ext>` and never overwrites. Ext: google/openai→`png`, grok→`jpeg`.
- `magick` (ImageMagick) is installed for the resize step.

## 1 — parse the argument string
Tokens beginning with `-` are flags; everything else is positional, in order.
- exactly **one** of `-grok` / `-google` / `-openai` — the single model you call.
- `-reprompt` — clarify the prompt before sending (step 3). If **absent**, send the prompt **verbatim —
  exact literal copy/paste, change nothing** (keep typos, casing, punctuation).
- `-preview` — you ARE allowed to view images this run (steps 4 & 7). If **absent**, you are **forbidden
  to open/view input or output pixels at all** — pass paths straight to the tool. Sole exception: the
  prompt text itself tells you to look at / match the image.
- `-size=VALUE` — short-side pixels. Accept `720p|1080p|1440p|2160p` (and `4k`=2160p). **Default `1080p`.**
  Value = the digits before `p`.
- `-ratio=VALUE` — aspect, colon removed. **Default `169`.** Decode: `169`=16:9 · `916`=9:16 · `11`=1:1 ·
  `43`=4:3 · `34`=3:4 · `32`=3:2 · `23`=2:3 · `219`=21:9. If unlisted, split into the intended `W:H`.
- **Input** = the first bare positional: a single image **file** → `--image <path>`. **Prompt** = the
  tokens after it, joined into one string. (You always get one concrete image path from the orchestrator;
  if it doesn't resolve to a real file, report that and stop.)

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

## 5 — run the API call (capture all logs)
Run your one model (edit mode is automatic), substituting the step-1/2 values — use the line for your model:
- google: `lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py --model google --image <path> --prompt "$(cat "$PF")" --aspect <rW:rH> --resolution <1k|2k|4k>`
- grok:   `… --model grok   --image <path> --prompt "$(cat "$PF")" --aspect <rW:rH> --resolution <1k|2k>`
- openai: `… --model openai --image <path> --prompt "$(cat "$PF")" --size <enum> --quality high`  (drop `--size` for a nonstandard ratio)

Capture the saved file path, the script's printed **est cost** line, and any error (e.g. a 422 content-policy block).

**Content-policy fallback (automatic — don't ask).** Fallback order is **google ↔ openai, then grok last**
(grok's edit tier is the most permissive). Trigger on **moderation rejections only** (a content-policy / safety
block — e.g. a 422, or a refusal / no image); for network/quota/timeout errors just report the failure. On a
moderation rejection, **immediately re-run the SAME request for this image** on the next model in the chain,
applying *that* model's own knobs per §2 (google/grok use `--aspect`+`--resolution`, grok has no 4k; openai uses
`--size`+`--quality high`):
- your model is **google**, rejected → retry on **openai**; if openai is *also* rejected → retry on **grok**.
- your model is **openai**, rejected → retry on **google**; if google is *also* rejected → retry on **grok**.
- your model is **grok** → no fallback (it's the last resort); on rejection just report the failure.

Keep walking the chain until one succeeds or grok fails. Then normalize the winner (step 6) and report it; flag
it `(fallback: <model>→<model>…)` and add **every** attempt's est cost to your total.

**Skip already-covered models.** If your task prompt says *"Do not fall back to these models for this image:
<list>"*, treat those models as unavailable fallback targets — skip over them in the chain (they already have
their own cells, so falling back onto one would duplicate work). If skipping leaves no remaining target, just
report the failure on a rejection.

## 6 — exact size normalization (for the saved output file F)
- `magick identify -format '%wx%h' "F"` → if it already equals the target `W×H`, leave it.
- Otherwise resize to exactly the target (handles up- **and** down-scale; center-crops aspect overflow):
  `magick "F" -resize "WxH^" -gravity center -extent "WxH" "F"`
  (in-place is safe — ImageMagick reads the whole file before writing). Use literal numbers, e.g.
  `-resize "1920x1080^" -gravity center -extent "1920x1080"`.

## 7 — QA (ONLY if `-preview`)
- **`-preview`:** view a 640px-wide downscaled copy of the final output and judge it against the prompt;
  if it's poor, you may re-run your model once with a clarified prompt, then re-normalize (step 6).
- **Not `-preview`:** never view outputs.

## Report
Work silently, then **report only once — your final message, when the job is fully done** (no progress
chatter). It is the result for this one (model, image):
- `SUCCESS <final path> <final W×H>` **or** `FAILURE <error>`; if a content-policy rejection triggered the
  grok fallback, say so and give the grok result `(fallback from <google|openai>)`;
- the exact prompt that was sent and the **est cost** (plus the fallback's cost, if any).
Then clean up your scratch files (`$PF`, any `/tmp/api_in.*`). (The orchestrator aggregates across all cells.)

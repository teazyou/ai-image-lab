# /sharpen-definition worker — set ONE image to 1080p + boost definition, then report

You were handed a `/sharpen-definition`-style **argument string** (it appears in your task prompt): a
single input image **PATH**. Run that one job yourself — it is **purely mechanical, no visual judgment
needed**. (The orchestrator fans a request out into one worker per image — you are one image.)

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here. Working dir = repo root; resolve paths relative to it.

**What it does:** sets the image to **1080p** (1080px tall, aspect ratio preserved — a 16:9 input →
1920×1080) and **sharpens its definition** via a Real-ESRGAN 4× upscale → Lanczos downscale to 1080p →
light unsharp. The whole pipeline is the sibling script; you just run it.

## 1 — parse the argument string
**Input** = the bare positional: a single image **PATH** (strip surrounding quotes). The orchestrator
hands you one concrete file path; if it doesn't resolve to a real file, report `FAILURE` and STOP.

## 2 — run the pipeline (one command)
`.claude/skills/sharpen-definition/sharpen_definition.sh -i "<img>"`
- It Real-ESRGAN 4×-upscales on MPS (~8s for a 1080p input), downscales to 1080p with Lanczos, applies a
  light unsharp, writes `outputs/<stem>_1080p-sharp.png`, and cleans its own `.cache/` scratch.
- Never modifies the input in place. **The script is the entire job** — no extra ImageMagick steps.

## 3 — do NOT review the result
This task needs **no vision and no QA**. **Do not open, view, or inspect** the input or the output — the
pipeline is deterministic and already validated. Just confirm the script exited 0 and printed its
`saved: …` line. Spend zero vision tokens.

## Report
Work silently, then **report only once — your final message, when the script has finished**:
- `SUCCESS <final output path>` with the saved dimensions the script printed — **or** `FAILURE <error>`
  (e.g. path didn't resolve, or the script exited non-zero — include its stderr tail).
(The orchestrator aggregates across all images; `outputs/` is git-ignored, nothing to commit.)

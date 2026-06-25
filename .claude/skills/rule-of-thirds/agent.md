# /rule-of-thirds worker — shift ONE subject off-center (face-aware), then QA

You were handed a `/rule-of-thirds`-style **argument string** (it appears in your task prompt): an
optional percent flag, then a single input image **PATH**. Run that one job yourself: decide which way
the subject should move (this needs **VISION**), run the mechanical shift, QA the result, then report.
(The orchestrator fans a request out into one worker per image — you are one image.)

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here. Execute every step yourself. Working dir = repo root; resolve
paths relative to it.

**Parallel-safe hard limits (other workers run at the same time — never touch anything shared).**
- **Never modify, overwrite, move, or delete any pre-existing file** — scripts (incl. the sibling
  shift script), skills, docs, configs, the tool/lab setup — **even to fix a bug or a broken script.**
  (Creating NEW files is fine: your `outputs/` result and temp scratch peek files.)
- **Never install or upgrade tools/packages/models, and never change the system or environment.**
- Blocked by something you can't clear within these limits (broken/missing script, missing dependency,
  a tool needing reinstall)? **Don't fix it yourself** — stop and **report it to the orchestrator in
  your final report**, describing the problem precisely so the main agent (the one who launched this
  workflow) can fix it.

**What it does:** moves the subject horizontally so it looks INTO the open space (rule-of-thirds /
lead-room look) on a **solid-background** image (e.g. our black-bg wallpapers). Direction needs visual
judgment (your job); the shift itself is mechanical (the sibling script). The script reads the bg color
from the top-left pixel and backfills the vacated side with it, clamping the shift so the subject never
clips the frame.

## 1 — parse the argument string
Tokens beginning with `-` are flags; everything else is positional.
- `-N` (e.g. `-20`, `-30`) — percent of image width to shift. **Default `20`** if absent.
- **Input** = the bare positional: a single image **PATH** (strip surrounding quotes). The orchestrator
  hands you one concrete file path; if it doesn't resolve to a real file, report that and STOP.

## 2 — decide the direction (VISION — the subject must look INTO the open space / lead room)
- Make a small copy to keep vision cheap, then view **that copy** once (never the full-res original):
  `magick "<img>" -resize 480x "$(mktemp /tmp/rot_peek.XXXXXX.png)"`
- Read which way the **subject faces** — head turn / gaze / nose / body lean — then shift to the
  **OPPOSITE** side so the empty space opens where it looks:
  - face points **left → shift `right`**
  - face points **right → shift `left`**
  - near-frontal: use the side the head / chin / shoulders lean toward.

## 3 — run the mechanical shift
`.claude/skills/rule-of-thirds/rule_of_thirds_shift.sh -i "<img>" -d <left|right> -p <pct>`
- Output lands in `outputs/<stem>_thirds-<dir><pct>.png` (never modifies the input in place).
- Note any `>> clamped …px -> …px` line it prints (the subject would have clipped that edge).

## 4 — QA (VISION)
View the output (a downscaled copy is fine) and confirm the subject moved the **correct** way and isn't
clipped. If the direction read was wrong, re-run step 3 with the opposite `-d` and re-check.

## Report
Work silently, then **report only once — your final message, when the job is fully done** (no progress
chatter). It is the result for this one image:
- `SUCCESS <final output path>` with: direction chosen (left/right) · the facing cue that decided it ·
  pct used · whether the shift was clamped — **or** `FAILURE <error>`.
Then clean up your scratch peek file(s) (`/tmp/rot_peek.*`). (The orchestrator aggregates across all
images; `outputs/` is git-ignored, nothing to commit.)

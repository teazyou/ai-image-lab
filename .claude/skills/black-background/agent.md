# /black-background worker — cut a GROUP of subjects onto solid black (sequentially, with vision + QA), then report

You were handed a **GROUP of image PATHS** — they appear in your task prompt, **one per line**. Process
the whole group yourself; each image **needs VISION** (pick the right rembg model for the subject, then
QA the cutout). (The orchestrator splits the request into at most a few groups and runs one worker per
group in parallel — you own ONE group, and you process it **strictly one image at a time**.)

**Do everything from THIS file alone** — don't read `lab/docs/`, `lab/wikis/`, the script source, or
`CLAUDE.md`; every fact you need is here. Execute every step yourself. Working dir = repo root; resolve
paths relative to it.

**Parallel-safe hard limits (other workers run at the same time — never touch anything shared).**
- **Never modify, overwrite, move, or delete any pre-existing file** — scripts (incl. the shared
  `bg_to_color.sh`), skills, docs, configs, the tool/lab setup — **even to fix a bug or a broken script.**
  (Creating NEW files is fine: the script's `outputs/` results, the `.cache/` cutouts, and your temp
  peek files.)
- **Never install or upgrade tools/packages/models, and never change the system or environment.**
- Blocked by something you can't clear within these limits (broken/missing script, missing dependency,
  a tool needing reinstall)? **Don't fix it yourself** — record those images as FAILURE and **report it
  to the orchestrator in your final report**, describing the problem precisely so the main agent (the
  one who launched this workflow) can fix it. (A per-image failure you still skip past per step 2.)

**What it does (per image):** removes the background and composites the subject onto a **pure-black**
canvas of the same dimensions. The mechanical pipeline is the shared script
`lab/scripts/bg_to_color.sh` (rembg cutout → ImageMagick black canvas); your judgment is **picking the
right rembg model for each subject and QA-ing the result**.

## 1 — parse your group
Your task prompt contains a **list of image PATHS, one per line** (strip any surrounding quotes). That
list is your group; keep its order.

## 2 — process ONE IMAGE AT A TIME (strictly sequential — RAM is why)
For each path in your group, in order, do steps 2a–2d fully **before** starting the next image.

- **Exactly one rembg cutout in flight at a time.** Start the next image **only after the previous one
  is fully done (run + QA + cleanup)**. **Never** run two cutouts at once, **never** `&` / background
  them, **never** batch multiple `bg_to_color.sh` calls in one step. `birefnet-general` can peak
  **~14 GB RAM**, so two rembg in flight inside one worker would blow the memory budget — running one at
  a time is the whole reason the work is split this way. One image → wait → next image.
- **Continue on failure.** If a path doesn't resolve or the script exits non-zero, record that image as
  a FAILURE (keep its stderr tail) and **move on to the next** — one bad image must not stop the rest of
  your group.
- **Process every image in your group before you report.** Don't stop early or summarize partway.

### 2a — pick the rembg model (cheap VISION)
Glance at a **downscaled copy** (never the full-res original) only to classify the subject:
`magick "<img>" -resize 480x /tmp/bb_peek.XXXX.png` (give each image a unique temp name). Then:
- **anime / illustration** → `-t anime` (isnet-anime)
- **real person / photo of a human** → `-t person` (u2net_human_seg)
- **other photo / object** → `-t photo` (birefnet-general)
- **Override → `-m birefnet-general`** when the subject has **dark, low-contrast parts that must
  survive** (shadow hands/claws, black fur, dark appendages): isnet-anime drops them, birefnet keeps
  them. Worth a glance specifically for this.

### 2b — run the cutout-onto-black
`lab/scripts/bg_to_color.sh -i "<img>" -c black -t <type>` (or `-m <model>` for the override).
- Output → `outputs/<stem>_black-bg.png` (same dims; never modifies the input in place).
- The script leaves a cutout at `.cache/<stem>_cutout.png`.

### 2c — QA the result (VISION)
View the output (a downscaled copy is fine). Check the **whole subject survived** (no dropped
limbs/hair) and there's **no white halo/fringe**. If parts were lost or it's haloed, **retry with
another model** (e.g. birefnet ↔ isnet) and **keep the better one**.

### 2d — clean up
Remove this image's cutout (`rm .cache/<stem>_cutout.png`) and its temp peek file(s). Then move to the
next image.

**Black-on-black ambiguity:** if an image has two subjects where one is a pure-black silhouette, both
can't show on a black canvas. You can't ask the user, so **do your best** (keep the more salient
subject) **AND note the ambiguity in that image's report line** for the orchestrator to relay — do not
silently guess and stay quiet about it.

## Report
Work silently through your whole group, then **report only once — your final message, after every image
in your group is done** — with **one line per image**:
- `SUCCESS <final output path>` plus the **rembg model used** (and "(retried <a>→<b>)" if you switched),
  and any **black-on-black ambiguity** note, **or**
- `FAILURE <error>` for that image (path didn't resolve, or the script exited non-zero — include its
  stderr tail).

(The orchestrator aggregates across all groups; `outputs/` is git-ignored, nothing to commit.)

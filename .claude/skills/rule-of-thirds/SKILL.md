---
name: rule-of-thirds
description: Shift a subject off-center so it looks into the open space (rule-of-thirds / lead-room look). Per image, decide left|right from the subject's facing, then move it that % of the image width. Local-only (ImageMagick).
argument-hint: "[-20|-30] <image-or-folder-path>"
disable-model-invocation: true
---

# /rule-of-thirds — face-aware off-center shift (local)

Move the subject horizontally for a stylish off-center composition. **Direction needs vision (your
job); the shift is mechanical** → `rule_of_thirds_shift.sh` (sibling file in this skill folder).
Assumes a **solid background** (e.g. our black-bg wallpapers); the script reads the bg color from the
top-left pixel and backfills with it, clamping the shift so the subject never clips.

Raw arguments: `$ARGUMENTS`

## Steps

1. **Parse args.** Percent = `20` unless a `-20` / `-30` (any `-N`) token is present → use that N.
   The remaining token is the **path** (file or folder; strip quotes).
2. **Build the image list.** File → `[that file]`. Folder → every image in it
   (`*.png *.jpg *.jpeg *.webp`, non-recursive). Empty → tell the user, stop.
3. **Per image — decide the direction (vision). The subject must look INTO the open space (lead room):**
   - Make a small copy to keep vision cheap: `magick "<img>" -resize 480x /tmp/rot_peek.png`, view it.
   - Read which way the **subject faces** — head turn / gaze / nose / body lean — then shift to the
     **OPPOSITE** side so the empty space opens where it looks: face points **left → shift `right`**,
     face points **right → shift `left`**. (Near-frontal: use the side the head/chin/shoulders lean toward.)
4. **Shift:** `.claude/skills/rule-of-thirds/rule_of_thirds_shift.sh -i "<img>" -d <left|right> -p <pct>`.
   Output lands in `outputs/<stem>_thirds-<dir><pct>.png`. Note any `clamped` line it prints.
5. **QA each result yourself** — view the output, confirm the subject moved the right way and isn't
   clipped. If a direction read was wrong, re-run with the opposite `-d`.
6. **Report** one line per image: direction chosen + output path. Remove the temp peek file.

Notes: never modify inputs in place; outputs are git-ignored (nothing to commit unless the script/skill itself changed).

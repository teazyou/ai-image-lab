---
name: black-background
description: Keep the subject, turn everything else into a solid black background. Works on one image or a whole folder. Local-only (rembg + ImageMagick).
argument-hint: "<image-or-folder-path>"
disable-model-invocation: true
---

# /black-background — cut out the subject onto solid black (local)

Remove each image's background and composite the subject onto a **pure-black** canvas (same dims).
The mechanical pipeline already exists → [lab/scripts/bg_to_color.sh](../../../lab/scripts/bg_to_color.sh)
(`rembg` cutout → ImageMagick black canvas). **Your job is the judgment: pick the right rembg model
per subject, then QA.** Don't duplicate the script.

Raw arguments: `$ARGUMENTS`

## Steps

1. **Build the image list.** Strip quotes from the path. File → `[that file]`. Folder → every image
   in it (`*.png *.jpg *.jpeg *.webp`, non-recursive). Empty → tell the user, stop.
2. **Per image — pick the rembg model (cheap vision):** glance at a downscaled copy
   (`magick "<img>" -resize 480x /tmp/bb_peek.png`) only to classify the subject:
   - **anime / illustration** → `-t anime` (isnet-anime)
   - **real person / photo of a human** → `-t person` (u2net_human_seg)
   - **other photo / object** → `-t photo` (birefnet-general)
   - **Override → `-m birefnet-general`** when the subject has **dark, low-contrast parts that must
     survive** (shadow hands/claws, black fur, dark appendages): isnet-anime drops them, birefnet keeps
     them (see `lab/wikis/background-removal/`). Worth a glance specifically for this.
3. **Run:** `lab/scripts/bg_to_color.sh -i "<img>" -c black -t <type>` (or `-m <model>`).
   Output → `outputs/<stem>_black-bg.png`. The script leaves a cutout at `.cache/<stem>_cutout.png`.
4. **QA each result yourself** — view it. Check the whole subject survived (no dropped limbs/hair) and
   there's no white halo/fringe. If parts were lost or it's haloed, **retry with another model**
   (e.g. birefnet ↔ isnet) and keep the better one.
5. **Clean up** the cutout(s) (`rm .cache/<stem>_cutout.png`) and the temp peek file.
6. **Report** one line per image: model used + output path.

Notes: never modify inputs in place; outputs are git-ignored (nothing to commit unless the skill itself changed).
Two subjects where one is a pure-black silhouette can't both show on black — flag that to the user instead of guessing.

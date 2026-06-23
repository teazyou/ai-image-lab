# Background removal — models & when to use which

**Overview.** Background removal = segment foreground subject, output an alpha matte / transparent
cutout. On this lab the go-to engine is **rembg** (ONNX, runs on CPU on Apple Silicon — no CUDA
needed). How to run it: [lab/docs/rembg.md](../../docs/rembg.md).

## Model comparison (rembg, as of 2026-06)

| Model | Best for | Notes |
|-------|----------|-------|
| **isnet-anime** | **anime / illustration / drawn art** | Purpose-built for drawn art; cleaner edges on hair/lineart than photo models. ~176 MB. |
| **birefnet-general** | photos, general subjects | SOTA quality (2025); preserves fine hair / fur / glass. Slower (~9–20 s). Larger model. |
| birefnet-general-lite | photos, faster | Lighter/faster birefnet, slightly lower quality. |
| birefnet-portrait | headshots / face photos | Optimized for portraits. |
| u2net | general default | Fast, decent; the historical default. |
| u2net_human_seg | people / full body photos | Best classic model for human subjects. |
| isnet-general-use | general | Between u2net and birefnet. |

**Rule of thumb:** drawn/anime → `isnet-anime`; photo of a person → `u2net_human_seg` or
`birefnet-portrait`; everything else / max quality → `birefnet-general`.

**Caveat (verified 2026-06-24): `isnet-anime` only works on *clean* illustrations.** On busy/blended
scenes — game screenshots, a character melting into a dark/red background, subject reflected in
water — it returns a faint, **translucent** matte (alpha near-zero everywhere), useless for a hard
cutout. **`birefnet-general` is the fix**: solid opaque masks that even keep thin attached elements
(flowing ribbons, hair bands, robe). So for anime *characters in complex scenes*, reach for
`birefnet-general`, not `isnet-anime`. (`u2net_human_seg`/`birefnet-portrait` are trained on real
people and **miss anime characters** — don't use them on illustration.)

**Hard isolations → SAM (click-to-select).** birefnet still fails two ways: it grabs a *connected*
blob (subject fused with snow/smoke/water) or drops a *low-contrast limb*. No single auto-model
fixes this; the reliable move is rembg's `sam` model with keep/exclude point prompts, **combined
with the birefnet matte** (`birefnet ∩ dilate(SAM)` to subtract a connected blob; `birefnet ∪ SAM`
to add a dropped limb). Recipe + the connected-components stray-removal trick: lab/docs/rembg.md.
rembg's `sam` is only ViT-B (coarse, no real interactive refine). For the SOTA *beyond* rembg —
EfficientTAM (native MPS, click-to-refine), SAM2/SAM3 in ComfyUI, BiRefNet matting variants, and
when to give up and mask manually — see [precise-segmentation](../precise-segmentation/README.md).

## Replacing the background with a solid color

rembg only removes the background (transparent alpha). To get a **solid-color background** (e.g.
plain black), composite the transparent cutout onto a solid canvas with ImageMagick — see
lab/docs/rembg.md. Compositing the cutout centered onto a fixed-size canvas also locks in the target
resolution / aspect ratio in one step.

## Benchmarks on this machine (M4 Max, CPU onnxruntime)

- isnet-anime on a 1920×1080 image: ~23 s CPU time incl. model load (first run also downloads
  176 MB). Fast enough that MPS/GPU isn't worth the trouble for single images.
- birefnet-general: ~9 s wall per image (1–4 MP) on M4 Max CPU once cached; model is 973 MB (first
  run downloads it — see the resume-loop gotcha in lab/docs/rembg.md).

## Links
- rembg: https://github.com/danielgatis/rembg · https://pypi.org/project/rembg/
- BiRefNet vs rembg vs U2Net (production notes):
  https://dev.to/om_prakash_3311f8a4576605/birefnet-vs-rembg-vs-u2net-which-background-removal-model-actually-works-in-production-4830

## Keeping the subject but only *dimming* the rest (not full removal)

Some requests want the subject untouched and the background **darkened**, not deleted (e.g. "black
square at 70% opacity over everything else"). Same matte, different composite: overlay a
semi-transparent color over the whole image, then paste the original subject (the cutout) back on
top. Opacity 1.0 = solid bg; 0.7 = background kept at 30% brightness. Script:
[`lab/scripts/dim_background.sh`](../../scripts/dim_background.sh). For a two-zone treatment (e.g. sky →
pure black, foreground water/flowers → 70% dim) split the background with a feathered horizontal
mask before compositing the subject — see lab/docs/rembg.md.

*Last verified: 2026-06-24*

# img2img restyle — keep composition/pose/design/colors, upgrade rendering (SDXL, MPS)

World-knowledge for **re-rendering an already-anime image into a higher-end style** (e.g. flat
3D-ish render → "gacha splash art / key visual") while preserving the **composition, pose, character
design, colors, and identity**. Operational graph/commands: [lab/docs/comfyui.md](../../docs/comfyui.md).
Base = **Illustrious-XL v2.0** (anime SDXL eps, reliable on MPS).

## The lever: ControlNet **Tile** is the structure anchor (not Canny/LineArt/Depth)
Tile conditions on the **downscaled color field** of the source → pins layout **and palette**
(skin/hair/costume colors survive) while leaving high-frequency surface (linework, shading, render)
free to repaint — exactly the restyle knob. **Canny/LineArt** pin the exact edge map → force the model
to retrace old strokes, fighting the render change. **Depth** fixes only coarse 3D, drops color/identity
→ face & colors drift. Tile needs **no preprocessor** (feed the raw image; preprocessor `none`).
Optional helpers (already installed): IP-Adapter plus (carry identity if face drifts), OpenPose (lock
pose) — but Tile alone usually locks both; add only if QA shows drift.

## Recipe (verified 2026-06-25)
- **Model:** `xinsir/controlnet-tile-sdxl-1.0` → `controlnet-tile-sdxl-xinsir.safetensors` (2.33 GB,
  Apache-2.0/ungated). In `models/controlnet/`.
- **img2img:** `VAEEncode(source)` → `KSampler` **denoise 0.65** (0.55 timid ↔ 0.75 strong; >0.8 drifts).
- **Tile CN:** `ControlNetApplyAdvanced` **strength 0.55** (0.5–0.65) · **start 0.0 · end 0.70**
  (end <1.0 releases the last ~30% steps so the new style paints freely; model-card default 1.0/1.0
  over-locks the original render). Drift → ↑strength/end or ↓denoise; style too weak → ↓strength/end or ↑denoise.
- **Sampler:** Euler a / Normal · **24–28 steps · CFG 5 · clip skip 2** (Illustrious is NAI-lineage).
- **Prompt = render/quality tags ONLY** (subject comes from the image+Tile). Positive: `masterpiece,
  best quality, amazing quality, very aesthetic, newest, official art, key visual, splash art, cel
  shading, glossy skin, subsurface scattering, detailed face/hair/clothes, dramatic/cinematic/rim
  lighting, backlighting, vibrant colors, high contrast, black background, simple background, absurdres`.
  Negative: `worst/low quality, lowres, jpeg artifacts, blurry, sketch, bad anatomy/hands, extra digits,
  watermark, signature, text, censored, monochrome, greyscale`. **OMIT subject-altering tags** (hair/eye
  color & length, outfit, body/age, pose/expression/framing, scene bg) — they'd change identity.

## Resolution (this matters for black-bg wallpapers)
SDXL trains ~1 MP → don't run a 2 MP / 1920×1080 frame (duplication/seams). When the subject occupies
only part of a mostly-black wide frame, **crop the subject region at native res to ~1 MP, restyle, then
composite the result back onto a fresh black canvas at the original offset** — seamless because
everything outside is pure black, and the face gets full pixel budget (far better than restyling the
whole frame at a tiny effective subject size). Worked example: char bbox `magick -fuzz 8% %@` → crop
`-crop WxH+X+Y` on a ÷8 box near 1 MP → process → paste onto `canvas:black` at +X+Y. Upscale only if a
larger deliverable is needed (Real-ESRGAN).

## MPS gotchas
- Illustrious ships a baked fp16-fixed VAE → our standard `--force-fp16` launch is fine (no black
  images). If a different SDXL ckpt gives black output, relaunch `--fp32-vae` (or `--cpu-vae`).
- Tile CN runs on MPS fine (slower than CUDA). Use `ControlNetApplyAdvanced` (start/end), not legacy
  `ControlNetApply`. Stack a 2nd CN by chaining another `ControlNetApplyAdvanced`.

*Last verified: 2026-06-25 (recipe researched + xinsir repo confirmed ungated; perf TBD on first run).*

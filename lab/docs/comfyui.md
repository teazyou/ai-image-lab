# ComfyUI — how to operate our install

Generative backbone, headless/API-driven. **Why/when to use it & all MPS world-knowledge:**
[lab/wikis/comfyui/](../wikis/comfyui/README.md). This page is only our working commands.

- **Install:** git+`uv` venv at `lab/downloads/tools/comfyui/` · ComfyUI **0.26.0** · Python 3.12 · torch 2.12.1 (MPS).
- **No autostart.** Nothing runs at login/boot — no LaunchAgent, no login item. Launch on demand only (below).

## Launch (headless, on demand)

```bash
cd lab/downloads/tools/comfyui
export PYTORCH_ENABLE_MPS_FALLBACK=1 PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export HF_HOME="$PWD/../../cache/huggingface"        # keep caches in-repo
.venv/bin/python main.py --force-fp16 --use-split-cross-attention \
  --disable-auto-launch --listen 127.0.0.1 --port 8188
```
Ready when `GET http://127.0.0.1:8188/system_stats` returns 200 (~10 s cold). Flags are
mandatory on this M4 Max — rationale + the `--force-channels-last` crash to avoid: see wiki.
Stop it with Ctrl-C (or `pkill -f comfyui/main.py`); it does not linger across reboots.

## Pilot it from a script

`lab/scripts/comfyui_run.py` is our standard client: upload inputs → `POST /prompt` →
poll `/history` → save result images. Run it with the venv (needs `requests`):

```bash
lab/downloads/tools/comfyui/.venv/bin/python lab/scripts/comfyui_run.py WORKFLOW.json \
  --upload test_img.png=PATH --upload test_mask.png=PATH --out OUTDIR
```
Workflow must be **API format** (UI → Dev Mode → "Save (API Format)"), i.e. a flat
`{node_id: {class_type, inputs}}` object. Edges are `["src_node_id", output_index]`.

## Raw HTTP API (what the client uses)

| Call | Purpose |
|------|---------|
| `GET /system_stats` | health + versions (readiness probe) |
| `GET /object_info` / `/object_info/<Node>` | node catalog + exact input names (792 nodes). Ground workflows in this, don't guess param names. |
| `POST /upload/image` (multipart `image=`) | put a file in the input dir; returns its name for `LoadImage` |
| `POST /prompt` `{prompt, client_id}` | enqueue; returns `prompt_id`. Non-200 body = validation error |
| `GET /history/{prompt_id}` | poll until `outputs` present; `status.status_str=="error"` on failure |
| `GET /view?filename=&type=output[&subfolder=]` | fetch the result bytes |
| `ws://…/ws?clientId=` | optional live progress (`progress`/`executing`; done = `executing` node:null). Our client polls `/history` instead — zero extra deps. |

## Installed model — inpaint / outpaint

`models/checkpoints/sd_xl_base_1.0_inpainting_0.1.safetensors` (6.5 GB, FP16, SDXL) — the
official SDXL Inpainting 0.1 as a single-file checkpoint. Load with `CheckpointLoaderSimple`.

- **Inpaint:** `LoadImage` + `LoadImageMask`(channel `red`, white=region to fill) →
  `VAEEncodeForInpaint`(grow_mask_by 6) → `KSampler`(denoise 1.0) → `VAEDecode` → `SaveImage`.
- **Outpaint:** same graph but feed image through `ImagePadForOutpaint`(left/top/right/bottom,
  feathering 40); use *its* IMAGE+MASK outputs into `VAEEncodeForInpaint`.

**Flux Fill (better, not installed):** `black-forest-labs/FLUX.1-Fill-dev` is **gated** (needs an
accepted BFL licence + HF token; ~34 GB FP16 stack). No token here → used SDXL fallback. To add
Flux Fill later: `export HF_TOKEN=…`, accept the licence, fetch the FP16 transformer + `t5xxl_fp16`
+ `clip_l` + flux `ae.safetensors`. FP8 will NOT run on MPS (wiki).

## Measured on this machine (M4 Max, 48 GB, 20 steps, euler/normal)

| Task | Resolution | Sampling | Wall (client, incl. load) |
|------|-----------|----------|---------------------------|
| Inpaint | 1024×1024 | ~1.5 s/it | 44 s (first run, +model load) |
| Outpaint | 1536×1024 | ~3.2 s/it | 68 s |

Model loads **directly to GPU** (MPS confirmed). First prompt pays a one-time checkpoint load.

## Gotchas (operational — install-specific; MPS world-gotchas are in the wiki)

- **New model files** dropped into `models/checkpoints/` after boot ARE picked up (dir mtime
  rescanned); `GET /object_info/CheckpointLoaderSimple` lists what's visible.
- `--listen 127.0.0.1` keeps it local-only. Single process = sequential queue; parallel needs
  multiple processes/ports.
- **Pad dims must leave the padded canvas ÷8** for the VAE. `ImagePadForOutpaint` pads are ÷8 (step 8),
  so the *base* image must also be ÷8 — else mask/pixel size mismatch. Pre-crop the input to ÷8 first
  (e.g. 1226→1224h). Outpaint at native scale (~1–1.6 MP total) gave clean SDXL results here.
- **Outpaint invents a "floor" + bg box (cutout pipelines).** SDXL outpaint of a portrait with
  denoise 1.0 fills new area with a lighter *ground/floor slab* under the subject and a rectangular
  tone-seam at the feather edge. If you then `rembg` the result, the bg seam is harmless (removed) but
  the floor survives as a **translucent mid-alpha slab** — looks like a white veil over the lower
  character on a black composite. It's mid-alpha, so a plain alpha threshold can't drop it without
  eating hair. Remove it by **HSL**: it's low-saturation + mid-brightness neutral gray, unlike
  saturated hair / near-black dress. Mask `(sat<18% AND light>22%)` *restricted to the lower region*
  (no skin there) and subtract from alpha; then feather the bottom edge. Worked example:
  ```bash
  magick cut.png -alpha off -colorspace HSL -channel G -separate sat.png   # G=saturation
  magick cut.png -alpha off -colorspace HSL -channel B -separate light.png # B=lightness
  magick sat.png -threshold 18% -negate lowsat.png; magick light.png -threshold 22% bright.png
  magick lowsat.png bright.png -compose Multiply -composite fogcand.png
  magick -size WxH canvas:black -fill white -draw "rectangle 0,Y0 W,H" -blur 0x10 region.png
  magick fogcand.png region.png -compose Multiply -composite -blur 0x2 fogmask.png
  magick cut.png -alpha extract \( fogmask.png -negate \) -compose Multiply -composite a.png
  magick cut.png a.png -compose CopyOpacity -composite cut_defloored.png
  ```
  Then drop now-isolated strays (connected-components area-threshold) and compose with
  `lab/scripts/compose_wallpaper.sh` (bottom feather hides the residual edge naturally).

## Text→image: anime character design-transfer + posing (IP-Adapter + ControlNet OpenPose)

Stack to **generate a full-body anime character that carries a reference image's design in a new pose.**
World-knowledge (picks/weights/why): [lab/wikis/anime-character-gen/](../wikis/anime-character-gen/README.md). This = our working setup.

- **Custom nodes** (`custom_nodes/`): `ComfyUI_IPAdapter_plus` (cubiq) · `comfyui_controlnet_aux` (Fannovel16). Install/uninstall: see `lab/_installed.md`.
- **Models** (catalog): checkpoints/`Illustrious-XL-v2.0` · ipadapter/`ip-adapter-plus_sdxl_vit-h` · clip_vision/`CLIP-ViT-H-14-laion2B-s32B-b79K` · controlnet/`controlnet-openpose-sdxl-xinsir`.

**Graph (API format):** `CheckpointLoaderSimple`→2×`CLIPTextEncode`. `LoadImage(ref)`+`IPAdapterModelLoader`+`CLIPVisionLoader`→`IPAdapterAdvanced` (patches **MODEL**; weight 0.7–0.85, weight_type `linear`, embeds_scaling `V only`). `LoadImage(pose skeleton)`→`ControlNetApplyAdvanced` (patches +/− **CONDITIONING**; control_net=xinsir, strength 0.85–0.9, start 0, end 0.8–0.85). →`KSampler` (model from IPAdapter; pos/neg from ControlNet; **euler_ancestral / normal / cfg 4.5–5 / 30 steps**)→`VAEDecode`→`SaveImage`. SDXL portrait **832×1216**.

**DWPose (extract a skeleton from a pose ref):** `DWPreprocessor` — set **`scale_stick_for_xinsr_cn=enable`** (xinsir needs thick lines) + resolution 1024. Runtime `CUDAExecutionProvider` warning is harmless (uses CoreML). First use auto-downloads yolox+dwpose (~336 MB) to `comfyui_controlnet_aux/ckpts/`. To reuse a **pre-made** skeleton, feed it straight to `ControlNetApplyAdvanced.image` (skip the preprocessor). Reframe a skeleton to a portrait canvas with `magick … -trim -resize x<H> -gravity center -extent 832x1216`.

**Gotchas (this stack):**
- **NoobAI-XL v-pred = BROKEN on this MPS install.** `ModelSamplingDiscrete v_prediction` (zsnr **on and off**) + `RescaleCFG`, euler/euler_a → pure noise / incoherent shards. Root cause unconfirmed (suspect `--force-fp16` × v-pred). **Use eps-prediction checkpoints (Illustrious) on MPS;** revisit v-pred later with `--fp32` / a v-pred-aware sampler.
- **IP-Adapter center-crops the ref to a square** → pre-pad a tall portrait ref to a square (black bars) first (`magick in.jpg -background black -gravity center -extent SxS out.png`), else the head/ears fall outside the embedding.
- IP-Adapter likeness ≠ identity: it transfers design/palette, **not the exact face/art-style** — output is recognizably-the-design but a re-render, not the original artwork.
- `output/` + `input/` here are ComfyUI scratch — clean them; real results go via `comfyui_run.py --out` into `.cache/<job>/` or `outputs/`.

**Perf (M4 Max, warm):** 832×1216, batch 4, 30 steps euler_a, checkpoint+IP-Adapter+ControlNet ≈ **6 min/batch** (~1.5 min/img). First batch pays one-time loads (checkpoint 6.9 GB + CLIP-vision 2.4 GB + ControlNet 2.4 GB).

*Last updated: 2026-06-25*

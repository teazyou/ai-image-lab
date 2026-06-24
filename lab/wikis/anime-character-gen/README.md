# Anime character generation — SDXL + IP-Adapter + ControlNet (ComfyUI, MPS)

World-knowledge for **generating a full-body anime character in a chosen pose while preserving a
reference design** (e.g. turn a bust into a full-body wallpaper). Operational commands/graph live in
[lab/docs/comfyui.md](../../docs/comfyui.md). Pipeline = anime SDXL checkpoint + IP-Adapter (carry
identity/design) + ControlNet OpenPose (impose pose). All SDXL-arch so they stack.

## Why this stack (not outpaint)
Outpainting a bust **cannot** invent a coherent lower body — it fills with a floor slab + smudge
(see comfyui.md outpaint gotcha). To get a *new* full body you must **generate fresh**: text prompt
for anatomy/pose, IP-Adapter to keep the character's look, ControlNet OpenPose to lock head-to-toe
framing + a dynamic pose. Then cut out (rembg `isnet-anime`) and composite on pure black.

## Checkpoint (anime SDXL, free/ungated)
| Pick | Repo | pred | Note |
|------|------|------|------|
| **Illustrious-XL v2.0** (used) | `OnomaAIResearch/Illustrious-XL-v2.0` (6.94 GB) | eps | cleanest anatomy, best NL+booru, broadest IP-Adapter/ControlNet/LoRA ecosystem → most reliable when stacking conditioners |
| NoobAI-XL V-Pred 1.0 | `Laxhar/noobai-XL-Vpred-1.0` (7.11 GB) | **v-pred** | strongest native HDR/ember drama *on paper*, BUT **produced pure noise on this MPS install** (`ModelSamplingDiscrete=v_prediction` zsnr on & off, +`RescaleCFG`, euler/euler_a). **Avoid v-pred on MPS** until root-caused — use the eps path. See [docs/comfyui.md](../../docs/comfyui.md). |
| Animagine XL 4.0 | `cagliostrolab/animagine-xl-4.0` (6.94 GB) | eps | flatter "official anime"; weaker for semi-real |

- **Prompting = Danbooru tags first:** `masterpiece, best quality, newest, absurdres, <subject tags>`.
  Illustrious also takes natural language. Neg: `worst quality, low quality, bad anatomy, jpeg artifacts, …`.
- **Sampler/steps/cfg:** Euler / Euler a, **no Karras** for v-pred; **CFG 4.5–6**, **24–30 steps**, 1024-bucket res (portrait 832×1216 / 768×1344 for a standing full body).
- Both picks ship a **baked fp16-fixed VAE** → the SDXL fp16 black-VAE bug doesn't bite; if it ever does, launch `--fp32-vae`.

## IP-Adapter (preserve the character's design)
- Node: **cubiq/ComfyUI_IPAdapter_plus** (no pip deps; pure torch on MPS).
- **Use `ip-adapter-plus_sdxl_vit-h.safetensors`** (the *plus* model: fine-grained patch embeds → keeps
  hair/ears/outfit/palette, the whole design — not just a face). `-plus-face` crops to the face (photoreal
  portraits), wrong for full-body anime.
- Encoder: **CLIP-ViT-H-14** = `h94/IP-Adapter .../models/image_encoder/model.safetensors` (2.41 GB)
  renamed to `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` in `models/clip_vision/` (Unified Loader needs
  that exact name; legacy loader takes any).
- Node **IPAdapter Advanced**, `weight_type=linear`, **weight ≈ 0.7–0.9** (start 0.8). ↓ if it fights the
  pose, ↑ if design drifts. A bust reference biases toward portrait framing → lean on ControlNet to force full body.
- **Skip FaceID/InstantID on Mac:** needs insightface (CPU-only, painful build) AND its detector wants a
  *photo* face — fails on anime art anyway. The plus adapter is the right tool.

## ControlNet OpenPose (impose the pose)
- Model: **`xinsir/controlnet-openpose-sdxl-1.0`** → `diffusion_pytorch_model.safetensors` (2.50 GB), the
  community SOTA SDXL pose CN. (`twins`/ProMax variants = skip for pose-only.)
- Preprocessor node: **Fannovel16/comfyui_controlnet_aux**. **Install gotcha:** its `requirements.txt`
  pins `onnxruntime-gpu` (CUDA, no Mac wheel) → strip that line, install plain **`onnxruntime`** (ships
  CoreMLExecutionProvider → DWPose accelerated). Auto-downloads yolox+dwpose (~400 MB) to its `ckpts/`.
- **DWPreprocessor**: the `CUDAExecutionProvider` warning is harmless (falls through to CoreML/CPU).
  **CRITICAL: set `scale_stick_for_xinsr_cn = ON`** — xinsir was trained on thick pose lines; thin default
  skeletons make pose control unstable.
- Apply via **ControlNetApplyAdvanced**: **strength ~0.8, start 0.0, end ~0.8** (release control before the
  last steps so the model finishes anatomy freely → strong pose, not rigid).
- You DO need a preprocessor: a pose reference image's pixels → skeleton before the CN. To fill a portrait
  frame, crop the pose source tight to the figure (a landscape full-body ref → pad the skeleton to 832×1216).

## Graph (txt2img + both conditioners)
`CheckpointLoaderSimple → (CLIPTextEncode ×2) ` ; `LoadImage(ref design) → IPAdapter Advanced(model, clip_vision)` ;
`LoadImage(pose) → DWPreprocessor → ControlNetApplyAdvanced(+,−, CN model)` → `KSampler(model from IPAdapter) → VAEDecode → SaveImage`.
IP-Adapter patches the MODEL; ControlNet patches the CONDITIONING — both feed one KSampler.

## Measured on this machine (M4 Max, 2026-06-25)
- **Illustrious eps path works** and is reliable: 832×1216, batch 4, 30 steps euler_a, +IP-Adapter +ControlNet ≈ **6 min/batch warm** (~1.5 min/img).
- **NoobAI v-pred → noise** (see checkpoint table) — eps only on MPS.
- IP-Adapter at 0.7–0.85 carries hair-colour/ears/outfit/palette but renders a **new face in the model's style** — good for "her design", not for "the identical artwork". For *identical* subject, don't generate the figure: keep the original pixels and only outpaint what's outside its frame.

*Last verified: 2026-06-25 (URLs curl-checked ungated; perf measured).*

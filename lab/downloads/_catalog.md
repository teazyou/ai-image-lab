# lab/downloads/_catalog.md — downloaded-asset catalog

Tracked catalog of heavy assets under `lab/downloads/` (the files themselves are git-ignored). Lets any
session answer "do we already have X, and where?" without re-fetching. Rules: see CLAUDE.md §4.

## Models & weights

| Asset | Type | For (tool / task) | Size | Path | Source (URL / repo) | Added |
|-------|------|-------------------|------|------|---------------------|-------|
| isnet-anime.onnx | model | rembg — anime/drawn-art bg removal | 176 MB | `lab/downloads/cache/u2net/isnet-anime.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |
| birefnet-general.onnx | model | rembg — SOTA general bg removal; best on busy/blended scenes | 973 MB | `lab/downloads/cache/u2net/birefnet-general.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |
| u2net_human_seg.onnx | model | rembg — human-body seg (note: misses anime characters) | 176 MB | `lab/downloads/cache/u2net/u2net_human_seg.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |
| sam_vit_b_01ec64.encoder.onnx | model | rembg `sam` — click-to-select encoder (ViT-B) | 359 MB | `lab/downloads/cache/u2net/sam_vit_b_01ec64.encoder.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |
| sam_vit_b_01ec64.decoder.onnx | model | rembg `sam` — click-to-select decoder | 16 MB | `lab/downloads/cache/u2net/sam_vit_b_01ec64.decoder.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |
| sd_xl_base_1.0_inpainting_0.1.safetensors | checkpoint | ComfyUI — SDXL inpaint/outpaint (FP16, single-file); SDXL Inpainting 0.1. Flux Fill fallback (gated) | 6.5 GB | `lab/downloads/tools/comfyui/models/checkpoints/` | huggingface.co/wangqyqq/sd_xl_base_1.0_inpainting_0.1.safetensors (ungated) | 2026-06-25 |
| Illustrious-XL-v2.0.safetensors | checkpoint | ComfyUI — anime SDXL txt2img/img2img (eps-pred); **reliable on MPS** | 6.9 GB | `…/models/checkpoints/` | huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0 | 2026-06-25 |
| NoobAI-XL-Vpred-v1.0.safetensors | checkpoint | ComfyUI — anime SDXL (v-pred). **BROKEN on MPS → noise** (see [docs/comfyui.md](../docs/comfyui.md)); safe to delete | 7.1 GB | `…/models/checkpoints/` | huggingface.co/Laxhar/noobai-XL-Vpred-1.0 | 2026-06-25 |
| ip-adapter-plus_sdxl_vit-h.safetensors | model (IP-Adapter) | ComfyUI — carry a ref image's design/identity onto a generation | 808 MB | `…/models/ipadapter/` | huggingface.co/h94/IP-Adapter `sdxl_models/` | 2026-06-25 |
| CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors | model (CLIP vision) | image encoder paired with the vit-h IP-Adapter | 2.4 GB | `…/models/clip_vision/` | huggingface.co/h94/IP-Adapter `models/image_encoder/model.safetensors` (renamed) | 2026-06-25 |
| controlnet-openpose-sdxl-xinsir.safetensors | ControlNet | ComfyUI — SDXL OpenPose pose control (xinsir, SOTA) | 2.5 GB | `…/models/controlnet/` | huggingface.co/xinsir/controlnet-openpose-sdxl-1.0 `diffusion_pytorch_model.safetensors` (renamed) | 2026-06-25 |
| DWPose (yolox_l + dw-ll_ucoco) | model | comfyui_controlnet_aux DWPreprocessor (auto-downloaded on first use) | 336 MB | `…/custom_nodes/comfyui_controlnet_aux/ckpts/` | hf hr16/* + yzd-v/DWPose (auto) | 2026-06-25 |

_Type = checkpoint · LoRA · VAE · ControlNet · embedding · upscaler · model · …_
rembg auto-downloads models into `$U2NET_HOME` → `lab/downloads/cache/u2net/` (kept in-repo, ignored).

## Datasets

| Dataset | For | Size | Path | Source | Added |
|---------|-----|------|------|--------|-------|
| _none yet_ |   |   |   |   |   |

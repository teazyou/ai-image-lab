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

*Last updated: 2026-06-25*

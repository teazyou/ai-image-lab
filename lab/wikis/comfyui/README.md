# ComfyUI — generative backbone evaluation

Scope: is ComfyUI the right backbone for this lab (free, local, M4 Max 48 GB MPS, agent-piloted)?

## Verdict

- **Backbone: confirmed.** ComfyUI is the only free local tool with a purpose-built HTTP+WebSocket API, covering every generative task class the lab needs.
- **Not a replacement** for rembg (bg-removal) or ImageMagick (mechanical ops) — those remain faster and simpler for their task classes.
- **Pair with mflux** for simple Flux txt2img where raw speed matters; use ComfyUI when any compositing, masking, ControlNet, or multi-step pipeline is needed.
- **Skip Draw Things** as a backbone: ~20% faster on Mac, but GUI-first, no native HTTP server API — unusable by an autonomous agent.
- **FP16 models only** on this machine (FP8 unsupported on MPS; GGUF has unresolved dequant bitshift issues on MPS but may improve in PyTorch 2.12+).

## What ComfyUI is & does

Node-graph execution engine for diffusion models. Workflows are directed acyclic graphs (DAGs) serialized as compact JSON. Execution is lazy/cached — only re-runs nodes with changed inputs. Covers: txt2img, img2img, inpaint/outpaint, upscale (ESRGAN/SUPIR nodes), ControlNet, IP-Adapter, LoRA loading, SAM segmentation, video, regional prompting. MIT-licensed; weekly releases (v0.26.0 released 2026-06-23). 118k+ GitHub stars. Moved to Comfy-Org GitHub org.

## On Apple Silicon (M4 Max, MPS)

**Install paths:** Comfy Desktop (official DMG, beta, macOS 13+) or git+venv (more control; use `uv` with Python 3.10–3.12). Prefer git+venv for agent-driven lab.

**Required launch flags for M4 Max:**
```
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
python main.py --force-fp16 --use-split-cross-attention --disable-auto-launch
```
Do NOT use `--force-channels-last` (crashes on MPS: "required rank 4 tensor to use channels_last format"). Do NOT install xformers or Flash Attention (CUDA-only). Source: [apatero setup guide](https://apatero.com/blog/comfyui-mac-m4-max-complete-setup-guide-2025), [GH issue #10292](https://github.com/Comfy-Org/ComfyUI/issues/10292).

**Performance (M4 Max, sourced benchmarks — not yet verified on this machine):**

| Model | Resolution | Steps | Time |
|-------|-----------|-------|------|
| Flux.1-Dev FP16 | 1024×1024 | 30 | ~85 s |
| Flux.1-Schnell | 1024×1024 | 4 | ~8–12 s |
| SDXL FP16 | 1024×1024 | 25 | ~10–14 s |

Sources: [apatero M4 Max benchmark](https://www.apatero.com/blog/flux-apple-silicon-m1-m2-m3-m4-complete-performance-guide-2025), [apatero M4 Max setup](https://apatero.com/blog/comfyui-mac-m4-max-complete-setup-guide-2025). RTX 4090 equivalent: ~3.8–7x faster (unavoidable on Apple Silicon regardless of tool).

**MPS gotchas (all sourced):**
1. **FP8 unsupported** — MPS cannot convert `Float8_e4m3fn`. Always download FP16/BF16 variants. A manual CPU-offload patch exists (patches `comfy/float.py` + `comfy/quant_ops.py`) but must be re-applied after each ComfyUI update. Source: [GH issue #10292](https://github.com/Comfy-Org/ComfyUI/issues/10292), [discussion #13273](https://github.com/Comfy-Org/ComfyUI/discussions/13273).
2. **GGUF Q4_0 dequant bitshift** — `aten::__rshift__.Tensor` not implemented on MPS; PYTORCH_ENABLE_MPS_FALLBACK=1 defeats GPU for those ops. With 48 GB, full FP16 Flux (~24 GB) sidesteps GGUF entirely. Partial fixes in PyTorch 2.12+. Source: [ComfyUI-GGUF #27](https://github.com/city96/ComfyUI-GGUF/issues/27).
3. **BF16 regression** — M1–M3 lack hardware BF16 acceleration; wrong dtype can turn 80 s tasks into 10+ min. M4 Max has hardware BF16, so less exposed, but use `--force-fp16` defensively. Source: [lilting.ch March 2026](https://lilting.ch/en/articles/comfyui-qwen-mps-bf16-slowdown).
4. **CPU fallback ops** — `PYTORCH_ENABLE_MPS_FALLBACK=1` is required for unimplemented MPS ops (torch.nonzero, scatter, bicubic interpolate) but causes 0% GPU utilization on those ops. Use; accept overhead.
5. **Memory cap** — `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` prevents Metal from capping allocation below available RAM; needed for 24 GB+ models.
6. **Draw Things** is ~20% faster than ComfyUI MPS on same hardware; **mflux** (MLX-native) also faster for Flux. ComfyUI's API composability is its advantage, not raw speed. Sources: [heyuan110.com benchmark](https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation/), [Draw Things Metal FlashAttention](https://engineering.drawthings.ai/p/metal-flashattention-2-0-pushing-forward-on-device-inference-training-on-apple-silicon-fe8aac1ab23c).

## vs our current tools

| Task | Current tool | ComfyUI | Winner / why |
|------|-------------|---------|--------------|
| Mechanical resize / crop / pad / format | ImageMagick (`magick`) | Node wraps ImageMagick anyway; 10–15 s server cold-start overhead | **ImageMagick** — millisecond CLI, zero overhead |
| Background removal | rembg (ONNX) | ComfyUI-RMBG node; BiRefNet **hangs at 0% on Apple Silicon MPS** (GH #200, unresolved Apr 2026); RMBG-2.0/BEN2 work | **rembg** — BiRefNet MPS hang blocks the best ComfyUI-RMBG model; rembg's `-m birefnet-general` flag already closes the quality gap |
| Upscale (single image) | Real-ESRGAN (planned, standalone) | ESRGAN upscale node — same model, 2.4× slower, 48–55× more RAM for batch | **Standalone Real-ESRGAN** — identical quality, faster, less RAM; neither has merged MPS support (falls back to CPU) |
| Upscale inside a generative pipeline | n/a | Upscale node after txt2img in one workflow | **ComfyUI** — server already warm, amortized cost |
| txt2img | nothing | Full Flux/SDXL pipeline | **ComfyUI** (or mflux for speed) |
| Inpaint / outpaint | nothing | Flux Fill node, comfyui-inpaint-nodes, LaMa fast fill | **ComfyUI** — no alternative in current stack |
| ControlNet (pose/depth/canny) | nothing | Official ComfyUI ControlNet nodes, SDXL and Flux variants | **ComfyUI** |
| Style / character transfer | nothing | IP-Adapter Plus (explicit MPS provider support) | **ComfyUI** |
| img2img restyle | nothing | Core primitive, ~12 s SDXL on M4 Max | **ComfyUI** |

## Unique value it adds

All capabilities below have no approximation in the current toolset.

| Capability | Node / model | Free + local? | MPS feasible? |
|-----------|-------------|--------------|---------------|
| **Inpaint** (object removal / fill) | Flux Fill, comfyui-inpaint-nodes, LaMa | Yes | Yes — FP16 Flux Fill fits in 48 GB; ~85 s/pass |
| **Outpaint / reconstruction** | Flux Fill + Pad Image node | Yes | Yes — same as inpaint |
| **img2img restyle** | KSampler (denoise<1.0) + any checkpoint | Yes | Yes — SDXL ~12 s, Flux ~85 s |
| **ControlNet (pose/depth/canny)** | Flux Canny-dev, Flux Depth-dev, SDXL ControlNet | Yes | Yes — SDXL faster; Flux ~85 s/pass. XLabs sampler crashed on older ComfyUI; use native ComfyUI nodes instead |
| **IP-Adapter style/character transfer** | ComfyUI_IPAdapter_plus (MPS provider option) | Yes | Yes — explicit MPS support in loader |
| **Regional prompting** | DifferentialDiffusion (native node), RegionalPrompt (Impact Pack) | Yes | Yes — no CUDA dependency |
| **SAM-based masking in generative pipeline** | ComfyUI-Impact-Pack (SAM3 compatible) | Yes | Yes |

## Piloting it headlessly

ComfyUI is API-first by design — the browser UI is one HTTP client among many.

**Core agent flow:**
1. Launch: `python main.py --disable-auto-launch --listen 127.0.0.1 --port 8188`
2. Submit: `POST /prompt` with workflow JSON `{client_id, prompt: {node_id: {class_type, inputs}}}` → returns `{prompt_id}`
3. Track: WebSocket `ws://127.0.0.1:8188/ws?clientId=<uuid>` — events: `executing`, `progress`, `executed`, `execution_error`, `execution_cached`; completion signal is `executing` with `node: null`
4. Retrieve: `GET /history/{prompt_id}` → filenames; `GET /view?filename=...&type=output` → image bytes
5. For img2img/inpaint: `POST /upload/image` (multipart) → filename → inject into workflow JSON before submission
6. Introspect nodes: `GET /object_info` → full node class catalog

**Key agent gotcha:** UI save format ≠ API format. Must export with Dev Mode → "Save (API Format)". Node IDs are string keys; edges are `["source_node_id", output_index]` tuples.

**Workflow JSON is plain JSON** — trivially templated and mutated per-run (swap prompt, seed, resolution, model path, mask image, denoise level). No SDK required — `curl` or any HTTP client works.

**Concurrency:** single process = sequential queue. Parallel generation needs multiple ComfyUI processes.

**Alternatives and when to prefer them:**

| Tool | API surface | Speed on M4 Max | When to use |
|------|------------|----------------|-------------|
| **mflux** (MLX-native) | CLI / Python import only — no HTTP server | Faster than ComfyUI for Flux | Simple Flux txt2img where speed matters and no compositing needed |
| **Draw Things CLI** | Subprocess CLI — no HTTP server (app has optional API server, requires GUI app running) | ~20% faster than ComfyUI MPS | Not recommended as backbone; lacks persistent server API |
| **InvokeAI** | REST API but secondary feature; model support lags weeks–months | Similar | No advantage over ComfyUI for agent use |
| **A1111 / Forge** | Web UI with API as afterthought | Similar or slower on MPS | Not worth adding complexity |
| **SwarmUI** | Simpler POST /API/<route> but proxies ComfyUI underneath | Same (ComfyUI backend) | Extra layer, still beta; no gain |

Recommended: ComfyUI as persistent API backbone + mflux as subprocess fast-path for pure Flux txt2img.

## Open questions / to benchmark on this machine

- Actual Flux Schnell and Flux Dev speeds with the recommended flags on this specific M4 Max (48 GB, published numbers vary 8–85 s depending on config).
- Whether GGUF Flux Q4_K_S works acceptably on PyTorch 2.12+ (resolves GGUF MPS issue) or whether full FP16 must be used throughout.
- ComfyUI-RMBG BiRefNet MPS hang (GH #200): check if a newer version resolves it before routing bg-removal through ComfyUI.
- ComfyUI MLX extension: claimed 40–70% speedup over vanilla MPS for SD/SDXL — worth benchmarking; model coverage is limited.
- Real-ESRGAN MPS patch (community gist, not merged in xinntao/Real-ESRGAN#902): validate on this machine before committing to standalone upscale path.

## Sources

- [ComfyUI GitHub (Comfy-Org)](https://github.com/comfy-org/comfyui)
- [ComfyUI official docs](https://docs.comfy.org)
- [ComfyUI API / comms overview](https://docs.comfy.org/development/comfyui-server/comms_overview)
- [ComfyUI API developer guide (runflow.io)](https://www.runflow.io/blog/comfyui-api-developer-guide)
- [deepwiki — ComfyUI API & programmatic usage](https://deepwiki.com/Comfy-Org/ComfyUI/7-api-and-programmatic-usage)
- [apatero — M4 Max setup guide](https://apatero.com/blog/comfyui-mac-m4-max-complete-setup-guide-2025)
- [apatero — Flux Apple Silicon benchmark](https://www.apatero.com/blog/flux-apple-silicon-m1-m2-m3-m4-complete-performance-guide-2025)
- [GH issue #10292 — MPS FP8 + channels_last](https://github.com/Comfy-Org/ComfyUI/issues/10292)
- [GH discussion #13273 — FP8 MPS workaround](https://github.com/Comfy-Org/ComfyUI/discussions/13273)
- [ComfyUI-GGUF #27 — MPS bitshift issue](https://github.com/city96/ComfyUI-GGUF/issues/27)
- [ComfyUI-RMBG #200 — BiRefNet MPS hang](https://github.com/1038lab/ComfyUI-RMBG/issues/200)
- [Real-ESRGAN #902 — MPS support unmerged](https://github.com/xinntao/Real-ESRGAN/issues/902)
- [lilting.ch — BF16 MPS regression (Mar 2026)](https://lilting.ch/en/articles/comfyui-qwen-mps-bf16-slowdown)
- [heyuan110.com — Draw Things vs ComfyUI benchmark (Feb 2026)](https://www.heyuan110.com/posts/ai/2026-02-15-mac-mini-local-image-generation/)
- [mflux GitHub](https://github.com/filipstrand/mflux)
- [MacRumors M4 Max image gen thread](https://forums.macrumors.com/threads/m4m-and-m3u-for-image-generation-speed-sd-flux-etc.2454524/)
- [Flux Fill workflow (ComfyUI docs)](https://docs.comfy.org/tutorials/flux/flux-1-fill-dev)
- [comfyui-inpaint-nodes](https://github.com/Acly/comfyui-inpaint-nodes)
- [AI hardware — ComfyUI vs standalone ESRGAN batch benchmark](https://ai-hardware-zukan.com/en/comfyui-standalone-esrgan-video-4k-upscale-en/)

*Last verified: 2026-06-25*

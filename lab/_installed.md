# lab/_installed.md — Installed software / tools

Software/tools this lab installs (system packages, CLIs, apps, per-tool venvs) are recorded here so
they can be understood and cleanly removed. Their heavy files live under `lab/downloads/` and are
git-ignored.

> **Downloaded model files & datasets are cataloged in [`lab/downloads/_catalog.md`](downloads/_catalog.md)**,
> not here — check that before downloading anything.
>
> **How to *use* each tool** (CLI/API, settings, gotchas) is documented in [`lab/docs/`](docs/).

**Conventions**
- Add a row the moment you install something; include the **exact uninstall command**.
- Sizes are approximate — update when known.
- "Apple-Silicon" = confirmed working on this M4 Max (MPS), with any notes.

## Installed by the lab (safe to remove)

| Name | Type | Version | Installed | Size | Location | Source | Uninstall | Apple-Silicon |
|------|------|---------|-----------|------|----------|--------|-----------|---------------|
| uv | Python pkg/venv manager | 0.11.23 | 2026-06-24 | ~50 MB | Homebrew (`/opt/homebrew`) | `brew install uv` | `brew uninstall uv` | native arm64 ✓ |
| rembg | bg-removal CLI (ONNX) | 2.0.76 | 2026-06-24 | ~1.2 GB venv | `lab/downloads/tools/rembg/.venv` | `uv pip install "rembg[cpu,cli]"` | `rm -rf lab/downloads/tools/rembg` | CPU onnxruntime ✓ (no MPS needed for 1 img); see [lab/docs/rembg.md](docs/rembg.md) |
| ComfyUI | generative backbone (headless, HTTP API) | 0.26.0 | 2026-06-25 | ~1.3 GB venv (+models) | `lab/downloads/tools/comfyui` (git + `.venv`) | `git clone comfyanonymous/ComfyUI` + `uv venv --python 3.12` + `uv pip install -r requirements.txt` | `rm -rf lab/downloads/tools/comfyui` | MPS ✓ (torch 2.12.1; `--force-fp16`; loads to GPU). **No autostart.** Launch/API: [lab/docs/comfyui.md](docs/comfyui.md) |
| ComfyUI_IPAdapter_plus | ComfyUI node — IP-Adapter | git 2026-06-25 | small | `lab/downloads/tools/comfyui/custom_nodes/ComfyUI_IPAdapter_plus` | `git clone github.com/cubiq/ComfyUI_IPAdapter_plus` (no pip deps) | `rm -rf …/custom_nodes/ComfyUI_IPAdapter_plus` | MPS ✓ (pure torch; FaceID/insightface NOT used) |
| comfyui_controlnet_aux | ComfyUI node — DWPose/ControlNet preprocessors | git 2026-06-25 | deps + 336 MB ckpts | `…/custom_nodes/comfyui_controlnet_aux` | `git clone github.com/Fannovel16/comfyui_controlnet_aux` then `uv pip install --python .venv -r requirements.txt onnxruntime` (drop `onnxruntime-gpu`, see gotcha) | `rm -rf …/comfyui_controlnet_aux` | MPS ✓ DWPose via CoreML onnxruntime |
| onnxruntime (comfy venv) | ONNX runtime for DWPose | 1.27.0 | ~40 MB | comfyui `.venv` | `uv pip install --python lab/downloads/tools/comfyui/.venv onnxruntime` | `uv pip uninstall onnxruntime` | CoreMLExecutionProvider ✓ |
| fal-client | fal.ai API client (Python) | 1.0.0 | 2026-06-25 | ~21 MB venv | `lab/downloads/tools/fal/.venv` | `uv venv --python 3.12` + `uv pip install fal-client python-dotenv pillow requests` | `rm -rf lab/downloads/tools/fal` | pure-Python ✓ — calls remote **PAID** fal API. Key in repo-root `.env` (`FAL_KEY`). Script [lab/scripts/fal_run.py], docs [lab/docs/fal-api/](docs/fal-api/README.md) |
| Real-ESRGAN (via spandrel) | image upscaler (super-resolution) | spandrel 0.4.2 · torch 2.12.1 · py3.12 | 2026-06-25 | ~2 GB venv (+64 MB model) | `lab/downloads/tools/realesrgan/.venv` | `uv venv --python 3.12` + `uv pip install spandrel torch torchvision pillow numpy` | `rm -rf lab/downloads/tools/realesrgan` | **MPS ✓** (256→1024 in 0.6s). spandrel sidesteps the original repo's basicsr/`functional_tensor` rot. Script [lab/scripts/upscale.py], docs [lab/docs/realesrgan.md](docs/realesrgan.md) |

> **rembg install gotcha:** plain `rembg[cpu,cli]` backtracks `numba` to 0.53.1 (Python <3.10 only) and fails on Py 3.12. Add `"numba>=0.60" "llvmlite>=0.43"` to the install. Full recipe in [lab/docs/rembg.md](docs/rembg.md).
>
> **comfyui_controlnet_aux install gotcha:** its `requirements.txt` pins `onnxruntime-gpu` (CUDA-only, no macOS-arm64 wheel → `uv` resolve fails). Install with that line stripped + plain `onnxruntime` (ships CoreMLExecutionProvider). DWPose's runtime `CUDAExecutionProvider` warning is harmless. See [lab/docs/comfyui.md](docs/comfyui.md).

## Pre-existing system tools (NOT installed by the lab — do not remove)

| Name | Version | Notes |
|------|---------|-------|
| ImageMagick | 7.1.2 (`magick`) | resize / crop / ratio / format without AI |
| Homebrew | 6.0.3 | system package manager |
| Node | 24.15 | |
| git | 2.50.1 | |
| Python (system) | 3.9.6 | too old for AI tooling — use `uv` instead |

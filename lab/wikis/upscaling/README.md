# Upscaling / super-resolution (world knowledge)

How to do image upscaling locally & free on this M4 Max (MPS, no CUDA), and why we chose
the tool we did. Operating instructions live in [docs/realesrgan.md](../../docs/realesrgan.md).

## Decision: run Real-ESRGAN weights through **spandrel**

spandrel is the model-loader used by ComfyUI/chaiNNer — actively maintained (v0.4.2,
2026-02), modern-torch-clean, MPS-tested, loads Real-ESRGAN `.pth` directly (auto-detects
RRDBNet/SRVGGNetCompact). It's the only well-maintained PyTorch path that gets real MPS speed.

### Options considered

| Option | Verdict | Why |
|--------|---------|-----|
| **spandrel + RealESRGAN_x4plus** | ✅ chosen | maintained; deps = torch/torchvision/safetensors/numpy/einops only (no basicsr → no rot); explicit `.to("mps")` |
| original `xinntao/Real-ESRGAN` Python repo | ❌ | abandoned (2024-04); `basicsr` imports removed `torchvision.transforms.functional_tensor` → breaks modern torchvision; its script doesn't select MPS (silent CPU) |
| `realesrgan-ncnn-vulkan` prebuilt (no Python) | ❌ | official macOS build is 2022 Intel-only (Rosetta), no arm64 asset / brew formula; arm64 binary only inside upscayl GUI backend (awkward + Gatekeeper) |
| maintained PyTorch fork w/ drop-in CLI | ❌ | none exists — spandrel *is* the modern PyTorch path |

## MPS reality

Real-ESRGAN is conv-heavy (RRDBNet/SRVGGNet) → MPS **does** accelerate it. The "Real-ESRGAN
runs on CPU on Mac" reputation is specifically the *original script* failing to select MPS,
not a torch limitation. With explicit `.to("mps")`: 256→1024 (4x) ≈ 0.6s here.

## Model choice

- General photo: **RealESRGAN_x4plus** (default).
- Lightweight/fast general: realesr-general-x4v3 (~5 MB).
- Anime/line-art: RealESRGAN_x4plus_anime_6B.
- Need 2x not 4x: RealESRGAN_x2plus, or downscale the 4x result (Lanczos) — what `--scale` does.
- Plain non-AI enlargement (no detail synthesis) → ImageMagick `-resize` is fine and instant.

## Links

- spandrel: github.com/chaiNNer-org/spandrel
- weights: github.com/xinntao/Real-ESRGAN/releases

*Last verified: 2026-06-25*

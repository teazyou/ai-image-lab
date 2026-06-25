# Real-ESRGAN (via spandrel) — local image upscaler

Super-resolution on Apple Silicon (M4 Max, MPS). We run Real-ESRGAN weights through
**spandrel** (the loader ComfyUI/chaiNNer use), not the original `xinntao/Real-ESRGAN`
repo — that repo is abandoned and its `basicsr` dep imports the removed
`torchvision.transforms.functional_tensor`, which breaks on modern torchvision. spandrel
pulls only torch/torchvision/safetensors/numpy/einops, so that rot never appears, and it
gets real MPS acceleration. (Why this path: see [wiki](../wikis/upscaling/README.md).)

## How to run

Use the realesrgan venv (it has spandrel, torch, torchvision, pillow, numpy):

```bash
lab/downloads/tools/realesrgan/.venv/bin/python lab/scripts/upscale.py IN OUT [opts]
```

- Default model = `lab/downloads/models/realesrgan/RealESRGAN_x4plus.pth` (general photo, **4x**).
- Default device = `mps`; tiling on (tile 512, overlap 16) so large inputs don't OOM.

```
upscale.py <input> <output>
  --model PATH     spandrel .pth/.safetensors (default RealESRGAN_x4plus)
  --scale N        desired TOTAL scale; if ≠ model's native scale, the native
                   result is resampled (Lanczos). Omit to keep native (4x).
  --tile 512       tile size in input px (lower if OOM)
  --overlap 16     feathered tile overlap in input px
  --device mps|cpu (default mps)
```

Examples:
```bash
# default 4x
upscale.py inputs/small.png outputs/big.png
# only 2x from the 4x model (downscales the 4x result)
upscale.py in.png out.png --scale 2
```

## Models

Default `RealESRGAN_x4plus.pth` (64 MB) is the general-photo 4x. Other Real-ESRGAN weights
load via `--model` (catalog them in `lab/downloads/_catalog.md` if fetched):
`realesr-general-x4v3` (~5 MB, faster), `RealESRGAN_x4plus_anime_6B` (anime), `RealESRGAN_x2plus`.
Any spandrel-supported SR model works.

## Apple-Silicon notes

- `PYTORCH_ENABLE_MPS_FALLBACK=1` is set in-process (before torch import); float32 throughout
  (Apple GPUs aren't fp16-optimized). No ops actually fell back in testing.
- Measured: 256→1024 (4x) in **~0.6s** on MPS. Real photos at 1MP+ are seconds, not minutes.

## Gotchas & fixes

- **spandrel API (0.4.2):** `ModelLoader().load_from_file(path)` → `ImageModelDescriptor`.
  Use `desc.model` (raw `nn.Module`): `desc.model.to(device).eval()`, call `desc.model(t)`.
  Native factor is `desc.scale` (=4 for x4plus).
- **Native scale is fixed** — `--scale` only resamples afterward; it can't make the model
  upscale by a different native factor.
- **OOM on huge inputs** → lower `--tile` (e.g. 256). Tiling uses feathered overlap-blend, seamless.

*Last updated: 2026-06-25*

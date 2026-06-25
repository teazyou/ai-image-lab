#!/usr/bin/env python3
"""upscale.py — local image upscaler (Real-ESRGAN / any spandrel model) on MPS.

Loads a super-resolution model with spandrel and upscales one image, tiling the
work so large inputs don't OOM the GPU. Default model is RealESRGAN_x4plus (4x,
general photo); any spandrel-supported .pth/.safetensors works via --model.

Run with the realesrgan venv (has spandrel, torch, torchvision, pillow, numpy):
    lab/downloads/tools/realesrgan/.venv/bin/python lab/scripts/upscale.py IN OUT [opts]

The model has a fixed native scale (x4plus = 4x). --scale only matters if it
differs from native: the native-scale result is then resampled (PIL Lanczos) to
hit the requested factor. Omit --scale to keep the native factor.

Examples:
    # default 4x upscale on MPS
    upscale.py .cache/job/001_small.png outputs/big.png
    # want only 2x from a 4x model (downsamples the 4x result)
    upscale.py in.png out.png --scale 2
    # CPU fallback, bigger tiles, custom model
    upscale.py in.png out.png --device cpu --tile 768 --model lab/downloads/models/realesrgan/RealESRGAN_x4plus.pth
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Must be set before torch is imported so unsupported MPS ops fall back to CPU.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from spandrel import ModelLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = REPO_ROOT / "lab/downloads/models/realesrgan/RealESRGAN_x4plus.pth"


def pick_device(requested: str) -> str:
    if requested == "mps":
        if not torch.backends.mps.is_available():
            print("[warn] MPS not available, falling back to CPU", file=sys.stderr)
            return "cpu"
        return "mps"
    return requested


def load_model(path: Path, device: str):
    desc = ModelLoader().load_from_file(str(path))
    model = desc.model.to(device).eval()
    # spandrel stores the model's fixed upscale factor on the descriptor.
    scale = int(getattr(desc, "scale", 4) or 4)
    return model, scale


def _feather_mask(h: int, w: int, overlap: int) -> np.ndarray:
    """1.0 in the interior, linearly ramping to ~0 across `overlap` px at each
    edge — used to cross-fade tile borders so seams disappear."""
    ramp_v = np.ones(h, dtype=np.float32)
    ramp_h = np.ones(w, dtype=np.float32)
    if overlap > 0:
        r = (np.arange(overlap, dtype=np.float32) + 1) / (overlap + 1)
        n = min(overlap, h // 2)
        ramp_v[:n] = r[:n]
        ramp_v[h - n:] = r[:n][::-1]
        n = min(overlap, w // 2)
        ramp_h[:n] = r[:n]
        ramp_h[w - n:] = r[:n][::-1]
    return np.outer(ramp_v, ramp_h)[:, :, None]  # (h, w, 1)


@torch.no_grad()
def upscale_tiled(model, img: np.ndarray, scale: int, device: str,
                  tile: int, overlap: int) -> np.ndarray:
    """img: HxWx3 float32 [0,1] -> (H*scale)x(W*scale)x3 float32 [0,1].
    Processes overlapping tiles and blends them with a feathered mask so big
    images fit in memory and tile boundaries are seamless."""
    H, W, _ = img.shape
    out_h, out_w = H * scale, W * scale
    acc = np.zeros((out_h, out_w, 3), dtype=np.float32)
    wsum = np.zeros((out_h, out_w, 1), dtype=np.float32)

    step = max(1, tile - overlap)
    ys = list(range(0, H, step))
    xs = list(range(0, W, step))
    for y in ys:
        for x in xs:
            y0, x0 = y, x
            y1, x1 = min(y + tile, H), min(x + tile, W)
            patch = img[y0:y1, x0:x1, :]
            t = torch.from_numpy(patch.transpose(2, 0, 1)).unsqueeze(0).to(device)
            out = model(t).clamp(0, 1).squeeze(0).cpu().numpy().transpose(1, 2, 0)
            ph, pw, _ = out.shape
            mask = _feather_mask(ph, pw, overlap * scale)
            oy0, ox0 = y0 * scale, x0 * scale
            acc[oy0:oy0 + ph, ox0:ox0 + pw, :] += out * mask
            wsum[oy0:oy0 + ph, ox0:ox0 + pw, :] += mask
    wsum[wsum == 0] = 1.0
    return acc / wsum


def main() -> int:
    p = argparse.ArgumentParser(
        description="Upscale an image with a spandrel model (Real-ESRGAN) on MPS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", help="input image path")
    p.add_argument("output", help="output image path")
    p.add_argument("--model", default=str(DEFAULT_MODEL),
                   help=f"model file (default: {DEFAULT_MODEL})")
    p.add_argument("--scale", type=int, default=None,
                   help="desired total scale; if it differs from the model's "
                        "native scale, the result is resampled (Lanczos). "
                        "Default: model's native scale.")
    p.add_argument("--tile", type=int, default=512,
                   help="tile size in input px (default 512; lower if OOM)")
    p.add_argument("--overlap", type=int, default=16,
                   help="tile overlap in input px, feathered (default 16)")
    p.add_argument("--device", default="mps", choices=["mps", "cpu"],
                   help="compute device (default mps)")
    args = p.parse_args()

    in_path, out_path = Path(args.input), Path(args.output)
    if not in_path.exists():
        print(f"[error] input not found: {in_path}", file=sys.stderr)
        return 1
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"[error] model not found: {model_path}", file=sys.stderr)
        return 1

    device = pick_device(args.device)
    img_pil = Image.open(in_path).convert("RGB")
    in_w, in_h = img_pil.size
    img = np.asarray(img_pil, dtype=np.float32) / 255.0

    t0 = time.time()
    model, native_scale = load_model(model_path, device)
    out = upscale_tiled(model, img, native_scale, device,
                        tile=args.tile, overlap=args.overlap)

    # Resample to the requested total scale if it differs from native.
    target = args.scale if args.scale is not None else native_scale
    out_img = Image.fromarray((out * 255.0 + 0.5).clip(0, 255).astype(np.uint8))
    if target != native_scale:
        out_img = out_img.resize((in_w * target, in_h * target), Image.LANCZOS)
    elapsed = time.time() - t0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_img.save(out_path)

    ow, oh = out_img.size
    print(f"device : {device}")
    print(f"model  : {model_path.name}  (native x{native_scale})")
    print(f"input  : {in_w}x{in_h}")
    print(f"output : {ow}x{oh}  (x{target})")
    print(f"time   : {elapsed:.1f}s")
    print(f"saved  : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

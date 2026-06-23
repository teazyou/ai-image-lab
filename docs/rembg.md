# rembg — background removal (our setup)

ONNX-based background removal. Installed as an isolated `uv` venv at
`downloads/tools/rembg/.venv`. Version 2.0.76. See world-knowledge / model comparison in
[wikis/background-removal](../wikis/background-removal/README.md).

## Install (the recipe that actually works on Py 3.12 / Apple Silicon)

```bash
export UV_CACHE_DIR="$PWD/downloads/cache/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/downloads/cache/uv-python"
uv venv --python 3.12 downloads/tools/rembg/.venv
uv pip install --python downloads/tools/rembg/.venv \
  "rembg[cpu,cli]" "numba>=0.60" "llvmlite>=0.43"
```

- Use the **`cpu`** extra (onnxruntime CPU). No CUDA on this machine; `gpu` extra is NVIDIA-only.
  CPU is plenty for single images (~10–60 s incl. model load).

## Gotchas & fixes

- **`numba` backtrack (the big one).** Plain `rembg[cpu,cli]` resolves `pymatting → numba 0.53.1 →
  llvmlite 0.36`, which only supports Python <3.10 and **fails to build on 3.12**
  (`RuntimeError: Cannot install on Python version 3.12.x`). Fix: pin `"numba>=0.60"
  "llvmlite>=0.43"` in the install command (done above).
- **Keep model downloads in-repo.** rembg fetches models to `~/.u2net` by default. Set
  `U2NET_HOME="$PWD/downloads/cache/u2net"` so they land in the (ignored) repo cache and get
  cataloged in `downloads/_index.md`. First use of a model downloads it (isnet-anime ≈ 176 MB).

## CLI (working examples)

```bash
export U2NET_HOME="$PWD/downloads/cache/u2net"
BIN=downloads/tools/rembg/.venv/bin/rembg

# Single image -> transparent PNG. -m picks the model.
$BIN i -m isnet-anime input.jpg cutout.png      # anime / drawn art
$BIN i -m birefnet-general input.jpg cutout.png # photos, highest quality
$BIN i -m u2net_human_seg photo.jpg cutout.png  # people / portraits
```

- Models: `u2net`, `u2netp`, `u2net_human_seg`, `isnet-general-use`, `isnet-anime`,
  `birefnet-general`, `birefnet-general-lite`, `birefnet-portrait`, `silueta`, `sam`, …
- `i` = single file; `p` = process a folder; `s` = HTTP server. Omit output path → `<stem>.out.png`.

## Replace background with a solid color (e.g. plain black)

rembg gives a transparent cutout; composite it onto a solid canvas with ImageMagick. Compositing a
same-size cutout centered onto a fixed canvas guarantees the exact target resolution/ratio:

```bash
magick -size 1920x1080 canvas:black cutout.png -gravity center -composite -depth 8 out.png
```

Use `-depth 8` — otherwise the `canvas:` source can yield a 16-bit PNG (2–3× larger, non-standard).
Reusable wrapper: [`scripts/bg_to_color.sh`](../scripts/bg_to_color.sh).

*Last updated: 2026-06-24*

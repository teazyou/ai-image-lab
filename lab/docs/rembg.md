# rembg — background removal (our setup)

ONNX-based background removal. Installed as an isolated `uv` venv at
`lab/downloads/tools/rembg/.venv`. Version 2.0.76. See world-knowledge / model comparison in
[lab/wikis/background-removal](../wikis/background-removal/README.md).

## Install (the recipe that actually works on Py 3.12 / Apple Silicon)

```bash
export UV_CACHE_DIR="$PWD/lab/downloads/cache/uv"
export UV_PYTHON_INSTALL_DIR="$PWD/lab/downloads/cache/uv-python"
uv venv --python 3.12 lab/downloads/tools/rembg/.venv
uv pip install --python lab/downloads/tools/rembg/.venv \
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
  `U2NET_HOME="$PWD/lab/downloads/cache/u2net"` so they land in the (ignored) repo cache and get
  cataloged in `lab/downloads/_catalog.md`. First use of a model downloads it (isnet-anime ≈ 176 MB).
- **`birefnet-general` download is flaky (973 MB).** rembg's pooch/requests downloader doesn't
  resume; the GitHub release CDN resets mid-stream (`urllib3 IncompleteRead` / `Connection reset`),
  leaving a partial file and a crash. Fix: fetch the `.onnx` yourself with a curl resume-loop, then
  re-run rembg (it sees the cached file and skips the download):
  ```bash
  DEST="lab/downloads/cache/u2net/birefnet-general.onnx"; T=972666916
  URL="https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx"
  for i in $(seq 1 40); do
    [ "$(stat -f%z "$DEST" 2>/dev/null || echo 0)" -ge "$T" ] && break
    curl -sL --retry 3 --retry-delay 1 -C - -o "$DEST" "$URL" || true   # -C - = resume
  done
  ```
- **`birefnet-general` is RAM-heavy: ~14 GB peak per image** (RSS — ONNX decoder activations, *not*
  the 973 MB weights; resolution-independent, same at 1080p and 4K). vs ~4.5 GB `isnet-anime` /
  ~2.1 GB `u2net_human_seg` (measured 2026-06-26). It's the heaviest single op in the lab → run
  birefnet jobs **sequentially** (≤2 in parallel on this 48 GB Mac). Per-model table:
  [lab/wikis/background-removal](../wikis/background-removal/README.md).

## CLI (working examples)

```bash
export U2NET_HOME="$PWD/lab/downloads/cache/u2net"
BIN=lab/downloads/tools/rembg/.venv/bin/rembg

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
Reusable wrapper: [`lab/scripts/bg_to_color.sh`](../scripts/bg_to_color.sh).

## Dim the background instead of removing it

Keep the subject untouched, overlay a color over the rest at a chosen opacity (0.7 = "black @ 70%,
background stays faintly visible"; 1.0 = solid bg): [`lab/scripts/dim_background.sh`](../scripts/dim_background.sh).
Core trick = darken whole image, then paste the original cutout back on top. Because the background
is only *dimmed* (not cut to a hard edge against black), an imperfect matte is nearly invisible —
so the auto-models are "good enough" here even when they'd look rough on a pure-black composite.

## SAM — click-to-select a *specific* object (`-m sam`)

When auto-models grab too much (subject fused with a connected blob — snow, smoke, water) or too
little (a low-contrast limb dropped), use SAM with point prompts. Pass prompts as JSON via `-x`;
`label:1` = keep-point, `label:0` = exclude-point (coords are full-res pixels). `-om` = output mask
only. Models (ViT-B encoder 359 MB + decoder 16 MB) download on first use — **flaky, use the
resume-loop above** (same GitHub release host; files `sam_vit_b_01ec64.{encoder,decoder}.onnx`).

```bash
rembg i -m sam -om -x '{"sam_prompt":[
  {"type":"point","label":1,"data":[737,242]},   # keep: on the subject
  {"type":"point","label":0,"data":[207,553]}]}' \  # exclude: on the unwanted blob
  input.jpg mask.png
# rectangle prompt also supported: {"type":"rectangle","data":[x1,y1,x2,y2]}
```

SAM (ViT-B) masks are **coarse/grainy** — don't use them raw for a black composite. Combine with a
clean birefnet matte:
- **Over-segmentation** (birefnet kept a connected blob): `birefnet ∩ dilate(SAM)` keeps birefnet's
  crisp edge but cuts anything far from the SAM selection.
  `magick sam.png -threshold 40% -morphology Dilate Disk:20 dil.png; magick bfAlpha.png dil.png -compose Darken -composite mask.png`
- **Under-segmentation** (birefnet dropped a limb): `birefnet ∪ SAM` then close/open to clean.
  `magick bfAlpha.png sam.png -compose Lighten -composite u.png`
- **Drop floating strays:** `-define connected-components:area-threshold=30000 -define connected-components:mean-color=true -connected-components 8` (small disconnected bits merge to bg; the one big subject blob survives). Don't use `keep-top=1` — it can keep the *background* component.
- A pure-luminance mask is NOT a substitute when background and subject are similarly bright (e.g. a
  bright blanket behind bright skin) — it grabs the background. Use SAM there.

### Two-zone treatment (e.g. sky → black, foreground → dimmed)
Split the background with a feathered horizontal mask at the horizon, then paste the subject:
darken whole image (`-evaluate multiply 0.3`); build sky mask (`-size WxH xc:black -fill white
-draw "rectangle 0,0 W,HORIZON" -blur 0x18`); composite a black layer through that mask over the
dark base; finally composite the subject cutout on top.

*Last updated: 2026-06-26*

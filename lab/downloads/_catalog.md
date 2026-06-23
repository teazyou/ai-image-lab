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

_Type = checkpoint · LoRA · VAE · ControlNet · embedding · upscaler · model · …_
rembg auto-downloads models into `$U2NET_HOME` → `lab/downloads/cache/u2net/` (kept in-repo, ignored).

## Datasets

| Dataset | For | Size | Path | Source | Added |
|---------|-----|------|------|--------|-------|
| _none yet_ |   |   |   |   |   |

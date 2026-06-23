# downloads/ — asset catalog (models, weights, datasets)

Single source of truth for **downloaded assets**: model checkpoints, LoRAs, VAEs, ControlNets,
embeddings, upscalers, and datasets stored under `downloads/`. The asset files themselves are
git-ignored, but **this catalog is tracked** so any future session can answer *"do we already have
X, and where is it?"* without downloading it again.

> Installed **software/tools** (ComfyUI, rembg, `uv`, …) are listed in
> [`_installed.md`](../_installed.md), not here.

**Rules**
- **Check this file before downloading anything** — never re-fetch a model already listed.
- Add a row the moment a download completes (and before using it).
- If unsure a file still exists on disk, reconcile with `ls -lh downloads/models`.
- Models auto-downloaded into the HF cache (`downloads/cache/huggingface`) also belong here; you can
  cross-check the cache with `huggingface-cli scan-cache`.

## Models & weights

| Asset | Type | For (tool / task) | Size | Path | Source (URL / repo) | Added |
|-------|------|-------------------|------|------|---------------------|-------|
| _none yet_ |   |   |   |   |   |   |

_Type = checkpoint · LoRA · VAE · ControlNet · embedding · upscaler · …_

## Datasets

| Dataset | For | Size | Path | Source | Added |
|---------|-----|------|------|--------|-------|
| _none yet_ |   |   |   |   |   |

# downloads/_catalog.md — downloaded-asset catalog

Tracked catalog of heavy assets under `downloads/` (the files themselves are git-ignored). Lets any
session answer "do we already have X, and where?" without re-fetching. Rules: see CLAUDE.md §4.

## Models & weights

| Asset | Type | For (tool / task) | Size | Path | Source (URL / repo) | Added |
|-------|------|-------------------|------|------|---------------------|-------|
| isnet-anime.onnx | model | rembg — anime/drawn-art bg removal | 176 MB | `downloads/cache/u2net/isnet-anime.onnx` | github.com/danielgatis/rembg releases | 2026-06-24 |

_Type = checkpoint · LoRA · VAE · ControlNet · embedding · upscaler · model · …_
rembg auto-downloads models into `$U2NET_HOME` → `downloads/cache/u2net/` (kept in-repo, ignored).

## Datasets

| Dataset | For | Size | Path | Source | Added |
|---------|-----|------|------|--------|-------|
| _none yet_ |   |   |   |   |   |

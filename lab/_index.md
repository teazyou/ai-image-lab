# lab/_index.md — repository map

One line per path (written from the repo root). **Rules and how-to live only in
[.claude/CLAUDE.md](../.claude/CLAUDE.md)**, which imports this file so the map loads at session start.

**Root — kept lean for image content**
- `.claude/CLAUDE.md` — operating manual & all rules (the brain; read fully every session)
- `README.md` — human-facing project intro
- `inputs/` — drop-in source images (untracked, user-managed; recreate after a clone)
- `outputs/` — generated results, final images sit at the root (untracked, user-managed)
- `.cache/` — intermediate/temp files (cutouts, masks); git-ignored, `.gitkeep` only
- `lab/` — the AI workspace; everything below lives here

**lab/ — workspace root**
- `lab/_index.md` — this file: the map of every path in the repo
- `lab/_installed.md` — inventory of installed tools (version, size, uninstall cmd)

**lab/docs/ — how to operate OUR installed tools (CLI/API, gotchas)**
- `lab/docs/rembg.md` — rembg: install recipe, model choice, solid-color composite
- `lab/docs/comfyui.md` — ComfyUI: headless launch flags, HTTP API, client script, installed SDXL inpaint model, measured perf

**lab/wikis/ — world knowledge (concepts, research, tool/model comparisons)**
- `lab/wikis/background-removal/README.md` — bg-removal model comparison (isnet-anime / birefnet / u2net)
- `lab/wikis/precise-segmentation/README.md` — SOTA local interactive segmentation + matting (EfficientTAM/SAM2-3, BiRefNet, ComfyUI); for sub-part/low-contrast isolation rembg can't do
- `lab/wikis/comfyui/README.md` — ComfyUI evaluation: confirmed generative backbone (inpaint/outpaint/controlnet/ip-adapter via HTTP+WS API); complements rembg/ImageMagick, not a replacement; M4 Max/MPS flags + gotchas

**lab/scripts/ — reusable parametrized scripts (`--help` on each)**
- `lab/scripts/bg_to_color.sh` — remove background, composite subject onto a solid-color canvas
- `lab/scripts/dim_background.sh` — keep subject, overlay a color over the rest at a chosen opacity (dim, not remove)
- `lab/scripts/comfyui_run.py` — headless ComfyUI client: upload inputs, submit API-format workflow, poll, save results

**lab/downloads/ — heavy artifacts (content git-ignored)**
- `lab/downloads/_catalog.md` — catalog of downloaded models/datasets (check before downloading)
- `lab/downloads/models/` — hand-fetched checkpoints / LoRAs / VAEs / upscalers
- `lab/downloads/tools/` — per-tool `uv` venvs (e.g. `rembg`; `comfyui` = git checkout + venv)
- `lab/downloads/cache/` — tool-managed caches & auto-downloaded models (`HF_HOME`, `U2NET_HOME`, `uv`)
- `lab/downloads/datasets/` — datasets

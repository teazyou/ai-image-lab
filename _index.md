# _index.md — repository map

One line per path. **Rules and how-to live only in [.claude/CLAUDE.md](.claude/CLAUDE.md)**, which
imports this file so the map loads at session start.

**Root**
- `.claude/CLAUDE.md` — operating manual & all rules (the brain; read fully every session)
- `_index.md` — this file: the map of every path in the repo
- `_installed.md` — inventory of installed tools (version, size, uninstall cmd)
- `README.md` — human-facing project intro

**docs/ — how to operate OUR installed tools (CLI/API, gotchas)**
- `docs/rembg.md` — rembg: install recipe, model choice, solid-color composite

**wikis/ — world knowledge (concepts, research, tool/model comparisons)**
- `wikis/background-removal/README.md` — bg-removal model comparison (isnet-anime / birefnet / u2net)

**scripts/ — reusable parametrized scripts (`--help` on each)**
- `scripts/bg_to_color.sh` — remove background, composite subject onto a solid-color canvas

**inputs/ — drop-in source images (git-ignored, ephemeral)**

**outputs/ — generated results (git-ignored); final images sit at the root**
- `outputs/assets/` — intermediate/temp files (cutouts, masks)

**downloads/ — heavy artifacts (content git-ignored)**
- `downloads/_catalog.md` — catalog of downloaded models/datasets (check before downloading)
- `downloads/models/` — hand-fetched checkpoints / LoRAs / VAEs / upscalers
- `downloads/tools/` — per-tool `uv` venvs (e.g. `rembg`)
- `downloads/cache/` — tool-managed caches & auto-downloaded models (`HF_HOME`, `U2NET_HOME`, `uv`)
- `downloads/datasets/` — datasets

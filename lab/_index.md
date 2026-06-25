# lab/_index.md — repository map

One line per path (written from the repo root). **Rules and how-to live only in
[.claude/CLAUDE.md](../.claude/CLAUDE.md)**, which imports this file so the map loads at session start.

**Root — kept lean for image content**
- `.claude/CLAUDE.md` — operating manual & all rules (the brain; read fully every session)
- `.claude/settings.json` — Claude Code project settings; disables auto-memory (`autoMemoryEnabled: false`, see CLAUDE.md §8)
- `.claude/skills/api/SKILL.md` — `/api` skill (orchestrator): pre-flight, build the (image×model) cell list, then launch a background dynamic Workflow (`fanout.workflow.js`) that runs one Sonnet/high worker per cell; chainable via "same params: …"; relays results, never views/edits images. PAID → `disable-model-invocation` (explicit `/api` only)
- `.claude/skills/api/agent.md` — `/api` worker spec for ONE (model×image) cell: parse args → fal gen/edit (one of Grok/Google/OpenAI) → normalize to exact size+ratio → report once; on content-policy reject self-walks the fallback chain google↔openai then grok last (skips any models the orchestrator says already have their own cells). Self-contained (reads no docs)
- `.claude/skills/api/fanout.workflow.js` — `/api` dynamic-Workflow script: fans out one sub-agent per (image×model) cell on `model: sonnet`/`effort: high`, each reading `agent.md`; passes each cell's `skipFallback` (other models already covering this image) as a skip line, and optional `fallbackRule` (custom per-cell fallback chain) as a separate instruction line — never into the prompt. Cells passed in via Workflow `args`
- `.claude/skills/rule-of-thirds/SKILL.md` — `/rule-of-thirds` skill (orchestrator): parse percent + path, build the per-image cell list, then launch a background dynamic Workflow (`fanout.workflow.js`) that runs one Sonnet/xhigh vision worker per image; relays results, never views/shifts/QAs images. Local-only, auto-invocable
- `.claude/skills/rule-of-thirds/agent.md` — `/rule-of-thirds` worker spec for ONE image: parse args → decide left|right from the subject's facing (vision: look INTO the open space) → run the sibling shift script → QA → report once. Self-contained (reads no docs)
- `.claude/skills/rule-of-thirds/fanout.workflow.js` — `/rule-of-thirds` dynamic-Workflow script: fans out one sub-agent per image on `model: sonnet`/`effort: xhigh`, each reading `agent.md`. Cells passed in via Workflow `args`
- `.claude/skills/rule-of-thirds/rule_of_thirds_shift.sh` — the shift: move subject by P% of width toward a given dir on a solid-bg image; auto-detects bg color (top-left px), clamps so the subject never clips
- `.claude/skills/black-background/SKILL.md` — `/black-background` skill: keep the subject, turn the rest solid black, for one image or a whole folder. Per image picks the rembg model by subject (anime/person/photo; birefnet to keep dark appendages) then QAs; wraps `lab/scripts/bg_to_color.sh -c black`. Local-only, explicit-invoke
- `.claude/skills/sharpen-definition/SKILL.md` — `/sharpen-definition` skill (orchestrator): parse file/folder + optional `-parallels=N`, build the flat per-image cell list, then launch a background dynamic Workflow (`fanout.workflow.js`) that chops images into groups of ≤`max_images_per_groups` (default 10) and runs them through a pool of ≤`max_parallels_agents` (default 2, ≈8 GB RAM each) Sonnet/low **mechanical** workers — the pool starts the next waiting group as each finishes, each worker processing its group **sequentially**; relays results, never views/edits/QAs images. Local-only, auto-invocable
- `.claude/skills/sharpen-definition/agent.md` — `/sharpen-definition` worker spec for ONE GROUP of images: parse the path list → run the sibling script on each image **strictly sequentially, one at a time** (set 1080p + sharpen) → report once (one line per image). **No vision, no QA** (purely mechanical). Self-contained (reads no docs)
- `.claude/skills/sharpen-definition/fanout.workflow.js` — `/sharpen-definition` dynamic-Workflow script: two tweakable top-of-file knobs — `max_parallels_agents` (default 2, pool/RAM cap ≈8 GB each) & `max_images_per_groups` (default 10, per-worker cap); chops cells into ≤size groups and runs them through a fixed-size worker **pool** (≤N concurrent, refills next group on finish) of `model: sonnet`/`effort: low` sub-agents, each reading `agent.md` and processing its group **sequentially**. `-parallels=N` overrides the pool size; args = `{ cells, parallels? }`
- `.claude/skills/sharpen-definition/sharpen_definition.sh` — the pipeline: Real-ESRGAN 4× upscale → Lanczos downscale to 1080p (height, AR preserved) → light unsharp; writes `outputs/<stem>_1080p-sharp.png`, cleans own `.cache/` scratch
- `README.md` — human-facing project intro
- `.env` — secrets (git-ignored); holds `FAL_KEY` for fal.ai. Template: `.env.example` (tracked)
- `.env.example` — tracked template for `.env`
- `inputs/` — drop-in source images (untracked, user-managed; recreate after a clone)
- `outputs/` — generated results, final images sit at the root (untracked, user-managed)
- `.cache/` — temp/intermediate assets (cutouts, masks, experimental gens, working copies), **one subfolder per source image** (`.cache/<job>/`); git-ignored, `.gitkeep` only
- `lab/` — the AI workspace; everything below lives here

**lab/ — workspace root**
- `lab/_index.md` — this file: the map of every path in the repo
- `lab/_installed.md` — inventory of installed tools (version, size, uninstall cmd)

**lab/docs/ — how to operate OUR installed tools (CLI/API, gotchas)**
- `lab/docs/rembg.md` — rembg: install recipe, model choice, solid-color composite
- `lab/docs/comfyui.md` — ComfyUI: headless launch flags, HTTP API, client script, installed SDXL inpaint model, measured perf
- `lab/docs/fal-api/README.md` — fal.ai API: install, `.env`/`FAL_KEY`, `fal_run.py` usage, best model per brand (OpenAI/Google/xAI) + ids/schemas, gotchas
- `lab/docs/realesrgan.md` — Real-ESRGAN upscaler (via spandrel, MPS): venv, `upscale.py` usage, models, Apple-Silicon notes, gotchas

**lab/wikis/ — world knowledge (concepts, research, tool/model comparisons)**
- `lab/wikis/background-removal/README.md` — bg-removal model comparison (isnet-anime / birefnet / u2net)
- `lab/wikis/precise-segmentation/README.md` — SOTA local interactive segmentation + matting (EfficientTAM/SAM2-3, BiRefNet, ComfyUI); for sub-part/low-contrast isolation rembg can't do
- `lab/wikis/comfyui/README.md` — ComfyUI evaluation: confirmed generative backbone (inpaint/outpaint/controlnet/ip-adapter via HTTP+WS API); complements rembg/ImageMagick, not a replacement; M4 Max/MPS flags + gotchas
- `lab/wikis/anime-character-gen/README.md` — full-body anime character gen preserving a reference design (SDXL + IP-Adapter + ControlNet OpenPose on ComfyUI/MPS); checkpoint/adapter/CN picks + install gotchas
- `lab/wikis/fal-api-router/README.md` — fal.ai vs brand-direct pricing for OpenAI/Gemini/Grok image models + top-3 competitors; 100-img cost in VND, per-model fal fee % (verified 2026-06-25)
- `lab/wikis/upscaling/README.md` — upscaling/super-resolution: why spandrel over original Real-ESRGAN repo/ncnn-vulkan; MPS reality; model choice (verified 2026-06-25)

**lab/scripts/ — reusable parametrized scripts (`--help` on each)**
- `lab/scripts/bg_to_color.sh` — remove background, composite subject onto a solid-color canvas
- `lab/scripts/dim_background.sh` — keep subject, overlay a color over the rest at a chosen opacity (dim, not remove)
- `lab/scripts/comfyui_run.py` — headless ComfyUI client: upload inputs, submit API-format workflow, poll, save results
- `lab/scripts/compose_wallpaper.sh` — place a transparent cutout on a solid canvas: main-blob trim, scale to %-of-height, gravity anchor, optional bottom feather
- `lab/scripts/fal_run.py` — fal.ai batch client: prompts × image/folder → gen or edit via OpenAI/Google/xAI (or raw fal id), saves to `outputs/`; `--dry-run`, cost estimate
- `lab/scripts/upscale.py` — Real-ESRGAN/spandrel upscaler on MPS: tiled super-resolution, `--model/--scale/--tile/--device` (run via the realesrgan venv)

**lab/downloads/ — heavy artifacts (content git-ignored)**
- `lab/downloads/_catalog.md` — catalog of downloaded models/datasets (check before downloading)
- `lab/downloads/models/` — hand-fetched checkpoints / LoRAs / VAEs / upscalers
- `lab/downloads/tools/` — per-tool `uv` venvs (e.g. `rembg`; `comfyui` = git checkout + venv)
- `lab/downloads/cache/` — tool-managed caches & auto-downloaded models (`HF_HOME`, `U2NET_HOME`, `uv`)
- `lab/downloads/datasets/` — datasets

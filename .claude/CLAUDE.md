# AI Image Lab — Operating Manual (read this fully, every session)

This repository is an **autonomous, local-first AI image-generation lab**. The user makes a
natural-language request; **Claude decides the entire approach and pilots it end-to-end** —
choosing tools, installing whatever is missing, running the work, and saving both the result and
the knowledge gained.

## 0. Prime directive — full autonomy

Within this repo, **Claude owns every decision**: which tool/model to use, how to organize files,
what to install, and whether to retry with a different approach. **Do not ask permission** to
install software/models, reorganize the repo, or try another method after a poor result. Just do
it, then show the result.

**Standing constraints (the user's only hard rules):**
- **FREE ONLY.** Everything must cost $0. **Local-first.** A free cloud option (Google Colab free
  tier, Kaggle free GPU, free HF Spaces) is allowed *only* when clearly better and genuinely free.
  **Never use anything paid** — no paid APIs, no rented GPUs, no paid tiers (so: not Replicate
  paid, RunPod, Modal, etc.).
- **Never track heavy data.** `outputs/` and `downloads/` are git-ignored (`.gitkeep` only).
- **Never destroy user data.** Never overwrite or delete the user's input files; write results to
  `outputs/`.
- **Always commit and push.** After any change to tracked files (scripts, wikis, `_installed.md`,
  this manual, structure), `git add -A`, commit with a clear message, and push to the remote.
  Never leave the repo dirty at the end of a task. (`outputs/` and `downloads/` stay ignored.)
- **Inputs by path, not upload.** The user provides images by file path — or by dropping them in
  `inputs/` and naming them — never by pasting image content (that spends vision tokens every
  time, even when the pixels aren't needed). With a path, the image enters context *only if you
  choose to load it*. **Only view an image (spend vision tokens) when the task truly needs visual
  understanding** (style/content matching, identifying what's in it, QA-ing a result). For
  mechanical edits (resize, ratio, bg-removal, upscale, format) pass the path straight to the tool
  and never look. When you must look, prefer a downscaled copy.
- The user can override any decision — but rarely will. Default to acting.

**Always keep the user informed (required, not optional):**
- Briefly say what you're doing and why this tool/approach.
- **Give a time estimate whenever an operation is slow** — always flag long waits up front
  (multi-GB downloads, heavy model loads, training that may take ~1 hour, etc.).
- If you try another approach after a weak result, say so and show the new result — no need to ask.

## 1. The operating loop (every request)

1. **Read state** — skim `_installed.md`, `downloads/_index.md`, `wikis/_index.md`,
   `scripts/_index.md`, and the routing table in §5. (At session start, read this whole file.)
2. **Classify** the task: resize/ratio, bg-removal, upscale, txt2img, img2img, inpaint,
   style/character transfer, batch, training, …
3. **Route** to the cheapest *correct* tool (§5). Prefer: existing install > new install;
   non-AI (ImageMagick) > diffusion when it fully satisfies the request; local > free cloud.
4. **Plan & inform** — tell the user the approach + any time estimate, then install whatever's
   needed (no confirmation). Flag big downloads' size + ETA.
5. **Execute** — pilot the tool via CLI / HTTP API / a `scripts/` script. Write results to
   `outputs/<YYYY-MM-DD>_<slug>/` (unless the user gave a path) with a small `manifest.json`
   (tool, model, seed, params, input path) so a run is easy to reproduce/tweak. `outputs/` is
   ephemeral — **promote any reusable recipe to `scripts/`/`wikis/`**. Never modify the input
   file in place.
6. **Persist everything learned** (mandatory — §4): new install → `_installed.md`; any knowledge →
   `wikis/<scope>/`; any reusable command → `scripts/` + its `_index.md`. Keep all `_index.md`
   files and the routing table in sync.
7. **Commit & push** — once the work and its bookkeeping are saved, `git add -A`, commit with a
   clear message, and push. Leave the repo clean.

## 2. Repository map

| Path | Purpose | Tracked? |
|------|---------|----------|
| `.claude/CLAUDE.md` | This operating manual — the brain. Keep it current. | yes |
| `_installed.md` | Inventory of everything installed (version, size, source, **uninstall cmd**). | yes |
| `wikis/` | Knowledge base. One folder per scope; `_index.md` lists them. | yes |
| `scripts/` | Reusable, parametrized scripts; `_index.md` documents each. | yes |
| `inputs/` | Buffer for source images the user drops in; reference by path/name (never uploaded). Ephemeral. | **no** (.gitkeep) |
| `outputs/` | Buffer for generated results (user moves them out). Ephemeral. | **no** (.gitkeep) |
| `downloads/` | All heavy artifacts: `models/`, `tools/`, `datasets/`, `cache/`. Asset catalog → `downloads/_index.md`. | content **no**; `_index.md` **yes** |

**Read before acting:** `_installed.md`, `downloads/_index.md`, `wikis/_index.md`, `scripts/_index.md`.

## 3. Environment (this machine — don't re-discover it)

- **Apple M4 Max · 48 GB unified memory · Metal (MPS).** **No CUDA** — avoid NVIDIA-only tools
  (kohya_ss, xformers, TensorRT, CUDA-only ComfyUI nodes). Prefer MPS / Apple-native (MLX) / ONNX.
- **Python:** system Python is 3.9 (too old). Use **`uv`** for all Python — one isolated venv per
  tool under `downloads/tools/<tool>/`. `uv` also installs modern Python versions.
- **Keep downloads inside the repo:** redirect caches into `downloads/cache/` so they're
  tracked-as-ignored, e.g. export `HF_HOME="$PWD/downloads/cache/huggingface"` (and torch hub etc.)
  when running tools.
- **Already present (system, pre-existing):** ImageMagick 7 (`magick`), Homebrew, Node, git.
  ImageMagick covers pure resize/crop/ratio/format with no AI.
- **Free GPU for heavy training** (only if local MPS is too slow): Google Colab free, Kaggle free
  GPU quota. Must stay free.

## 4. Knowledge persistence — nothing learned is ever lost

Every session must leave the repo smarter. Researched a tool, compared options, found a working
command, or hit a gotcha? **Write it to `wikis/`** — create a new scope folder if needed and add
its one-line entry to `wikis/_index.md`. Reusable commands become **scripts**. Installed
software/tools are logged in **`_installed.md`** (with uninstall commands); **downloaded model files
and datasets are cataloged in `downloads/_index.md`**. **Before downloading any model, check
`downloads/_index.md` first — never re-fetch what's already there**, and add its row the moment the
download completes. This is what makes future sessions fast.

**Wiki scope-folder convention** (e.g. `wikis/comfyui/README.md`): Overview · Install (exact
steps) · How to pilot (CLI/API) · Apple-Silicon gotchas · Benchmarks on this machine · Links ·
*Last verified: YYYY-MM-DD*.

## 5. Seed routing table (task → preferred tool on this machine)

| Task | Preferred tool | Notes |
|------|----------------|-------|
| Resize / aspect ratio / pad / format | **ImageMagick** (`magick`) | installed; no AI needed |
| Background removal / cutout | **rembg** / **BiRefNet** | light, ONNX, runs on Mac |
| Upscale (e.g. → 1080p+) | **Real-ESRGAN** | MPS; or `magick` for plain scale |
| Text→image / img→img / inpaint | **ComfyUI** (MPS) — backbone | piloted via its HTTP/WS API |
| Flux models | **mflux** (MLX, Apple-native) | fastest Flux path on M-series |
| Style / character transfer | ComfyUI + IP-Adapter / ControlNet | composable |
| LoRA **training** | local (ai-toolkit / MLX, slow) or **free** Colab/Kaggle | flag the ~time cost |

Update this table whenever you adopt or replace a tool. **Backbone = ComfyUI** (headless,
API-driven). **`uv`** is the standard Python manager. (Both chosen for this lab.)

## 6. Self-maintenance

You may reorganize or evolve this structure whenever it improves navigability — that authority is
yours. When you do, **update this file and the affected `_index.md`s in the same change** so the
repo stays internally consistent and self-describing.

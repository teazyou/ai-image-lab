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
- **Research-backed, never guessed.** Every decision must trace to knowledge written in `wikis/`,
  not to training data (it goes stale fast for AI tooling). If the wiki lacks it — or it looks
  outdated — research first and save it *before* acting; see the operating loop, step 3.
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

1. **Read state** — skim `_installed.md`, `downloads/_index.md`, `docs/_index.md`, `wikis/_index.md`,
   `scripts/_index.md`, and the routing table in §5. (At session start, read this whole file.)
2. **Classify** the task: resize/ratio, bg-removal, upscale, txt2img, img2img, inpaint,
   style/character transfer, batch, training, …
3. **Ground in research — never guess (mandatory).** Check `wikis/` for existing knowledge on this
   task/tool. **If it's missing — or its "Last verified" date is stale — research it first** (web
   search + official docs / current releases; do a deeper pass for big tool or model decisions),
   then **save the findings to `wikis/` before acting**. Never rely on training data for tool
   specifics, install steps, commands, parameters, model choices, or comparisons — they drift fast.
   Everything below must trace to something written in `wikis/`, not to memory.
4. **Route** to the cheapest *correct* tool (§5), justified by the step-3 wiki knowledge. Prefer: existing install > new install;
   non-AI (ImageMagick) > diffusion when it fully satisfies the request; local > free cloud.
5. **Plan & inform** — tell the user the approach + any time estimate, then install whatever's
   needed (no confirmation). Flag big downloads' size + ETA.
6. **Execute** — pilot the tool via CLI / HTTP API / a `scripts/` script; first check `docs/<tool>` for its working commands, API shapes, and known gotchas. Write results to
   `outputs/<YYYY-MM-DD>_<slug>/` (unless the user gave a path) with a small `manifest.json`
   (tool, model, seed, params, input path) so a run is easy to reproduce/tweak. `outputs/` is
   ephemeral — **promote any reusable recipe to `scripts/`/`wikis/`**. Never modify the input
   file in place.
7. **Persist everything learned** (mandatory — §4): new install → `_installed.md`; hard-won tool
   how-to / gotchas → `docs/<tool>`; world knowledge & research → `wikis/<scope>/`; reusable
   command → `scripts/`. Update the matching `_index.md` and the routing table.
8. **Commit & push** — once the work and its bookkeeping are saved, `git add -A`, commit with a
   clear message, and push. Leave the repo clean.

## 2. Repository map

| Path | Purpose | Tracked? |
|------|---------|----------|
| `.claude/CLAUDE.md` | This operating manual — the brain. Keep it current. | yes |
| `_installed.md` | Inventory of installed software/tools (version, size, source, **uninstall cmd**). | yes |
| `docs/` | **How to operate OUR setup**: installed tools' CLI/API, settings, gotchas & fixes. `_index.md` lists pages. | yes |
| `wikis/` | **World knowledge**: AI-image concepts, research, tool/model comparisons. `_index.md` lists scopes. | yes |
| `scripts/` | Reusable, parametrized scripts; `_index.md` documents each. | yes |
| `inputs/` | Buffer for source images the user drops in; reference by path/name (never uploaded). Ephemeral. | **no** (.gitkeep) |
| `outputs/` | Buffer for generated results (user moves them out). Ephemeral. | **no** (.gitkeep) |
| `downloads/` | All heavy artifacts: `models/`, `tools/`, `datasets/`, `cache/`. Asset catalog → `downloads/_index.md`. | content **no**; `_index.md` **yes** |

**Read before acting:** `_installed.md`, `downloads/_index.md`, `docs/_index.md`, `wikis/_index.md`, `scripts/_index.md`.

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

Knowledge flows both ways: **read before acting** (loop steps 1, 3, 6) and **write back what you
learn** after — every session must leave the repo smarter. Where each kind of knowledge lives:

| Kind of knowledge | Goes in |
|-------------------|---------|
| How to operate an installed tool — working CLI/API, settings, **gotchas & fixes** | `docs/<tool>` |
| World knowledge — concepts, research findings, tool/model comparisons | `wikis/<scope>/` |
| Reusable automation (a command worth re-running) | `scripts/` |
| Installed software/tools (inventory + uninstall) | `_installed.md` |
| Downloaded models / datasets | `downloads/_index.md` |

**Save only what's worth saving.** Document the things that cost trial-and-error — exact flags, API
shapes, env vars, version quirks, workarounds. **Don't** record trivia any shell user knows (e.g.
copying a file with `cp`) or what `--help` already prints. Rule of thumb: *if it took back-and-forth
to get working, write it down; otherwise skip it.*

Always add/update the matching `_index.md` when you record knowledge. **Before downloading any
model, check `downloads/_index.md` first — never re-fetch what's already there.**

**Page conventions**
- `docs/<tool>.md` (or `docs/<tool>/README.md` if it grows): How to launch · CLI/API (working
  examples) · Settings/config · Apple-Silicon notes · Gotchas & fixes · *Last updated: YYYY-MM-DD*.
- `wikis/<scope>/README.md`: Overview · findings / comparison · benchmarks on this machine · Links ·
  *Last verified: YYYY-MM-DD*.

## 5. Seed routing table (task → preferred tool on this machine)

| Task | Preferred tool | Notes |
|------|----------------|-------|
| Resize / aspect ratio / pad / format | **ImageMagick** (`magick`) | installed; no AI needed |
| Background removal / cutout | **rembg** *(installed)* | ONNX/CPU on Mac. Model by subject: anime→`isnet-anime`, person→`u2net_human_seg`, photo→`birefnet-general`. Solid-color bg → `scripts/bg_to_color.sh`. Docs: `docs/rembg.md`, wiki: `wikis/background-removal/`. |
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

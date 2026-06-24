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
- **Never track heavy data.** `inputs/`, `outputs/`, `.cache/`, and `lab/downloads/` content are git-ignored.
- **Never destroy user data.** Never overwrite or delete the user's input files; write results to
  `outputs/`.
- **Research-backed, never guessed.** Every decision must trace to knowledge written in `lab/wikis/`,
  not to training data (it goes stale fast for AI tooling). If the wiki lacks it — or it looks
  outdated — research first and save it *before* acting; see the operating loop, step 3.
- **Always commit and push.** After any change to tracked files (scripts, wikis, `lab/_installed.md`,
  this manual, structure), `git add -A`, commit with a clear message, and push to the remote.
  Never leave the repo dirty at the end of a task. (`inputs/`, `outputs/`, `.cache/`, `lab/downloads/` stay ignored.)
- **Inputs by path, not upload.** The user provides images by file path — or by dropping them in
  `inputs/` and naming them — never by pasting image content (that spends vision tokens every
  time, even when the pixels aren't needed). With a path, the image enters context *only if you
  choose to load it*. **Only view an image (spend vision tokens) when the task truly needs visual
  understanding** (style/content matching, identifying what's in it, QA-ing a result). For
  mechanical edits (resize, ratio, bg-removal, upscale, format) pass the path straight to the tool
  and never look. When you must look, prefer a downscaled copy.
- **Token-budget aware — write compact.** Everything tracked here is re-read by future sessions, so
  every word costs tokens forever. Write the minimum that conveys the fact: terse phrasing, no
  boilerplate, no restating what another file (or this manual) already says. Compactness is a hard
  requirement, not a style preference — applies to all `lab/docs/`, `lab/wikis/`, `lab/_index.md`, commit
  messages, and what you load into context.
- The user can override any decision — but rarely will. Default to acting.

**Always keep the user informed (required, not optional):**
- Briefly say what you're doing and why this tool/approach.
- **Give a time estimate whenever an operation is slow** — always flag long waits up front
  (multi-GB downloads, heavy model loads, training that may take ~1 hour, etc.).
- If you try another approach after a weak result, say so and show the new result — no need to ask.

## 1. The operating loop (every request)

1. **Read state** — the master `lab/_index.md` (repo map) and `lab/_installed.md` (installed tools) are
   auto-imported into this manual, so you already have both. Check `lab/downloads/_catalog.md` and the
   routing table §5; open the specific `lab/docs/` / `lab/wikis/` page the map points to only when the task
   needs it. (Read this whole manual at session start.)
2. **Classify** the task: resize/ratio, bg-removal, upscale, txt2img, img2img, inpaint,
   style/character transfer, batch, training, …
3. **Ground in research — never guess (mandatory).** Check `lab/wikis/` for existing knowledge on this
   task/tool. **If it's missing — or its "Last verified" date is stale — research it first** (web
   search + official docs / current releases; do a deeper pass for big tool or model decisions),
   then **save the findings to `lab/wikis/` before acting**. Never rely on training data for tool
   specifics, install steps, commands, parameters, model choices, or comparisons — they drift fast.
   Everything below must trace to something written in `lab/wikis/`, not to memory.
   **Run the research itself in a sub-agent (§6).**
4. **Route** to the cheapest *correct* tool (§5), justified by the step-3 wiki knowledge. Prefer: existing install > new install;
   non-AI (ImageMagick) > diffusion when it fully satisfies the request; local > free cloud.
5. **Plan & inform** — tell the user the approach + any time estimate, then install whatever's
   needed (no confirmation). Flag big downloads' size + ETA. **Run the install in a sub-agent (§6).**
6. **Execute** — pilot the tool via CLI / HTTP API / a `lab/scripts/` script; first check `lab/docs/<tool>`
   for its working commands, API shapes, and known gotchas. Write the **final result(s) to the root
   of `outputs/`** with a descriptive name (unless the user gave a path); put any
   **intermediate/temp files** (cutouts, masks) in `.cache/`. **No `manifest.json`** —
   `outputs/` is ephemeral; if a run's recipe is worth keeping, promote it to `lab/scripts/` (reusable
   command) or `lab/docs/` (process notes). Never modify the input file in place.
   **Run heavy/long modification runs in a sub-agent and QA its output yourself (§6).**
7. **Persist everything learned** (mandatory — §4): new install → `lab/_installed.md`; downloaded asset
   → `lab/downloads/_catalog.md`; hard-won tool how-to / gotchas → `lab/docs/<tool>`; world knowledge &
   research → `lab/wikis/<scope>/`; reusable command → `lab/scripts/`. If you added/removed a tracked
   file or folder, update the master `lab/_index.md`; update the routing table §5 when a tool changes.
8. **Commit & push** — once the work and its bookkeeping are saved, `git add -A`, commit with a
   clear message, and push. Leave the repo clean.

## 2. Repository map

The path map (**master index**) and the installed-tools inventory are imported here so both load at
session start:

@../lab/_index.md
@../lab/_installed.md

- **Master index (`lab/_index.md`)** — one line per path + a concise description; the single
  map of the repo. **No rules live there**, only in this manual. Keep it current: update it in the
  same change whenever you add or remove a tracked file/folder.
- **Tracked:** this manual, `lab/_index.md`, `lab/_installed.md`, `lab/downloads/_catalog.md`, and everything in
  `lab/docs/`, `lab/wikis/`, `lab/scripts/`.
- **Git-ignored** (heavy / ephemeral): `inputs/` and `outputs/` (untracked entirely — you recreate
  them after a clone), plus `.cache/` and `lab/downloads/` **content** (folder skeleton kept via `.gitkeep`).

## 3. Environment (this machine — don't re-discover it)

- **Apple M4 Max · 48 GB unified memory · Metal (MPS).** **No CUDA** — avoid NVIDIA-only tools
  (kohya_ss, xformers, TensorRT, CUDA-only ComfyUI nodes). Prefer MPS / Apple-native (MLX) / ONNX.
- **Python:** system Python is 3.9 (too old). Use **`uv`** for all Python — one isolated venv per
  tool under `lab/downloads/tools/<tool>/`. `uv` also installs modern Python versions.
- **Keep downloads inside the repo:** redirect caches into `lab/downloads/cache/` so they're
  tracked-as-ignored, e.g. export `HF_HOME="$PWD/lab/downloads/cache/huggingface"` (and torch hub etc.)
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
| How to operate an installed tool — working CLI/API, settings, **gotchas & fixes** | `lab/docs/<tool>` |
| World knowledge — concepts, research findings, tool/model comparisons | `lab/wikis/<scope>/` |
| Reusable automation (a command worth re-running) | `lab/scripts/` |
| Installed software/tools (inventory + uninstall) | `lab/_installed.md` |
| Downloaded models / datasets | `lab/downloads/_catalog.md` |

**Save only what's worth saving.** Document the things that cost trial-and-error — exact flags, API
shapes, env vars, version quirks, workarounds. **Don't** record trivia any shell user knows (e.g.
copying a file with `cp`) or what `--help` already prints. Rule of thumb: *if it took back-and-forth
to get working, write it down; otherwise skip it.*

When you add or remove a tracked file/folder, update the master `lab/_index.md` (the repo map) in the
same change. **Before downloading any model, check `lab/downloads/_catalog.md` first — never re-fetch
what's already there.**

**Page conventions**
- `lab/docs/<tool>.md` (or `lab/docs/<tool>/README.md` if it grows): How to launch · CLI/API (working
  examples) · Settings/config · Apple-Silicon notes · Gotchas & fixes · *Last updated: YYYY-MM-DD*.
- `lab/wikis/<scope>/README.md`: Overview · findings / comparison · benchmarks on this machine · Links ·
  *Last verified: YYYY-MM-DD*.

## 5. Seed routing table (task → preferred tool on this machine)

| Task | Preferred tool | Notes |
|------|----------------|-------|
| Resize / aspect ratio / pad / format | **ImageMagick** (`magick`) | installed; no AI needed |
| Background removal / cutout | **rembg** *(installed)* | ONNX/CPU on Mac. Model by subject: anime→`isnet-anime`, person→`u2net_human_seg`, photo→`birefnet-general`. Solid-color bg → `lab/scripts/bg_to_color.sh`. Docs: `lab/docs/rembg.md`, wiki: `lab/wikis/background-removal/`. |
| Upscale (e.g. → 1080p+) | **Real-ESRGAN** | MPS; or `magick` for plain scale |
| Text→image / img→img / inpaint / outpaint | **ComfyUI** *(installed, MPS)* — backbone | launch headless + pilot via `lab/scripts/comfyui_run.py`; SDXL inpaint model installed (Flux Fill gated). Docs: `lab/docs/comfyui.md`, wiki: `lab/wikis/comfyui/`. |
| Flux models | **mflux** (MLX, Apple-native) | fastest Flux path on M-series |
| Style / character transfer | ComfyUI + IP-Adapter / ControlNet | composable |
| LoRA **training** | local (ai-toolkit / MLX, slow) or **free** Colab/Kaggle | flag the ~time cost |

Update this table whenever you adopt or replace a tool. **Backbone = ComfyUI** (headless,
API-driven). **`uv`** is the standard Python manager. (Both chosen for this lab.)

## 6. Delegate heavy work to sub-agents (protect the context window)

Research, installation, and heavy modification runs spew large volumes of output — web pages,
`pip`/build logs, multi-GB download chatter, generation traces — that would bloat this session's
context. **Run them in a plain sub-agent** (Agent tool, `subagent_type: claude`, **same model as
this session — never downgrade**) and keep only the distilled result in the main thread.

**Always delegate:**
- **Wiki research** (loop step 3) — the sub-agent does the web search + doc reading and returns the
  findings; **you** write them to `lab/wikis/` and act on them.
- **Installation** (loop step 5) — the sub-agent runs the installs/downloads and returns the working
  recipe, versions, sizes, and gotchas; **you** record them in `lab/_installed.md` / `lab/docs/`.
- **Heavy modification runs** (loop step 6) — generation, batch edits, training, any long pipeline.
  The sub-agent executes and **reports back everything**: each step, errors hit, and how it resolved
  them. **You then QA the output yourself** — load the result, judge quality, and **iterate
  (re-delegate with adjustments) if it's not good enough.**

Quality control, knowledge-writing, and user-facing reporting **stay with the main session** — never
the sub-agent. The sub-agent does the verbose work; you keep the judgment.

## 7. Self-maintenance

You may reorganize or evolve this structure whenever it improves navigability — that authority is
yours. When you do, **update this file and the master `lab/_index.md` in the same change** so the repo
stays internally consistent and self-describing.

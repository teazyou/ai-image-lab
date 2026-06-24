# fal.ai API — how to operate it from this lab

fal.ai = hosted-inference router ("OpenRouter for image/video gen"): many big-lab + third-party
models behind one HTTP API. **PAID** — every call debits fal credits. Per-image cost + the 100-image
VND table: [lab/wikis/fal-api-router/](../../wikis/fal-api-router/README.md). **No autostart** (it's a
remote API; nothing runs locally except the client).

- **Install:** uv venv at `lab/downloads/tools/fal/.venv` · `fal-client` **1.0.0** · Python 3.12 ·
  also `python-dotenv`, `requests`, `pillow`. (`uv pip install fal-client python-dotenv pillow requests`)
- **Key:** create at <https://fal.ai/dashboard/keys> → put in repo-root **`.env`** as `FAL_KEY=...`
  (`.env` is git-ignored; `.env.example` is the tracked template). The client auto-reads `FAL_KEY`.

## Our script — `lab/scripts/fal_run.py`

Batch gen/edit: one-or-many prompts × one image / a folder → results saved to `outputs/`. Run with the
fal venv:

```bash
lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py --model <openai|google|xai> [opts]
```

- **Model** (`--model`): brand alias (`openai`/`gpt`, `google`/`nano`, `xai`/`grok`) → the best model of
  each brand, or a **raw fal id** (e.g. `fal-ai/flux-pro/v1.1`) used as-is.
- **Mode is auto:** input image(s) present → **edit**; none → **text-to-image** (force with `--mode`).
- **Inputs:** `--image PATH` (repeatable) and/or `--images-dir DIR`. **Prompts:** `--prompt TEXT`
  (repeatable) and/or `--prompts-file FILE` (one per line, `#`=comment).
- **Combination:** edit default = **cartesian** (each image × each prompt = one output). `--combine` =
  pass ALL images together in one call per prompt (multi-reference compositing; great for Nano Banana
  Pro; xAI capped at 3 inputs).
- **Knobs:** `--num-images`, `--aspect` (g/x), `--resolution 1k|2k|4k` (g/x; auto-cased), `--quality
  low|medium|high` (openai), `--size <enum>` (openai), `--output-format png|jpeg|webp`, `--seed` (g).
  Unsupported-by-model knobs are silently dropped.
- **Safety:** `--dry-run` prints the plan + cost estimate with **no API call / no key needed**;
  `--max-jobs N` (default 100) aborts oversized batches unless `--force`.

```bash
# t2i, two prompts (Google flagship)
… fal_run.py --model google --prompt "a red fox in snow" --prompt "a city at dusk" --aspect 16:9 --resolution 2k
# edit every image in inputs/ with prompts from a file (OpenAI)
… fal_run.py --model openai --images-dir inputs/ --prompts-file prompts.txt --quality high
# composite two references in ONE call (Nano Banana Pro)
… fal_run.py --model google --image inputs/a.png --image inputs/b.png --combine --prompt "put A into B's scene"
# preview plan + cost, no key
… fal_run.py --model xai --images-dir inputs/ --prompt "anime style" --dry-run
```

Outputs are named `<brand>__<imgstem|t2i>__<prompt-slug>__<HHMMSS>.<ext>` (never overwritten). Failures
are per-job (one bad prompt doesn't kill the batch); a 422 content-policy block is reported, not retried.

## Best model per brand (verified live, 2026-06-25)

| Brand | t2i id | edit id | Input-image field | Notes |
|---|---|---|---|---|
| **OpenAI** GPT Image 2 | `openai/gpt-image-2` | `openai/gpt-image-2/edit` | `image_urls` (list) | `quality` default **high** (~4× medium); `image_size` enum (`square_hd`,`landscape_16_9`,…); `mask_url` for inpaint |
| **Google** Nano Banana Pro | `fal-ai/nano-banana-pro` | `fal-ai/nano-banana-pro/edit` | `image_urls` (list, multi) | `aspect_ratio` (def `1:1`), `resolution` `1K/2K/4K` (4K=2× price), `seed`, `safety_tolerance` 1–6. Output also has `description` |
| **xAI** Grok Imagine (quality) | `xai/grok-imagine-image/quality/text-to-image` | `xai/grok-imagine-image/edit` | `image_urls` (list, **max 3**) | `resolution` **`1k/2k`** (lowercase!); **no** `/quality/edit` id — edit uses the standard line ($0.02) |

## General API (when piloting without the script)

```python
import fal_client                                   # reads FAL_KEY from env
url = fal_client.upload_file("inputs/cat.png")      # local file -> fal.media URL (str)
res = fal_client.subscribe(                          # sync; blocks; streams logs
    "fal-ai/nano-banana-pro/edit",
    arguments={"prompt": "watercolor", "image_urls": [url]},
    with_logs=True,
    on_queue_update=lambda u: [print(l["message"]) for l in getattr(u, "logs", []) or []],
)
img_url = res["images"][0]["url"]                    # output: images[] {url,content_type,width,height,…}
```

- **Queue API** (recommended for big/long batches): `h = fal_client.submit(id, arguments=…)` →
  `h.status(with_logs=True)`, `h.get()` (blocks for result), `h.request_id`, `h.cancel()`.
- **Raw HTTP** (no client): `POST https://fal.run/{id}` (sync) or `https://queue.fal.run/{id}` (queue),
  header `Authorization: Key $FAL_KEY`, JSON body = the arguments.

## Gotchas

- **Id prefixes differ:** OpenAI = `openai/…`, Google/most = `fal-ai/…`, xAI = `xai/…`. Don't assume `fal-ai/`.
- **Edit input is always `image_urls` (a list)** for all three — even for a single image. Output is always `images[]`.
- **Grok image-edit on fal is STANDARD-tier — it DISTORTS identity (key gotcha).** `xai/grok-imagine-image/edit` (~$0.022, what `--model xai` uses for edits) is the *only* Grok image-input endpoint on fal; there is **no quality-tier image-to-image** here (`.../quality/image-to-image` → 404; fal's quality Grok is *text*-to-image only). It has **no strength/fidelity param** (verified in the OpenAPI schema — only prompt/aspect_ratio/resolution/num_images), so it reimagines the subject — face, pose, proportions drift — and does **NOT** match grok.ai, which runs the quality tier. Prompt tweaks (identity-lock, "keep proportions", aspect changes) do **not** fix a tier limit; don't waste calls on it.
  - **For faithful, identity-preserving edits/outpaints on fal** → use **Google Nano Banana Pro** (`fal-ai/nano-banana-pro/edit`), the SOTA character-consistent editor.
  - **For Grok's *quality* image edit specifically** → go **direct to the xAI API** (not fal): model `grok-imagine-image-quality` supports editing (input image URL/base64 + prompt, up to **3** reference images, 1k/2k), ~**$0.05/img** (1k) / $0.07 (2k), edits billed for input+output. This is the tier the website uses; fal does not resell it. Needs a separate `XAI_API_KEY`; our `fal_run.py` is fal-only.
- **Resolution case:** Google `1K/2K/4K`, xAI `1k/2k`. Our script auto-cases; raw calls must match.
- **GPT Image 2 cost trap:** default `quality=high` (1024² ≈ $0.211) is ~4× `medium` ($0.053). Set `--quality medium` to control spend.
- **Content moderation** → HTTP **422** with `detail[].type == "content_policy_violation"`; not retryable — fix the prompt/image.
- **Token-priced models** (GPT, Gemini): the per-image figures are estimates at the default tier; real cost adds prompt tokens.

*Last updated: 2026-06-25.*

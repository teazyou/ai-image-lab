#!/usr/bin/env python3
"""fal_run.py — batch image generation / editing via the fal.ai API.

Give it one or many prompts and (optionally) one image or a folder of images;
it runs the chosen model on fal and saves every result into outputs/.

Run with the fal venv (has fal-client, python-dotenv, requests, pillow):
    lab/downloads/tools/fal/.venv/bin/python lab/scripts/fal_run.py [opts]

Auth: reads FAL_KEY from the repo-root .env (or the environment). Get a key at
https://fal.ai/dashboard/keys . fal is a PAID API — each call debits fal credits
(per-image cost + the VND table live in lab/wikis/fal-api-router/).

Model picking (--model): a brand alias or a raw fal id.
    openai | gpt   -> OpenAI GPT Image 2        (t2i openai/gpt-image-2,            edit .../edit)
    google | nano  -> Google Nano Banana Pro    (t2i fal-ai/nano-banana-pro,        edit .../edit)
    xai    | grok  -> xAI Grok Imagine quality   (t2i xai/grok-imagine-image/quality/text-to-image,
                                                  edit xai/grok-imagine-image/edit)
    fal-ai/...      -> any raw fal model id, used as-is.

Mode is auto: images present -> edit, none -> text-to-image (override with --mode).

Examples:
    # text-to-image, two prompts, Google flagship
    fal_run.py --model google --prompt "a red fox in snow" --prompt "a city at dusk"
    # edit one image with one prompt (OpenAI)
    fal_run.py --model openai --image inputs/cat.png --prompt "make it a watercolor"
    # edit every image in a folder with prompts from a file (xAI)
    fal_run.py --model xai --images-dir inputs/ --prompts-file prompts.txt
    # composite MULTIPLE reference images in ONE call per prompt (Nano Banana Pro)
    fal_run.py --model google --image inputs/a.png --image inputs/b.png --combine \
               --prompt "put the character from image 1 into the scene of image 2"
    # see the plan + cost estimate without calling the API (no key needed)
    fal_run.py --model openai --images-dir inputs/ --prompt "..." --dry-run
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# Per-model config. t2i/edit ids + which knobs the model accepts + a rough
# per-image price (USD, default tier) for the pre-run cost estimate. All ids and
# schemas verified live on fal.ai (June 2026); see lab/docs/fal-api/.
MODELS = {
    "openai": {
        "label": "OpenAI GPT Image 2",
        "t2i": "openai/gpt-image-2",
        "edit": "openai/gpt-image-2/edit",
        "knobs": {"quality", "image_size", "output_format"},
        "price": {"t2i": 0.053, "edit": 0.061},  # medium 1024^2; high tier ~4x
    },
    "google": {
        "label": "Google Nano Banana Pro (Gemini 3 Pro Image)",
        "t2i": "fal-ai/nano-banana-pro",
        "edit": "fal-ai/nano-banana-pro/edit",
        "knobs": {"aspect_ratio", "resolution", "output_format", "seed"},
        "price": {"t2i": 0.15, "edit": 0.15},  # 1K/2K; 4K doubles
    },
    "xai": {
        "label": "xAI Grok Imagine (quality)",
        "t2i": "xai/grok-imagine-image/quality/text-to-image",
        "edit": "xai/grok-imagine-image/edit",  # no /quality/edit id exists
        "knobs": {"aspect_ratio", "resolution", "output_format"},
        "max_input_images": 3,
        "price": {"t2i": 0.05, "edit": 0.02},  # quality t2i 1k; standard edit
    },
}
ALIASES = {
    "gpt": "openai", "gpt-image-2": "openai", "openai": "openai",
    "google": "google", "gemini": "google", "nano": "google",
    "nano-banana-pro": "google", "nanobanana": "google",
    "xai": "xai", "grok": "xai", "grok-imagine": "xai",
}


def slug(s, n=44):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").strip().lower()).strip("-")
    return s[:n].rstrip("-") or "untitled"


def resolve_model(name):
    """Return (alias_or_None, cfg_dict). Raw fal ids (containing '/') pass through."""
    if "/" in name:
        return None, {
            "label": name, "t2i": name, "edit": name,
            "knobs": {"aspect_ratio", "resolution", "image_size", "quality",
                      "output_format", "seed"},
            "price": {}, "raw": True,
        }
    key = ALIASES.get(name.lower())
    if not key:
        sys.exit(f"Unknown --model '{name}'. Use openai|google|xai or a raw fal id "
                 f"(e.g. fal-ai/flux-pro/v1.1).")
    return key, MODELS[key]


def gather_images(args):
    paths = []
    for p in args.image or []:
        paths.append(Path(p))
    if args.images_dir:
        d = Path(args.images_dir)
        if not d.is_dir():
            sys.exit(f"--images-dir not a directory: {d}")
        paths += sorted(q for q in d.iterdir()
                        if q.suffix.lower() in IMG_EXTS and not q.name.startswith("."))
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        sys.exit("Image(s) not found:\n  " + "\n  ".join(missing))
    # de-dup, keep order
    seen, out = set(), []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def gather_prompts(args):
    prompts = list(args.prompt or [])
    if args.prompts_file:
        f = Path(args.prompts_file)
        if not f.is_file():
            sys.exit(f"--prompts-file not found: {f}")
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                prompts.append(line)
    return prompts


def build_args(cfg, mode, prompt, image_urls, alias, a):
    """Assemble the fal `arguments` dict, sending only knobs this model accepts."""
    args = {"prompt": prompt}
    if a.num_images != 1:
        args["num_images"] = a.num_images
    knobs = cfg["knobs"]
    if a.output_format and "output_format" in knobs:
        args["output_format"] = a.output_format
    if a.quality and "quality" in knobs:
        args["quality"] = a.quality
    if a.size and "image_size" in knobs:
        args["image_size"] = a.size
    if a.aspect and "aspect_ratio" in knobs:
        args["aspect_ratio"] = a.aspect
    if a.resolution and "resolution" in knobs:
        # Google wants 1K/2K/4K (upper), xAI wants 1k/2k (lower).
        args["resolution"] = a.resolution.upper() if alias == "google" else a.resolution.lower()
    if a.seed is not None and "seed" in knobs:
        args["seed"] = a.seed
    if mode == "edit":
        args["image_urls"] = image_urls
    return args


def uniquify(path):
    if not path.exists():
        return path
    stem, suf, i = path.stem, path.suffix, 1
    while True:
        cand = path.with_name(f"{stem}-{i}{suf}")
        if not cand.exists():
            return cand
        i += 1


def main():
    ap = argparse.ArgumentParser(
        description="Batch image gen/edit via fal.ai.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--model", required=True, help="openai|google|xai or a raw fal id")
    ap.add_argument("--prompt", action="append", help="a prompt (repeatable)")
    ap.add_argument("--prompts-file", help="text file, one prompt per line (# = comment)")
    ap.add_argument("--image", action="append", help="an input image path (repeatable)")
    ap.add_argument("--images-dir", help="folder of input images")
    ap.add_argument("--mode", choices=["auto", "t2i", "edit"], default="auto")
    ap.add_argument("--combine", action="store_true",
                    help="edit: pass ALL images together in one call per prompt (multi-ref)")
    ap.add_argument("--num-images", type=int, default=1, help="images per call (default 1)")
    ap.add_argument("--aspect", help="aspect_ratio (google/xai), e.g. 1:1, 16:9")
    ap.add_argument("--resolution", help="resolution (google/xai): 1k/2k[/4k]")
    ap.add_argument("--quality", choices=["auto", "low", "medium", "high"],
                    help="openai quality (default = model default 'high' = ~4x medium)")
    ap.add_argument("--size", help="openai image_size enum, e.g. square_hd, landscape_16_9")
    ap.add_argument("--output-format", dest="output_format",
                    choices=["png", "jpeg", "webp"], help="output format")
    ap.add_argument("--seed", type=int, help="seed (google)")
    ap.add_argument("--out", default=str(REPO_ROOT / "outputs"), help="output dir")
    ap.add_argument("--max-jobs", type=int, default=100, help="abort if plan exceeds this (safety)")
    ap.add_argument("--force", action="store_true", help="ignore the --max-jobs guard")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan + cost estimate; no API call, no key needed")
    a = ap.parse_args()

    alias, cfg = resolve_model(a.model)
    images = gather_images(a)
    prompts = gather_prompts(a)
    if not prompts:
        sys.exit("No prompts. Use --prompt and/or --prompts-file.")

    mode = a.mode
    if mode == "auto":
        mode = "edit" if images else "t2i"
    if mode == "edit" and not images:
        sys.exit("--mode edit needs at least one --image / --images-dir.")
    if mode == "t2i" and images:
        print("note: t2i mode — input images ignored.", file=sys.stderr)
        images = []

    model_id = cfg[mode]

    # Build the job list: (prompt, [image_paths]) per call.
    jobs = []
    if mode == "t2i":
        jobs = [(p, []) for p in prompts]
    elif a.combine:
        imgs = images
        cap = cfg.get("max_input_images")
        if cap and len(imgs) > cap:
            print(f"note: {cfg['label']} accepts max {cap} input images; using the first {cap}.",
                  file=sys.stderr)
            imgs = imgs[:cap]
        jobs = [(p, imgs) for p in prompts]
    else:  # edit, per-image
        jobs = [(p, [img]) for img in images for p in prompts]

    n_imgs_out = max(1, a.num_images)
    price = cfg.get("price", {}).get(mode)
    est = f"≈ ${price * n_imgs_out * len(jobs):.3f} ({price * n_imgs_out * len(jobs) * 26330:,.0f}₫)" \
        if price else "(unknown — raw model id)"

    print(f"model:   {cfg['label']}  [{model_id}]")
    print(f"mode:    {mode}{'  (combine)' if (mode=='edit' and a.combine) else ''}")
    print(f"prompts: {len(prompts)}   images: {len(images)}   jobs: {len(jobs)}   "
          f"images/call: {n_imgs_out}")
    print(f"est cost: {est}   [default tier; varies w/ quality/res — see wiki]")
    out_dir = Path(a.out)

    if len(jobs) > a.max_jobs and not a.force:
        sys.exit(f"Plan has {len(jobs)} jobs > --max-jobs {a.max_jobs}. "
                 f"Re-run with --force or narrow the inputs.")

    if a.dry_run:
        print("\n--- DRY RUN (no API call) ---")
        for i, (prompt, imgs) in enumerate(jobs, 1):
            built = build_args(cfg, mode, prompt, [f"<url:{p.name}>" for p in imgs], alias, a)
            print(f"[{i}] {model_id}  args={built}")
        return

    # ---- live run ----
    try:
        from dotenv import load_dotenv
        import requests
        import fal_client
    except ImportError as e:
        sys.exit(f"Missing dep ({e}). Run with the fal venv: "
                 f"lab/downloads/tools/fal/.venv/bin/python")

    load_dotenv(REPO_ROOT / ".env")
    load_dotenv()  # also honor cwd/.env and existing env
    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY not set. Put it in .env (FAL_KEY=...) — key from "
                 "https://fal.ai/dashboard/keys")

    out_dir.mkdir(parents=True, exist_ok=True)

    def on_update(update):
        try:
            if isinstance(update, fal_client.InProgress):
                for lg in (update.logs or []):
                    msg = lg.get("message") if isinstance(lg, dict) else str(lg)
                    if msg:
                        print("    ·", msg)
        except Exception:
            pass

    # Upload each local image once; reuse the URL across prompts.
    url_cache = {}

    def url_for(path):
        rp = str(path.resolve())
        if rp not in url_cache:
            print(f"    uploading {path.name} …")
            url_cache[rp] = fal_client.upload_file(str(path))
        return url_cache[rp]

    ext = a.output_format or "png"
    ok, fail = [], []
    for i, (prompt, imgs) in enumerate(jobs, 1):
        stem = "t2i" if mode == "t2i" else (
            f"{imgs[0].stem}+{len(imgs)-1}" if (a.combine and len(imgs) > 1) else imgs[0].stem)
        print(f"\n[{i}/{len(jobs)}] {stem} :: {prompt[:70]}")
        try:
            image_urls = [url_for(p) for p in imgs] if mode == "edit" else []
            arguments = build_args(cfg, mode, prompt, image_urls, alias, a)
            result = fal_client.subscribe(model_id, arguments=arguments,
                                          with_logs=True, on_queue_update=on_update)
            items = result.get("images") or ([result["image"]] if result.get("image") else [])
            if not items:
                raise RuntimeError(f"no images in result: {list(result)[:6]}")
            ts = datetime.now().strftime("%H%M%S")
            for k, item in enumerate(items):
                url = item["url"]
                ct = (item.get("content_type") or "").split("/")[-1]
                e = (ext if a.output_format else (ct if ct in ("png", "jpeg", "webp") else "png"))
                suffix = f"-{k}" if len(items) > 1 else ""
                name = f"{alias or 'fal'}__{stem}__{slug(prompt)}__{ts}{suffix}.{e}"
                dest = uniquify(out_dir / name)
                r = requests.get(url, timeout=180)
                r.raise_for_status()
                dest.write_bytes(r.content)
                print(f"    ✓ saved {dest.relative_to(REPO_ROOT) if dest.is_relative_to(REPO_ROOT) else dest}")
                ok.append(dest)
        except Exception as e:
            msg = str(e)
            if "content_policy" in msg or "content checker" in msg or "422" in msg:
                msg = "content policy violation (prompt/image flagged) — not retried"
            print(f"    ✗ FAILED: {msg}", file=sys.stderr)
            fail.append((stem, prompt, msg))

    print(f"\nDone: {len(ok)} image(s) saved to {out_dir}, {len(fail)} job(s) failed.")
    if fail:
        for stem, prompt, msg in fail:
            print(f"  - [{stem}] {prompt[:50]} -> {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

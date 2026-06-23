# _installed.md — Installed software / tools

Software/tools this lab installs (system packages, CLIs, apps, per-tool venvs) are recorded here so
they can be understood and cleanly removed. Their heavy files live under `downloads/` and are
git-ignored.

> **Downloaded model files & datasets are cataloged in [`downloads/_catalog.md`](downloads/_catalog.md)**,
> not here — check that before downloading anything.
>
> **How to *use* each tool** (CLI/API, settings, gotchas) is documented in [`docs/`](docs/).

**Conventions**
- Add a row the moment you install something; include the **exact uninstall command**.
- Sizes are approximate — update when known.
- "Apple-Silicon" = confirmed working on this M4 Max (MPS), with any notes.

## Installed by the lab (safe to remove)

| Name | Type | Version | Installed | Size | Location | Source | Uninstall | Apple-Silicon |
|------|------|---------|-----------|------|----------|--------|-----------|---------------|
| uv | Python pkg/venv manager | 0.11.23 | 2026-06-24 | ~50 MB | Homebrew (`/opt/homebrew`) | `brew install uv` | `brew uninstall uv` | native arm64 ✓ |
| rembg | bg-removal CLI (ONNX) | 2.0.76 | 2026-06-24 | ~1.2 GB venv | `downloads/tools/rembg/.venv` | `uv pip install "rembg[cpu,cli]"` | `rm -rf downloads/tools/rembg` | CPU onnxruntime ✓ (no MPS needed for 1 img); see [docs/rembg.md](docs/rembg.md) |

> **rembg install gotcha:** plain `rembg[cpu,cli]` backtracks `numba` to 0.53.1 (Python <3.10 only) and fails on Py 3.12. Add `"numba>=0.60" "llvmlite>=0.43"` to the install. Full recipe in [docs/rembg.md](docs/rembg.md).

## Pre-existing system tools (NOT installed by the lab — do not remove)

| Name | Version | Notes |
|------|---------|-------|
| ImageMagick | 7.1.2 (`magick`) | resize / crop / ratio / format without AI |
| Homebrew | 6.0.3 | system package manager |
| Node | 24.15 | |
| git | 2.50.1 | |
| Python (system) | 3.9.6 | too old for AI tooling — use `uv` instead |

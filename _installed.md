# _installed.md — Installed software / tools

Software/tools this lab installs (system packages, CLIs, apps, per-tool venvs) are recorded here so
they can be understood and cleanly removed. Their heavy files live under `downloads/` and are
git-ignored.

> **Downloaded model files & datasets are cataloged in [`downloads/_index.md`](downloads/_index.md)**,
> not here — check that before downloading anything.

**Conventions**
- Add a row the moment you install something; include the **exact uninstall command**.
- Sizes are approximate — update when known.
- "Apple-Silicon" = confirmed working on this M4 Max (MPS), with any notes.

## Installed by the lab (safe to remove)

_None yet — tools and models are installed on first need._

| Name | Type | Version | Installed | Size | Location | Source | Uninstall | Apple-Silicon |
|------|------|---------|-----------|------|----------|--------|-----------|---------------|
|      |      |         |           |      |          |        |           |               |

## Pre-existing system tools (NOT installed by the lab — do not remove)

| Name | Version | Notes |
|------|---------|-------|
| ImageMagick | 7.1.2 (`magick`) | resize / crop / ratio / format without AI |
| Homebrew | 6.0.3 | system package manager |
| Node | 24.15 | |
| git | 2.50.1 | |
| Python (system) | 3.9.6 | too old for AI tooling — use `uv` instead |

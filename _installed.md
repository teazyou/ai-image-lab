# _installed.md — Lab inventory

Everything this lab installs is recorded here so it can be understood and cleanly removed. Heavy
artifacts (models, tool repos, venvs) live under `downloads/` and are git-ignored.

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

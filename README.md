# ai-image-lab

A local-first, **free-only** AI image-generation lab, fully piloted by Claude Code.

Make a request in plain language — e.g. *"take this image, make it 1080p 16:9, keep the character,
black background"* — and Claude picks the best tool, installs whatever's missing, runs it, and
drops the result in `outputs/` for you to grab.

Provide source images by **path** (Finder → Option + right-click → *Copy as Pathname*), or drop
them into `inputs/` and name them — no need to upload image content into the chat (it just burns
tokens).

**How it works / where things live**
- [.claude/CLAUDE.md](.claude/CLAUDE.md) — the operating manual Claude follows (read this first).
- [_index.md](_index.md) — map of every path in the repo, one line each.
- [_installed.md](_installed.md) — inventory of everything installed (and how to remove it).
- [wikis/](wikis/) — knowledge base, grown on demand.
- [scripts/](scripts/) — reusable scripts.

Heavy artifacts (models, tools, datasets) live under `downloads/`, and generated results under
`outputs/`; both are git-ignored.

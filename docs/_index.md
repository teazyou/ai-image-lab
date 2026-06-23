# docs/ — system & tooling knowledge (how to operate OUR setup)

Operational know-how for the tools actually installed in this lab: how to launch them, drive their
CLI/API, the Apple-Silicon flags they need, their settings/config, and — most importantly — the
**gotchas and workarounds discovered the hard way**, so the next run doesn't repeat the
back-and-forth.

**docs/ vs wikis/**
- **`docs/` = our system.** How to *use* an installed tool/API here, its settings, its quirks. Specific.
- **`wikis/` = world knowledge.** Concepts, research, tool/model comparisons — what to choose & why. General.

**What to save (and what not to)**
- ✅ Exact working commands/flags, API request shapes, required env vars, config-file locations,
  version-specific quirks, and any fix that took trial-and-error to land.
- ❌ Trivia any shell user knows (e.g. copying a file with `cp`), or anything `--help` already says.
- **Rule of thumb: if it cost back-and-forth to get working, document it; otherwise skip it.**

**Conventions**
- One file per tool — `docs/<tool>.md` — or a folder `docs/<tool>/` if it grows.
- Suggested sections: How to launch · CLI/API (working examples) · Settings/config ·
  Apple-Silicon notes · Gotchas & fixes · *Last updated: YYYY-MM-DD*.
- Cross-link the tool's row in [`_installed.md`](../_installed.md). Keep pages current as behavior changes.

## Index

| Tool / topic | What it covers |
|--------------|----------------|
| _none yet_ | Written the first time a tool needs back-and-forth to work. |

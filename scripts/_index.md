# scripts/ — reusable scripts index

One row per script. Every script must be parametrized and support `--help`. Results go to
`outputs/` unless a path is given. Register a script here the moment you add it.

| Script | Purpose | Usage |
|--------|---------|-------|
| [bg_to_color.sh](bg_to_color.sh) | Remove background (rembg) and place subject on a solid-color canvas; auto-picks model by subject type; can lock output size/ratio. | `scripts/bg_to_color.sh -i IN [-c black] [-t anime\|photo\|person] [-s WxH] [-o OUT]` (`--help` for all) |

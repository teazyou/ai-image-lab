# Background removal — models & when to use which

**Overview.** Background removal = segment foreground subject, output an alpha matte / transparent
cutout. On this lab the go-to engine is **rembg** (ONNX, runs on CPU on Apple Silicon — no CUDA
needed). How to run it: [docs/rembg.md](../../docs/rembg.md).

## Model comparison (rembg, as of 2026-06)

| Model | Best for | Notes |
|-------|----------|-------|
| **isnet-anime** | **anime / illustration / drawn art** | Purpose-built for drawn art; cleaner edges on hair/lineart than photo models. ~176 MB. |
| **birefnet-general** | photos, general subjects | SOTA quality (2025); preserves fine hair / fur / glass. Slower (~9–20 s). Larger model. |
| birefnet-general-lite | photos, faster | Lighter/faster birefnet, slightly lower quality. |
| birefnet-portrait | headshots / face photos | Optimized for portraits. |
| u2net | general default | Fast, decent; the historical default. |
| u2net_human_seg | people / full body photos | Best classic model for human subjects. |
| isnet-general-use | general | Between u2net and birefnet. |

**Rule of thumb:** drawn/anime → `isnet-anime`; photo of a person → `u2net_human_seg` or
`birefnet-portrait`; everything else / max quality → `birefnet-general`.

## Replacing the background with a solid color

rembg only removes the background (transparent alpha). To get a **solid-color background** (e.g.
plain black), composite the transparent cutout onto a solid canvas with ImageMagick — see
docs/rembg.md. Compositing the cutout centered onto a fixed-size canvas also locks in the target
resolution / aspect ratio in one step.

## Benchmarks on this machine (M4 Max, CPU onnxruntime)

- isnet-anime on a 1920×1080 image: ~23 s CPU time incl. model load (first run also downloads
  176 MB). Fast enough that MPS/GPU isn't worth the trouble for single images.

## Links
- rembg: https://github.com/danielgatis/rembg · https://pypi.org/project/rembg/
- BiRefNet vs rembg vs U2Net (production notes):
  https://dev.to/om_prakash_3311f8a4576605/birefnet-vs-rembg-vs-u2net-which-background-removal-model-actually-works-in-production-4830

*Last verified: 2026-06-24*

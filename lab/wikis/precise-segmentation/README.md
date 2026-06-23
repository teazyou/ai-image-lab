# Precise & interactive segmentation / matting — SOTA local, free (Apple Silicon)

**Scope.** When rembg (`birefnet-general` matte + `sam` ViT-B points) can't isolate a *specific
sub-part* (one limb, a hairband) or can't separate a subject from a *connected / low-contrast blob*
(bare limb on a bright blanket, white clothing on snow, a character reflected in water). This is the
SOTA scan *beyond* [background-removal](../background-removal/README.md). World-knowledge, not yet
benchmarked here. See also rembg's `sam` usage in [lab/docs/rembg.md](../../docs/rembg.md).

**Two-part approach.** Precise selective masking = **promptable click-to-select** (positive clicks
on what to keep, **negative clicks to cut the connected blob**) **+ high-quality matting** (clean
hair/edges). No single local model does both well.

## Options (verified 2026-06)

**Promptable (click point/box):**

| Model | License (free?) | Apple-Silicon / MPS | Notes |
|-------|-----------------|---------------------|-------|
| **EfficientTAM** (yformer/EfficientTAM) | Apache-2.0 ✓ | **official MPS** (added Jan 2025) | **best free local click-to-refine.** point+box+segment-everything. SAM2-derived → some ops may CPU-fallback |
| SAM 2 / 2.1 (facebookresearch/sam2) | Apache-2.0 ✓ (weights incl.) | MPS (SAM2-arch; occasional CPU fallback) | standard promptable baseline |
| SAM 3 (Nov 2025) / 3.1 (~May 2026) | check per-release | **MLX port** `mlx-community/sam3-image` (Apple-native); `mps` via ComfyUI-Easy-Sam3 | newest; adds text prompts |
| HQ-SAM (SysCV/sam-hq) | Apache-2.0 ✓ | MPS unverified | best SAM for hair/thin structures; still weak on hollow/slender |

**Matting (edges, no clicks):**

| Model | License (free?) | MPS | Notes |
|-------|-----------------|-----|-------|
| **BiRefNet** (ZhengPeng7) | MIT ✓ | **NO MPS** — CUDA/CPU only (slow CPU on Mac) | leading fine-structure matte; `BiRefNet-matting` + `BiRefNet_HR-matting` (2048²). We already run `birefnet-general` via rembg |
| BEN2 Base (PramaLLC) | MIT ✓ (base only; full = paid) | **NO MPS** (hardcoded cuda autocast) | Confidence-Guided-Matting refiner targets low-confidence edges |
| InSPyReNet (plemeri) → `transparent-background` CLI | MIT ✓ | MPS unverified | one-shot CLI tool |
| ~~RMBG-2.0 (BRIA)~~ | **CC BY-NC 4.0 ✗** | — | **EXCLUDED** (free-only rule); commercial needs paid BRIA license |

**Anime/illustration:** `BiRefNet-toonOut` variant (via ComfyUI-RMBG) is the one confirmed
illustration-tuned matte. `SkyTNT/anime-segmentation` (isnet-anime origin) and
`CartoonSegmentation/CartoonSegmentation` exist but were not verified for MPS/quality.

## Local harnesses (ComfyUI = the practical one)

- **ComfyUI-RMBG** (1038lab) v3.0.0, 2026-01 — one pack: RMBG/INSPYRENET/BEN2/BiRefNet (9 variants
  incl. toonOut)/SDMatte/SAM·SAM2·SAM3/GroundingDINO/Florence2. Models download from HF separately;
  per-model licenses still apply.
- **ComfyUI-segment-anything-2** (kijai) — SAM2 point/box via KJNodes **PointsEditor** (interactive
  clicks). Mac caveat: built-in mask post-processing is **disabled** (needs a CUDA extension) — core
  segmentation still runs on MPS; do cleanup with other nodes (morphology/maskfix).
- **ComfyUI-Easy-Sam3** (yolain) — SAM3 text+point/box, interactive **Frames Editor**
  (green=positive / red=negative clicks), explicit `mps` device option (autocast off on mps).

## Recommended free local workflow (for the cases rembg failed)

1. **Click-to-refine select:** EfficientTAM (Apache, native MPS) — or SAM3 via ComfyUI-Easy-Sam3
   (`mps`). Positive clicks on the sub-part to keep; **negative clicks on the connected blob**
   (snow/blanket/reflection). This is the step birefnet + SAM ViT-B lacked.
2. **Refine edges (hair):** feed the selected region to BiRefNet HR-matting (CPU on Mac — slow but
   offline/free), or keep the SAM mask if edges are clean enough.
3. **Composite** as before (on black / dim background — see lab/docs/rembg.md scripts).
4. **UI:** ComfyUI (ComfyUI-RMBG + a SAM2/SAM3 points node) for an integrated click canvas; or
   script EfficientTAM for a CLI path.

## Reality check (when to stop)

- **No M4 Max benchmarks exist** — every published FPS is NVIDIA. BiRefNet/BEN2 run **CPU-only** on
  Mac (slow); only EfficientTAM and yolain's SAM3 node expose intentional MPS paths. Measure before
  committing a pipeline.
- SOTA promptable models make the hard cases *tractable* (via negative clicks) but don't **solve**
  bare-limb-on-bright-blanket / white-on-snow / reflections — the last mile is **manual mask
  painting** (ComfyUI MaskEditor, Krita, GIMP). For one-off wallpapers that's often the fastest path.
- Fast-moving area (SAM3 shipped 2025-11; 3.1 ~2026-05) — re-verify versions/licenses before acting.

## Sources (primary)
EfficientTAM github.com/yformer/EfficientTAM · SAM2 github.com/facebookresearch/sam2 · HQ-SAM
github.com/SysCV/sam-hq · BiRefNet github.com/ZhengPeng7/BiRefNet · BEN2 github.com/PramaLLC/BEN2 ·
RMBG-2.0 huggingface.co/briaai/RMBG-2.0 (CC BY-NC) · InSPyReNet github.com/plemeri/InSPyReNet ·
ComfyUI-RMBG github.com/1038lab/ComfyUI-RMBG · ComfyUI-segment-anything-2
github.com/kijai/ComfyUI-segment-anything-2 · ComfyUI-Easy-Sam3 github.com/yolain/ComfyUI-Easy-Sam3 ·
anime: github.com/SkyTNT/anime-segmentation, github.com/CartoonSegmentation/CartoonSegmentation

*Last verified: 2026-06-24*

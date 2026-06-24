# fal.ai as an image-model API router — pricing vs paying the brand direct

**Scope:** for every current **image-generation** model from **OpenAI**, **Google (Gemini/Imagen)** and
**xAI (Grok)**, what 100 images cost via **fal.ai** vs the **brand's own API**, the **fal fee %**, and the
**top-3 competitor** models on fal. *(Video models out of scope.)*

## What fal.ai is

An "OpenRouter for image/video gen": a hosted-inference aggregator exposing many third-party + big-lab
models behind one unified API + playground, pay-per-use. Billing is **per image**, **per megapixel**
(round up to nearest MP), or **per compute-second** depending on model. For big-lab models fal mostly
**passes the brand's own price through at cost** and adds margin only on select premium models.

## Method / basis (so the table is reproducible)

- **Standard image** = 1024×1024 (~1 MP), **standard/medium quality**, **1** output, **text-to-image**, no add-ons.
  Token-priced models (GPT Image, Gemini) are converted to per-image at the **medium/standard** tier; the
  real blended cost drifts with prompt-token count.
- **FX (fixed, applied everywhere):** **1 USD = 26,330 VND** (TradingEconomics spot, 23 Jun 2026).
  → **100 imgs (VND) = USD/img × 2,633,000.**
- Prices fetched live **2026-06-25** from fal.ai + each brand's pricing page, then **independently
  re-derived by a second agent** (27-agent research workflow).

## The table — 100-image cost, fal vs brand-direct (★ = brand flagship)

| Brand · Maker | Model | fal $/img | **fal · 100 imgs (VND)** | Direct $/img | **Direct · 100 imgs (VND)** | **fal fee %** |
|---|---|--:|--:|--:|--:|--:|
| OpenAI | ★ **GPT Image 2** | 0.053 | **139,549** | 0.053 | **139,549** | **0%** |
| OpenAI | GPT Image 2 — Edit (img2img) | 0.061 | **160,613** | 0.053 | **139,549** | **+15.1%** |
| OpenAI | GPT Image 1.5 | 0.034 | **89,522** | 0.034 | **89,522** | **0%** |
| OpenAI | GPT Image 1 Mini | 0.011 | **28,963** | 0.011 | **28,963** | **0%** |
| Google | ★ **Gemini 3 Pro Image** (Nano Banana Pro) | 0.15 | **394,950** | 0.134 | **352,822** | **+11.9%** |
| Google | Gemini 3.1 Flash Image (Nano Banana 2) | 0.08 | **210,640** | 0.067 | **176,411** | **+19.4%** |
| Google | Gemini 2.5 Flash Image (Nano Banana, orig.) | 0.039 | **102,687** | 0.039 | **102,687** | **0%** |
| Google | Imagen 4 (Standard) — *deprecated, EOL 2026-08-17* | 0.05 | **131,650** | 0.04 | **105,320** | **+25%** |
| xAI | ★ **grok-imagine-image-quality** (Grok Imagine Pro) | 0.05 | **131,650** | 0.05 | **131,650** | **0%** |
| xAI | grok-imagine-image (standard) | 0.02 | **52,660** | 0.02 | **52,660** | **0%** |
| xAI | grok-2-image (Aurora) — *legacy, retired 2026-02-28* | — (not on fal) | **N/A** | 0.07¹ | **184,310** | **N/A** |
| **Competitor** · Black Forest Labs | FLUX1.1 [pro] | 0.04 | **105,320** | 0.04² | **105,320** | **0%** |
| **Competitor** · ByteDance | Seedream 4 | 0.03 | **78,990** | —³ | **N/A** | **N/A** |
| **Competitor** · Ideogram | Ideogram V3 (Balanced) | 0.06 | **157,980** | 0.06² | **157,980** | **0%** |

¹ grok-2-image historical launch price (model removed from xAI API; not currently sellable). 
² Maker's own API equals fal's per-image price → 0% fal markup. 
³ ByteDance/BytePlus per-image price not confirmable (JS-rendered pricing page).

## Key findings

- **fal's fee is model-dependent, not flat.** It passes most models through **at cost (0%)** and is *cheaper
  to reason about* than expected; its markup concentrates on **Google's premium tiers** (Nano Banana Pro
  **+11.9%**, Nano Banana 2 **+19.4%**, Imagen 4 **+25%**) and the **GPT-Image Edit** endpoint (**+15.1%**).
- **The OpenAI + Grok lines are pure passthrough** for text-to-image — paying fal costs the same as paying
  OpenAI/xAI directly, so fal buys you one API + no separate account at no premium.
- **Cheapest usable big-lab options (100 imgs):** grok-imagine-image **52,660₫**, GPT Image 1 Mini
  **28,963₫** (cheapest overall), Nano Banana orig. **102,687₫**.
- **Flagship cost ladder (100 imgs, fal):** Grok Pro **131,650₫** < GPT Image 2 **139,549₫** ≪ Gemini 3 Pro
  Image **394,950₫** (Google's flagship is ~3× the others).
- **Competitors undercut the flagships:** Seedream 4 **78,990₫** and FLUX1.1 [pro] **105,320₫** beat every
  flagship on price while topping quality leaderboards; Ideogram V3 **157,980₫** leads on in-image text.

## Caveats

- **Token-priced models** (all GPT Image, all Gemini): the per-image figure is the **medium/standard-tier**
  estimate. OpenAI's API *default* quality is actually `high` (GPT Image 2 high = $0.211/img ≈ 555,613₫/100);
  real cost also adds prompt-text input tokens. Gemini per-image = output-token math ($120/$60/$30 per 1M ×
  ~1,120–1,290 tokens/img).
- **Imagen 4** verifier disagreement: fal **model-page Standard = $0.05**; some third-party trackers + fal's
  marketing blurb show **$0.04** (the Fast tier). Used $0.05 (model-page authoritative). Model is **EOL
  2026-08-17** — Google steers users to Nano Banana.
- **grok-2-image** is gone from xAI's API (retired 2026-02-28); $0.07 is its historical launch price, shown
  for reference only.
- fal also bills small token/MP surcharges on some endpoints (de-minimis for one short-prompt image); FLUX
  bills **per-MP** (1024² rounds up to 1 MP = $0.04).

## Sources (fetched 2026-06-25)

- fal model pages: `fal.ai/models/openai/gpt-image-2`, `…/gpt-image-2/edit`, `fal-ai/gpt-image-1.5`,
  `fal-ai/gpt-image-1-mini`, `fal-ai/nano-banana-pro`, `…/nano-banana-2`, `…/nano-banana`,
  `fal-ai/imagen4/preview`, `xai/grok-imagine-image/quality/text-to-image`, `xai/grok-imagine-image`,
  `fal-ai/flux-pro/v1.1`, `fal-ai/bytedance/seedream/v4/text-to-image`, `fal-ai/ideogram/v3` · fal.ai/pricing
- Brand: `developers.openai.com/api/docs/pricing` · `ai.google.dev/gemini-api/docs/pricing` ·
  `docs.x.ai/developers/pricing` · `docs.bfl.ml` · `ideogram.ai/api-pricing`

*Last verified: 2026-06-25.*

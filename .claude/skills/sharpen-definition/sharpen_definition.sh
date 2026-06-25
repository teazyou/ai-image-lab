#!/usr/bin/env bash
# sharpen_definition.sh — set an image to 1080p and boost its definition.
#
# Recipe (validated): Real-ESRGAN 4x upscale (reconstructs fine detail) -> Lanczos
# downscale to 1080p height (AR preserved) -> light unsharp. The 4x round-trip is
# what sharpens — a far cleaner result than a plain unsharp on the original.
# "1080p" = 1080px tall, aspect ratio preserved (a 16:9 input -> 1920x1080). The
# resize is idempotent if the image is already 1080p, so this also satisfies
# "set 1080p if not already". Never modifies the input in place.
#
# Output: outputs/<stem>_1080p-sharp.png  (override with -o)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENV_PY="$REPO_ROOT/lab/downloads/tools/realesrgan/.venv/bin/python"
UPSCALE="$REPO_ROOT/lab/scripts/upscale.py"
HEIGHT=1080

usage(){ echo "usage: $(basename "$0") -i <image> [-o <output>]"; exit 1; }
IN=""; OUT=""
while getopts "i:o:" opt; do
  case "$opt" in
    i) IN="$OPTARG";;
    o) OUT="$OPTARG";;
    *) usage;;
  esac
done
[ -n "$IN" ] || usage
[ -e "$IN" ] || { echo "input not found: $IN" >&2; exit 1; }

stem="$(basename "${IN%.*}")"
[ -n "$OUT" ] || OUT="$REPO_ROOT/outputs/${stem}_1080p-sharp.png"
job="$REPO_ROOT/.cache/${stem}_sharpen"
mkdir -p "$job" "$(dirname "$OUT")"

# 1) Real-ESRGAN 4x (detail reconstruction) on MPS
"$VENV_PY" "$UPSCALE" "$IN" "$job/001_upscaled_4x.png"

# 2) Lanczos downscale to 1080p height + light unsharp
magick "$job/001_upscaled_4x.png" -filter Lanczos -resize "x${HEIGHT}" -unsharp 0x0.8+0.7+0.01 "$OUT"

# 3) clean the job scratch folder
rm -rf "$job"

magick identify -format "saved: %d/%f  (%wx%h)\n" "$OUT"

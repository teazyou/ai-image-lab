#!/usr/bin/env bash
# dim_background.sh — keep the subject untouched, overlay a solid color over everything else.
# Pipeline: rembg (subject alpha) -> ImageMagick: darken full image, paste original subject on top.
# At --opacity 1.0 the background becomes a solid color (same as bg_to_color.sh); below 1.0 it just
# dims the background (e.g. 0.7 = "black square @ 70% opacity, background stays faintly visible").
# Repo: ai-image-lab. See lab/docs/rembg.md and lab/wikis/background-removal/.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lab/scripts/dim_background.sh -i INPUT [options]

Keep INPUT's subject untouched; overlay COLOR at OPACITY over the rest (same canvas size).

Options:
  -i, --input PATH      Source image (required). Never modified in place.
  -o, --output PATH     Output. Default: outputs/<stem>_dim<NN>.<ext> (cutout -> .cache/)
  -O, --opacity N       Overlay opacity 0..1. 1.0 = solid bg; 0.7 = darken rest to 30%. Default: 0.7
  -c, --color COLOR     Overlay color (IM name or #hex). Default: black
  -m, --model NAME      rembg model. Default: birefnet-general (best on busy/blended scenes)
  -h, --help            Show this help.

Examples:
  lab/scripts/dim_background.sh -i a.jpg -O 0.7              # keep subject, darken rest to 30%
  lab/scripts/dim_background.sh -i a.jpg -O 1.0             # subject on solid black bg
  lab/scripts/dim_background.sh -i a.jpg -O 0.7 -c '#001020'
EOF
}

INPUT="" OUTPUT="" OPACITY="0.7" COLOR="black" MODEL="birefnet-general"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)   INPUT="$2"; shift 2;;
    -o|--output)  OUTPUT="$2"; shift 2;;
    -O|--opacity) OPACITY="$2"; shift 2;;
    -c|--color)   COLOR="$2"; shift 2;;
    -m|--model)   MODEL="$2"; shift 2;;
    -h|--help)    usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

[[ -n "$INPUT" ]] || { echo "Error: --input is required" >&2; usage; exit 1; }
[[ -f "$INPUT" ]] || { echo "Error: input not found: $INPUT" >&2; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMBG="$ROOT/lab/downloads/tools/rembg/.venv/bin/rembg"
[[ -x "$REMBG" ]] || { echo "Error: rembg venv missing. See lab/docs/rembg.md to install." >&2; exit 1; }
export U2NET_HOME="$ROOT/lab/downloads/cache/u2net"

OPCT="$(awk -v o="$OPACITY" 'BEGIN{printf "%.2f", o*100}')"   # opacity as a percentage

stem="$(basename "$INPUT")"; stem="${stem%.*}"
nn="$(awk -v o="$OPACITY" 'BEGIN{printf "%02d", o*100}')"
ASSETS="$ROOT/.cache"; mkdir -p "$ASSETS"
CUTOUT="$ASSETS/${stem}_cutout.png"
[[ -n "$OUTPUT" ]] || OUTPUT="$ROOT/outputs/${stem}_dim${nn}.png"
mkdir -p "$(dirname "$OUTPUT")"

echo ">> rembg ($MODEL) -> $CUTOUT"
"$REMBG" i -m "$MODEL" "$INPUT" "$CUTOUT"

echo ">> dim background (color=$COLOR opacity=$OPACITY) + paste subject -> $OUTPUT"
# overlay a COLOR layer at OPACITY alpha over the whole image, then paste the untouched subject on top
magick "$INPUT" \
  \( +clone -fill "$COLOR" -colorize 100 -alpha set -channel A -evaluate set "${OPCT}%" +channel \) \
  -compose over -composite \
  "$CUTOUT" -compose over -composite -depth 8 "$OUTPUT"

echo ">> done: $OUTPUT ($(magick identify -format '%wx%h %[channels]' "$OUTPUT"))"

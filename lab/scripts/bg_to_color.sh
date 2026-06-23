#!/usr/bin/env bash
# bg_to_color.sh — remove an image's background and place the subject on a solid-color canvas.
# Pipeline: rembg (transparent cutout) -> ImageMagick composite onto a solid canvas.
# Repo: ai-image-lab. See lab/docs/rembg.md and lab/wikis/background-removal/.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lab/scripts/bg_to_color.sh -i INPUT [options]

Remove INPUT's background and composite the subject onto a solid-color canvas.

Options:
  -i, --input PATH     Source image (required). Never modified in place.
  -o, --output PATH    Output PNG. Default: outputs/<stem>_<color>-bg.png (cutout -> .cache/)
  -c, --color COLOR    Background color (ImageMagick name or #hex). Default: black
  -m, --model NAME     rembg model. Default: auto-pick by --type
  -t, --type KIND      Subject hint when -m not given: anime | photo | person  (default: anime)
  -s, --size WxH       Output canvas size. Default: same as the cutout (keeps source dims)
  -h, --help           Show this help.

Examples:
  lab/scripts/bg_to_color.sh -i inputs/art.jpg                     # anime art -> black bg, source size
  lab/scripts/bg_to_color.sh -i photo.jpg -t photo -c white -s 1920x1080
  lab/scripts/bg_to_color.sh -i p.png -m u2net_human_seg -c '#101010'
EOF
}

INPUT="" OUTPUT="" COLOR="black" MODEL="" TYPE="anime" SIZE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)  INPUT="$2"; shift 2;;
    -o|--output) OUTPUT="$2"; shift 2;;
    -c|--color)  COLOR="$2"; shift 2;;
    -m|--model)  MODEL="$2"; shift 2;;
    -t|--type)   TYPE="$2"; shift 2;;
    -s|--size)   SIZE="$2"; shift 2;;
    -h|--help)   usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

[[ -n "$INPUT" ]] || { echo "Error: --input is required" >&2; usage; exit 1; }
[[ -f "$INPUT" ]] || { echo "Error: input not found: $INPUT" >&2; exit 1; }

# Resolve repo root from this script's location (lab/scripts/.. -> lab; /../.. -> repo root).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMBG="$ROOT/lab/downloads/tools/rembg/.venv/bin/rembg"
[[ -x "$REMBG" ]] || { echo "Error: rembg venv missing. See lab/docs/rembg.md to install." >&2; exit 1; }
export U2NET_HOME="$ROOT/lab/downloads/cache/u2net"

if [[ -z "$MODEL" ]]; then
  case "$TYPE" in
    anime)  MODEL="isnet-anime";;
    person) MODEL="u2net_human_seg";;
    photo)  MODEL="birefnet-general";;
    *) echo "Error: --type must be anime|photo|person" >&2; exit 1;;
  esac
fi

stem="$(basename "$INPUT")"; stem="${stem%.*}"
colslug="$(echo "$COLOR" | tr -cd 'a-zA-Z0-9')"
# Convention: final result -> outputs/ root; intermediates -> .cache/.
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$ROOT/outputs/${stem}_${colslug}-bg.png"
fi
mkdir -p "$(dirname "$OUTPUT")"
ASSETS="$ROOT/.cache"; mkdir -p "$ASSETS"
CUTOUT="$ASSETS/${stem}_cutout.png"

echo ">> rembg ($MODEL) -> $CUTOUT"
"$REMBG" i -m "$MODEL" "$INPUT" "$CUTOUT"

if [[ -z "$SIZE" ]]; then
  SIZE="$(magick identify -format '%wx%h' "$CUTOUT")"
fi
echo ">> composite onto $COLOR canvas ${SIZE} -> $OUTPUT"
magick -size "$SIZE" "canvas:$COLOR" "$CUTOUT" -gravity center -composite -depth 8 "$OUTPUT"

echo ">> done: $OUTPUT ($(magick identify -format '%wx%h %[channels]' "$OUTPUT"))"

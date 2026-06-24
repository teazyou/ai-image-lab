#!/usr/bin/env bash
# compose_wallpaper.sh — place an isolated transparent-PNG subject onto a solid canvas as a wallpaper.
# Trims to the MAIN subject blob (ignoring stray specks that fool plain -trim), scales it to a
# target fraction of the canvas height, and positions it at a chosen gravity. Optional bottom
# feather makes a bottom-anchored subject fade off the canvas edge (natural run-off, no cut line).
# Input must already be a cutout (subject on alpha) — e.g. from bg_to_color.sh / rembg. Repo: ai-image-lab.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lab/scripts/compose_wallpaper.sh -i CUTOUT.png [options]

Place an isolated transparent-PNG subject onto a solid-color canvas.

Options:
  -i, --input PATH     Transparent cutout PNG (required; subject on alpha). Never modified.
  -o, --output PATH    Output PNG. Default: outputs/<stem>_wallpaper.png
  -s, --size WxH       Canvas size. Default: 1920x1080
  -c, --color COLOR    Canvas color (IM name or #hex). Default: black
  -H, --height FRAC    Subject height as a fraction of canvas height. Default: 0.7
  -g, --gravity G      Placement: center | south | north | east | west | ... Default: center
                       Use 'south' to anchor the subject to the bottom edge (hides a portrait's
                       bottom crop line by running it off-canvas).
  -f, --feather PX     Feather the subject's BOTTOM edge to transparent over PX px (natural fade
                       when bottom-anchored; also kills faint matte remnants at the edge). Default: 0
  -h, --help           Show this help.

Examples:
  # 70%-tall, centered on black 1920x1080
  lab/scripts/compose_wallpaper.sh -i .cache/char_cutout.png
  # 80%-tall, anchored to bottom, 70px bottom fade (character "emerges" from the edge)
  lab/scripts/compose_wallpaper.sh -i .cache/char_cutout.png -H 0.8 -g south -f 70
EOF
}

INPUT="" OUTPUT="" SIZE="1920x1080" COLOR="black" FRAC="0.7" GRAV="center" FEATHER="0"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)   INPUT="$2"; shift 2;;
    -o|--output)  OUTPUT="$2"; shift 2;;
    -s|--size)    SIZE="$2"; shift 2;;
    -c|--color)   COLOR="$2"; shift 2;;
    -H|--height)  FRAC="$2"; shift 2;;
    -g|--gravity) GRAV="$2"; shift 2;;
    -f|--feather) FEATHER="$2"; shift 2;;
    -h|--help)    usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

[[ -n "$INPUT" ]] || { echo "Error: --input is required" >&2; usage; exit 1; }
[[ -f "$INPUT" ]] || { echo "Error: input not found: $INPUT" >&2; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
stem="$(basename "$INPUT")"; stem="${stem%.*}"
[[ -n "$OUTPUT" ]] || OUTPUT="$ROOT/outputs/${stem}_wallpaper.png"
mkdir -p "$(dirname "$OUTPUT")"
WORK="$ROOT/.cache"; mkdir -p "$WORK"

CANVAS_H="${SIZE#*x}"
TARGET_H=$(awk "BEGIN{printf \"%d\", $CANVAS_H*$FRAC}")

# 1) Trim to the MAIN subject blob (connected-components drops stray specks that fool -trim).
#    area-threshold = 1% of frame: real subjects are far larger; strays far smaller.
THR=$(magick identify -format "%[fx:int(w*h*0.01)]" "$INPUT")
BBOX=$(magick "$INPUT" -alpha extract -threshold 25% \
  -define connected-components:area-threshold="$THR" \
  -define connected-components:mean-color=true -connected-components 8 \
  -threshold 50% -format "%@" info:)
TRIM="$WORK/${stem}_subject.png"
magick "$INPUT" -crop "$BBOX" +repage "$TRIM"

# 2) Optional bottom-edge feather to transparent.
if [[ "$FEATHER" -gt 0 ]]; then
  read -r W H < <(magick "$TRIM" -format "%w %h\n" info:)
  magick -size "${W}x${H}" xc:white \( -size "${W}x${FEATHER}" gradient:white-black \) \
    -gravity south -composite "$WORK/${stem}_fade.png"
  magick "$TRIM" -alpha extract "$WORK/${stem}_fade.png" -compose Multiply -composite "$WORK/${stem}_fa.png"
  magick "$TRIM" "$WORK/${stem}_fa.png" -compose CopyOpacity -composite "$TRIM"
fi

# 3) Scale subject to TARGET_H tall and place on the canvas.
echo ">> subject $(magick identify -format '%wx%h' "$TRIM") -> ${TARGET_H}px tall (${FRAC} of ${CANVAS_H}), gravity=$GRAV"
magick -size "$SIZE" "canvas:$COLOR" \
  \( "$TRIM" -resize "x${TARGET_H}" \) -gravity "$GRAV" -composite -depth 8 "$OUTPUT"
echo ">> done: $OUTPUT ($(magick identify -format '%wx%h %[channels]' "$OUTPUT"))"

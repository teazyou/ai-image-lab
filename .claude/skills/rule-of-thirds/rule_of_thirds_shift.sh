#!/usr/bin/env bash
# rule_of_thirds_shift.sh — move a subject horizontally by P% of image width toward
# a given direction, backfilling the vacated side with the (uniform) background color.
# Local-only (ImageMagick). DIRECTION is decided by the caller (Claude's vision), since
# "which way does the subject face" needs visual judgment; this script is the mechanical half.
# Assumes a solid background (e.g. a black-bg wallpaper); bg color is read from the top-left pixel.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: lab/scripts/rule_of_thirds_shift.sh -i INPUT -d left|right [-p 20|30] [-o OUTPUT]

Shift the subject by P% of the image width toward DIRECTION on a solid-background image.
Background color is auto-detected from the top-left pixel and used to fill the vacated side.
The shift is clamped so the subject never clips the frame (logs when clamped).

Options:
  -i, --input PATH    Source image (required; never modified in place).
  -d, --dir DIR       Direction to move the subject: left | right (required).
  -p, --percent N     Percent of width to shift. Default: 20.
  -o, --output PATH   Output PNG. Default: outputs/<stem>_thirds-<dir><pct>.png
  -h, --help          Show help.
EOF
}

INPUT="" DIR="" PCT=20 OUTPUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)   INPUT="$2"; shift 2;;
    -d|--dir)     DIR="$2"; shift 2;;
    -p|--percent) PCT="$2"; shift 2;;
    -o|--output)  OUTPUT="$2"; shift 2;;
    -h|--help)    usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

[[ -n "$INPUT" ]] || { echo "Error: --input required" >&2; usage; exit 1; }
[[ -f "$INPUT" ]] || { echo "Error: not found: $INPUT" >&2; exit 1; }
[[ "$DIR" == left || "$DIR" == right ]] || { echo "Error: --dir must be left|right" >&2; exit 1; }
[[ "$PCT" =~ ^[0-9]+$ ]] || { echo "Error: --percent must be an integer" >&2; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
stem="$(basename "$INPUT")"; stem="${stem%.*}"
[[ -n "$OUTPUT" ]] || OUTPUT="$ROOT/outputs/${stem}_thirds-${DIR}${PCT}.png"
mkdir -p "$(dirname "$OUTPUT")"

read -r W H < <(magick identify -format '%w %h\n' "$INPUT")
BG="$(magick "$INPUT" -format '%[pixel:p{0,0}]' info:)"

# Subject bounding box (non-background). Fuzz tolerates compression noise; corner = bg.
BBOX="$(magick "$INPUT" -fuzz 8% -format '%@' info:)"   # WxH+X+Y
bw=${BBOX%%x*}; rest=${BBOX#*x}; bh=${rest%%+*}; rest=${rest#*+}; bx=${rest%%+*}; by=${rest##*+}

want=$(( PCT * W / 100 ))
if [[ "$DIR" == right ]]; then room=$(( W - (bx + bw) )); sign=1; else room=$bx; sign=-1; fi
(( room < 0 )) && room=0
shift_px=$want
if (( shift_px > room )); then shift_px=$room; echo ">> clamped ${want}px -> ${room}px (would clip the ${DIR} edge)"; fi
off=$(( sign * shift_px ))
if (( off >= 0 )); then geo="+${off}+0"; else geo="${off}+0"; fi

echo ">> bg=$BG bbox=$BBOX dir=$DIR shift=${off}px (${PCT}% of ${W}) -> $OUTPUT"
magick -size "${W}x${H}" "canvas:$BG" "$INPUT" -gravity northwest -geometry "$geo" -composite -depth 8 "$OUTPUT"
echo ">> done: $(magick identify -format '%wx%h' "$OUTPUT")"

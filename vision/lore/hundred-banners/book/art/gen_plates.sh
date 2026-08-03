#!/bin/bash
# Generate pencil plates from plates.tsv. Usage: gen_plates.sh <from-line> <to-line>
# Lines are 1-based inclusive over plates.tsv. Skips files that already exist.
set +u
ROOT="/Users/roy/Library/CloudStorage/GoogleDrive-vaselin@gmail.com/My Drive/my-projects/luna-linear-ascent"
ART="$ROOT/plugin-linear-ascent/vision/lore/hundred-banners/book/art"
GEN="$ROOT/.cursor/skills/gemini-image/scripts/gen.py"
STYLE="Graphite pencil illustration for a printed epic-fantasy novel, dense cross-hatching, heavy blacks, strong contrast, textured paper grain, dramatic composition, fully monochrome, in the tradition of classic novel plates. No text, no words, no letters, no logos, no border, no frame."
ANCHOR="$ART/plate-03.png"
FROM="$1"; TO="$2"
n=0
while IFS=$'\t' read -r name aspect subject; do
  n=$((n+1))
  [ "$n" -lt "$FROM" ] && continue
  [ "$n" -gt "$TO" ] && break
  out="$ART/$name.png"
  if [ -s "$out" ]; then echo "SKIP $name"; continue; fi
  refargs=()
  if [ -s "$ANCHOR" ] && [ "$name" != "plate-03" ]; then refargs=(--ref "$ANCHOR"); fi
  for attempt in 1 2 3; do
    python3 "$GEN" --prompt "$subject. $STYLE" --aspect "$aspect" --out "$out" "${refargs[@]}" >/dev/null 2>&1
    if [ -s "$out" ]; then echo "OK   $name (try $attempt)"; break; fi
    echo "RETRY $name (try $attempt)"; sleep 5
  done
  [ -s "$out" ] || echo "FAIL $name"
done < "$ART/plates.tsv"
echo "LANE-DONE $FROM-$TO"

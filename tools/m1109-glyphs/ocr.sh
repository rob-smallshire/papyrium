#!/bin/sh
# OCR every page image of the M-1109 manual to a text file beside it.
cd "$(dirname "$0")/../../docs/local/m1109/pages"
for image_filename in p-*.png; do
  base=${image_filename%.png}
  [ -s "$base.txt" ] || tesseract "$image_filename" "$base" --dpi 400 -l eng --psm 4 >/dev/null 2>&1
done

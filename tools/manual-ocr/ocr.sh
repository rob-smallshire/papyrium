#!/bin/sh
# OCR a scanned printer manual, page by page, into docs/local/<name>/pages/.
#
# Usage: tools/manual-ocr/ocr.sh MANUAL_PDF NAME [DPI]
#
# Each page is rendered at DPI (default 300, the resolution these scans
# were made at) as p-NNN.png, and OCRed with Tesseract to p-NNN.txt beside
# it; pages already done are skipped, so an interrupted run can be resumed.
# The whole text is gathered into docs/local/<name>/<name>.txt with a
# "=== page N ===" line before each page. Manuals are copyrighted, so
# docs/local/ is never committed.
set -eu
pdf_filepath=$1
name=$2
dpi=${3:-300}
pages_dirpath="$(dirname "$0")/../../docs/local/$name/pages"
mkdir -p "$pages_dirpath"
if [ ! -e "$pages_dirpath/p-001.png" ]; then
  pdftoppm -r "$dpi" -gray -png "$pdf_filepath" "$pages_dirpath/p"
fi
# pdftoppm numbers pages with as many digits as the last page needs.
ls "$pages_dirpath"/p-*.png | while read -r image_filepath; do
  base=${image_filepath%.png}
  [ -s "$base.txt" ] || echo "$image_filepath"
done | xargs -P "$(sysctl -n hw.ncpu 2>/dev/null || nproc)" -I {} sh -c \
  'tesseract "{}" "$(echo {} | sed "s/\.png$//")" --dpi '"$dpi"' -l eng --psm 4 >/dev/null 2>&1'
text_filepath="$(dirname "$pages_dirpath")/$name.txt"
: > "$text_filepath"
for page_text_filepath in "$pages_dirpath"/p-*.txt; do
  number=$(basename "$page_text_filepath" .txt | sed 's/^p-0*//')
  printf '=== page %s ===\n' "$number" >> "$text_filepath"
  cat "$page_text_filepath" >> "$text_filepath"
done
echo "$(ls "$pages_dirpath"/p-*.txt | wc -l | tr -d ' ') pages OCRed into $text_filepath"

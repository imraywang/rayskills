#!/usr/bin/env bash
# render-pdf.sh — Generate PDF from editorial HTML via headless Chrome
#
# Usage:
#   bash render-pdf.sh input.html              # outputs input.pdf next to input
#   bash render-pdf.sh input.html output.pdf   # custom output path

set -e

INPUT="${1:?Usage: render-pdf.sh <input.html> [output.pdf]}"
OUTPUT="${2:-${INPUT%.html}.pdf}"

# Resolve to absolute paths
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
OUTPUT_ABS="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

if [[ ! -f "$INPUT_ABS" ]]; then
  echo "Error: input file not found: $INPUT_ABS" >&2
  exit 1
fi

# Locate Chrome
CHROME=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "/usr/bin/google-chrome" \
  "/usr/bin/chromium" \
  "/usr/bin/chromium-browser"; do
  if [[ -x "$candidate" ]]; then
    CHROME="$candidate"
    break
  fi
done

if [[ -z "$CHROME" ]]; then
  echo "Error: Chrome / Chromium not found. Install Google Chrome." >&2
  exit 1
fi

echo "Rendering: $INPUT_ABS"
echo "  via: $CHROME"
echo "  to:  $OUTPUT_ABS"

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --virtual-time-budget=12000 \
  --hide-scrollbars \
  --print-to-pdf="$OUTPUT_ABS" \
  "file://$INPUT_ABS" 2>&1 | grep -v -E "(SSL|GCM|allocator|gcm_client|registration_request|mcs_client)" || true

if [[ -f "$OUTPUT_ABS" ]]; then
  SIZE=$(ls -la "$OUTPUT_ABS" | awk '{print $5}')
  echo ""
  echo "✓ PDF generated: $OUTPUT_ABS ($SIZE bytes)"
else
  echo "Error: PDF generation failed" >&2
  exit 1
fi

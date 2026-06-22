#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for inst in gbpusd usdjpy audusd usdcad usdchf nzdusd; do
  echo "=== ${inst} h1 ==="
  npx --yes dukascopy-node@latest -i "$inst" -from 2020-01-01 -to 2026-06-20 \
    -t h1 -p bid -v -f csv -dir ./data/raw -fn "${inst}_h1" -ch -r 3 -bp 500 -s 2>&1 | grep -E "saved|rror" | head -1
done
echo "=== H1 EXTRA DONE ==="

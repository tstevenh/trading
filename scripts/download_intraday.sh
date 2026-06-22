#!/usr/bin/env bash
# Downloads intraday history for XAUUSD + EURUSD from Dukascopy.
# H1 from 2020 (6+ yrs), M15 from 2024 (~2.5 yr sample — enough for session/noise EDA).
set -euo pipefail
cd "$(dirname "$0")/.."

for inst in xauusd eurusd; do
  echo "=== ${inst} h1 ==="
  npx --yes dukascopy-node@latest -i "$inst" -from 2020-01-01 -to 2026-06-20 \
    -t h1 -p bid -v -f csv -dir ./data/raw -fn "${inst}_h1" -ch -r 3 -bp 500 -s 2>&1 | tail -3
done

for inst in xauusd eurusd; do
  echo "=== ${inst} m15 ==="
  npx --yes dukascopy-node@latest -i "$inst" -from 2024-01-01 -to 2026-06-20 \
    -t m15 -p bid -v -f csv -dir ./data/raw -fn "${inst}_m15" -ch -r 3 -bp 500 -s 2>&1 | tail -3
done

echo "=== ALL INTRADAY DOWNLOADS DONE ==="
ls -la ./data/raw/

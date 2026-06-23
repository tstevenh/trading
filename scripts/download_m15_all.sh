#!/usr/bin/env bash
# Robust M15 history for ALL 7 universe pairs from 2020 -> enables IS(pre-2023)/OOS split.
# NO `set -e` and NO `| head` (both caused the previous run to die after pair 1 via SIGPIPE).
# Per-pair full logs; continues past a failed pair; reports row counts.
cd "$(dirname "$0")/.."
rm -rf .dukascopy-cache            # clear any stale/partial cache from the failed run
mkdir -p data/raw/m15logs
for inst in xauusd eurusd usdjpy usdchf nzdusd gbpusd usdcad; do
  echo "=== ${inst} m15 (2020+) start ==="
  npx --yes dukascopy-node@latest -i "$inst" -from 2020-01-01 -to 2026-06-20 \
    -t m15 -p bid -v -f csv -dir ./data/raw -fn "${inst}_m15" \
    -r 5 -bp 600 -s > "data/raw/m15logs/${inst}.log" 2>&1
  code=$?
  rows=$(wc -l < "data/raw/${inst}_m15.csv" 2>/dev/null || echo 0)
  echo "=== ${inst} m15 done: exit=${code} rows=${rows} ==="
done
echo "=== M15 ALL DONE ==="
wc -l data/raw/*_m15.csv

#!/usr/bin/env bash
# LotClock daily collection - invoked by cron on the always-on host.
# Mirrors run_daily.cmd so the log format stays identical across both hosts;
# the model needs to know which days were actually observed, not just which
# listings were seen.
set -uo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

{
  echo
  echo "=================================================="
  echo "RUN STARTED $(date '+%a %m/%d/%Y %H:%M:%S')"
} >> logs/scrape.log

# Extra args pass through, so a backup host can add --skip-if-collected.
python3 -m scraper.run "$@" >> logs/scrape.log 2>&1
code=$?

echo "RUN FINISHED $(date '+%a %m/%d/%Y %H:%M:%S') exit=$code" >> logs/scrape.log
exit $code

#!/usr/bin/env bash
# One-shot setup for an always-on collector host (Oracle always-free VM, Ubuntu).
# Idempotent: safe to re-run after a repo update or a botched attempt.
#
#   curl -fsSL https://raw.githubusercontent.com/TALVIN29/LotClock/main/deploy/oracle_setup.sh | bash
#
# Collection must not depend on a desktop being powered on - a gap in a daily
# time series cannot be backfilled.
set -euo pipefail

REPO="https://github.com/TALVIN29/LotClock.git"
DIR="$HOME/LotClock"
UA="LotClock/0.1 (+https://github.com/TALVIN29/LotClock)"
CRON_HOUR="${CRON_HOUR:-10}"   # 10:00 local; set the VM timezone to MYT below

# --- gate: does this host's IP get served at all? ------------------------------
# GitHub Actions already failed here - motortrader's WAF 403s Azure ranges.
# Oracle is a different ASN but also a datacenter, so verify before building
# anything on top of it.
echo "checking whether this host is served..."
code=$(curl -s -o /dev/null -w "%{http_code}" -A "$UA" \
  "https://www.motortrader.com.my/car/index?page=1" || true)

if [ "$code" != "200" ]; then
  echo "BLOCKED: got HTTP $code, not 200."
  echo "This host is refused like the GitHub Actions runner was. Do not deploy here."
  echo "Options: a residential-ASN host, a different source, or keep collecting locally."
  echo "Do NOT add proxy rotation - evading the WAF while claiming to honour"
  echo "robots.txt defeats the point of the project."
  exit 1
fi
echo "served (HTTP 200) - proceeding."

# --- host prep -----------------------------------------------------------------
sudo timedatectl set-timezone Asia/Kuala_Lumpur
if ! command -v git >/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq git
fi
python3 --version   # the scraper is stdlib-only: no venv, no pip, nothing to install

# --- code ----------------------------------------------------------------------
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only
else
  git clone --depth 1 "$REPO" "$DIR"
fi
chmod +x "$DIR/deploy/run_daily.sh"

# --- secrets -------------------------------------------------------------------
# Never fetched from the repo - .env is gitignored and must be placed by hand.
if [ ! -f "$DIR/.env" ]; then
  cat > "$DIR/.env.template" <<'EOF'
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
HEALTHCHECK_URL=
SCRAPER_USER_AGENT=LotClock/0.1 (+https://github.com/TALVIN29/LotClock)
SCRAPE_DELAY_SECONDS=5
SCRAPE_MAX_LISTINGS=2000
SCRAPE_MIN_EXPECTED=200
EOF
  chmod 600 "$DIR/.env.template"
  echo
  echo "NEXT: copy your values into $DIR/.env then re-run this script."
  echo "  cp $DIR/.env.template $DIR/.env && nano $DIR/.env && chmod 600 $DIR/.env"
  echo "Template written. Nothing scheduled yet."
  exit 0
fi
chmod 600 "$DIR/.env"

# --- verify before scheduling --------------------------------------------------
echo "dry run (parses live pages, writes nothing)..."
( cd "$DIR" && python3 -m scraper.run --dry-run --max 80 )

# --- schedule ------------------------------------------------------------------
LINE="0 $CRON_HOUR * * * $DIR/deploy/run_daily.sh"
( crontab -l 2>/dev/null | grep -v -F "deploy/run_daily.sh" ; echo "$LINE" ) | crontab -

echo
echo "scheduled: daily $CRON_HOUR:00 MYT"
crontab -l | grep run_daily.sh
echo
echo "Verify tomorrow: tail $DIR/logs/scrape.log  (expect exit=0)"
echo "Then disable the Windows task so one host owns collection:"
echo "  Disable-ScheduledTask -TaskName 'LotClock daily scrape'"

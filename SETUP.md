# Setup

One-time. About 20 minutes. Everything is a free tier.

---

## 1. Supabase project

1. Go to https://supabase.com → sign in with GitHub → **New project**.
2. Name `lotclock`, pick region **Southeast Asia (Singapore)**, set a database
   password (save it in your password manager — you won't need it for this
   project, but losing it is annoying).
3. Wait ~2 minutes for provisioning.

### Create the tables

Dashboard → **SQL Editor** → **New query** → paste the entire contents of
[`schema.sql`](schema.sql) → **Run**.

You should see `Success. No rows returned`.

### Get your keys

Dashboard → **Settings** → **API Keys**. You need two values:

| field | where |
|---|---|
| `SUPABASE_URL` | "Project URL" — looks like `https://abcdefgh.supabase.co` |
| `SUPABASE_SERVICE_KEY` | a **secret key** (`sb_secret_...`) — or, on older projects, the legacy **`service_role`** key. Either works. |

Supabase runs two key systems side by side: the newer publishable/secret keys
(`sb_publishable_...` / `sb_secret_...`) and the legacy `anon` / `service_role`
JWTs. We need the **elevated** one — secret or service_role — because the
collector writes on a schedule with no user session to authorise it.

> **This key bypasses row-level security.** Anyone holding it can read and delete
> your entire database. It goes in GitHub Secrets and your local `.env` — never
> in code, never in a commit, never in a screenshot, never pasted into a chat.
> If it ever leaks, rotate it immediately on this same dashboard page and treat
> it as compromised from the moment it was exposed, even if you delete the commit.
>
> Never use the **publishable**/`anon` key here — it is deliberately powerless
> and the writes will fail with a 401.

---

## 2. Dead-man's switch (recommended)

This catches the failure nothing else does: the workflow silently never running
at all. No error fires, so nothing alerts — unless something is watching for
*silence*.

1. Sign up free at https://healthchecks.io
2. **Add Check** → name `lotclock-daily` → period **1 day**, grace **6 hours**
3. Copy the ping URL (`https://hc-ping.com/<uuid>`)

If a daily ping doesn't arrive, healthchecks emails you.

---

## 3. Local `.env` (for testing on your machine)

```bash
cp .env.example .env
```

Fill in `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `HEALTHCHECK_URL`.

`.env` is gitignored. Confirm before your first commit:

```bash
git check-ignore -v .env      # must print a .gitignore line
```

If that prints nothing, **stop** and fix `.gitignore` before committing.

---

## 4. GitHub repository secrets

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository
secret**. Add three:

| name | value |
|---|---|
| `SUPABASE_URL` | your project URL |
| `SUPABASE_SERVICE_KEY` | the `service_role` key |
| `HEALTHCHECK_URL` | your hc-ping.com URL |

---

## 5. First run

```bash
# local, no writes — confirms parsing still works against the live site
python -m scraper.run --dry-run --max 80
```

Then trigger the real thing from GitHub: **Actions** tab → **daily-scrape** →
**Run workflow**.

> Scheduled workflows only start running after the workflow file exists on your
> **default branch**. Push to `main` first, or the cron never fires.

### Confirm it worked

Supabase → SQL Editor:

```sql
select scraped_at, count(*) from listing_snapshot group by 1 order by 1 desc;
```

---

## 6. The gate that actually matters

Run it again **the next day**, then:

```sql
-- same listing captured on two different days
select listing_id, count(distinct scraped_at) days
from listing_snapshot
group by 1 having count(distinct scraped_at) > 1
limit 10;

-- a price that actually moved — this is the entire thesis
select listing_id, min(price_myr) lo, max(price_myr) hi, count(*) snaps
from listing_snapshot
group by 1 having min(price_myr) <> max(price_myr);
```

The second query returning rows is the moment this project becomes real. Nothing
downstream — no liquidity model, no negotiation-room estimate — is possible
without it.

Record the date of your first successful run in `PROGRESS.md` under
**Data collection started**. That date is day 0 of the only asset here that
compounds.

---

## 7. Second collector on another machine (do this next)

**Checkpoint as of 2026-08-05:** the desktop collects daily at 10:00 and is
working. Aug 1–3 were missed because the machine was powered off. Rather than
chase an always-on host — Oracle's free tier rejected the signup, there is no
card for a VPS, and the motortrader allowlist email is unanswered — a second
machine on a different power schedule covers the gaps, and Phase 1 models the
remainder as interval censoring. See the 2026-08-05 decision in `PROGRESS.md`.

Run these **on the laptop**, in order.

The path below is the laptop's; `install_task.ps1` uses `$PSScriptRoot`, so any
location works — just keep it consistent with the commands that follow.

Clone the repo:

```powershell
git clone https://github.com/TALVIN29/LotClock.git E:\Portfolio\LotClock
```

Copy `.env` across **by hand** — it is gitignored and will not come with the
clone. Use a USB stick or retype it; do not email it to yourself. If the other
machine isn't with you, start from `.env.example` and read the values back out
of the web dashboards — Supabase → Settings → API Keys, and healthchecks.io for
the ping URL. Use the *same* key as the primary host, don't mint a new one.

Create the venv:

```powershell
python -m venv E:\Portfolio\LotClock\.venv
```

Install dependencies — the scraper needs `scrapling` for parsing, so a bare
venv is not enough:

```powershell
E:\Portfolio\LotClock\.venv\Scripts\python.exe -m pip install -r E:\Portfolio\LotClock\requirements.txt
```

Confirm parsing works from this machine before scheduling anything:

```powershell
E:\Portfolio\LotClock\.venv\Scripts\python.exe -m scraper.run --dry-run --max 80
```

Register the backup task, in an **Administrator** PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File E:\Portfolio\LotClock\install_task.ps1 -Backup
```

`-Backup` runs at 20:00 instead of 10:00 and passes `--skip-if-collected`, so if
the desktop already took today's snapshot this host exits in about two seconds
without touching motortrader. Redundancy must not double the request load on a
source that grants access on the strength of good behaviour.

Don't wait until tomorrow to find out the keys are wrong — trigger it once by
hand. Running early is safe: the scheduled 20:00 run will then see the day
already collected and skip, so the source isn't hit twice.

```powershell
Start-ScheduledTask -TaskName "LotClock daily scrape (backup)"
```

Then watch the log:

```powershell
Get-Content E:\Portfolio\LotClock\logs\scrape.log -Tail 5
```

Expect either `exit=0` after a real collection, or the line
`today already collected by another host, skipping`. Both are healthy.

A freshly registered task reports `LastTaskResult 267011` until its first run.
That means "has not run yet", not a failure.

### What "done" looks like now

The old target was seven consecutive days with no gap. That is no longer the
goal — with no always-on host it is not achievable, and it is not what the model
needs. The target is **every gap being a known interval rather than a silent
hole**: `scrape_run` has a row for every observation day, and both machines are
scheduled. Check the run log after a week and confirm the missing days are
visible, not that there are none.

---

## Troubleshooting

| symptom | cause |
|---|---|
| `KeyError: 'SUPABASE_URL'` | secret not set, or `.env` not loaded locally |
| Action green but no rows | check the log — likely `under_threshold`, exit 1 |
| `HTTP 401` from Supabase | wrong key, or you used `anon` instead of `service_role` |
| 0 listings parsed | site markup changed — run `pytest tests -q`, it's designed to catch this |
| Scheduled run never fires | workflow file isn't on the default branch, or repo has been inactive 60 days |

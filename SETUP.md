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

Dashboard → **Project Settings** → **API**. You need two values:

| field | where |
|---|---|
| `SUPABASE_URL` | "Project URL" — looks like `https://abcdefgh.supabase.co` |
| `SUPABASE_SERVICE_KEY` | "Project API keys" → **`service_role`** → reveal & copy |

> **The `service_role` key bypasses row-level security.** Anyone holding it can
> read and delete your entire database. It goes in GitHub Secrets and your local
> `.env` — never in code, never in a commit, never in a screenshot. If it ever
> leaks, rotate it immediately in the same dashboard page and treat it as
> compromised from the moment it was exposed, even if you delete the commit.

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

## Troubleshooting

| symptom | cause |
|---|---|
| `KeyError: 'SUPABASE_URL'` | secret not set, or `.env` not loaded locally |
| Action green but no rows | check the log — likely `under_threshold`, exit 1 |
| `HTTP 401` from Supabase | wrong key, or you used `anon` instead of `service_role` |
| 0 listings parsed | site markup changed — run `pytest tests -q`, it's designed to catch this |
| Scheduled run never fires | workflow file isn't on the default branch, or repo has been inactive 60 days |

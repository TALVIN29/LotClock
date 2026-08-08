# LotClock — Progress

**Status:** phase 1 — **collecting.** 32,178 rows in Supabase across **16 observed
days** of 21 calendar days since day 0. Desktop scheduled task `Ready`, next run
2026-08-09 10:00.
**Repo:** https://github.com/TALVIN29/LotClock (public, `main` is default)
**Data collection started: 2026-07-19** ← day 0 of the only asset that compounds
**Continuity:** longest clean streak **7 days (07-25 → 07-31)**. Current streak **2
days (08-07, 08-08)**. Gaps: 07-24, 08-01, 08-02, 08-03, 08-06 — see the log below.
**Hours spent:** ~8 / 18
**Previous session:** 2026-08-08 — continuity audit. Counted rows per day straight out of
Supabase instead of trusting `logs/scrape.log`, and back-filled 20 unrecorded runs into
the collection log below. Found that 07-24 started, was killed with `^C`, and wrote
**zero** rows — the log's `RUN STARTED` line had been hiding a lost day. Single-host
collection is the root cause of every gap; the laptop is the fix.

**Last session:** 2026-08-08 (later) — armed the full census and made it survivable.
See the section directly below; that is where to start reading.

## 2026-08-08 (later) — full census armed, and a 45-minute run made interruptible

The 15% coverage problem is fixed at the source: the crawl now stops when it runs out
of cars, not out of budget. `MAX_LISTINGS` 2,000 -> 20,000, `MAX_PAGES` -> 700,
`MIN_EXPECTED` 200 -> 8,000 (~60% of the known 13,029 inventory).

**The cap lived in `.env`, not only in the code.** `SCRAPE_MAX_LISTINGS=2000` and
`SCRAPE_MIN_EXPECTED=200` were set there, and `os.getenv` means the environment wins.
Raising the constants in `run.py` alone would have changed nothing — the next run would
have capped at 2,000 exactly as before, and the census would have looked broken for a
reason nothing in the code showed. Both `.env` and `.env.example` now carry the new
values. **Check `.env` first whenever a constant appears not to take effect.**

### Writes now flush per batch, mid-walk

A census is ~45 minutes (543 pages x the 5s crawl-delay) where the old run was ~8, and
`save_snapshots` used to be called once, after the walk. A run killed at minute 40 wrote
**zero** rows — which is exactly how 07-24 was lost, with a 6x wider window.

`collect()` now buffers and writes whenever the buffer passes `store.BATCH` (500).
Because the write is idempotent on `(listing_id, scraped_at)`, a partial write plus a
later re-run compose into a complete day with no reconciliation code. A killed run now
loses at most the current buffer instead of the day.

Consequence, accepted deliberately: **`MIN_EXPECTED` can no longer gate the write** —
rows are already in the database by the time the total is known. It labels the day
instead, via the `under_threshold` status that `scrape_run` already had. The run still
exits 1 and still withholds the healthcheck ping, so a thin day is loud. A thin day
recorded as thin is usable; a thin day thrown away leaves a hole indistinguishable from
a day nobody looked. Same principle as the 08-05 gap decision.

### `already_collected()` had to change with it

It tested whether *any* row existed for today. That was correct only while a run wrote
all-or-nothing. Under per-batch writes, a run killed halfway leaves thousands of rows,
an existence test reads that as "done", and the laptop's 8pm `--skip-if-collected`
**skips the host that could have finished the day.** It now counts rows (PostgREST
`Prefer: count=exact`, new `store.day_row_count()`) and compares against the same
threshold, read from the same env var so the two can never disagree.

### ⚠️ Coverage is now a regime change — do not model across it

Census day one adds roughly 11,000 listings never seen before. Any later day that falls
back to a partial harvest makes 85% of them vanish at once, which is **not** a wave of
sales.

- Treat the 15% -> 100% transition as a **censoring event**. Any absence computed across
  that boundary is invalid.
- The exit-rule table below (N = 5/6) was fitted entirely on ~2,010-row days. It stands
  for that era only and **must not be pooled** with census days.
- Re-run `exit_rule.py` once census days accumulate, conditioned on per-day coverage.
  `scrape_run.rows_ok` plus the per-day counts are what that conditioning reads.

### Verified, not assumed

- 9 scraper tests pass (`tests/test_collect.py` is new — an interrupted walk keeps its
  finished batches, a dry run writes nothing, a complete walk flushes its remainder),
  plus `test_train.py` 4 passed and `exit_rule.py --test` ok.
- Bounded live run, `--max 600`: **flushed 513 rows at page 24, mid-walk** — the whole
  point. Ran twice; 08-08 went 2,020 -> 2,105 rows, so idempotency held (1,219 rows
  written, 85 net new) and the +85 are listings the morning's 15% sample had missed.
- Thin run exits 1 and logs `under_threshold` — `scrape_run` ids 37 and 38 confirm it.
- `--dry-run --max 100` printed no flush line and left the count at 2,105.
- Not re-tested live: a real `^C` mid-walk. The stubbed test pins it, and re-proving it
  against motortrader costs ~28 pages of crawl for a weaker signal.

**Next action: read `logs/scrape.log` after the 08-09 10:00 run.** Four things, and the
run is only a census if all four hold:

1. `"no new listings for 3 pages, assuming end of results"` **appears**
2. `"reached max_listings"` does **not** appear — if it does, the site grew past 20,000
3. page count lands near **543**, listings near **13,029**
4. wall time is inside the 2 h `ExecutionTimeLimit` in `install_task.ps1` (~45 min expected)

Then, still open and unchanged: the healthchecks.io dashboard check below, and the
laptop collector.

## 2026-08-08 (same session) — the exit rule, fitted not guessed

`exit_rule.py` (new, self-checking: `python exit_rule.py --test`) measures how long
absences actually last, in OBSERVED days, and picks the smallest N where "absent N days
running" stops reversing. Closed gaps only count as returns; a run of absence that
reaches the end of the data is censored, so it sits in the denominator and never in the
numerator.

| N days absent | reached | came back | return rate |
|---|---|---|---|
| 1 | 2,376 | 2,081 | 87.6% |
| 2 | 565 | 433 | 76.6% |
| 3 | 189 | 96 | 50.8% |
| 4 | 108 | 26 | 24.1% |
| 5 | 77 | 9 | 11.7% |
| **6** | 64 | 0 | **0.0%** |

Geometric decay, no ambiguity about the shape. **N = 6** is the smallest threshold under
5%. Under it **64 listings count as exited**, against 295 by naive last-seen — so the
naive count was ~4.6x inflated.

**Caveat to carry into any writeup:** with 16 observed days, a 6-day gap has little room
left to close, so the 0% at N>=6 is partly window-limited. N = 5 (11.7%) is the estimate
standing on firmer ground. More observed days will settle it; re-run `exit_rule.py` as
the series grows and watch whether N drifts.

Note the noise is dominated by 1-day flicker (1,648 of 2,081 closed gaps), which is what
a pagination-instability explanation predicts.

## 2026-08-08 — coverage audit: the sold-event does not survive contact with the data

Measured, not guessed. Three findings, in order of how much they hurt:

1. **The crawl cap binds every single run — 16 of 16.** `grep "reached max_listings"
   logs/scrape.log` returns 16; `"no new listings for 3 pages"` returns 0. The run has
   never once reached the end of results, so every day is a partial harvest of ~2,010.

2. **The site holds 13,029 listings. We collect 15% of them.** Page 1 markup states the
   count; probing confirms real results end at page ~543 (24 real listings per page,
   plus a 12-card featured block that repeats on *every* page — which is why a naive
   "last non-empty page" probe reports 6,399 and is wrong).

3. **87.6% of disappearances reappear later — 2,081 of 2,376.** Dropping the final
   transition, where reappearance is impossible by construction, it is **94%**. Daily
   "gone" runs 150–180 listings; only **295** listings vanished permanently across the
   whole 21 days. The noise is roughly 10x the signal. **A survival model fitted on
   absence-as-sold today would mostly be modelling crawl noise.**

Supporting detail: only **2,314 distinct listing_ids** appeared across 21 days while
collecting ~2,010/day. The same cars are seen every day and only ~15 genuinely new IDs
arrive daily, so the index is not recency-sorted at the top and the cap is not pushing
old cars off the end. The flicker has another cause — most likely pagination
instability: the run walks 92 pages over ~8 minutes at the 5s crawl-delay, and any
reordering between page requests drops listings across page boundaries.

Also confirmed, and good news: **155 of 2,314 listings changed price** at least once
(schema.sql verification query 3, run for the first time). Price movement is real and
observable. That half of the thesis stands.

Consequence: **coverage and event-definition come before any modelling.** Two separate
fixes, independent of each other —
- *coverage*: 543 pages at 5s is ~45 min/day for a full census, versus 8 min for 15%;
- *event definition*: require absence on N consecutive observed days before calling a
  listing sold, instead of trusting a single day's absence. Costs nothing to compute
  and is the direct answer to the 94% reappearance rate.

Audit scripts were throwaway (scratchpad, read-only, no writes to Supabase).

**Next action (superseded — see the 08-09 log check at the top): install the backup
collector on the laptop (model 83JN).**
One step at a time:

1. `git clone https://github.com/TALVIN29/LotClock C:\LotClock`
2. copy `.env` across by hand — it is gitignored and must never be committed
3. create `.venv` there and `pip install -r requirements.txt`
4. `python -m scraper.run --dry-run` — proves fetch + parse work on that host before
   anything is scheduled
5. `powershell -ExecutionPolicy Bypass -File C:\LotClock\install_task.ps1 -Backup`
   as admin — registers `LotClock daily scrape (backup)` at 8pm with
   `--skip-if-collected`

Verified on the desktop 2026-08-05: `--skip-if-collected` exits 0 without scraping when
the day is already covered, and the 5 existing tests still pass, so the backup host adds
no load on motortrader on days the desktop already ran. See the 2026-08-05 decision
below for why gaps are modelled rather than engineered away.

**Also open: the dead-man's switch has never been proven to fire.** `HEALTHCHECK_URL`
is pinged from `scraper/run.py`, but no alert has been confirmed for the 08-01→08-03 or
08-06 gaps, and this cannot be checked from the code side — the ping URL exposes no
history. Open the healthchecks.io dashboard, read the event history for 08-01 and 08-06,
and confirm period = 1 day, grace ≤ 6 h, and an email destination that actually exists.
Record the verdict here with the event timestamp. Until then, treat gap detection as
manual.

**Earlier next-action list (day-1 checks, kept for reference):**
1. **2026-07-20 after 10:00 — the day-1 checks. This is the whole session.**
   Three things, in this order, because each one is worthless if the previous
   failed:

   a. **Did the run happen at all?** `logs/scrape.log` should have a new
      `RUN STARTED`/`RUN FINISHED ... exit=0` pair, and healthchecks.io should
      be green. A *missing* log entry means the task didn't fire — that is the
      exact failure that hid on day 0, so check it first and don't infer it
      from row counts.

   b. **Are there two distinct dates?** No second date, no time series:
      ```sql
      select scraped_at, count(*) from listing_snapshot group by 1 order by 1;
      ```

   c. **Did any price move?** The real gate. A price that moved is the entire
      thesis; nothing downstream exists without it:
      ```sql
      select listing_id, min(price_myr) lo, max(price_myr) hi, count(*) snaps
      from listing_snapshot group by 1 having min(price_myr) <> max(price_myr);
      ```
      **Expect zero or close to it on day 1, and don't panic** — cars don't get
      repriced overnight. This query becoming non-empty is a day-7-to-14 event.
      Day 1 only has to prove two dates exist and rows repeat by `listing_id`.

2. **Await motortrader reply** (sent 2026-07-19 to lai@motortrader.com.my,
   MT Digital Sdn Bhd). If they allowlist, the GitHub Actions workflow already
   in the repo starts working and collection stops depending on this PC being
   awake. If they decline, honour it — that ends motortrader as a source and
   carsome becomes the plan, not a redundancy.
3. Optional: Oracle always-free VM. **Test with one curl before configuring
   anything** — Oracle is also a datacenter ASN and may get the same 403:
   ```
   curl -s -o /dev/null -w "%{http_code}\n" -A "LotClock/0.1 (+https://github.com/TALVIN29/LotClock)" "https://www.motortrader.com.my/car/index?page=1"
   ```

Scheduled task: `LotClock daily scrape`, daily 10:00 MYT, wakes from sleep,
catches up missed runs. Logs to `logs/scrape.log`.

Full walkthrough: `SETUP.md`

> `Next action` is the anti-abandonment field. Update it at the **end** of every
> session, never the start. Future-you reads this first.

## Phases

- [x] 0. `PROGRESS.md`
- [ ] 1. Collector  ← **current**
  - [x] Recon: source selection, robots.txt, rendering check
  - [x] Parser + 5 tests passing on a real saved page
  - [x] Fetcher (5s crawl-delay, honest UA, retry/backoff)
  - [x] Supabase writer (append-only, idempotent)
  - [x] GitHub Actions workflow — **built, but 403'd by Cloudflare**
  - [x] Supabase project created, `schema.sql` run
  - [x] Repo secrets set
  - [x] **First run verified end-to-end — 216 rows in the database**
  - [x] Windows scheduled task registered, verified running
  - [x] Second day's run — proves the time series (2026-07-20)
  - [x] 7 days of collection — 07-25 → 07-31, clean
  - [x] Full census — cap raised past the real end of results, `.env` raised to match
  - [x] Per-batch writes so a 45-min run survives being killed
  - [ ] Confirm the 08-09 run is a real census (4 checks at the top) ← NEXT
  - [ ] Second collector host (laptop) so one machine being off is not a gap
- [ ] 2. Spec join table + government data (JPJ, fuel, OPR)
- [ ] 3. Entity resolution + credibility scorer
- [ ] 4. Model v0
- [ ] 5. Site, two routes
- [ ] 6. Ship — Vercel, screenshot, README

## Phase 1 exit gates

- [x] Runs 7 consecutive days unattended, zero manual intervention — 07-25 → 07-31.
      Broke afterwards: 5 gap days in 21 (07-24, 08-01…03, 08-06), all one host being
      off. Re-gate as **7 consecutive days with two hosts live**
- [x] ≥2,000 unique listings captured — 2,016 on day 0
- [ ] **≥1 price change captured for the same `listing_id`** ← the real gate
- [ ] ≥1 delisting captured
- [ ] Dead-man's switch verified by deliberately breaking it — **armed**
      2026-07-19 (healthchecks.io, `HEALTHCHECK_URL` set, ping test-fired
      through `ping_healthcheck()` and returned 200). Still unverified: proving
      it goes *red* requires letting one period + grace lapse with no ping.
      **2026-08-08: four such lapses have now happened by accident (08-01…08-03,
      08-06) and it is still unknown whether any alert arrived.** Check the
      healthchecks.io event history for those dates — if nothing fired, the switch is
      decoration.

## Decisions made (and why)

- 2026-07-19: **Source = motortrader.com.my**, not Carlist or Mudah.
  Carlist returns 403 to datacenter IPs (so GitHub Actions would fail too);
  Mudah's robots.txt *expressly forbids* automated access. Motortrader's
  robots.txt has an empty `Disallow`, `Allow: /`, and `Crawl-delay: 5` — an
  explicit permission with a stated rate.
- 2026-07-19: **No Scrapy.** This is ~560 sequential GETs, not a concurrent
  crawl needing pipelines. stdlib `urllib` does it with nothing to maintain.
- 2026-07-19: **No supabase-py.** PostgREST takes a plain POST; a dependency
  wrapping `urllib` isn't worth it. Scraper has zero runtime dependencies.
- 2026-07-19: **No n8n.** It needs a machine left on, which defeats the whole
  constraint. GitHub Actions emails on failure natively; healthchecks.io covers
  the "workflow never fired at all" case that nothing else catches.
- 2026-07-19: **Scrape the index pages, not individual listings.** 34 listings
  per request instead of one, and the sitemap turned out to be full of expired
  listings anyway.
- 2026-07-19: **Price and monthly installment parsed by separate patterns.**
  Every card shows both (`RM 170,888` and `RM 2,304 / month`); confusing them is
  the classic bait-price bug. A test asserts they never cross.

- 2026-08-05: **Stop chasing an always-on host. Tolerate gaps and model them
  as interval censoring instead.** Aug 1–3 were missed because the desktop was
  powered off — not a config fault (`WakeToRun` and `StartWhenAvailable` were
  both already set; a wake timer cannot boot a machine that is shut down).
  Every hosting fix was closed off: Oracle's free-tier signup rejects the
  account, no credit card for a VPS, the motortrader allowlist email is still
  unanswered, and BIOS RTC wake fails the moment the PC is unplugged for a trip.

  The requirement was the expensive part, not the infrastructure. Daily
  observation is not what survival analysis needs — knowing *when we looked* is.
  A listing last seen Aug 5 and gone by Aug 9 is interval-censored, which is
  standard and honest, not a workaround. `scrape_run` already records every
  observation day, so the gaps are known rather than silent — that is the line
  between messy data and unusable data. Days-on-market at ±3-day resolution is
  still a number that does not exist for this market.

  Mitigation, zero cost: **the laptop collects too** (`install_task.ps1 -Backup`,
  20:00, `--skip-if-collected`). Two machines with different power schedules
  means either one being off no longer creates a gap. `store.already_collected()`
  makes the second host exit early on a day the first covered, so redundancy
  never doubles the request load on a source that granted access on the strength
  of good behaviour.

  **Phase 1 must use an interval-censored fit, not a daily-exact one**, and the
  Kaggle data card must state the observation gaps. Being explicit about them is
  a credibility gain, not a weakness.

## ⚠️ Blocker found 2026-07-18: motortrader 403s GitHub Actions IPs

First real workflow run failed: `HTTP 403` on every page, run
[29654172225](https://github.com/TALVIN29/LotClock/actions/runs/29654172225).

Diagnosed as purely IP-range based — identical code, user-agent and timing
returned `200` from a non-cloud IP and `403` from the GitHub runner in the same
minute. GitHub Actions runs on Azure ranges that most WAFs block wholesale.
Their robots.txt still permits crawling at `Crawl-delay: 5`; it is the edge
infrastructure blocking cloud IPs generically, not a policy against us.

**Not doing:** proxy rotation, IP spoofing, CAPTCHA solving. Honouring robots.txt
while routing around the WAF that enforces it would defeat the point of the
project.

**The failure handling worked** — loud exit 1, `under_threshold` logged, no
silent green run over an empty database. That part of the design is validated.

Options under consideration (see chat 2026-07-18):
- A. Windows Task Scheduler on the builder's PC — works today, gaps when off
- B. Oracle Cloud always-free VM — genuinely unattended, non-Azure IP
- C. Email motortrader.com.my requesting access for a student research project
- D. Switch source again — weak: carlist blocks harder, mudah forbids outright

This is Porter's "supplier power: VERY HIGH" materialising on day one, exactly as
predicted. Worth writing up in the README as a finding rather than hiding.

## Source survey 2026-07-19 — why motortrader, and what else exists

Surveyed every Malaysian used-car site I could find. Motortrader was not a
preference; it was the only one clean on all three axes at once — permitted by
robots, reachable from a script, and server-rendering prices into HTML.

| site | robots.txt | reachable | rendering | verdict |
|---|---|---|---|---|
| **motortrader** | `Allow: /`, `Crawl-delay: 5` | 200 | server-rendered, 34/page | **in use** |
| carsome | permissive | 200 | Nuxt payload, parseable w/o browser | **best 2nd source** |
| carsifu | `Allow: /` | 200 | client-side XHR | needs Playwright |
| carousell | permissive on listings | 200 | heavy JS, 1.6MB pages | low priority |
| mytukar | `Disallow:` (empty) | redirects to carro.co | no listings in sitemap | dead end |
| carlist | permits crawling | **403** | — | Cloudflare blocks scripts |
| **mudah** | **"expressly forbidden to use spiders"** | — | — | **excluded on principle** |
| **carbase** | **`Disallow: /cars-for-sale/`** | — | — | **excluded on principle** |
| **wapcar** | `Allow: /` but **`Content-Signal: ai-train=no`** | — | — | **excluded on principle** |
| oto, carking, carvara, icarsclub | — | DNS fail / timeout | — | dead sites |

**Three exclusions are ethical, not technical** — all three are reachable. Wapcar
is the notable one: its robots.txt says `Allow: /`, so a robots-only check passes
it. The `Content-Signal: ai-train=no` header is what refuses it, and this project
trains a model on what it collects. Scraping it would be technically compliant
and substantively dishonest. Worth stating in the README.

Next source when redundancy is wanted: **carsome** — Nuxt embeds its data in the
page, so it parses with stdlib and needs no browser, consistent with the current
zero-dependency design. Not now though: one working source collecting daily beats
two half-built ones.

## Known limitations (record honestly, do not hide)

- **Mileage is banded at source** (`75k-79k`), not exact. Midpoint imputation
  only.
- Featured listings repeat on every index page (~12/page); deduped by
  `listing_id` and by the DB unique constraint.
- Single source so far. Multi-source is the resilience plan but isn't built.
- Delisted ≠ sold. Resolving that is phase 3 work.

## Blocked / open questions

- ~~Does `HEALTHCHECK_URL` need a paid healthchecks.io tier for daily?~~
  Answered 2026-07-19: free tier covers it. One check, configured and pinging.
- Full pass is ~563 pages ≈ 47 min. Start capped at 2,000 listings; decide later
  whether the full 12,954 daily is worth the load on their server.

## Collection log (append each run)

Row counts read from Supabase on 2026-08-08 (`count=exact` per `scraped_at`), not from
`logs/scrape.log` — a run can start, log, and still write nothing. Gap rows are recorded
deliberately: the survival model has to know which days were *observed*, and a missing
row in this table is indistinguishable from a day nobody looked.

| date | rows | source | notes |
|------|------|--------|-------|
| 2026-07-19 | 2,016 | local PC + scheduled task | day 0; two runs, `on_conflict` bug found and fixed. Price range RM 4,800 – RM 6,888,000 |
| 2026-07-20 | 2,011 | scheduled task | second day — time series exists |
| 2026-07-21 | 2,013 | scheduled task | |
| 2026-07-22 | 2,002 | scheduled task | |
| 2026-07-23 | 2,020 | scheduled task | |
| 2026-07-24 | **0** | — GAP — | run started 20:58, killed with `^C`, wrote nothing. See below |
| 2026-07-25 | 2,002 | scheduled task | streak restarts |
| 2026-07-26 | 2,014 | scheduled task | |
| 2026-07-27 | 2,014 | scheduled task | |
| 2026-07-28 | 2,009 | scheduled task | |
| 2026-07-29 | 2,004 | scheduled task | |
| 2026-07-30 | 2,011 | scheduled task | |
| 2026-07-31 | 2,015 | scheduled task | **7 clean days (07-25 → 07-31)** — longest so far |
| 2026-08-01 | **0** | — GAP — | desktop off |
| 2026-08-02 | **0** | — GAP — | desktop off |
| 2026-08-03 | **0** | — GAP — | desktop off |
| 2026-08-04 | 2,013 | scheduled task | `-StartWhenAvailable` caught up only the day it came back, not the three missed |
| 2026-08-05 | 2,005 | scheduled task | parser swapped regex → selectors, output byte-identical |
| 2026-08-06 | **0** | — GAP — | desktop off |
| 2026-08-07 | 2,009 | scheduled task | |
| 2026-08-08 | 2,020 | scheduled task | **32,178 rows total, 16 observed days of 21** |

## Lost day 2026-07-24: a run that started, logged, and wrote nothing

`logs/scrape.log` shows `RUN STARTED Fri 07/24/2026 20:58:30`, then `^C`, then nothing
— no `RUN FINISHED`, no error, no row in the database. Something interrupted it: a
closed console or a shutdown while it was walking the index.

This is a **third** failure mode, and the one the existing guards miss:

1. the task never fires — no log line at all (the folder-rename bug)
2. the task fires and fails — `RUN FINISHED ... exit=1`
3. **the task fires, logs `RUN STARTED`, and dies silently** — looks like a *successful*
   day if you only skim for start lines

Guard: never infer a collected day from the log. `scraped_at` counts in Supabase are the
only record that matters, which is exactly what the query at the top of this log does.

## Bug found and fixed 2026-07-19: re-runs were not idempotent

The scheduled task collected 2,006 listings then died with `HTTP 409 Conflict`
on write. `Prefer: resolution=ignore-duplicates` is not sufficient on its own —
PostgREST resolves conflicts against the **primary key**, which here is the
surrogate `id`. The constraint that matters is the composite
`(listing_id, scraped_at)`, so it must be named explicitly:
`?on_conflict=listing_id,scraped_at`.

The earlier commit claiming re-runs were idempotent was simply wrong. Verified
properly this time: re-inserting an existing row leaves the count unchanged and
returns no error.

Worth noting *why* this surfaced now rather than on day 30 — running the same
day twice is exactly what `-StartWhenAvailable` will do after a missed run.

## Bug found and fixed 2026-07-19: scheduled task pointed at the old folder path

Renaming `E:\Portfolio\price-story` to `E:\Portfolio\LotClock` broke the task.
Its registered action still read `E:\Portfolio\price-story\run_daily.cmd`, a
path that no longer exists. The 12:51 run returned `LastTaskResult = 1` and the
next run was scheduled to fail the same way.

Fixed by re-running `install_task.ps1` from the new folder — it builds the
action from `$PSScriptRoot`, so it re-registers with the correct path by
construction. Verified: the task's `Execute` now reads
`E:\Portfolio\LotClock\run_daily.cmd`.

**The failure mode matters more than the bug.** `run_daily.cmd` is what writes
`logs/scrape.log`, so a task that never starts it produces *no* log line at all
— not an error, just nothing. A missing day looks identical to a day the
scraper was never scheduled for. The only signal is the gap itself, and gaps
are exactly what a days-to-sell model has to reason about. Two guards worth
having before day 30:

- an external dead-man's switch (the already-planned `HEALTHCHECK_URL` — it
  fires on *absence* of a ping, which is precisely this case)
- a `collection_days` table, or a query over `distinct scraped_at`, so an
  observed day is a recorded fact rather than an inference from listing rows

Neither is built yet. Until one is, verify the task after any folder move:
`(Get-ScheduledTask -TaskName "LotClock daily scrape").Actions.Execute`

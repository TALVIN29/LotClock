# LotClock — Progress

**Status:** phase 1 — **census coverage, and the reason runs kept dying is now known
and fixed.** 164,647 rows in Supabase across **28 observed days** of 35 calendar days
since day 0. Desktop scheduled task re-registered **S4U** 2026-08-22, so a run no
longer dies with the desktop session.
**Repo:** https://github.com/TALVIN29/LotClock (public, `main` is default)
**Data collection started: 2026-07-19** ← day 0 of the only asset that compounds
**Continuity:** longest clean streak **7 days (07-25 → 07-31)**. Gaps: 07-24, 08-01,
08-02, 08-03, 08-06, 08-13, 08-18. Thin days: 08-15 (4,097), 08-11 (8,153),
08-21 (8,657) — all killed mid-walk, see the section directly below.
**Coverage regime:** 07-19 → 08-08 are ~15% partial harvests (~2,010 rows/day).
**2026-08-09 onward is census era (~12,400 rows/day).** Never pool the two.
**Census days safe to model on: 08-09, 08-10, 08-12, 08-14, 08-17, 08-19, 08-20,
08-22** — the eight that ran to exhaustion with `exit=0`. 08-16 (11,702) is
near-complete but unfinished; 08-11, 08-15, 08-21 are thin.
**Hours spent:** ~14 / 18
**Previous session:** 2026-08-16 — continuity re-audit against the database. Three of
the last six runs killed mid-walk, cause unidentified.
**Last session:** 2026-08-22 — **found the cause: the scheduled task ran with
`LogonType Interactive`.** Fixed, and 08-22 re-collected to a full census. See the
section directly below; that is where to start reading.

## 2026-08-24 — the census era gets its own numbers, and they are not comparable

`price_moves.py` only ever ran on the partial-harvest era; the census era — the regime
everything from here on is modelled in — had no price numbers at all. It now takes
`--census`, which selects days from `observed_days()`: census-era days that clear
`COMPLETE_MIN` (10,000 rows), so the killed walks 08-11, 08-15 and 08-21 drop out
automatically. Their absences are a coverage artefact and would read as exits.

Both windows, same code, run 2026-08-24:

| | partial era 07-19..08-08 | census era 08-09..08-24 |
|---|---|---|
| observed days | 16 | 11 |
| listings | 2,315 | 13,181 |
| cut rate | 6.56% | 1.17% |
| median first cut | 2.07% / RM4,000 | 1.88% / RM5,000 |
| observed days to first cut | 7.0 | 6.0 |
| exits under N=5 | 68 | 47 |
| censored | 97.1% | **99.6%** |

**The two cut rates must not be read as a change in the market.** Window length is part
of it, but the sharper reason is survivorship: the partial harvest could only see a
listing twice if it lived long enough to be caught twice, so it oversampled exactly the
listings with time to cut. Sampling artefact, not a falling market. The cut *sizes* are
what survive the comparison, and they agree: ~2% of asking price.

**Superseded the same day — read the reframe at the bottom of this file before quoting
the exit numbers above.** The `exited` / `censored` rows here use N=5, and refitting
`exit_rule.py` on all 30 observed days that afternoon measured a 60.2% reversal rate at
5 days absent. N=5 is wrong; the defensible threshold is N=10, which the census era
cannot carry (1 exit in 13,172). The price-cut rows stand — they never depended on the
exit rule. The `--census` window itself stands too.

## 2026-08-22 — the runs were never crashing, Windows was killing them

Six days of "forced terminate" (`0xC000013A`) had no explanation because the evidence
had been thrown away: **`Microsoft-Windows-TaskScheduler/Operational` was disabled**
(`IsEnabled: False`), so Task Scheduler recorded no history at all. The 08-16 session
stopped at "the log lies" and never checked the task's own configuration. That was the
miss — the answer was one `Get-ScheduledTask` away the whole time.

**The signature.** Every dead run ends the same way: a literal `^C` in `scrape.log`
and then nothing. `run_daily.cmd` never reaches its own `RUN FINISHED` line, so the
entire process tree is hard-killed from outside. That is not a Python crash — a crash
still lets the batch file write its last line, which is exactly what the 08-12 network
failure did (`WinError 10060`, `exit=1`, clean `RUN FINISHED`).

**The cause.** The task was registered with:

```
LogonType          : Interactive
AllowHardTerminate : True
StartWhenAvailable : True
```

`Interactive` means the run lives inside the logged-on desktop session, in a visible
console window. It dies at logoff or shutdown, and anyone can close the window.
`0xC000013A` is `STATUS_CONTROL_C_EXIT` — precisely what Windows reports for that.

**Correlated against the System event log:**

| Run started | Fate | Power event |
|---|---|---|
| 08-15 17:40:33 | `^C` ~18 min in | shutdown initiated **17:59:07** — proven |
| 08-21 10:00:01 | `^C` ~41 min in (401 log lines) | none — session-level kill |
| 08-22 19:24:45 | `^C` at **19:32:44** (log mtime), 8 min in | none — session-level kill |

**Why the clean runs were clean, which is the uncomfortable part.** Look at the start
times across the whole log: 11:31, 15:48, 19:47, 20:00, 20:03, 14:21, 15:03. Almost
none fire at the scheduled 10:00 — `StartWhenAvailable` is catching up a missed trigger
at logon. **The runs that finished are the ones where the machine was then left alone
for ~55 minutes.** Collection was never reliable; it was a coin flip on whether the
desk stayed empty.

**Ruled out, each with evidence, so none of these gets re-investigated:**

- `ExecutionTimeLimit` is `PT2H` and a census takes ~55 min — not a timeout.
- `RunOnlyIfIdle` is `False`, so `StopOnIdleEnd: True` is inert — not the idle killer.
- `powercfg /q ... STANDBYIDLE` is `0` (never) and `/lastwake` is empty — not sleep.

**Fixed 2026-08-22** (elevated, `~/Downloads/lotclock-fix-task.ps1`; previous task
definition backed up to `~/Downloads/LotClock-task-backup-20260822.xml`):

1. `Microsoft-Windows-TaskScheduler/Operational` **enabled** — the next kill names itself.
2. Principal re-registered **`LogonType S4U`** ("run whether user is logged on or not").
   Session 0, no console window, survives logoff. This is the actual fix.
3. `RestartCount = 2`, `RestartInterval = PT30M` — a killed run retries instead of
   costing a day.

**Verified so far:** 08-22 re-collected end to end after the change —
`RUN FINISHED Sat 08/22/2026 20:34:00.08 exit=0`, 12,508 listings, 12,468 with a
price, **0 page failures**, day total 12,614 (the killed 1,759-row partial merged
idempotently, as designed).

**NOT yet verified, and this is the real gate:** that run was started by hand from a
logged-on session, so it does not prove S4U works. **The proof is the next unattended
10:00 trigger finishing while logged out.** Check `Get-ScheduledTaskInfo` for
`LastTaskResult 0x0` plus a matching `RUN FINISHED ... exit=0`. If S4U fails it will
fail loudly — the account may need the "Log on as a batch job" right.

**What this does not fix:** a real shutdown mid-run, which is what killed 08-15.
Nothing running on one host can. That is the second-host argument, deliberately
deferred.

## 2026-08-16 — the log lies again, and this time the reason is stdout buffering

Per-day counts read from Supabase (`store.day_row_count`), never from the log:

```
08-09 12392   08-10 12370   08-11  8153   08-12 12649
08-13   GAP   08-14 12378   08-15  4097   08-16 11702
```

**`logs/scrape.log` disagrees, and the log is the one that is wrong.** It records
`RUN FINISHED` for only 08-10, 08-12 and 08-14 in that span, and `scrape_run` (written
by `log_run`, at the *end* of a run) has no row for 08-11, 08-15 or 08-16 either.
Yet those days hold 8,153 / 4,097 / 11,702 rows.

Both symptoms have one cause: **a killed process loses buffered stdout and never reaches
`log_run`.** 08-15 is the clean demonstration — the log holds `RUN STARTED 17:40:33` then
`^C` and nothing between, while the database holds 4,097 rows the run demonstrably
collected before it died. The per-batch flush added on 08-08 is what saved those rows;
under the old all-or-nothing write, 08-11, 08-15 and 08-16 would all read as zero.

Consequences, in order of importance:

1. **Row counts are the only ground truth.** `RUN FINISHED`, `scrape_run.status`, and
   `Get-ScheduledTaskInfo` are all end-of-run artefacts and all three go missing together
   whenever the process is killed. Any continuity claim must come from
   `day_row_count()`.
2. **A day above threshold is not the same as a census.** A census is proved by
   `no new listings for 3 pages` — the exhaustion line. Only 08-09, 08-10, 08-12 and
   08-14 have it. 08-11 (8,153) and 08-16 (11,702) clear `SCRAPE_MIN_EXPECTED=8000`
   but stopped early, so their absences are partly coverage, not sales. **Condition on
   the exhaustion line, not on the row count, before modelling exits.**
3. **`SCRAPE_MIN_EXPECTED=8000` passes days that are ~34% short.** 08-11 is 8,153 against
   a ~12,400 census. It labels catastrophe, not incompleteness.
4. Today's kill is `LastTaskResult = 0xC000013A` = `STATUS_CONTROL_C_EXIT`. Started
   11:49:55, died around page 387 of ~545. Cause is host-side (sleep / logoff / manual),
   not scraper code — the walk was clean to that point, 0 page failures.

**Root cause is unchanged and is still the single collector host.** The gaps changed
shape — from "never ran" to "ran and was killed" — but not origin. Skipped this session
by choice; it remains the Phase 0 blocker.

**Next action:** decide Phase 2 (Kaggle dataset) scope on the four proven census days,
or fix the kill problem first. Nothing else is blocking.
to start reading.

## 2026-08-09 — the census landed, and the first price numbers exist

### The census passed all four checks

Read out of `logs/scrape.log`, not assumed:

1. `no new listings for 3 pages, assuming end of results` — **present**. The crawl
   stopped because it ran out of cars.
2. `reached max_listings` — **absent**, for the first time in 17 runs.
3. **543 real pages**, `collected 12392 listings, 12347 with a price, 0 page failures`.
   Pages 544–546 returned 12 parsed / 0 new each — that is the featured block repeating,
   which is exactly the artefact the 08-08 audit predicted and why a naive last-page
   probe reports 6,399.
4. `14:17:17 → 15:11:51`, **54.5 min**, well inside the 2 h `ExecutionTimeLimit`. exit=0.

Per-batch flushing worked in production, not just in the stub test: `flushed 507 rows,
12190 written so far` mid-walk, then `flushed 202 rows` at the end. A kill at minute 50
would have cost 202 rows, not 12,392.

Supabase confirms **12,392 rows for 2026-08-09** — the log and the database agree exactly.
Total **44,655 rows, 17 observed days**. Coverage went 15% → ~95% of the stated 13,029
(the site's own count moves day to day; 12,392 is what actually existed at 14:17).

### The dead-man's switch works — verified on the dashboard, and it is too twitchy

Check `My First Check`, uuid `63a29a98…f7a640`. **Period 1 day, grace 2 hours, one
notification method: email to talvinleegenwei0329@gmail.com, ON.** It is not unproven
any more, and it is not broken:

| event | what it was |
|---|---|
| `Aug 1 12:09  up ➔ down` | the 08-01→08-03 gap. **It fired.** |
| `Aug 4 11:20  down ➔ up` | desktop came back |
| `Aug 7 00:47  up ➔ down` | the 08-06 gap. **It fired.** |
| `Aug 7 11:19  down ➔ up` | desktop came back |

August shows 4 downtimes / 87.58% uptime, July 6 downtimes / 95.88%.

**But most of those downtimes were not lost days.** `Jul 26 20:20 down ➔ 20:27 up` and
`Aug 8 13:19 down ➔ 16:54 up` are days that collected fine — the run simply started
later than the day before. With period 1 day + grace 2 h, the switch is really asserting
"pings land within 26 h of each other", and run times have ranged 10:00 → 23:34. So it
alerts on *lateness*, not only on *absence*.

That matters because a switch that cries wolf gets ignored, which is the same failure as
a switch that never fires. **Recommended change (not made — it is an account setting):
grace 2 h → 12 h.** The requirement is "a day got collected", not "collected on time".
Nothing in the repo changes.

### First Phase 1 measurement — `price_moves.py` (new)

Same shape as `exit_rule.py`: reuses its `load_env()`, reads Supabase read-only, and
self-checks with `python price_moves.py --test` (passes) before it is pointed at real
data. Window is **07-19 → 08-08, 16 observed days, partial-harvest regime only** —
`CENSUS_FROM = "2026-08-09"` excludes the census day, because 11,000 listings appearing
at once is a coverage change and an absence measured across it is meaningless.

Verbatim output:

```
window: 2026-07-19 .. 2026-08-08  (16 observed days, partial-harvest regime only; 2026-08-09 census excluded)
listings seen in window: 2,315
  listings_multi_day: 2288
  listings_cut: 150
  cut_rate_pct: 6.56
  raises: 5
  median_first_cut_pct: 2.07
  median_first_cut_myr: 4000
  median_obs_days_to_first_cut: 7.0
  median_total_discount_pct: 2.21
exit rule N = 5 observed days
  exited: 68
  censored: 2247
  censored_pct: 97.1
  median_dom_obs_days_exited: 5.0
```

**The candidate headline number: 6.6% of Malaysian used-car listings cut their price
within three weeks, and the typical first cut is RM 4,000 — about 2% off ask.** Price
raises are almost nonexistent (5 across the whole window), so this is a one-directional
market. That is a number that exists nowhere else, which is the entire Phase 1 milestone.

**What it is not, and the teardown must say so:**

- **97.1% right-censored.** 2,247 of 2,315 listings were still alive when the window
  ended. `median_dom_obs_days_exited = 5.0` is therefore **not** the median days-on-market
  — only listings that died fast *can* be observed dying in a 16-day window. Quoting 5
  days as "how long a car takes to sell" would be flatly wrong. This is precisely why
  the project needs survival analysis and not an average.
- The 6.56% cut rate is over ~3 weeks of a 15% sample of the site, not over a listing's
  lifetime. It is a floor, not the rate.
- `median_obs_days_to_first_cut = 7` observed days ≈ 9 calendar days once the gaps are
  counted back in. Report it in observed days.
- Everything above dies the moment census days are pooled in. Re-run once there are
  enough census days to stand on their own, and never merge the two eras.

**Next action:** the laptop collector (below) — it is the only thing still blocking
Phase 0. Then the teardown writeup off the numbers above.

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

**Next action (done — see the 2026-08-09 section at the top): read `logs/scrape.log`
after the 08-09 10:00 run.** All four criteria held.

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

**STILL THE ONLY THING BLOCKING PHASE 0 (2026-08-09): install the backup
collector on the laptop (model 83JN).** Must be run *on the laptop*.

⚠️ **Re-check the 8pm timing before trusting it.** `--skip-if-collected` now counts rows
against `SCRAPE_MIN_EXPECTED` (8,000) via `store.day_row_count()`, not mere existence.
The desktop's census takes ~55 min from 10:00, so it is done long before 8pm and the
laptop will correctly skip. But if the desktop ever starts late enough to still be
walking at 8pm, the laptop sees a sub-threshold count and starts a **second** 543-page
census against motortrader the same evening. If desktop run times drift later, move the
backup task later too.
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
  - [x] Confirm the 08-09 run is a real census (4 checks at the top)
  - [x] Diagnose the `0xC000013A` kills — `LogonType Interactive`, fixed via S4U 08-22
  - [ ] Confirm S4U with one unattended 10:00 run finishing while logged out ← NEXT
  - [ ] Second collector host (laptop) so one machine being off is not a gap
        — deferred: only covers mid-run shutdown, and LotClock is now a proof piece
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
- [x] **≥1 price change captured for the same `listing_id`** — 150 listings cut in the
      partial era, 154 in the census era (`price_moves.py`, both windows)
- [ ] ≥1 delisting captured — **not met, and now known to be unmeetable as written.**
      N=5 gave 68 / 47 exits, but the 30-day refit puts the reversal rate at 5 days
      absent at 60.2%: those are mostly listings that came back. At the defensible
      N=10 the census era yields 1 exit in 13,172. A *delisting* is observable; a
      *sale* is not, and that is what this gate was really asking for. See the
      reframe at the bottom of this file
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
| 2026-08-08 | 2,105 | scheduled task | 2,020 from the 10:00 run + 85 net new from two bounded `--max 600` test runs |
| 2026-08-09 | **12,392** | scheduled task | **first full census** — 543 pages, ended on exhaustion not on the cap, 54.5 min. **44,655 rows total, 17 observed days of 22** |
| 2026-08-10 | 12,370 | scheduled task | census, `ok` |
| 2026-08-11 | 8,153 | scheduled task | **killed mid-walk** — no `RUN FINISHED`, no `scrape_run` row; the 8,153 survive only because writes flush per batch. Above the 8,000 threshold, so usable |
| 2026-08-12 | 12,649 | scheduled task | first attempt exit=1 at 20:10, retry 20:56 `ok` (12,426); the extra 223 are the failed attempt's flushed batches |
| 2026-08-13 | **0** | — GAP — | desktop off |
| 2026-08-14 | 12,378 | scheduled task | census, `ok` — last clean finish |
| 2026-08-15 | 4,097 | scheduled task | **killed mid-walk.** Log shows `RUN STARTED 17:40` then `^C` and nothing else — python's stdout was buffered and died with the process. **Thin day: below the 8,000 threshold, do not treat as a census** |
| 2026-08-16 | 11,702 | scheduled task | **killed mid-walk** at ~page 387. `LastTaskResult = 0xC000013A` (forced terminate). Near-complete but unfinished — no exhaustion line, so coverage is unproven |

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

**Update 2026-08-20: the dead-man's switch is built, configured and verified.**
`ping_healthcheck()` in `scraper/run.py` fires only on a healthy run — it is skipped
when the harvest is thin, so a degraded day goes red instead of green. `HEALTHCHECK_URL`
is set in `.env` and a live ping returned HTTP 200 `OK`. The note above saying it was
unbuilt was stale. The observation-day item is closed too — see below.

Until that exists, verify the task after any folder move:
`(Get-ScheduledTask -TaskName "LotClock daily scrape").Actions.Execute`

## Fix shipped 2026-08-16: `-u` in `run_daily.cmd`

`python -m scraper.run` became `python -u -m scraper.run`. One flag, unbuffered stdout,
so a killed run leaves its real progress in the log instead of a bare `^C`. It does not
prevent kills — only the second collector host does that — it makes them diagnosable.

## Observation days: derived, not a table (closed 2026-08-23)

The open item above asked for a `collection_days` table. It is not needed. A day is
an observation day if it lands enough rows, and `kaggle_export.py` already decides
that from the snapshots themselves: `is_observation_day` compares the day's row count
against `COMPLETE_MIN` inside the census era, and the self-check at the bottom of the
file asserts a 1-row day is excluded. A table would restate what the rows already
prove, and could disagree with them — a killed run would still write its "I collected
today" row.

That check earns its keep. 2026-08-21 started at 10:00 and never logged a
`RUN FINISHED`; the export dropped it as a partial walk automatically, alongside
08-11 and 08-15.

Coverage as of 2026-08-23: **10 observation days** (08-09, 10, 12, 14, 16, 17, 19, 20,
22, 23), 3 census days dropped as killed walks (08-11, 08-15, 08-21), 13,167 listings.
Exits under the N=5 rule: 25, so 99.8% still censored — survival remains not estimable,
and the notebook must keep saying so rather than quoting a median.

Still open: the second collector host. It is the only thing that closes a gap caused by
this machine being off or killing the run.

## Reframe decided 2026-08-24: stop waiting for days-to-sell

Refitting `exit_rule.py` on all 30 observed days overturned teardown-01's exit rule.
At 5 days absent, teardown-01 estimated an 11.7% reversal rate; the refit says
**60.2%**. The defensible threshold moved from N=5 to **N=10**.

That threshold is longer than the census era can carry. Census era is 11 observation
days; requiring 10 days of absence yields **1 exit out of 13,172 listings** (100.0%
censored). N=5 gives 48 (99.6%), N=3 gives 95 (99.3%) — every rule with enough events
to model is a rule now known to be too loose. The 41-exit figure from the refit pools
both coverage eras, which the method notes forbid; inside the clean era it is 1.

Conclusion: the exit event is not in the data. What the snapshots observe is *listing
removal* — expiry, relist, crawl miss, sale — unlabelled. More calendar time adds more
of the same ambiguous signal, so waiting was the wrong plan. Extrapolated, a
50%-uncensored sample lands ~April 2027 and would still be mostly housekeeping.

Shipped instead: `docs/teardown-02.md`, which publishes the censoring wall itself as
the finding. Survival model **deferred, not cancelled** — it needs a labelled exit
(sold badge / status field on the detail page), not a longer window. That is a new
scrape surface and triggers the PII rule, so it is a decision, not a formality.

Also corrected there: the cut rate did NOT fall from 6.6% to 1.15%. The partial-harvest
era could only see a listing twice if it survived long enough to be caught twice, so it
oversampled long-lived listings — the ones with time to cut. Sampling artifact, labelled
as such rather than published as a trend.

Standing action: **refit `exit_rule.py` monthly.** This entry exists because a refit
overturned a published number.
